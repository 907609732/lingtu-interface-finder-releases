"""Build an NSIS web installer from checksum-verified release volumes."""
import argparse,hashlib,json,pathlib,shutil,subprocess

def quote(s):
    return str(s).replace('$','$$').replace('"','$\\"').replace('\n','')

def build(bundle,public,tools,nsis,plugins,version,test_url=None,offline=False):
    bundle=pathlib.Path(bundle).resolve();public=pathlib.Path(public).resolve();tools=pathlib.Path(tools).resolve()
    nsis=pathlib.Path(nsis).resolve();plugins=pathlib.Path(plugins).resolve()
    out=public/('offline-installer-build' if offline else 'installer-build');out.mkdir(exist_ok=True)
    source=pathlib.Path(__file__).resolve().parent
    (out/'web-installer.nsi').write_text((source/'web-installer.nsi').read_text(encoding='utf-8-sig'),encoding='utf-8-sig')
    shutil.copy2(tools/'StdUtils.nsh',out/'StdUtils.nsh')
    parts=sorted(public.glob(f'quick-interface-{version}-windows-x64.7z.*'))
    assert parts and parts[0].suffix=='.001'
    hashes=[(p,hashlib.file_digest(p.open('rb'),'sha256').hexdigest()) for p in parts]
    exe=public/f'quick-interface-{version}-{"OfflineSetup" if offline else "Setup"}.exe'
    config={'VERSION':version,'OUTPUT_EXE':exe,'PLUGIN_DIR':plugins,'DOWNLOAD_URL':f'https://github.com/907609732/lingtu-interface-finder-releases/releases/download/v{version}','DOWNLOAD_GIB':f'{sum(p.stat().st_size for p in parts)/1024**3:.1f}','FIRST_PART':parts[0].name,'SEVEN_EXE':tools/'7za.exe','STOP_HELPER':source/'stop-installed-service.cjs'}
    config['SEVEN_LICENSE']=tools/'7zip-LICENSE.txt'
    config['SEVEN_COPYING']=tools/'7zip-COPYING'
    if offline:config['OFFLINE']='1'
    if test_url:
        assert version=='0.0.0' and test_url.startswith('http://127.0.0.1:')
        config['DOWNLOAD_URL']=test_url
    (out/'generated-config.nsh').write_text('\n'.join(f'!define {k} "{quote(v)}"' for k,v in config.items()),encoding='utf-8-sig')
    (out/'generated-parts.nsh').write_text('\n'.join(f'StrCpy $PartName "{quote(p.name)}"\nStrCpy $PartHash "{h}"\nCall GetPart' for p,h in hashes),encoding='utf-8-sig')
    # Delete only original installed files. Nonrecursive directory removal preserves additions.
    files=sorted(p for p in bundle.rglob('*') if p.is_file())
    lines=[f'Delete "\\\\?\\$INSTDIR\\团队便携版\\{quote(p.relative_to(bundle).as_posix().replace("/",chr(92)))}"' for p in files]
    dirs=sorted((p for p in bundle.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True)
    lines += [f'RMDir "\\\\?\\$INSTDIR\\团队便携版\\{quote(p.relative_to(bundle).as_posix().replace("/",chr(92)))}"' for p in dirs]
    lines += ['RMDir "$INSTDIR\\团队便携版"']
    (out/'generated-uninstall.nsh').write_text('\n'.join(lines),encoding='utf-8-sig')
    subprocess.run([str(nsis),'/V2',str(out/'web-installer.nsi')],check=True)
    report={'version':version,'file':exe.name,'bytes':exe.stat().st_size,'sha256':hashlib.file_digest(exe.open('rb'),'sha256').hexdigest(),'volumes':[{'name':p.name,'sha256':h,'bytes':p.stat().st_size} for p,h in hashes],'installedFiles':len(files),'mode':('offline; local volumes only; no download plugin; ' if offline else 'online; ')+'SHA256 verified; per-user; user data preserved on uninstall'}
    (public/('offline-installer-manifest.json' if offline else 'installer-manifest.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--public',required=True);p.add_argument('--tools',required=True);p.add_argument('--nsis',required=True);p.add_argument('--plugins',required=True);p.add_argument('--version',default='0.5.7')
    p.add_argument('--test-url');p.add_argument('--offline',action='store_true');a=p.parse_args();build(a.bundle,a.public,a.tools,a.nsis,a.plugins,a.version,a.test_url,a.offline)
