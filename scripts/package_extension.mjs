// Reuse electron-builder's production dependency collection and ASAR tooling.
// Only resources enter the extension; no second Electron/Chromium is distributed.
import fs from 'node:fs/promises';
import fss from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {ZipArchive} from 'archiver';
import {parseArgs} from 'node:util';
const root=path.resolve(import.meta.dirname,'..');
const {values}=parseArgs({options:{'reuse-build':{type:'boolean'},'output-dir':{type:'string'},'build-dir':{type:'string'},help:{type:'boolean'}}});
if(values.help){console.log('node scripts/package_extension.mjs [--reuse-build] [--output-dir <目录>] [--build-dir <构建目录>]');process.exit(0);}
const pkg=JSON.parse(await fs.readFile(path.join(root,'package.json'),'utf8'));
const version=pkg.version;
if(!/^\d+\.\d+\.\d+$/.test(version))throw Error('Invalid extension version');
const output=path.resolve(root,values['output-dir']||path.join('release',version)),name=`quick-interface-finder-${version}`;
const staging=path.join(output,name),build=path.resolve(root,values['build-dir']||path.join('.local',`extension-build-${version}`));
const zip=path.join(output,`${name}-extension.zip`);
for(const file of [staging,zip,path.join(output,'extension-delivery.json'),path.join(output,'SHA256SUMS.txt')]){
 if(await fs.lstat(file).catch(e=>{if(e.code==='ENOENT')return null;throw e;}))throw Error('Existing delivery preserved: '+file);
}
async function run(args){await new Promise((resolve,reject)=>{const child=spawn(process.execPath,args,{cwd:root,stdio:'inherit',windowsHide:true});child.on('error',reject);child.on('exit',code=>code===0?resolve():reject(Error(`Build failed: ${code}`)));});}
if(!values['reuse-build']){
 await run(['node_modules/typescript/bin/tsc','--noEmit']);
 await run(['node_modules/vite/bin/vite.js','build']);
 await run(['node_modules/electron-builder/out/cli/cli.js','--win','dir',`--config.directories.output=${build}`]);
}
// A custom unpacked Electron distribution still carries Electron's stock default app.
// It is not part of either edition and must not enter the shared resources payload.
await fs.rm(path.join(build,'win-unpacked','resources','default_app.asar'),{force:true});
await fs.mkdir(output,{recursive:true});
await fs.mkdir(staging);
await fs.cp(path.join(build,'win-unpacked','resources'),path.join(staging,'resources'),{recursive:true});
async function walk(dir){let files=[];for(const item of await fs.readdir(dir,{withFileTypes:true})){const file=path.join(dir,item.name);if(item.isSymbolicLink())throw Error('Link in extension payload');if(item.isDirectory())files.push(...await walk(file));else if(item.isFile())files.push(file);}return files;}
const files=[];
for(const file of (await walk(staging)).sort()){
 const relative=path.relative(staging,file).replaceAll(path.sep,'/');
 if(/(^|\/)(locales|bundled-model)(\/|$)|(^|\/)(快速找界面|electron)\.exe$|\.(trt|safetensors)$/i.test(relative))throw Error('Unexpected desktop/model payload: '+relative);
 const hash=crypto.createHash('sha256');for await(const chunk of fss.createReadStream(file))hash.update(chunk);
 files.push({path:relative,size:(await fs.stat(file)).size,sha256:hash.digest('hex')});
}
const manifest={format:1,id:'quick-interface-finder',name:'快速找界面',version,hostApi:1,entry:'resources/app.asar/desktop/main.cjs',platform:'win32',arch:'x64',files};
await fs.writeFile(path.join(staging,'extension.json'),JSON.stringify(manifest,null,2),{flag:'wx'});
const archive=new ZipArchive({zlib:{level:6}}),stream=fss.createWriteStream(zip,{flags:'wx'});
const done=new Promise((resolve,reject)=>{stream.on('close',resolve);stream.on('error',reject);archive.on('error',reject);});
archive.pipe(stream);archive.directory(staging,name);await archive.finalize();await done;
const hash=crypto.createHash('sha256');for await(const chunk of fss.createReadStream(zip))hash.update(chunk);
const report={id:manifest.id,version,format:1,zip:path.basename(zip),zipBytes:(await fs.stat(zip)).size,sha256:hash.digest('hex'),files:files.length,unpackedBytes:files.reduce((n,f)=>n+f.size,0)+(await fs.stat(path.join(staging,'extension.json'))).size,noBundledElectron:true,noBundledModels:true};
await fs.writeFile(path.join(output,'extension-delivery.json'),JSON.stringify(report,null,2),{flag:'wx'});await fs.writeFile(path.join(output,'SHA256SUMS.txt'),`${report.sha256}  ${report.zip}\n`,{flag:'wx'});console.log(JSON.stringify(report,null,2));
