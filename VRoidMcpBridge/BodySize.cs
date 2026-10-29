using System;
using System.Collections.Generic;
using UnityEngine;
using VRoid.Studio.Component;

namespace VRoidMcpBridge;

/// <summary>Mesure la hauteur du modèle (en mètres, d'après les maillages affichés).</summary>
public static class BodySize
{
    public static object Measure()
    {
        VRoidApi.RequireContextPublic();
        var renderers = new List<Renderer>();
        foreach (var u in UnityEngine.Object.FindObjectsOfType<VRoidCoreModelUpdater>())
            foreach (var r in u.GetComponentsInChildren<SkinnedMeshRenderer>(false)) renderers.Add(r);
        string source = "updater";
        if (renderers.Count == 0)
        {
            source = "scene";
            foreach (var r in UnityEngine.Object.FindObjectsOfType<SkinnedMeshRenderer>()) if (r.enabled && r.gameObject.activeInHierarchy) renderers.Add(r);
        }
        if (renderers.Count == 0) throw new InvalidOperationException("no mesh found");
        float minY = float.MaxValue, maxY = float.MinValue;
        float minX = float.MaxValue, maxX = float.MinValue;
        float minZ = float.MaxValue, maxZ = float.MinValue;
        foreach (var r in renderers)
        {
            var b = r.bounds;
            minY = Math.Min(minY, b.min.y); maxY = Math.Max(maxY, b.max.y);
            minX = Math.Min(minX, b.min.x); maxX = Math.Max(maxX, b.max.x);
            minZ = Math.Min(minZ, b.min.z); maxZ = Math.Max(maxZ, b.max.z);
        }
        // Repères osseux (sans les cheveux) si un Animator humanoïde est présent.
        float? headY = null, footY = null;
        var anim = UnityEngine.Object.FindObjectOfType<Animator>();
        if (anim != null && anim.isHuman)
        {
            var head = anim.GetBoneTransform(HumanBodyBones.Head);
            var foot = anim.GetBoneTransform(HumanBodyBones.LeftFoot);
            if (head != null) headY = head.position.y;
            if (foot != null) footY = foot.position.y;
        }
        return new
        {
            source, renderers = renderers.Count,
            boundsMinY = minY, boundsMaxY = maxY, boundsHeightM = maxY - minY,
            boundsMinX = minX, boundsMaxX = maxX, centerX = (minX + maxX) / 2f,
            boundsMinZ = minZ, boundsMaxZ = maxZ, centerZ = (minZ + maxZ) / 2f,
            headY, footY
        };
    }
}
