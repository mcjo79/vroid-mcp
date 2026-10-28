using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Il2CppInterop.Runtime;
using UnityEngine;
using UColor = UnityEngine.Color;
using VRoid.Studio.Component;
using VRoidCore.Common.SpecificTypes;
using VRoidCore.Common.TransferableTypes.Path;
using VRoidCore.Editing;
using VRoidCore.Editing.History.Command;
using Il2Gen = Il2CppSystem.Collections.Generic;

namespace VRoidMcpBridge;

/// <summary>Accès au modèle VRoid en cours d'édition. Toutes les méthodes synchrones tournent sur le thread principal.</summary>
public static class VRoidApi
{
    // ---------- Accès au Context ----------

    static Context FindContext()
    {
        var updaters = UnityEngine.Object.FindObjectsOfType<VRoidCoreModelUpdater>();
        foreach (var u in updaters)
        {
            var c = u._context;
            if (c != null && c.IsCommandExecutable) return c;
        }
        foreach (var u in updaters)
            if (u._context != null) return u._context;
        return null;
    }

    public static Context RequireContextPublic() => RequireContext();

    static Context RequireContext() =>
        FindContext() ?? throw new InvalidOperationException("Aucun modèle ouvert dans VRoid Studio (ouvrez ou créez un modèle).");

    // ---------- Lecture ----------

    public static object Status()
    {
        var c = FindContext();
        return new
        {
            plugin = "VRoidMcpBridge 0.10.0",
            unity = Application.unityVersion,
            modelOpen = c != null,
            modelType = c?.ModelType,
            isEditing = c?.IsEditing ?? false,
            canUndo = c?.CanUndo ?? false,
            canRedo = c?.CanRedo ?? false,
        };
    }

    public static object Groups()
    {
        var c = RequireContext();
        var list = new List<object>();
        foreach (var kv in c.GetActiveLeafTransferableGroups())
        {
            var info = c.GetActiveTransferableGroupInfo(kv.Key);
            list.Add(new
            {
                id = kv.Key,
                type = info?.Type,
                resource = info?.ResourceName,
            });
        }
        return list;
    }

    public static object Params(string groupId)
    {
        if (string.IsNullOrEmpty(groupId)) throw new ArgumentException("paramètre manquant : group");
        var c = RequireContext();
        var list = new List<object>();
        foreach (var kv in c.GetParametersForTransferableGroup(groupId))
        {
            var p = kv.Value;
            object value = null;
            var kind = p._Type_k__BackingField.ToString();
            if (p.blendShapeTransform != null) { kind = "blendshape"; value = p.blendShapeTransform._Value_k__BackingField; }
            else if (p.boneTransform != null) { kind = "bone"; value = p.boneTransform._Value_k__BackingField; }
            else if (p.color != null)
            {
                kind = "color";
                var col = p.color._Color_k__BackingField;
                value = new { r = col.r, g = col.g, b = col.b, a = col.a };
            }
            list.Add(new { key = kv.Key, paramKey = p._Key_k__BackingField, kind, value });
        }
        return list;
    }

    // ---------- Écriture (commandes annulables via Ctrl+Z) ----------

    // Les paires clé/valeur génériques ne doivent PAS être construites côté managé (plantage du runtime) :
    // on remplit un Dictionary IL2CPP natif, que la commande lit comme IEnumerable<KeyValuePair<,>>.

