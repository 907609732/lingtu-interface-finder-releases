"""Release-only assembly: overlay verified components onto an existing public runtime."""
import argparse,hashlib,json,pathlib,shutil,subprocess,zipfile

VERSION='0.5.7'
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def overlay():
    components=pathlib.Path('components');payload=components/'payload';bundle=pathlib.Path('bundle/团队便携版')
    m=json.loads((components/'manifest.json').read_text(encoding='utf-8'));assert m['version']==VERSION
    for entry in m['files']:
        rel=pathlib.PurePosixPath(entry['path']);assert not rel.is_absolute() and '..' not in rel.parts
        source=payload/rel;assert sha(source)==entry['sha256'],str(rel)
    shutil.copytree(payload,bundle,dirs_exist_ok=True)
    assert not (bundle/'服务端/server-data').exists()
    model=json.loads((bundle/'桌面端/resources/bundled-model/manifest.json').read_text(encoding='utf-8'))
    for record in model['models']:
        for f in record['files']:
            file=bundle/'桌面端/resources/bundled-model'/f['path']
            assert file.stat().st_size==f['size'] and sha(file)==f['sha256'],f['path']
    assert json.loads((bundle/'服务端/package.json').read_text(encoding='utf-8'))['version']==VERSION
    (bundle/'cloud-verification.json').unlink(missing_ok=True)
    print('Components, bundled model weights and package versions verified.',flush=True)

def archives():
    public=pathlib.Path('public');public.mkdir(exist_ok=True)
    update=pathlib.Path('update')/(VERSION+'更新包');update.mkdir(parents=True)
    shutil.copytree('components/payload',update/'payload')
    shutil.copy2(pathlib.Path(__file__).parent/'apply-update.ps1',update/'更新程序.ps1')
    (update/'更新程序.cmd').write_text('@echo off\r\nchcp 65001 >nul\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0更新程序.ps1"\r\npause\r\n',encoding='utf-8')
    (update/'manifest.json').write_text((pathlib.Path('components')/'manifest.json').read_text(encoding='utf-8'),encoding='utf-8')
    target=public/f'quick-interface-{VERSION}-update.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in sorted(update.rglob('*')):
            if f.is_file():z.write(f,pathlib.Path(update.name)/f.relative_to(update))
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    assert target.stat().st_size<1_000_000_000
    (public/'update.json').write_text(json.dumps({'application':'quick-interface-team','version':VERSION,'bytes':target.stat().st_size,'sha256':sha(target),'url':f'https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v{VERSION}/{target.name}','notes':'单窗口新版、顶部单行工具栏、默认资料表和单元格直接编辑。保留已有模型、工作区与索引。首次安装推荐 EXE 在线安装器。'},ensure_ascii=False,indent=2),encoding='utf-8')
    subprocess.run(['7z','a','-t7z','-mx1','-mmt=4','-v1900m',str((public/f'quick-interface-{VERSION}-windows-x64.7z').resolve()),'团队便携版'],cwd='bundle',check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['7z','t',str(public/f'quick-interface-{VERSION}-windows-x64.7z.001')],check=True,stdout=subprocess.DEVNULL)
    print('Update and full split archives verified.',flush=True)

def finish():
    public=pathlib.Path('public')
    manifest=json.loads((public/'installer-manifest.json').read_text(encoding='utf-8'))
    assert (public/manifest['file']).exists() and sha(public/manifest['file'])==manifest['sha256']
    for f in public.iterdir():
        if f.is_file():assert f.stat().st_size<2*1024**3,f.name
    text=''.join(f'{sha(p)}  {p.name}\n' for p in sorted(public.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt')
    (public/'SHA256SUMS.txt').write_text(text,encoding='utf-8')
    print('Final release manifest written.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('step',choices=['overlay','archives','finish']);a=p.parse_args();globals()[a.step]()
