using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Il2CppInterop.Runtime.InteropTypes;
using VRoidStudio.GUI.AvatarEditor;
using VRoidStudio.GUI.AvatarEditor.PhotoBooth;
using VRoidStudio.PhotoBooth;

namespace VRoidMcpBridge;

/// <summary>
/// VRM export without UI clicks or the Windows file dialog.
/// Opens VRoid's own "Export as VRM" screen (EditRoot.EnterToVRMExport), sets the same options
/// the screen shows (ExportSettings / MeshReduction / HairBoneReduction), then calls the
/// path-based export VRoid uses internally (PhotoBoothViewModel.OnVRM1SettingChanged / OnVRMSettingChanged).
/// </summary>
public static class VrmExport
{
    static readonly object ExportGate = new();
    static bool _exportRunning;

    public class Options
    {
        public string Path;
        public string Version = "1";          // "1" (VRM 1.0) or "0" (VRM 0.x)
        public bool? MeshErasure = true;       // "Delete Transparent Meshes"
        public bool? HairCrossSection;
        public int? HairSmoothness, Hair, Face, Body, Outfit;   // polygon reduction sliders
        public int? MaterialMode;              // index in MaterialReductionModeItems (Default / 2 / 8 / 12)
        public int? AtlasResolution;           // index in AtlasResolutionItems
        public bool? CombineHair;              // "Combine Hair Mesh"
        public int? TextureMode;               // index in TextureCompressionModeItems (Original / Shrunk)
        public int? HairBones;                 // "Reduce Bones: Hair" strength
        public string Title, Author, ModelVersion;
        public bool Leave = true;              // go back to the editor afterwards
        public int TimeoutSec = 600;
    }

    static PhotoBoothViewModel PhotoBooth()
    {
        var ed = UnityEngine.Object.FindObjectOfType<AvatarEditor>();
        return ed?._instantiatedPhotoBoothViewModel;
    }

    static bool InExportMode(PhotoBoothViewModel pb) =>
        pb != null && pb.ExportSettings != null && pb.PreviewAvatar != null;

    static object Item(Il2CppSystem.Object o, int i)
    {
        string name = null;
        try { name = (string)Interop.Get(o, "TranslatedDisplayName"); } catch { }
        object val = null;
        foreach (var p in new[] { "MaterialReductionMode", "TextureCompressionMode", "AtlasResolution" })
        {
            try { var v = Interop.Get(o, p); if (v != null) { val = v.ToString(); break; } } catch { }
        }
        return new { index = i, name, value = val };
    }

    static List<object> Items<T>(Il2CppSystem.Collections.Generic.List<T> list) where T : Il2CppObjectBase
    {
        var r = new List<object>();
        if (list == null) return r;
        for (int i = 0; i < list.Count; i++) r.Add(Item(list[i].Cast<Il2CppSystem.Object>(), i));
        return r;
    }

    static object Snapshot(PhotoBoothViewModel pb)
    {
        var s = pb.ExportSettings;
        var m = s.MeshReduction;
        var meta1 = s.VRM10MetaData;
        var meta0 = s.VRM0MetaData;
        return new
        {
            meshErasure = m?.MeshErasure,
            hairCrossSection = m?.HairCrossSection,
            hairSmoothness = m?.HairSmoothnessRate,
            hair = m?.HairReductionStrength,
            face = m?.FaceReductionStrength,
            body = m?.BodyReductionStrength,
            outfit = m?.ClothingReductionStrength,
            hairBones = s.hairBoneReduction?.HairReductionStrength,
            combineHair = s.IsEnableHairCombination,
            materialMode = s.MaterialReductionModeIndex,
            textureMode = s.TextureCompressionModeIndex,
            atlasResolution = s.AtlasResolutionIndex,
            materialModes = Items(s.MaterialReductionModeItems),
            textureModes = Items(s.TextureCompressionModeItems),
            atlasResolutions = Items(s.AtlasResolutionItems),
            vrm1Meta = meta1 == null ? null : new { name = meta1.Name, version = meta1.Version, authors = meta1.Authors == null ? null : string.Join(", ", ToArray(meta1.Authors)) },
            vrm0Meta = meta0 == null ? null : new { title = meta0.title, version = meta0.version, author = meta0.author },
        };
    }

    static string[] ToArray(Il2CppSystem.Collections.Generic.List<string> l)
    {
        var a = new string[l.Count];
        for (int i = 0; i < l.Count; i++) a[i] = l[i];
        return a;
    }

