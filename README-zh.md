# 适用于 VRoid Studio 的 MCP 桥接

[English](README.md) | [Français](README-fr.md) | [日本語](README-ja.md) | **简体中文**

本地 MCP 桥接，让 AI（Claude Code、Claude Desktop、DeepSeek 等）读取和编辑 VRoid Studio 中打开的模型。

## 环境要求

- Windows 与 VRoid Studio 2.14
- **已内置 Python 3.12**（无需安装；有网络时会自动安装 numpy 和 Pillow）
- BepInEx 6 IL2CPP（由安装器安装）

安装器直接使用包内的 `python\python.exe`，无需配置 PATH。

## 安装

1. 从 GitHub Releases 下载 `VRoidMcp-Setup-v<version>.exe`。
2. 关闭 VRoid Studio，运行安装程序（无需管理员权限，支持中文）。
3. 重启 Claude Code / Claude Desktop，然后调用 `vroid_status`。

安装器会配置 BepInEx 6、插件、MCP 服务器和默认文档。可在 Windows“设置 → 应用”中卸载。安装失败时，日志位于 `%TEMP%\VRoidMcp-install.log`。

## 主要功能（52 个工具）

- 分区/类别/参数的读取与编辑
- 贴图与图层导出、重新导入、改色
- 头发颜色、程序化发束、预设与共享缓存
- 相机、3D 截图、表情预览
- **VRM 导出**（VRM 1.0 / 0.x、删除透明网格、多边形/材质/骨骼精简）
- VRoid 最小化时仍可操作（后台模式始终开启）

## 文档

- [MCP 参考](docs/REFERENCE.md)（法语）
- [贴图编辑](docs/TEXTURES.md)（法语）
- [网站](https://mcjo79.github.io/vroid-mcp/zh/)
- `vroid_help topic=export lang=zh` 查看 VRM 导出帮助

## 许可证

MIT。第三方声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
