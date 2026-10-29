using System;
using HarmonyLib;

namespace VRoidMcpBridge;

/// <summary>
/// Capture l'écran d'édition (pour Save/MainMenu) et l'état IsUpdatingModel.
/// Les types sont résolus par nom : ils viennent de VRoid.Studio et ne sont pas exposés
/// dans toutes les versions d'interop.
/// </summary>
internal static class LifecycleHooks
{
    public static void Patch(Harmony harmony)
    {
        PatchMethod(harmony, "VRoid.Studio.EditRootScreen.ViewModel", "OnScreenActivate", nameof(OnEditRoot));
        PatchMethod(harmony, "VRoid.Studio.EditRootScreen.ViewModel", "set_EditMode", nameof(OnEditRoot));
        PatchMethod(harmony, "VRoid.Studio.EditRootScreen.ViewModel", "BackToModelSelect", nameof(OnLeave));
        PatchMethod(harmony, "VRoid.Studio.Component.VRoidCoreModelUpdater", "set_IsUpdatingModel", nameof(OnUpdating));
    }

    static void PatchMethod(Harmony harmony, string typeName, string methodName, string postfixName)
    {
        try
        {
            var type = AccessTools.TypeByName(typeName);
            if (type == null)
            {
                Plugin.Logger?.LogWarning($"hook: type {typeName} introuvable");
                return;
            }
            var method = AccessTools.Method(type, methodName);
            if (method == null)
            {
                Plugin.Logger?.LogWarning($"hook: méthode {typeName}.{methodName} introuvable");
                return;
            }
            harmony.Patch(method, postfix: new HarmonyMethod(typeof(LifecycleHooks), postfixName));
            Plugin.Logger?.LogInfo($"hook: {typeName}.{methodName}");
        }
        catch (Exception e)
        {
            Plugin.Logger?.LogWarning($"hook {typeName}.{methodName}: {e.Message}");
        }
    }

    static void OnEditRoot(object __instance) => FileLifecycle.CaptureEditRoot(__instance);
    static void OnLeave(object __instance) => FileLifecycle.LeaveEdit();
    static void OnUpdating(bool value) => FileLifecycle.OnUpdating(value);
}