    /// <summary>
    /// Opens VRoid's export screen and waits until its preview avatar exists.
    /// With fresh=true an already open screen is closed first: after an export its mesh
    /// reduction lists point to destroyed objects and the sliders would fail.
    /// </summary>
    static async Task EnsureExportScreen(bool fresh, int timeoutMs = 60000)
    {
        if (VrmExportProbe.ScreenActive)
        {
            if (!fresh) { await WaitPreview(); return; }
            await LeaveExportScreen();
        }
        await MainThread.Run(() =>
        {
            var root = FileLifecycle.EditRoot as Il2CppObjectBase
                       ?? throw new InvalidOperationException("Editor screen not available: open a model first.");
            root.Cast<VRoid.Studio.EditRootScreen.ViewModel>().EnterToVRMExport();
            return true;
        });
        var start = DateTime.UtcNow;
        while ((DateTime.UtcNow - start).TotalMilliseconds < timeoutMs)
        {
            if (VrmExportProbe.ScreenActive && await MainThread.Run(() => InExportMode(PhotoBooth()))) break;
            await Task.Delay(200);
        }
        if (!VrmExportProbe.ScreenActive || !await MainThread.Run(() => InExportMode(PhotoBooth())))
            throw new TimeoutException("VRoid's export screen did not open.");
        await WaitPreview();
    }

    /// <summary>Waits until the export preview (mesh/material reduction) has been recomputed.</summary>
    static async Task WaitPreview(int timeoutMs = 120000)
    {
        await Task.Delay(500);
        var start = DateTime.UtcNow;
        int calm = 0;
        while ((DateTime.UtcNow - start).TotalMilliseconds < timeoutMs)
        {
            bool busy = await MainThread.Run(() =>
            {
                var pb = PhotoBooth();
                return pb == null || pb._isBlockingUpdateExportPreview || pb.waitForPointerUpAndUpdateExportPreview != null
                       || FileLifecycle.IsUpdating;
            });
            calm = busy ? 0 : calm + 1;
            if (calm >= 4) return;
            await Task.Delay(250);
        }
    }

    public static async Task<object> Options_()
    {
        await EnsureExportScreen(fresh: false);
        return await MainThread.Run(() => (object)new { exportScreenOpen = true, settings = Snapshot(PhotoBooth()) });
    }

    public static async Task<object> Export(Options o)
    {
        lock (ExportGate)
        {
            if (_exportRunning)
                throw new InvalidOperationException("A VRM export is already running; wait for it to finish before starting another one.");
            _exportRunning = true;
        }
        try
        {
            return await ExportCore(o);
        }
        finally
        {
            lock (ExportGate) _exportRunning = false;
        }
    }

