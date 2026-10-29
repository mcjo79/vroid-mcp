"""Offline tests for the MCP layer, help, batch, labels and framing.

Run from the repository root:
    python -m unittest discover -s tests -v
No VRoid Studio instance and no network access are required.
"""
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "mcp_server"))

import help_i18n  # noqa: E402
import labeler  # noqa: E402
import preset_cache  # noqa: E402
import tool_i18n  # noqa: E402
import vroid_mcp  # noqa: E402

FRENCH_ACCENTS = re.compile(r"[àâçéèêëîïôùûüÿœ]")


class ToolMetadataTests(unittest.TestCase):
    def test_unique_tool_names(self):
        names = [t["name"] for t in vroid_mcp.TOOLS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(names), 52)

    def test_all_tools_have_english_descriptions(self):
        self.assertEqual(vroid_mcp._MISSING_EN, [])
        for tool in vroid_mcp.TOOLS:
            self.assertTrue(tool.get("description"), tool["name"])
            self.assertIsNone(FRENCH_ACCENTS.search(tool["description"]), tool["name"])
            for prop in (tool.get("inputSchema", {}).get("properties") or {}).values():
                desc = prop.get("description", "") or ""
                self.assertIsNone(FRENCH_ACCENTS.search(desc), tool["name"])

    def test_help_index_lists_every_tool(self):
        text = help_i18n.help_text("tools", "en", vroid_mcp.TOOLS)
        listed = [line.split("`")[1] for line in text.splitlines() if line.startswith("- `")]
        self.assertEqual(len(listed), len(vroid_mcp.TOOLS))
        self.assertEqual(set(listed), {t["name"] for t in vroid_mcp.TOOLS})


class CatalogScanTests(unittest.TestCase):
    """Le scan du catalogue ne doit jamais vider le cache sur une liste vide."""

    def test_empty_preset_list_is_skipped(self):
        import unittest.mock as mock

        def fake_bridge(path, **kwargs):
            if path == "/presets":
                return {"presets": []}
            if path == "/status":
                return {"modelOpen": False, "ready": False, "unity": "6000.0.62f1"}
            return {"items": []}

        calls = []
        with mock.patch.object(vroid_mcp, "call_bridge", side_effect=fake_bridge), \
             mock.patch.object(preset_cache, "scan", side_effect=lambda *a, **k: calls.append(a) or {"total": 0}):
            res = vroid_mcp.cache_sync()

        self.assertEqual(calls, [], "scan() ne doit pas être appelé sans presets")
        self.assertIn("skipped", res)
        self.assertEqual(res["removed"], [])

    def test_unreadable_customs_are_not_marked_removed(self):
        """Une lecture d'/custom_items en échec ne doit pas retirer les assets du cache."""
        import unittest.mock as mock

        def fake_bridge(path, **kwargs):
            if path == "/presets":
                return {"presets": [{"resource": "pixiv/x/N00/Base_000/a.transferablegroup", "id": "p1"}]}
            if path == "/status":
                return {"modelOpen": True, "ready": True, "unity": "6000.0.62f1", "startedUtc": "s1"}
            raise RuntimeError("bridge injoignable")

        cached = {"presets": {"custom:res#fichier.vroid": {
            "kind": "custom", "removed": False, "name": "Mon objet", "removedSince": None}}}
        with mock.patch.object(vroid_mcp, "call_bridge", side_effect=fake_bridge), \
             mock.patch.object(preset_cache, "load", side_effect=lambda: cached), \
             mock.patch.object(preset_cache, "_save", lambda cat: cached.update(cat)), \
             mock.patch.object(preset_cache, "now", lambda: "2026-01-01T00:00:00Z"), \
             mock.patch.object(preset_cache, "category_of", lambda k: ("", "")), \
             mock.patch.object(preset_cache, "slot_of", lambda k: ""):
            vroid_mcp.cache_sync()

        self.assertFalse(cached["presets"]["custom:res#fichier.vroid"]["removed"],
                         "l'objet personnalisé doit rester présent")

    def test_maybe_scan_ignores_closed_model(self):
        import unittest.mock as mock
        st = {"modelOpen": False, "ready": False, "startedUtc": "sess-1"}
        with mock.patch.object(vroid_mcp, "call_bridge", return_value=st):
            self.assertIsNone(vroid_mcp.maybe_scan())


