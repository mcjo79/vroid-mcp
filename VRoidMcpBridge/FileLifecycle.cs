using System;
using System.IO;
using System.Threading.Tasks;
using UnityEngine;
using VRoid.Studio;
using VRoidStudio.GUI.AvatarEditor;

namespace VRoidMcpBridge;

public sealed class LifecycleInfo
{
    public bool modelOpen { get; set; }
    public bool ready { get; set; }
    public string path { get; set; }
    public bool dirty { get; set; }
    public bool canSave { get; set; }
}

/// <summary>
/// Cycle de vie du fichier .vroid : créer un modèle depuis un template, ouvrir un fichier,
/// sauver sur place ou enregistrer sous, revenir au menu des modèles.
/// Toute lecture/écriture d'objet VRoid passe par le thread principal (MainThread.Run).
/// </summary>
public static class FileLifecycle
{
    static MainViewModel _mainVm;
    static object _editRoot;
    static volatile bool _updating;
    static volatile bool _atMenu;

    internal static void CaptureEditRoot(object vm)
    {
        _editRoot = vm;
        _atMenu = false;
    }

    internal static void LeaveEdit()
    {
        _editRoot = null;
        _atMenu = true;
    }

    internal static void OnUpdating(bool value) => _updating = value;
    internal static object EditRoot => _editRoot;
    internal static bool IsUpdating => _updating;

    static MainViewModel MainVm()
    {
        if (_mainVm == null)
        {
            var editor = UnityEngine.Object.FindObjectOfType<AvatarEditor>();
            if (editor != null) _mainVm = editor._viewModel;
        }
        return _mainVm;
    }

    public static string CurrentPath()
    {
        try
        {
            var vm = MainVm();
            return vm?.CurrentFile?.model?.path;
        }
        catch { return null; }
    }

    public static bool IsDirty()
    {
        try { return MainVm()?.ActionHandler?.IsUnSaved ?? false; }
        catch { return false; }
    }

    public static bool HasModel => !_atMenu && VRoidApi.IsModelOpen();

    public static LifecycleInfo Info()
    {
        var open = HasModel;
        var path = open ? CurrentPath() : null;
        return new LifecycleInfo
        {
            modelOpen = open,
            ready = open && VRoidApi.IsContextReady(),
            path = path,
            dirty = open && IsDirty(),
            canSave = path != null
        };
    }

    static async Task<bool> WaitUntil(Func<bool> condition, int timeoutSeconds)
    {
        var start = DateTime.UtcNow;
        while ((DateTime.UtcNow - start).TotalSeconds < timeoutSeconds)
        {
            try
            {
                if (await MainThread.Run(condition)) return true;
            }
            catch { }
            await Task.Delay(150);
        }
        return false;
    }

    static async Task WaitModelReady(int timeoutSeconds = 45)
    {
        if (await WaitUntil(() => VRoidApi.IsContextReady() && !_updating, timeoutSeconds))
        {
            await Task.Delay(600);
            if (await WaitUntil(() => VRoidApi.IsContextReady(), 5)) return;
        }
        throw new TimeoutException("The model is not ready after " + timeoutSeconds + " seconds.");
    }

    public static async Task<object> Create(string gender)
    {
        var g = (gender ?? "female").Trim().ToLowerInvariant();
        string preset, variant;
        switch (g)
        {
            case "female": preset = "Preset_F"; variant = "F00"; break;
            case "male": preset = "Preset_M"; variant = "M00"; break;
            default: throw new ArgumentException("gender must be female or male");
        }

        await MainThread.Run(() =>
        {
            if (HasModel)
                throw new InvalidOperationException("A model is already open. Save it, then return to the model menu (vroid_main_menu) before creating another.");
            var vm = MainVm();
            if (vm == null) throw new InvalidOperationException("VRoid MainViewModel not found (VRoid is not ready).");
            vm.InitializeCurrentFileAndMoveToEditRoot(preset, variant);
            return true;
        });

        await WaitModelReady();
        return new { ok = true, gender = g, preset, variant, path = (string)null };
    }

    public static async Task<object> Open(string path)
    {
        if (string.IsNullOrWhiteSpace(path)) throw new ArgumentException("missing parameter: path");
        var full = Path.GetFullPath(path);
        if (Directory.Exists(full)) throw new ArgumentException("directory path, not a .vroid file: " + full);
        if (!File.Exists(full)) throw new FileNotFoundException(".vroid file not found", full);

        await MainThread.Run(() =>
        {
            if (HasModel)
                throw new InvalidOperationException("A model is already open. Save it, then return to the model menu (vroid_main_menu) before opening another.");
            var vm = MainVm();
            if (vm == null) throw new InvalidOperationException("VRoid MainViewModel not found (VRoid is not ready).");
            _ = vm.ImportFileAndMoveToEditRoot(full, false, false);
            return true;
        });

        await WaitModelReady();
        return new { ok = true, path = full };
    }

