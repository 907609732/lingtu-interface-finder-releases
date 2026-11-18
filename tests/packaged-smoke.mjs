// Cloud acceptance for the real assembled standalone APP.
//
// The synthetic 20-screen library is created through the packaged ASAR's own
// Library/Catalog modules inside the Electron main process; a plain Node process
// cannot require an ASAR. Then the packaged EXE is launched with that fixture and
// an isolated profile. Only fixture/profile are written. No models are used.
import {_electron as electron, expect} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const exe = process.env.QIF_SMOKE_EXE;
const expectedVersion = process.env.QIF_SMOKE_VERSION;
const staging = process.env.QIF_SMOKE_STAGING || path.join(os.tmpdir(), 'qif-cloud-smoke');
const reportDir = process.env.QIF_SMOKE_REPORT_DIR || path.join(staging, 'report');
if (!exe) throw Error('QIF_SMOKE_EXE is required');
if (!/^\d+\.\d+\.\d+$/.test(expectedVersion || '')) throw Error('QIF_SMOKE_VERSION is required');
await fs.access(exe);
await fs.mkdir(reportDir, {recursive: true});
const fixture = path.join(staging, 'fixture');
const profile = path.join(staging, 'profile');
const fixtureProfile = path.join(staging, 'fixture-profile');
const screenshots = path.join(reportDir, 'screenshots');
await fs.mkdir(screenshots, {recursive: true});
for (const directory of [fixture, profile, fixtureProfile]) {
  assert.equal(await fs.stat(directory).catch(() => null), null, `smoke staging must be fresh: ${directory}`);
}
const workspace = process.cwd();
const installRoot = path.dirname(exe);
const report = {
  success: false,
  checks: [],
  errors: [],
  pageErrors: [],
  fixtureOnly: true,
  realGpu: false,
  realArtHubCloud: false,
  packagedArtifact: true,
  exe,
  workspace,
  installRoot,
  staging,
  versions: {},
};
const pngBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAAAwCAIAAAAuKetIAAAACXBIWXMAAAPoAAAD6AG1e1JrAAAAfUlEQVRoge2SAQkAURSD1stw18SsF2M8/sAAOhY+T5O6AQuwviK7kHdJ3YAFWF+RXci7pG7AAqyvyC7kXVI3YAHWV2QX8i6pG7AA6yuyC3mX1A1YgPUV2YW8S+oGLMD6iuxC3iV1AxZgfUV2Ie+SugELsL4iu5B3Sd2AxwN+mVEg8baXlsoAAAAASUVORK5CYII=';
const screens = Array.from({length: 20}, (_, index) => {
  const number = String(index + 1).padStart(2, '0');
  return {
    id: 'screen_' + number,
    name: '界面 ' + number,
    engines: ['Engine_' + number, 'Engine_' + number + '_CND'],
    uiFigma: 'https://www.figma.com/design/ui-' + number,
    stitchFigma: 'https://www.figma.com/design/stitch-' + number,
    images: [],
    coverId: '',
    gm: [{id: 'gm_' + number, name: 'GM ' + number, description: '界面动作说明 ' + number, command: 'open screen ' + number}],
  };
});
const system = {
  id: 'system-ui', name: '二十界面系统', aliases: [], category: '', tags: [], description: '云端合成验收 fixture',
  deleted: false,
  gm: [{id: 'system_gm', name: '系统 GM', description: '系统级指令', command: 'open system'}],
  screens,
};
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function cleanEnv(extra = {}) {
  const env = {...process.env};
  for (const name of ['ELECTRON_RUN_AS_NODE', 'QUICK_UI_DEV_URL', 'QUICK_UI_MODEL_PATH',
    'QUICK_UI_PYTHON', 'NODE_OPTIONS', 'QUICK_UI_LIBRARY_PATH']) delete env[name];
  return Object.assign(env, extra);
}

