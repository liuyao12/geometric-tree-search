#!/usr/bin/env node
/*
 * Offline extractor for the public-domain Wikimedia P1 patch.
 *
 * Decimal SVG coordinates are used only to identify coincident vertices and
 * one of the ten unit-edge directions. The emitted model contains integers
 * only: every vertex is reconstructed as a coefficient vector in Z[zeta_5].
 */
import { readFile, writeFile } from "node:fs/promises";

const SOURCE = "https://upload.wikimedia.org/wikipedia/commons/8/8c/Penrose_Tiling_%28P1%29.svg";
const OUTPUT = new URL("../assets/penrose-p1-patch.js", import.meta.url);
const IDS = ["path4107", "path4109", "path4111", "path4123", "path4135", "path4225"];
const KIND = {
  path4107: "p3",
  path4109: "p2",
  path4111: "p5",
  path4123: "diamond",
  path4135: "boat",
  path4225: "star"
};
const STAR = Array.from({ length: 5 }, (_, index) => {
  const angle = -Math.PI / 2 + index * Math.PI * 2 / 5;
  return [Math.cos(angle), Math.sin(angle)];
});

const multiply = (left, right) => {
  const [a, b, c, d, e, f] = left;
  const [A, B, C, D, E, F] = right;
  return [
    a * A + c * B, b * A + d * B,
    a * C + c * D, b * C + d * D,
    a * E + c * F + e, b * E + d * F + f
  ];
};

function matrix(source = "") {
  const match = source.match(/(matrix|translate)\(([^)]*)\)/);
  if (!match) return [1, 0, 0, 1, 0, 0];
  const values = match[2].trim().split(/[\s,]+/).map(Number);
  return match[1] === "matrix"
    ? values
    : [1, 0, 0, 1, values[0], values[1] || 0];
}

function attributes(source) {
  return Object.fromEntries(
    [...source.matchAll(/([\w:-]+)="([^"]*)"/g)].map(match => [match[1], match[2]])
  );
}

function pathPoints(source) {
  const values = [...source.matchAll(/[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/gi)]
    .map(match => Number(match[0]));
  const points = [];
  for (let index = 0; index < values.length - 2; index += 2) {
    points.push([values[index], values[index + 1]]);
  }
  return points;
}

const svg = process.argv[2]
  ? await readFile(process.argv[2], "utf8")
  : await (async () => {
      const response = await fetch(SOURCE);
      if (!response.ok) throw new Error(`P1 source download failed: ${response.status}`);
      return response.text();
    })();
const layerSource = svg.match(/<g\s+id="layer1"[\s\S]*?>([\s\S]*)<\/g>/)?.[0];
if (!layerSource) throw new Error("P1 layer was not found");
const layerMatrix = matrix(attributes(layerSource.slice(0, layerSource.indexOf(">")))?.transform);

const paths = new Map();
for (const match of svg.matchAll(/<path\b[\s\S]*?\/>/g)) {
  const attr = attributes(match[0]);
  if (!IDS.includes(attr.id)) continue;
  paths.set(attr.id, { attr, points: pathPoints(attr.d) });
}

const tiles = [];
for (const match of layerSource.matchAll(/<use\b[\s\S]*?\/>/g)) {
  const attr = attributes(match[0]);
  const pathId = attr["xlink:href"]?.slice(1);
  if (!paths.has(pathId)) continue;
  const prototype = paths.get(pathId);
  const transform = multiply(layerMatrix, multiply(matrix(attr.transform), matrix(prototype.attr.transform)));
  const [a, b, c, d, e, f] = transform;
  const points = prototype.points.map(([x, y]) => [a * x + c * y + e, b * x + d * y + f]);
  tiles.push({ kind: KIND[pathId], points });
}

const vertices = [];
const tileVertices = tiles.map(tile => ({
  kind: tile.kind,
  vertices: tile.points.map(point => {
    let closest = -1;
    for (let index = 0; index < vertices.length; index++) {
      const dx = vertices[index][0] - point[0];
      const dy = vertices[index][1] - point[1];
      if (dx * dx + dy * dy < .05 * .05) { closest = index; break; }
    }
    if (closest < 0) { closest = vertices.length; vertices.push(point); }
    return closest;
  })
}));

const graph = Array.from({ length: vertices.length }, () => []);
for (const tile of tileVertices) {
  tile.vertices.forEach((from, index) => {
    const to = tile.vertices[(index + 1) % tile.vertices.length];
    const dx = vertices[to][0] - vertices[from][0];
    const dy = -(vertices[to][1] - vertices[from][1]);
    const length = Math.hypot(dx, dy);
    const choices = STAR.flatMap(([x, y], family) => [
      { score: (dx * x + dy * y) / length, family, sign: 1 },
      { score: -(dx * x + dy * y) / length, family, sign: -1 }
    ]).sort((left, right) => right.score - left.score);
    if (choices[0].score < .999999) throw new Error("An SVG edge is not cyclotomic");
    const delta = [0, 0, 0, 0, 0];
    delta[choices[0].family] = choices[0].sign;
    graph[from].push([to, delta]);
    graph[to].push([from, delta.map(value => -value)]);
  });
}

const coefficients = Array(vertices.length);
coefficients[0] = [0, 0, 0, 0, 0];
const queue = [0];
for (let head = 0; head < queue.length; head++) {
  const from = queue[head];
  for (const [to, delta] of graph[from]) {
    const candidate = coefficients[from].map((value, index) => value + delta[index]);
    if (!coefficients[to]) {
      coefficients[to] = candidate;
      queue.push(to);
    } else {
      const difference = coefficients[to].map((value, index) => value - candidate[index]);
      if (!difference.every(value => value === difference[0])) {
        throw new Error("Cyclotomic reconstruction is inconsistent");
      }
    }
  }
}
if (coefficients.some(value => !value)) throw new Error("P1 patch is disconnected");

const centerX = (Math.min(...vertices.map(point => point[0])) + Math.max(...vertices.map(point => point[0]))) / 2;
const centerY = (Math.min(...vertices.map(point => point[1])) + Math.max(...vertices.map(point => point[1]))) / 2;
const origin = vertices
  .map((point, index) => ({ index, distance: (point[0] - centerX) ** 2 + (point[1] - centerY) ** 2 }))
  .sort((left, right) => left.distance - right.distance)[0].index;
const offset = coefficients[origin];
const exactVertices = coefficients.map(coeff => {
  const translated = coeff.map((value, index) => value - offset[index]);
  const gauge = translated[4];
  return translated.map(value => value - gauge);
});

const output = `// Generated by scripts/generate-penrose-p1-patch.mjs from a public-domain P1 patch.\n` +
  `// Runtime geometry contains integers only; SVG decimals never enter the model.\n` +
  `export const P1_SOURCE = ${JSON.stringify(SOURCE)};\n` +
  `export const P1_EXACT_VERTICES = ${JSON.stringify(exactVertices)};\n` +
  `export const P1_EXACT_TILES = ${JSON.stringify(tileVertices.map(tile => [tile.kind, tile.vertices]))};\n`;
await writeFile(OUTPUT, output);
console.log(`wrote ${tiles.length} exact P1 tiles and ${vertices.length} vertices`);
