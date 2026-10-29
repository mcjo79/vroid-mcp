"""Trilingual help for the VRoid Studio MCP server.

Tool names and arguments stay English. The manual is available in English, French,
Japanese and Simplified Chinese; the tool index is generated from the live TOOLS list so it
cannot go stale when a tool is added.
"""

LANGUAGES = {
    "en": "English",
    "fr": "Français",
    "ja": "日本語",
    "zh": "简体中文",
}

LANG_ALIASES = {
    "en": "en", "english": "en",
    "fr": "fr", "français": "fr", "francais": "fr", "french": "fr",
    "ja": "ja", "jp": "ja", "日本語": "ja", "japanese": "ja",
    "zh": "zh", "zh-cn": "zh", "zh_cn": "zh", "zh-hans": "zh", "cn": "zh",
    "中文": "zh", "简体中文": "zh", "chinese": "zh",
}

TOPICS = {
    "overview": {"en": "Overview and first steps", "fr": "Vue d'ensemble et premiers pas",
                 "ja": "概要と最初の手順", "zh": "概览与快速开始"},
    "lifecycle": {"en": "Create / open / save / model menu", "fr": "Créer / ouvrir / sauver / menu des modèles",
                  "ja": "作成 / 開く / 保存 / モデル選択", "zh": "创建 / 打开 / 保存 / 模型菜单"},
    "export": {"en": "VRM export and reduction options", "fr": "Export VRM et options de réduction",
               "ja": "VRM 書き出しと軽量化", "zh": "VRM 导出与精简"},
    "framing": {"en": "Thumbnail framing and orientation", "fr": "Cadrage et orientation des vignettes",
                "ja": "サムネイルの構図と向き", "zh": "缩略图构图与朝向"},
    "thumbnails": {"en": "Preset thumbnails and the shared cache", "fr": "Vignettes de presets et cache partagé",
                   "ja": "プリセットのサムネイルと共有キャッシュ", "zh": "预设缩略图与共享缓存"},
    "colors": {"en": "Clothing and hair colors", "fr": "Couleurs des vêtements et des cheveux",
               "ja": "服と髪の色", "zh": "服装与头发颜色"},
    "outfit": {"en": "Outfits, single items and whole sets", "fr": "Tenues, pièces seules et ensembles complets",
               "ja": "服、単品、セットアップ", "zh": "服装、单件与整套"},
    "sessions": {"en": "Sessions, saving and reconnecting", "fr": "Sessions, sauvegarde et reconnexion",
                 "ja": "セッション、保存、再接続", "zh": "会话、保存与重连"},
    "errors": {"en": "Common errors and fixes", "fr": "Erreurs courantes et solutions",
               "ja": "よくあるエラーと対処", "zh": "常见错误与处理"},
    "languages": {"en": "Available languages", "fr": "Langues disponibles",
                  "ja": "利用できる言語", "zh": "可用语言"},
    "batch": {"en": "Batch operations", "fr": "Opérations par lot",
              "ja": "バッチ操作", "zh": "批量操作"},
    "tools": {"en": "Tool index", "fr": "Index des outils", "ja": "ツール一覧", "zh": "工具索引"},
}

INITIALIZE_INSTRUCTIONS = (
    "VRoid Studio MCP. Tool names and arguments are English. "
    "Call vroid_help('overview') before a complex task; vroid_help supports lang=en|fr|ja|zh-CN. "
    "VRoid Studio must be running with the bridge loaded. Only one model can be open at a time. "
    "Call vroid_status first. Save before vroid_main_menu, vroid_open or vroid_create. "
    "For visual work, use vroid_screenshot. For preset discovery, use vroid_preset_cache_search "
    "before applying presets. For sequences, use vroid_batch (up to 200 sequential operations, "
    "no automatic rollback). Do not assume that one preset replaces only one slot: whole outfits "
    "can replace several slots; verify with vroid_list_groups. Thumbnail generation strips all "
    "clothes, underwear and hair except the tested item. "
    "An English Agent Reference is exposed as MCP resources: vroid://agent/reference (full), "
    "plus vroid://agent/start, face, hairstyle, body, outfit, accessories, look, physical, presets, "
    "tools, workflows and troubleshooting. Read only the section needed; tools/list stays the "
    "authoritative schema list."
)

