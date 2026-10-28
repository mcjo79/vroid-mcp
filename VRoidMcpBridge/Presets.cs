using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using VRoid.Studio;
using VRoidStudio.GUI.AvatarEditor;

namespace VRoidMcpBridge;

/// <summary>
/// Presets de VRoid (coiffures, visages, tenues, corps...) : le catalogue est tenu par PlayFabUserModel,
/// accessible depuis le composant principal AvatarEditor. Appliquer un preset = remplacer le groupe
/// correspondant, comme le font les vignettes de l'interface.
/// </summary>
public static class Presets
{
    static PlayFabUserModel Catalog()
    {
        var ed = UnityEngine.Object.FindObjectOfType<AvatarEditor>();
        var user = ed?._viewModel?._mainModel?.playFabUser;
        return user ?? throw new InvalidOperationException("catalogue des presets introuvable (VRoid pas encore prêt ?)");
    }

    /// <summary>
    /// Liste les presets. filter : texte cherché dans le nom de ressource (ex. "Hair", "Tops", "Face", "Bottoms").
    /// Seuls les presets utilisables (gratuits ou possédés) sont listés, sauf include_locked.
    /// </summary>
    public static object List(string filter, bool includeLocked, int limit)
    {
        var all = new List<(string id, string res, bool owned, int price, bool set)>();
        foreach (var kv in Catalog().GetTransferableGroupIdToPresetModel())
        {
            var p = kv.Value;
            if (p == null) continue;
            all.Add((kv.Key, p.resourceName ?? "", p.isOwned || p.priceInCoin == 0, p.priceInCoin, p.isSetItem));
        }
        var c = VRoidApi.RequireContextPublic();
        var active = new HashSet<string>();
        foreach (var kv in c.GetActiveLeafTransferableGroups()) active.Add(kv.Key);

        var q = all.Where(p => includeLocked || p.owned);
        if (!string.IsNullOrEmpty(filter))
            q = q.Where(p => p.res.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0
                             || p.id.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0);
        var items = q.OrderBy(p => p.res).ToList();
        // Catégories : le chemin de ressource ressemble à pixiv/VRoid/<Partie>/<Catégorie>/N00/<numéro>/...
        var categories = all.Select(p => Category(p.res)).Where(x => x != null).Distinct().OrderBy(x => x).ToList();
        return new
        {
            total = items.Count,
            categories,
            presets = items.Take(limit > 0 ? limit : 200).Select(p => new
            {
                id = p.id, resource = p.res, category = Category(p.res), usable = p.owned, price = p.price,
                isSet = p.set, active = active.Contains(p.id),
            }),
        };
    }

    static string Category(string res)
    {
        var parts = res.Split('/');
        int i = Array.IndexOf(parts, "N00");
        return i >= 2 ? parts[i - 2] + "/" + parts[i - 1] : (parts.Length > 3 ? parts[2] + "/" + parts[3] : null);
    }

    /// <summary>
    /// Retire un élément du modèle (vêtement, accessoire...) : son groupe et ses enfants.
    /// group = id de groupe, ou type court (ex. "Tops", "Bottoms") pour retirer tous les groupes de ce type.
    /// </summary>
    public static async Task<object> Remove(string group)
    {
        if (string.IsNullOrEmpty(group)) throw new ArgumentException("paramètre manquant : group");
        var ids = await MainThread.Run(() =>
        {
            var c = VRoidApi.RequireContextPublic();
            var list = new List<string>();
            foreach (var kv in c.GetActiveLeafTransferableGroups())
            {
                var type = c.GetActiveTransferableGroupInfo(kv.Key)?.Type ?? "";
                if (kv.Key == group || type.EndsWith("." + group, StringComparison.OrdinalIgnoreCase)) list.Add(kv.Key);
            }
            return list;
        });
        if (ids.Count == 0) throw new ArgumentException($"aucun groupe actif ne correspond à {group}");
        foreach (var id in ids)
            await MainThread.RunAsync<object>(tcs => VRoidApi.RequireContextPublic().RemoveTransferableGroupAndChildren(id,
                (Il2CppSystem.Action)(Action)(() => tcs.TrySetResult(null)),
                (Il2CppSystem.Action<Il2CppSystem.Exception>)(Action<Il2CppSystem.Exception>)(e => tcs.TrySetException(new Exception(e.Message)))));
        return new { ok = true, removed = ids };
    }

    /// <summary>Applique un preset (remplace l'élément de la même catégorie). Annulable avec Ctrl+Z.</summary>
    public static Task<object> Apply(string id, bool preserveMaterial) => MainThread.RunAsync<object>(tcs =>
    {
        if (string.IsNullOrEmpty(id)) throw new ArgumentException("paramètre manquant : id");
        var cat = Catalog().GetTransferableGroupIdToPresetModel();
        if (!cat.ContainsKey(id)) throw new ArgumentException($"preset inconnu : {id}");
        var p = cat[id];
        if (!(p.isOwned || p.priceInCoin == 0))
            throw new InvalidOperationException("preset payant non possédé : à acheter dans VRoid d'abord");
        var c = VRoidApi.RequireContextPublic();
        c.LoadAndReplaceTransferableGroup(id,
            (Il2CppSystem.Action)(Action)(() => tcs.TrySetResult(new { ok = true, id, resource = p.resourceName })),
            (Il2CppSystem.Action<Il2CppSystem.Exception>)(Action<Il2CppSystem.Exception>)(e => tcs.TrySetException(new Exception(e.Message))),
            preserveMaterial);
    });
}
