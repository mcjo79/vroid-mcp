; Installer texts (English, French, Japanese, Simplified Chinese).

!macro S ID EN FR JA ZH
  LangString ${ID} ${LANG_ENGLISH} "${EN}"
  LangString ${ID} ${LANG_FRENCH} "${FR}"
  LangString ${ID} ${LANG_JAPANESE} "${JA}"
  LangString ${ID} ${LANG_SIMPCHINESE} "${ZH}"
!macroend

!insertmacro S ReadmeFile "README.md" "README-fr.md" "README-ja.md" "README-zh.md"

!insertmacro S SecBridge "VRoid bridge (required)" "Pont VRoid (requis)" "VRoid ブリッジ（必須）" "VRoid 桥接（必需）"
!insertmacro S DescBridge \
  "BepInEx (if needed), the VRoidMcpBridge plugin, the local MCP server and its embedded Python." \
  "BepInEx (si besoin), le plugin VRoidMcpBridge, le serveur MCP local et son Python embarqué." \
  "BepInEx（必要な場合）、VRoidMcpBridge プラグイン、ローカル MCP サーバーと組み込み Python。" \
  "BepInEx（如需要）、VRoidMcpBridge 插件、本地 MCP 服务器及其内置 Python。"
!insertmacro S SecClaude "Connect Claude Code / Claude Desktop" "Connecter Claude Code / Claude Desktop" "Claude Code / Claude Desktop に接続" "连接 Claude Code / Claude Desktop"
!insertmacro S DescClaude \
  "Declares the vroid MCP server in Claude Code and Claude Desktop (a backup of each config is kept)." \
  "Déclare le serveur MCP vroid dans Claude Code et Claude Desktop (une sauvegarde de chaque configuration est conservée)." \
  "Claude Code と Claude Desktop に vroid MCP サーバーを登録します（設定のバックアップを保持）。" \
  "在 Claude Code 和 Claude Desktop 中注册 vroid MCP 服务器（保留配置备份）。"
!insertmacro S SecDsh "Connect DeepSeek Harness" "Connecter DeepSeek Harness" "DeepSeek Harness に接続" "连接 DeepSeek Harness"
!insertmacro S DescDsh \
  "Adds the connector to DeepSeek Harness when it is installed." \
  "Ajoute le connecteur à DeepSeek Harness s'il est installé." \
  "DeepSeek Harness がインストールされていればコネクタを追加します。" \
  "如已安装 DeepSeek Harness，则添加连接器。"
!insertmacro S SecForceBie "Reinstall BepInEx" "Réinstaller BepInEx" "BepInEx を再インストール" "重新安装 BepInEx"
!insertmacro S DescForceBie \
  "Reinstall BepInEx 6 even if a version is already present (the old one is backed up)." \
  "Réinstalle BepInEx 6 même si une version est déjà présente (l'ancienne est sauvegardée)." \
  "既にある場合でも BepInEx 6 を再インストールします（旧版はバックアップ）。" \
  "即使已存在也重新安装 BepInEx 6（旧版本会备份）。"

!insertmacro S GameHeader "VRoid Studio folder" "Dossier de VRoid Studio" "VRoid Studio のフォルダー" "VRoid Studio 文件夹"
!insertmacro S GameSubHeader "Where VRoidStudio.exe is installed." "Là où se trouve VRoidStudio.exe." "VRoidStudio.exe がある場所。" "VRoidStudio.exe 所在位置。"
!insertmacro S GameTop \
  "The plugin and BepInEx are installed in VRoid Studio's folder. It was searched in your Steam libraries; change it if needed." \
  "Le plugin et BepInEx s'installent dans le dossier de VRoid Studio. Il a été cherché dans vos bibliothèques Steam ; modifiez-le si besoin." \
  "プラグインと BepInEx は VRoid Studio のフォルダーにインストールされます。Steam ライブラリから検出しました。必要なら変更してください。" \
  "插件和 BepInEx 将安装到 VRoid Studio 文件夹。已在 Steam 库中查找；如有需要请修改。"
!insertmacro S GameDest "VRoid Studio folder" "Dossier de VRoid Studio" "VRoid Studio のフォルダー" "VRoid Studio 文件夹"
!insertmacro S GameNotFound \
  "VRoidStudio.exe was not found in this folder. Choose VRoid Studio's installation folder." \
  "VRoidStudio.exe est introuvable dans ce dossier. Choisissez le dossier d'installation de VRoid Studio." \
  "このフォルダーに VRoidStudio.exe がありません。VRoid Studio のインストールフォルダーを選んでください。" \
  "此文件夹中找不到 VRoidStudio.exe。请选择 VRoid Studio 的安装文件夹。"
