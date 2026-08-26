#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";

const app = fs.readFileSync(new URL("../apps/iqc-growth-live/app.js", import.meta.url), "utf8");
const match = app.match(/const MATERIALS_STUDY_RECIPES = Object\.freeze\((\[[\s\S]*?\])\);\n\nconst MATERIALS_STUDY_COMPARISONS/);
assert.ok(match, "study recipe table remains extractable");
const recipes = Function(`"use strict"; return (${match[1]});`)();

assert.equal(recipes.length, 8);
assert.equal(new Set(recipes.map(({ id }) => id)).size, recipes.length);
assert.deepEqual(new Set(recipes.map(({ kind }) => kind)),
  new Set(["crystal", "molecular", "quasicrystal", "2D", "interface", "microstructure", "confinement", "negative control"]));

const scenarios = new Set(["competition", "iceIh", "cdyb", "moire", "hbn", "random"]);
const geometryModes = new Set(["auto", "module", "offlattice"]);
const protocols = new Set(["bulk", "epitaxy", "impingement", "pore-fill"]);
const representations = new Set(["ports", "halo", "chiral-halo"]);
const observables = new Set(["rdf", "sq", "order"]);

for (const recipe of recipes) {
  assert.ok(scenarios.has(recipe.scenario), `${recipe.id}: known sample`);
  assert.ok(geometryModes.has(recipe.geometryMode), `${recipe.id}: known geometry hypothesis`);
  assert.ok(protocols.has(recipe.protocol), `${recipe.id}: known growth protocol`);
  assert.ok(representations.has(recipe.marking.representation), `${recipe.id}: known marking representation`);
  assert.ok([2, 3].includes(recipe.marking.reach), `${recipe.id}: bounded marking reach`);
  assert.equal(recipe.marking.channels, 0, `${recipe.id}: channel count remains geometry-derived`);
  assert.ok(observables.has(recipe.observable), `${recipe.id}: known structural microscope`);
  assert.ok(recipe.encodings.length >= 3, `${recipe.id}: geometry encoding manifest`);
  assert.ok(recipe.observables.length >= 4, `${recipe.id}: observable manifest`);
  assert.ok(recipe.prediction.length > 100, `${recipe.id}: falsifiable geometric prediction`);
  assert.ok(recipe.route[0], `${recipe.id}: explicit pipeline route`);
  assert.ok(recipe.boundary.length > 70, `${recipe.id}: material claim boundary`);
}

assert.ok(recipes.some(({ kind }) => kind === "negative control"));
assert.ok(recipes.some(({ scenario }) => scenario === "iceIh"));
assert.ok(recipes.some(({ scenario }) => scenario === "cdyb"));
assert.ok(recipes.some(({ scenario }) => scenario === "moire"));
console.log("materials study recipes passed");
