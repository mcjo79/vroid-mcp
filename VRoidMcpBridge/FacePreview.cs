using System;
using System.Collections.Generic;
using UnityEngine;

namespace VRoidMcpBridge;

/// <summary>
/// Aperçu d'expression (bouche ouverte, sourire, yeux fermés...) en pilotant directement les blendshapes du
/// maillage du visage. Affichage seulement : rien n'est enregistré dans le modèle. VRoid peut remettre les poids
/// à zéro quand il recalcule le visage ; refaire l'appel juste avant la capture.
/// </summary>
public static class FacePreview
{
    static IEnumerable<SkinnedMeshRenderer> Faces()
    {
        foreach (var r in UnityEngine.Object.FindObjectsOfType<SkinnedMeshRenderer>())
        {
            var m = r.sharedMesh;
            if (m != null && m.blendShapeCount > 0 && r.gameObject.activeInHierarchy) yield return r;
        }
    }

    /// <summary>Noms des blendshapes disponibles (filtre facultatif, ex. "MTH" pour la bouche).</summary>
    public static object List(string filter)
    {
        var res = new List<object>();
        foreach (var r in Faces())
        {
            var m = r.sharedMesh;
            var names = new List<string>();
            for (int i = 0; i < m.blendShapeCount; i++)
            {
                var n = m.GetBlendShapeName(i);
                if (string.IsNullOrEmpty(filter) || n.IndexOf(filter, StringComparison.OrdinalIgnoreCase) >= 0) names.Add(n);
            }
            if (names.Count > 0) res.Add(new { renderer = r.name, names });
        }
        return res;
    }

    /// <summary>Règle le poids (0..100) des blendshapes dont le nom contient name ; name vide + weight 0 = tout remettre à zéro.</summary>
    public static object Set(string name, float weight)
    {
        int n = 0;
        foreach (var r in Faces())
        {
            var m = r.sharedMesh;
            for (int i = 0; i < m.blendShapeCount; i++)
            {
                var bn = m.GetBlendShapeName(i);
                if (string.IsNullOrEmpty(name) ? weight == 0 : bn.EndsWith(name, StringComparison.OrdinalIgnoreCase))
                {
                    r.SetBlendShapeWeight(i, weight);
                    n++;
                }
            }
        }
        return new { ok = n > 0, changed = n, name, weight };
    }
}