async function treeSnapshot(root, skip = []) {
  const rows = [];
  async function walk(directory) {
    for (const entry of await fs.readdir(directory, {withFileTypes: true})) {
      const full = path.join(directory, entry.name);
      if (skip.some((prefix) => full === prefix || full.startsWith(prefix + path.sep))) continue;
      if (entry.isSymbolicLink()) {
        rows.push([path.relative(root, full).split(path.sep).join('/'), 'link']);
        continue;
      }
      if (entry.isDirectory()) {
        await walk(full);
        continue;
      }
      if (!entry.isFile()) continue;
      const stat = await fs.stat(full);
      rows.push([path.relative(root, full).split(path.sep).join('/'), stat.size, Math.round(stat.mtimeMs)]);
    }
  }
  await walk(root);
  return rows.sort((a, b) => String(a[0]).localeCompare(String(b[0])));
}

async function closeApp(target) {
  await target.evaluate(({app: electronApp}) => electronApp.exit(0)).catch(() => {});
  await target.close().catch(() => {});
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
let page = null;
try {
  const workspaceSkip = ['node_modules', '.git', 'public-output', 'build', 'smoke', staging]
    .map((name) => path.resolve(workspace, name));
  const workspaceBefore = await treeSnapshot(workspace, workspaceSkip);
  const installBefore = await treeSnapshot(installRoot);

  // 1. Build the fixture from the packaged ASAR's own modules in the main process.
  app = await electron.launch({
    executablePath: exe,
    args: [],
    cwd: installRoot,
    env: cleanEnv({QUICK_UI_USER_DATA: fixtureProfile, ELECTRON_ENABLE_LOGGING: '0'}),
    timeout: 180000,
  });
  page = await app.firstWindow();
  page.on('pageerror', (error) => report.errors.push('fixture: ' + error.message));
  await page.waitForFunction(() => !!window.quickUI, null, {timeout: 60000});
  report.versions.electron = await app.evaluate(() => process.versions.electron);
  report.versions.node = await app.evaluate(() => process.versions.node);
  const created = await app.evaluate(async (_electron, args) => {
    const fsp = process.getBuiltinModule('fs/promises');
    const pathMod = process.getBuiltinModule('path');
    const {createRequire} = process.getBuiltinModule('module');
    const asar = _electron.app.getAppPath();
    const requireFromAsar = createRequire(pathMod.join(asar, 'desktop', 'main.cjs'));
    const {createLibrary, Library} = requireFromAsar('./library.cjs');
    const {Catalog} = requireFromAsar('./catalog.cjs');
    await createLibrary(args.root, '云端合成验收');
    const library = new Library(args.root, args.cache);
    await library.open();
    await library.save(args.system, [], 'cloud-ci', 'cloud-ci');
    library.close();
    const catalog = new Catalog(args.root);
    await catalog.scan();
    await catalog.save({id: args.folderId, kind: 'folder', name: '回收站验收文件夹', folderId: ''}, [], 'cloud-ci');
    const picture = pathMod.join(args.staging, '夹具截图.png');
    await fsp.writeFile(picture, Buffer.from(args.pngBase64, 'base64'));
    const asset = await catalog.importFile(picture, args.folderId, 'cloud-ci');
    const metadata = JSON.parse(await fsp.readFile(pathMod.join(asar, 'package.json'), 'utf8'));
    return {asar, version: metadata.version, name: metadata.name, asset};
  }, {root: fixture, cache: path.join(staging, 'fixture-cache'), staging, pngBase64, system, folderId: 'fixture-folder'});
  assert.equal(created.name, 'quick-interface-finder');
  assert.equal(created.version, expectedVersion, 'packaged ASAR version');
  assert.equal(created.asset.type, 'image');
  assert.equal(created.asset.deleted, false);
  const fixtureRevisions = await fs.readdir(path.join(fixture, 'revisions'));
  const fixtureCatalogRevisions = await fs.readdir(path.join(fixture, 'catalog', 'revisions'));
  assert.equal(fixtureRevisions.length, 1, 'one system revision');
  assert.equal(fixtureCatalogRevisions.length, 2, 'folder and image catalog revisions');
  await fs.access(path.join(fixture, 'media', created.asset.file));
  report.fixture = {
    root: fixture,
    asar: created.asar,
    screens: 20,
    systemRevisions: fixtureRevisions.length,
    catalogRevisions: fixtureCatalogRevisions.length,
    assetId: created.asset.id,
    assetFile: created.asset.file,
    createdBy: 'packaged app.asar Library/Catalog in the Electron main process',
  };
  await closeApp(app);
  app = null;
  page = null;
  report.checks.push('synthetic 20-screen fixture created by the packaged ASAR');

  // 2. Launch the real packaged EXE against that fixture with an isolated profile.
  page = null;
  app = await electron.launch({
    executablePath: exe,
    args: [],
    cwd: installRoot,
    env: cleanEnv({
      QUICK_UI_USER_DATA: profile,
      QUICK_UI_LIBRARY_PATH: fixture,
      ELECTRON_ENABLE_LOGGING: '0',
    }),
    timeout: 180000,
  });
  page = await app.firstWindow();
  page.on('pageerror', (error) => report.pageErrors.push(error.message));
  await page.waitForFunction(() => !!window.quickUI, null, {timeout: 60000});
  await page.locator('.seek-shell').waitFor({timeout: 120000});
  await closeOnboarding(page);
  assert.equal(await app.evaluate(({app: electronApp}) => electronApp.getVersion()), expectedVersion);
  const boot = await page.evaluate(() => window.quickUI.boot());
  assert.equal(boot.settings.hosted, false);
  assert.equal(boot.settings.version, expectedVersion);
  assert.equal(path.resolve(boot.library.root).toLowerCase(), path.resolve(fixture).toLowerCase());
  const systemRecord = boot.library.records.find((record) => record.recordId === 'system-ui');
  assert.ok(systemRecord, 'fixture system record missing');
  assert.equal(systemRecord.payload.screens.length, 20);
  assert.equal(boot.library.storage.storage, 'direct-folder');
  assert.equal(boot.library.storage.connected, true);
  assert.equal(boot.library.storage.writable, true);
  assert.equal(boot.library.storage.state, 'ready');
  assert.match(boot.library.storage.phase, /普通文件夹/);
  report.boot = {
    version: boot.settings.version,
    libraryRoot: boot.library.root,
    screens: systemRecord.payload.screens.length,
    storage: boot.library.storage,
    aiReady: boot.library.ai.ready,
  };
  report.checks.push('packaged EXE boots the fixture library with direct-folder storage');

  // 3. Default two-value summary, expand and collapse.
  const systemRow = page.locator('tr[data-folder-id="system_system-ui"]');
  await systemRow.waitFor({timeout: 60000});
  await expect(systemRow.getByRole('button', {name: /展开详情/})).toBeVisible();
  assert.equal(await systemRow.locator('.dossier-engine').count(), 2, 'default engine summary must show two items');
  await expect(systemRow.locator('.dossier-summary-more').first()).toContainText('展开详情查看');
  const compactHeight = (await systemRow.boundingBox()).height;
  await systemRow.getByRole('button', {name: /展开详情/}).click();
  await expect(systemRow.getByRole('button', {name: /收起详情/})).toBeVisible();
  await expect(systemRow.locator('.dossier-summary-more')).toHaveCount(0);
  assert.equal(await systemRow.locator('.dossier-engine').count(), 40, 'expanded engine list must show every screen');
  assert.ok(await systemRow.locator('.dossier-group').count() >= 20);
  await expect(systemRow.getByText('界面 20', {exact: true}).first()).toBeVisible();
  const expandedHeight = (await systemRow.boundingBox()).height;
  assert.ok(expandedHeight > compactHeight + 120, `expanded row should grow: ${compactHeight} -> ${expandedHeight}`);
  await page.screenshot({path: path.join(screenshots, 'dossier-expanded.png'), animations: 'disabled'});
  await systemRow.getByRole('button', {name: /收起详情/}).click();
  await expect(systemRow.getByRole('button', {name: /展开详情/})).toBeVisible();
  assert.equal(await systemRow.locator('.dossier-engine').count(), 2);
  const collapsedHeight = (await systemRow.boundingBox()).height;
  assert.ok(Math.abs(collapsedHeight - compactHeight) < 3, 'collapse must restore the compact row');
  report.summary = {compactHeight, expandedHeight, collapsedHeight, defaultItems: 2, expandedEngines: 40};
  report.checks.push('two-item summary, expand and collapse behave in the packaged UI');

  // 4. The library:// image protocol serves the catalog image.
  const folderRow = page.locator('tr[data-folder-id="fixture-folder"]');
  await folderRow.waitFor({timeout: 60000});
  const thumb = folderRow.locator('.dossier-attachment-thumb');
  await expect(thumb).toHaveCount(1);
  const image = thumb.locator('img');
  const imageSource = await image.getAttribute('src');
  assert.match(imageSource, /^library:\/\/media\/[a-f0-9]{64}\.png\?library=/);
  await expect.poll(() => image.evaluate((element) => element.complete && element.naturalWidth > 0), {timeout: 60000}).toBe(true);
  report.imageProtocol = {src: imageSource, naturalWidth: await image.evaluate((element) => element.naturalWidth)};
  report.checks.push('library:// media image is readable in the packaged renderer');

  // 5. Local image recycle bin: delete, thumbnail, restore.
  await thumb.click({button: 'right'});
  const confirm = page.getByRole('dialog', {name: '删除图片', exact: true});
  await expect(confirm).toBeVisible({timeout: 30000});
  await expect(confirm).toContainText('夹具截图.png');
  await confirm.getByRole('button', {name: '确认删除图片', exact: true}).click();
  await expect(confirm).toBeHidden({timeout: 60000});
  await expect(folderRow.locator('.dossier-attachment-thumb')).toHaveCount(0);
  const trash = await page.evaluate(() => window.quickUI.catalogImageTrash());
  assert.equal(trash.items.length, 1);
  const trashItemInfo = trash.items[0];
  assert.equal(trashItemInfo.status, 'ready');
  assert.match(trashItemInfo.thumbnailURL, /^library:\/\/recycle\//);
  assert.ok(path.resolve(trashItemInfo.recyclePath).startsWith(path.resolve(profile) + path.sep),
    'recycle copy must live in the isolated profile');
  assert.ok((await fs.readFile(trashItemInfo.recyclePath)).length > 0);
  await page.getByRole('button', {name: '已删除图片', exact: true}).click();
  const trashDialog = page.getByRole('dialog', {name: '已删除图片', exact: true});
  await expect(trashDialog).toBeVisible();
  const trashRow = trashDialog.locator('.folder-trash-item').filter({hasText: '夹具截图.png'});
  await expect(trashRow).toHaveCount(1);
  const trashImage = trashRow.getByRole('img', {name: '夹具截图.png'});
  await expect(trashImage).toBeVisible();
  await expect.poll(() => trashImage.evaluate((element) => element.complete && element.naturalWidth > 0), {timeout: 60000}).toBe(true);
  await expect(trashRow).toContainText('可恢复');
  await page.screenshot({path: path.join(screenshots, 'image-recycle.png'), animations: 'disabled'});
  await trashRow.getByRole('button', {name: '恢复图片', exact: true}).click();
  await expect(trashRow).toHaveCount(0, {timeout: 60000});
  await expect.poll(async () => {
    const rows = await page.evaluate(() => window.quickUI.catalogList());
    return rows.records.find((record) => record.recordId === created.asset.id)?.payload.deleted;
  }, {timeout: 30000}).toBe(false);
  await expect.poll(async () => {
    const rows = await page.evaluate(() => window.quickUI.catalogList());
    const record = rows.records.find((entry) => entry.recordId === created.asset.id);
    return Boolean(record?.payload.file) && fs.stat(path.join(fixture, 'media', record.payload.file)).then(() => true, () => false);
  }, {timeout: 60000}).toBe(true);
  await expect.poll(async () => fs.stat(path.join(fixture, '素材', '回收站验收文件夹', '夹具截图.png')).then(() => true, () => false),
    {timeout: 60000}).toBe(true);
  await trashDialog.getByRole('button', {name: '关闭已删除图片', exact: true}).click();
  await expect(trashDialog).toBeHidden();
  await expect(folderRow.locator('.dossier-attachment-thumb')).toHaveCount(1, {timeout: 60000});
  report.recycle = {
    status: trashItemInfo.status,
    thumbnailURL: trashItemInfo.thumbnailURL,
    recyclePath: trashItemInfo.recyclePath,
    restored: true,
  };
  report.checks.push('local recycle bin deletes, previews the recycle copy and restores one image');

  // 6. No manual commit/update submission is offered.
  assert.equal(await page.getByRole('button', {name: /提交更新/}).count(), 0);
  assert.equal(await page.getByText(/提交更新/).count(), 0);
  const updater = await page.evaluate(() => window.quickUI.updater({action: 'status'}));
  assert.equal(updater.current, expectedVersion);
  assert.equal(updater.phase, 'idle');
  assert.equal(updater.release, undefined);
  report.update = {current: updater.current, hosted: updater.hosted === true, phase: updater.phase, installable: updater.installable, submitted: false};
  report.checks.push('no manual commit/update submission is offered by the direct-folder build');

  // 7. All writes stay in the fixture and the isolated profile.
  const workspaceAfter = await treeSnapshot(workspace, workspaceSkip);
  const installAfter = await treeSnapshot(installRoot);
  assert.deepEqual(workspaceAfter, workspaceBefore, 'packaged app wrote into the workspace');
  assert.deepEqual(installAfter, installBefore, 'packaged app wrote into its install directory');
  await fs.access(path.join(profile, 'settings.json'));
  const libraryManifest = JSON.parse(await fs.readFile(path.join(fixture, 'library.json'), 'utf8'));
  assert.equal(typeof libraryManifest.id, 'string');
  const fixtureEntries = (await fs.readdir(fixture)).sort();
  for (const required of ['library.json', 'revisions', 'catalog', 'media', '素材']) {
    assert.ok(fixtureEntries.includes(required), `fixture missing ${required}`);
  }
  report.dataContainment = {
    workspaceUnchanged: true,
    installDirUnchanged: true,
    profileSettings: path.join(profile, 'settings.json'),
    fixtureEntries,
  };
  report.checks.push('only the isolated fixture and profile were written');

  assert.deepEqual(report.errors, [], 'fixture launch page errors');
  assert.deepEqual(report.pageErrors, [], 'renderer page errors');
  await app.evaluate(({app: electronApp}) => electronApp.exit(0)).catch(() => {});
  await app.close().catch(() => {});
  app = null;
  report.success = true;
  report.screenshots = (await fs.readdir(screenshots)).map((entry) => path.join(screenshots, entry));
  await fs.writeFile(path.join(reportDir, 'packaged-smoke.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  report.success = false;
  report.error = error.stack || String(error);
  report.pageErrors = report.pageErrors || [];
  if (app) {
    if (page) await page.screenshot({path: path.join(screenshots, 'failure.png')}).catch(() => {});
    await closeApp(app);
    app = null;
  }
  await fs.writeFile(path.join(reportDir, 'packaged-smoke.json'), JSON.stringify(report, null, 2) + '\n', 'utf8');
  console.error(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  if (app) await closeApp(app);
}
