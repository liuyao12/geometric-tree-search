import { readFileSync } from "node:fs";
import { verify } from "./kernel.mjs";
import { verifyOverlaps } from "./overlap-rules.mjs";
const file = process.argv[2];
if (!file) throw Error("Usage: node verify-artifact.mjs exported-audit.json");
const data = JSON.parse(readFileSync(file, "utf8"));
if (data.schema !== "materials-growth-v2/1")
  throw Error("Unsupported artifact schema");
const result = verify(data.model, data.selected);
if (data.connectionPolicy === "observed-only") {
  if (!data.marking?.overlapRules || !data.grammar || !data.points)
    throw Error("Missing observed-only rule provenance");
  result.overlaps = verifyOverlaps(
    data.grammar,
    data.marking.overlapRules,
    { points: data.points },
    new Map(data.model.candidates.map((c) => [c.id, c])),
    data.selected,
  );
  result.legal &&= result.overlaps.legal;
}
console.log(JSON.stringify({ scope: data.scope, ...result }, null, 2));
if (!result.legal) process.exitCode = 1;
