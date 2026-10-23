; NSIS online installer; HTTPS download and hashing use electron-builder's plugins.
Unicode true
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "x64.nsh"
!include "StdUtils.nsh"
!include "generated-config.nsh"
!addplugindir "${PLUGIN_DIR}"
Name "快速找界面 ${VERSION}"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\Programs\LingtuInterfaceFinder\${VERSION}"
RequestExecutionLevel user
ManifestDPIAware true
SetCompressor /SOLID lzma
ShowInstDetails show
ShowUninstDetails show
VIProductVersion "${VERSION}.0"
!ifdef OFFLINE
VIAddVersionKey /LANG=2052 "ProductName" "快速找界面完整离线安装器"
!else
VIAddVersionKey /LANG=2052 "ProductName" "快速找界面在线安装器"
!endif
VIAddVersionKey /LANG=2052 "FileDescription" "快速找界面 ${VERSION} 安装程序"
VIAddVersionKey /LANG=2052 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=2052 "LegalCopyright" "Lingtu"
!define MUI_ABORTWARNING
!ifdef OFFLINE
!define MUI_WELCOMEPAGE_TEXT "安装完整程序、运行环境和本地 AI 模型，全程无需联网。$\r$\n$\r$\n请将安装 EXE 与当前版本全部数据分卷放在同一文件夹。安装器会自动校验并解压，缺失或损坏时停止，不会联网补下载。$\r$\n$\r$\n建议为程序准备 15 GiB 可用空间。"
!else
!define MUI_WELCOMEPAGE_TEXT "安装完整程序、运行环境和本地 AI 模型。$\r$\n$\r$\n首次安装需要联网，自动下载并校验约 ${DOWNLOAD_GIB} GiB 文件。安装完成后可离线搜索。$\r$\n$\r$\n请为安装和下载缓存准备至少 20 GiB 可用空间。"
!endif
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp
!define MUI_FINISHPAGE_RUN_TEXT "打开快速找界面"
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"
Var PayloadDir
Var ExplicitPayload
Var PartName
Var PartHash
Var Result
Var Hash

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "此安装程序需要 64 位 Windows。" /SD IDOK
    Abort
  ${EndIf}
  ${GetParameters} $0
  ${GetOptions} $0 "/PAYLOADDIR=" $PayloadDir
  StrCpy $ExplicitPayload ""
  ${If} $PayloadDir != ""
    StrCpy $ExplicitPayload "1"
  ${Else}
!ifdef OFFLINE
    StrCpy $PayloadDir "$EXEDIR"
    StrCpy $ExplicitPayload "1"
!else
    StrCpy $PayloadDir "$LOCALAPPDATA\LingtuInterfaceFinder\downloads\${VERSION}"
!endif
  ${EndIf}
FunctionEnd

Function GetPart
  ${If} ${FileExists} "$PayloadDir\$PartName"
    DetailPrint "正在校验 $PartName"
    ${StdUtils.HashFile} $Hash "SHA2-256" "$PayloadDir\$PartName"
    ${If} $Hash == $PartHash
      Return
    ${EndIf}
    ${If} $ExplicitPayload == "1"
      MessageBox MB_ICONSTOP "本地安装文件校验失败：$PartName。请重新下载此文件。" /SD IDOK
      SetErrorLevel 2
      Abort
    ${EndIf}
  ${ElseIf} $ExplicitPayload == "1"
    MessageBox MB_ICONSTOP "缺少本地安装文件：$PartName。" /SD IDOK
    SetErrorLevel 2
    Abort
  ${EndIf}
!ifndef OFFLINE
  DetailPrint "正在下载 $PartName"
  inetc::get /CAPTION "下载快速找界面 ${VERSION}" /USERAGENT "LingtuInstaller/${VERSION}" /RESUME "网络中断，是否继续下载？" "${DOWNLOAD_URL}/$PartName" "$PayloadDir\$PartName" /END
  Pop $Result
  ${If} $Result != "OK"
    MessageBox MB_ICONSTOP "下载未完成：$Result。已下载文件会保留，重新运行安装器可继续。" /SD IDOK
    SetErrorLevel 3
    Abort
  ${EndIf}
  ${StdUtils.HashFile} $Hash "SHA2-256" "$PayloadDir\$PartName"
  ${If} $Hash != $PartHash
    MessageBox MB_ICONSTOP "下载文件校验失败：$PartName。未开始安装。" /SD IDOK
    SetErrorLevel 2
    Abort
  ${EndIf}
!endif
FunctionEnd

