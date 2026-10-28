using System;
using System.Collections.Generic;
using System.IO;
using Il2CppInterop.Runtime.InteropTypes.Arrays;
using UnityEngine;
using VRoidCore.Common.SpecificTypes;
using VRoidCore.Draw.TiledBitmap;
using VRoidCore.Editing;
using VRoidCore.Editing.History.Command;
using VRoidCore.Editing.Query;
using UColor = UnityEngine.Color;

namespace VRoidMcpBridge;

/// <summary>
/// Calques de texture : lister, exporter en PNG, réimporter un PNG (remplacement ou nouveau calque).
/// Même principe que les boutons Exporter/Importer de l'éditeur de texture de VRoid, sans boîte de dialogue.
/// </summary>
public static class Textures
{
    static Context Ctx() => VRoidApi.RequireContextPublic();

    /// <summary>Éléments (transferables) d'un groupe → images éditables → calques.</summary>
    public static object Layers(string groupId)
    {
        if (string.IsNullOrEmpty(groupId)) throw new ArgumentException("paramètre manquant : group");
        var c = Ctx();
        var model = c.ActiveModel;
        var result = new List<object>();
        foreach (var kv in c.GetActiveLeafTransferables())
        {
            var info = kv.Value;
            if (info == null || info.GroupId != groupId) continue;
            var images = new List<object>();
            var imagePaths = new GetEditableImagePathsForTransferableQuery(kv.Key).Execute(model);
            foreach (var ip in imagePaths)
                images.Add(new { image = ip.ImageId, layers = LayersOfImage(ip, model) });
            result.Add(new { transferable = kv.Key, type = info.Type, images });
        }
        return result;
    }

    /// <summary>Calques raster d'une image éditable (node, nom, opacité, visibilité, mode de fusion).</summary>
    public static List<object> LayersOfImage(EditableImagePath ip, Model model)
    {
        var layers = new List<object>();
        foreach (var lp in new GetEditableImageRasterLayersQuery(ip).Execute(model))
        {
            var ps = new GetEditableImageLayerTreeParameterSetQuery(lp).Execute(model);
            layers.Add(new
            {
                node = lp.NodeId,
                name = ps?._Name_k__BackingField,
                opacity = ps?._Opacity_k__BackingField,
                visible = ps?._Visibility_k__BackingField,
                mode = ps?._CompositionMode_k__BackingField.ToString(),
            });
        }
        return layers;
    }

    static EditableImageRasterLayerPath LayerPath(string transferable, string image, string node) =>
        new(new EditableImagePath(transferable, image), node);

    /// <summary>Exporte un calque en PNG (RGBA, transparence conservée).</summary>
    public static object Export(string transferable, string image, string node, string path)
    {
        var c = Ctx();
        var res = new GetRasterLayerContentQuery(LayerPath(transferable, image, node)).Execute(c.ActiveModel);
        int w = res.size.x, h = res.size.y;
        byte[] rgba = res.rgbaBytes;
        var tex = new Texture2D(w, h, TextureFormat.RGBA32, false);
        try
        {
            tex.LoadRawTextureData(rgba);
            tex.Apply(false);
            byte[] png = ImageConversion.EncodeToPNG(tex);
            path = Path.GetFullPath(path ?? Path.Combine(Path.GetTempPath(), $"vroid_layer_{node}.png"));
            File.WriteAllBytes(path, png);
            return new { ok = true, path, width = w, height = h };
        }
        finally { UnityEngine.Object.Destroy(tex); }
    }

    /// <summary>
    /// Recolore un calque sur place (alpha conservé). mode = "multiply" (tissu clair → couleur, ombres gardées)
    /// ou "colorize" (garde la luminosité, impose teinte et saturation de la couleur cible). Annulable.
    /// </summary>
    public static object Recolor(string transferable, string image, string node, float r, float g, float b, string mode, float strength)
    {
        var c = Ctx();
        var lp = LayerPath(transferable, image, node);
        var res = new GetRasterLayerContentQuery(lp).Execute(c.ActiveModel);
        int w = res.size.x, h = res.size.y;
        byte[] src = res.rgbaBytes;
        strength = Mathf.Clamp01(strength);
        mode = (mode ?? "multiply").ToLowerInvariant();
        UColor.RGBToHSV(new UColor(r, g, b), out var th, out var ts, out var tv);

        var px = new UColor[w * h];
        int touched = 0;
        for (int i = 0; i < px.Length; i++)
        {
            int o = i * 4;
            float sr = src[o] / 255f, sg = src[o + 1] / 255f, sb = src[o + 2] / 255f, a = src[o + 3] / 255f;
            float nr, ng, nb;
            if (mode == "colorize")
            {
                // Luminosité d'origine conservée, teinte et saturation de la cible.
                float lum = 0.299f * sr + 0.587f * sg + 0.114f * sb;
                var col = UColor.HSVToRGB(th, ts, 1f);
                float cl = 0.299f * col.r + 0.587f * col.g + 0.114f * col.b;
                float k = cl > 1e-4f ? lum / cl : 0f;
                nr = Mathf.Clamp01(col.r * k); ng = Mathf.Clamp01(col.g * k); nb = Mathf.Clamp01(col.b * k);
            }
            else
            {
                nr = sr * r; ng = sg * g; nb = sb * b;
            }
            if (a > 0) touched++;
            px[i] = new UColor(Mathf.Lerp(sr, nr, strength), Mathf.Lerp(sg, ng, strength), Mathf.Lerp(sb, nb, strength), a);
        }
        var cmd = new LoadImageToEditableImageRasterLayerCommand(lp, new BitmapSize(w, h), new Il2CppStructArray<UColor>(px));
        c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
        return new { ok = true, width = w, height = h, mode, strength, opaquePixels = touched };
    }

    /// <summary>
    /// Importe un PNG dans un calque existant (remplacement) ou comme nouveau calque.
    /// Le PNG doit avoir la taille de l'image (celle donnée par l'export). Annulable (Ctrl+Z).
    /// </summary>
    public static object Import(string transferable, string image, string node, string path, bool asNewLayer)
    {
        var c = Ctx();
        if (!File.Exists(path)) throw new FileNotFoundException($"PNG introuvable : {path}");
        var bytes = File.ReadAllBytes(path);
        var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
        try
        {
            if (!ImageConversion.LoadImage(tex, bytes)) throw new InvalidDataException("PNG illisible");
            int w = tex.width, h = tex.height;
            UColor[] px = tex.GetPixels();
            var pixels = new Il2CppStructArray<UColor>(px);
            var size = new BitmapSize(w, h);
            var imagePath = new EditableImagePath(transferable, image);

            if (asNewLayer)
            {
                var cmd = new LoadImageAsNewRasterLayerCommand(imagePath, size, pixels);
                c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
            }
            else
            {
                if (string.IsNullOrEmpty(node)) throw new ArgumentException("paramètre manquant : node (ou as_new_layer=true)");
                var expected = new GetRasterLayerContentQuery(LayerPath(transferable, image, node)).Execute(c.ActiveModel).size;
                if (expected.x != w || expected.y != h)
                    throw new ArgumentException($"taille {w}x{h} différente du calque ({expected.x}x{expected.y})");
                var cmd = new LoadImageToEditableImageRasterLayerCommand(LayerPath(transferable, image, node), size, pixels);
                c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
            }
            return new { ok = true, width = w, height = h, asNewLayer };
        }
        finally { UnityEngine.Object.Destroy(tex); }
    }
}
