using System;
using UnityEngine;
using VRoid.UI.Component;

namespace VRoidMcpBridge;

/// <summary>
/// Clean 3D preview capture: render the avatar camera into our own RenderTexture, with optional
/// MSAA and supersampling (SSAA), then read/downsample and encode a PNG. Unlike ScreenCapture this
/// does not include VRoid's UI panels.
/// </summary>
public static class PreviewCapture
{
    public sealed class Result
    {
        public byte[] png;
        public int width;
        public int height;
        public int msaa;
        public int ssaa;
        public string camera;
    }

    static Camera FindPreviewCamera()
    {
        Camera fallback = null;
        try
        {
            foreach (var cam in Camera.allCameras)
            {
                if (cam == null || cam.targetTexture == null) continue;
                if (cam.name == "NormalLayerCamera") return cam;
                fallback ??= cam;
            }
        }
        catch { }
        if (fallback != null) return fallback;

        try
        {
            var ac = UnityEngine.Object.FindObjectOfType<AvatarCameraPosition>();
            if (ac != null)
            {
                var cam = Interop.Get(ac, "_unityCamera") as Camera;
                if (cam != null) return cam;
            }
        }
        catch { }
        return null;
    }

    static Texture2D ReadTexture(RenderTexture rt)
    {
        var prev = RenderTexture.active;
        RenderTexture.active = rt;
        var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
        try
        {
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            tex.Apply();
            return tex;
        }
        finally
        {
            RenderTexture.active = prev;
        }
    }

    /// <summary>
    /// Capture the 3D camera only. width/height=0 keeps the camera's viewport size. msaa 1..8,
    /// ssaa 1..3 (SSAA is applied before the final downsample). Returns the PNG bytes and metadata;
    /// throws when no avatar camera can be found (caller can fall back to ScreenCapture).
    /// </summary>
    public static Result Capture(int width = 0, int height = 0, int msaa = 4, int ssaa = 2)
    {
        var cam = FindPreviewCamera();
        if (cam == null) throw new InvalidOperationException("No VRoid 3D preview camera found");

        int srcW = cam.targetTexture != null ? cam.targetTexture.width : cam.pixelWidth;
        int srcH = cam.targetTexture != null ? cam.targetTexture.height : cam.pixelHeight;
        if (srcW <= 0) srcW = 1280;
        if (srcH <= 0) srcH = 720;
        int outW = width > 0 ? width : srcW;
        int outH = height > 0 ? height : srcH;
        outW = Math.Clamp(outW, 64, 4096);
        outH = Math.Clamp(outH, 64, 4096);
        const long MaxPixels = 16_000_000;
        long outputArea = (long)outW * outH;
        if (outputArea > MaxPixels)
        {
            double f = Math.Sqrt((double)MaxPixels / outputArea);
            outW = Math.Max(64, (int)(outW * f));
            outH = Math.Max(64, (int)(outH * f));
        }
        int factor = Math.Clamp(ssaa, 1, 3);
        while (factor > 1 && (long)outW * factor * outH * factor > MaxPixels) factor--;
        int samples = Math.Clamp(msaa, 1, 8);
        int rw = outW * factor, rh = outH * factor;

        var desc = new RenderTextureDescriptor(rw, rh, RenderTextureFormat.ARGB32, 24)
        {
            msaaSamples = samples,
        };
        var rt = new RenderTexture(desc);
        rt.Create();
        var resolved = RenderTexture.GetTemporary(rw, rh, 0, RenderTextureFormat.ARGB32);
        Texture2D hi = null, down = null;
        var prevTarget = cam.targetTexture;
        var prevAllowMsaa = cam.allowMSAA;
        var prevAspect = cam.aspect;
        try
        {
            cam.targetTexture = rt;
            cam.allowMSAA = samples > 1;
            cam.aspect = (float)outW / outH;
            cam.Render();

            // Resolve MSAA into a normal texture that ReadPixels can use.
            Graphics.Blit(rt, resolved);
            hi = ReadTexture(resolved);

            Texture2D final = hi;
            if (factor > 1)
            {
                var downRt = RenderTexture.GetTemporary(outW, outH, 0, RenderTextureFormat.ARGB32);
                try
                {
                    hi.filterMode = FilterMode.Bilinear;
                    Graphics.Blit(hi, downRt);
                    down = ReadTexture(downRt);
                    final = down;
                }
                finally { RenderTexture.ReleaseTemporary(downRt); }
            }

            // ReadPixels from the camera RT is already top-down in this Unity build.
            var png = (byte[])ImageConversion.EncodeToPNG(final);
            return new Result
            {
                png = png,
                width = outW,
                height = outH,
                msaa = samples,
                ssaa = factor,
                camera = cam.name,
            };
        }
        finally
        {
            cam.targetTexture = prevTarget;
            cam.allowMSAA = prevAllowMsaa;
            cam.aspect = prevAspect;
            if (hi != null) UnityEngine.Object.Destroy(hi);
            if (down != null) UnityEngine.Object.Destroy(down);
            RenderTexture.ReleaseTemporary(resolved);
            rt.Release();
            UnityEngine.Object.Destroy(rt);
        }
    }
}
