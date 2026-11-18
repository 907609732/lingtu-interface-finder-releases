# 快速找界面 · 游戏 UI 资料库与本地搜图

**简体中文（默认）** | [English](README.en.md)

按游戏系统和文件夹整理界面截图、工程名、Figma 链接与 GM 说明，使用资料表、图片画册及本地相似图搜索查找参考。

[下载与发行记录](https://github.com/907609732/lingtu-interface-finder-releases/releases) · [ArtHub 普通文件夹同步指南](docs/folder-package-sync.zh-CN.md)

## 版本与下载

文档更新于 **2026-11-18**。当前下载与历史版本：

| 类型             | 版本与入口                                                                                                              | 使用方式                                 |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 当前双版本 | [0.7.5 · 发行页](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.7.5) | 独立 APP 完整 ZIP／兼容宿主扩展 ZIP |
| 已发布扩展       | [0.7.4 · AI资源领航扩展版](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/extension-v0.7.4) | 在兼容宿主中导入扩展 ZIP                 |
| 历史独立版       | [0.5.7 · EXE 安装版](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.5.7)                 | 用于旧版独立安装及回退                   |
| 历史离线试用版   | [0.5.8 · 精简全量试用版](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.5.8)             | 下载同版全部分卷与离线安装 EXE           |
| 独立 AI 模型     | [TensorRT for RTX 模型包](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/models-rtx-1)      | 在兼容版本的模型设置中导入               |
| 普通目录同步 | [ArtHub 同步指南](docs/folder-package-sync.zh-CN.md) | 0.7.5 已包含；旧文件夹包仅只读迁移 |

请使用 **0.7.5 专用下载链接**。为兼容旧版自动更新器，`releases/latest` 和旧更新源保持历史版本；两个完整 ZIP 不用于旧版增量更新。

## 0.7.5 更新

普通文件夹直接同步取代人工提交打包，缓存留在本机；同时优化主题标题栏、紧凑布局、字段摘要展开、本机回收站图片预览和 AI 增量索引调度。[云端检查](https://github.com/907609732/lingtu-interface-finder-releases/actions/runs/44303948563)及同次最终下载包的本机隔离运行验收通过。本轮未进行真实 ArtHub 双机传输或 GPU 推理验收。

## 可以做什么

- **资料表整理**：按系统、文件夹及子文件夹管理资料，填写工程名、UI／拼接 Figma 链接和 GM；直接编辑单元格。
- **图片与画册**：行内查看附件，打开画册浏览原图；支持图片改名、删除确认和恢复。
- **浏览与筛选**：切换布局、字段、筛选和排序，调整列宽、行高及资料表尺寸；界面默认浅色，可切换深色。
- **截图找图**：粘贴截图或选择图片，使用本地 Chinese-CLIP＋DINOv2 检索相似界面；相似度是候选排序依据，不是正确率。
- **修订与冲突**：保留资料历史，查看和恢复旧版本；多人修改同一资料时保留冲突分支，避免静默覆盖。
- **本机媒体预览**：支持图片、视频、音频及部分工程附件，具体格式能力以对应版本说明为准。

## 安装 0.7.5 扩展版

1. 使用已接入 `hostApi: 1` 工作台扩展接口的 AI资源领航。
2. 从 [0.7.5 发行页](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.7.5)下载 `quick-interface-finder-0.7.5-extension.zip`。
3. 关闭正在运行的快速找界面工作台，在宿主的“更多功能 → 快速找界面”管理入口导入 ZIP，无需手工解压。
4. 打开工作台，选择已有资料库。需要 AI 搜图时，再下载或导入独立模型包。

此 ZIP 是工作台扩展，不是独立 EXE、宿主安装器或旧版更新器所用的 `update.zip`。旧宿主需要先升级到支持该接口的版本。

### 独立 APP 完整版

从 [0.7.5 发行页](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/v0.7.5)下载 `quick-interface-finder-0.7.5-app-windows-x64.zip`，解压完整目录后双击“快速找界面.exe”。不要覆盖旧版正在运行的目录。功能与验证范围见[版本说明](docs/0.7.5-版本说明.md)。

## 普通文件夹直接由 ArtHub 同步

> **0.7.5 已包含以下流程。** 历史 `extension-v0.7.4` 与 0.5.x 安装包不包含。

```text
修改资料 → 直接保存普通文件夹（原图＋不可变修订）
       → ArtHub 同步该文件夹
       → 其他电脑打开同一文件夹，直接读取资料与历史
```

资料库不再生成文件夹 ZIP、提交日志或人工发布步骤。没有“提交更新”按钮，也不会自动解包；保存即写入共享目录，ArtHub 负责传输。**SQLite、query-cache、缩略图/预览、AI 模型与索引、显卡缓存、任务和回收站只留在本机，不写入共享文件夹。**

首次接入时选择已有 ArtHub 资料库文件夹，或新建一个空文件夹。多人修改同一资料时继续保留冲突分支，不静默覆盖。

旧 `format 3 / folder-packages` 项目只读兼容：首次打开不会自动创建空库，需显式“迁移旧文件夹包到普通资料库”。迁移先复制到旁路普通目录并校验文件哈希、修订和原件，保留本机未提交修改、冲突、待发布快照、远端独有提交和本机回收站；失败不切换，旧目录、包、state、outgoing、archives 和回收站不删除。详见[中文同步与迁移指南](docs/folder-package-sync.zh-CN.md)。

## 历史实现与验证边界

2026-11-12 曾在隔离开发环境验证“每文件夹一个包＋人工提交”，包括只保存草稿、人工发布 ZIP＋JSON、第二端接收和修订/原图哈希一致。该日常流程已被普通文件夹直连取代，记录仅用于历史追溯。

旧演示使用本地文件复制模拟传输，**不等于真实 ArtHub 云端或两台物理电脑的验收**。普通文件夹模式仍需在真实 ArtHub 双机、离线恢复和并发同步环境中验收；写入目录成功也不代表云端上传完成。

## AI 模型与运行环境

- 当前桌面目标为 Windows x64。扩展复用宿主 Electron，并带独立推理运行环境与媒体工具，不内置模型权重或用户资料。
- 兼容的 TensorRT for RTX 模型面向 NVIDIA RTX 30／40／50 系列；已验证设备为 RTX 3080 Ti，其他显卡以实际兼容测试为准。
- 在“设置 → 本地 AI 模型”在线下载，或从[模型发布页](https://github.com/907609732/lingtu-interface-finder-releases/releases/tag/models-rtx-1)下载 ZIP 后离线导入。无需另装 Python、PyTorch 或 CUDA Toolkit。
- 未安装模型时，仍可管理资料并搜索文字字段。旧 PyTorch 模型不能直接导入 RTX 模型环境。
- 普通文件夹模式下，各电脑独立生成图片索引、预览和特征缓存；这些内容不会写入 ArtHub 共享目录。

## 旧版独立安装与回退

[0.5.7 EXE 安装器](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-Setup.exe)会下载并校验该旧版程序、运行环境和内置模型。首次安装需联网，建议准备 20 GiB 空间（包含缓存）。历史安装器没有商业数字签名。

离线使用时下载同版全部 `.7z.*` 分卷到一个目录，从 `.001` 解压并保留完整程序目录。0.5.8 离线试用版需同时下载发行页列出的 EXE 和两个数据分卷。已有 0.5.x 用户按对应发行说明使用更新包，不能用扩展 ZIP 代替旧更新包。

旧版本发行文件保留供回退。旧文件夹包迁移只会生成新目录中的普通资料库副本，保留旧目录及其包、状态和回收站；切回旧库前，应另外保留迁移后新增的修改。

## 数据与发行边界

此公开仓库提供发行文件、使用说明及发行组装脚本，不公开应用源码归档。用户资料、本机配置、识别数据库与模型权重不会作为本次文档提交上传。

校验值、许可证、签名及设备验收范围以各发行页和包内说明为准。真实 ArtHub 双机传输、占位文件下载、低配设备和大规模图库性能仍需单独验收。

---

[English documentation](README.en.md) · [ArtHub 普通文件夹同步指南](docs/folder-package-sync.zh-CN.md) · [全部发行记录](https://github.com/907609732/lingtu-interface-finder-releases/releases)
