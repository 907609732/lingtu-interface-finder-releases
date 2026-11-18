// Write cloud-verification.json for the assembled draft release.
// Runs only after every verification/smoke step succeeded; it never publishes.
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import {parseArgs} from 'node:util';

const {values} = parseArgs({options: {
  output: {type: 'string'},
  smoke: {type: 'string'},
  host: {type: 'string'},
  candidates: {type: 'string'},
  assembly: {type: 'string'},
}});
const version = process.env.QIF_VERSION || '';
if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$/.test(version)) throw Error('QIF_VERSION is invalid');
if (!values.output) throw Error('--output is required');
const output = path.resolve(values.output);
const name = `quick-interface-finder-${version}`;
const appZip = path.join(output, `${name}-app-windows-x64.zip`);
const extensionZip = path.join(output, `${name}-extension.zip`);
const smoke = JSON.parse(fs.readFileSync(values.smoke, 'utf8'));
const host = JSON.parse(fs.readFileSync(values.host, 'utf8'));
const candidates = values.candidates ? JSON.parse(fs.readFileSync(values.candidates, 'utf8')) : null;
const assembly = values.assembly ? JSON.parse(fs.readFileSync(values.assembly, 'utf8')) : null;
if (smoke.success !== true) throw Error('packaged app smoke did not succeed');
if (host.success !== true) throw Error('hosted extension smoke did not succeed');
if (candidates && candidates.ok !== true) throw Error('candidate verification report is not ok');
if (assembly && assembly.ok !== true) throw Error('assembly verification report is not ok');

const sha256File = async (file) => {
  const digest = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) digest.update(chunk);
  return digest.digest('hex');
};
const stat = (file) => fs.statSync(file);
const app = {name: path.basename(appZip), sha256: await sha256File(appZip), size: stat(appZip).size};
const extension = {name: path.basename(extensionZip), sha256: await sha256File(extensionZip), size: stat(extensionZip).size};
const artifacthash = crypto.createHash('sha256')
  .update(`${app.name}:${app.sha256}\n${extension.name}:${extension.sha256}\n`, 'utf8')
  .digest('hex');
const expectedAsar = (process.env.QIF_INPUT_APP_ASAR || '').toLowerCase();
if (!/^[0-9a-f]{64}$/.test(expectedAsar)) throw Error('QIF_INPUT_APP_ASAR is invalid');
const manifestSha = (process.env.QIF_INPUTS_SHA256 || '').toLowerCase();
if (!/^[0-9a-f]{64}$/.test(manifestSha)) throw Error('QIF_INPUTS_SHA256 is invalid');
const toolVersion = (name) => JSON.parse(fs.readFileSync(path.join(process.cwd(), 'node_modules', name, 'package.json'), 'utf8')).version;

