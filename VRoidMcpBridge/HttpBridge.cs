using System;
using System.IO;
using System.Net;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;

namespace VRoidMcpBridge;

/// <summary>
/// Petit serveur HTTP local (127.0.0.1 uniquement). Chaque route renvoie du JSON.
/// GET  /status
/// GET  /groups
/// GET  /params?group=ID
/// POST /set_blendshape {group, key, value}
/// POST /set_bone       {group, key, value}
/// POST /set_color      {group, key, r, g, b, a?}
/// POST /undo, /redo
/// POST /screenshot     {path?}
/// </summary>
public class HttpBridge
{
    readonly HttpListener _listener = new();
    Thread _thread;
    volatile bool _running;

    public HttpBridge(int port) => _listener.Prefixes.Add($"http://127.0.0.1:{port}/");

    public void Start()
    {
        _listener.Start();
        _running = true;
        _thread = new Thread(Loop) { IsBackground = true, Name = "VRoidMcpBridge.Http" };
        _thread.Start();
    }

    public void Stop()
    {
        _running = false;
        try { _listener.Stop(); } catch { }
    }

    void Loop()
    {
        while (_running)
        {
            HttpListenerContext ctx;
            try { ctx = _listener.GetContext(); }
            catch { if (!_running) return; continue; }
            _ = Task.Run(() => Handle(ctx));
        }
    }

    static readonly JsonSerializerOptions Json = new() { WriteIndented = false };