class PreviewTests(unittest.TestCase):
    def test_screenshot_exposes_preview_quality_options(self):
        tool = next(t for t in vroid_mcp.TOOLS if t["name"] == "vroid_screenshot")
        props = tool["inputSchema"]["properties"]
        self.assertIn("msaa", props)
        self.assertIn("ssaa", props)
        self.assertIn("clean", props)
        self.assertIn("width", props)
        self.assertIn("height", props)

    def test_high_level_navigation_tools(self):
        names = {t["name"] for t in vroid_mcp.TOOLS}
        for name in ("vroid_sections", "vroid_categories", "vroid_enter", "vroid_set_param"):
            self.assertIn(name, names)
        tool = next(t for t in vroid_mcp.TOOLS if t["name"] == "vroid_set_param")
        self.assertEqual(tool["inputSchema"]["required"], ["section", "category", "param", "value"])

    def test_vrm_export_tools_and_help(self):
        names = {t["name"] for t in vroid_mcp.TOOLS}
        self.assertIn("vroid_export_vrm", names)
        self.assertIn("vroid_export_vrm_options", names)
        export = next(t for t in vroid_mcp.TOOLS if t["name"] == "vroid_export_vrm")
        props = export["inputSchema"]["properties"]
        self.assertEqual(export["inputSchema"]["required"], ["path"])
        self.assertEqual(props["version"]["enum"], ["1", "0"])
        for key in ("delete_transparent", "hair_smoothness", "hair", "face", "body", "outfit",
                    "material_mode", "combine_hair", "texture_mode", "atlas_resolution", "hair_bones", "leave"):
            self.assertIn(key, props)
        index = help_i18n.help_text("tools", "en", vroid_mcp.TOOLS)
        self.assertIn("### VRM export", index)
        self.assertIn("vroid_export_vrm", index)
        for lang in ("en", "fr", "ja", "zh"):
            text = help_i18n.help_text("export", lang, vroid_mcp.TOOLS)
            self.assertIn("vroid_export_vrm", text)
            self.assertGreater(len(text), 200)

    def test_colorize_supports_global_and_texture(self):
        tool = next(t for t in vroid_mcp.TOOLS if t["name"] == "vroid_colorize")
        props = tool["inputSchema"]["properties"]
        self.assertEqual(props["target"]["enum"], ["global", "texture", "both"])
        self.assertIn("mode", props)


class CSharpErrorTests(unittest.TestCase):
    def test_user_facing_csharp_errors_are_english(self):
        root = os.path.join(ROOT, "VRoidMcpBridge")
        for name in os.listdir(root):
            if not name.endswith(".cs"):
                continue
            with open(os.path.join(root, name), encoding="utf-8") as f:
                for number, line in enumerate(f, 1):
                    if ("throw new " in line or 'message = "' in line or 'error = "' in line):
                        self.assertIsNone(FRENCH_ACCENTS.search(line), f"{name}:{number}: {line.strip()}")


class HelpTests(unittest.TestCase):
    def test_all_topics_and_languages(self):
        for lang in ("en", "fr", "ja", "zh"):
            for topic in help_i18n.TOPICS:
                text = help_i18n.help_text(topic, lang, vroid_mcp.TOOLS)
                self.assertGreater(len(text), 40, (lang, topic))

    def test_aliases_and_fallback(self):
        self.assertEqual(help_i18n.normalize_lang("zh-CN"), "zh")
        self.assertEqual(help_i18n.normalize_lang("jp"), "ja")
        self.assertEqual(help_i18n.normalize_lang("unknown"), "en")
        text = help_i18n.help_text("/help", "fr", vroid_mcp.TOOLS)
        self.assertIn("lang=fr", text)

    def test_help_works_without_vroid(self):
        old = vroid_mcp.BRIDGE
        vroid_mcp.BRIDGE = "http://127.0.0.1:1"
        try:
            result = vroid_mcp.handle({
                "method": "tools/call",
                "params": {"name": "vroid_help", "arguments": {"topic": "overview", "lang": "ja"}},
            })
        finally:
            vroid_mcp.BRIDGE = old
        self.assertFalse(result["isError"])
        self.assertEqual(result["content"][0]["type"], "text")
        self.assertIn("lang=ja", result["content"][0]["text"])

    def test_initialize_instructions_and_prompt(self):
        init = vroid_mcp.handle({"method": "initialize", "params": {}})
        self.assertIn("vroid_help", init["instructions"])
        self.assertIn("prompts", init["capabilities"])
        prompts = vroid_mcp.handle({"method": "prompts/list", "params": {}})
        self.assertEqual(prompts["prompts"][0]["name"], "help")
        result = vroid_mcp.handle({
            "method": "prompts/get",
            "params": {"name": "help", "arguments": {"topic": "lifecycle", "lang": "zh-CN"}},
        })
        self.assertGreater(len(result["messages"][0]["content"]["text"]), 40)