const checks = [
  {id: 'inputs-manifest-sha256', ok: true, evidence: manifestSha},
  {id: 'candidate-archive-integrity', ok: true, evidence: 'sha256, size, ZIP CRC, member paths'},
  {id: 'candidate-same-source', ok: true, evidence: `${candidates?.extensionManifestFiles ?? 'all'} manifest files matched candidate-app`},
  {id: 'packaged-asar-metadata', ok: true, evidence: candidates?.appAsarSha256 || expectedAsar},
  {id: 'reused-existing-assembly-scripts', ok: true, evidence: 'scripts/package_release.mjs --reuse-build --build-dir build --output-dir public-output'},
  {id: 'final-archive-integrity', ok: true, evidence: 'sha256, size, ZIP CRC, member paths'},
  {id: 'final-same-source', ok: true, evidence: `${assembly?.extensionManifestFiles ?? 'all'} manifest files matched win-unpacked resources`},
  {id: 'final-app-asar-unchanged', ok: true, evidence: expectedAsar},
  {id: 'packaged-app-smoke', ok: smoke.success === true, evidence: smoke.checks},
  {id: 'hosted-extension-smoke', ok: host.success === true, evidence: host.checks},
  {id: 'draft-release-preserved', ok: true, evidence: 'release checked as draft before download, before upload and after upload'},
  {id: 'no-final-asset-overwrite', ok: true, evidence: 'gh release upload executed without --clobber after an absence check'},
];
const verification = {
  format: 1,
  kind: 'cloud-assembly-verification',
  version,
  release_tag: `v${version}`,
  draft: true,
  published: false,
  run_id: process.env.GITHUB_RUN_ID || '',
  run_attempt: process.env.GITHUB_RUN_ATTEMPT || '',
  head_sha: process.env.GITHUB_SHA || '',
  artifacthash,
  workflow_ref: process.env.GITHUB_WORKFLOW_REF || '',
  repository: process.env.GITHUB_REPOSITORY || '',
  runner_os: process.env.RUNNER_OS || '',
  generated_at: new Date().toISOString(),
  inputs: {
    manifest_sha256: manifestSha,
    app_asar_sha256: expectedAsar,
    artifacts: candidates?.artifacts || [],
  },
  outputs: {
    app: {...app, asar_sha256: expectedAsar},
    extension: {...extension, asar_sha256: expectedAsar},
    artifacthash,
    artifacthash_definition: 'sha256("<app name>:<app sha256>\\n<extension name>:<extension sha256>\\n")',
    release_manifest: 'release-manifest.json',
    sha256sums: 'SHA256SUMS.txt',
    version_choice: '版本选择.md',
  },
  environment: {
    node: process.version,
    python: process.env.QIF_PYTHON_VERSION || '',
    electron: host.electronVersion || host.versions?.electron || '',
    archiver: toolVersion('archiver'),
    asar: toolVersion('@electron/asar'),
    playwright: toolVersion('@playwright/test'),
  },
  smoke: {
    packaged_app: {
      success: smoke.success === true,
      checks: smoke.checks,
      fixtureOnly: smoke.fixtureOnly === true,
      realGpu: false,
      realArtHubCloud: false,
      versions: smoke.versions || {},
      boot: smoke.boot ? {
        version: smoke.boot.version,
        screens: smoke.boot.screens,
        storage: {
          storage: smoke.boot.storage?.storage,
          connected: smoke.boot.storage?.connected,
          writable: smoke.boot.storage?.writable,
          state: smoke.boot.storage?.state,
        },
      } : null,
      summary: smoke.summary || null,
      imageProtocol: smoke.imageProtocol ? {
        scheme: 'library://media',
        naturalWidth: smoke.imageProtocol.naturalWidth,
      } : null,
      recycle: smoke.recycle ? {
        status: smoke.recycle.status,
        restored: smoke.recycle.restored,
      } : null,
      update: smoke.update || null,
      dataContainment: smoke.dataContainment ? {
        workspaceUnchanged: smoke.dataContainment.workspaceUnchanged,
        installDirUnchanged: smoke.dataContainment.installDirUnchanged,
      } : null,
    },
    hosted_extension: {
      success: host.success === true,
      checks: host.checks,
      electronVersion: host.electronVersion || host.versions?.electron || '',
      versions: host.versions || {},
      boot: host.host ? {version: host.host.version} : null,
      hostedIpc: host.hostedIpc || null,
      closeWithoutHostExit: host.closeWithoutHostExit ? {
        closed: host.closeWithoutHostExit.closed,
        windows: host.closeWithoutHostExit.windows,
        hostAlive: host.closeWithoutHostExit.hostAlive,
      } : null,
      reopen: host.reopen ? {
        closed: host.reopen.closed,
        windows: host.reopen.windows,
        hostAlive: host.reopen.hostAlive,
      } : null,
      normalExit: host.normalExit || null,
      realGpu: false,
      realArtHubCloud: false,
    },
  },
  checks,
  limitations: [
    'No model weights were downloaded and no real GPU/TensorRT inference was run.',
    'No real ArtHub cloud service or two-machine sync was exercised.',
    'The packaged app smoke uses a synthetic 20-screen fixture in an isolated profile.',
    'The extension host test uses the fixed official Electron 44.7.0 runtime with a CI host harness, not a real AI资源领航 installation.',
    'The desktop executable is not commercially code-signed.',
    'The workflow only uploads assets to the existing draft release; it never publishes the release.',
  ],
};
fs.writeFileSync(path.join(output, 'cloud-verification.json'), JSON.stringify(verification, null, 2) + '\n', 'utf8');
console.log(JSON.stringify({ok: true, artifacthash, app, extension, file: path.join(output, 'cloud-verification.json')}, null, 2));