HELP = {
    "en": {
        "overview": """# VRoid Studio MCP — help

VRoid Studio must be running with the BepInEx bridge loaded (default http://127.0.0.1:7811).
Tool names and arguments are English. This manual is available in English, French, Japanese
and Simplified Chinese:

    vroid_help topic=overview lang=fr
    vroid_help topic=tools lang=ja
    vroid_help topic=lifecycle lang=zh-CN

Recommended first steps:
1. `vroid_status` — is VRoid reachable and is a model open?
2. `vroid_help topic=lifecycle` — create/open/save rules.
3. `vroid_list_groups` and `vroid_get_params` — inspect before editing.
4. `vroid_undo` if an experiment goes wrong; `vroid_screenshot` to verify.

One model at a time. Save before returning to the model menu or opening another file.
For a visual task, inspect first, change one thing, capture, then continue.""",
        "lifecycle": """# Lifecycle

- `vroid_create gender=female|male`: only at the model-select screen; blocks until ready.
  The new model has no file yet, so save it with `vroid_save path=...`.
- `vroid_open path=...`: only at the model-select screen; blocks until ready.
- `vroid_save`: in place if the model already has a file; `vroid_save path=...` = Save As.
- `vroid_main_menu`: returns to model select. Refuses unsaved changes unless `discard=true`.
- `vroid_status`: check `modelOpen`, `ready`, `currentFile`, `dirty`, `canSave`.

`vroid_create` and `vroid_open` are refused while a model is open. Save, then
`vroid_main_menu`, then create/open. There is no automatic rollback for lifecycle operations.""",
        "framing": """# Framing and orientation

Framing is configured per category/body part in `config/framing.json`, never per garment.

- `top` / `bottom`: fractions from the top of the model (0 = top, 1 = feet).
- `half`: half-width; `null` = full width.
- `distance`: zoom-out factor.
- `yaw`: 0 = front, 90 = profile, 180 = back; 45/135 = three-quarter.
- `fit`: `region` or `full-body`.

`vroid_framing_get` reads defaults/overrides; `vroid_framing_set` writes a local override;
`vroid_framing_reset` returns to the committed defaults. Per-item facts stay in
`catalog.json`; only the framing profile is shared per category.

Whole outfits use `fit=full-body` so shoes stay visible. Back hair uses yaw=180; full hair
sets use a three-quarter back view by default.""",
        "thumbnails": """# Preset thumbnails

`vroid_preset_cache_build category=...` captures one category at a time:

- removes all clothes, accessories, underwear (including default underwear, which shows
  through swimwear) and hair except BaseHair/the tested item;
- verifies that nothing else remains before capturing;
- resets the camera, centers it on the model bounds and applies the category yaw;
- writes `thumbnailMeta` into `catalog.json` (mannequin, stripped slots, camera, pixels,
  SHA-1, orientation);
- restores the original outfit afterwards.

`vroid_preset_cache_search` returns a `preview` with kind/mannequin/clothing/underwear/hair/
orientation/yaw. Old thumbnails show `"unknown"` until rebuilt with `refresh=true`.
Save the model before a build: restoration is not guaranteed to be identical.""",
        "colors": """# Colors

- Clothes have no color sliders. Use `vroid_list_layers` and `vroid_recolor_layer`.
  `multiply` keeps light-fabric shadows; `colorize` forces a hue while keeping luminance.
- Hair: `vroid_list_hair_materials` then `vroid_set_hair_color`. For preset hair, the
  `base:<id>` tint is often what must change. If the color is painted in the texture,
  recolor the layers instead.
- Color changes can be shared/global across materials or layers. Verify visually with
  `vroid_screenshot`, and use `vroid_undo` if the effect propagates unexpectedly.
- `vroid_begin_clothing_edit` / `vroid_begin_hair_edit` expose texture layers first.""",
        "outfit": """# Outfits, single items and whole sets

A preset replaces the item in its category, but a whole outfit/ClothingSet can replace
several slots at once (tops, bottoms, shoes, underwear...). Do not assume a single-slot
edit.

Recommended:
1. `vroid_list_groups` before and after applying a preset.
2. If unwanted items appeared, remove them with `vroid_remove_item` (group id or short type).
3. Use `vroid_apply_custom` for user items; `vroid_apply_preset` for built-in presets.
4. Verify with a screenshot; undo one step at a time if needed.

Thumbnail generation always removes default underwear; this is intentional, especially for
swimwear.""",
        "sessions": """# Sessions and persistence

- The bridge lives inside the VRoid Studio process. If VRoid quits, the bridge disappears;
  restart VRoid and reconnect the MCP server.
- Only one model can be open at a time through the bridge.
- The preset cache (`preset_cache/`) and framing overrides persist independently of the
  model and of the VRoid process.
- Save before `vroid_main_menu`, `vroid_open` or `vroid_create`; lifecycle calls do not
  create a backup.
- If the endpoint is unreachable, check that VRoid is running and that the plugin loaded.""",
        "errors": """# Common errors

- **VRoid Studio unreachable**: start VRoid; check BepInEx loaded the plugin; the default
  bridge is http://127.0.0.1:7811.
- **Model already open**: save, `vroid_main_menu`, then create/open.
- **Unsaved changes**: save, or pass `discard=true` to `vroid_main_menu` if you really want
  to lose them.
- **No thumbnail**: run `vroid_preset_cache_sync` then
  `vroid_preset_cache_build category=...`.
- **Editor not ready / modification in progress**: wait, call `vroid_status`, retry.
- **Nothing changed visually**: inspect with `vroid_list_groups`, `vroid_get_params` or
  `vroid_screenshot`; a preset may have replaced more than one slot.

When in doubt, call `vroid_help topic=tools` for the current tool list.""",
        "languages": """# Languages

- Commands and arguments: English.
- Manual: English (default), French, Japanese and Simplified Chinese.
- Use `vroid_help topic=overview lang=fr|ja|zh-CN`.
- README-fr.md and the French website pages remain available; Japanese and Chinese manuals
  are being expanded from this help source.
- The help index is generated from the live tool registry, so new tools appear automatically.""",
        "batch": """# Batch operations (next step)

Batch execution is planned but not enabled yet. For now, issue sequential tool calls.

The intended contract:
- `vroid_batch operations=[{tool, args}, ...]`, up to 200 operations;
- sequential, no parallel access to VRoid;
- `stop_on_error=true` by default, partial results returned;
- text summary + up to 8 images in one MCP response;
- no nested batches and no automatic rollback;
- save before destructive sequences, or use `vroid_undo` afterwards.

Until then, prefer one change → screenshot → next change, and use the preset cache to avoid
retrying presets blindly.""",
    },
    "fr": {
        "overview": """# VRoid Studio MCP — aide

VRoid Studio doit tourner avec le pont BepInEx chargé (http://127.0.0.1:7811 par défaut).
Les noms d'outils et les arguments sont en anglais. Ce manuel existe en anglais, français,
japonais et chinois simplifié :

    vroid_help topic=overview lang=en
    vroid_help topic=tools lang=ja
    vroid_help topic=lifecycle lang=zh-CN

Premiers pas :
1. `vroid_status` — VRoid répond-il, un modèle est-il ouvert ?
2. `vroid_help topic=lifecycle` — règles créer/ouvrir/sauver.
3. `vroid_list_groups` et `vroid_get_params` — inspecter avant de modifier.
4. `vroid_undo` en cas d'erreur ; `vroid_screenshot` pour vérifier.

Un seul modèle à la fois. Sauvegarder avant de revenir au menu ou d'ouvrir un autre fichier.
Pour un travail visuel : inspecter, modifier une chose, capturer, puis continuer.""",
        "lifecycle": """# Cycle de vie

- `vroid_create gender=female|male` : uniquement au menu des modèles ; attend que le modèle
  soit prêt. Le nouveau modèle n'a pas de fichier : `vroid_save path=...`.
- `vroid_open path=...` : uniquement au menu des modèles ; attend le chargement.
- `vroid_save` : sur place si le modèle a déjà un fichier ; avec `path`, enregistrement sous.
- `vroid_main_menu` : retour au menu. Refuse les modifications non sauvegardées sauf
  `discard=true`.
- `vroid_status` : `modelOpen`, `ready`, `currentFile`, `dirty`, `canSave`.

`vroid_create` et `vroid_open` sont refusés si un modèle est ouvert. Sauvegarder, revenir au
menu, puis créer/ouvrir. Aucun rollback automatique pour ces opérations.""",
        "framing": """# Cadrage et orientation

Le cadrage se règle par catégorie/partie du corps dans `config/framing.json`, jamais par
vêtement.

- `top` / `bottom` : fractions depuis le haut du modèle (0 = sommet, 1 = pieds).
- `half` : demi-largeur ; `null` = toute la largeur.
- `distance` : facteur de recul.
- `yaw` : 0 = face, 90 = profil, 180 = dos ; 45/135 = trois-quarts.
- `fit` : `region` ou `full-body`.

`vroid_framing_get` lit les valeurs ; `vroid_framing_set` écrit un override local ;
`vroid_framing_reset` restaure les defaults commités. Les infos par vêtement restent dans
`catalog.json` ; seul le profil de cadrage est partagé par catégorie.

Les tenues complètes utilisent `fit=full-body` pour garder les chaussures visibles. Les
cheveux arrière utilisent yaw=180 ; les coiffures complètes un trois-quarts dos.""",
        "thumbnails": """# Vignettes de presets

`vroid_preset_cache_build category=...` traite une catégorie :

- retire tous les vêtements, accessoires, sous-vêtements (même par défaut, qui dépassent sur
  les maillots) et cheveux sauf BaseHair/la pièce testée ;
- vérifie qu'il ne reste rien avant de capturer ;
- remet la caméra de face, la centre sur les bounds et applique le yaw de la catégorie ;
- écrit `thumbnailMeta` dans `catalog.json` (mannequin, emplacements retirés, caméra, pixels,
  SHA-1, orientation) ;
- remet la tenue d'origine ensuite.

`vroid_preset_cache_search` renvoie `preview` (kind/mannequin/clothing/underwear/hair/
orientation/yaw). Les anciennes vignettes affichent `"unknown"` jusqu'à reconstruction avec
`refresh=true`. Sauvegarder le modèle avant : la restauration n'est pas garantie à
l'identique.""",
        "colors": """# Couleurs

- Les vêtements n'ont pas de curseurs de couleur : `vroid_list_layers` puis
  `vroid_recolor_layer`. `multiply` garde les ombres d'un tissu clair ; `colorize` impose la
  teinte en gardant la luminosité.
- Cheveux : `vroid_list_hair_materials` puis `vroid_set_hair_color`. Pour une coiffure
  preset, la teinte `base:<id>` est souvent celle à changer. Si la couleur est peinte dans
  la texture, recolorer les calques.
- Une couleur peut être partagée/globale entre matériaux ou calques. Vérifier avec
  `vroid_screenshot` et utiliser `vroid_undo` si l'effet se propage.
- `vroid_begin_clothing_edit` / `vroid_begin_hair_edit` rendent les calques accessibles.""",
        "outfit": """# Tenues, pièces seules et ensembles

Un preset remplace l'élément de sa catégorie, mais une tenue complète/ClothingSet peut
remplacer plusieurs emplacements (haut, bas, chaussures, sous-vêtements...). Ne pas supposer
une modification d'un seul slot.

Conseillé :
1. `vroid_list_groups` avant et après.
2. Si des éléments indésirables apparaissent, `vroid_remove_item` (id de groupe ou type court).
3. `vroid_apply_custom` pour les objets personnalisés ; `vroid_apply_preset` pour les presets.
4. Vérifier avec une capture ; annuler étape par étape si besoin.

La génération de vignettes retire toujours les sous-vêtements par défaut ; c'est voulu,
surtout pour les maillots de bain.""",
        "sessions": """# Sessions et persistance

- Le pont vit dans le processus VRoid Studio. Si VRoid quitte, le pont disparaît : relancer
  VRoid puis reconnecter le serveur MCP.
- Un seul modèle peut être ouvert à la fois via le pont.
- Le cache des presets (`preset_cache/`) et les overrides de cadrage persistent indépendamment
  du modèle et du processus VRoid.
- Sauvegarder avant `vroid_main_menu`, `vroid_open` ou `vroid_create` ; ces appels ne font pas
  de sauvegarde.
- Si l'endpoint est injoignable, vérifier que VRoid tourne et que le plugin est chargé.""",
        "errors": """# Erreurs courantes

- **VRoid Studio injoignable** : lancer VRoid ; vérifier le plugin BepInEx ; pont par défaut
  http://127.0.0.1:7811.
- **Modèle déjà ouvert** : sauvegarder, `vroid_main_menu`, puis créer/ouvrir.
- **Modifications non sauvegardées** : sauvegarder, ou `discard=true` si vous acceptez de les
  perdre.
- **Pas de vignette** : `vroid_preset_cache_sync` puis
  `vroid_preset_cache_build category=...`.
- **Éditeur non prêt / modification en cours** : attendre, `vroid_status`, réessayer.
- **Rien ne change visuellement** : inspecter avec `vroid_list_groups`, `vroid_get_params` ou
  `vroid_screenshot` ; un preset peut avoir remplacé plusieurs slots.

En cas de doute : `vroid_help topic=tools`.""",
        "languages": """# Langues

- Commandes et arguments : anglais.
- Manuel : anglais (défaut), français, japonais et chinois simplifié.
- `vroid_help topic=overview lang=en|fr|ja|zh-CN`.
- README-fr.md et les pages françaises du site restent disponibles ; les manuels japonais et
  chinois sont enrichis à partir de cette aide.
- L'index des outils est généré depuis le registre vivant : les nouveaux outils apparaissent
  automatiquement.""",
        "batch": """# Opérations par lot (étape suivante)

Le batch est prévu mais pas encore actif. En attendant, faire des appels séquentiels.

Contrat prévu :
- `vroid_batch operations=[{tool, args}, ...]`, jusqu'à 200 opérations ;
- séquentiel, pas d'accès parallèle à VRoid ;
- `stop_on_error=true` par défaut, résultats partiels renvoyés ;
- résumé texte + jusqu'à 8 images dans une même réponse MCP ;
- pas de batch imbriqué ni de rollback automatique ;
- sauvegarder avant une séquence destructive, ou `vroid_undo` ensuite.

Pour l'instant : une modification → une capture → la suivante, et utiliser le cache des
presets pour éviter les essais à l'aveugle.""",
    },
    "ja": {
        "overview": """# VRoid Studio MCP — ヘルプ

VRoid Studio を起動し、BepInEx ブリッジを読み込んだ状態で使用します（既定:
http://127.0.0.1:7811）。ツール名と引数は英語です。このマニュアルは英語・フランス語・
日本語・簡体字中国語で利用できます。

    vroid_help topic=overview lang=en
    vroid_help topic=tools lang=fr
    vroid_help topic=lifecycle lang=zh-CN

最初の手順:
1. `vroid_status` — VRoid に接続でき、モデルが開いているか。
2. `vroid_help topic=lifecycle` — 作成・開く・保存のルール。
3. `vroid_list_groups` と `vroid_get_params` — 編集前に確認。
4. 失敗したら `vroid_undo`、確認には `vroid_screenshot`。

モデルは同時に 1 つだけです。モデル選択に戻る前、別ファイルを開く前に保存してください。
視覚作業は「確認 → 1 か所変更 → キャプチャ → 次へ」の順が安全です。""",
        "lifecycle": """# ライフサイクル

- `vroid_create gender=female|male`: モデル選択画面でのみ実行。準備完了まで待機。
  新しいモデルにはファイルがないため `vroid_save path=...` で保存します。
- `vroid_open path=...`: モデル選択画面でのみ実行。読み込み完了まで待機。
- `vroid_save`: 既存ファイルがあれば上書き。`path` を渡すと「名前を付けて保存」。
- `vroid_main_menu`: モデル選択に戻る。未保存がある場合は `discard=true` が必要。
- `vroid_status`: `modelOpen`、`ready`、`currentFile`、`dirty`、`canSave` を確認。

モデルを開いたまま `vroid_create` / `vroid_open` は拒否されます。保存 →
`vroid_main_menu` → 作成/開く の順にします。ライフサイクル操作に自動ロールバックは
ありません。""",
        "framing": """# 構図と向き

構図はカテゴリ／体の部位ごとに `config/framing.json` で設定します。個々の服ごとでは
ありません。

- `top` / `bottom`: モデル上端からの割合（0 = 頭頂、1 = 足元）。
- `half`: 半幅。`null` は全幅。
- `distance`: 引きの倍率。
- `yaw`: 0 = 正面、90 = 横顔、180 = 背面、45/135 = 斜め。
- `fit`: `region` または `full-body`。

`vroid_framing_get` で確認、`vroid_framing_set` でローカル上書き、
`vroid_framing_reset` でコミット済み既定値に戻します。アイテム固有の情報は
`catalog.json` に残ります。

全身コーデは `fit=full-body` で靴まで表示します。後ろ髪は yaw=180、髪セットは既定で
斜め後ろです。""",
        "thumbnails": """# プリセットのサムネイル

`vroid_preset_cache_build category=...` はカテゴリ単位で生成します:

- テスト対象以外の服、アクセサリ、下着（水着で透ける既定の下着も）、髪をすべて除去；
- 何も残っていないことを確認してから撮影；
- カメラを正面に戻し、モデルの bounds に合わせて中央化し、カテゴリの yaw を適用；
- `catalog.json` に `thumbnailMeta`（マネキン、除去スロット、カメラ、ピクセル、SHA-1、
  向き）を記録；
- 最後に元の服を復元。

`vroid_preset_cache_search` は `preview`（kind/mannequin/clothing/underwear/hair/
orientation/yaw）を返します。古いサムネイルは `refresh=true` で再生成するまで
`"unknown"` です。復元は完全ではない可能性があるため、事前にモデルを保存してください。""",
        "colors": """# 色

- 服にカラースライダーはありません。`vroid_list_layers` → `vroid_recolor_layer`。
  `multiply` は明るい布の陰影を保持、`colorize` は輝度を保って色相を付けます。
- 髪: `vroid_list_hair_materials` → `vroid_set_hair_color`。プリセット髪は
  `base:<id>` の色を変えることが多いです。テクスチャに描かれた色はレイヤーを
  再配色してください。
- 色はマテリアル／レイヤー間で共有・グローバルな場合があります。`vroid_screenshot` で
  確認し、意図しない伝播は `vroid_undo` で戻します。
- テクスチャ編集は `vroid_begin_clothing_edit` / `vroid_begin_hair_edit` で有効化します。""",
        "outfit": """# 服、単品、セットアップ

プリセットは同カテゴリのアイテムを置き換えますが、全身コーデ/ClothingSet は複数スロット
（トップス、ボトムス、靴、下着など）を一度に置き換えることがあります。1 スロットだけ
変わると仮定しないでください。

推奨:
1. 適用前後に `vroid_list_groups` で確認。
2. 不要なアイテムは `vroid_remove_item`（グループ id または短い種類）で削除。
3. ユーザーアイテムは `vroid_apply_custom`、組み込みは `vroid_apply_preset`。
4. スクリーンショットで確認し、必要なら 1 手ずつ undo。

サムネイル生成では既定の下着を必ず外します。水着などで重要です。""",
        "sessions": """# セッションと保存

- ブリッジは VRoid Studio プロセス内で動きます。VRoid を終了すると消えるため、再起動して
  MCP サーバーを再接続してください。
- ブリッジ経由で開けるモデルは同時に 1 つです。
- プリセットキャッシュ（`preset_cache/`）と構図の上書きは、モデルや VRoid プロセスとは
  独立して永続化されます。
- `vroid_main_menu`、`vroid_open`、`vroid_create` の前に保存してください。自動バックアップは
  ありません。
- 接続できない場合は VRoid の起動と BepInEx プラグインの読み込みを確認してください。""",
        "errors": """# よくあるエラー

- **VRoid Studio に接続できない**: VRoid を起動、BepInEx プラグインを確認。既定は
  http://127.0.0.1:7811。
- **モデルが既に開いている**: 保存 → `vroid_main_menu` → 作成/開く。
- **未保存の変更**: 保存するか、失ってよい場合のみ `discard=true`。
- **サムネイルがない**: `vroid_preset_cache_sync` →
  `vroid_preset_cache_build category=...`。
- **エディタ準備中 / 変更中**: 待って `vroid_status` を確認し再試行。
- **見た目が変わらない**: `vroid_list_groups`、`vroid_get_params`、`vroid_screenshot` で
  確認。プリセットが複数スロットを変えた可能性があります。

不明なときは `vroid_help topic=tools`。""",
        "languages": """# 言語

- コマンドと引数: 英語。
- マニュアル: 英語（既定）、フランス語、日本語、簡体字中国語。
- `vroid_help topic=overview lang=en|fr|ja|zh-CN`。
- README-fr.md とフランス語サイトは維持し、日本語・中国語のマニュアルはこのヘルプを
  元に拡充します。
- ツール一覧は実際のツール登録から自動生成されるため、新ツールも自動で載ります。""",
        "batch": """# バッチ操作（次の段階）

バッチは予定されていますが、まだ有効ではありません。現在は順次呼び出しを使用します。

予定仕様:
- `vroid_batch operations=[{tool, args}, ...]`、最大 200 操作；
- 逐次実行（VRoid への並列アクセスなし）；
- 既定 `stop_on_error=true`、部分結果を返す；
- 1 つの MCP 応答にテキスト要約 + 最大 8 画像；
- ネスト禁止、自動ロールバックなし；
- 破壊的な連続操作の前に保存、または後で `vroid_undo`。

それまでは「1 変更 → キャプチャ → 次」を基本にし、プリセットキャッシュを活用して
やみくもな試行を避けてください。""",
    },
    "zh": {
        "overview": """# VRoid Studio MCP — 帮助

VRoid Studio 必须正在运行并加载 BepInEx 桥接插件（默认 http://127.0.0.1:7811）。
工具名称和参数使用英文。本手册提供英语、法语、日语和简体中文：

    vroid_help topic=overview lang=en
    vroid_help topic=tools lang=fr
    vroid_help topic=lifecycle lang=ja

建议步骤：
1. `vroid_status` — VRoid 是否可连接、是否已打开模型？
2. `vroid_help topic=lifecycle` — 创建/打开/保存规则。
3. `vroid_list_groups` 和 `vroid_get_params` — 修改前先检查。
4. 出错时 `vroid_undo`；用 `vroid_screenshot` 确认结果。

同一时间只能打开一个模型。返回模型选择或打开其他文件前请保存。
视觉工作建议：检查 → 只改一处 → 截图 → 继续。""",
        "lifecycle": """# 生命周期

- `vroid_create gender=female|male`：仅在模型选择界面可用；等待模型就绪。
  新模型还没有文件，请用 `vroid_save path=...` 保存。
- `vroid_open path=...`：仅在模型选择界面可用；等待加载完成。
- `vroid_save`：已有文件则原地保存；传入 `path` 即“另存为”。
- `vroid_main_menu`：返回模型选择。有未保存修改时拒绝，除非 `discard=true`。
- `vroid_status`：查看 `modelOpen`、`ready`、`currentFile`、`dirty`、`canSave`。

模型打开时 `vroid_create` / `vroid_open` 会被拒绝。顺序：保存 → `vroid_main_menu` →
创建/打开。生命周期操作没有自动回滚。""",
        "framing": """# 构图与朝向

构图按类别/身体部位配置在 `config/framing.json`，不是按单件服装配置。

- `top` / `bottom`：从模型顶部算起的比例（0 = 头顶，1 = 脚底）。
- `half`：半宽；`null` 表示全宽。
- `distance`：拉远倍率。
- `yaw`：0 = 正面，90 = 侧面，180 = 背面；45/135 = 斜侧。
- `fit`：`region` 或 `full-body`。

`vroid_framing_get` 读取；`vroid_framing_set` 写入本地覆盖；
`vroid_framing_reset` 恢复已提交的默认值。单件物品信息保存在 `catalog.json`。

整套服装使用 `fit=full-body`，确保鞋子可见。后发默认 yaw=180；整套发型默认斜后方。""",
        "thumbnails": """# 预设缩略图

`vroid_preset_cache_build category=...` 按类别生成：

- 移除所有服装、配饰、内衣（包括会在泳装下露出的默认内衣）和头发，仅保留被测项目；
- 拍摄前确认没有其他残留；
- 相机重置为正面，按模型 bounds 居中，并应用类别的 yaw；
- 将 `thumbnailMeta` 写入 `catalog.json`（人体模型、移除的槽位、相机、像素、SHA-1、朝向）；
- 完成后恢复原服装。

`vroid_preset_cache_search` 返回 `preview`（kind/mannequin/clothing/underwear/hair/
orientation/yaw）。旧缩略图在 `refresh=true` 重建前显示 `"unknown"`。
恢复不一定完全一致，拍摄前请保存模型。""",
        "colors": """# 颜色

- 服装没有颜色滑块：使用 `vroid_list_layers` → `vroid_recolor_layer`。
  `multiply` 保留浅色布料阴影；`colorize` 保留亮度并强制色相。
- 头发：`vroid_list_hair_materials` → `vroid_set_hair_color`。预设发型通常改
  `base:<id>` 色调；若颜色画在贴图中，请重着色图层。
- 颜色可能在材质/图层之间共享或全局生效。用 `vroid_screenshot` 检查，必要时
  `vroid_undo`。
- 先用 `vroid_begin_clothing_edit` / `vroid_begin_hair_edit` 打开贴图图层。""",
        "outfit": """# 服装、单件与整套

预设会替换同类别的项目，但整套服装/ClothingSet 可能一次替换多个槽位（上衣、下装、鞋子、
内衣等）。不要假设只改一个槽位。

建议：
1. 应用前后都用 `vroid_list_groups` 检查。
2. 出现多余项目时用 `vroid_remove_item`（组 id 或短类型）移除。
3. 自定义项目用 `vroid_apply_custom`；内置预设用 `vroid_apply_preset`。
4. 截图确认；必要时逐步 undo。

生成缩略图时始终移除默认内衣，这是有意为之，尤其适用于泳装。""",
        "sessions": """# 会话与持久化

- 桥接运行在 VRoid Studio 进程内。VRoid 退出后桥接消失；请重启 VRoid 并重新连接 MCP。
- 通过桥接同时只能打开一个模型。
- 预设缓存（`preset_cache/`）和构图覆盖独立于模型和 VRoid 进程持久化。
- 在 `vroid_main_menu`、`vroid_open`、`vroid_create` 之前保存；这些操作不会自动备份。
- 无法连接时，检查 VRoid 是否运行、BepInEx 插件是否加载。""",
        "errors": """# 常见错误

- **无法连接 VRoid Studio**：启动 VRoid；检查 BepInEx 插件；默认桥接
  http://127.0.0.1:7811。
- **模型已打开**：保存 → `vroid_main_menu` → 创建/打开。
- **有未保存修改**：保存，或确实要放弃时传 `discard=true`。
- **没有缩略图**：先 `vroid_preset_cache_sync`，再
  `vroid_preset_cache_build category=...`。
- **编辑器未就绪 / 正在修改**：等待，调用 `vroid_status` 后重试。
- **画面没有变化**：用 `vroid_list_groups`、`vroid_get_params` 或 `vroid_screenshot`
  检查；预设可能替换了多个槽位。

不确定时调用 `vroid_help topic=tools`。""",
        "languages": """# 语言

- 命令和参数：英文。
- 手册：英文（默认）、法语、日语、简体中文。
- `vroid_help topic=overview lang=en|fr|ja|zh-CN`。
- README-fr.md 和法语网站继续保留；日语、中文手册将基于此帮助内容扩充。
- 工具索引由实际工具注册表自动生成，新工具会自动出现。""",
        "batch": """# 批量操作（下一步）

批量功能已规划但尚未启用。目前请按顺序逐个调用。

计划接口：
- `vroid_batch operations=[{tool, args}, ...]`，最多 200 个操作；
- 顺序执行，不并行访问 VRoid；
- 默认 `stop_on_error=true`，返回部分结果；
- 同一个 MCP 响应中返回文本摘要 + 最多 8 张图片；
- 不允许嵌套批次，不自动回滚；
- 破坏性操作前保存，或之后使用 `vroid_undo`。

在此之前：一次修改 → 一次截图 → 下一步，并利用预设缓存避免盲目尝试。""",
    },
}