Section "安装完整程序" Main
  ${If} ${FileExists} "$INSTDIR\团队便携版\桌面端\快速找界面.exe"
    MessageBox MB_ICONSTOP "此目录已经安装了程序。请先卸载，或选择另一个安装目录。" /SD IDOK
    SetErrorLevel 4
    Abort
  ${EndIf}
  IfFileExists "$INSTDIR\*.*" 0 directory_ok
    IfFileExists "$INSTDIR\.lingtu-install-id" directory_ok 0
    MessageBox MB_ICONSTOP "请选择空文件夹，避免覆盖已有资料。" /SD IDOK
    SetErrorLevel 4
    Abort
  directory_ok:
  CreateDirectory "$PayloadDir"
  !include "generated-parts.nsh"
  InitPluginsDir
  SetOutPath "$PLUGINSDIR"
  File "${SEVEN_EXE}"
  DetailPrint "正在解压并安装完整程序和 AI 模型，请稍候……"
  CreateDirectory "$INSTDIR"
  nsExec::ExecToLog '"$PLUGINSDIR\7za.exe" x "$PayloadDir\${FIRST_PART}" "-o$INSTDIR" -y -bb0 -bsp0'
  Pop $Result
  ${If} $Result != 0
    MessageBox MB_ICONSTOP "解压失败（$Result）。请检查磁盘空间，保留下载缓存后重新安装。" /SD IDOK
    SetErrorLevel 5
    Abort
  ${EndIf}
  ${IfNot} ${FileExists} "$INSTDIR\团队便携版\桌面端\快速找界面.exe"
    MessageBox MB_ICONSTOP "安装文件不完整，未创建快捷方式。" /SD IDOK
    SetErrorLevel 5
    Abort
  ${EndIf}
  SetOutPath "$INSTDIR"
  File "${STOP_HELPER}"
  File /oname=7zip-LICENSE.txt "${SEVEN_LICENSE}"
  File /oname=7zip-COPYING.txt "${SEVEN_COPYING}"
  FileOpen $0 "$INSTDIR\.lingtu-install-id" w
  FileWrite $0 "LingtuInterfaceFinder:${VERSION}"
  FileClose $0
  WriteUninstaller "$INSTDIR\卸载快速找界面.exe"
  CreateDirectory "$SMPROGRAMS\灵兔"
  CreateShortcut "$SMPROGRAMS\灵兔\快速找界面 ${VERSION}.lnk" "$INSTDIR\团队便携版\桌面端\快速找界面.exe"
  CreateShortcut "$DESKTOP\快速找界面 ${VERSION}.lnk" "$INSTDIR\团队便携版\桌面端\快速找界面.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "DisplayName" "快速找界面 ${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "UninstallString" '$\"$INSTDIR\卸载快速找界面.exe$\"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "DisplayIcon" "$INSTDIR\团队便携版\桌面端\快速找界面.exe"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}" "NoRepair" 1
SectionEnd

Function LaunchApp
  Exec '"$INSTDIR\团队便携版\桌面端\快速找界面.exe"'
FunctionEnd

Function un.onInit
  FileOpen $0 "$INSTDIR\.lingtu-install-id" r
  FileRead $0 $1
  FileClose $0
  ${If} $1 != "LingtuInterfaceFinder:${VERSION}"
    MessageBox MB_ICONSTOP "安装目录标识不匹配，取消卸载以保护资料。" /SD IDOK
    Abort
  ${EndIf}
  ClearErrors
  System::Call 'kernel32::CreateFileW(w "$INSTDIR\团队便携版\桌面端\快速找界面.exe", i 0x80000000, i 0, p 0, i 3, i 0, p 0) p .r0'
  ${If} $0 == -1
    MessageBox MB_ICONSTOP "请先从托盘退出此安装目录中的快速找界面，再卸载。" /SD IDOK
    Abort
  ${EndIf}
  System::Call 'kernel32::CloseHandle(p r0)'
  ExecWait '"$INSTDIR\团队便携版\服务端\bin\node.exe" "$INSTDIR\stop-installed-service.cjs" "$INSTDIR"' $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP "本机服务未能正常停止，未删除程序。请稍后重试。" /SD IDOK
    Abort
  ${EndIf}
FunctionEnd

Section "Uninstall"
  ; Only remove files present in the verified release, never arbitrary data folders.
  !include "generated-uninstall.nsh"
  Delete "$INSTDIR\stop-installed-service.cjs"
  Delete "$INSTDIR\7zip-LICENSE.txt"
  Delete "$INSTDIR\7zip-COPYING.txt"
  Delete "$INSTDIR\卸载快速找界面.exe"
  Delete "$DESKTOP\快速找界面 ${VERSION}.lnk"
  Delete "$SMPROGRAMS\灵兔\快速找界面 ${VERSION}.lnk"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\LingtuInterfaceFinder-${VERSION}"
  DetailPrint "程序已卸载。用户资料、账号设置和新增文件已保留。"
SectionEnd
