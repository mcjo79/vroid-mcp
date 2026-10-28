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
        if (renderers.Count == 0) throw new InvalidOperationException("aucun maillage trouvé");
        float min = float.MaxValue, max = float.MinValue;
        foreach (var r in renderers)
        {
            var b = r.bounds;
            min = Math.Min(min, b.min.y); max = Math.Max(max, b.max.y);
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
        return new { source, renderers = renderers.Count, boundsMinY = min, boundsMaxY = max, boundsHeightM = max - min, headY, footY };
    }
}
