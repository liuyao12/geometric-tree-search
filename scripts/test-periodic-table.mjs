import assert from "node:assert/strict";
import { PERIODIC_ELEMENTS } from "../apps/iqc-growth-live/periodic-table.js";

assert.equal(PERIODIC_ELEMENTS.length, 118);
assert.equal(new Set(PERIODIC_ELEMENTS.map((element) => element.symbol)).size, 118);
assert.equal(new Set(PERIODIC_ELEMENTS.map((element) => element.atomicNumber)).size, 118);
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "H").column, 1);
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "He").column, 18);
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "Cl").atomicNumber, 17);
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "La").row, 8);
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "Og").atomicNumber, 118);
assert.ok(PERIODIC_ELEMENTS.every((element) => element.column >= 1 && element.column <= 18 && element.row >= 1 && element.row <= 9));
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "O").phase, "gas");
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "Br").phase, "liquid");
assert.equal(PERIODIC_ELEMENTS.find((element) => element.symbol === "Fe").phase, "solid");
assert.deepEqual([...new Set(PERIODIC_ELEMENTS.map((element) => element.phase))].sort(), ["gas", "liquid", "solid"]);

console.log("mini periodic table: all 118 elements have positions, atomic numbers, and standard-state phases");
