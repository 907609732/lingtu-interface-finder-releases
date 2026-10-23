# 快速找界面 0.5.7 全量离线安装包

包含完整软件、Node/Python 运行环境、Chinese-CLIP 和 DINOv2 模型。无需旧版本、无需单独配置 Python、无需联网安装模型。

## 下载全部 4 个文件

请使用“另存为”下载到同一个文件夹，保持以下文件名，不要只下载 EXE：

1. [quick-interface-0.5.7-OfflineSetup.exe（离线安装器）](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-OfflineSetup.exe)
2. [quick-interface-0.5.7-windows-x64.7z.001（数据 1）](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-windows-x64.7z.001)
3. [quick-interface-0.5.7-windows-x64.7z.002（数据 2）](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-windows-x64.7z.002)
4. [quick-interface-0.5.7-windows-x64.7z.003（数据 3）](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-windows-x64.7z.003)

数据文件合计约 4.35 GB（4.05 GiB）。GitHub 每个附件需小于 2 GiB，因此采用分卷；这四个文件共同组成完整离线安装包。数据分卷与已发布的 0.5.7 全量版相同，已下载过的不必重复下载。

## 安装

下载齐后可断开网络，双击 **OfflineSetup.exe**。安装器直接读取同目录分卷，逐个 SHA-256 校验，自动解压并创建桌面快捷方式。不需要手动解压分卷，不需要安装 7-Zip。缺失或损坏时会停止并指明文件，不会联网补下载。

安装时建议为程序留出 15 GiB 空间，数据分卷另外保留约 4.35 GB。安装后双击桌面“快速找界面 0.5.7”进入主界面。内置模型自动加载，搜索在本机处理。打开 Figma 或检查在线更新仍需网络。

资料和程序目录分离；升级前保存编辑内容并从托盘退出。已有资料、GM、Figma 和识别缓存沿用原工作区。卸载仅删除本次安装的文件，保留用户资料和新增文件。

校验值见 `OFFLINE-SHA256SUMS.txt`。安装验证结果见 `offline-installer-verification.json`。程序尚无商业数字签名。真实双机 NAS/SMB 和系统 DPI 视觉验收仍待实机验证。

此发行库只提供软件、说明与组装脚本，不公开项目源码归档。在线安装器 `Setup.exe` 和增量更新包 `update.zip` 仍保留，首次离线安装请选择此处的 **OfflineSetup.exe＋全部三个数据文件**。
