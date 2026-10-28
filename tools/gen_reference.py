"""Génère docs/REFERENCE.md à partir de VRoid en marche (plugin chargé, modèle ouvert) et du cache des presets.

    python tools/gen_reference.py

Contenu : outils MCP, catégories de presets (avec l'emplacement remplacé et le nombre), groupes éditables
du modèle ouvert et tous leurs paramètres, couleurs des matériaux de cheveux, catégories de la caméra.
"""
import collections
import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "mcp_server"))
import preset_cache as pc  # noqa: E402
import vroid_mcp as v  # noqa: E402

OUT = os.path.join(os.path.dirname(HERE), "docs", "REFERENCE.md")

CAT_FR = {
    "Attachment": "accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes)",
    "Clothing/AccessoryArm": "accessoire de bras (bracelets, manchettes)",
    "Clothing/AccessoryNeck": "accessoire de cou (collier, ruban, cravate)",
    "Clothing/Bottoms": "bas (jupes, pantalons, shorts)",
    "Clothing/InnerBottom": "sous-vêtement du bas", "Clothing/InnerTop": "haut porté dessous (caraco, col roulé...)",
    "Clothing/Onepiece": "robe ou tenue d'une pièce (remplace haut et bas)",
    "Clothing/Shoes": "chaussures", "Clothing/Socks": "chaussettes, bas, collants (ou jambes nues)",
    "Clothing/Tops": "haut (t-shirts, sweats, chemises, vestes)",
    "Face/Ear": "forme des oreilles", "Face/EyeHighlight": "reflets des yeux", "Face/EyeSurrounding": "contour des yeux",
    "Face/EyeWhite": "blanc des yeux", "Face/Eyebrow": "sourcils", "Face/Eyelash": "cils", "Face/Eyelid": "paupières",
    "Face/Eyeline": "trait d'eye-liner", "Face/FaceShape": "forme du visage", "Face/Iris": "iris",
    "Face/Mouth": "bouche (texture intérieure)", "Face/Nose": "forme du nez",
    "Hair/AllHair": "coiffure complète (toutes les mèches)", "Hair/Front": "frange (avant)", "Hair/Back": "cheveux arrière",
    "Hair/Sideburns": "mèches latérales (devant les oreilles)", "Hair/Hanege": "pointes relevées",
    "Hair/Tied": "cheveux attachés (queues, chignons, tresses)", "Hair/Ahoge": "mèche rebelle sur le dessus",
    "Hair/Base": "cheveux de base (calotte)",
    "Overlay/Cheek": "joues (rougeurs)", "Overlay/FacePaint": "maquillage / peinture du visage", "Overlay/Lip": "lèvres",
    "Overlay/MouthLine": "trait de la bouche", "Overlay/NoseLighting": "reflet du nez",
    "Skin/Body": "peau du corps", "Skin/Face": "peau du visage",
    "VRoid/Body": "corps complet (un fichier par partie : bras, buste, mains...)",
    "VRoid/ClothingSet": "tenue complète", "VRoid/EyeSet": "ensemble des yeux", "VRoid/EyeballSet": "globes oculaires",
    "VRoid/FaceSet": "visage complet", "VRoid/FixedPreset": "modèle de base fixe", "VRoid/HairSet": "coiffure complète prête à l'emploi",
}


def desc(cat):
    return CAT_FR.get(cat) or CAT_FR.get(cat.split("/")[0], "")