HELP["en"]["batch"] = """# Batch operations

`vroid_batch` runs several operations sequentially in one MCP call:

    vroid_batch operations=[
      {"tool":"vroid_status","args":{}},
      {"tool":"vroid_apply_preset","args":{"id":"..."}},
      {"tool":"vroid_screenshot","args":{"path":"..."}}
    ]

Rules:
- up to 200 operations; sequential only, never parallel access to VRoid;
- `stop_on_error=true` by default; partial results are returned with the failing index;
- no nested batches and no `vroid_help` inside a batch;
- no automatic rollback: save first or use `vroid_undo` afterwards;
- text summary + up to 8 images / 16 MiB in the same MCP response; excess images are
  reported by path only.

Lifecycle calls still obey their own rules: `vroid_create`/`vroid_open` require the model
menu, and `vroid_main_menu` can close the model for the following operations."""

HELP["fr"]["batch"] = """# Opérations par lot

`vroid_batch` exécute plusieurs opérations séquentiellement dans un seul appel MCP :

    vroid_batch operations=[
      {"tool":"vroid_status","args":{}},
      {"tool":"vroid_apply_preset","args":{"id":"..."}},
      {"tool":"vroid_screenshot","args":{"path":"..."}}
    ]

Règles :
- jusqu'à 200 opérations ; séquentiel, jamais d'accès parallèle à VRoid ;
- `stop_on_error=true` par défaut ; résultats partiels avec l'index de l'échec ;
- pas de batch imbriqué ni de `vroid_help` dans un batch ;
- pas de rollback automatique : sauvegarder avant, ou `vroid_undo` après ;
- résumé texte + jusqu'à 8 images / 16 Mio dans la même réponse MCP ; au-delà, chemins seuls.

Les appels de cycle de vie gardent leurs règles : `vroid_create`/`vroid_open` exigent le menu,
et `vroid_main_menu` peut fermer le modèle pour les opérations suivantes."""