    static async Task<object> ExportCore(Options o)
    {
        if (string.IsNullOrWhiteSpace(o.Path)) throw new ArgumentException("missing parameter: path");
        var full = System.IO.Path.GetFullPath(o.Path);
        if (!full.EndsWith(".vrm", StringComparison.OrdinalIgnoreCase)) full += ".vrm";
        var dir = System.IO.Path.GetDirectoryName(full);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        bool vrm1 = o.Version is not ("0" or "0.0" or "0.x" or "vrm0");
        var before = File.Exists(full) ? File.GetLastWriteTimeUtc(full) : DateTime.MinValue;

        // Options not given fall back to VRoid's defaults (VRoid itself remembers the last export).
        o.MeshErasure ??= true; o.HairCrossSection ??= false; o.CombineHair ??= true;
        o.HairSmoothness ??= 0; o.Hair ??= 0; o.Face ??= 0; o.Body ??= 0; o.Outfit ??= 0; o.HairBones ??= 0;
        o.MaterialMode ??= 0; o.AtlasResolution ??= 0; o.TextureMode ??= 0;

        // 1. Set the options, then reopen the screen: polygon reduction is only rebuilt into the
        //    exported meshes when VRoid loads the saved settings as the screen opens.
        await EnsureExportScreen(fresh: true);
        await ApplyOptions(o);
        await EnsureExportScreen(fresh: true);
        var mismatch = await MainThread.Run(() => Mismatch(o));
        if (mismatch.Count > 0) { await ApplyOptions(o); mismatch = await MainThread.Run(() => Mismatch(o)); }

        // 2. Export to the path, like VRoid does after its settings dialog, but without the file picker.
        var tcs = await MainThread.Run(() =>
        {
            var pb = PhotoBooth();
            var s = pb.ExportSettings;
            var t = new Il2CppSystem.Threading.Tasks.TaskCompletionSource<bool>();
            if (vrm1)
            {
                var meta = s.VRM10MetaData ?? new UniVRM10.VRM10ObjectMeta();
                if (!string.IsNullOrWhiteSpace(o.Title) || string.IsNullOrWhiteSpace(meta.Name))
                    meta.Name = !string.IsNullOrWhiteSpace(o.Title) ? o.Title : System.IO.Path.GetFileNameWithoutExtension(full);
                if (!string.IsNullOrWhiteSpace(o.ModelVersion)) meta.Version = o.ModelVersion;
                if (meta.Authors == null) meta.Authors = new Il2CppSystem.Collections.Generic.List<string>();
                if (!string.IsNullOrWhiteSpace(o.Author)) { meta.Authors.Clear(); meta.Authors.Add(o.Author); }
                if (meta.Authors.Count == 0) meta.Authors.Add("unknown");
                pb.OnVRM1SettingChanged(meta, full, t);
            }
            else
            {
                var meta = s.VRM0MetaData ?? new VRM.glTF_VRM_Meta();
                if (!string.IsNullOrWhiteSpace(o.Title) || string.IsNullOrWhiteSpace(meta.title))
                    meta.title = !string.IsNullOrWhiteSpace(o.Title) ? o.Title : System.IO.Path.GetFileNameWithoutExtension(full);
                if (!string.IsNullOrWhiteSpace(o.ModelVersion)) meta.version = o.ModelVersion;
                if (!string.IsNullOrWhiteSpace(o.Author)) meta.author = o.Author;
                if (string.IsNullOrWhiteSpace(meta.author)) meta.author = "unknown";
                pb.OnVRMSettingChanged(meta, full, t);
            }
            return t;
        });

        var start = DateTime.UtcNow;
        bool? ok = null;
        string fault = null;
        while ((DateTime.UtcNow - start).TotalSeconds < o.TimeoutSec)
        {
            var st = await MainThread.Run<(bool done, bool res, string err)>(() =>
            {
                var task = tcs.Task;
                if (!task.IsCompleted) return (done: false, res: false, err: (string)null);
                if (task.IsFaulted) return (true, false, task.Exception?.ToString() ?? "faulted");
                if (task.IsCanceled) return (true, false, "canceled");
                return (true, task.Result, null);
            });
            if (st.done) { ok = st.res; fault = st.err; break; }
            await Task.Delay(250);
        }

        // The export task completes before VRoid's cleanup/coroutines are necessarily done.
        // Leave the screen too early and VRoid can log "Coroutine continue failure" or close;
        // wait for the file to be stable, then give the screen one more idle interval.
        await Task.Delay(1200);
        await WaitFileStable(full);
        await Task.Delay(800);

        var settings = await MainThread.Run(() => Snapshot(PhotoBooth()));
        bool written = File.Exists(full) && File.GetLastWriteTimeUtc(full) > before;
        long size = written ? new FileInfo(full).Length : 0;

        bool left = false;
        if (o.Leave) left = await LeaveExportScreen();

        if (ok == null) throw new TimeoutException($"Export still running after {o.TimeoutSec}s (file written: {written}).");
        if (ok == false || !written)
            throw new InvalidOperationException($"VRoid reported a failed export ({fault ?? "result=false"}), file written: {written}.");
        return new { ok = true, path = full, version = vrm1 ? "1.0" : "0.x", bytes = size,
                     elapsedSec = Math.Round((DateTime.UtcNow - start).TotalSeconds, 1), leftExportScreen = left, warnings = mismatch, settings };
    }

    static async Task WaitFileStable(string path, int timeoutMs = 30000)
    {
        var start = DateTime.UtcNow;
        long last = -1;
        int stable = 0;
        while ((DateTime.UtcNow - start).TotalMilliseconds < timeoutMs)
        {
            long len = File.Exists(path) ? new FileInfo(path).Length : 0;
            if (len > 0 && len == last) stable++;
            else { stable = 0; last = len; }
            if (stable >= 5) return;
            await Task.Delay(200);
        }
    }

