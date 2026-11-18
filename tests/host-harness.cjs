// CI-only host harness for the packaged extension ASAR.
//
// It is a miniature stand-in for AI资源领航: it loads resources/app.asar/desktop/main.cjs
// as a factory with hosted:true, gives the extension its own profile/cache and keeps
// the host process alive when the extension window closes. It does not emulate a real
// host application, GPU acceleration or the ArtHub service.
const path = require('node:path');
const crypto = require('node:crypto');
const physicalFs = require('original-fs');
const {app, protocol, BrowserWindow} = require('electron');

const resources = process.env.QIF_EXT_RESOURCES;
const profile = process.env.QIF_HOST_PROFILE;
const cache = process.env.QIF_HOST_CACHE;
if (!resources || !profile || !cache) throw Error('QIF_EXT_RESOURCES, QIF_HOST_PROFILE and QIF_HOST_CACHE are required');
const asar = path.join(resources, 'app.asar');
const {createFinderRuntime, registerFinderScheme} = require(path.join(asar, 'desktop', 'main.cjs'));

app.setPath('userData', profile);
app.disableHardwareAcceleration();
registerFinderScheme(protocol);

// A real host owns the application lifetime; the extension window must never quit it.
app.on('window-all-closed', () => {});

let closed = 0;
let asarSha256 = '';
globalThis.__qifHostClosed = 0;

function createRuntime() {
  return createFinderRuntime({
    hosted: true,
    root: asar,
    resourcesRoot: resources,
    profileRoot: profile,
    cacheRoot: cache,
    onClosed: () => {
      closed += 1;
      globalThis.__qifHostClosed = closed;
    },
  });
}

globalThis.__qifHostCreate = createRuntime;
globalThis.__qifHostState = () => ({
  closed,
  ready: app.isReady(),
  pid: process.pid,
  windows: BrowserWindow.getAllWindows().length,
  asar,
  asarSha256,
  versions: {
    electron: process.versions.electron,
    node: process.versions.node,
    chrome: process.versions.chrome,
  },
});

app.whenReady().then(async () => {
  asarSha256 = await new Promise((resolve, reject) => {
    const digest = crypto.createHash('sha256');
    const stream = physicalFs.createReadStream(asar);
    stream.on('data', (chunk) => digest.update(chunk));
    stream.on('error', reject);
    stream.on('end', () => resolve(digest.digest('hex')));
  });
  globalThis.__qifRuntime = createRuntime();
  await globalThis.__qifRuntime.start();
}).catch((error) => {
  console.error('HOST_HARNESS_FAILED', (error && error.stack) || error);
  app.exit(2);
});