HELP["ja"]["batch"] = """# バッチ操作

`vroid_batch` は複数操作を 1 回の MCP 呼び出しで順番に実行します:

    vroid_batch operations=[
      {"tool":"vroid_status","args":{}},
      {"tool":"vroid_apply_preset","args":{"id":"..."}},
      {"tool":"vroid_screenshot","args":{"path":"..."}}
    ]

ルール:
- 最大 200 操作。VRoid への並列アクセスはしません。
- 既定 `stop_on_error=true`。失敗した index と部分結果を返します。
- バッチのネスト、バッチ内の `vroid_help` は禁止。
- 自動ロールバックなし。事前に保存するか、後で `vroid_undo`。
- 1 つの MCP 応答にテキスト要約 + 最大 8 画像 / 16 MiB。超過分はパスのみ。

ライフサイクル操作は通常どおりです。`vroid_create`/`vroid_open` はモデル選択が必要で、
`vroid_main_menu` は後続操作のためにモデルを閉じることがあります。"""

HELP["zh"]["batch"] = """# 批量操作

`vroid_batch` 在一次 MCP 调用中顺序执行多个操作：

    vroid_batch operations=[
      {"tool":"vroid_status","args":{}},
      {"tool":"vroid_apply_preset","args":{"id":"..."}},
      {"tool":"vroid_screenshot","args":{"path":"..."}}
    ]

规则：
- 最多 200 个操作；严格顺序执行，不并行访问 VRoid；
- 默认 `stop_on_error=true`，返回失败索引和部分结果；
- 不允许嵌套批次，批次内不允许 `vroid_help`；
- 不自动回滚：操作前保存，或之后使用 `vroid_undo`；
- 同一 MCP 响应返回文本摘要 + 最多 8 张图片 / 16 MiB；超出部分只返回路径。

生命周期操作仍遵守自身规则：`vroid_create` / `vroid_open` 需要模型选择界面，
`vroid_main_menu` 可能为后续操作关闭模型。"""


