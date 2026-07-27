#!/usr/bin/env node
// Lightweight DOM/canvas harness for the Turtle playground's online engine.

import assert from "node:assert/strict";

class MockClassList {
  constructor() { this.values = new Set(); }
  add(...values) { values.forEach(value => this.values.add(value)); }
  remove(...values) { values.forEach(value => this.values.delete(value)); }
  contains(value) { return this.values.has(value); }
  toggle(value, force) { if (force ?? !this.values.has(value)) this.values.add(value); else this.values.delete(value); }
}

const context = new Proxy({}, {
  get(target, property) {
    if (!(property in target)) target[property] = () => undefined;
    return target[property];
  },
  set(target, property, value) { target[property] = value; return true; }
});

class MockElement {
  constructor(id) {
    this.id = id;
    this.width = 1200;
    this.height = 780;
    this.value = id === "coronaTarget" ? "2" : "";
    this.checked = id === "onlineLearning";
    this.textContent = "";
    this.hidden = false;
    this.dataset = {};
    this.classList = new MockClassList();
    this.attributes = new Map();
    this.listeners = new Map();
  }
  getContext() { return context; }
  getBoundingClientRect() { return { left:0, top:0, right:1200, bottom:780, width:1200, height:780 }; }
  addEventListener(type, listener) { this.listeners.set(type, listener); }
  setAttribute(name, value) { this.attributes.set(name, String(value)); }
  getAttribute(name) { return this.attributes.get(name) ?? null; }
  setPointerCapture() {}
}

const elements = new Map();
const element = id => {
  if (!elements.has(id)) elements.set(id, new MockElement(id));
  return elements.get(id);
};

globalThis.document = {
  getElementById: element,
  querySelector: selector => selector === ".symmetry-label" ? element("symmetry-label") : null,
  querySelectorAll: () => [],
  addEventListener() {},
  removeEventListener() {}
};
globalThis.window = {
  devicePixelRatio:1,
  addEventListener() {},
  setTimeout,
  clearTimeout,
  requestAnimationFrame: callback => setTimeout(() => callback(performance.now()),0)
};

await import("../apps/turtle-tiling-game/app.js");

const targetCorona = Number(process.argv[2] || 3);
const trefoil = window.__turtleGctsDebug.runOnline("trefoil",targetCorona);
const hexagon = window.__turtleGctsDebug.runOnline("hexagon",targetCorona);
for (const result of [trefoil,hexagon]) {
  assert.ok(result.tiles > 1, `${result.center} should be surrounded by Turtle tiles`);
  assert.ok(result.corona >= 1, `${result.center} should reach a nonzero corona`);
  assert.equal(result.replayValid,true, `${result.center} patch should replay under its learned marking`);
}

const validLoop = [[0,0,0],[2,0,-2],[2,2,-4],[0,2,-2]];
const crossedLoop = [[0,0,0],[2,2,-4],[0,2,-2],[2,0,-2]];
assert.equal(window.__turtleGctsDebug.validateLoop(validLoop,true).valid,true,"simple closed lattice loop should validate");
assert.equal(window.__turtleGctsDebug.validateLoop(crossedLoop,true).valid,false,"self-crossing loop should be rejected");

const customHatLoop = [[0,0,0],[1,0,-1],[1,1,-2],[3,0,-3],[4,1,-5],[3,2,-5],[3,3,-6],[1,4,-5],[0,6,-6],[-1,6,-5],[-1,5,-4],[-1,4,-3],[0,3,-3],[-1,2,-1]];
const customDefinition = window.__turtleGctsDebug.setCustomLoop(customHatLoop,"Custom Hat outline");
assert.equal(customDefinition.vertices,14);
assert.ok(customDefinition.orientations>0);
const custom = window.__turtleGctsDebug.runOnline("trefoil",3,"custom");
assert.ok(custom.tiles>1,"custom tile should enter the same search pipeline");
assert.equal(custom.replayValid,true);
const customHexagon = window.__turtleGctsDebug.runOnline("hexagon",1,"custom");
assert.ok(customHexagon.tiles>1,"custom tile should run around a Hexagon center");
assert.equal(customHexagon.replayValid,true);

const hat = window.__turtleGctsDebug.runOnline("trefoil",3,"hat");
assert.ok(hat.tiles>1,"Hat should enter the same search pipeline");
assert.equal(hat.replayValid,true);
const hatHexagon = window.__turtleGctsDebug.runOnline("hexagon",1,"hat");
assert.ok(hatHexagon.tiles>1,"Hat should run around a Hexagon center");
assert.equal(hatHexagon.replayValid,true);

console.log(JSON.stringify({ trefoil,hexagon,hat,hatHexagon,custom,customHexagon,customDefinition },null,2));
