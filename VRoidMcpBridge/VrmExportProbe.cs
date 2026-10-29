using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace VRoidMcpBridge;

/// <summary>
/// Runtime probe for VRoid's native VRM export screen. Harmony captures the screen/context
/// objects when the user opens "Export as VRM"; /vrm_probe then dumps their fields so the
/// exporter settings can be driven by the plugin instead of mouse automation.
/// </summary>
public static class VrmExportProbe
{
    static object _screenVm;
    static object _contextVm;
    static object _exportButton;
    static readonly List<string> _patchStatus = new();

    internal static object ScreenVm => _screenVm;
    internal static volatile bool ScreenActive;
    internal static void CaptureScreen(object vm) { _screenVm = vm; ScreenActive = true; }
    internal static void CaptureContext(object vm) => _contextVm = vm;
    internal static void CaptureButton(object vm) => _exportButton = vm;

    public static void Patch(Harmony harmony)
    {
        try
        {
            var screen = Interop.FindType("VRoid.Studio.VRMExportScreen.ViewModel");
            var onActivate = screen == null ? null : AccessTools.Method(screen, "OnScreenActivate");
            if (onActivate != null)
            {
                harmony.Patch(onActivate, postfix: new HarmonyMethod(
                    typeof(VrmExportProbe).GetMethod(nameof(OnScreenActivatePostfix), BindingFlags.Static | BindingFlags.NonPublic)));
                _patchStatus.Add("screen:ok");
            }
            else _patchStatus.Add("screen:missing");
            var onDeactivate = screen == null ? null : AccessTools.Method(screen, "OnScreenDeactivate");
            if (onDeactivate != null)
                harmony.Patch(onDeactivate, postfix: new HarmonyMethod(
                    typeof(VrmExportProbe).GetMethod(nameof(OnScreenDeactivatePostfix), BindingFlags.Static | BindingFlags.NonPublic)));

            var context = Interop.FindType("VRoid.Studio.XWear.Export.ExportContextViewModel");
            var ctor = context == null ? null : AccessTools.Constructor(context);
            if (ctor != null)
            {
                harmony.Patch(ctor, postfix: new HarmonyMethod(
                    typeof(VrmExportProbe).GetMethod(nameof(OnContextPostfix), BindingFlags.Static | BindingFlags.NonPublic)));
                _patchStatus.Add("context:ok");
            }
            else _patchStatus.Add("context:missing");

            var button = Interop.FindType("VRoid.Studio.XWear.Export.VrmExportButtonProperty");
            var export = button == null ? null : AccessTools.Method(button, "Export");
            if (export != null)
            {
                harmony.Patch(export, postfix: new HarmonyMethod(
                    typeof(VrmExportProbe).GetMethod(nameof(OnExportPostfix), BindingFlags.Static | BindingFlags.NonPublic)));
                _patchStatus.Add("button:ok");
            }
            else _patchStatus.Add("button:missing");
        }
        catch (Exception e) { Plugin.Logger?.LogWarning($"vrm probe patch: {e.Message}"); }
    }

    static void OnScreenActivatePostfix(object __instance) => CaptureScreen(__instance);
    static void OnScreenDeactivatePostfix() => ScreenActive = false;
    static void OnContextPostfix(object __instance) => CaptureContext(__instance);
    static void OnExportPostfix(object __instance) => CaptureButton(__instance);

    static bool Simple(Type t) =>
        t.IsPrimitive || t.IsEnum || t == typeof(string) || t == typeof(decimal) ||
        t == typeof(Vector2) || t == typeof(Vector3) || t == typeof(Color);

    static object SimpleValue(object v)
    {
        if (v == null) return null;
        if (v is string s) return s;
        if (v is Vector2 v2) return new { x = v2.x, y = v2.y };
        if (v is Vector3 v3) return new { x = v3.x, y = v3.y, z = v3.z };
        if (v is Color c) return new { r = c.r, g = c.g, b = c.b, a = c.a };
        return v.ToString();
    }

    static object Describe(string label, object o, int depth = 0)
    {
        if (o == null) return new { label, value = (object)null };
        o = Interop.RealObj(o);
        var t = o.GetType();
        if (Simple(t)) return new { label, type = t.Name, value = SimpleValue(o) };
        var fields = new Dictionary<string, object>();
        if (depth < 2)
        {
            foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            {
                if (f.IsStatic) continue;
                object v;
                try { v = f.GetValue(o); } catch { continue; }
                if (v == null) { fields[f.Name] = null; continue; }
                var vt = v.GetType();
                fields[f.Name] = Simple(vt) ? SimpleValue(v) : Describe(f.Name, v, depth + 1);
                if (fields.Count >= 40) break;
            }
            foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance))
            {
                if (p.GetIndexParameters().Length != 0) continue;
                if (fields.ContainsKey(p.Name)) continue;
                object v;
                try { v = p.GetValue(o); } catch { continue; }
                if (v == null) { fields[p.Name] = null; continue; }
                var vt = v.GetType();
                fields[p.Name] = Simple(vt) ? SimpleValue(v) : Describe(p.Name, v, depth + 1);
                if (fields.Count >= 60) break;
            }
        }
        return new { label, type = t.FullName, value = fields };
    }

    public static object Info()
    {
        var list = new List<object>();
        if (_screenVm != null) list.Add(Describe("screenVm", _screenVm));
        if (_contextVm != null) list.Add(Describe("contextVm", _contextVm));
        if (_exportButton != null) list.Add(Describe("exportButton", _exportButton));

        // Also list currently active objects whose type mentions VRMExport (view/context objects
        // are often MonoBehaviours, not the screen ViewModel).
        try
        {
            int n = 0;
            foreach (var mb in Resources.FindObjectsOfTypeAll<MonoBehaviour>())
            {
                var tn = mb.GetType().FullName ?? "";
                if (!tn.Contains("VRMExport") && !tn.Contains("Export")) continue;
                list.Add(new { label = "unityObject", type = tn, name = mb.name, active = mb.isActiveAndEnabled });
                if (++n >= 30) break;
            }
        }
        catch { }
        return new { captured = new { screen = _screenVm != null, context = _contextVm != null, button = _exportButton != null },
                     patches = _patchStatus, objects = list };
    }
}
