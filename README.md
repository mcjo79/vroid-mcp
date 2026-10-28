# Pont MCP pour VRoid Studio (prototype)

Permet à une IA (Claude Code, Claude Desktop…) de lire et modifier le modèle ouvert dans VRoid Studio.

```
IA ──MCP (stdio)──> mcp_server/vroid_mcp.py ──HTTP 127.0.0.1:7811──> plugin BepInEx (dans VRoid) ──> VRoidCore.Editing.Context
```

## Composants

| Élément | Emplacement |
|---|---|
| BepInEx 6 BE #791 (IL2CPP) | `D:\steam\steamapps\common\VRoid Studio\BepInEx` |
| Ancien BepInEx 5 + VRoidXYTool (sauvegarde) | `D:\divers\vroid\backup_bepinex5` |
| Plugin (source) | `VRoidMcpBridge/` → compilé dans `BepInEx\plugins\VRoidMcpBridge` |
| Serveur MCP | `mcp_server/vroid_mcp.py` (Python 3, aucune dépendance) |

## Recompiler le plugin

```
cd D:\divers\vroid\VRoidMcpBridge
dotnet build -c Release
```
(VRoid doit être fermé, sinon la DLL est verrouillée.)

## Brancher le MCP dans Claude Code

```
claude mcp add vroid -- python D:\divers\vroid\mcp_server\vroid_mcp.py
```

Ou dans Claude Desktop (`claude_desktop_config.json`) :

```json
{ "mcpServers": { "vroid": { "command": "python", "args": ["D:\\divers\\vroid\\mcp_server\\vroid_mcp.py"] } } }
```

## Référence complète

`docs/REFERENCE.md` liste tous les outils MCP, les catégories de presets (avec la partie du modèle remplacée :
coiffure complète, frange, cheveux arrière, mèches latérales, attachés, lèvres, oreilles...), et chaque paramètre
de chaque groupe (corps, visage...). Elle se régénère avec VRoid ouvert :

```
python tools/gen_reference.py
```

## Éditer les textures

`docs/TEXTURES.md` : où se trouvent les textures (vêtements, cheveux, crâne, peau, yeux), les trois façons de les
modifier (recolorer, exporter/réimporter, ajouter un calque), le repérage d'une position sur la texture et les
pièges. Aides : `tools/texture_utils.py`, `tools/skin_detail.py`.

## Cache partagé des presets

`preset_cache/` est un catalogue normalisé que plusieurs IA (ou sessions) peuvent lire et enrichir, pour ne pas
refaire les essais dans VRoid :

- `catalog.json` : une entrée par preset, clé = chemin de ressource (stable d'une version à l'autre), avec id VRoid,
  catégorie, emplacement remplacé, prix/possession, vignette, description, tags, couleurs et historique des
  annotations (auteur, date). Schéma détaillé dans `mcp_server/preset_cache.py`.
- `thumbs/<Catégorie>/<numéro>.jpg` : vignettes recadrées sur la zone utile (haut, bas, jambes, tête...).
- Écritures atomiques avec verrou : plusieurs IA peuvent annoter en même temps.

