"""Fusionne le cache de presets fourni avec la release dans un cache existant, sans perdre les annotations locales.

    python merge_cache.py <cache_fourni> <cache_installé>

- Les presets absents du cache installé sont ajoutés.
- Pour un preset déjà présent, seuls les champs vides (description, tags, couleurs, vignette) sont complétés.
- Les vignettes manquantes sont copiées ; celles déjà présentes ne sont pas écrasées.
"""
import json
import os
import shutil
import sys


def main(src, dst):
    with open(os.path.join(src, "catalog.json"), encoding="utf-8") as f:
        new = json.load(f)
    path = os.path.join(dst, "catalog.json")
    with open(path, encoding="utf-8") as f:
        cur = json.load(f)
    added = filled = thumbs = 0
    for key, e in new.get("presets", {}).items():
        c = cur["presets"].get(key)
        if c is None:
            cur["presets"][key] = e
            added += 1
        else:
            for field in ("description", "tags", "colors", "thumbnail"):
                if not c.get(field) and e.get(field):
                    c[field] = e[field]
                    filled += 1
            if e.get("annotations") and not c.get("annotations"):
                c["annotations"] = e["annotations"]
        t = e.get("thumbnail")
        if t:
            s, d = os.path.join(src, t), os.path.join(dst, t)
            if os.path.exists(s) and not os.path.exists(d):
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copy2(s, d)
                thumbs += 1
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)
    print(f"  Cache fusionné : {added} presets ajoutés, {filled} champs complétés, {thumbs} vignettes copiées.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
