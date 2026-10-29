using System;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;
using Il2CppInterop.Runtime.Injection;
using UnityEngine;
using VRoid.Studio.Component;

namespace VRoidMcpBridge;

[BepInPlugin(Guid, "VRoid MCP Bridge", "0.13.0")]
public class Plugin : BasePlugin
{
    public const string Guid = "dev.vroid.mcpbridge";
    public const int Port = 7811;
    internal static ManualLogSource Logger;
    HttpBridge _http;

    public override void Load()
    {
        Logger = Log;
        MainThread.Pump("Plugin.Load"); // fixe le thread principal et capture la file de tâches Unity
        ClassInjector.RegisterTypeInIl2Cpp<MainThread>();
        var comp = AddComponent<MainThread>();
        UnityEngine.Object.DontDestroyOnLoad(comp.gameObject);
        comp.gameObject.hideFlags = HideFlags.HideAndDontSave;

        // Seconde source de "ticks" : tourne à chaque frame quand un modèle est ouvert.
        var harmony = new Harmony(Guid);
        harmony.PatchAll(typeof(Plugin).Assembly);
        LifecycleHooks.Patch(harmony);
        VrmExportProbe.Patch(harmony);

        _http = new HttpBridge(Port);
        _http.Start();
        Log.LogInfo($"VRoid MCP Bridge en écoute sur http://127.0.0.1:{Port}/");
    }

    public override bool Unload()
    {
        _http?.Stop();
        return true;
    }
}

[HarmonyPatch(typeof(VRoidCoreModelUpdater), nameof(VRoidCoreModelUpdater.LateUpdate))]
static class ModelUpdaterTick
{
    static void Postfix() => MainThread.Pump("ModelUpdater.LateUpdate");
}

/// <summary>Exécute du code sur le thread principal d'Unity (obligatoire pour toucher au modèle).</summary>
public class MainThread : MonoBehaviour
{
    static readonly ConcurrentQueue<Action> Queue = new();
    static int _mainThreadId = -1;
    public static DateTime LastPumpUtc { get; private set; }
    public static string LastPumpSource { get; private set; } = "none";
    public static int Pending => Queue.Count;
    // Le premier chargement de l'éditeur (shaders, interop) peut dépasser largement 10 s,
    // surtout dans une VM. Tant que l'éditeur n'a pas été chargé une fois dans la session,
    // on laisse beaucoup plus de marge pour ne pas laisser l'appel en échec au milieu
    // d'une transition d'écran (c'est ce qui figeait VRoid au premier vroid_create).
    static readonly TimeSpan WarmTimeout = TimeSpan.FromSeconds(10);
    static readonly TimeSpan ColdTimeout = TimeSpan.FromSeconds(120);
    /// <summary>Vrai dès qu'un modèle a été ouvert une première fois dans cette session.</summary>
    public static bool EditorWarm { get; set; }
    static TimeSpan Timeout => EditorWarm ? WarmTimeout : ColdTimeout;

    public MainThread(IntPtr ptr) : base(ptr) { }

    void Update() => Pump("MainThread.Update");

    // File de tâches d'Unity (UnitySynchronizationContext) : vidée par le moteur à chaque frame,
    // indépendamment des scènes et des GameObjects.
    static Il2CppSystem.Threading.SynchronizationContext _unityContext;
    public static bool HasUnityContext => _unityContext != null;

    /// <summary>À appeler depuis le thread principal : mémorise la file de tâches d'Unity.</summary>
    public static void CaptureUnityContext()
    {
        if (_unityContext != null) return;
        try { _unityContext = Il2CppSystem.Threading.SynchronizationContext.Current; }
        catch (Exception e) { Plugin.Logger.LogWarning($"SynchronizationContext indisponible : {e.Message}"); }
        if (_unityContext != null) Plugin.Logger.LogInfo("File de tâches Unity capturée.");
    }

    /// <summary>Vide la file. Appelé depuis plusieurs points ; sans effet hors du thread principal.</summary>
    public static void Pump(string source)
    {
        var tid = Thread.CurrentThread.ManagedThreadId;
        if (_mainThreadId == -1) _mainThreadId = tid;
        if (tid != _mainThreadId) return;
        CaptureUnityContext();
        // VRoid suspend sa boucle quand la fenêtre n'a pas le focus : l'IA travaille justement
        // pendant que l'utilisateur est dans une autre fenêtre. Le mode minimisé/arrière-plan
        // est le seul mode supporté (testé) ; pas de bascule foreground.
        if (!Application.runInBackground) Application.runInBackground = true;
        LastPumpUtc = DateTime.UtcNow;
        LastPumpSource = source;
        for (int i = 0; i < 32 && Queue.TryDequeue(out var a); i++) a();
    }

    public static Task<T> Run<T>(Func<T> fn, TimeSpan? timeout = null) =>
        RunAsync<T>(tcs => tcs.SetResult(fn()), timeout);

    /// <summary>Pour les API asynchrones de VRoid (callbacks onSuccess/onError).</summary>
    public static async Task<T> RunAsync<T>(Action<TaskCompletionSource<T>> start, TimeSpan? timeout = null)
    {
        var tcs = new TaskCompletionSource<T>(TaskCreationOptions.RunContinuationsAsynchronously);
        Queue.Enqueue(() =>
        {
            try { start(tcs); }
            catch (Exception e) { tcs.TrySetException(e); }
        });
        if (_unityContext != null)
        {
            // Le thread appelant doit être connu d'IL2CPP avant d'appeler du code du jeu.
            Il2CppInterop.Runtime.IL2CPP.il2cpp_thread_attach(Il2CppInterop.Runtime.IL2CPP.il2cpp_domain_get());
            Action<Il2CppSystem.Object> cb = _ => Pump("UnitySynchronizationContext");
            _unityContext.Post(cb, null);
        }
        var limit = timeout ?? Timeout;
        var done = await Task.WhenAny(tcs.Task, Task.Delay(limit));
        if (done != tcs.Task)
            throw new TimeoutException($"The VRoid main thread did not respond within {limit.TotalSeconds:0} s " +
                                       $"(dernier tick : {LastPumpSource}, {LastPumpUtc:HH:mm:ss} UTC).");
        return await tcs.Task;
    }
}