!insertmacro S InstTop \
  "Folder of the MCP server, its embedded Python and the preset cache (no administrator rights needed)." \
  "Dossier du serveur MCP, de son Python embarqué et du cache des presets (aucun droit administrateur requis)." \
  "MCP サーバー、組み込み Python、プリセットキャッシュのフォルダー（管理者権限は不要）。" \
  "MCP 服务器、内置 Python 和预设缓存所在文件夹（无需管理员权限）。"

!insertmacro S VRoidRunning \
  "VRoid Studio is open. Save your work, close it, then click Retry." \
  "VRoid Studio est ouvert. Enregistrez votre travail, fermez-le, puis cliquez sur Réessayer." \
  "VRoid Studio が起動しています。作業を保存して終了し、「再試行」を押してください。" \
  "VRoid Studio 正在运行。请保存工作并关闭，然后点击“重试”。"
!insertmacro S Extracting "Extracting files..." "Extraction des fichiers..." "ファイルを展開しています..." "正在解压文件..."
!insertmacro S InstallFailed \
  "Installation failed. The details are in the log above" \
  "L'installation a échoué. Le détail est dans le journal ci-dessus" \
  "インストールに失敗しました。詳細は上のログを参照してください" \
  "安装失败。详情见上方日志"
!insertmacro S UninstallShortcut "Uninstall" "Désinstaller" "アンインストール" "卸载"

!insertmacro S FinishTitle "VRoid is connected" "VRoid est connecté" "VRoid の接続が完了しました" "VRoid 已连接"
!insertmacro S FinishText \
  "Restart Claude Code / Claude Desktop to see the vroid_* tools.$\r$\n$\r$\nThe first VRoid Studio launch after installing BepInEx takes one or two extra minutes.$\r$\n$\r$\nCheck: with VRoid open, http://127.0.0.1:7811/status answers." \
  "Redémarrez Claude Code / Claude Desktop pour voir les outils vroid_*.$\r$\n$\r$\nLe premier lancement de VRoid Studio après l'installation de BepInEx prend une à deux minutes de plus.$\r$\n$\r$\nVérification : VRoid ouvert, http://127.0.0.1:7811/status répond." \
  "vroid_* ツールを使うには Claude Code / Claude Desktop を再起動してください。$\r$\n$\r$\nBepInEx 導入後の最初の VRoid Studio 起動は 1〜2 分長くかかります。$\r$\n$\r$\n確認：VRoid を開いた状態で http://127.0.0.1:7811/status が応答します。" \
  "请重启 Claude Code / Claude Desktop 以使用 vroid_* 工具。$\r$\n$\r$\n安装 BepInEx 后首次启动 VRoid Studio 会多花一到两分钟。$\r$\n$\r$\n检查：打开 VRoid 后，http://127.0.0.1:7811/status 应有响应。"
!insertmacro S FinishReadme "Open the README" "Ouvrir le README" "README を開く" "打开 README"
!insertmacro S FinishLink "Project website" "Site du projet" "プロジェクトのサイト" "项目网站"

!insertmacro S UnSecBridge "Plugin, server and connectors" "Plugin, serveur et connecteurs" "プラグイン、サーバー、コネクタ" "插件、服务器和连接器"
!insertmacro S UnDescBridge \
  "Removes the plugin from VRoid Studio, the MCP server, its Python and the Claude / DeepSeek Harness entries." \
  "Retire le plugin de VRoid Studio, le serveur MCP, son Python et les entrées Claude / DeepSeek Harness." \
  "VRoid Studio のプラグイン、MCP サーバー、Python、Claude / DeepSeek Harness の登録を削除します。" \
  "删除 VRoid Studio 中的插件、MCP 服务器及其 Python，以及 Claude / DeepSeek Harness 中的条目。"
!insertmacro S UnSecBie "BepInEx" "BepInEx" "BepInEx" "BepInEx"
!insertmacro S UnDescBie \
  "Also removes BepInEx and its backups from VRoid Studio. Leave unchecked if you use other BepInEx plugins." \
  "Retire aussi BepInEx et ses sauvegardes de VRoid Studio. Laissez décoché si vous utilisez d'autres plugins BepInEx." \
  "BepInEx とそのバックアップも削除します。他の BepInEx プラグインを使う場合はチェックしないでください。" \
  "同时从 VRoid Studio 删除 BepInEx 及其备份。如使用其他 BepInEx 插件请勿勾选。"
!insertmacro S UnSecCache "Preset cache" "Cache des presets" "プリセットキャッシュ" "预设缓存"
!insertmacro S UnDescCache \
  "Also deletes the preset thumbnails and your annotations." \
  "Supprime aussi les vignettes des presets et vos annotations." \
  "プリセットのサムネイルと注釈も削除します。" \
  "同时删除预设缩略图和你的标注。"
!insertmacro S UnCleanupWarn \
  "Some items could not be removed; see the log" \
  "Certains éléments n'ont pas pu être retirés ; voir le journal" \
  "一部の項目を削除できませんでした。ログを参照してください" \
  "部分项目无法删除；请查看日志"
