import { tileSpecs } from "../apps/3d-lattice-tiler/engine.js";

const gcd = (a, b) => {
  a = Math.abs(Math.round(a));
  b = Math.abs(Math.round(b));
  while (b) [a, b] = [b, a % b];
  return a || 1;
};

const formatTValue = (weight, maxValue) => {
  if (Math.abs(weight - Math.round(weight)) < 1e-9 && Math.abs(maxValue - Math.round(maxValue)) < 1e-9) {
    const divisor = gcd(weight, maxValue);
    const numerator = Math.round(weight) / divisor;
    const denominator = Math.round(maxValue) / divisor;
    return denominator === 1 ? String(numerator) : `${numerator}/${denominator}`;
  }
  return (weight / maxValue).toFixed(5).replace(/0+$/u, "").replace(/\.$/u, "");
};

const profile = (tile, maxValue) => {
  const counts = new Map();
  for (const point of tile.occupancy_points ?? []) {
    if (point.kind === "interior") continue;
    const label = point.display_symbolic ?? point.symbolic ?? formatTValue(point.weight, maxValue);
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => Number(evalFraction(a[0])) - Number(evalFraction(b[0])));
};

const evalFraction = (label) => {
  const [num, den] = label.split("/").map(Number);
  return Number.isFinite(den) ? num / den : num;
};

const failures = [];
for (const [modeKey, entry] of Object.entries(tileSpecs.TILING_REGISTRY)) {
  const tiles = entry.build();
  for (const tile of tiles) {
    const maxValue = tile.solid_angle?.max_value ?? tileSpecs.LEGACY_SOLID_ANGLE_MAX;
    const values = profile(tile, maxValue);
    const isThreeDimensional = (tile.verts ?? []).some(v => v[2] !== tile.verts?.[0]?.[2]);
    const hasOnlyFullInterior = values.length === 1 && values[0][0] === "1";
    if (!values.length) failures.push(`${modeKey}/${tile.name}: no solid-angle samples`);
    if (isThreeDimensional && hasOnlyFullInterior) failures.push(`${modeKey}/${tile.name}: only full solid-angle samples (t=1)`);
    const label = values.map(([value, count]) => `${value}×${count}`).join(", ");
    console.log(`${modeKey}/${tile.name} [max=${maxValue}, kind=${tile.solid_angle?.kind ?? "numeric"}, t full=1]: ${label}`);
  }
}

if (failures.length) {
  console.error("\nSolid-angle validation failures:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}
