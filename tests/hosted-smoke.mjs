// Cloud acceptance for the packaged extension loaded by a fixed official Electron host.
//
// The host harness requires the extension's own app.asar/desktop/main.cjs factory with
// hosted:true and a separate profile/cache. Checks cover load, version, hosted IPC, UI,
// close-without-host-exit, reopen and a normal host quit. No real GPU or ArtHub cloud.
import {_electron as electron, expect} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';

const electronExe = process.env.QIF_HOST_ELECTRON;
const extensionResources = process.env.QIF_EXT_RESOURCES;
const expectedVersion = process.env.QIF_SMOKE_VERSION;
const expectedAsar = (process.env.QIF_INPUT_APP_ASAR || '').toLowerCase();
const staging = process.env.QIF_HOST_STAGING || path.join(os.tmpdir(), 'qif-host-smoke');
const reportDir = process.env.QIF_HOST_REPORT_DIR || path.join(staging, 'report');
const harness = path.join(path.dirname(fileURLToPath(import.meta.url)), 'host-harness.cjs');
if (!electronExe) throw Error('QIF_HOST_ELECTRON is required');
if (!extensionResources) throw Error('QIF_EXT_RESOURCES is required');
if (!/^\d+\.\d+\.\d+$/.test(expectedVersion || '')) throw Error('QIF_SMOKE_VERSION is required');
if (!/^[0-9a-f]{64}$/.test(expectedAsar)) throw Error('QIF_INPUT_APP_ASAR is required');
await fs.access(electronExe);
await fs.access(path.join(extensionResources, 'app.asar'));
await fs.access(harness);
const profile = path.join(staging, 'host-profile');
const cache = path.join(staging, 'host-cache');
const screenshots = path.join(reportDir, 'screenshots');
for (const directory of [profile, cache]) {
  assert.equal(await fs.stat(directory).catch(() => null), null, `host staging must be fresh: ${directory}`);
}
await fs.mkdir(screenshots, {recursive: true});
const report = {
  success: false,
  checks: [],
  pageErrors: [],
  errors: [],
  hosted: true,
  realGpu: false,
  realArtHubCloud: false,
  officialElectron: true,
  electronExe,
  extensionResources,
  harness,
  staging,
};
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function cleanEnv(extra = {}) {
  const env = {...process.env};
  for (const name of ['ELECTRON_RUN_AS_NODE', 'QUICK_UI_DEV_URL', 'QUICK_UI_MODEL_PATH',
    'QUICK_UI_PYTHON', 'QUICK_UI_LIBRARY_PATH', 'QUICK_UI_USER_DATA', 'NODE_OPTIONS']) delete env[name];
  return Object.assign(env, extra);
}

async function closeOnboarding(target) {
  const dialog = target.getByRole('dialog');
  if (!(await dialog.count())) return false;
  const close = dialog.first().getByTitle('关闭');
  if (await close.count()) {
    await close.click().catch(() => {});
    await delay(250);
  }
  return true;
}