HELP["en"]["lifecycle"] += (
    "\n\n- `vroid_exit discard=false|true` quits VRoid after sending the response. It refuses unsaved "
    "changes unless discard=true. It cannot be used inside a batch; call it after the batch."
)
HELP["fr"]["lifecycle"] += (
    "\n\n- `vroid_exit discard=false|true` quitte VRoid après avoir envoyé la réponse. Il refuse les "
    "modifications non sauvegardées sauf discard=true. Interdit dans un batch : l'appeler après."
)
HELP["ja"]["lifecycle"] += (
    "\n\n- `vroid_exit discard=false|true` は応答を送ってから VRoid を終了します。未保存の変更は "
    "discard=true でない限り拒否します。バッチ内では使えません。バッチの後に呼び出してください。"
)
HELP["zh"]["lifecycle"] += (
    "\n\n- `vroid_exit discard=false|true` 在发送响应后退出 VRoid。未保存修改默认拒绝，需传 "
    "discard=true。不能在批次内使用，请在批次结束后调用。"
)

HELP["en"]["overview"] += (
    "\n\nFor grouped navigation, use `vroid_sections` → `vroid_categories` → `vroid_enter`, then "
    "`vroid_set_param` with a section/category and a key or short label. The fine-grained tools "
    "(`vroid_list_groups`, `vroid_get_params`, `vroid_set_bone`, etc.) remain available."
)
HELP["fr"]["overview"] += (
    "\n\nPour une navigation groupée : `vroid_sections` → `vroid_categories` → `vroid_enter`, puis "
    "`vroid_set_param` avec section/catégorie et une clé ou un libellé court. Les outils fins "
    "(`vroid_list_groups`, `vroid_get_params`, `vroid_set_bone`, etc.) restent disponibles."
)
HELP["ja"]["overview"] += (
    "\n\nグループ単位の操作: `vroid_sections` → `vroid_categories` → `vroid_enter` の順に選び、"
    "`vroid_set_param` に section/category とキーまたは短いラベルを渡します。細かい操作向けの"
    "既存ツール（`vroid_list_groups`、`vroid_get_params`、`vroid_set_bone` など）も残っています。"
)
HELP["zh"]["overview"] += (
    "\n\n分组操作：`vroid_sections` → `vroid_categories` → `vroid_enter`，然后用 "
    "`vroid_set_param` 传入 section/category 和键名或短标签。细粒度工具"
    "（`vroid_list_groups`、`vroid_get_params`、`vroid_set_bone` 等）仍然可用。"
)

