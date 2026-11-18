// One electron-builder build feeds both editions. Archiver writes the archives;
// Python's standard zipfile validates CRCs. No user data, model or host build runs here.
import fs from 'node:fs/promises';
import fss from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn,execFile} from 'node:child_process';
import {parseArgs,promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';
import {ZipArchive} from 'archiver';

const root=path.resolve(import.meta.dirname,'..'),require=createRequire(import.meta.url),runFile=promisify(execFile);
const absent=async file=>!(await fs.lstat(file).catch(e=>{if(e.code==='ENOENT')return null;throw e;}));
export async function publishFileWithoutOverwrite(source,target){
 // link is an atomic no-replace operation on NTFS. Filesystems without hard links
 // still get COPYFILE_EXCL protection; never fall back to replacing rename.
 try{await fs.link(source,target);}catch(error){
  if(!['EXDEV','ENOSYS','ENOTSUP','EPERM'].includes(error.code))throw error;
  await fs.copyFile(source,target,fss.constants.COPYFILE_EXCL);
 }
 await fs.unlink(source);
}
async function sha(file){const hash=crypto.createHash('sha256');for await(const bytes of fss.createReadStream(file))hash.update(bytes);return hash.digest('hex');}
async function filesUnder(directory){
 const files=[];
 for(const item of await fs.readdir(directory,{withFileTypes:true})){
  const file=path.join(directory,item.name);
  if(item.isSymbolicLink())throw Error('发行目录不允许链接：'+file);
  if(item.isDirectory())files.push(...await filesUnder(file));else if(item.isFile())files.push(file);else throw Error('不支持的发行文件：'+file);
 }
 return files;
}
async function zipDirectory(directory,zip,prefix){
 const archive=new ZipArchive({zlib:{level:6}}),stream=fss.createWriteStream(zip,{flags:'wx'});
 const done=new Promise((resolve,reject)=>{stream.on('close',resolve);stream.on('error',reject);archive.on('error',reject);archive.on('warning',reject);});
 archive.pipe(stream);archive.directory(directory,prefix);await archive.finalize();await done;
}
async function verifyZip(file,python){
 await runFile(python,['-c','import sys,zipfile\nwith zipfile.ZipFile(sys.argv[1]) as z:\n bad=z.testzip()\n if bad: raise RuntimeError("ZIP CRC failed: "+bad)\n',file],{windowsHide:true,timeout:300000});
}
async function runExtension(args){
 await new Promise((resolve,reject)=>{const child=spawn(process.execPath,[path.join(root,'scripts/package_extension.mjs'),...args],{cwd:root,stdio:'inherit',windowsHide:true});child.on('error',reject);child.on('exit',code=>code===0?resolve():reject(Error('扩展构建失败：'+code)));});
}

export async function packageRelease({outputDir,buildDir,reuseBuild=false,python='python'}={}){
 const pkg=JSON.parse(await fs.readFile(path.join(root,'package.json'),'utf8')),version=pkg.version;
 if(!/^\d+\.\d+\.\d+$/.test(version))throw Error('版本号必须为 x.y.z');
 const name=`quick-interface-finder-${version}`,output=path.resolve(root,outputDir||path.join('release',version));
 const appZip=`${name}-app-windows-x64.zip`,extensionZip=`${name}-extension.zip`;
 const names=[name,appZip,extensionZip,'app-delivery.json','extension-delivery.json','SHA256SUMS.txt','release-manifest.json','版本选择.md'];
 for(const file of names)if(!await absent(path.join(output,file)))throw Error('现有交付包保留，请更新版本号或指定空输出目录：'+path.join(output,file));
 // Check the existing system dependency before paying for an Electron build.
 await runFile(python,['-c','import sys,zipfile; assert sys.version_info >= (3,8)'],{windowsHide:true});
 await fs.mkdir(output,{recursive:true});
 const lock=path.join(output,'.release-packaging.lock'),handle=await fs.open(lock,'wx');
 let work;
 try{
  await handle.writeFile(JSON.stringify({pid:process.pid,version}));
  work=await fs.mkdtemp(path.join(output,'.packaging-'));
  const build=path.resolve(root,buildDir||path.join('.local',`release-build-${version}-${crypto.randomUUID().slice(0,8)}`));
  const args=['--output-dir',work,'--build-dir',build];if(reuseBuild)args.push('--reuse-build');
  await runExtension(args); // The only electron-builder invocation; no second app build.
  const app=path.join(build,'win-unpacked'),resources=path.join(app,'resources');
  await fs.access(path.join(app,'快速找界面.exe'));
  const asar=require('@electron/asar'),metadata=JSON.parse(asar.extractFile(path.join(resources,'app.asar'),'package.json').toString());
  if(metadata.name!==pkg.name||metadata.version!==version)throw Error('构建产物版本与源码不一致，请重新构建');
  const extension=JSON.parse(await fs.readFile(path.join(work,'extension-delivery.json'),'utf8'));
  const manifest=JSON.parse(await fs.readFile(path.join(work,name,'extension.json'),'utf8'));
  for(const file of manifest.files){
   const source=path.join(app,...file.path.split('/'));
   if((await fs.stat(source)).size!==file.size||await sha(source)!==file.sha256)throw Error('两个版本的公共文件不一致：'+file.path);
  }
  const appFiles=await filesUnder(app);
  for(const file of appFiles){
   const relative=path.relative(app,file).split(path.sep).join('/');
   if(/(^|\/)(bundled-model|server-data|user-data|profile|cache)(\/|$)|^(?:resources\/)?models\/|\.(trt|safetensors)$/i.test(relative))throw Error('独立包混入模型或用户数据：'+relative);
  }
  const appAsarSha256=await sha(path.join(resources,'app.asar'));
  await zipDirectory(app,path.join(work,appZip),`${name}-app`);
  await verifyZip(path.join(work,extensionZip),python);await verifyZip(path.join(work,appZip),python);
  const standalone={id:pkg.name,version,edition:'standalone-full',zip:appZip,zipBytes:(await fs.stat(path.join(work,appZip))).size,sha256:await sha(path.join(work,appZip)),unpackedBytes:(await Promise.all(appFiles.map(file=>fs.stat(file)))).reduce((n,s)=>n+s.size,0),appAsarSha256,bundledElectron:true,bundledModels:false,crcVerified:true,entry:`${name}-app/快速找界面.exe`};
  const release={format:1,kind:'dual-edition-release',version,models:'separate-download-or-import',sharedResourcesVerified:true,appAsarSha256,notAutoUpdateManifest:true,artifacts:[{edition:'extension',...extension,appAsarSha256,crcVerified:true},standalone]};
  await fs.writeFile(path.join(work,'app-delivery.json'),JSON.stringify(standalone,null,2),{flag:'wx'});
  await fs.writeFile(path.join(work,'SHA256SUMS.txt'),release.artifacts.map(item=>`${item.sha256}  ${item.zip}`).join('\n')+'\n');
  await fs.writeFile(path.join(work,'版本选择.md'),`# 快速找界面 ${version}\n\n| 版本 | 适合谁 | 使用方式 |\n|---|---|---|\n| AI资源领航扩展版 | 已使用支持 hostApi 1 的 AI资源领航 | 导入 ${extensionZip} |\n| 独立 APP 完整版 | 希望单独使用快速找界面 | 解压 ${appZip} 后双击“快速找界面.exe” |\n\n两版功能和项目格式一致，模型均需单独下载或导入；完整 APP 包包含 Electron、推理环境和媒体工具。更换版本时打开同一项目目录即可，本机查询缓存各自维护。\n\n完整 APP ZIP、扩展 ZIP 均不是内置更新器的更新包，不要将其直接填入旧 update.json。\n`);
  await fs.writeFile(path.join(work,'release-manifest.json'),JSON.stringify(release,null,2),{flag:'wx'});
  // All archives are verified before publication; the release catalogue is written last.
  for(const file of names.filter(file=>file!=='release-manifest.json')){
   if(!await absent(path.join(output,file)))throw Error('输出位置已被占用，停止发布：'+file);
   if(file===name)await fs.rename(path.join(work,file),path.join(output,file));
   else await publishFileWithoutOverwrite(path.join(work,file),path.join(output,file));
  }
  await publishFileWithoutOverwrite(path.join(work,'release-manifest.json'),path.join(output,'release-manifest.json'));
  await fs.rmdir(work);
  return release;
 }catch(error){if(work)error.message+='；中间产物保留于 '+work;throw error;}
 finally{await handle.close();await fs.unlink(lock);}
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const {values}=parseArgs({options:{'reuse-build':{type:'boolean'},'output-dir':{type:'string'},'build-dir':{type:'string'},python:{type:'string'},help:{type:'boolean'}}});
 if(values.help)console.log('npm.cmd run release:package -- [--output-dir <空输出目录>] [--build-dir <构建目录>] [--reuse-build] [--python <系统Python>]\n一次构建生成扩展 ZIP 和独立 APP 完整 ZIP；不内置模型、不发布、不覆盖旧包。');
 else console.log(JSON.stringify(await packageRelease({outputDir:values['output-dir'],buildDir:values['build-dir'],reuseBuild:values['reuse-build'],python:values.python}),null,2));
}
