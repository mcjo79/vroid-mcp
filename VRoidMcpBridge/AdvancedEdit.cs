using System;
using System.Collections.Generic;
using Il2CppInterop.Runtime.InteropTypes;
using VRoidCore.Common.SpecificTypes;
using VRoidCore.Common.TransferableTypes.Path;
using VRoidCore.Editing;
using VRoidCore.Editing.History.Command;
using VRoidCore.Editing.History.Command.AdvancedEdit;
using VRoidCore.Editing.Query.AdvancedEdit;
using Il2Gen = Il2CppSystem.Collections.Generic;

namespace VRoidMcpBridge;

/// <summary>
/// Édition avancée des vêtements : couleurs réglables d'un vêtement preset, et passage en mode
/// « édition de texture » (comme le bouton Éditer de VRoid) pour rendre ses calques modifiables.
/// </summary>
public static class AdvancedEdit
{
    static Context Ctx() => VRoidApi.RequireContextPublic();

    static string TypeOfGroup(Context c, string groupId) =>
        c.GetActiveTransferableGroupInfo(groupId)?.Type ?? throw new ArgumentException($"unknown group: {groupId}");

    /// <summary>Couleurs réglables d'un vêtement (clé utilisable avec /set_color et le même groupe).</summary>
    public static object ClothingColors(string groupId)
    {
        var c = Ctx();
        var res = new GetClothingQuery(TypeOfGroup(c, groupId)).Execute(c.ActiveModel);
        var colors = new List<object>();
        var other = new List<string>();
        if (res?.sections != null) foreach (var s in res.sections) Walk(c, s, colors, other);
        return new { group = groupId, colors, otherSections = other };
    }

    static void Walk(Context c, Il2CppObjectBase s, List<object> colors, List<string> other)
    {
        if (s == null) return;
        if (s.TryCast<TopCategory>() is { } top) { if (top.childSections != null) foreach (var ch in top.childSections) Walk(c, ch, colors, other); }
        else if (s.TryCast<ClothingTemplate>() is { } tpl) { if (tpl.childSections != null) foreach (var ch in tpl.childSections) Walk(c, ch, colors, other); }
        else if (s.TryCast<ColorGroup>() is { } cg) { if (cg.colors != null) foreach (var col in cg.colors) Walk(c, col, colors, other); }
        else if (s.TryCast<ColorSubGroup>() is { } sg) { if (sg.colors != null) foreach (var col in sg.colors) Walk(c, col, colors, other); }
        else if (s.TryCast<CommonColor>() is { } cc)
        {
            var key = cc.elementKey?.TryCast<ColorPath>()?.Key;
            if (string.IsNullOrEmpty(key) && cc.elementKey != null)
            {
                // Some VRoid versions expose IColorPath through a different concrete wrapper
                // (PrimitiveWrapper<string>): try the backing value/property before giving up.
                try
                {
                    key = cc.elementKey.Cast<VRoidCore.Common.PrimitiveWrapper<string>>()?.Value;
                }
                catch { }
                if (string.IsNullOrEmpty(key))
                    key = Interop.Get(cc.elementKey, "Key") as string
                          ?? Interop.Get(cc.elementKey, "Value") as string
                          ?? Interop.Get(cc.elementKey, "_Value_k__BackingField") as string
                          ?? Interop.Invoke(cc.elementKey, "get_Key") as string;
            }
            object value = null;
            try
            {
                var v = c.GetColorParameter(cc.transferableGroupId, cc.elementKey);
                value = new { v.r, v.g, v.b, v.a };
            }
            catch { }
            colors.Add(new { group = cc.transferableGroupId, key, label = cc.translationKey, value });
        }
        else other.Add(s.TryCast<Il2CppSystem.Object>()?.GetIl2CppType()?.FullName ?? "?");
    }

    /// <summary>Passe un vêtement en édition de texture (ses calques deviennent visibles par /layers). Annulable.</summary>
    public static object BeginClothingEdit(string groupId)
    {
        var c = Ctx();
        TypeOfGroup(c, groupId);
        var ids = new Il2Gen.List<string>();
        foreach (var kv in c.GetActiveLeafTransferables())
            if (kv.Value != null && kv.Value.GroupId == groupId) ids.Add(kv.Key);
        if (ids.Count == 0) throw new InvalidOperationException("no item in this group");
        var cmd = new BeginClothingAdvancedEditCommand(ids.Cast<Il2Gen.IEnumerable<string>>(), groupId, "Layer");
        c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());
        return new { ok = true, group = groupId, transferables = ids.Count };
    }
}
