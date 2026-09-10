import { readFileSync } from "node:fs";
import { verify } from "./kernel.mjs";
const file = process.argv[2];
if (!file) throw Error("Usage: node verify-artifact.mjs exported-audit.json");
const data = JSON.parse(readFileSync(file, "utf8"));
if (data.schema !== "materials-growth-v2/1")
  throw Error("Unsupported artifact schema");
const result = verify(data.model, data.selected);
console.log(JSON.stringify({ scope: data.scope, ...result }, null, 2));
if (!result.legal) process.exitCode = 1;
