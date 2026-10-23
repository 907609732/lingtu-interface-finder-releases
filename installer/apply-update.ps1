param([string]$Target,[switch]$NoStart,[string]$PackageRoot=$PSScriptRoot,[switch]$RestartDesktop)
$ErrorActionPreference='Stop'
if (-not $Target) { $Target=Read-Host '请输入原有「团队便携版」文件夹的完整路径' }
$taskTarget=(Resolve-Path -LiteralPath $Target).Path
if (-not (Test-Path -LiteralPath (Join-Path $taskTarget '服务端/server/start.cjs'))) { throw '请选择完整的团队便携版目录' }
$taskPayload=Join-Path $PackageRoot 'payload'
$taskManifest=Get-Content -LiteralPath (Join-Path $PackageRoot 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$taskCurrent=Get-Content -LiteralPath (Join-Path $taskTarget '服务端/package.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($taskCurrent.version -notmatch '^0\.5\.\d+$' -or $taskManifest.version -notmatch '^0\.5\.\d+$' -or [version]$taskCurrent.version -gt [version]$taskManifest.version) { throw '此更新包适用于 0.5.x 团队便携版，不支持降级' }
$taskFiles=@()
foreach ($taskEntry in $taskManifest.files) {
  $taskRelative=$taskEntry.path.Replace('/',[IO.Path]::DirectorySeparatorChar)
  if ([IO.Path]::IsPathRooted($taskRelative) -or $taskRelative.Split([IO.Path]::DirectorySeparatorChar) -contains '..') { throw '更新包路径无效' }
  if ($taskRelative -match '(^|[\\/])(server-data|logs|模型包|models)([\\/]|$)') { throw '更新包不能修改用户数据或模型' }
  $taskSource=[IO.Path]::GetFullPath((Join-Path $taskPayload $taskRelative))
  $taskDestination=[IO.Path]::GetFullPath((Join-Path $taskTarget $taskRelative))
  if (-not $taskDestination.StartsWith($taskTarget+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw '更新路径越界' }
  if ((Get-FileHash -LiteralPath $taskSource -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskEntry.sha256) { throw "更新包校验失败：$taskRelative" }
  if ((Test-Path -LiteralPath $taskDestination -PathType Leaf) -and (Get-FileHash -LiteralPath $taskDestination -Algorithm SHA256).Hash.ToLowerInvariant() -eq $taskEntry.sha256) { continue }
  $taskFiles+=@{relative=$taskRelative;source=$taskSource;destination=$taskDestination}
}
$taskBackup=Join-Path $taskTarget ('升级备份/'+$taskManifest.version+'-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $taskBackup | Out-Null
$taskStop=Join-Path $taskTarget '停止团队服务器.ps1'
if (Test-Path -LiteralPath $taskStop) { & $taskStop }
$taskLock=Join-Path $taskTarget '服务端/server-data/server.lock'
if (Test-Path -LiteralPath $taskLock) {
  $taskLockData=Get-Content -LiteralPath $taskLock -Raw -Encoding UTF8 | ConvertFrom-Json
  if (Get-Process -Id $taskLockData.pid -ErrorAction SilentlyContinue) { throw '服务器尚未停止，未覆盖程序文件，请稍后重试' }
}
$taskApplied=@()
try {
  foreach ($taskFile in $taskFiles) {
    $taskSaved=Join-Path $taskBackup $taskFile.relative
    if (Test-Path -LiteralPath $taskFile.destination) {
      New-Item -ItemType Directory -Force -Path (Split-Path $taskSaved) | Out-Null
      Copy-Item -LiteralPath $taskFile.destination -Destination $taskSaved
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $taskFile.destination) | Out-Null
    Copy-Item -LiteralPath $taskFile.source -Destination $taskFile.destination -Force
    $taskApplied+=$taskFile
  }
} catch {
  foreach ($taskFile in $taskApplied) {
    $taskSaved=Join-Path $taskBackup $taskFile.relative
    if (Test-Path -LiteralPath $taskSaved) { Copy-Item -LiteralPath $taskSaved -Destination $taskFile.destination -Force }
  }
  throw "更新未完成，已恢复覆盖过的旧文件。请关闭桌面端后重试。备份：$taskBackup。$($_.Exception.Message)"
}
Write-Host "已更新到 $($taskManifest.version)；旧程序文件保存在：$taskBackup"
Write-Host '刷新网页使用新版；用户资料、模型与历史保持原位置。'
if (-not $NoStart) {
  if ($RestartDesktop) {
    Start-Process -FilePath (Join-Path $taskTarget '桌面端/快速找界面.exe') -WorkingDirectory $taskTarget
  } else { & (Join-Path $taskTarget '启动团队服务器.ps1') -NoOpen }
}
