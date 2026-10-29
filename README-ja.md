# VRoid Studio 用 MCP ブリッジ

[English](README.md) | [Français](README-fr.md) | **日本語** | [简体中文](README-zh.md)

VRoid Studio で開いているモデルを AI（Claude Code、Claude Desktop、DeepSeek Harness など）から読み取り・編集するローカル MCP ブリッジです。

## 必要環境

- Windows 10 / 11 と VRoid Studio 2.16（Steam）
- **Python 3.12、numpy、Pillow を同梱**。Python のインストールも PATH の設定も不要です。
- BepInEx 6 IL2CPP（インストーラーが導入）
- 管理者権限は不要です。

## インストール

1. GitHub Releases から **`VRoidMcp-Setup-v<version>.exe`** を取得します。
2. **VRoid Studio と Claude Desktop を完全に終了**します（Claude Desktop はトレイから終了）。
3. インストーラーを実行します。日本語を含む 4 言語対応、管理者権限不要、コンソールなしです。
   - Claude Code / Claude Desktop、DeepSeek Harness、BepInEx の再インストールを選択できます。
   - VRoid Studio のフォルダーは Steam ライブラリから自動検出されます（見つからない場合は「参照」）。
4. VRoid Studio を起動します（BepInEx 初回起動は 1〜2 分余分にかかります）。
5. Claude Code / Claude Desktop / DeepSeek Harness を再起動し、`vroid_status` を呼びます。

インストーラーは BepInEx 6、プラグイン、MCP サーバー、Python 3.12、numpy、Pillow、既定のドキュメントを配置します。Windows の「設定 → アプリ」に登録され、アンインストーラーとスタートメニューのショートカットが作成されます。ログは `%TEMP%\VRoidMcp-install.log` にあります。

サイレントインストール:

```bat
VRoidMcp-Setup-v<version>.exe /S /GAMEDIR="<VRoid Studio フォルダー>" /NOCLAUDE /NODSH
```

アンインストール:

```bat
Uninstall-VRoidMcp.exe /S /REMOVEBEPINEX /REMOVECACHE
```

## 0.12 の新機能

- **Windows インストーラー（NSIS）**: `Installer.cmd` の代わりに、4 言語の標準ウィザード。管理者権限もコンソールも不要です。
- **Python 3.12 + numpy + Pillow を同梱**: ネットワークも `pip` も不要。0.11 の「Python 3.8+ を PATH に」という条件はなくなりました。
- **DeepSeek Harness コネクター**: Web / Desktop のすべてのプロファイルに `vroid` サーバーを登録します。
- **VRoid Studio 2.16 / Unity 6 の安定性**: セッション最初のエディター読み込みを最大 120 秒待機します。
- **プリセットキャッシュ保護**: VRoid がモデル選択画面にあるときやカスタム項目を読めないときに、既存のキャッシュを「削除済み」にしません。

## 主な機能（52 ツール）

- セクション／カテゴリ／パラメータの読み取りと編集
- テクスチャとレイヤーの書き出し・再読み込み・色変更
- 髪の色、手続き型ヘア、プリセットと共有キャッシュ
- カメラ、3D キャプチャ、表情プレビュー
- **VRM 書き出し**（VRM 1.0 / 0.x、透明メッシュ削除、ポリゴン・マテリアル・ボーン削減）
- VRoid を最小化したまま操作（バックグラウンド動作は常時有効）

## ドキュメント

- [MCP リファレンス](docs/REFERENCE.md)（フランス語）
- [テクスチャ編集](docs/TEXTURES.md)（フランス語）
- [Web サイト](https://mcjo79.github.io/vroid-mcp/ja/)
- `vroid_help topic=export lang=ja` で VRM 書き出しのヘルプ

## ライセンス

MIT。第三者通知は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。
