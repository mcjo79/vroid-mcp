using System;
using System.Collections.Generic;
using VRoidCore.Common.TransferableTypes.Path;
using VRoidCore.Editing;
using VRoidCore.Editing.Query;

namespace VRoidMcpBridge;

/// <summary>
/// Shape sliders of an item, as VRoid shows them under Customize &gt; Parameters
/// (skirt tighter/wider/shorter/longer, sleeve length, collar...).
/// They are template blendshapes of the clothing group: VRoid lists them with
/// GetTransferableGroupBlendShapesQuery (one call per transferable of the group) and reads/writes them
/// as IBlendShapeTransformPath, so the regular SetBlendShapeTransformParameterCommand applies (undoable).
/// A slider key is "template:&lt;template path&gt;|&lt;blendshape key&gt;" for a template blendshape,
/// or the plain blendshape key otherwise.
/// </summary>
public static class ClothingSliders
{
    const string TemplatePrefix = "template:";

    static string Wrapped(Il2CppSystem.Object o)
    {
        if (o == null) return null;
        try { return o.Cast<VRoidCore.Common.PrimitiveWrapper<string>>().Value; } catch { }
        return Interop.Get(o, "Value") as string ?? Interop.Get(o, "Key") as string;
    }

    /// <summary>Stable text key for a blendshape path.</summary>
    public static string Encode(IBlendShapeTransformPath path)
    {
        if (path == null) return null;
        var tpl = path.TryCast<TemplateBlendShapeTransformPath>();
        if (tpl != null)
        {
            var t = Wrapped(tpl.templatePath?.Cast<Il2CppSystem.Object>());
            var k = Wrapped(tpl.editableElementPath?.Cast<Il2CppSystem.Object>());
            return TemplatePrefix + t + "|" + k;
        }
        var plain = path.TryCast<BlendShapeTransformPath>();
        return plain != null ? plain.Key : Wrapped(path.Cast<Il2CppSystem.Object>());
    }

    /// <summary>Path object for a key produced by Encode (or a plain blendshape key).</summary>
    public static IBlendShapeTransformPath Decode(string key)
    {
        if (key != null && key.StartsWith(TemplatePrefix, StringComparison.Ordinal))
        {
            var rest = key.Substring(TemplatePrefix.Length);
            var bar = rest.LastIndexOf('|');
            if (bar <= 0) throw new ArgumentException("template key must be template:<template path>|<blendshape key>");
            return new TemplateBlendShapeTransformPath(new TemplatePath(rest.Substring(0, bar)),
                new BlendShapeTransformPath(rest.Substring(bar + 1))).Cast<IBlendShapeTransformPath>();
        }
        return new BlendShapeTransformPath(key).Cast<IBlendShapeTransformPath>();
    }

    static string Label(VRoidCore.Protobuf.LocalizedString name)
    {
        if (name == null) return null;
        string s = null;
        try { s = name.userDefinedString_; } catch { }
        if (string.IsNullOrEmpty(s)) try { s = name.localizationKey_; } catch { }
        return s;
    }

    /// <summary>Current value of a blendshape parameter (0..1), read from the model.</summary>
    public static float? Read(Context c, string groupId, IBlendShapeTransformPath path)
    {
        try { return c.ActiveModel.GetBlendShapeTransformParameter(groupId, path); } catch { return null; }
    }

    /// <summary>Sliders of one group: key, label and current value (0..1).</summary>
    public static List<object> List(Context c, string groupId)
    {
        var list = new List<object>();
        var seen = new HashSet<string>();
        var transferables = new List<string>();
        foreach (var kv in c.GetActiveLeafTransferables())
            if (kv.Value != null && kv.Value.GroupId == groupId) transferables.Add(kv.Key);
        if (transferables.Count == 0) transferables.Add(null);

        foreach (var tid in transferables)
        {
            GetTransferableGroupBlendShapesQuery.Result res;
            try { res = new GetTransferableGroupBlendShapesQuery(groupId, tid).Execute(c.ActiveModel); }
            catch { continue; }
            if (res?.blendShapes == null) continue;
            foreach (var bs in res.blendShapes)
            {
                if (bs?.path == null) continue;
                var key = Encode(bs.path);
                if (key == null || !seen.Add(key)) continue;
                list.Add(new { key, label = Label(bs.name), value = Read(c, groupId, bs.path) });
            }
        }
        return list;
    }
}
