# Automatisation de l’export VRM — échec initial, puis résolu

Date : 2026-10-29  
Statut : **résolu** — l’export VRM automatisé fonctionne via l’API interne de VRoid, sans clic ni
sélecteur de fichier.

Contexte : VRoid Studio 2.14.0, BepInEx 6 IL2CPP, pont MCP `127.0.0.1:7811`.

Ce document conserve l’historique de l’échec initial. Il ne décrit plus l’état actuel du projet :
la solution et les résultats récents sont en bas.

## Objectif

Automatiser l’export VRM depuis le pont MCP, avec :

- choix de la version **VRM 1.0 / VRM 0.x** ;
- **suppression des meshes transparents** par défaut ;
- réduction des polygones : cheveux, visage, corps, outfit ;
- réduction des matériaux : `Default / 2 / 8 / 12`, `Combine Hair Mesh`, texture
  `Original / Shrunk`, atlas 4096/2048 ;
- réduction des bones de cheveux (`Hair (1 or more per group)`).

## Ce qui a échoué au départ

### 1. Automatisation souris

Tentatives avec `SetCursorPos`, `mouse_event`, `SetProcessDPIAware`, restauration et mise au
premier plan de la fenêtre. Le curseur se déplaçait, mais **VRoid ignorait les clics synthétiques** :
l’onglet Body ne changeait pas, le menu d’export ne s’ouvrait pas.

### 2. Probe C#

`VRoidMcpBridge/VrmExportProbe.cs` a été ajouté pour capturer :

- `VRoid.Studio.VRMExportScreen.ViewModel` via `OnScreenActivate` ;
- le constructeur de `ExportContextViewModel` ;
- `VrmExportButtonProperty.Export`.

Le probe capturait bien l’écran :

```json
{"captured":{"screen":true,"context":false,"button":false},
 "patches":["screen:ok","context:ok","button:ok"]}
```

Mais **pas le contexte d’export ni le bouton**. `VRMExportScreen.ViewModel` ne porte que
`ShortcutHandler` et `ObsoleteLegacyPhotoBoothViewModel`.

### 3. Boîte de dialogue native

Même en déclenchant `Export`, VRoid ouvre un sélecteur de fichier Windows. Il fallait soit le
piloter, soit trouver l’appel d’export avec un chemin direct.

## Solution

L’export passe désormais par l’API interne de VRoid, sans clic ni dialogue :

1. `EditRootScreen.ViewModel.EnterToVRMExport()` ouvre l’écran « Export as VRM ».
2. Le vrai porteur des réglages est `AvatarEditor._instantiatedPhotoBoothViewModel`
   (`VRoidStudio.GUI.AvatarEditor.PhotoBooth.PhotoBoothViewModel`), pas `VRMExportScreen.ViewModel` :
   - `ExportSettings.MeshReduction` : `MeshErasure` (Delete Transparent Meshes),
     `HairCrossSection`, `HairSmoothnessRate`, `Hair/Face/Body/ClothingReductionStrength` ;
   - `ExportSettings` : `MaterialReductionModeIndex` (Default / 2 / 8 / 12),
     `IsEnableHairCombination`, `TextureCompressionModeIndex` (Original / Shrunk),
     `AtlasResolutionIndex` (4096 / 2048), `hairBoneReduction.HairReductionStrength`.
3. `OnVRM1SettingChanged(meta, path, TaskCompletionSource<bool>)` (ou `OnVRMSettingChanged` pour
   VRM 0.x) exporte directement vers un chemin : c’est la suite que VRoid exécute après son
   dialogue, sans sélecteur de fichier.
4. `PopScreen()` sur `VRMExportScreen.ViewModel` ramène à l’éditeur.

Pièges rencontrés :

- après un export, les listes de meshes de réduction pointent vers des objets détruits : chaque
  export rouvre donc un écran neuf ;
- la réduction de polygones n’est reprise dans le fichier que si les réglages sont chargés à
  l’ouverture de l’écran : on règle, on rouvre, puis on exporte ;
- VRoid mémorise le dernier export : les options non fournies sont remises aux valeurs par défaut ;
- `Shrunk` n’est accepté qu’avec `material_mode` 0 ; avec une réduction de matériaux, VRoid utilise
  l’atlas (`atlas_resolution` 1 = 2048). Une option refusée est signalée dans `warnings` ;
- l’écran d’export ne doit pas être refermé avant la fin réelle des coroutines VRoid. Un garde
  `_exportRunning` empêche deux exports simultanés, et l’export attend maintenant que le fichier
  soit stable avant de quitter l’écran.

## Validation

Export automatique testé sur `Konoha.vroid` :

```text
path=D:\divers\vroid\out\character_test\konoha_export_test.vrm
version=1.0
delete_transparent=true
bytes=16 566 252
elapsedSec=10.1
warnings=[]
leftExportScreen=true
```

Après la correction de timing, l’export par défaut a laissé VRoid ouvert et `ready=true`.
Le fichier est un GLB VRM 1.0 valide (`VRMC_vrm`, `VRMC_springBone`,
`VRMC_materials_mtoon`), avec 15 matériaux. L’export manuel de référence `ssss.vrm` avait servi
à vérifier les options natives avant l’automatisation.

Autres cas testés via le même exporteur : VRM 0.x, réductions de polygones, 2/8 matériaux, atlas
2048 et texture Shrunk. Les options refusées apparaissent dans `warnings`.

> Remarque : après le premier export automatique, VRoid a journalisé
> `Coroutine continue failure` puis s’est fermé. Le fichier `.vrm` était complet et valide, mais
> la fermeture de l’écran était trop précoce. Le code attend désormais la stabilisation du fichier
> et un délai supplémentaire ; ne pas relancer un export avant la fin du précédent.

## Outils et aide

- `vroid_export_vrm` : export direct avec toutes les options ; `path` obligatoire ;
  `leave=true` par défaut pour revenir à l’éditeur.
- `vroid_export_vrm_options` : ouvre l’écran, renvoie les réglages courants et les choix
  matériaux/texture/atlas ; `leave=true` par défaut.
- `vroid_help topic=export` : documentation EN/FR/JA/ZH.
- 52 outils au total ; les nouveaux outils sont dans le groupe **VRM export** de l’index.

## Conclusion

L’échec initial venait de l’automatisation de l’interface (clics ignorés, contexte non exposé,
dialogue natif). La solution n’essaie plus de cliquer : elle appelle directement l’exporteur natif
avec un chemin de sortie et les réglages de `PhotoBoothViewModel`.

L’export fonctionne, mais il reste sensible au timing : **un seul export à la fois**, et attendre
la fin avant toute autre opération VRoid.
