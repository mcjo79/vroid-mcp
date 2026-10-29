using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;
using Il2CppInterop.Runtime;
using Il2CppInterop.Runtime.InteropTypes;

namespace VRoidMcpBridge;

/// <summary>
/// Petits accès réflexifs aux objets IL2CPP (champs/propriétés/méthodes privés).
/// Adapté de vroid-studio-mcp (Runtime/Interop.cs, licence MIT) pour rester minimal ici.
/// </summary>
internal static class Interop
{
    const BindingFlags All = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

    static readonly Dictionary<string, Type> Types = new(StringComparer.Ordinal);

    public static Type FindType(string name)
    {
        if (string.IsNullOrEmpty(name)) return null;
        lock (Types)
        {
            if (Types.TryGetValue(name, out var cached)) return cached;
        }
        Type found = null;
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            try { found = asm.GetType(name, false); } catch { found = null; }
            if (found != null) break;
        }
        if (found == null)
        {
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                try
                {
                    found = asm.GetTypes().FirstOrDefault(t => t.FullName == name || t.Name == name);
                }
                catch (ReflectionTypeLoadException e)
                {
                    found = e.Types.Where(t => t != null).FirstOrDefault(t => t.FullName == name || t.Name == name);
                }
                catch { }
                if (found != null) break;
            }
        }
        if (found != null)
        {
            lock (Types) Types[name] = found;
        }
        return found;
    }

    static string NativeClassName(IntPtr ptr)
    {
        var klass = IL2CPP.il2cpp_object_get_class(ptr);
        var name = Marshal.PtrToStringAnsi(IL2CPP.il2cpp_class_get_name(klass));
        var ns = Marshal.PtrToStringAnsi(IL2CPP.il2cpp_class_get_namespace(klass));
        return string.IsNullOrEmpty(ns) ? name : ns + "." + name;
    }

    public static Type RealType(object o)
    {
        if (o == null) return null;
        try
        {
            if (o is Il2CppObjectBase ob)
            {
                var full = NativeClassName(ob.Pointer);
                if (!string.IsNullOrEmpty(full))
                {
                    var t = FindType(full);
                    if (t != null) return t;
                }
            }
        }
        catch { }
        return o.GetType();
    }

    public static object RealObj(object o)
    {
        if (o is not Il2CppObjectBase ob) return o;
        try
        {
            var t = RealType(o);
            if (t == null || o.GetType() == t) return o;
            if (!typeof(Il2CppObjectBase).IsAssignableFrom(t)) return o;
            var tryCast = typeof(Il2CppObjectBase).GetMethods(BindingFlags.Public | BindingFlags.Instance)
                .FirstOrDefault(m => m.Name == "TryCast" && m.IsGenericMethodDefinition && m.GetParameters().Length == 0);
            if (tryCast != null)
            {
                var r = tryCast.MakeGenericMethod(t).Invoke(o, null);
                if (r != null) return r;
            }
        }
        catch { }
        return o;
    }

    public static object Get(object o, string member)
    {
        if (o == null) return null;
        try
        {
            var obj = RealObj(o);
            var t = obj.GetType();
            var p = t.GetProperty(member, All);
            if (p != null) return p.GetValue(obj);
            var f = t.GetField(member, All);
            if (f != null) return f.GetValue(obj);
        }
        catch { }
        return null;
    }

    public static bool Set(object o, string member, object value)
    {
        if (o == null) return false;
        try
        {
            var obj = RealObj(o);
            var t = obj.GetType();
            var p = t.GetProperty(member, All);
            if (p != null && p.CanWrite) { p.SetValue(obj, value); return true; }
            var f = t.GetField(member, All);
            if (f != null) { f.SetValue(obj, value); return true; }
        }
        catch { }
        return false;
    }

    public static object Invoke(object instance, string method, params object[] args)
    {
        if (instance == null) return null;
        try
        {
            var obj = RealObj(instance);
            var candidates = obj.GetType().GetMethods(All).Where(m => m.Name == method).ToList();
            if (candidates.Count == 0) return null;
            var m = candidates.FirstOrDefault(x => x.GetParameters().Length == (args?.Length ?? 0)) ?? candidates[0];
            return m.Invoke(obj, args);
        }
        catch (Exception e)
        {
            Plugin.Logger?.LogWarning($"{method} a échoué : {e.InnerException?.Message ?? e.Message}");
            return null;
        }
    }
}
