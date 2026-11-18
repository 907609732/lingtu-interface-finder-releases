// Assert the packaged app.asar metadata and required entry points.
// Uses the pinned @electron/asar from the CI-only tool manifest; no app source is read.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
import {parseArgs} from 'node:util';

const require = createRequire(import.meta.url);
const {values} = parseArgs({options: {
  'asar': {type: 'string'},
  'expect-name': {type: 'string'},
  'expect-version': {type: 'string'},
  'expect-sha256': {type: 'string'},
}});
if (!values.asar) throw Error('usage: node scripts/check_asar.mjs --asar <app.asar> --expect-name <name> --expect-version <x.y.z> [--expect-sha256 <hex>]');
const asar = require('@electron/asar');
const file = values.asar;
if (!fs.existsSync(file)) throw Error('app.asar missing: ' + file);
const metadata = JSON.parse(asar.extractFile(file, 'package.json').toString('utf8'));
if (metadata.name !== values['expect-name']) throw Error(`app.asar name ${JSON.stringify(metadata.name)} != ${JSON.stringify(values['expect-name'])}`);
if (metadata.version !== values['expect-version']) throw Error(`app.asar version ${metadata.version} != ${values['expect-version']}`);
if (metadata.main !== 'desktop/main.cjs') throw Error('app.asar main must be desktop/main.cjs');
const files = asar.listPackage(file).map((entry) => entry.replaceAll('\\', '/').replace(/^\/+/, ''));
for (const required of ['desktop/main.cjs', 'desktop/preload.cjs', 'dist/index.html', 'desktop/library.cjs', 'desktop/catalog.cjs']) {
  if (!files.includes(required)) throw Error('app.asar missing required entry: ' + required);
}
let sha256 = '';
if (values['expect-sha256']) {
  const digest = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) digest.update(chunk);
  sha256 = digest.digest('hex');
  if (sha256 !== values['expect-sha256'].toLowerCase()) throw Error(`app.asar sha256 ${sha256} != ${values['expect-sha256']}`);
}
console.log(JSON.stringify({ok: true, name: metadata.name, version: metadata.version, main: metadata.main, files: files.length, sha256}, null, 2));
