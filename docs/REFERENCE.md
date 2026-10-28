# Référence du pont MCP VRoid

Générée le 2026-10-28 avec VRoidMcpBridge 0.7.0 (Unity 6000.0.62f1) par `tools/gen_reference.py`.

Voir aussi `docs/TEXTURES.md` pour l'édition des textures et de leurs calques.

## Outils MCP

| Outil | Rôle |
|---|---|
| `vroid_status` | Indique si VRoid Studio répond et si un modèle est ouvert. |
| `vroid_list_groups` | Liste les groupes éditables du modèle ouvert (visage, yeux, cheveux, corps, tenues...). Chaque groupe a un id à passer aux autres outils. |
| `vroid_get_params` | Liste les paramètres d'un groupe (curseurs blendshape, os, couleurs) avec leur valeur actuelle. |
| `vroid_set_blendshape` | Règle un curseur de forme (blendshape) d'un groupe. Annulable dans VRoid (Ctrl+Z). |
| `vroid_set_bone` | Règle un paramètre de transformation d'os (proportions du corps, taille...). |
| `vroid_set_color` | Règle une couleur (composantes 0..1). Annulable dans VRoid. |
| `vroid_list_layers` | Liste les textures éditables d'un groupe (ex. jupe = Bottoms) : éléments (transferable), images et calques (node, nom, opacité, visibilité, mode de fusion). Les vêtements n'ont pas de curseurs de couleur : leur couleur se change par leurs calques de texture. |
| `vroid_recolor_layer` | Recolore un calque de texture sur place, transparence conservée, annulable. mode 'multiply' : tissu clair -> couleur cible en gardant ombres et plis. mode 'colorize' : garde la luminosité, impose la teinte (pour un tissu déjà coloré). |
| `vroid_export_layer` | Exporte un calque de texture en PNG (RGBA) pour le retoucher avec un autre outil. |
| `vroid_import_layer` | Réimporte un PNG dans un calque (même taille que l'export) ou comme nouveau calque. Annulable. |
| `vroid_list_hair_materials` | Liste les matériaux de cheveux (la couleur des cheveux ne passe pas par vroid_get_params) : id, nom, couleurs réglables (key + valeur) et textures avec leurs calques (transferable/image/node utilisables avec vroid_recolor_layer). |
| `vroid_set_hair_color` | Règle une couleur d'un matériau de cheveux (composantes 0..1). Annulable. Pour des cheveux dont la couleur est peinte dans la texture, recolorer plutôt les calques (mode colorize). |
| `vroid_list_hair_groups` | Liste les groupes de cheveux : 'procedural' (longueur, nombre de mèches réglables) ou 'brush' (mèches dessinées : nombre de mèches, longueur moyenne). |
| `vroid_set_procedural_hair` | Règle la longueur et/ou le nombre de mèches d'un groupe de cheveux procédural. Annulable. |
| `vroid_scale_brush_hair` | Allonge (factor > 1) ou raccourcit (factor < 1) toutes les mèches d'un groupe dessiné au pinceau, à partir de leur racine. Annulable (une étape par point). |
| `vroid_clone_brush_hair` | Duplique un groupe de mèches dessinées et décale la copie (en mètres, repère du modèle) pour ajouter des mèches. |
| `vroid_undo` | Annule la dernière modification dans VRoid Studio. |
| `vroid_redo` | Rétablit la dernière modification annulée. |
| `vroid_screenshot` | Capture la fenêtre de VRoid Studio et renvoie l'image, pour voir le résultat des modifications. |
| `vroid_list_presets` | Liste les presets de VRoid (coiffures, visages, tenues, corps...). filter cherche dans le chemin de ressource (ex. 'Hair', 'Tops', 'Bottoms', 'Onepiece', 'Shoes', 'Face'). Renvoie aussi la liste des catégories. Seuls les presets gratuits ou possédés sont listés, sauf include_locked. |
| `vroid_apply_preset` | Applique un preset (remplace l'élément de la même catégorie, comme un clic sur sa vignette). Annulable. |
| `vroid_clothing_colors` | Liste les couleurs réglables d'un vêtement (même preset) : group + key à passer à vroid_set_color. |
| `vroid_begin_clothing_edit` | Passe un vêtement preset en édition de texture (comme le bouton Éditer de VRoid) : ses calques deviennent accessibles à vroid_list_layers / vroid_recolor_layer. Annulable. |
| `vroid_measure` | Mesure la taille actuelle du modèle en cm (identique à l'étiquette de taille de VRoid). |
| `vroid_set_body_size` | Règle directement la taille (cm) via le curseur de silhouette du genre (FigureHeight/FigureSlender, proportions gardées), et si donné le poids (kg), converti en largeur de taille via l'IMC (VRoid n'a pas de poids). gender : female, male ou neutral. Annulable. |
| `vroid_preset_cache_search` | Cherche dans le cache partagé des presets (sans VRoid) : descriptions, tags et couleurs déjà notés par d'autres IA, avec le chemin de la vignette. Tous les mots de query doivent correspondre (ex. 'jupe plissée courte bleu', 'hoodie yellow'). Utiliser avant d'essayer des presets un par un. |
| `vroid_preset_cache_annotate` | Ajoute ou corrige la description, les tags et les couleurs d'un preset dans le cache partagé, pour les autres IA. Tags courts en minuscules (type, couleur, longueur, style). |
| `vroid_preset_thumbnail` | Renvoie la vignette en cache d'un preset (image), pour juger sans l'appliquer. |
| `vroid_preset_cache_sync` | Met à jour la liste des presets du cache depuis VRoid (nouveaux presets, prix, possession) sans effacer les annotations. |
| `vroid_preset_cache_build` | Crée les vignettes manquantes d'une catégorie : applique chaque preset dans VRoid, capture, recadre sur la zone utile, puis remet le preset d'origine. Long (environ 2 s par preset). |
| `vroid_camera` | Oriente la vue 3D de VRoid pour regarder le modèle sous un autre angle avant une capture. action : get (état + liste des rotations prédéfinies), angles (x,y en degrés), rotate (dx,dy), zoom (d), pan (x,y), reset (vue initiale), mode (rotation prédéfinie de VRoid), projection (bascule perspective/orthographique), custom (px,py,pz,cx,cy,cz). |

## Catégories de presets

Clé stable d'un preset = son chemin de ressource. « Emplacement » = partie du modèle remplacée quand on l'applique (`vroid_apply_preset`). Les cheveux et le visage ont des presets par sous-partie, pas seulement des ensembles complets.

| Catégorie | Emplacement | Nombre | Vignettes | Annotés | Contenu |
|---|---|---|---|---|---|
| `Attachment/BaseballCap` | Hat | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/CatEar` | AnimalEar | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/CatTail` | Tail | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/FoxTail` | Tail | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/GlassesHi` | Glasses | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/GlassesLow` | Glasses | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/RabbitEar` | AnimalEar | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/RabbitTail` | Tail | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/SilkHat` | Hat | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/StrawHat` | Hat | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/WitchHat` | Hat | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Attachment/WorkCap` | Hat | 1 | 0 | 0 | accessoire de tête ou de corps (chapeau, oreilles, queue, lunettes) |
| `Clothing/AccessoryArm` | ArmAccessory | 20 | 0 | 0 | accessoire de bras (bracelets, manchettes) |
| `Clothing/AccessoryNeck` | NeckAccessory | 22 | 0 | 0 | accessoire de cou (collier, ruban, cravate) |
| `Clothing/Bottoms` | Bottoms | 69 | 69 | 69 | bas (jupes, pantalons, shorts) |
| `Clothing/InnerBottom` | InnerBottom | 3 | 0 | 0 | sous-vêtement du bas |
| `Clothing/InnerTop` | InnerTop | 9 | 0 | 0 | haut porté dessous (caraco, col roulé...) |
| `Clothing/Onepiece` | Onepiece | 43 | 0 | 0 | robe ou tenue d'une pièce (remplace haut et bas) |
| `Clothing/Shoes` | Shoes | 69 | 0 | 0 | chaussures |
| `Clothing/Socks` | Socks | 34 | 34 | 34 | chaussettes, bas, collants (ou jambes nues) |
| `Clothing/Tops` | Tops | 102 | 102 | 102 | haut (t-shirts, sweats, chemises, vestes) |
| `Face/Ear` | Ear | 51 | 0 | 0 | forme des oreilles |
| `Face/EyeHighlight` | EyeHighlight | 66 | 0 | 0 | reflets des yeux |
| `Face/EyeSurrounding` | EyeSurrounding | 51 | 0 | 0 | contour des yeux |
| `Face/EyeWhite` | EyeWhite | 11 | 0 | 0 | blanc des yeux |
| `Face/Eyebrow` | Eyebrow | 65 | 0 | 0 | sourcils |
| `Face/Eyelash` | Eyelash | 47 | 0 | 0 | cils |
| `Face/Eyelid` | Eyelid | 36 | 0 | 0 | paupières |
| `Face/Eyeline` | Eyeline | 67 | 0 | 0 | trait d'eye-liner |
| `Face/FaceShape` | FaceShape | 52 | 0 | 0 | forme du visage |
| `Face/Iris` | Iris | 57 | 0 | 0 | iris |
| `Face/Mouth` | Mouth | 11 | 0 | 0 | bouche (texture intérieure) |
| `Face/Nose` | Nose | 51 | 0 | 0 | forme du nez |
| `Hair/Ahoge` | HairAhoge | 26 | 0 | 0 | mèche rebelle sur le dessus |
| `Hair/AllHair` | AllHair | 41 | 0 | 0 | coiffure complète (toutes les mèches) |
| `Hair/Back` | HairBack | 31 | 0 | 0 | cheveux arrière |
| `Hair/Base` | BaseHair | 3 | 0 | 0 | cheveux de base (calotte) |
| `Hair/Front` | HairFront | 50 | 0 | 0 | frange (avant) |
| `Hair/Hanege` | HairHanege | 66 | 0 | 0 | pointes relevées |
| `Hair/Sideburns` | HairSideburns | 66 | 0 | 0 | mèches latérales (devant les oreilles) |
| `Hair/Tied` | HairTied | 72 | 0 | 0 | cheveux attachés (queues, chignons, tresses) |
| `Overlay/Cheek` | Cheek | 37 | 0 | 0 | joues (rougeurs) |
| `Overlay/FacePaint` | FacePaint | 31 | 0 | 0 | maquillage / peinture du visage |
| `Overlay/Lip` | Lip | 26 | 0 | 0 | lèvres |
| `Overlay/MouthLine` | MouthLine | 11 | 0 | 0 | trait de la bouche |
| `Overlay/NoseLighting` | NoseLighting | 39 | 0 | 0 | reflet du nez |
| `Skin/Body` | BodySkin | 7 | 0 | 0 | peau du corps |
| `Skin/Face` | FaceSkin | 13 | 0 | 0 | peau du visage |
| `VRoid/Body` | 10 parties | 20 | 0 | 0 | corps complet (un fichier par partie : bras, buste, mains...) |
| `VRoid/ClothingSet` | ClothingSet | 69 | 0 | 0 | tenue complète |
| `VRoid/EyeSet` | EyeSet | 52 | 0 | 0 | ensemble des yeux |
| `VRoid/EyeballSet` | EyeballSet | 51 | 0 | 0 | globes oculaires |
| `VRoid/FaceSet` | FaceSet | 52 | 0 | 0 | visage complet |
| `VRoid/FixedPreset` | FixedPreset | 2 | 0 | 0 | modèle de base fixe |
| `VRoid/HairSet` | HairSet | 37 | 0 | 0 | coiffure complète prête à l'emploi |

## Groupes éditables et paramètres (modèle ouvert)

Clés à passer à `vroid_set_bone`, `vroid_set_blendshape` ou `vroid_set_color` avec l'id du groupe. Les valeurs sont celles du modèle au moment de la génération. Les ids de groupe changent d'un modèle à l'autre ; les clés (`Level2...`) et les types de groupe, non.

Curseurs appariés : `...Mag`/`...Shrink`, `...Long`/`...Short`, `...Wide`/`...Narrow`, `FigureHeight<Genre>`/`FigureSlender<Genre>` sont les deux moitiés d'un même curseur ; régler l'une remet l'autre à zéro.

### Arm

Type `TransferableGroupType.N00.Level1.Arm`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Arm_ArmShort` | bone | 0 |
| `Level2Arm_ArmLong` | bone | 0 |

### BaseHair

Type `TransferableGroupType.N00.Level1.BaseHair`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1BaseHair_OverlayColor` | color | rgba(0.51, 0.35, 0.27, 1.00) |
| `Level1BaseHair_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1BaseHair_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1BaseHair_MaterialEmissionColor` | color | rgba(0.86, 0.69, 0.69, 1.00) |
| `Level1BaseHair_MaterialOutlineColor` | color | rgba(0.47, 0.75, 0.74, 1.00) |

### BodySkin

Type `TransferableGroupType.N00.Level1.BodySkin`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1BodySkin_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1BodySkin_MaterialShadeColor` | color | rgba(0.97, 0.81, 0.86, 1.00) |
| `Level1BodySkin_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level1BodySkin_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level1BodySkin_ShadowColor` | color | rgba(0.94, 0.73, 0.64, 1.00) |
| `Level1BodySkin_MainColor` | color | rgba(0.98, 0.92, 0.87, 1.00) |
| `Level1BodySkin_HighlightColor` | color | rgba(1.00, 0.97, 0.95, 1.00) |

### Cheek

Type `TransferableGroupType.N00.Level1.Cheek`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1Cheek_OverlayColor` | color | rgba(1.00, 0.87, 0.82, 1.00) |

### Chest

Type `TransferableGroupType.N00.Level1.Chest`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Breast_BustDown` | bone | 0 |
| `Level2Breast_BustUp` | bone | 0 |
| `Level2Breast_BustOpen` | bone | 0 |
| `Level2Breast_BustClose` | bone | 0 |
| `Level2Breast_BustScaleMag` | bone | 0 |
| `Level2Breast_BustScaleShrink` | bone | 0 |
| `Level2Breast_BustScaleShrink2` | bone | 0 |

### Ear

Type `TransferableGroupType.N00.Level1.Ear`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Ear_EarScaleMag` | bone | 0 |
| `Level2Ear_EarScaleShrink` | bone | 0 |
| `Level2Ear_EarTipUp` | bone | 0 |
| `Level2Ear_EarTipWide` | bone | 0 |
| `Level2Ear_EarTipDown` | bone | 0 |
| `Level2Ear_EarStandUp` | bone | 0 |
| `Level2Ear_EarLieDown` | bone | 0 |
| `Level2Ear_EarRound` | bone | 0 |
| `Level2Ear_EarOff` | blendshape | 0 |

### Eyebrow

Type `TransferableGroupType.N00.Level1.Eyebrow`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1Eyebrow_EyebrowUp` | bone | 0 |
| `Level1Eyebrow_EyebrowDown` | bone | 0 |
| `Level1Eyebrow_EyebrowGather` | bone | 0 |
| `Level1Eyebrow_EyebrowSeparate` | bone | 0 |
| `Level1Eyebrow_EyebrowRise` | bone | 0 |
| `Level1Eyebrow_EyebrowDrooping` | bone | 0 |
| `Level1Eyebrow_EyebrowShapeFemale` | bone | 0 |
| `Level1Eyebrow_EyebrowShapeMale` | bone | 0 |
| `Level1Eyebrow_EyebrowForward` | bone | 0 |
| `Level1Eyebrow_EyebrowBackward` | bone | 0 |
| `Level1Eyebrow_EyebrowRotateInner` | bone | 0 |
| `Level1Eyebrow_EyebrowRotateOuter` | bone | 0 |
| `Level1Eyebrow_EyebrowSizeYShrink` | bone | 0 |
| `Level1Eyebrow_EyebrowSizeY` | bone | 0 |
| `Level1Eyebrow_EyebrowSizeXShrink` | bone | 0 |
| `Level1Eyebrow_EyebrowSizeX` | bone | 0 |
| `Level1Eyebrow_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1Eyebrow_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1Eyebrow_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level1Eyebrow_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level1Eyebrow_OverlayColor` | color | rgba(0.56, 0.35, 0.21, 1.00) |

### FaceShape

Type `TransferableGroupType.N00.Level1.FaceShape`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2FaceContour_FacelineDown` | bone | 0 |
| `Level2FaceContour_FacelineUp` | bone | 0 |
| `Level2FaceContour_MandibleSize` | bone | 0 |
| `Level2FaceContour_FacelineForward` | bone | 0 |
| `Level2FaceContour_FacelineBackward` | bone | 0 |
| `Level2FaceContour_ChinSlim` | bone | 0 |
| `Level2FaceContour_ChinUp` | bone | 0 |
| `Level2FaceContour_ChinRoundness` | bone | 0 |
| `Level2FaceContour_ChinSharp` | bone | 0 |
| `Level2FaceContour_SinciputDown` | bone | 0 |
| `Level2FaceContour_SinciputUp` | bone | 0 |
| `Level2FaceContour_FaceMale` | bone | 0 |
| `Level2FaceContour_FaceFemale` | bone | 1 |
| `Level2FaceContour_ChinOutlineFemale` | bone | 0 |
| `Level2FaceContour_ChinOutlineMale` | bone | 0 |
| `Level2FaceContour_ChinFullCheeked` | bone | 0 |
| `Level2FaceContour_ChinJawBackward` | bone | 0 |
| `Level2FaceContour_ChinJawForward` | bone | 0 |
| `Level2FaceContour_ChinRound` | bone | 0 |
| `Level2FaceContour_HeadShapeFemale` | bone | 0 |
| `Level2FaceContour_HeadShapeMale` | bone | 0 |
| `Level2FaceContour_ChinDown` | bone | 0 |
| `Level2FaceContour_FaceRound` | blendshape | 0 |

### FaceSkin

Type `TransferableGroupType.N00.Level1.FaceSkin`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1FaceSkin_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1FaceSkin_MaterialShadeColor` | color | rgba(0.97, 0.81, 0.86, 1.00) |
| `Level1FaceSkin_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level1FaceSkin_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level1FaceSkin_ShadowColor` | color | rgba(0.94, 0.73, 0.64, 1.00) |
| `Level1FaceSkin_MainColor` | color | rgba(0.98, 0.92, 0.87, 1.00) |
| `Level1FaceSkin_HighlightColor` | color | rgba(1.00, 0.97, 0.95, 1.00) |

### FixedPreset

Type `TransferableGroupType.N00.Level1.FixedPreset`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2WholeBody_BaseFemale` | bone | 1 |
| `Level2WholeBody_BaseMale` | bone | 0 |

### Hand

Type `TransferableGroupType.N00.Level1.Hand`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Hand_HandScaleMag` | bone | 0 |
| `Level2Hand_HandScaleShrink` | bone | 0 |
| `Level2Hand_FingerThin` | bone | 0 |
| `Level2Hand_FingerThick` | bone | 0 |

### Head

Type `TransferableGroupType.N00.Level1.Head`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Head_HeadScaleMag` | bone | 0 |
| `Level2Head_HeadScaleShrink` | bone | 0 |
| `Level2Head_HeadNarrow` | bone | 0 |
| `Level2Head_HeadWide` | bone | 0 |

### Leg

Type `TransferableGroupType.N00.Level1.Leg`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Leg_LegShort` | bone | 0 |
| `Level2Leg_LegLong` | bone | 0 |
| `Level2Foot_FootScaleMag` | bone | 0 |
| `Level2Foot_FootScaleShrink` | bone | 0 |

### Mouth

Type `TransferableGroupType.N00.Level1.Mouth`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Mouth_MouthDown` | bone | 0 |
| `Level2Mouth_MouthUp` | bone | 0 |
| `Level2Mouth_MouthNarrow` | bone | 0 |
| `Level2Mouth_MouthWide` | bone | 0 |
| `Level2Mouth_MouthCornerUp` | bone | 0 |
| `Level2Mouth_MouthCornerDown` | bone | 0 |
| `Level2Mouth_MouthShapeFemale` | bone | 0 |
| `Level2Mouth_MouthShapeMale` | bone | 0 |
| `Level2Mouth_MouthBackward` | bone | 0 |
| `Level2Mouth_MouthForward` | bone | 0 |
| `Level1Mouth_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level1Mouth_MaterialShadeColor` | color | rgba(0.97, 0.81, 0.86, 1.00) |
| `Level1Mouth_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level1Mouth_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level1Mouth_OverlayColor` | color | rgba(0.50, 0.50, 0.50, 1.00) |
| `Level2Mouth_MouthSkinFung` | blendshape | 0 |
| `Level2Mouth_MouthSkinFungR` | blendshape | 0 |
| `Level2Mouth_MouthSkinFungL` | blendshape | 0 |
| `Level2Mouth_ToothHide` | blendshape | 0 |
| `Level2Mouth_ToothHideLower` | blendshape | 0 |
| `Level2Mouth_ToothHideUpper` | blendshape | 0 |
| `Level2Mouth_ToothFung1` | blendshape | 0 |
| `Level2Mouth_ToothFung1Lower` | blendshape | 0 |
| `Level2Mouth_ToothFung1Upper` | blendshape | 0 |
| `Level2Mouth_ToothFung2` | blendshape | 0 |
| `Level2Mouth_ToothFung2Lower` | blendshape | 0 |
| `Level2Mouth_ToothFung2Upper` | blendshape | 0 |
| `Level2Mouth_ToothFung3` | blendshape | 0 |
| `Level2Mouth_ToothFung3Lower` | blendshape | 0 |
| `Level2Mouth_ToothFung3Upper` | blendshape | 0 |
| `Level2Mouth_ToothShort` | blendshape | 0 |
| `Level2Mouth_ToothShortLower` | blendshape | 0 |
| `Level2Mouth_ToothShortUpper` | blendshape | 0 |
| `Level2Mouth_LipsFlat` | blendshape | 0 |
| `Level2Mouth_LipsThick1Upper` | blendshape | 0 |
| `Level2Mouth_LipsThick1Lower` | blendshape | 0 |
| `Level2Mouth_LipsThick2Upper` | blendshape | 0 |
| `Level2Mouth_LipsThick2Lower` | blendshape | 0 |

### MouthLine

Type `TransferableGroupType.N00.Level1.MouthLine`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1MouthLine_OverlayColor` | color | rgba(0.62, 0.34, 0.34, 1.00) |

### Neck

Type `TransferableGroupType.N00.Level1.Neck`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Head_NeckShort` | bone | 0 |
| `Level2Head_NeckLong` | bone | 0 |
| `Level2Head_NeckAdamsApple` | blendshape | 0 |
| `Level2Head_NeckNarrowX` | blendshape | 0 |
| `Level2Head_NeckSpreadX` | blendshape | 0 |
| `Level2Head_NeckNarrowZ` | blendshape | 0 |
| `Level2Head_NeckSpreadZ` | blendshape | 0 |

### Nose

Type `TransferableGroupType.N00.Level1.Nose`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Nose_NoseDown` | bone | 0 |
| `Level2Nose_NoseUp` | bone | 0 |
| `Level2Nose_NoseWide` | bone | 0 |
| `Level2Nose_NoseBig` | bone | 0 |
| `Level2Nose_NoseSmall` | bone | 0 |
| `Level2Nose_NoseShapeFemale` | bone | 0 |
| `Level2Nose_NoseShapeMale` | bone | 0 |
| `Level2Nose_NoseRootLow` | bone | 0 |
| `Level2Nose_NoseCurve` | bone | 0 |
| `Level2Nose_NoseBridgeNarrow` | bone | 0 |
| `Level2Nose_NoseBridgeWide` | bone | 0 |
| `Level2Nose_NoseWingNarrow` | bone | 0 |
| `Level2Nose_NoseWingWide` | bone | 0 |
| `Level2Nose_NoseBottomUp` | bone | 0 |
| `Level2Nose_NoseBottomDown` | bone | 0 |
| `Level2Nose_NoseBottomForward` | bone | 0 |
| `Level2Nose_NoseBottomBackward` | bone | 0 |
| `Level2Nose_NoseWholeUp` | bone | 0 |
| `Level2Nose_NoseWholeDown` | bone | 0 |

### NoseLighting

Type `TransferableGroupType.N00.Level1.NoseLighting`

| Clé | Genre | Valeur |
|---|---|---|
| `Level1NoseLighting_ShadowColor` | color | rgba(0.94, 0.73, 0.64, 1.00) |
| `Level1NoseLighting_MainColor` | color | rgba(0.98, 0.92, 0.87, 1.00) |
| `Level1NoseLighting_HighlightColor` | color | rgba(1.00, 0.97, 0.95, 1.00) |

### Shoulder

Type `TransferableGroupType.N00.Level1.Shoulder`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Shoulder_ShoulderBroad` | bone | 0 |
| `Level2Shoulder_ShoulderNarrow` | bone | 0 |
| `Level2Shoulder_ClavicleLow` | blendshape | 0 |

### Torso

Type `TransferableGroupType.N00.Level1.Torso`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Torso_WaistShort` | bone | 0 |
| `Level2Torso_WaistLong` | bone | 0 |

### Waist

Type `TransferableGroupType.N00.Level1.Waist`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Waist_WaistScaleMag` | bone | 0 |
| `Level2Waist_WaistScaleShrink` | bone | 0 |

### WholeBody

Type `TransferableGroupType.N00.Level1.WholeBody`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2WholeBody_WholeBodyScaleMag` | bone | 0 |
| `Level2WholeBody_WholeBodyScaleShrink` | bone | 0 |
| `Level2WholeBody_FigureHeightNeutral` | bone | 0 |
| `Level2WholeBody_FigureHeightFemale` | bone | 0 |
| `Level2WholeBody_FigureHeightMale` | bone | 0 |
| `Level2WholeBody_FigureSlenderNeutral` | bone | 0 |
| `Level2WholeBody_FigureSlenderFemale` | bone | 0 |
| `Level2WholeBody_FigureSlenderMale` | bone | 0 |

### EyeSurrounding

Type `TransferableGroupType.N00.Level2.EyeSurrounding`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Eye_EyePosUp` | bone | 0 |
| `Level2Eye_EyePosDown` | bone | 0 |
| `Level2Eye_EyePosIn` | bone | 0 |
| `Level2Eye_EyePosOut` | bone | 0 |
| `Level2Eye_EyeSizeX` | bone | 0 |
| `Level2Eye_EyeSizeXShrink` | bone | 0 |
| `Level2Eye_EyeSizeY` | bone | 0 |
| `Level2Eye_EyeSizeYShrink` | bone | 0 |
| `Level2Eye_EyeRotateInner` | bone | 0 |
| `Level2Eye_EyeRotateOuter` | bone | 0 |
| `Level2EyeSurrounding_EyeOutsideDown` | bone | 0 |
| `Level2EyeSurrounding_EyeOutsideUp` | bone | 0 |
| `Level2EyeSurrounding_EyeCenterDown` | bone | 0 |
| `Level2EyeSurrounding_EyeCenterUp` | bone | 0 |
| `Level2EyeSurrounding_EyeInsideDown` | bone | 0 |
| `Level2EyeSurrounding_EyeInsideUp` | bone | 0 |
| `Level2EyeSurrounding_EyeShapeFemale` | bone | 0 |
| `Level2EyeSurrounding_EyeShapeMale` | bone | 0 |
| `Level2EyeSurrounding_EyelidStraightUpper` | bone | 0 |
| `Level2EyeSurrounding_EyelidStraightLower` | bone | 0 |
| `Level2EyeSurrounding_EyeJitome` | bone | 0 |
| `Level2EyeSurrounding_EyeInsideSuppressCurve` | bone | 0 |
| `Level2EyeSurrounding_EyeDrooping` | bone | 0 |
| `Level2EyeSurrounding_EyelashLow` | blendshape | 0 |

### Eyelash

Type `TransferableGroupType.N00.Level2.Eyelash`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Eyelash_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level2Eyelash_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level2Eyelash_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level2Eyelash_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level2Eyelash_OverlayColor` | color | rgba(0.43, 0.36, 0.30, 1.00) |

### Eyelid

Type `TransferableGroupType.N00.Level2.Eyelid`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Eyelid_ShadowColor` | color | rgba(0.94, 0.73, 0.64, 1.00) |
| `Level2Eyelid_MainColor` | color | rgba(0.98, 0.92, 0.87, 1.00) |
| `Level2Eyelid_HighlightColor` | color | rgba(1.00, 0.97, 0.95, 1.00) |

### Eyeline

Type `TransferableGroupType.N00.Level2.Eyeline`

| Clé | Genre | Valeur |
|---|---|---|
| `Level2Eyeline_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level2Eyeline_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level2Eyeline_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level2Eyeline_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level2Eyeline_OverlayColor` | color | rgba(0.54, 0.33, 0.26, 1.00) |

### EyeHighlight

Type `TransferableGroupType.N00.Level3.EyeHighlight`

| Clé | Genre | Valeur |
|---|---|---|
| `Level3EyeHighlight_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level3EyeHighlight_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level3EyeHighlight_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level3EyeHighlight_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level3EyeHighlight_OverlayColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |

### EyeWhite

Type `TransferableGroupType.N00.Level3.EyeWhite`

| Clé | Genre | Valeur |
|---|---|---|
| `Level3EyeWhite_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level3EyeWhite_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level3EyeWhite_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level3EyeWhite_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level3EyeWhite_OverlayColor` | color | rgba(0.86, 0.80, 0.79, 1.00) |

### Iris

Type `TransferableGroupType.N00.Level3.Iris`

| Clé | Genre | Valeur |
|---|---|---|
| `Level3Iris_EyeIrisScaleXMag` | bone | 0 |
| `Level3Iris_EyeIrisScaleXShrink` | bone | 0 |
| `Level3Iris_EyeIrisScaleYMag` | bone | 0 |
| `Level3Iris_EyeIrisScaleYShrink` | bone | 0 |
| `Level3Iris_GazeUpward` | bone | 0 |
| `Level3Iris_GazeDownward` | bone | 0 |
| `Level3Iris_GazeInside` | bone | 0 |
| `Level3Iris_GazeOutside` | bone | 0 |
| `Level3Iris_MaterialColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level3Iris_MaterialShadeColor` | color | rgba(1.00, 1.00, 1.00, 1.00) |
| `Level3Iris_MaterialEmissionColor` | color | rgba(0.00, 0.00, 0.00, 1.00) |
| `Level3Iris_MaterialOutlineColor` | color | rgba(0.27, 0.09, 0.13, 1.00) |
| `Level3Iris_LeftOverlayColor` | color | rgba(0.62, 0.38, 0.20, 1.00) |
| `Level3Iris_RightOverlayColor` | color | rgba(0.62, 0.38, 0.20, 1.00) |

Groupes sans curseur (couleur ou forme via presets, textures ou matériaux) : Bottoms, InnerBottom, InnerTop, Shoes, Tops

## Matériaux de cheveux

Couleurs réglables par `vroid_set_hair_color` (clé) ; textures recolorables par calques (transferable `Base`).

(lecture impossible sur ce modèle : Il2CppException) — relancer après installation du plugin 0.8.0)

## Caméra

(non disponible avec ce plugin : 'rotationModes')
