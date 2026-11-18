// Pin the CI-only tool manifest to the dispatched release version.
// The manifest intentionally contains no application source or dependencies.
import fs from 'node:fs';
import path from 'node:path';

const version = process.argv[2] || '';
if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version)) {
  throw Error('usage: node scripts/set_ci_version.mjs <x.y.z>');
}
const root = path.resolve(import.meta.dirname, '..');
const file = path.join(root, 'package.json');
const pkg = JSON.parse(fs.readFileSync(file, 'utf8'));
if (pkg.name !== 'quick-interface-finder') throw Error('CI package.json name must be quick-interface-finder');
if (pkg.private !== true) throw Error('CI package.json must stay private');
const expected = {'archiver': '8.0.0', '@electron/asar': '3.4.1', '@playwright/test': '1.64.1'};
for (const [name, wanted] of Object.entries(expected)) {
  if (pkg.devDependencies?.[name] !== wanted) throw Error(`CI package.json must pin ${name}@${wanted}`);
}
if (pkg.dependencies && Object.keys(pkg.dependencies).length) {
  throw Error('CI package.json must not install the application dependencies');
}
const updated = {...pkg, version};
fs.writeFileSync(file, JSON.stringify(updated, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({name: updated.name, version: updated.version, devDependencies: updated.devDependencies}, null, 2));
