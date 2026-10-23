// Stop only a service whose script belongs to this installation. Never kill other Node processes.
const fs=require('node:fs/promises'),path=require('node:path');
(async()=>{
  const root=path.resolve(process.argv[2]);
  const expected=path.join(root,'团队便携版','服务端','server','start.cjs');
  const profile=process.env.QUICK_UI_USER_DATA||path.join(process.env.APPDATA,'QuickInterfaceFinder');
  const settings=JSON.parse(await fs.readFile(path.join(profile,'settings.json'),'utf8').catch(()=>'{}'));
  const candidates=[settings.serviceDataPath,path.join(root,'团队便携版','服务端','server-data')].filter(Boolean);
  for(const data of new Set(candidates)){
    const file=path.join(data,'server.lock');
    const lock=JSON.parse(await fs.readFile(file,'utf8').catch(()=>'null'));
    if(!lock||path.resolve(lock.script).toLowerCase()!==expected.toLowerCase())continue;
    try{process.kill(lock.pid,0);}catch(e){if(e.code==='ESRCH')continue;throw e;}
    await fs.writeFile(path.join(data,'stop.request'),String(lock.pid));
    let exited=false;
    for(let i=0;i<120;i++){
      try{process.kill(lock.pid,0);}catch(e){if(e.code==='ESRCH'){exited=true;break;}throw e;}
      await new Promise(r=>setTimeout(r,250));
    }
    if(!exited)throw Error('Service is still running');
  }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
