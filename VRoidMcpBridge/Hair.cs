using System;
using System.Collections.Generic;
using Il2CppInterop.Runtime.InteropTypes;
using VRoidCore.Common.SpecificTypes;
using VRoidCore.Editing;
using VRoidCore.Editing.History.Command;
using VRoidCore.Editing.Query;
using VRoidCore.Editing.Query.AdvancedEdit;
using UColor = UnityEngine.Color;

namespace VRoidMcpBridge;

/// <summary>
/// Matériaux de cheveux : leur couleur ne passe pas par les paramètres de groupe mais par des
/// « matériaux de cheveux partagés » (SharedHairMaterialPath), avec leurs couleurs et leur texture.
/// </summary>
public static class Hair
{
    static Context Ctx() => VRoidApi.RequireContextPublic();

    /// <summary>Identifiants des matériaux de cheveux utilisés par les éléments de cheveux du modèle.</summary>
    static List<string> MaterialIds(Context c)
    {
        var ids = new List<string>();
        foreach (var kv in c.GetActiveLeafTransferables())
        {
            var type = kv.Value?.Type ?? "";
            if (!type.Contains("Hair")) continue;
            foreach (var p in new GetAllMaterialsQuery(kv.Key).Execute(c.ActiveModel))
                if (p != null && !ids.Contains(p.SharedHairMaterialId)) ids.Add(p.SharedHairMaterialId);
        }
        if (ids.Count == 0)
        {
            var def = new GetDefaultHairMaterialIdQuery().Execute(c.ActiveModel);
            if (def != null) ids.Add(def.SharedHairMaterialId);
        }
        return ids;
    }

    /// <summary>Liste les matériaux de cheveux : nom, couleurs réglables (clé + valeur) et textures (avec leurs calques).</summary>
    public static object Materials()
    {
        var c = Ctx();
        var model = c.ActiveModel;
        var result = new List<object>();
        foreach (var id in MaterialIds(c))
        {
            var path = new SharedHairMaterialPath(id);
            var colors = new List<object>();
            var textures = new List<object>();
            var other = new List<string>();
            var res = new GetHairMaterialQuery(path).Execute(model);
            if (res?.sections != null)
                foreach (var s in res.sections) Walk(s, model, colors, textures, other);
            result.Add(new
            {
                material = id,
                name = new GetMaterialNameQuery(path).Execute(model),
                colors,
                textures,
                otherSections = other,
            });
        }
        return result;
    }

    static void Walk(Il2CppObjectBase s, Model model, List<object> colors, List<object> textures, List<string> other)
    {
        if (s == null) return;
        if (s.TryCast<TopCategory>() is { } top)
        {
            if (top.childSections != null) foreach (var ch in top.childSections) Walk(ch, model, colors, textures, other);
        }
        else if (s.TryCast<ClothingTemplate>() is { } tpl)
        {
            if (tpl.childSections != null) foreach (var ch in tpl.childSections) Walk(ch, model, colors, textures, other);
        }
        else if (s.TryCast<ColorGroup>() is { } cg)
        {
            if (cg.colors != null) foreach (var col in cg.colors) Walk(col, model, colors, textures, other);
        }
        else if (s.TryCast<ColorSubGroup>() is { } sg)
        {
            if (sg.colors != null) foreach (var col in sg.colors) Walk(col, model, colors, textures, other);
        }
        else if (s.TryCast<MaterialColor>() is { } mc)
        {
            var v = new GetMaterialColorQuery(mc.materialPath, mc.parameterKey).Execute(model);
            colors.Add(new { key = mc.parameterKey, label = mc.translationKey, value = new { v.r, v.g, v.b, v.a } });
        }
        else if (s.TryCast<BaseColor>() is { } bc)
        {
            // Couleur de superposition (teinte des cheveux d'un preset) : se règle avec SetBaseColorCommand.
            colors.Add(new { key = "base:" + bc.colorId, colorId = bc.colorId, label = bc.translationKey, value = (object)null });
        }
        else if (s.TryCast<VRoidCore.Editing.Query.AdvancedEdit.Texture>() is { } tex)
        {
            var ip = tex.editableImagePath;
            textures.Add(new
            {
                label = tex.translationKey,
                transferable = ip?.TransferableId,
                image = ip?.ImageId,
                layers = ip != null ? SafeLayers(ip, model) : null,
            });
        }
        else
        {
            other.Add(s.TryCast<Il2CppSystem.Object>()?.GetIl2CppType()?.FullName ?? "?");
        }
    }

    // Une texture pas encore éditable (ex. après réouverture) fait échouer la requête de calques : on l'ignore.
    static object SafeLayers(EditableImagePath ip, Model model)
    {
        try { return Textures.LayersOfImage(ip, model); }
        catch (Exception e) { return new { error = "texture is not editable yet", detail = e.Message.Split('\n')[0] }; }
    }

    /// <summary>Passe un matériau de cheveux en édition de texture (bouton Éditer). Annulable.</summary>
    public static object BeginEdit(string material)
    {
        if (string.IsNullOrEmpty(material)) throw new ArgumentException("missing parameter: material");
        var c = Ctx();
        var cmd = new VRoidCore.Editing.History.Command.AdvancedEdit.BeginHairMaterialAdvancedEditCommand(
            new SharedHairMaterialPath(material), "Layer", true);
        c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
        return new { ok = true, material };
    }

    /// <summary>Change une couleur d'un matériau de cheveux (clé donnée par Materials). Annulable.</summary>
    public static object SetColor(string material, string key, float r, float g, float b, float a)
    {
        if (string.IsNullOrEmpty(key)) throw new ArgumentException("missing parameter: key");
        if (key.StartsWith("base:"))
        {
            // Couleur de superposition d'un preset : identifiant global, le matériau n'est pas nécessaire.
            var cb = new SetBaseColorCommand(key.Substring(5), new UColor(r, g, b, a));
            Ctx().ExecuteSyncCommand(cb.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
            return new { ok = true, key, color = new { r, g, b, a } };
        }
        if (string.IsNullOrEmpty(material)) throw new ArgumentException("missing parameter: material");
        var c = Ctx();
        var cmd = new SetMaterialColorCommand(new SharedHairMaterialPath(material), key, new UColor(r, g, b, a));
        c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
        return new { ok = true, material, key, color = new { r, g, b, a } };
    }
}
