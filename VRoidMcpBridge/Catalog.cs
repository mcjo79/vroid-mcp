using System;
using System.Collections.Generic;
using UnityEngine;
using VRoid.Studio;
using VRoidCore.AssetStorage;
using VRoidStudio.GUI.AvatarEditor;

namespace VRoidMcpBridge;

/// <summary>
/// Ce que VRoid propose réellement au moment de l'appel : objets personnalisés (custom items) de l'utilisateur
/// et vignettes natives des presets. Sert au scan du cache à chaque ouverture de VRoid.
/// </summary>
public static class Catalog
{
    static MainModel Main()
    {
        var ed = UnityEngine.Object.FindObjectOfType<AvatarEditor>();
        return ed?._viewModel?._mainModel ?? throw new InvalidOperationException("VRoid is not ready yet");
    }

    /// <summary>Objets personnalisés enregistrés par l'utilisateur, toutes catégories personnalisables.</summary>
    public static object CustomItems()
    {
        var reg = Main().customItemRegistry ?? throw new InvalidOperationException("custom-item registry not found");
        var result = new List<object>();
        var types = new List<string>();
        // Dictionnaire interne type -> liste (IL2CPP) : itérable directement, contrairement aux interfaces.
        foreach (var kv in reg._transferableGroupTypeToFileCustomItemModelLists)
        {
            var type = kv.Key;
            var models = kv.Value;
            types.Add(type);
            if (models == null) continue;
            for (int i = 0; i < models.Count; i++)
            {
                var m = models[i];
                if (m == null) continue;
                string res = null, rev = null;
                try { res = m.CustomItemId?.ResourceName; rev = m.CustomItemId?.Revision; } catch { }
                bool registered = false;
                try { registered = reg.CheckIfIsRegisteredInAssetStorage(m.TransferableGroupResourceName); } catch { }
                result.Add(new
                {
                    type = m.TransferableGroupTypeId ?? type,
                    name = m.DisplayName,
                    id = m.TransferableGroupId,
                    resource = m.TransferableGroupResourceName,
                    customItemResource = res,
                    revision = rev ?? m.TransferableGroupRevision,
                    file = m.FilePath,
                    timestamp = m.TimestampForSorting.ToString(),
                    registered,
                });
            }
        }
        return new { count = result.Count, types, items = result };
    }

    // ---------- Vignettes natives des presets ----------
    // Méthode reprise de vroid-studio-mcp (Thumbnails.cs, licence MIT, © Ilya Chelyadin et contributeurs) :
    // la vignette d'un preset intégré est l'image "thumbnail.png" du bundle "vroid-thumbnails-<chemin en minuscules>".

    const string PathPrefix = "Assets/vroid-vroidcoredata/AssetBundles/Thumbnails/";

    public static bool TryDerive(string resource, out string bundle, out string path)
    {
        bundle = path = null;
        if (string.IsNullOrEmpty(resource)) return false;
        var cut = resource.IndexOf("/TransferableGroupType.", StringComparison.Ordinal);
        if (cut < 0) return false;
        bundle = "vroid-thumbnails-" + resource.Substring(0, cut).ToLowerInvariant().Replace('/', '-');
        path = PathPrefix + bundle + "/thumbnail.png";
        return true;
    }

    /// <summary>PNG de la vignette d'un preset intégré, écrit dans path. Rien n'est appliqué au modèle.</summary>
    public static object PresetThumbnail(string resource, string outPath)
    {
        if (!TryDerive(resource, out var bundle, out var path)) throw new ArgumentException($"not a built-in preset: {resource}");
        var storage = Main().assetStorage?.TryCast<BundleAssetStorage>()
                      ?? throw new InvalidOperationException("unexpected asset storage");
        var fs = storage.bundleManager.OpenReadOnly(bundle) ?? throw new InvalidOperationException($"bundle not found: {bundle}");
        byte[] png = null;
        var rfs = fs.TryCast<ResourcesFileSystem>();
        if (rfs != null)
        {
            var tex = rfs.GetObject<Texture2D>(path);
            if (tex != null) png = EncodeAny(tex);
        }
        if (png == null)
        {
            var bytes = fs.GetBytes(path);
            if (bytes != null && bytes.Length > 8) png = bytes;
        }
        if (png == null) throw new InvalidOperationException("unreadable thumbnail");
        outPath = System.IO.Path.GetFullPath(outPath ?? System.IO.Path.Combine(System.IO.Path.GetTempPath(), bundle + ".png"));
        System.IO.File.WriteAllBytes(outPath, png);
        return new { ok = true, path = outPath, bytes = png.Length };
    }

    /// <summary>Encode une texture en PNG, même si elle n'est pas lisible (copie via une RenderTexture).</summary>
    static byte[] EncodeAny(Texture2D tex)
    {
        if (tex.isReadable) return ImageConversion.EncodeToPNG(tex);
        var rt = RenderTexture.GetTemporary(tex.width, tex.height, 0, RenderTextureFormat.ARGB32);
        var prev = RenderTexture.active;
        try
        {
            Graphics.Blit(tex, rt);
            RenderTexture.active = rt;
            var copy = new Texture2D(tex.width, tex.height, TextureFormat.RGBA32, false);
            copy.ReadPixels(new Rect(0, 0, tex.width, tex.height), 0, 0);
            copy.Apply(false);
            var png = ImageConversion.EncodeToPNG(copy);
            UnityEngine.Object.Destroy(copy);
            return png;
        }
        finally
        {
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
        }
    }
}