    static async Task ApplyOptions(Options o)
    {
        await MainThread.Run(() =>
        {
            var m = PhotoBooth().ExportSettings.MeshReduction;
            if (m.MeshErasure != o.MeshErasure.Value) m.MeshErasure = o.MeshErasure.Value;
            if (m.HairCrossSection != o.HairCrossSection.Value) m.HairCrossSection = o.HairCrossSection.Value;
            if (m.HairSmoothnessRate != o.HairSmoothness.Value) m.HairSmoothnessRate = o.HairSmoothness.Value;
            if (m.HairReductionStrength != o.Hair.Value) m.HairReductionStrength = o.Hair.Value;
            if (m.FaceReductionStrength != o.Face.Value) m.FaceReductionStrength = o.Face.Value;
            if (m.BodyReductionStrength != o.Body.Value) m.BodyReductionStrength = o.Body.Value;
            if (m.ClothingReductionStrength != o.Outfit.Value) m.ClothingReductionStrength = o.Outfit.Value;
            return true;
        });
        await WaitPreview();
        await MainThread.Run(() =>
        {
            var s = PhotoBooth().ExportSettings;
            if (s.hairBoneReduction != null && s.hairBoneReduction.HairReductionStrength != o.HairBones.Value)
                s.hairBoneReduction.HairReductionStrength = o.HairBones.Value;
            if (s.IsEnableHairCombination != o.CombineHair.Value) s.IsEnableHairCombination = o.CombineHair.Value;
            var mm = Check(o.MaterialMode.Value, s.MaterialReductionModeItems.Count, "materialMode");
            if (s.MaterialReductionModeIndex != mm) s.MaterialReductionModeIndex = mm;
            return true;
        });
        await WaitPreview();
        await MainThread.Run(() =>
        {
            var s = PhotoBooth().ExportSettings;
            var ar = Check(o.AtlasResolution.Value, s.AtlasResolutionItems.Count, "atlasResolution");
            if (s.AtlasResolutionIndex != ar) s.AtlasResolutionIndex = ar;
            var tm = Check(o.TextureMode.Value, s.TextureCompressionModeItems.Count, "textureMode");
            if (s.TextureCompressionModeIndex != tm) s.TextureCompressionModeIndex = tm;
            // The public setter ignores "Shrunk" outside a UI interaction: write the backing field.
            if (s.TextureCompressionModeIndex != tm) s.textureCompressionModeIndex = tm;
            return true;
        });
        await WaitPreview();
    }

    static List<string> Mismatch(Options o)
    {
        var s = PhotoBooth().ExportSettings;
        var m = s.MeshReduction;
        var r = new List<string>();
        void C<T>(string n, T have, T want) { if (!Equals(have, want)) r.Add($"{n}: wanted {want}, VRoid kept {have}"); }
        C("delete_transparent", m.MeshErasure, o.MeshErasure.Value);
        C("hair_cross_section", m.HairCrossSection, o.HairCrossSection.Value);
        C("hair_smoothness", m.HairSmoothnessRate, o.HairSmoothness.Value);
        C("hair", m.HairReductionStrength, o.Hair.Value);
        C("face", m.FaceReductionStrength, o.Face.Value);
        C("body", m.BodyReductionStrength, o.Body.Value);
        C("outfit", m.ClothingReductionStrength, o.Outfit.Value);
        C("hair_bones", s.hairBoneReduction?.HairReductionStrength ?? -1, o.HairBones.Value);
        C("combine_hair", s.IsEnableHairCombination, o.CombineHair.Value);
        C("material_mode", s.MaterialReductionModeIndex, o.MaterialMode.Value);
        C("atlas_resolution", s.AtlasResolutionIndex, o.AtlasResolution.Value);
        C("texture_mode", s.TextureCompressionModeIndex, o.TextureMode.Value);
        return r;
    }

    static int Check(int i, int count, string name)
    {
        if (i < 0 || i >= count) throw new ArgumentException($"{name} must be between 0 and {count - 1}");
        return i;
    }

    static async Task<bool> LeaveExportScreen()
    {
        var screen = VrmExportProbe.ScreenVm;
        if (screen == null || !VrmExportProbe.ScreenActive) return false;
        try
        {
            await MainThread.Run(() => { Interop.Invoke(screen, "PopScreen"); return true; });
            var start = DateTime.UtcNow;
            while (VrmExportProbe.ScreenActive && (DateTime.UtcNow - start).TotalSeconds < 15) await Task.Delay(100);
            await ContextState.WaitReady();
            return !VrmExportProbe.ScreenActive;
        }
        catch (Exception e)
        {
            Plugin.Logger.LogWarning($"leave export screen: {e.Message}");
            return false;
        }
    }

    public static async Task<object> Leave() => new { left = await LeaveExportScreen() };
}
