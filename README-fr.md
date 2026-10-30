# Pont MCP pour VRoid Studio

[English](README.md) | **Français** | [日本語](README-ja.md) | [简体中文](README-zh.md)

Permet à une IA (Claude Code, Claude Desktop…) de lire et modifier le modèle ouvert dans VRoid Studio.

```
IA ──MCP (stdio)──> mcp_server/vroid_mcp.py ──HTTP 127.0.0.1:7811──> plugin BepInEx (dans VRoid) ──> VRoidCore.Editing.Context
```

## Nouveautés de la 0.13

- **Skill `vroid-studio`** pour Claude Code et DeepSeek Harness : un guide de travail d'une page, chargé seulement
  quand la conversation parle de VRoid, installé dans `~/.claude/skills` et `~/.dsh/skills`.
- **Prompts MCP** `start`, `character` et `export_vrm` (en plus de `help`) : des workflows prêts à l'emploi, en
  commandes `/mcp__vroid__*` dans Claude Code et dans le menu **+** de Claude Desktop.
- **Référence agent en ressources MCP** `vroid://agent/...` : la référence anglaise, section par section.
- Section **« Utiliser avec votre assistant »** ci-dessous : quoi faire après l'installation, et ce que reçoit
  chaque client.

## Nouveautés de la 0.12

- **Installeur Windows (NSIS)** : un assistant standard en quatre langues remplace `Installer.cmd` ; sans droits administrateur, sans console, avec une entrée dans *Applications installées* et un désinstalleur.
- **Python 3.12, numpy et Pillow sont embarqués** : aucun Python à installer, aucun PATH, aucun `pip` et aucun accès réseau nécessaire. Le prérequis *Python 3.8+ dans le PATH* de la 0.11 disparaît.
- **Connecteur DeepSeek Harness** : le serveur `vroid` est déclaré dans chaque profil web et desktop du harnais.
- **Fiabilité VRoid Studio 2.16 / Unity 6** : le premier chargement de l'éditeur d'une session attend désormais jusqu'à 120 s.
- **Protection du cache des presets** : un scan effectué au menu des modèles, ou qui ne peut pas lire les éléments personnalisés, ne marque plus le cache comme supprimé.

## Installation (release)

1. Télécharger **`VRoidMcp-Setup-v<version>.exe`** depuis les releases GitHub.
2. Fermer VRoid Studio, puis le lancer.

Un installeur Windows classique (français, anglais, japonais, chinois) guide pas à pas : options
(Claude Code / Claude Desktop, DeepSeek Harness, réinstaller BepInEx), dossier de VRoid Studio (trouvé
dans les bibliothèques Steam, ou « Parcourir… »), puis dossier du serveur. Aucun droit administrateur, aucune
console : la progression et le journal s'affichent dans l'installeur. Il apparaît ensuite dans les
*Applications installées* de Windows, avec un désinstalleur et des raccourcis dans le menu Démarrer.

L'installeur :
- installe BepInEx 6.0.0-be.791 (IL2CPP) s'il manque, après avoir mis de côté une autre version (BepInEx 5...)
  dans `BepInEx_sauvegarde_<date>` ; un BepInEx 6 déjà en place est conservé (option *Réinstaller BepInEx* pour le remplacer).
  L'archive est téléchargée depuis builds.bepinex.dev et son empreinte SHA-256 vérifiée ;
- copie le plugin dans `BepInEx\plugins\VRoidMcpBridge` ;
- copie le serveur MCP, son Python 3.12 embarqué (avec numpy et Pillow), les outils, la documentation et la config de
  cadrage par défaut dans `%LOCALAPPDATA%\VRoidMcp` (cache des presets local et overrides de cadrage locaux, jamais écrasés) ;
- déclare le serveur `vroid` dans **Claude Code** (`~/.claude.json`) et Claude Desktop, et pose le
  **connecteur DeepSeek Harness** dans chaque profil du harnais (`~/.dsh/profiles/web` et `desktop`, fichier `cordis.patch.yml`), avec sauvegarde.

Le serveur MCP est le transport : l'utilisateur, lui, « connecte son assistant » à VRoid.

Prérequis : Windows 10/11. Rien d'autre à installer.
Mise à jour : lancer l'installeur d'une version plus récente. Désinstallation : *Paramètres → Applications → VRoid MCP Bridge*
(BepInEx et le cache des presets sont conservés sauf si vous les cochez). En cas d'échec, le journal complet est dans
`%TEMP%\VRoidMcp-install.log`.