    public static async Task<object> Save(string path)
    {
        if (!await MainThread.Run(() => HasModel))
            throw new InvalidOperationException("No model open: nothing to save.");

        if (!string.IsNullOrWhiteSpace(path))
        {
            var full = Path.GetFullPath(path);
            if (Directory.Exists(full)) throw new ArgumentException("directory path, not a .vroid file: " + full);
            var dir = Path.GetDirectoryName(full);
            if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

            var result = await MainThread.Run(() =>
            {
                var vm = MainVm();
                var mah = vm?.ActionHandler;
                if (mah == null) throw new InvalidOperationException("VRoid MainActionHandler not found.");
                return mah.SaveSync(full, true);
            }, TimeSpan.FromSeconds(30));

            if (!(result is bool ok) || !ok)
                throw new InvalidOperationException("VRoid refused to save to " + full);

            var start = DateTime.UtcNow;
            while ((DateTime.UtcNow - start).TotalSeconds < 15)
            {
                if (File.Exists(full) && new FileInfo(full).Length > 0) break;
                await Task.Delay(150);
            }
            if (!File.Exists(full) || new FileInfo(full).Length == 0)
                throw new IOException("the file was not written: " + full);

            await MainThread.Run(() =>
            {
                var vm = MainVm();
                if (vm?.CurrentFile?.model != null) vm.CurrentFile.model.path = full;
                return true;
            });
            return new { ok = true, path = full, saved = true, savedAs = true };
        }

        var current = await MainThread.Run(CurrentPath);
        if (string.IsNullOrEmpty(current))
            throw new InvalidOperationException("This model has no .vroid file yet: provide path to save it.");

        var saved = await MainThread.Run(() =>
        {
            var vm = MainVm();
            var mah = vm?.ActionHandler;
            if (mah == null) throw new InvalidOperationException("VRoid MainActionHandler not found.");
            return mah.SaveSync(current, true);
        }, TimeSpan.FromSeconds(30));
        if (!(saved is bool ok2) || !ok2)
            throw new InvalidOperationException("VRoid refused to save " + current);

        if (!await WaitUntil(() => !IsDirty(), 20))
            throw new TimeoutException("VRoid did not confirm the save (model still marked as modified).");
        return new { ok = true, path = current, saved = true, savedAs = false };
    }

    public static async Task<object> Quit(bool discard)
    {
        var state = await MainThread.Run(() => new { dirty = IsDirty(), open = HasModel });
        if (state.open && state.dirty && !discard)
            throw new InvalidOperationException(
                "Unsaved changes: save with vroid_save, or pass discard=true to quit and lose them.");

        await MainThread.Run(() =>
        {
            var mah = MainVm()?.ActionHandler;
            if (mah != null) mah.IsUnSaved = false; // avoid VRoid's unsaved-edits dialog
            return true;
        });

        // Give the HTTP/MCP response time to leave before the Unity process exits.
        _ = Task.Run(async () =>
        {
            await Task.Delay(800);
            try
            {
                await MainThread.Run(() =>
                {
                    var mah = MainVm()?.ActionHandler;
                    if (mah != null)
                    {
                        mah.IsUnSaved = false;
                        mah.Quit();
                    }
                    else Application.Quit();
                    return true;
                });
            }
            catch (Exception e) { Plugin.Logger.LogWarning($"quit failed: {e.Message}"); }

            // VRoid/BepInEx can leave a non-responsive process after Application.Quit;
            // do not leave an invisible hung VRoid behind.
            await Task.Delay(3000);
            try { System.Diagnostics.Process.GetCurrentProcess().Kill(); } catch { }
        });
        return new { ok = true, closing = true, discarded = state.open && state.dirty && discard };
    }

    public static async Task<object> MainMenu(bool discard)
    {
        var state = await MainThread.Run(() => new { open = HasModel, dirty = IsDirty() });
        if (!state.open) return new { ok = true, mainMenu = true };
        if (state.dirty && !discard)
            throw new InvalidOperationException("Unsaved changes: save with vroid_save, or pass discard=true to lose them.");

        await MainThread.Run(() =>
        {
            var mah = MainVm()?.ActionHandler;
            if (mah != null) mah.IsUnSaved = false;
            if (_editRoot == null) throw new InvalidOperationException("VRoid editor not found.");
            Interop.Invoke(_editRoot, "BackToModelSelect");
            return true;
        });

        if (!await WaitUntil(() => _atMenu || !VRoidApi.IsModelOpen(), 20))
            throw new TimeoutException("VRoid did not return to the model menu.");
        LeaveEdit();
        return new { ok = true, mainMenu = true };
    }
}
