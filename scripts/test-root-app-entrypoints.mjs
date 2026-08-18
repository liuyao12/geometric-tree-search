#!/usr/bin/env node

import assert from "node:assert/strict";
import { readdir, readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const appsRoot = path.join(root, "apps");
const appNames = [];

for (const name of await readdir(appsRoot)) {
  const appIndex = path.join(appsRoot, name, "index.html");
  try {
    if ((await stat(appIndex)).isFile()) appNames.push(name);
  } catch {
    // Non-app support directories do not need a root URL.
  }
}

for (const name of appNames.sort()) {
  const source = await readFile(path.join(appsRoot, name, "index.html"), "utf8");
  const alias = await readFile(path.join(root, name, "index.html"), "utf8");
  const expectedBase = `<base href="../apps/${name}/">`;
  assert.ok(alias.includes(expectedBase), `${name} root entry point has the correct asset base`);
  assert.equal(
    alias.replace(/^\s*<!-- Canonical root-level entry point; assets remain in apps\/.*? -->\n\s*<base href="[^"]+">\n/m, ""),
    source,
    `${name} root entry point mirrors apps/${name}/index.html`
  );
}

console.log(`Root app entry-point checks passed (${appNames.length} apps)`);
