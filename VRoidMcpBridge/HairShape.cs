using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using VRoidCore.Common.SpecificTypes;
using VRoidCore.Editing;
using VRoidCore.Editing.History.Command;
using VRoidCore.Editing.Query;

namespace VRoidMcpBridge;

/// <summary>
/// Forme des cheveux : groupes procéduraux (longueur, nombre de mèches) et groupes dessinés au pinceau
/// (allonger les mèches en déplaçant leurs points de contrôle, dupliquer un groupe pour ajouter des mèches).
/// </summary>
public static class HairShape
{
    static Context Ctx() => VRoidApi.RequireContextPublic();

    static void Exec(Context c, Il2CppInterop.Runtime.InteropTypes.Il2CppObjectBase cmd) =>
        c.ExecuteSyncCommand(cmd.Cast<ISyncCommand<Context.HistoryManagerContext, Model>>());

    static IEnumerable<string> HairTransferables(Context c)
    {
        foreach (var kv in c.GetActiveLeafTransferables())
            if ((kv.Value?.Type ?? "").Contains("Hair")) yield return kv.Key;
    }

    static List<IHairStrandPath> Strands(Model model, IHairGroupPath g)
    {
        var list = new List<IHairStrandPath>();
        foreach (var s in new GetHairGroupChildrenQuery(g).Execute(model)) if (s != null) list.Add(s);
        return list;
    }

    /// <summary>Liste les groupes de cheveux (type, nom, paramètres utiles, nombre de mèches).</summary>
    public static object Groups()
    {
        var c = Ctx();
        var model = c.ActiveModel;
        var result = new List<object>();
        foreach (var tid in HairTransferables(c))
        {
            foreach (var g in new GetHairGroupListQuery(tid).Execute(model))
            {
                if (g == null) continue;
                string name = null;
                try { name = new GetHairGroupNameQuery(g).Execute(model)?.ToString(); } catch { }
                var strands = Strands(model, g);
                if (g.TryCast<ProceduralHairGroupPath>() is { } pg)
                {
                    var ps = new GetProceduralHairGroupParameterSetQuery(pg).Execute(model);
                    var f = ps?.ProceduralFormParameterSet;
                    result.Add(new { kind = "procedural", transferable = tid, group = pg.HairGroupId, name,
                        length = f?.Length, hairCount = f?.HairCount, strands = strands.Count });
                }
                else if (g.TryCast<BrushHairGroupPath>() is { } bg)
                {
                    float total = 0;
                    foreach (var s in strands) total += StrandLength(model, s);
                    result.Add(new { kind = "brush", transferable = tid, group = bg.HairGroupId, name,
                        strands = strands.Count, meanStrandLength = strands.Count > 0 ? total / strands.Count : 0 });
                }
                else result.Add(new { kind = "?", transferable = tid, name, strands = strands.Count });
            }
        }
        return result;
    }

    static float StrandLength(Model model, IHairStrandPath s)
    {
        int n = new GetHairStrandControlPointCountQuery(s).Execute(model);
        float len = 0;
        Vector3 prev = default;
        for (int i = 0; i < n; i++)
        {
            var p = new GetHairStrandControlPointQuery(s, i).Execute(model).Point;
            if (i > 0) len += Vector3.Distance(prev, p);
            prev = p;
        }
        return len;
    }

    /// <summary>Groupe procédural : longueur et/ou nombre de mèches. Annulable.</summary>
    public static object SetProcedural(string transferable, string group, float length, int hairCount)
    {
        var c = Ctx();
        var path = new ProceduralHairGroupPath(transferable, group);
        Action<ProceduralHairGroupParameterSet> mod = ps =>
        {
            if (!float.IsNaN(length)) ps.ProceduralFormParameterSet.Length = length;
            if (hairCount > 0) ps.ProceduralFormParameterSet.HairCount = hairCount;
        };
        Exec(c, new ModifyProceduralHairGroupParameterSetCommand("mcp", path,
            (Il2CppSystem.Action<ProceduralHairGroupParameterSet>)mod, true));
        var f = new GetProceduralHairGroupParameterSetQuery(path).Execute(c.ActiveModel).ProceduralFormParameterSet;
        return new { ok = true, length = f.Length, hairCount = f.HairCount };
    }

    /// <summary>
    /// Groupe dessiné au pinceau : allonge (factor &gt; 1) ou raccourcit chaque mèche en éloignant ses points
    /// de sa racine. Une étape d'annulation par point déplacé.
    /// </summary>
    public static object ScaleBrush(string transferable, string group, float factor)
    {
        var c = Ctx();
        var model = c.ActiveModel;
        var gp = new BrushHairGroupPath(transferable, group);
        int moved = 0, strandsDone = 0;
        foreach (var s in Strands(model, gp.Cast<IHairGroupPath>()))
        {
            var bs = s.TryCast<BrushHairStrandPath>();
            if (bs == null) continue;
            int n = new GetHairStrandControlPointCountQuery(s).Execute(model);
            if (n < 2) continue;
            var pts = new ControlPoint[n];
            for (int i = 0; i < n; i++) pts[i] = new GetHairStrandControlPointQuery(s, i).Execute(model);
            var root = pts[0].Point;
            for (int i = 1; i < n; i++)
            {
                var cp = pts[i];
                cp.Point = root + (cp.Point - root) * factor;
                Exec(c, new MoveBrushHairStrandControlPointCommand(bs, i, cp));
                moved++;
            }
            strandsDone++;
        }
        return new { ok = true, strands = strandsDone, pointsMoved = moved, factor };
    }

    /// <summary>Duplique un groupe pinceau puis décale la copie (dx, dy, dz) pour créer des mèches supplémentaires.</summary>
    public static object CloneBrush(string transferable, string group, float dx, float dy, float dz)
    {
        var c = Ctx();
        var model = c.ActiveModel;
        var before = new HashSet<string>(new GetHairGroupListQuery(transferable).Execute(model)
            .Where(g => g != null).Select(g => g.TryCast<BrushHairGroupPath>()?.HairGroupId).Where(x => x != null));
        Exec(c, new CloneBrushHairGroupCommand(new BrushHairGroupPath(transferable, group)));
        model = c.ActiveModel;
        var created = new GetHairGroupListQuery(transferable).Execute(model)
            .Where(g => g != null).Select(g => g.TryCast<BrushHairGroupPath>())
            .FirstOrDefault(g => g != null && !before.Contains(g.HairGroupId));
        if (created == null) return new { ok = false, message = "copy not found after duplication" };
        int moved = 0;
        var off = new Vector3(dx, dy, dz);
        if (off != Vector3.zero)
            foreach (var s in Strands(model, created.Cast<IHairGroupPath>()))
            {
                var bs = s.TryCast<BrushHairStrandPath>();
                if (bs == null) continue;
                int n = new GetHairStrandControlPointCountQuery(s).Execute(model);
                for (int i = 0; i < n; i++)
                {
                    var cp = new GetHairStrandControlPointQuery(s, i).Execute(model);
                    cp.Point += off;
                    Exec(c, new MoveBrushHairStrandControlPointCommand(bs, i, cp));
                    moved++;
                }
            }
        return new { ok = true, newGroup = created.HairGroupId, pointsMoved = moved };
    }
}
