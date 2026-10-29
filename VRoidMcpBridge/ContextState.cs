using System;
using System.Threading.Tasks;

namespace VRoidMcpBridge;

/// <summary>
/// État interne du contexte d'édition de VRoid, et attente qu'il soit prêt. Certaines opérations
/// (chargement d'un élément, retrait) confirment avant que VRoid ait fini d'appliquer le résultat :
/// enchaîner trop tôt peut bloquer le contexte (« Operation is not valid due to the current state »).
/// </summary>
public static class ContextState
{
    public static object Get()
    {
        var c = VRoidApi.RequireContextPublic();
        return new
        {
            commandExecutable = c.IsCommandExecutable,
            queryExecutable = c.IsQueryExecutable,
            modifyingEditingModel = c.IsModifyingEditingModel,
            modifyingCheckingModel = c.IsModifyingCheckingModel,
            needsUpdate = c.NeedsUpdate,
            needsUpdateAvatar = c.NeedsUpdateAvatar,
            editing = c.IsEditing,
            canUndo = c.CanUndo,
            canRedo = c.CanRedo,
        };
    }

    static bool Ready()
    {
        var c = VRoidApi.RequireContextPublic();
        return c.IsCommandExecutable && !c.IsModifyingEditingModel && !c.IsModifyingCheckingModel && !c.NeedsUpdate;
    }

    /// <summary>Attend que VRoid ait fini d'appliquer la dernière modification (10 s maximum).</summary>
    public static async Task<bool> WaitReady(int timeoutMs = 10000)
    {
        var start = DateTime.UtcNow;
        while ((DateTime.UtcNow - start).TotalMilliseconds < timeoutMs)
        {
            if (await MainThread.Run(Ready)) return true;
            await Task.Delay(50);
        }
        return false;
    }

    /// <summary>Exécute une opération seulement si VRoid est prêt, puis attend qu'il le redevienne.</summary>
    public static async Task<object> Guarded(Func<Task<object>> op)
    {
        if (!await WaitReady())
            throw new InvalidOperationException("VRoid is not ready (edit in progress or context blocked): " +
                                                System.Text.Json.JsonSerializer.Serialize(await MainThread.Run(Get)));
        var r = await op();
        var ready = await WaitReady();
        return ready ? r : new { result = r, warning = "VRoid did not become ready again after the operation", state = await MainThread.Run(Get) };
    }
}
