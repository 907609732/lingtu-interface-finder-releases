// Verify the exact CI tool versions that the workflow pins in package.json.
import fs from 'node:fs';
import path from 'node:path';

const expected = {'archiver': '8.0.0', '@electron/asar': '3.4.1', '@playwright/test': '1.64.1'};
const problems = [];
if (process.versions.node !== '24.18.0') problems.push(`node ${process.versions.node} != 24.18.0`);
for (const [name, wanted] of Object.entries(expected)) {
  const file = path.join(process.cwd(), 'node_modules', name, 'package.json');
  try {
    const actual = JSON.parse(fs.readFileSync(file, 'utf8')).version;
    if (actual !== wanted) problems.push(`${name} ${actual} != ${wanted}`);
  } catch (error) {
    problems.push(`${name} not installed: ${error.message}`);
  }
}
if (problems.length) throw Error('CI tool version check failed: ' + problems.join('; '));
console.log(JSON.stringify({ok: true, node: process.versions.node, tools: expected}, null, 2));
