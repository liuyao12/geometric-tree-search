import { CirclePackingSearch } from "../assets/circle-packing-search.js";

function option(name, fallback) {
  const prefix = `--${name}=`;
  const argument = process.argv.slice(2).find(item => item.startsWith(prefix));
  return argument ? Number(argument.slice(prefix.length)) : fallback;
}
const minBend = option("min-bend", 7);
const maxBend = option("max-bend", 20);
const maxCircles = option("max-circles", 8);
const nodeLimit = option("node-limit", 100000);
if (![minBend, maxBend, maxCircles, nodeLimit].every(Number.isInteger)
    || minBend < 2 || maxBend < minBend || maxCircles < 1 || nodeLimit < 1) {
  throw new Error("scan options must be positive integers with max-bend >= min-bend");
}

const families = [];
for (let bend = minBend; bend <= maxBend; bend += 1) {
  families.push([2, 3, bend], [2, 4, bend], [2, 3, 6, bend]);
}

for (const bends of families) {
  let result = null;
  for (let horizon = bends.length; horizon <= maxCircles; horizon += 1) {
    const search = new CirclePackingSearch(bends, { maxCircles: horizon, nodeLimit });
    while (search.status === "running") search.step(1000);
    result = search;
    if (search.status === "found" || search.status === "node_limit") break;
  }
  const record = {
    bends,
    status: result.status,
    maxCircles: result.maxCircles,
    nodes: result.nodes,
  };
  if (result.solution) record.circles = result.solution.circles;
  process.stdout.write(`${JSON.stringify(record)}\n`);
}