Outils : `vroid_preset_cache_search` (sans VRoid), `vroid_preset_thumbnail`, `vroid_preset_cache_annotate`,
`vroid_preset_cache_sync` (nouveaux presets, sans perte d'annotations), `vroid_preset_cache_build`
(vignettes automatiques d'une catégorie, puis remise du preset d'origine).

État : 1750 presets ; hauts (102), bas (69) et chaussettes (34) ont vignette et description.

## Outils exposés

`vroid_status`, `vroid_list_groups`, `vroid_get_params`, `vroid_set_blendshape`, `vroid_set_bone`,
`vroid_set_color`, `vroid_list_layers`, `vroid_recolor_layer`, `vroid_export_layer`, `vroid_import_layer`,
`vroid_list_hair_materials`, `vroid_set_hair_color` (0.3.0), `vroid_undo`, `vroid_redo`, `vroid_screenshot`.

Les modifications passent par le système de commandes de VRoid : elles apparaissent dans l'historique et s'annulent avec Ctrl+Z.

## Classes clés trouvées dans le dump

- `VRoidCore.Editing.Context` : modèle en cours d'édition (lecture des paramètres, `ExecuteSyncCommand`, `UndoAsync`…).
- `VRoid.Studio.Component.VRoidCoreModelUpdater` (MonoBehaviour) : détient le `Context` actif (`_context`).
- `VRoidCore.Editing.History.Command.*` : ~110 commandes (cheveux, textures, matériaux, couleurs, os, blendshapes…).

## État des tests (plugin 0.3.0, VRoid sous Unity 6000.0.62)

| Fonction | Résultat |
|---|---|
| Lecture des groupes et paramètres | OK (36 groupes sur un modèle N00) |
| Réglage d'os, de forme (blendshape), de couleur | OK, valeurs relues identiques |
| Annuler / rétablir | OK, dans l'ordre ; les réglages successifs d'un même curseur sont fusionnés en une étape, comme un glissement de curseur |
| Capture d'écran | OK |
| Couleur des cheveux (0.3.0) | OK : matériaux de cheveux listés (couleurs + textures) ; cheveux bruns → roses en remappant la texture par luminosité (dégradé et reflets conservés) |
| Presets (0.5.0) | OK : 1750 presets listés (50 catégories), application comme un clic sur la vignette ; planches de captures pour choisir (102 hauts, 69 bas) |
| Taille / poids (0.7.0) | OK : `vroid_set_body_size` 160 cm → 159,9 ; 152 cm/39 kg → 152,0 (curseur 0,338, comme le réglage manuel 0,337) |
| Vêtements preset (0.6.0) | `begin_clothing_edit` rend la texture éditable, puis recoloration par calques ; `clothing_colors` liste les couleurs (clés non textuelles pour l'instant) |
| Forme des cheveux (0.4.0) | Lecture des groupes OK. Allonger une mèche pinceau OK techniquement, mais l'agrandissement depuis la racine fait ressortir la mèche (à remplacer par un prolongement vers le bas). Dupliquer + décaler un groupe OK : 41 groupes côtés/arrière dupliqués 6 cm plus bas = cheveux plus longs (une étape d'annulation par point) |
| Calques de texture : lister, exporter/importer PNG (0.2.0) | OK ; aller-retour export → import → export identique au bit près |
| Recolorer un vêtement (0.2.0) | OK : jupe blanche → bleu marine en mode multiply, plis et transparence conservés |

`tools/skin_detail.py` génère un calque de détails de peau (grain, pores, teint, rougeurs aux joues, nez, coudes, genoux, doigts)
à importer comme nouveau calque sur la peau du corps et du visage (`vroid_import_layer` avec `as_new_layer`).
Positions UV mesurées sur le corps N00 en important temporairement un calque qui code U/V en teinte, puis en lisant la capture.

Sur un modèle composé de presets, beaucoup de couleurs sont des « couleurs de superposition » simples à régler : `Level1BaseHair_OverlayColor` (crâne), `Level3Iris_Left/RightOverlayColor` (yeux), `Level1Eyebrow_OverlayColor` (sourcils) avec `vroid_set_color` ; la teinte d'une coiffure preset est une clé `base:<id>` de `vroid_list_hair_materials`.

Les cheveux utilisent des « matériaux de cheveux » partagés (`GetAllMaterialsQuery`, `GetHairMaterialQuery`,
`SetMaterialColorCommand`) ; leurs textures ont pour transferable `Base` et se recolorent avec les outils de calques.
Le crâne est peint à part : l'avant en haut de la texture FaceSkin, l'arrière (dôme en bas) et la nuque
(haut) sur la texture BodySkin. Il faut les recolorer aussi pour changer la couleur des cheveux.

Les vêtements n'ont pas de curseurs de couleur : leur couleur vient de leurs calques de texture
(`vroid_list_layers` puis `vroid_recolor_layer`, ou export → retouche → import).

À savoir :
- Beaucoup de curseurs sont stockés en deux moitiés (`…Mag`/`…Shrink`, `…Wide`/`…Narrow`). Régler une moitié remet l'autre à zéro, VRoid compensant la différence.
- Couleurs en composantes 0..1.
- `vroid_face_preview` ouvre la bouche (Fcl_MTH_A...) sur le maillage du visage seulement : les dents (crocs `Level2Mouth_ToothFung1/2/3Upper/Lower`) ne s'affichent pas dans cet aperçu ; pour les voir, passer par l'éditeur d'expressions de VRoid.
- FigureHeight<Genre> et FigureSlender<Genre> sont les deux moitiés d'un même curseur de silhouette : Height rapetisse en gardant les proportions, Slender agrandit et affine. C'est lui qu'il faut utiliser pour la taille (pas WholeBodyScale, qui réduit tout uniformément).
- Taille affichée par VRoid ≈ sommet du modèle (m) x 100, mais l'étiquette ignore les mèches fines dressées (ahoge) alors que `/measure` les compte : avec une ahoge, viser quelques cm de plus et vérifier l'étiquette (onglet Corps). Ex. Shinobu : cible 132,3 → étiquette 130,0.
- Taille affichée par VRoid = sommet du modèle (m) x 100 : `/measure` (boundsMaxY) donne la même valeur. `vroid_set_body_size` vise une taille en cm (et convertit le poids en largeur de taille via l'IMC).

## Pièges IL2CPP rencontrés

- VRoid suspend sa boucle quand sa fenêtre n'a pas le focus : le plugin force `Application.runInBackground = true`.
- Construire des `KeyValuePair<,>` IL2CPP côté managé fait planter le runtime : passer par un `Dictionary` IL2CPP natif.
- `ScreenCapture.CaptureScreenshot(string)` plante dans l'interop : utiliser `CaptureScreenshotAsTexture` + `EncodeToPNG`.

## Limites

- Les mises à jour de VRoid Studio peuvent renommer ces classes : il faudra alors refaire le dump et ajuster le code.
- BepInEx 6 est en « bleeding edge » : stable ici, mais sans garantie.
- L'ancien plugin VRoidXYTool (BepInEx 5) ne fonctionne plus sur cette version de VRoid.
