# 适用于 VRoid Studio 的 MCP 桥接

[English](README.md) | [Français](README-fr.md) | [日本語](README-ja.md) | **简体中文**

本地 MCP 桥接，让 AI（Claude Code、Claude Desktop、DeepSeek Harness 等）读取和编辑 VRoid Studio 中打开的模型。

## 环境要求

- Windows 10 / 11 与 VRoid Studio 2.16（Steam）
- **已内置 Python 3.12、numpy 和 Pillow**。无需安装 Python，也无需配置 PATH。
- BepInEx 6 IL2CPP（由安装器安装）
- 无需管理员权限。

## 安装

1. 从 GitHub Releases 下载 **`VRoidMcp-Setup-v<version>.exe`**。
2. **完全退出 VRoid Studio 和 Claude Desktop**（Claude Desktop 需从托盘退出）。
3. 运行安装程序。支持中文等四种语言，无需管理员权限，也不会打开控制台。
   - 可选择 Claude Code / Claude Desktop、DeepSeek Harness、重新安装 BepInEx。
   - VRoid Studio 文件夹会从 Steam 库自动检测（找不到时可手动浏览）。
4. 启动 VRoid Studio（BepInEx 首次启动会多花 1–2 分钟）。
5. 重启 Claude Code / Claude Desktop / DeepSeek Harness，然后调用 `vroid_status`。

安装器会配置 BepInEx 6、插件、MCP 服务器、Python 3.12、numpy、Pillow 和默认文档。它会出现在 Windows“设置 → 应用”中，并创建卸载程序和开始菜单快捷方式。日志位于 `%TEMP%\VRoidMcp-install.log`。

静默安装：

```bat
VRoidMcp-Setup-v<version>.exe /S /GAMEDIR="<VRoid Studio 文件夹>" /NOCLAUDE /NODSH
```

卸载：

```bat
Uninstall-VRoidMcp.exe /S /REMOVEBEPINEX /REMOVECACHE
```

## 0.12 新功能

- **Windows 安装器（NSIS）**：用四语言标准向导替代 `Installer.cmd`，无需管理员权限，也没有控制台窗口。
- **内置 Python 3.12 + numpy + Pillow**：无需网络，也无需 `pip`；0.11 的“Python 3.8+ 在 PATH 中”要求已取消。
- **DeepSeek Harness 连接器**：在 Web / Desktop 的所有配置文件中注册 `vroid` 服务器。
- **VRoid Studio 2.16 / Unity 6 稳定性**：首次加载编辑器时最多等待 120 秒。
- **预设缓存保护**：当 VRoid 处于模型选择界面或无法读取自定义项目时，不再把现有缓存标记为已删除。

## 主要功能（52 个工具）

- 分区/类别/参数的读取与编辑
- 贴图与图层导出、重新导入、改色
- 头发颜色、程序化发束、预设与共享缓存
- 相机、3D 截图、表情预览
- **VRM 导出**（VRM 1.0 / 0.x、删除透明网格、多边形/材质/骨骼精简）
- VRoid 最小化时仍可操作（后台模式始终开启）

## 文档

- **面向代理的英文参考**: [AGENT_REFERENCE_EN.md](docs/AGENT_REFERENCE_EN.md) — 52 个工具、每个分区/类别的参数、身体尺寸和表情限制
- [MCP 参考](docs/REFERENCE.md)（法语）
- [贴图编辑](docs/TEXTURES.md)（法语）
- [网站](https://mcjo79.github.io/vroid-mcp/zh/)
- `vroid_help topic=export lang=zh` 查看 VRM 导出帮助

## 许可证

MIT。第三方声明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
