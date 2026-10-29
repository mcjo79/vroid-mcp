using System;
using System.Threading.Tasks;
using VRoid.Studio.ModelPresetsSelector;
using VRoidCore.Common.Container;
using VRoidStudio.GUI.AvatarEditor;
using Il2Gen = Il2CppSystem.Collections.Generic;

namespace VRoidMcpBridge;

/// <summary>
/// Appliquer un objet personnalisé (custom item) depuis son fichier, comme un clic dans l'onglet « Custom » :
/// lecture du fichier (LoadCustomItemContents), conversion (DeserializeCustomItem), puis remplacement de
/// l'élément de la même catégorie (Context.ReplaceTransferableGroupAsync). Annulable avec Ctrl+Z.
/// </summary>
public static class CustomItems
{
    static FileCustomItemModel Find(string file)
    {
        var ed = UnityEngine.Object.FindObjectOfType<AvatarEditor>();
        var reg = ed?._viewModel?._mainModel?.customItemRegistry ?? throw new InvalidOperationException("VRoid is not ready yet");
        var want = System.IO.Path.GetFullPath(file);
        foreach (var kv in reg._transferableGroupTypeToFileCustomItemModelLists)
        {
            var list = kv.Value;
            if (list == null) continue;
            for (int i = 0; i < list.Count; i++)
            {
                var m = list[i];
                if (m != null && string.Equals(System.IO.Path.GetFullPath(m.FilePath), want, StringComparison.OrdinalIgnoreCase))
                    return m;
            }
        }
        throw new ArgumentException($"custom item unknown to VRoid: {file}");
    }

    public static async Task<object> Apply(string file)
    {
        if (string.IsNullOrEmpty(file)) throw new ArgumentException("missing parameter: file");
        Il2CppSystem.Threading.Tasks.Task<V1CustomItemContents<VRoid.Studio.Saving.VRoidCustomItemFileMetaData>> load = null;
        string name = null, type = null;
        await MainThread.Run(() =>
        {
            var m = Find(file);
            name = m.DisplayName;
            type = m.TransferableGroupTypeId;
            load = m.LoadCustomItemContents();
            return 0;
        });
        // Le chargement du fichier se fait hors du thread principal : on attend sa fin sans bloquer VRoid.
        for (int i = 0; i < 600; i++)
        {
            if (await MainThread.Run(() => load.IsCompleted)) break;
            await Task.Delay(100);
        }
        return await MainThread.RunAsync<object>(tcs =>
        {
            if (!load.IsCompleted) throw new TimeoutException("file read timed out");
            if (load.IsFaulted) throw new InvalidOperationException("cannot read file: " + load.Exception?.Message);
            var obj = CustomItemSerializationUtil.DeserializeCustomItem(load.Result);
            try { if (obj.IsNecessarilyMigrateBodySuitsCustomItemV2()) obj.MigrateCustomItemTransferableObject(); } catch { }
            var rootId = obj.customItemMetaData.rootTransferableGroupId;
            var removing = new Il2Gen.List<string>().Cast<Il2Gen.IEnumerable<string>>();
            var fallback = new Il2Gen.List<Il2Gen.KeyValuePair<string, string>>()
                .Cast<Il2Gen.IEnumerable<Il2Gen.KeyValuePair<string, string>>>();
            VRoidApi.RequireContextPublic().ReplaceTransferableGroupAsync(rootId, obj.transferableGroups, obj.transferables,
                obj.baseCollection, removing, fallback, false, false,
                (Il2CppSystem.Action)(Action)(() => tcs.TrySetResult(new { ok = true, name, type, group = rootId, file })),
                (Il2CppSystem.Action<Il2CppSystem.Exception>)(Action<Il2CppSystem.Exception>)(e => tcs.TrySetException(new Exception(e.Message))));
        });
    }
}
