# Éditer les textures et leurs calques

Guide pratique, tiré des essais faits sur des modèles N00 (jupe recolorée, peau détaillée, cheveux roses puis
indigo, tenue de Konoha). Toutes les modifications passent par l'historique de VRoid : Ctrl+Z les annule.

## Vocabulaire

| Terme | Sens |
|---|---|
| groupe (`group`) | partie éditable du modèle (`vroid_list_groups`) : Tops, FaceSkin, Iris... |
| élément (`transferable`) | contenu d'un groupe ; un groupe peut en avoir plusieurs (ex. vêtement + masque de peau) |
| image (`image`) | texture éditable d'un élément |
| calque (`node`) | calque raster d'une image, avec nom, opacité, visibilité, mode de fusion |

Une texture se désigne donc par le triplet `transferable` + `image` + `node`.

## Où se trouvent les textures

| Ce qu'on veut changer | Où chercher |
|---|---|
| Vêtement personnalisé (custom item) | `vroid_list_layers` sur son groupe |
| Vêtement tout juste choisi dans les presets | rien n'est éditable : d'abord `vroid_begin_clothing_edit` (bouton « Éditer » de VRoid), puis `vroid_list_layers` |
| Cheveux (mèches) | `vroid_list_hair_materials` : une texture principale (`MainTexture`) et une de reflets par matériau ; `transferable` vaut `Base` |
| Dessous des cheveux (couleur intérieure) | souvent un matériau à part (sur le modèle de Konoha : le 4ᵉ, gris à l'origine) |
| Crâne, avant | calque « cheveux » en haut de la texture FaceSkin |
| Crâne, arrière et nuque | calque « cheveux » de la texture BodySkin : dôme en bas, petites mèches en haut |
| Peau | FaceSkin (1024²) et BodySkin (2048²) |
| Yeux | groupe Iris ; sourcils : groupe Eyebrow |

Les calques masqués (`visible: false`) n'ont pas d'effet : modifier un calque visible, ou en ajouter un.

## Les trois façons de modifier

### 1. Recolorer sur place : `vroid_recolor_layer`

- `mode: multiply` : multiplie chaque pixel par la couleur. Pour un tissu clair (blanc, pâle) : garde plis et ombres.
- `mode: colorize` : garde la luminosité, impose teinte et saturation. Pour un tissu déjà coloré.
- `strength` (0..1) dose l'effet. La transparence est toujours conservée.

Limite : sur une texture sombre (cheveux bruns), `colorize` donne une couleur terne. Utiliser alors la méthode 2.

### 2. Exporter, retoucher, réimporter : `vroid_export_layer` puis `vroid_import_layer`

- L'export donne un PNG RGBA à la taille du calque. Le réimport doit avoir exactement la même taille.
- Aller-retour vérifié : export → import → export est identique au bit près.
- Retouche efficace pour changer une couleur : **remapper la luminosité sur une rampe de couleurs**
  (sombre → moyen → clair). Le dégradé et les reflets d'origine sont conservés, quelle que soit la couleur de
  départ. Exemples utilisés (r, g, b de 0 à 1) :
  - rose : (0.50, 0.16, 0.32) → (0.93, 0.45, 0.64) → (1.0, 0.86, 0.91)
  - indigo : (0.07, 0.07, 0.15) → (0.17, 0.17, 0.32) → (0.38, 0.40, 0.62)
  - moutarde (tissu pâle, lum. 0,55 à 0,95) : (0.40, 0.24, 0.04) → (0.86, 0.58, 0.14) → (0.97, 0.74, 0.28)
  - écossais aplati en bleu uni : rampe bleue avec bornes de luminosité très larges (-0,55 à 1,25)
- Aide : `tools/texture_utils.py`, fonction `ramp_recolor(src, dst, stops, lo, hi, mask)` (plus `export`, `imp`,
  `shot`). `mask` limite l'effet à une zone (ex. ne pas toucher les traits
  du visage quand on recolore le crâne sur FaceSkin).

### 3. Ajouter un calque : `vroid_import_layer` avec `as_new_layer: true`

- Ajoute le PNG par-dessus, en mode normal. L'original reste intact, et on peut masquer ou supprimer le calque
  dans VRoid.
- Exemple : `tools/skin_detail.py` génère un calque de détails de peau (grain, pores, teint, rougeurs) pour
  FaceSkin et BodySkin.
- Pour modifier ensuite ce calque, relancer `vroid_list_layers` : son `node` apparaît en dernier.

## Trouver une position sur une texture (UV)

Pour peindre à un endroit précis du corps (genou, coude...) :

1. Importer en nouveau calque une image dont la **teinte code la coordonnée** (V du haut en bas, puis U de gauche
   à droite).
2. Attendre environ 3 s (le rendu se met à jour à l'image suivante), faire une capture, lire la teinte du pixel
   à l'endroit voulu : on en déduit U et V.
3. Annuler le calque de repérage (`vroid_undo`).

Positions mesurées sur le corps N00 (BodySkin 2048²) : bras sur les colonnes latérales (u 0-480 et 1568-2048,
épaule en haut, poignet vers v ≈ 950), coude vers v ≈ 500, genou avant vers v ≈ 1490 (u ≈ 350 et 1690), doigts en
bas (u 480-780 et 1270-1570, v ≥ 1460). Visage N00 (FaceSkin 1024²) : joues vers (330, 690) et (694, 690), bout du
nez vers (512, 640).

## Pièges

- Capture trop tôt après une modification : l'ancien rendu apparaît. Attendre 2 à 3 s.
- Les ids (`group`, `transferable`, `image`, `node`) changent d'un modèle à l'autre et après réimport d'un preset :
  toujours relister.
- Réouvrir un modèle peut rendre une texture de cheveux temporairement non éditable : `vroid_list_hair_materials`
  le signale sur la texture concernée au lieu d'échouer (plugin 0.8.0).
- Ce que la peau peut rendre est limité par le shader de VRoid (rendu anime, ombres en aplats) : les détails
  restent de la peinture, sans relief.