HELP["en"]["colors"] += (
    "\n\nComposite: `vroid_colorize group=... r=... g=... b=... target=both` applies the same color "
    "to global/material colors and texture layers. Use `target=global` or `target=texture` to keep "
    "the fine-grained behavior; the separate tools remain available for surgical edits."
)
HELP["fr"]["colors"] += (
    "\n\nComposite : `vroid_colorize group=... r=... g=... b=... target=both` applique la même couleur "
    "aux couleurs globales/matériaux et aux calques de texture. `target=global` ou `texture` pour "
    "garder le comportement fin ; les outils séparés restent disponibles pour les retouches ciblées."
)
HELP["ja"]["colors"] += (
    "\n\n複合: `vroid_colorize group=... r=... g=... b=... target=both` は同じ色をグローバル/マテリアル "
    "カラーとテクスチャレイヤーの両方に適用します。`target=global` / `texture` で個別指定でき、"
    "細かい調整には既存の個別ツールも使えます。"
)
HELP["zh"]["colors"] += (
    "\n\n复合：`vroid_colorize group=... r=... g=... b=... target=both` 会把同一颜色同时应用到"
    "全局/材质颜色和贴图图层。`target=global` 或 `texture` 可只处理一侧；需要精细调整时仍可使用"
    "独立工具。"
)