let app = null;
try {
  app = await electron.launch({
    executablePath: electronExe,
    args: [harness],
    cwd: path.dirname(harness),
    env: cleanEnv({
      QIF_EXT_RESOURCES: extensionResources,
      QIF_HOST_PROFILE: profile,
      QIF_HOST_CACHE: cache,
      QIF_HOST_STAGING: staging,
      ELECTRON_ENABLE_LOGGING: '0',
    }),
    timeout: 180000,
  });
  const page = await app.firstWindow();
  page.on('pageerror', (error) => report.pageErrors.push(error.message));
  await page.waitForFunction(() => !!window.quickUI, null, {timeout: 120000});
  await page.locator('.seek-shell').waitFor({timeout: 120000});
  await closeOnboarding(page);
  const electronVersion = await app.evaluate(() => process.versions.electron);
  assert.equal(electronVersion, '44.7.0');
  const hostState = await app.evaluate(() => globalThis.__qifHostState());
  assert.equal(hostState.asarSha256, expectedAsar, 'extension app.asar hash');
  assert.equal(hostState.versions.node, await app.evaluate(() => process.versions.node));
  const windowURL = page.url();
  assert.match(windowURL, /^file:/);
  assert.ok(windowURL.includes('app.asar'), windowURL);
  const boot = await page.evaluate(() => window.quickUI.boot());
  assert.equal(boot.settings.hosted, true);
  assert.equal(boot.settings.version, expectedVersion);
  assert.ok(path.resolve(boot.library.root).toLowerCase().startsWith(path.resolve(profile).toLowerCase() + path.sep));
  assert.equal(boot.library.records.length, 0, 'hosted fixture library should be empty');
  assert.equal(boot.library.ai.ready, false);
  const catalog = await page.evaluate(() => window.quickUI.catalogList());
  assert.deepEqual(catalog.records, []);
  const updater = await page.evaluate(() => window.quickUI.updater({action: 'status'}));
  assert.equal(updater.hosted, true);
  assert.equal(updater.installable, false);
  assert.equal(updater.phase, 'host-managed');
  assert.equal(updater.current, expectedVersion);
  await expect(page.locator('.seek-shell')).toBeVisible();
  await page.screenshot({path: path.join(screenshots, 'hosted-extension.png'), animations: 'disabled'});
  report.versions = {electron: electronVersion, node: hostState.versions.node, chrome: hostState.versions.chrome};
  report.electronVersion = electronVersion;
  report.host = {windowURL, libraryRoot: boot.library.root, version: boot.settings.version};
  report.hostedIpc = {bootVersion: boot.settings.version, catalogRecords: catalog.records.length, updater};
  report.checks.push('packaged extension loads from app.asar in the official Electron host');
  report.checks.push('hosted version, hosted IPC and UI are reachable');

  // Closing the extension window disposes it but must not quit the host process.
  await app.evaluate(({BrowserWindow}) => BrowserWindow.getAllWindows()[0].close());
  await expect.poll(() => app.evaluate(() => globalThis.__qifHostState().closed), {timeout: 60000}).toBe(1);
  const afterClose = await app.evaluate(() => globalThis.__qifHostState());
  assert.equal(afterClose.windows, 0);
  assert.equal(afterClose.ready, true);
  assert.equal(afterClose.pid, hostState.pid);
  assert.equal(await app.evaluate(() => process.pid), hostState.pid);
  report.closeWithoutHostExit = {closed: afterClose.closed, windows: afterClose.windows, hostAlive: true, pid: afterClose.pid};
  report.checks.push('closing the hosted window does not exit the host');

  // The host can open the extension again with the same profile.
  const windowEvent = app.waitForEvent('window', {timeout: 120000});
  await app.evaluate(async () => {
    globalThis.__qifRuntime2 = globalThis.__qifHostCreate();
    await globalThis.__qifRuntime2.start();
    return true;
  });
  const second = await windowEvent;
  second.on('pageerror', (error) => report.pageErrors.push(error.message));
  await second.waitForFunction(() => !!window.quickUI, null, {timeout: 120000});
  await second.locator('.seek-shell').waitFor({timeout: 120000});
  await closeOnboarding(second);
  const secondBoot = await second.evaluate(() => window.quickUI.boot());
  assert.equal(secondBoot.settings.hosted, true);
  assert.equal(secondBoot.settings.version, expectedVersion);
  assert.equal((await app.evaluate(() => globalThis.__qifHostState().windows)), 1);
  await app.evaluate(({BrowserWindow}) => BrowserWindow.getAllWindows()[0].close());
  await expect.poll(() => app.evaluate(() => globalThis.__qifHostState().closed), {timeout: 60000}).toBe(2);
  const afterSecondClose = await app.evaluate(() => globalThis.__qifHostState());
  assert.equal(afterSecondClose.windows, 0);
  assert.equal(afterSecondClose.ready, true);
  report.reopen = {closed: afterSecondClose.closed, windows: afterSecondClose.windows, hostAlive: true, version: secondBoot.settings.version};
  report.checks.push('host can reopen the extension after closing it');
  assert.deepEqual(report.pageErrors, [], 'renderer page errors');

  // Normal host quit returns exit code 0.
  const child = app.process();
  const exited = new Promise((resolve) => {
    child.once('exit', (code, signal) => resolve({code, signal}));
  });
  await app.evaluate(({app: electronApp}) => electronApp.quit()).catch(() => {});
  const exit = await Promise.race([exited, delay(30000).then(() => ({timeout: true}))]);
  assert.equal(exit.timeout, undefined, 'host did not exit after quit');
  assert.equal(exit.code, 0, JSON.stringify(exit));
  report.normalExit = exit;
  report.checks.push('host quits normally with exit code 0');
  app = null;
  report.success = true;
  report.screenshots = (await fs.readdir(screenshots)).map((entry) => path.join(screenshots, entry));
  await fs.writeFile(path.join(reportDir, 'hosted-smoke.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.success = false;
  report.error = error.stack || String(error);
  if (app) {
    await app.close().catch(() => {});
    app = null;
  }
  await fs.writeFile(path.join(reportDir, 'hosted-smoke.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.error(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  if (app) await app.close().catch(() => {});
}