Installation scriptée : `VRoidMcp-Setup-v<version>.exe /S [/GAMEDIR=<dossier de VRoid Studio>] [/NOCLAUDE] [/NODSH] [/FORCEBEPINEX] [/D=<dossier d'installation>]` ;
désinstallation : `Uninstall-VRoidMcp.exe /S [/REMOVEBEPINEX] [/REMOVECACHE]`. Le `.zip` de la release contient aussi
`install.ps1` pour qui préfère PowerShell.
Premier lancement après installation de BepInEx : une à deux minutes de plus (génération de l'interop).

## Utiliser avec votre assistant

**Avant d'installer**, quittez complètement Claude Desktop (icône près de l'horloge → *Quitter*) : il
réécrit sa configuration en quittant, et une entrée ajoutée pendant qu'il tourne peut être perdue. Fermez
aussi DeepSeek Harness si vous l'utilisez.

**Après l'installation** : lancez VRoid Studio, puis redémarrez Claude Code, Claude Desktop ou DeepSeek Harness.
Ensuite, demandez simplement, en français :

- *« Vérifie que VRoid répond »* (`vroid_status`)
- *« Ouvre D:\modeles\konoha.vroid, mets-lui les cheveux rose pastel et montre-moi »*
- *« Trouve une jupe plissée courte dans les presets et essaies-en trois »*
- *« Exporte le modèle en VRM 1.0 dans D:\export\konoha.vrm avec 2 matériaux »*

Où apparaissent les outils :