HELP["en"]["thumbnails"] += (
    "\n\nLabels and metadata are generated with the thumbnail: `label` (category + number + "
    "dominant colours), `generated.colors`, `generated.tags` (type, colours, plain/patterned) "
    "and `generated.visual` (brightness, edge density). A manual label or annotation always wins; "
    "never treat a generated label as an exact product name."
)
HELP["fr"]["thumbnails"] += (
    "\n\nLes labels et métadonnées sont générés avec la vignette : `label` (catégorie + numéro + "
    "couleurs dominantes), `generated.colors`, `generated.tags` (type, couleurs, plain/patterned) "
    "et `generated.visual` (luminosité, densité de bords). Un label ou une annotation manuelle "
    "gagne toujours ; ne pas traiter un label généré comme un nom produit exact."
)
HELP["ja"]["thumbnails"] += (
    "\n\nラベルとメタデータはサムネイル生成時に作られます: `label`（カテゴリ + 番号 + 主要色）、"
    "`generated.colors`、`generated.tags`（種類、色、plain/patterned）、"
    "`generated.visual`（明るさ、エッジ密度）。手動ラベル/注釈が常に優先されます。生成ラベルは"
    "正確な商品名ではありません。"
)
HELP["zh"]["thumbnails"] += (
    "\n\n标签和元数据随缩略图一起生成：`label`（类别 + 编号 + 主色）、`generated.colors`、"
    "`generated.tags`（类型、颜色、plain/patterned）和 `generated.visual`（亮度、边缘密度）。"
    "手动标签或注释始终优先；不要把自动标签当作精确商品名。"
)


HELP["en"]["export"] = """# VRM export

`vroid_export_vrm` uses VRoid's own exporter, without clicks or a file dialog. The open model is
not modified.

    vroid_export_vrm path=D:\\out\\model.vrm version=1 delete_transparent=true hair=50 hair_bones=50

- `path` is required; `.vrm` is appended when missing.
- `version`: `1` = VRM 1.0 (default), `0` = VRM 0.x.
- `delete_transparent` (default `true`) = VRoid's **Delete Transparent Meshes**.
- `hair_smoothness`, `hair`, `face`, `body`, `outfit`: polygon reduction 0..100.
- `material_mode`: 0 = Default, 1 = 2 materials, 2 = 8, 3 = 12.
- `combine_hair` (default `true`) = Combine Hair Mesh.
- `texture_mode`: 0 = Original, 1 = Shrunk. Shrunk is only accepted with `material_mode=0`.
- `atlas_resolution` with material reduction: 0 = 4096, 1 = 2048.
- `hair_bones`: Reduce Bones / Hair, 0..100.
- The export opens VRoid's export screen and takes about 10-40 s; it returns to the editor
  afterwards by default. `leave=false` leaves the export screen open for manual inspection.

Options refused by VRoid are reported in `warnings`; the response also contains the final
`settings`, byte size and elapsed time. The `.vroid` file itself is not changed, so save before
exporting only if you also want to keep model edits.

`vroid_export_vrm_options` opens the same screen and returns its current settings and the
available material/texture/atlas choices. It closes the screen by default (`leave=true`); use
`leave=false` only when you want to inspect it and continue manually."""

HELP["fr"]["export"] = """# Export VRM

`vroid_export_vrm` utilise l'exporteur natif de VRoid, sans clic ni boîte de dialogue. Le modèle
ouvert n'est pas modifié.

    vroid_export_vrm path=D:\\out\\modele.vrm version=1 delete_transparent=true hair=50 hair_bones=50

- `path` obligatoire ; `.vrm` est ajouté si absent.
- `version` : `1` = VRM 1.0 (défaut), `0` = VRM 0.x.
- `delete_transparent` (défaut `true`) = **Delete Transparent Meshes** de VRoid.
- `hair_smoothness`, `hair`, `face`, `body`, `outfit` : réduction des polygones de 0 à 100.
- `material_mode` : 0 = Default, 1 = 2 matériaux, 2 = 8, 3 = 12.
- `combine_hair` (défaut `true`) = Combine Hair Mesh.
- `texture_mode` : 0 = Original, 1 = Shrunk. Shrunk n'est accepté qu'avec `material_mode=0`.
- `atlas_resolution` avec réduction de matériaux : 0 = 4096, 1 = 2048.
- `hair_bones` : Reduce Bones / Hair, de 0 à 100.
- L'export ouvre l'écran VRM de VRoid et prend environ 10 à 40 s ; il revient ensuite à l'éditeur.
- `leave=false` laisse l'écran d'export ouvert après l'export (pour inspection manuelle) ; défaut `true`.

Les options refusées par VRoid sont listées dans `warnings` ; la réponse contient aussi les
`settings` finaux, la taille et la durée. Le fichier `.vroid` n'est pas modifié.

`vroid_export_vrm_options` ouvre le même écran et renvoie les réglages courants et les choix de
matériaux/textures/atlas. Il referme l'écran par défaut (`leave=true`) ; `leave=false` le laisse
ouvert pour une inspection manuelle."""

HELP["ja"]["export"] = """# VRM 書き出し

`vroid_export_vrm` は VRoid 標準の書き出しを使います。クリックもファイルダイアログも不要で、
開いているモデルは変更されません。

    vroid_export_vrm path=D:\\out\\model.vrm version=1 delete_transparent=true hair=50 hair_bones=50

- `path` は必須。拡張子がなければ `.vrm` を追加します。
- `version`: `1` = VRM 1.0（既定）、`0` = VRM 0.x。
- `delete_transparent`（既定 `true`）= **Delete Transparent Meshes**。
- `hair_smoothness`、`hair`、`face`、`body`、`outfit`: ポリゴン削減 0..100。
- `material_mode`: 0 = Default、1 = 2 マテリアル、2 = 8、3 = 12。
- `combine_hair`（既定 `true`）= Combine Hair Mesh。
- `texture_mode`: 0 = Original、1 = Shrunk。Shrunk は `material_mode=0` のときだけ有効です。
- `atlas_resolution`: マテリアル削減時 0 = 4096、1 = 2048。
- `hair_bones`: Reduce Bones / Hair、0..100。
- 書き出しは VRM 画面を開き、約 10〜40 秒かかります。既定では終了後にエディターへ戻ります。
- `leave=false` にすると、書き出し後も VRM 画面を開いたままにします（手動確認用）。

VRoid が拒否した設定は `warnings` に入ります。応答には最終 `settings`、サイズ、所要時間も
含まれます。`.vroid` ファイル自体は変更されません。

`vroid_export_vrm_options` は同じ画面を開き、現在の設定とマテリアル/テクスチャ/アトラスの
選択肢を返します。既定では画面を閉じます（`leave=true`）。手動で確認する場合だけ
`leave=false` にしてください。"""

