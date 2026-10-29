# VRoid Studio 用 MCP ブリッジ

[English](README.md) | [Français](README-fr.md) | **日本語** | [简体中文](README-zh.md)

VRoid Studio で開いているモデルを AI（Claude Code、Claude Desktop、DeepSeek など）から読み取り・編集するローカル MCP ブリッジです。

## 必要環境

- Windows と VRoid Studio 2.14
- **Python 3.12 を同梱**（インストール不要。numpy と Pillow はネットワークがあれば自動導入）
- BepInEx 6 IL2CPP（インストーラーが導入）

Python はパッケージ内の `python\python.exe` が使われるため、PATH の設定は不要です。

## インストール

1. GitHub Releases から `VRoidMcp-Setup-v<version>.exe` を取得します。
2. VRoid Studio を終了し、インストーラーを実行します（管理者権限不要、日本語対応）。
3. Claude Code / Claude Desktop を再起動し、`vroid_status` を呼びます。

インストーラーは BepInEx 6、プラグイン、MCP サーバー、既定のドキュメントを配置します。アンインストールは Windows の「設定 → アプリ」から行えます。失敗した場合のログは `%TEMP%\VRoidMcp-install.log` にあります。

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
