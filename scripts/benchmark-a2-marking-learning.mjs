import {
  A2_TILE_LOOPS,
  FixedTurtleMarking,
  NoA2Marking,
  OnlineA2Marking,
  makeHexBoundary,
  selectA2FrozenMarking,
  solveA2Tiling
} from "../assets/a2-tiling-engine.js";

globalThis.requestAnimationFrame = callback => callback();

const numberArgument = (name, fallback) => {
  const prefix = `--${name}=`;
  const raw = process.argv.find(argument => argument.startsWith(prefix))?.slice(prefix.length);
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
};

const target = numberArgument("target", 30);
const trainingTarget = numberArgument("training-target", Math.min(target, 30));
const validationTarget = numberArgument("validation-target", Math.min(target, trainingTarget + 10));
const nodeLimit = numberArgument("nodes", 5000);
const trainingSeed = numberArgument("training-seed", 4);
const validationSeed = numberArgument("validation-seed", 2);
const validationSeeds = (process.argv.find(argument => argument.startsWith("--validation-seeds="))?.slice(19) || `${validationSeed},5`)
  .split(",").map(Number).filter(Number.isFinite);
const seeds = (process.argv.find(argument => argument.startsWith("--seeds="))?.slice(8) || "1,2,3,4")
  .split(",").map(Number).filter(Number.isFinite);
const tile = process.argv.find(argument => argument.startsWith("--tile="))?.slice(7) || "turtle";
if (!A2_TILE_LOOPS[tile]) throw new Error(`Unknown built-in A2 tile: ${tile}`);
const boundary = makeHexBoundary(Math.max(50, target * 2));
const seed = { loop: A2_TILE_LOOPS[tile] };

async function run(label, marking, randomSeed, placementTarget = target, limit = nodeLimit) {
  const started = performance.now();
  const result = await solveA2Tiling({
    boundary,
    seed,
    tiles: [tile],
    maximize: true,
    targetPlacements: placementTarget,
    nodeLimit: limit,
    learningWarmupDepth: 10,
    maxMarkingRevisions: 200,
    markingStagnationNodes: 400,
    marking,
    randomSeed
  });
  return {
    label,
    seed: randomSeed,
    result: result.result,
    tiles: result.placements.length,
    nodes: result.stats.nodes,
    backtracks: result.stats.backtracks,
    revisions: result.stats.revision ?? 0,
    support: result.stats.supportSites ?? 0,
    prunes: result.stats.prunes ?? 0,
    milliseconds: Math.round(performance.now() - started)
  };
}

const learner = new OnlineA2Marking({ maxWitnessTrials: 128, yieldEvery: 128 });
const training = await run("online-training", learner, trainingSeed, trainingTarget);
const selection = await selectA2FrozenMarking({
  learner,
  validationSeeds,
  validationNodeLimit: Math.min(nodeLimit, 3000),
  solveOptions: {
    boundary, seed, tiles: [tile], maximize: true,
    targetPlacements: validationTarget, learningWarmupDepth: 10,
    maxMarkingRevisions: 200, markingStagnationNodes: 400
  }
});
const validation = selection.validation.map(entry => ({
  row: {
    label: `candidate-r${entry.revision}`,
    seed: entry.seed,
    result: entry.result.result,
    tiles: entry.result.placements.length,
    nodes: entry.result.stats.nodes,
    backtracks: entry.result.stats.backtracks,
    revisions: entry.result.stats.revision ?? 0,
    support: entry.result.stats.supportSites ?? 0,
    prunes: entry.result.stats.prunes ?? 0
  },
  marking: entry.marking
}));
const frozen = selection.marking;
const rows = [training];

for (const randomSeed of seeds) {
  rows.push(await run("naive", new NoA2Marking(), randomSeed));
  if (tile === "turtle") rows.push(await run("human-fixed", new FixedTurtleMarking(1), randomSeed));
  rows.push(await run("learned-frozen", frozen, randomSeed));
}

const successful = rows.filter(row => row.result === "yes");
const medians = Object.fromEntries([...new Set(rows.map(row => row.label))].map(label => {
  const values = successful.filter(row => row.label === label).map(row => row.nodes).sort((a, b) => a - b);
  return [label, values.length ? values[Math.floor(values.length / 2)] : null];
}));

console.table(rows);
console.log(JSON.stringify({ tile, target, trainingTarget, validationTarget, nodeLimit, trainingSeed, validationSeeds: selection.seeds, candidateCount: selection.candidates.length, selectedRevision: frozen.metadata.learnedRevisions ?? 0, learnedSupport: frozen.support.length, validation: validation.map(entry => entry.row), medianSuccessfulNodes: medians }, null, 2));
