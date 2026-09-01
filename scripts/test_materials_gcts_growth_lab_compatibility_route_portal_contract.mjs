import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const compatibility = readFileSync(new URL("../iqc-growth-live/index.html", import.meta.url), "utf8");
const homepage = readFileSync(new URL("../index.html", import.meta.url), "utf8");

assert.match(homepage, /href="\.\/iqc-growth-live\/">Open Materials Growth Lab/);
assert.match(compatibility, /<base href="\.\.\/apps\/iqc-growth-live\/">/);
assert.match(compatibility, /\.\/app\.js\?v=20260901-440/);
assert.match(compatibility, /\.\/style\.css\?v=20260901-440/);

console.log("growth lab compatibility route portal contract: all tests passed");