    static void Exec(LegacySyncCommandBase cmd) =>
        RequireContext().ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());

    /// <summary>Construit les structures utilisées par les commandes, sans modifier le modèle.</summary>
    public static object SelfTest()
    {
        var d1 = new Il2Gen.Dictionary<IBlendShapeTransformPath, float>();
        d1.Add(new BlendShapeTransformPath("test").Cast<IBlendShapeTransformPath>(), 0.5f);
        var e1 = d1.Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<IBlendShapeTransformPath, float>>>();
        var d2 = new Il2Gen.Dictionary<IBoneTransformPath, float>();
        d2.Add(new BoneTransformPath("test").Cast<IBoneTransformPath>(), 0.5f);
        var e2 = d2.Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<IBoneTransformPath, float>>>();
        var d3 = new Il2Gen.Dictionary<IColorPath, UColor>();
        d3.Add(new ColorPath("test").Cast<IColorPath>(), new UColor(1, 0, 0, 1));
        var e3 = d3.Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<IColorPath, UColor>>>();
        var c1 = new SetBlendShapeTransformParameterCommand("g", e1, true);
        var c2 = new SetBoneTransformParameterCommand("g", e2, true);
        var c3 = new SetColorParameterCommand("g", e3, true);
        return new { ok = true, counts = new[] { d1.Count, d2.Count, d3.Count }, commands = new[] { c1.ToString(), c2.ToString(), c3.ToString() } };
    }

    public static object SetBlendShape(string groupId, string key, float value)
    {
        RequireContext();
        var d = new Il2Gen.Dictionary<IBlendShapeTransformPath, float>();
        d.Add(new BlendShapeTransformPath(key).Cast<IBlendShapeTransformPath>(), value);
        Exec(new SetBlendShapeTransformParameterCommand(groupId,
            d.Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<IBlendShapeTransformPath, float>>>(), true));
        return new { ok = true, group = groupId, key, value };
    }

    public static object SetBone(string groupId, string key, float value)
    {
        RequireContext();
        var d = new Il2Gen.Dictionary<IBoneTransformPath, float>();
        d.Add(new BoneTransformPath(key).Cast<IBoneTransformPath>(), value);
        Exec(new SetBoneTransformParameterCommand(groupId,
            d.Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<IBoneTransformPath, float>>>(), true));
        return new { ok = true, group = groupId, key, value };
    }

    public static object SetColor(string groupId, string key, float r, float g, float b, float a)
    {
        RequireContext();
        var d = new Il2Gen.Dictionary<IColorPath, UColor>();
        d.Add(new ColorPath(key).Cast<IColorPath>(), new UColor(r, g, b, a));
        Exec(new SetColorParameterCommand(groupId,
            d.Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<IColorPath, UColor>>>(), true));
        return new { ok = true, group = groupId, key, color = new { r, g, b, a } };
    }

    public static Task<object> Undo() => MainThread.RunAsync<object>(tcs =>
    {
        var c = RequireContext();
        if (!c.CanUndo) { tcs.SetResult(new { ok = false, message = "rien à annuler" }); return; }
        c.UndoAsync(
            (Il2CppSystem.Action)(Action)(() => tcs.TrySetResult(new { ok = true })),
            (Il2CppSystem.Action<Il2CppSystem.Exception>)(Action<Il2CppSystem.Exception>)(e => tcs.TrySetException(new Exception(e.Message))));
    });

    public static Task<object> Redo() => MainThread.RunAsync<object>(tcs =>
    {
        var c = RequireContext();
        if (!c.CanRedo) { tcs.SetResult(new { ok = false, message = "rien à rétablir" }); return; }
        c.RedoAsync(
            (Il2CppSystem.Action)(Action)(() => tcs.TrySetResult(new { ok = true })),
            (Il2CppSystem.Action<Il2CppSystem.Exception>)(Action<Il2CppSystem.Exception>)(e => tcs.TrySetException(new Exception(e.Message))));
    });

    // ---------- Capture d'écran (permet à l'IA de "voir" le résultat) ----------

    public static async Task<object> Screenshot(string path)
    {
        path ??= Path.Combine(Path.GetTempPath(), $"vroid_{DateTime.Now:yyyyMMdd_HHmmss_fff}.png");
        path = Path.GetFullPath(path);
        if (File.Exists(path)) File.Delete(path);
        // CaptureScreenshot(string) plante dans l'interop (conversion de chaîne) : on passe par une texture.
        var png = await MainThread.Run(() =>
        {
            var tex = ScreenCapture.CaptureScreenshotAsTexture();
            try { return (byte[])ImageConversion.EncodeToPNG(tex); }
            finally { UnityEngine.Object.Destroy(tex); }
        });
        await File.WriteAllBytesAsync(path, png);
        return new { ok = true, path, bytes = png.Length };
    }
}