HELP["zh"]["export"] = """# VRM 导出

`vroid_export_vrm` 使用 VRoid 自带导出器，无需点击或文件对话框；打开的模型不会被修改。

    vroid_export_vrm path=D:\\out\\model.vrm version=1 delete_transparent=true hair=50 hair_bones=50

- `path` 必填；没有扩展名时自动加 `.vrm`。
- `version`：`1` = VRM 1.0（默认），`0` = VRM 0.x。
- `delete_transparent`（默认 `true`）= **Delete Transparent Meshes**。
- `hair_smoothness`、`hair`、`face`、`body`、`outfit`：多边形削减 0..100。
- `material_mode`：0 = Default，1 = 2 个材质，2 = 8 个，3 = 12 个。
- `combine_hair`（默认 `true`）= Combine Hair Mesh。
- `texture_mode`：0 = Original，1 = Shrunk；只有 `material_mode=0` 时支持 Shrunk。
- `atlas_resolution`（材质削减时）：0 = 4096，1 = 2048。
- `hair_bones`：Reduce Bones / Hair，0..100。
- 导出会打开 VRoid 的 VRM 界面，约需 10–40 秒；默认完成后返回编辑器。
- `leave=false` 会在导出后保留 VRM 界面，便于手动检查。

VRoid 拒绝的选项会出现在 `warnings` 中；响应还包含最终 `settings`、文件大小和耗时。`.vroid`
文件本身不会被修改。

`vroid_export_vrm_options` 会打开同一界面，返回当前设置以及可用的材质/贴图/图集选项。默认
会关闭界面（`leave=true`）；只有需要手动检查时才用 `leave=false`。"""


GROUP_LABELS = {
    "en": {"start": "Start", "lifecycle": "Lifecycle", "export": "VRM export", "framing": "Framing", "inspect": "Inspect & edit",
           "textures": "Textures", "hair": "Hair", "history": "History & capture", "presets": "Presets & cache",
           "body": "Body & camera", "batch": "Batch", "other": "Other"},
    "fr": {"start": "Démarrage", "lifecycle": "Cycle de vie", "export": "Export VRM", "framing": "Cadrage",
           "inspect": "Inspection et édition", "textures": "Textures", "hair": "Cheveux",
           "history": "Historique et capture", "presets": "Presets et cache", "body": "Corps et caméra",
           "batch": "Par lot", "other": "Autres"},
    "ja": {"start": "開始", "lifecycle": "ライフサイクル", "export": "VRM 書き出し", "framing": "構図",
           "inspect": "確認と編集", "textures": "テクスチャ", "hair": "髪", "history": "履歴とキャプチャ",
           "presets": "プリセットとキャッシュ", "body": "体型とカメラ", "batch": "バッチ", "other": "その他"},
    "zh": {"start": "开始", "lifecycle": "生命周期", "export": "VRM 导出", "framing": "构图",
           "inspect": "检查与编辑", "textures": "贴图", "hair": "头发", "history": "历史与截图", "presets": "预设与缓存",
           "body": "身体与相机", "batch": "批量", "other": "其他"},
}

TOOL_GROUPS = [
    ("start", ["vroid_help", "vroid_status"]),
    ("lifecycle", ["vroid_create", "vroid_open", "vroid_save", "vroid_main_menu", "vroid_exit"]),
    ("export", ["vroid_export_vrm", "vroid_export_vrm_options"]),
    ("framing", ["vroid_framing_get", "vroid_framing_set", "vroid_framing_reset"]),
    ("batch", ["vroid_batch"]),
    ("inspect", ["vroid_list_groups", "vroid_sections", "vroid_categories", "vroid_enter",
                 "vroid_get_params", "vroid_set_param", "vroid_set_blendshape", "vroid_set_bone",
                 "vroid_set_color"]),
    ("textures", ["vroid_list_layers", "vroid_colorize", "vroid_recolor_layer", "vroid_export_layer",
                  "vroid_import_layer"]),
    ("hair", ["vroid_list_hair_materials", "vroid_set_hair_color", "vroid_list_hair_groups",
              "vroid_set_procedural_hair", "vroid_scale_brush_hair", "vroid_clone_brush_hair",
              "vroid_begin_hair_edit"]),
    ("history", ["vroid_undo", "vroid_redo", "vroid_screenshot"]),
    ("presets", ["vroid_list_presets", "vroid_apply_preset", "vroid_clothing_colors",
                 "vroid_begin_clothing_edit", "vroid_apply_custom", "vroid_remove_item",
                 "vroid_preset_cache_search", "vroid_preset_cache_annotate", "vroid_preset_thumbnail",
                 "vroid_preset_cache_sync", "vroid_preset_cache_build"]),
    ("body", ["vroid_measure", "vroid_set_body_size", "vroid_camera", "vroid_face_preview"]),
]


def normalize_lang(lang):
    key = (lang or "en").strip().lower()
    return LANG_ALIASES.get(key, "en")


def _required_args(tool):
    req = (tool.get("inputSchema") or {}).get("required") or []
    return ", ".join(req)


def _short_description(tool, limit=220):
    text = " ".join((tool.get("description") or "").split())
    if len(text) > limit:
        text = text[:limit - 1].rstrip() + "…"
    return text


def tool_index(tools, lang):
    lang = normalize_lang(lang)
    labels = GROUP_LABELS[lang]
    by_name = {t["name"]: t for t in tools}
    lines = ["", "## " + TOPICS["tools"][lang], ""]
    used = set()
    for group, names in TOOL_GROUPS:
        present = [n for n in names if n in by_name]
        if not present:
            continue
        lines.append("### " + labels.get(group, group))
        for name in present:
            tool = by_name[name]
            req = _required_args(tool)
            suffix = f" ({req})" if req else ""
            lines.append(f"- `{name}`{suffix} — {_short_description(tool)}")
            used.add(name)
    rest = [t for t in tools if t["name"] not in used]
    if rest:
        lines.append("### " + labels["other"])
        for tool in rest:
            req = _required_args(tool)
            suffix = f" ({req})" if req else ""
            lines.append(f"- `{tool['name']}`{suffix} — {_short_description(tool)}")
    return "\n".join(lines)


def help_text(topic, lang, tools):
    lang = normalize_lang(lang)
    topic = (topic or "overview").strip().lower().lstrip("/")
    if topic in ("", "help", "start", "index"):
        topic = "overview"
    if topic not in TOPICS:
        names = ", ".join(TOPICS)
        return f"Unknown topic: {topic}. Available topics: {names}."
    body = HELP[lang].get(topic, "")
    if topic == "tools":
        body = tool_index(tools, lang)
    header = f"<!-- lang={lang} topic={topic} -->\n"
    return header + body.strip() + "\n"
