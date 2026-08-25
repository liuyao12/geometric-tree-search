#!/usr/bin/env node
// Oracle-side crop bridge for the sealed headless Ice VI benchmark.  The
// caller receives only the requested molecular crop, never the surrounding
// resolved supercell.  Core browser and learner code do not import this file.

import { resolveIceViIceRuleMicrostate } from "../apps/iqc-growth-live/ice-vi-browser-fixture.js";

function displacement(first, second, lengths) {
  return first.map((value, axis) => {
    let delta = second[axis] - value;
    delta -= Math.round(delta / lengths[axis]) * lengths[axis];
    return delta;
  });
}

function distance(first, second, lengths) {
  return Math.hypot(...displacement(first, second, lengths));
}

export function iceViMolecularCrop({ seed, repeats, centerFraction, radius }) {
  if (!Array.isArray(centerFraction) || centerFraction.length !== 3
    || !(radius > 0)) throw new Error("crop requires centerFraction[3] and positive radius");
  const resolved = resolveIceViIceRuleMicrostate(seed, repeats);
  const lengths = resolved.cell.map((vector, axis) => vector[axis]);
  const center = centerFraction.map((fraction, axis) => fraction * lengths[axis]);
  const oxygens = resolved.atoms.map((atom, index) => atom.species === "O" ? index : -1)
    .filter((index) => index >= 0);
  const deuteria = resolved.atoms.map((atom, index) => atom.species === "D" ? index : -1)
    .filter((index) => index >= 0);
  const owners = new Map(oxygens.map((index) => [index, []]));
  deuteria.forEach((index) => {
    const owner = oxygens.map((oxygen) => ({ oxygen,
      distance: distance(resolved.atoms[index].position, resolved.atoms[oxygen].position, lengths) }))
      .sort((first, second) => first.distance - second.distance || first.oxygen - second.oxygen)[0].oxygen;
    owners.get(owner).push(index);
  });
  if ([...owners.values()].some((members) => members.length !== 2)) {
    throw new Error("resolved Ice VI crop does not contain two donor D per oxygen");
  }
  const moleculeIds = [];
  const sites = [];
  oxygens.forEach((oxygenIndex) => {
    const oxygen = resolved.atoms[oxygenIndex];
    if (Math.hypot(...oxygen.position.map((value, axis) => value - center[axis])) > radius) return;
    moleculeIds.push(oxygen.q.join(":"));
    sites.push(["O", oxygen.position.slice()]);
    owners.get(oxygenIndex).sort((first, second) => first - second).forEach((deuteriumIndex) => {
      const delta = displacement(oxygen.position, resolved.atoms[deuteriumIndex].position, lengths);
      sites.push(["D", oxygen.position.map((value, axis) => value + delta[axis])]);
    });
  });
  return {
    seed,
    repeats: repeats.slice(),
    centerFraction: centerFraction.slice(),
    center,
    radius,
    cell: resolved.cell,
    moleculeIds,
    species: sites.map(([species]) => species),
    positions: sites.map(([, position]) => position),
    sites,
    molecules: moleculeIds.length,
    atoms: sites.length,
    resolverAudit: resolved.audit,
    sourceSupercellCoordinatesReturned: false,
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const request = JSON.parse(process.argv[2] || "{}");
  process.stdout.write(`${JSON.stringify(iceViMolecularCrop(request))}\n`);
}