def main():
    L = []
    w = L.append
    st = v.call_bridge("/status")
    w("# Référence du pont MCP VRoid\n")
    w(f"Générée le {datetime.date.today()} avec {st.get('plugin')} (Unity {st.get('unity')}) par `tools/gen_reference.py`.\n")

    w("Voir aussi `docs/TEXTURES.md` pour l'édition des textures et de leurs calques.\n")
    w("## Outils MCP\n")
    w("| Outil | Rôle |\n|---|---|")
    for t in v.TOOLS:
        w(f"| `{t['name']}` | {t['description'].replace('|', '/')} |")

    w("\n## Catégories de presets\n")
    w("Clé stable d'un preset = son chemin de ressource. « Emplacement » = partie du modèle remplacée quand on "
      "l'applique (`vroid_apply_preset`). Les cheveux et le visage ont des presets par sous-partie, pas seulement "
      "des ensembles complets.\n")
    w("| Catégorie | Emplacement | Nombre | Vignettes | Annotés | Contenu |\n|---|---|---|---|---|---|")
    cat = pc.load()["presets"]
    by = collections.defaultdict(list)
    for e in cat.values():
        by[e["category"]].append(e)
    for c in sorted(by):
        es = by[c]
        slots = sorted({e.get("slot") or "?" for e in es})
        slot = ", ".join(slots) if len(slots) <= 3 else f"{len(slots)} parties"
        w(f"| `{c}` | {slot} | {len(es)} | {sum(1 for e in es if e.get('thumbnail'))} | "
          f"{sum(1 for e in es if e.get('description'))} | {desc(c)} |")

    w("\n## Groupes éditables et paramètres (modèle ouvert)\n")
    w("Clés à passer à `vroid_set_bone`, `vroid_set_blendshape` ou `vroid_set_color` avec l'id du groupe. "
      "Les valeurs sont celles du modèle au moment de la génération. Les ids de groupe changent d'un modèle à "
      "l'autre ; les clés (`Level2...`) et les types de groupe, non.\n")
    w("Curseurs appariés : `...Mag`/`...Shrink`, `...Long`/`...Short`, `...Wide`/`...Narrow`, "
      "`FigureHeight<Genre>`/`FigureSlender<Genre>` sont les deux moitiés d'un même curseur ; régler l'une remet "
      "l'autre à zéro.\n")
    groups = v.call_bridge("/groups")
    for g in sorted(groups, key=lambda g: g["type"] or ""):
        ps = v.call_bridge("/params", query={"group": g["id"]})
        if not ps:
            continue
        w(f"### {g['type'].split('.')[-1]}\n")
        w(f"Type `{g['type']}`\n")
        w("| Clé | Genre | Valeur |\n|---|---|---|")
        for p in ps:
            val = p["value"]
            if isinstance(val, dict):
                val = "rgba(" + ", ".join(f"{val[k]:.2f}" for k in "rgba") + ")"
            elif isinstance(val, float):
                val = f"{val:.3f}"
            w(f"| `{p['key']}` | {p['kind']} | {val} |")
        w("")
    empty = sorted(g["type"].split(".")[-1] for g in groups if not v.call_bridge("/params", query={"group": g["id"]}))
    w("Groupes sans curseur (couleur ou forme via presets, textures ou matériaux) : " + ", ".join(empty) + "\n")

    w("## Matériaux de cheveux\n")
    w("Couleurs réglables par `vroid_set_hair_color` (clé) ; textures recolorables par calques "
      "(transferable `Base`).\n")
    mats = v.call_bridge("/hair_materials")
    if isinstance(mats, dict):
        w(f"(lecture impossible sur ce modèle : {mats.get('error')}) — relancer après installation du plugin 0.8.0)")
        mats = []
    for m in mats:
        keys = ", ".join(f"`{c['key']}`" for c in m["colors"])
        tex = ", ".join(t["label"].split(".")[-1] for t in m["textures"])
        w(f"- `{m['material']}` ({m['name']}) : couleurs {keys} ; textures {tex}")

    w("\n## Caméra\n")
    try:
        cam = v.call_bridge("/camera", body={"action": "get"})
        w("Rotations prédéfinies (`vroid_camera` action `mode`) : " + ", ".join(f"`{x}`" for x in cam["rotationModes"]))
    except Exception as e:  # plugin < 0.8.0
        w(f"(non disponible avec ce plugin : {e})")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