    async Task Handle(HttpListenerContext ctx)
    {
        object result;
        int code = 200;
        try
        {
            var req = ctx.Request;
            JsonNode body = null;
            if (req.HasEntityBody)
            {
                using var sr = new StreamReader(req.InputStream, Encoding.UTF8);
                var text = await sr.ReadToEndAsync();
                if (!string.IsNullOrWhiteSpace(text)) body = JsonNode.Parse(text);
            }
            string Q(string name) => req.QueryString[name] ?? body?[name]?.ToString();
            float F(string name, float def = float.NaN)
            {
                var n = body?[name];
                if (n != null) return n.GetValue<float>();
                var s = req.QueryString[name];
                if (s != null) return float.Parse(s, System.Globalization.CultureInfo.InvariantCulture);
                if (float.IsNaN(def)) throw new ArgumentException($"missing parameter: {name}");
                return def;
            }

            bool? B(string name) => Q(name) is { } v ? string.Equals(v, "true", StringComparison.OrdinalIgnoreCase) || v == "1" : null;
            int? I(string name) => Q(name) is { } v ? (int)Math.Round(double.Parse(v, System.Globalization.CultureInfo.InvariantCulture)) : null;

            result = req.Url.AbsolutePath.TrimEnd('/') switch
            {
                // Répondu directement par le thread HTTP : utile quand le thread principal ne répond pas.
                "/debug" => new
                {
                    lastPumpUtc = MainThread.LastPumpUtc.ToString("o"),
                    lastPumpSource = MainThread.LastPumpSource,
                    secondsSinceLastPump = (DateTime.UtcNow - MainThread.LastPumpUtc).TotalSeconds,
                    pending = MainThread.Pending,
                    unityContext = MainThread.HasUnityContext,
                },
                "" or "/status" => await MainThread.Run(VRoidApi.Status),
                "/selftest" => await MainThread.Run(VRoidApi.SelfTest),
                "/groups" => await MainThread.Run(VRoidApi.Groups),
                "/params" => await MainThread.Run(() => VRoidApi.Params(Q("group"))),
                "/set_blendshape" => await MainThread.Run(() => VRoidApi.SetBlendShape(Q("group"), Q("key"), F("value"))),
                "/set_bone" => await MainThread.Run(() => VRoidApi.SetBone(Q("group"), Q("key"), F("value"))),
                "/set_color" => await MainThread.Run(() => VRoidApi.SetColor(Q("group"), Q("key"), F("r"), F("g"), F("b"), F("a", 1f))),
                "/layers" => await MainThread.Run(() => Textures.Layers(Q("group"))),
                "/export_layer" => await MainThread.Run(() => Textures.Export(Q("transferable"), Q("image"), Q("node"), Q("path"))),
                "/import_layer" => await MainThread.Run(() => Textures.Import(Q("transferable"), Q("image"), Q("node"), Q("path"),
                    string.Equals(Q("as_new_layer"), "true", StringComparison.OrdinalIgnoreCase))),
                "/recolor_layer" => await MainThread.Run(() => Textures.Recolor(Q("transferable"), Q("image"), Q("node"),
                    F("r"), F("g"), F("b"), Q("mode"), F("strength", 1f))),
                "/hair_materials" => await MainThread.Run(Hair.Materials),
                "/set_hair_color" => await MainThread.Run(() => Hair.SetColor(Q("material"), Q("key"), F("r"), F("g"), F("b"), F("a", 1f))),
                "/hair_groups" => await MainThread.Run(HairShape.Groups),
                "/set_procedural_hair" => await MainThread.Run(() => HairShape.SetProcedural(Q("transferable"), Q("group"),
                    F("length", -1f) is var l && l < 0 ? float.NaN : l, (int)F("hair_count", 0))),
                "/scale_brush_hair" => await MainThread.Run(() => HairShape.ScaleBrush(Q("transferable"), Q("group"), F("factor"))),
                "/clone_brush_hair" => await MainThread.Run(() => HairShape.CloneBrush(Q("transferable"), Q("group"),
                    F("dx", 0), F("dy", 0), F("dz", 0))),
                "/clothing_colors" => await MainThread.Run(() => AdvancedEdit.ClothingColors(Q("group"))),
                "/begin_clothing_edit" => await MainThread.Run(() => AdvancedEdit.BeginClothingEdit(Q("group"))),
                "/measure" => await MainThread.Run(BodySize.Measure),
                "/camera" => await MainThread.Run(() => CameraView.Run(Q("action"), F, Q("mode"))),
                "/face_blendshapes" => await MainThread.Run(() => FacePreview.List(Q("filter"))),
                "/face_preview" => await MainThread.Run(() => FacePreview.Set(Q("name"), F("weight", 100f))),
                "/begin_hair_edit" => await MainThread.Run(() => Hair.BeginEdit(Q("material"))),
                "/context_state" => await MainThread.Run(ContextState.Get),
                "/create" => await FileLifecycle.Create(Q("gender")),
                "/open" => await FileLifecycle.Open(Q("path")),
                "/save" => await FileLifecycle.Save(Q("path")),
                "/main_menu" => await FileLifecycle.MainMenu(string.Equals(Q("discard"), "true", StringComparison.OrdinalIgnoreCase)),
                "/vrm_probe" => await MainThread.Run(VrmExportProbe.Info),
                "/vrm_export_options" => await VrmExport.Options_(),
                "/vrm_export_leave" => await VrmExport.Leave(),
                "/vrm_export" => await VrmExport.Export(new VrmExport.Options
                {
                    Path = Q("path"),
                    Version = Q("version") ?? "1",
                    MeshErasure = B("delete_transparent") ?? true,
                    HairCrossSection = B("hair_cross_section"),
                    HairSmoothness = I("hair_smoothness"), Hair = I("hair"), Face = I("face"), Body = I("body"), Outfit = I("outfit"),
                    MaterialMode = I("material_mode"), AtlasResolution = I("atlas_resolution"),
                    CombineHair = B("combine_hair"), TextureMode = I("texture_mode"), HairBones = I("hair_bones"),
                    Title = Q("title"), Author = Q("author"), ModelVersion = Q("model_version"),
                    Leave = B("leave") ?? true,
                    TimeoutSec = I("timeout") ?? 600,
                }),
                "/exit" => await FileLifecycle.Quit(string.Equals(Q("discard"), "true", StringComparison.OrdinalIgnoreCase)),
                "/load_group" => await ContextState.Guarded(() => Presets.LoadGroup(Q("id"))),
                "/apply_custom" => await ContextState.Guarded(() => CustomItems.Apply(Q("file"))),
                "/remove_group" => await ContextState.Guarded(() => Presets.Remove(Q("group"))),
                "/custom_items" => await MainThread.Run(Catalog.CustomItems),
                "/preset_thumbnail" => await MainThread.Run(() => Catalog.PresetThumbnail(Q("resource"), Q("path"))),
                "/presets" => await MainThread.Run(() => Presets.List(Q("filter"),
                    string.Equals(Q("include_locked"), "true", StringComparison.OrdinalIgnoreCase), (int)F("limit", 200))),
                "/apply_preset" => await ContextState.Guarded(() => Presets.Apply(Q("id"),
                    string.Equals(Q("preserve_material"), "true", StringComparison.OrdinalIgnoreCase))),
                "/undo" => await VRoidApi.Undo(),
                "/redo" => await VRoidApi.Redo(),
                "/screenshot" => await VRoidApi.Screenshot(Q("path"),
                    (int)F("width", 0), (int)F("height", 0),
                    (int)F("msaa", 4), (int)F("ssaa", 2),
                    !string.Equals(Q("clean"), "false", StringComparison.OrdinalIgnoreCase)),
                _ => throw new FileNotFoundException("unknown route"),
            };
        }
        catch (Exception e)
        {
            code = e is FileNotFoundException ? 404 : 500;
            result = new { error = e.GetType().Name, message = e.Message };
            Plugin.Logger.LogWarning($"{ctx.Request.Url.AbsolutePath}: {e}");
        }

        try
        {
            var bytes = JsonSerializer.SerializeToUtf8Bytes(result, Json);
            ctx.Response.StatusCode = code;
            ctx.Response.ContentType = "application/json; charset=utf-8";
            await ctx.Response.OutputStream.WriteAsync(bytes);
            ctx.Response.Close();
        }
        catch { }
    }
}