class BatchTests(unittest.TestCase):
    def test_sequential_local_operations(self):
        result = vroid_mcp.run_tool("vroid_batch", {"operations": [
            {"tool": "vroid_framing_get", "args": {"category": "Clothing/Tops"}},
            {"tool": "vroid_framing_get", "args": {"category": "Hair/Back"}},
        ]})
        summary = result["__batch__"]
        self.assertTrue(summary["ok"])
        self.assertEqual(summary["executed"], 2)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(len(result["__images__"]), 0)

    def test_nested_batch_is_rejected(self):
        result = vroid_mcp.run_tool("vroid_batch", {"operations": [
            {"tool": "vroid_batch", "args": {"operations": []}},
        ]})
        summary = result["__batch__"]
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["stopped_at"], 0)
        self.assertIn("nested", summary["results"][0]["error"])

    def test_stop_on_error(self):
        result = vroid_mcp.run_tool("vroid_batch", {"operations": [
            {"tool": "vroid_create", "args": {}},
            {"tool": "vroid_status", "args": {}},
        ]})
        summary = result["__batch__"]
        self.assertFalse(summary["ok"])
        self.assertEqual(summary["executed"], 1)
        self.assertEqual(summary["stopped_at"], 0)

    def test_continue_on_error(self):
        result = vroid_mcp.run_tool("vroid_batch", {"operations": [
            {"tool": "vroid_batch", "args": {}},
            {"tool": "vroid_framing_get", "args": {"category": "Clothing/Tops"}},
        ], "stop_on_error": False})
        summary = result["__batch__"]
        self.assertEqual(summary["executed"], 2)
        self.assertEqual(summary["failed"], 1)


class LabelTests(unittest.TestCase):
    def test_structural_label(self):
        entry = {"kind": "preset", "category": "Clothing/Tops", "number": "013"}
        data = labeler.generate(entry)
        self.assertEqual(data["label"], "Tops 013")
        self.assertEqual(data["labelSource"], "generated")
        self.assertIn("top", data["generated"]["tags"])

    def test_manual_label_is_protected(self):
        entry = {"kind": "preset", "category": "Clothing/Tops", "number": "013",
                 "label": "Manual name", "labelSource": "manual"}
        labeler.apply(entry, force=True)
        self.assertEqual(entry["label"], "Manual name")
        self.assertEqual(entry["labelSource"], "manual")

    def test_visual_label(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "swatch.png")
            image = Image.new("RGB", (160, 160), (230, 230, 230))
            for x in range(30, 130):
                for y in range(30, 130):
                    image.putpixel((x, y), (30, 90, 190))
            image.save(path)
            entry = {"kind": "preset", "category": "Clothing/Tops", "number": "001"}
            data = labeler.generate(entry, path)
            self.assertIn("blue", data["label"])
            self.assertEqual(data["generated"]["method"], "structural+thumbnail")
            self.assertIn("blue", data["generated"]["colors"])


class FramingTests(unittest.TestCase):
    def test_defaults_and_validation(self):
        f = preset_cache.framing_for("VRoid/ClothingSet")
        self.assertEqual(f["fit"], "full-body")
        self.assertEqual(f["source"], "default")
        with self.assertRaises(ValueError):
            preset_cache.set_framing("Clothing/Tops", {"yaw": 999})

    def test_set_and_reset(self):
        old = preset_cache.FRAMING_OVERRIDES
        with tempfile.TemporaryDirectory() as d:
            preset_cache.FRAMING_OVERRIDES = os.path.join(d, "framing_overrides.json")
            try:
                result = preset_cache.set_framing("Clothing/Tops", {"yaw": 45, "distance": 3.5})
                self.assertEqual(result["effective"]["source"], "override")
                self.assertEqual(result["effective"]["yaw"], 45)
                reset = preset_cache.reset_framing("Clothing/Tops")
                self.assertEqual(reset["effective"]["source"], "default")
                self.assertEqual(reset["effective"]["yaw"], 0)
            finally:
                preset_cache.FRAMING_OVERRIDES = old


if __name__ == "__main__":
    unittest.main()
