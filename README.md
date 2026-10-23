# 快速找界面 0.5.7

## 首次安装（推荐）

[下载 Windows x64 EXE 安装器](https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v0.5.7/quick-interface-0.5.7-Setup.exe)，双击后按提示安装。

安装器自动下载并逐个校验完整程序、Node/Python 运行环境、Chinese-CLIP 和 DINOv2 模型，创建桌面和开始菜单快捷方式。不需要另外安装 Python 或手动解压。首次安装需要网络，安装后可离线使用。默认安装到当前用户目录，不要求管理员权限；建议准备 20 GiB 空间（包含下载缓存）。程序尚无商业数字签名。

## 离线安装和更新

- 离线搬运：下载当前版本全部 `quick-interface-0.5.7-windows-x64.7z.*` 分卷，放在同一目录，用 7-Zip 从 `.001` 解压。保留整个“团队便携版”目录，双击“桌面端/快速找界面.exe”或“双击这里启动.cmd”。
- 已有 0.5.x：在设置中检查更新，或下载 `quick-interface-0.5.7-update.zip`。更新包复用已有模型，首次安装请用 EXE 安装器。更新前保存编辑内容并退出客户端。
- EXE 安装器也支持本地分卷：`quick-interface-0.5.7-Setup.exe /PAYLOADDIR="D:\下载目录"`，会校验同目录中的当前版本全部分卷。
- 卸载只删除此次安装的程序文件，保留工作区、账号设置、模型查询缓存和后续添加的文件。不会递归删除整个安装目录。

## 本版

单窗口打开新版主界面；顶部统一工具栏；默认资料表，点击单元格填写工程名、GM 和 Figma；设置中可查看并打开实际工作区路径；浅色默认、保留深色主题。模型随完整包安装。工作区和程序目录分离。

校验值见 `SHA256SUMS.txt`，安装器记录见 `installer-manifest.json`，实际测试结果见 `installer-verification.json` 和 `VERIFICATION.md`。真实双机 NAS/SMB 及系统 DPI 视觉验收仍待实机验证。

此仓库只发布程序、说明和发行组装脚本，不公开项目源码归档。旧版本发行文件保留供回退。安装器使用 NSIS（https://nsis.sourceforge.io/）及 electron-builder 的 INetC/StdUtils 插件，解压使用 7-Zip（https://www.7-zip.org/）；模型许可证随程序保存。