| Client | Outils | Prompts prêts à l'emploi |
|---|---|---|
| Claude Code (terminal ou onglet *Code* de l'app) | `vroid_*`, vérifiable avec `/mcp` | `/mcp__vroid__start`, `/mcp__vroid__character`, `/mcp__vroid__export_vrm`, `/mcp__vroid__help` |
| Claude Desktop (*Chat*) | menu des outils de la conversation | les mêmes prompts, via le menu **+** |
| DeepSeek Harness (web et desktop) | `mcp__vroid__vroid_*` | — |

**Contexte de travail fourni à l'assistant** (rien à configurer) :

- **Instructions du serveur** (MCP `initialize`) : le contrat court — `vroid_status` d'abord, un modèle à la
  fois, enregistrer avant de changer de modèle, ne jamais écraser le fichier de l'utilisateur sans demander.
- **Skill `vroid-studio`**, installé dans `~/.claude/skills` (Claude Code) et `~/.dsh/skills` (DeepSeek Harness,
  tous les profils) : un guide de travail d'une page, chargé seulement quand la conversation parle de VRoid.
  Source : [`agent/skills/vroid-studio/SKILL.md`](agent/skills/vroid-studio/SKILL.md).
- **Ressources MCP** `vroid://agent/...` : la [référence agent](docs/AGENT_REFERENCE_EN.md), section par section
  (visage, coiffure, corps, tenue, presets, outils, workflows, dépannage…). Dans Claude Code, en joindre une
  avec `@vroid:vroid://agent/face`.
- **Prompts MCP** `start`, `character`, `export_vrm` et `help` (tableau ci-dessus).
- **`vroid_help`** : le manuel intégré en quatre langues, disponible même VRoid fermé.

L'onglet *Chat* de Claude Desktop ne lit pas les dossiers de skills : il s'appuie sur les instructions, les
prompts et les ressources. Pour lui donner aussi le guide, importez `agent/skills/vroid-studio` comme skill
(*Paramètres → Capacités → Skills*) ou collez `SKILL.md` dans les instructions d'un projet.

## Composants

| Élément | Emplacement |
|---|---|
| BepInEx 6 BE #791 (IL2CPP) | `<dossier de VRoid Studio>\BepInEx` |
| Plugin (source) | `VRoidMcpBridge/` → compilé dans `BepInEx\plugins\VRoidMcpBridge` |
| Serveur MCP | `mcp_server/vroid_mcp.py` (Python 3.12, numpy et Pillow embarqués) |
| Cadrage par défaut | `config/framing.json` (par catégorie/partie du corps ; overrides locaux dans le cache) |
| Skill pour les assistants | `agent/skills/vroid-studio/SKILL.md` → `~/.claude/skills` et `~/.dsh/skills` |
| Référence agent | `docs/AGENT_REFERENCE_EN.md`, servie en ressources MCP `vroid://agent/...` |
| Installeur | `installer/` (script NSIS, `build_release.py` et le ZIP portable) |

## Recompiler le plugin

```
cd VRoidMcpBridge
dotnet build -c Release -p:GameDir="<dossier de VRoid Studio>"
```
(VRoid doit être fermé, sinon la DLL est verrouillée. BepInEx 6 doit avoir été lancé une fois, pour que les
assemblages `BepInEx\interop` existent.)

## Brancher le MCP à la main

L'installeur le fait. Sinon, dans Claude Code :

La copie installée possède déjà son propre runtime :

```
claude mcp add --scope user vroid -- "%LOCALAPPDATA%\VRoidMcp\python\python.exe" -X utf8 -E -s "%LOCALAPPDATA%\VRoidMcp\mcp_server\vroid_mcp.py"
```

Ou dans Claude Desktop (`claude_desktop_config.json`) :

```json
{
  "mcpServers": {
    "vroid": {
      "command": "C:\\Users\\<vous>\\AppData\\Local\\VRoidMcp\\python\\python.exe",
      "args": ["-X", "utf8", "-E", "-s", "C:\\Users\\<vous>\\AppData\\Local\\VRoidMcp\\mcp_server\\vroid_mcp.py"]
    }
  }
}
```

## Référence complète

`docs/REFERENCE.md` liste tous les outils MCP, les catégories de presets (avec la partie du modèle remplacée :
coiffure complète, frange, cheveux arrière, mèches latérales, attachés, lèvres, oreilles...), et chaque paramètre
de chaque groupe (corps, visage...). Elle se régénère avec VRoid ouvert :

```
python tools/gen_reference.py
```

La documentation est aussi disponible en japonais et en chinois simplifié (voir les liens de langue en haut).

Pour un agent qui utilise le serveur via MCP (DeepSeek Harness inclus), voir
[`docs/AGENT_REFERENCE_EN.md`](docs/AGENT_REFERENCE_EN.md) : la référence anglaise
complète, avec les 53 outils et tous les paramètres par section/catégorie, les
paramètres physiques et les limites des expressions faciales. Elle est générée
depuis le registre vivant avec `python tools/gen_agent_reference_en.py`. Harness reçoit
le contrat court via MCP `initialize`, les schémas des outils via `tools/list`, et cette
référence à la demande via les ressources MCP sous `vroid://agent/`.

## Éditer les textures

`docs/TEXTURES.md` : où se trouvent les textures (vêtements, cheveux, crâne, peau, yeux), les trois façons de les
modifier (recolorer, exporter/réimporter, ajouter un calque), le repérage d'une position sur la texture et les
pièges. Aides : `tools/texture_utils.py`, `tools/skin_detail.py`.

## Cache partagé des presets

`preset_cache/` (local, non versionné : `%LOCALAPPDATA%\VRoidMcp\preset_cache` après installation) est un catalogue
normalisé que plusieurs IA (ou sessions) peuvent lire et enrichir, pour ne pas refaire les essais dans VRoid :

- `catalog.json` : une entrée par preset ou objet personnalisé, clé = chemin de ressource (stable d'une version à
  l'autre), avec id VRoid, catégorie, emplacement remplacé, prix/possession, vignette, description, tags, couleurs et
  historique des annotations (auteur, date). Les vignettes générées portent aussi `thumbnailMeta` : mannequin neutre,
  emplacements retirés, sous-vêtements/cheveux enlevés, cadrage (`fit: full-body` pour une tenue complète), pixels et
  SHA-1. Schéma détaillé dans `mcp_server/preset_cache.py`.
- Un `label` lisible est généré automatiquement : catégorie + numéro au scan, puis couleurs dominantes et indication
  `plain`/`patterned` depuis la vignette au build. `labelSource` distingue `generated` et `manual` ; un label manuel
  gagne toujours. Les données visuelles brutes sont dans `generated.visual` (couleurs, luminosité, densité de bords).
- `thumbs/<Catégorie>/<numéro>.jpg` : vignettes recadrées sur la zone utile (haut, bas, jambes, tête...).
- Les vignettes sont générées sur un mannequin nu : tous les vêtements, accessoires **et sous-vêtements** sont retirés
  (les sous-vêtements par défaut dépassent sur les maillots), les cheveux sont retirés sauf Base Hair / la partie
  testée, et la caméra est remise de face, centrée sur les bounds du modèle. Les tenues complètes sont cadrées plus
  large pour que les chaussures restent visibles.
- Écritures atomiques avec verrou : plusieurs IA peuvent annoter en même temps.

Outils : `vroid_preset_cache_search` (sans VRoid ; chaque résultat contient `preview` avec kind/mannequin/clothing/
underwear/hair/fit), `vroid_preset_thumbnail`, `vroid_preset_cache_annotate`, `vroid_preset_cache_sync` (nouveaux
presets et objets personnalisés, sans perte d'annotations), `vroid_preset_cache_build` (vignettes automatiques d'une
catégorie, puis remise de la tenue d'origine).

Le cache se remplit à l'usage. Les anciennes vignettes sans métadonnées affichent `preview.mannequin = "unknown"`
jusqu'à leur reconstruction avec `refresh=true`.

## Profils de cadrage

Le cadrage se règle **par catégorie / partie du corps**, jamais par vêtement individuel : `config/framing.json`
(versionné) contient les defaults pour `Clothing/Tops`, `Clothing/Shoes`, `Hair`, `Face`, `VRoid/ClothingSet`, etc.
Chaque profil a `top`/`bottom` (fractions depuis le haut du modèle), `half` (demi-largeur, `null` = toute la largeur),
`distance` (facteur de recul), `yaw` (orientation : 0 = face, 90 = profil, 180 = dos) et `fit` (`region` ou
`full-body` ; une tenue complète est reculée pour voir les chaussures).

L'IA peut surcharger un profil avec `vroid_framing_set` ; les overrides vont dans le fichier local non versionné
`preset_cache/framing_overrides.json`. `vroid_framing_reset` les efface et revient aux defaults commités. Les
informations propres à un vêtement (vignette, description, tags, couleurs, métadonnées de capture) restent dans
`catalog.json`.

## Outils exposés

53 outils `vroid_*` (aide, lot, cycle de vie, **export VRM**, cadrage, paramètres, couleurs, calques, cheveux,
presets, taille, caméra, captures...) : liste complète et description dans `docs/REFERENCE.md`. Les outils de
cycle de vie sont `vroid_create`, `vroid_open`, `vroid_save`, `vroid_main_menu` et `vroid_exit` ; le cadrage se
règle avec `vroid_framing_get/set/reset` ; `vroid_status` indique aussi le fichier courant et l'état modifié.

### Aide et langues

Le serveur MCP expose `vroid_help` (alias `/help` dans la documentation client), utilisable sans VRoid :

```text
vroid_help topic=overview lang=en       # défaut
vroid_help topic=tools lang=fr
vroid_help topic=lifecycle lang=ja
vroid_help topic=thumbnails lang=zh-CN
```

Les noms d'outils et arguments sont en anglais. Le manuel existe en anglais, français, japonais et chinois
simplifié ; l'index des outils est généré depuis le registre vivant. `initialize.instructions` oriente les
nouveaux clients IA vers `vroid_help` et les règles de sauvegarde/cycle de vie.

### Lot

`vroid_batch` exécute jusqu'à 200 opérations séquentiellement dans un seul appel MCP, avec
`stop_on_error=true` par défaut, sans batch imbriqué ni rollback automatique. Il renvoie un résumé texte +
jusqu'à 8 images / 16 Mio dans la même réponse ; les images en trop sont données par leur chemin. Utile pour
les balayages de presets, les séquences de paramètres et les séries de captures. Sauvegarder avant une
séquence destructive.

Les modifications passent par le système de commandes de VRoid : elles apparaissent dans l'historique et s'annulent avec Ctrl+Z.

### Export VRM

`vroid_export_vrm` pilote l'exporteur natif de VRoid sans clic ni boîte de dialogue. Il gère VRM 1.0/0.x,
**Delete Transparent Meshes** (par défaut), les curseurs de réduction de polygones, la réduction de matériaux
(Default/2/8/12), la combinaison des cheveux, la compression de texture/atlas et la réduction des bones de
cheveux :

```text
vroid_export_vrm path=D:\out\modele.vrm version=1 delete_transparent=true \
  hair=50 hair_bones=50 material_mode=1 combine_hair=true
```

Le fichier `.vroid` ouvert n'est pas modifié. L'export prend 10 à 40 s, renvoie `warnings` pour toute option
refusée par VRoid et referme l'écran d'export par défaut (`leave=false` le laisse ouvert). Un seul export à la
fois : attendre la réponse avant toute autre opération VRoid. `vroid_export_vrm_options` ouvre le même écran et
renvoie les réglages courants et les choix disponibles. Voir `vroid_help topic=export`.

## Classes clés trouvées dans le dump

- `VRoidCore.Editing.Context` : modèle en cours d'édition (lecture des paramètres, `ExecuteSyncCommand`, `UndoAsync`…).
- `VRoid.Studio.Component.VRoidCoreModelUpdater` (MonoBehaviour) : détient le `Context` actif (`_context`).
- `VRoidCore.Editing.History.Command.*` : ~110 commandes (cheveux, textures, matériaux, couleurs, os, blendshapes…).

## Tests automatisés

La suite hors ligne couvre le protocole MCP, les quatre langues d'aide, l'index vivant des outils,
la sémantique du batch, les labels générés et les defaults/overrides de cadrage. Aucun VRoid n'est
nécessaire :

```text
python -m unittest discover -s tests -v
```

La CI lance la même suite sur push/PR (`.github/workflows/tests.yml`). Les smoke tests propres à
VRoid (create/open/save, capture, build de presets) restent manuels : ils exigent l'éditeur et BepInEx.

## Mode minimisé / arrière-plan

L’exécution en arrière-plan est **toujours active** : le plugin maintient
`Application.runInBackground`. Il n’y a plus de bascule foreground ; le mode testé et fiable est
celui où VRoid reste minimisé.

Testé sur une fenêtre VRoid minimisée : `/status`, `vroid_enter`/`vroid_set_param` et une capture
propre MSAA/SSAA ont fonctionné. Cela évite le piège où la désactivation de l’arrière-plan mettait
VRoid en pause et faisait expirer les appels MCP.

## Preview 3D

`vroid_screenshot` rend maintenant la caméra 3D du modèle dans sa propre RenderTexture (sans panneaux
UI), avec **MSAA 4x** et **SSAA 2x** par défaut. `width`/`height` choisissent la taille de sortie,
`msaa`/`ssaa` arbitrent qualité/vitesse, `clean=false` restaure la capture plein écran. Cette capture
sert au contrôle visuel ; les vignettes de presets gardent le chemin plein écran, recadré par
`crop_center`.

## État des tests (VRoid sous Unity 6000.0.62)

| Fonction | Résultat |
|---|---|
| Lecture des groupes et paramètres | OK (36 groupes sur un modèle N00) |
| Réglage d'os, de forme (blendshape), de couleur | OK, valeurs relues identiques |
| Annuler / rétablir | OK, dans l'ordre ; les réglages successifs d'un même curseur sont fusionnés en une étape, comme un glissement de curseur |
| Preview 3D (MSAA 4x / SSAA 2x) | OK, sans panneaux UI, orientation correcte |
| Couleur des cheveux (0.3.0) | OK : matériaux de cheveux listés (couleurs + textures) ; cheveux bruns → roses en remappant la texture par luminosité (dégradé et reflets conservés) |
| Presets (0.5.0) | OK : 1750 presets listés (50 catégories), application comme un clic sur la vignette ; planches de captures pour choisir (102 hauts, 69 bas) |
| Taille / poids (0.7.0) | OK : `vroid_set_body_size` 160 cm → 159,9 ; 152 cm/39 kg → 152,0 (curseur 0,338, comme le réglage manuel 0,337) |
| Export VRM | OK : `vroid_export_vrm` sur `Konoha.vroid` → VRM 1.0, 16,6 Mo, 10,1 s, aucun warning, VRoid toujours ouvert après l’export ; VRM 0.x, réductions, matériaux/atlas et modes de texture testés via le même exporteur natif |
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
- Taille affichée par VRoid ≈ sommet du modèle (m) x 100, que `/measure` (boundsMaxY) retrouve. `vroid_set_body_size` vise une taille en cm (et convertit le poids en largeur de taille via l'IMC). L'étiquette ignore les mèches fines dressées (ahoge) alors que `/measure` les compte : avec une ahoge, viser quelques cm de plus et vérifier l'étiquette (onglet Corps). Ex. : cible 132,3 → étiquette 130,0.

## Licence

MIT — voir [`LICENSE`](LICENSE). Le code adapté de `vroid-studio-mcp` est couvert par sa
notice MIT dans [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). VRoid Studio, BepInEx et
leurs ressources ne sont pas distribués avec ce projet.

## Pièges IL2CPP rencontrés

- VRoid suspend sa boucle quand sa fenêtre n'a pas le focus : le plugin force `Application.runInBackground = true`.
- Construire des `KeyValuePair<,>` IL2CPP côté managé fait planter le runtime : passer par un `Dictionary` IL2CPP natif.
- `ScreenCapture.CaptureScreenshot(string)` plante dans l'interop : utiliser `CaptureScreenshotAsTexture` + `EncodeToPNG`.

## Limites

- Les mises à jour de VRoid Studio peuvent renommer ces classes : il faudra alors refaire le dump et ajuster le code.
- BepInEx 6 est en « bleeding edge » : stable ici, mais sans garantie.
- Les anciens plugins BepInEx 5 (ex. VRoidXYTool) ne fonctionnent pas avec BepInEx 6 IL2CPP.
