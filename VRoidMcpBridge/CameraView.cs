using System;
using UnityEngine;
using VRoid.UI.Component;

namespace VRoidMcpBridge;

/// <summary>
/// Caméra de la vue 3D (composant AvatarCameraPosition de VRoid) : lire/changer les angles, tourner,
/// zoomer, décaler, revenir à la vue initiale, rotations prédéfinies de VRoid.
/// </summary>
public static class CameraView
{
    static AvatarCameraPosition Cam()
    {
        AvatarCameraPosition best = null;
        foreach (var c in UnityEngine.Object.FindObjectsOfType<AvatarCameraPosition>())
            if (c.isActiveAndEnabled) { best = c; break; }
        return best ?? throw new InvalidOperationException("VRoid 3D camera not found");
    }

    static object State(AvatarCameraPosition c)
    {
        var a = c.GetAngles();
        var t = c.transform;
        return new
        {
            angles = new { x = a.x, y = a.y },
            position = new { t.position.x, t.position.y, t.position.z },
            rotationCenter = new { c._rotationCenter.x, c._rotationCenter.y, c._rotationCenter.z },
            rotationModes = Enum.GetNames(typeof(AvatarCameraPosition.CameraRotationMode)),
        };
    }

    /// <summary>
    /// action : get | angles (x,y absolus, en degrés) | rotate (dx,dy relatifs) | zoom (d) | pan (x,y) |
    /// reset | mode (nom d'une rotation prédéfinie de VRoid) | projection (perspective/orthographique) |
    /// custom (px,py,pz = position, cx,cy,cz = centre de rotation).
    /// </summary>
    public static object Run(string action, Func<string, float, float> f, string mode)
    {
        var c = Cam();
        switch ((action ?? "get").ToLowerInvariant())
        {
            case "get": break;
            case "angles": c.ChangeAngles(new Vector2(f("x", float.NaN), f("y", float.NaN))); break;
            case "rotate":
            {
                var a = c.GetAngles();
                c.ChangeAngles(new Vector2(a.x + f("dx", 0), a.y + f("dy", 0)));
                break;
            }
            case "zoom": c.Zoom(f("d", float.NaN)); break;
            case "pan": c.Pan(new Vector2(f("x", 0), f("y", 0))); break;
            case "reset": c.ResetPosition(); break;
            case "projection": c.SwitchCameraProjection(); break;
            case "mode":
                if (!Enum.TryParse<AvatarCameraPosition.CameraRotationMode>(mode, true, out var m))
                    throw new ArgumentException($"unknown rotation mode: {mode} (see rotationModes)");
                c.RotateAxis(m);
                break;
            case "custom":
                c.SetCustomView(new Vector3(f("px", float.NaN), f("py", float.NaN), f("pz", float.NaN)),
                    new Vector3(f("cx", float.NaN), f("cy", float.NaN), f("cz", float.NaN)));
                break;
            default: throw new ArgumentException($"unknown camera action: {action}");
        }
        return State(c);
    }
}
