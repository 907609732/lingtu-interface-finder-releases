"""Copy a release into fresh staging, excluding build-only worker files.

Uses the existing runtime and model versions; never edits the source release.
All DLL/PYD files, Python source, metadata and licenses are preserved.
"""
import argparse,hashlib,json,pathlib,shutil,subprocess

DEV_SUFFIXES={'.lib','.pdb','.h','.hpp','.hxx','.cuh'}
FRONTEND={'@tanstack/react-table','@types/three','lucide-react','react','react-dom','three','wavesurfer.js'}

def excluded(relative):
    rel=pathlib.PurePosixPath(str(relative).replace('\\','/'))
    return rel.parts[:3]==('桌面端','resources','worker') and ('__pycache__' in rel.parts or rel.suffix.lower() in DEV_SUFFIXES or rel.suffix.lower()=='.pyc')

def sha(file):
    with file.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def package(source,destination,version):
    source=pathlib.Path(source).resolve();destination=pathlib.Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(source) or source.is_relative_to(destination):raise ValueError('Use a fresh directory outside the source release')
    if (source/'服务端/server-data').exists():raise ValueError('Source includes a user workspace')
    assert (source/'桌面端/resources/bundled-model/manifest.json').is_file()
    files=[p for p in source.rglob('*') if p.is_file()]
    removed=[{'path':p.relative_to(source).as_posix(),'bytes':p.stat().st_size} for p in files if excluded(p.relative_to(source))]
    def ignore(directory,names):
        root=pathlib.Path(directory)
        return [name for name in names if excluded((root/name).relative_to(source))]
    shutil.copytree(source,destination,ignore=ignore)
    service=destination/'服务端'
    package_file=service/'package.json';m=json.loads(package_file.read_text(encoding='utf-8-sig'));m['version']=version
    dropped=sorted(FRONTEND.intersection(m['dependencies']))
    for key in dropped:del m['dependencies'][key]
    package_file.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lock_file=service/'package-lock.json';lock=json.loads(lock_file.read_text(encoding='utf-8-sig'));lock['version']=version;lock['packages']['']['version']=version
    for key in dropped:lock['packages']['']['dependencies'].pop(key,None)
    lock_file.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    npm=shutil.which('npm.cmd') or shutil.which('npm')
    subprocess.run([npm,'prune','--offline','--omit=dev','--ignore-scripts','--no-audit','--no-fund'],cwd=service,check=True)
    # Every inference DLL/PYD and model file must survive byte-for-byte.
    protected=[p for p in files if p.suffix.lower() in {'.dll','.pyd'} and p.relative_to(source).parts[:3]==('桌面端','resources','worker')]
    protected += [p for p in files if p.relative_to(source).parts[:3]==('桌面端','resources','bundled-model')]
    for old in protected:
        new=destination/old.relative_to(source)
        assert new.is_file() and old.stat().st_size==new.stat().st_size and sha(old)==sha(new),str(new)
    before=sum(p.stat().st_size for p in files);after=sum(p.stat().st_size for p in destination.rglob('*') if p.is_file())
    report={'version':version,'sourceVersion':json.loads((source/'服务端/package.json').read_text(encoding='utf-8-sig'))['version'],'beforeBytes':before,'afterBytes':after,'savedBytes':before-after,'removedWorkerFiles':removed,'removedFrontendDependencies':dropped,'protectedRuntimeAndModelFilesVerified':len(protected),'modelAndCudaChanged':False}
    (destination/'slim-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='removedWorkerFiles'},ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--destination',required=True);p.add_argument('--version',default='0.5.8');a=p.parse_args();package(a.source,a.destination,a.version)
