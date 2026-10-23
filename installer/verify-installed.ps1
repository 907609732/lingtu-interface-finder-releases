$ErrorActionPreference='Stop'
$workspace=(Get-Location).Path
$target=Join-Path $env:RUNNER_TEMP 'lingtu-installed-0.5.7'
if(Test-Path -LiteralPath $target){throw 'Test installation target already exists'}
$public=Join-Path $workspace 'public'
$setup=Join-Path $public 'quick-interface-0.5.7-Setup.exe'
$install=Start-Process -FilePath $setup -ArgumentList @('/S',('/PAYLOADDIR="'+$public+'"'),('/D='+$target)) -PassThru -Wait
if($install.ExitCode -ne 0){throw "Installer failed: $($install.ExitCode)"}
$entry=Join-Path $target '团队便携版/桌面端/快速找界面.exe'
if(!(Test-Path -LiteralPath $entry)){throw 'Installed EXE missing'}
$env:QUICK_UI_USER_DATA=Join-Path $env:RUNNER_TEMP 'lingtu-test-profile-0.5.7'
$env:QUICK_TEAM_DATA=Join-Path $env:RUNNER_TEMP 'lingtu-test-data-0.5.7'
$env:QUICK_TEAM_HOST='127.0.0.1';$env:QUICK_TEAM_PORT='5689'
$client=Start-Process -FilePath $entry -WindowStyle Hidden -PassThru
try{
  $health=$null
  for($i=0;$i -lt 90;$i++){try{$health=Invoke-RestMethod http://127.0.0.1:5689/health;break}catch{Start-Sleep -Seconds 1}}
  if($health.version -ne '0.5.7'){throw 'Installed runtime health check failed'}
  $sessionResult=Invoke-RestMethod http://127.0.0.1:5689/api/session -SessionVariable session
  if(!$sessionResult.quickStart -or $sessionResult.version -ne '0.5.7'){throw 'Direct main-interface session failed'}
  $page=Invoke-WebRequest 'http://127.0.0.1:5689/?v=0.5.7'
  if($page.StatusCode -ne 200 -or $page.Content -notlike '*<div id="root">*'){throw 'Main interface failed'}
  $model=$null
  for($i=0;$i -lt 240;$i++){$model=Invoke-RestMethod http://127.0.0.1:5689/api/models -WebSession $session;if($model.ready){break};Start-Sleep -Seconds 1}
  if(!$model.ready -or $model.path -notlike '*bundled-model'){throw ('Installed automatic model loading failed: '+($model|ConvertTo-Json -Compress))}
  $client.Refresh()
  if($client.HasExited){throw 'Desktop client exited unexpectedly'}
  $title=$client.MainWindowTitle
  @{version='0.5.7';installer='NSIS per-user';silentInstall=$true;health=$health;sessionQuickStart=$sessionResult.quickStart;pageStatus=$page.StatusCode;model=$model;windowTitle=$title;offlineModels=$true;fixtureDownloadTest='Local isolated HTTP download, SHA256 and extraction passed';boundaries=@('Real dual-machine NAS/SMB pending','Windows DPI visual acceptance pending','Public GitHub download resume under packet loss not simulated')}|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 (Join-Path $public 'installer-verification.json')
}finally{
  if(!$client.HasExited){Stop-Process -Id $client.Id -Force;$client.WaitForExit(15000)|Out-Null}
  $helper=Join-Path $target 'stop-installed-service.cjs'
  & (Join-Path $target '团队便携版/服务端/bin/node.exe') $helper $target
  if($LASTEXITCODE){throw 'Installed service could not be stopped'}
}
$sentinel=Join-Path $target '团队便携版/服务端/server-data/用户资料保留测试.txt'
New-Item -ItemType Directory -Path (Split-Path $sentinel) -Force|Out-Null
Set-Content -LiteralPath $sentinel 'keep user data'
$extra=Join-Path $target '团队便携版/用户新增文件.txt'
Set-Content -LiteralPath $extra 'keep user additions'
$uninstall=Start-Process -FilePath (Join-Path $target '卸载快速找界面.exe') -ArgumentList @('/S',('_?='+$target)) -Wait -PassThru
if($uninstall.ExitCode -ne 0 -or (Test-Path -LiteralPath $entry)){throw 'Uninstall failed'}
if(!(Test-Path -LiteralPath $sentinel) -or !(Test-Path -LiteralPath $extra)){throw 'Uninstall removed user files'}
if(!(Test-Path -LiteralPath (Join-Path $env:QUICK_TEAM_DATA 'team.sqlite'))){throw 'Workspace data missing after uninstall'}
$report=Get-Content (Join-Path $public 'installer-verification.json') -Raw|ConvertFrom-Json
$report|Add-Member uninstallPreservesData $true
$report|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 (Join-Path $public 'installer-verification.json')
Write-Host 'Installed desktop, local service, bundled models and data-preserving uninstall passed.'
