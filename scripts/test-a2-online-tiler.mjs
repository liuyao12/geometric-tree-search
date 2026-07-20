import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  A2_TILE_LOOPS,
  FixedTurtleMarking,
  NoA2Marking,
  OnlineA2Marking,
  a2Transform,
  makeHexBoundary,
  polygonCells,
  selectA2FrozenMarking,
  solveA2Tiling,
  tileOrientations
} from "../assets/a2-tiling-engine.js";

globalThis.requestAnimationFrame ??= callback => setTimeout(callback, 0);

for (const tile of ["hat", "turtle"]) {
  const result = await solveA2Tiling({ boundary: A2_TILE_LOOPS[tile], tiles: [tile], nodeLimit: 100 });
  assert.equal(result.result, "yes", `${tile} must tile its own boundary`);
  assert.equal(result.placements.length, 1);
}

const customHexagon = await solveA2Tiling({
  boundary: A2_TILE_LOOPS.hexagon,
  tiles: ["custom-hexagon"],
  customTiles: { "custom-hexagon": A2_TILE_LOOPS.hexagon },
  nodeLimit: 100
});
assert.equal(customHexagon.result, "yes", "custom A2 loops must use the same generic placement engine");
assert.equal(customHexagon.placements[0].tile, "custom-hexagon");

const impossible = await solveA2Tiling({ boundary: A2_TILE_LOOPS.hat, tiles: ["turtle"], nodeLimit: 1000 });
assert.equal(impossible.result, "no", "an exhaustive finite search returns a decision");

// The article demo and the online-learning page must exercise this same search.
// Its known Turtle marking is the oracle that the geometry can grow well past a
// small local patch when supplied as a constraint add-on. The strict nearest-
// shell policy deliberately changes its old branch order.
const fixedOrientation = tileOrientations("turtle", A2_TILE_LOOPS.turtle)[1];
const fixedTranslation = a2Transform(A2_TILE_LOOPS.turtle[0], fixedOrientation.symmetry);
const fixedSeed = {
  loop: A2_TILE_LOOPS.turtle.map(point => a2Transform(point, fixedOrientation.symmetry)),
  markingPlacement: { tile: "turtle", orientation: fixedOrientation, translation: fixedTranslation }
};
const fixed = await solveA2Tiling({
  boundary: makeHexBoundary(100),
  seed: fixedSeed,
  tiles: ["turtle"],
  maximize: true,
  targetPlacements: 50,
  nodeLimit: 1000,
  marking: new FixedTurtleMarking(1),
  randomSeed: 2
});
assert.equal(fixed.result, "yes", "the shared tiler must grow a large patch with the article marking");
assert.equal(fixed.placements.length, 50);
assert.equal(new Set(fixed.placements.map(placement => placement.id)).size, 50, "growth cannot reuse a placement");
const occupiedTriangles = new Set(polygonCells(fixedSeed.loop));
for (const placement of fixed.placements) {
  for (const cell of polygonCells(placement.loop)) {
    assert.ok(!occupiedTriangles.has(cell), `marked growth overlaps triangular cell ${cell}`);
    occupiedTriangles.add(cell);
  }
}

const recoveredLearner = new OnlineA2Marking({ maxWitnessTrials: 32, yieldEvery: 32 });
const recoveredUpdates = [];
const recoveredChoiceStack = [];
const recovered = await solveA2Tiling({
  boundary: makeHexBoundary(50),
  seed: { loop: fixedSeed.loop },
  tiles: ["turtle"],
  maximize: true,
  targetPlacements: 100,
  nodeLimit: 3000,
  learningWarmupDepth: 10,
  maxMarkingRevisions: 30,
  marking: recoveredLearner,
  randomSeed: 4,
  onEvent: event => {
    if (event.type === "learn") recoveredUpdates.push(event.update);
    if (event.type === "trial") assert.equal(event.frontierDistance, event.nearestFrontierDistance, "growth may branch only on the shell closest to the initial tile");
    if (event.type === "placement") recoveredChoiceStack.push(event.frontierDistance);
    if (event.type === "backtrack") recoveredChoiceStack.pop();
    if (event.type === "marking-reencoded") recoveredChoiceStack.length = 0;
  }
});
assert.equal(recovered.result, "yes", "the sparse symbolic learner must keep growing while learning");
assert.equal(recovered.placements.length, 100, "Turtle-only online learning must cover a large patch");
assert.equal(recoveredChoiceStack.length, 100);
assert.ok(recoveredChoiceStack.every((distance, index) => index === 0 || distance >= recoveredChoiceStack[index - 1]), "the successful branch must close inner shells before opening outer ones");
const unmarkedLarge = await solveA2Tiling({
  boundary: makeHexBoundary(50), seed: { loop: fixedSeed.loop }, tiles: ["turtle"],
  maximize: true, targetPlacements: 100, nodeLimit: 5000,
  marking: new NoA2Marking(), randomSeed: 4
});
assert.equal(unmarkedLarge.result, "yes");
assert.ok(recovered.stats.nodes < unmarkedLarge.stats.nodes, `GCTS memoization must traverse fewer nodes than the same unmarked search (${recovered.stats.nodes} < ${unmarkedLarge.stats.nodes})`);
assert.ok(recovered.stats.backtracks < unmarkedLarge.stats.backtracks, "GCTS memoization must skip repeated failed subtrees");
assert.ok(recovered.stats.prunes > 0, "learned geometric mismatches must reject repeated placement candidates");
assert.equal(recovered.stats.suspended, false, "the learned support must never be erased by suspension");
assert.ok(recovered.stats.revision > 0, "growth must learn inequalities on the fly");
assert.equal(recovered.stats.inequalities, recovered.stats.revision);
assert.ok(recovered.stats.supportSites > 0, "online learning must retain visible learned support");
assert.equal(recoveredLearner.failures.length, recoveredLearner.inequalities.length);
assert.equal(recovered.stats.encodedFailures + recovered.stats.pendingFailures, recovered.stats.observedFailures, "every observed branch failure is either encoded or pending");
const revisionBeforeReencoding = recoveredLearner.revision;
const failureLedgerBeforeReencoding = recoveredLearner.failures.slice();
const latestWitnessBeforeReencoding = recoveredLearner.inequalities.at(-1).witnessKey;
const reencoding = await recoveredLearner.reencodeLatest();
assert.ok(reencoding, "a geometric witness can be replaced without forgetting its failure");
assert.equal(recoveredLearner.revision, revisionBeforeReencoding, "re-encoding does not erase or create a failure revision");
assert.deepEqual(recoveredLearner.failures, failureLedgerBeforeReencoding, "the complete failure ledger is immutable during re-encoding");
assert.notEqual(recoveredLearner.inequalities.at(-1).witnessKey, latestWitnessBeforeReencoding, "only the latest witness is replaced");
assert.equal(recoveredLearner.inequalities.length, recoveredLearner.failures.length, "every retained failure remains geometrically encoded");
for (const failure of failureLedgerBeforeReencoding) assert.equal(recoveredLearner.compatible(failure.candidate, failure.context, new Map(recoveredLearner.support), recoveredLearner.assignments, false), false, "recompilation keeps every earlier failure rejected");
for (let index = 0; index < recoveredLearner.failures.length; index++) {
  const failure = recoveredLearner.failures[index], inequality = recoveredLearner.inequalities[index];
  const footprint = new Set(failure.failureFootprint.map(point => point.join(",")));
  assert.ok(footprint.has(inequality.sourceGlobal.join(",")), "every marking witness must come from its failed-subtree footprint");
  for (const point of failure.failurePoints) assert.ok(footprint.has((typeof point === "string" ? point : point.join(","))), "every terminal obstruction belongs to the memoized footprint");
  for (const placement of failure.failedBranch) for (const entry of placement.occupancy.values()) assert.ok(footprint.has(entry.point.join(",")), "the certificate retains the full exhausted branch");
  assert.ok(failure.frontier.length > 0, "the learned inequality must attach to the branch interface");
}
const witnessedSites = new Set(recoveredLearner.inequalities.flatMap(inequality => [inequality.left, inequality.right]));
assert.ok([...recoveredLearner.support.keys()].every(key => witnessedSites.has(key)), "no marking-domain site may be allocated without a failed-branch witness");
assert.ok(recoveredUpdates.every(update => update.subtreeSites > 0 && update.frontierTiles > 0), "the UI audit must expose footprint and frontier provenance");
const allocatedChannels = new Map();
for (const mark of recovered.stats.support) {
  const key = `${mark.tile}:${mark.point.join(",")}`;
  if (!allocatedChannels.has(key)) allocatedChannels.set(key, new Set());
  allocatedChannels.get(key).add(mark.component);
}
assert.ok([...allocatedChannels.values()].some(channels => channels.size < 3), "the three channel domains must be allocated independently");

const recoveredSelection = await selectA2FrozenMarking({
  learner: recoveredLearner,
  validationSeeds: [2, 5],
  validationNodeLimit: 1200,
  solveOptions: {
    boundary: makeHexBoundary(50), seed: { loop: fixedSeed.loop },
    tiles: ["turtle"], maximize: true, targetPlacements: 30,
    learningWarmupDepth: 10, markingStagnationNodes: 400
  }
});
const frozenLearned = recoveredSelection.marking;
assert.ok(frozenLearned.metadata.learnedRevisions > 0 && frozenLearned.metadata.learnedRevisions <= recovered.stats.revision, "fresh validation should retain a learned Turtle revision");
const [naiveReplay, learnedReplay] = await Promise.all([
  solveA2Tiling({ boundary: makeHexBoundary(50), seed: { loop: fixedSeed.loop }, tiles: ["turtle"], maximize: true, targetPlacements: 30, nodeLimit: 3000, marking: new NoA2Marking(), randomSeed: 2 }),
  solveA2Tiling({ boundary: makeHexBoundary(50), seed: { loop: fixedSeed.loop }, tiles: ["turtle"], maximize: true, targetPlacements: 30, nodeLimit: 3000, marking: frozenLearned, randomSeed: 2 })
]);
assert.equal(naiveReplay.result, "yes");
assert.equal(learnedReplay.result, "yes", "the frozen learned marking must support a fresh tiling run");
assert.ok(learnedReplay.stats.nodes < naiveReplay.stats.nodes, `the learned marking must accelerate fresh search (${learnedReplay.stats.nodes} < ${naiveReplay.stats.nodes})`);

const appSource = readFileSync(new URL("../apps/a2-online-tiler/app.js", import.meta.url), "utf8");
const certifiedBoundary = JSON.parse(appSource.match(/const CERTIFIED_TURTLE_BOUNDARY = (\[.*?\]);/s)[1]);
const certifiedPlacements = JSON.parse(appSource.match(/const CERTIFIED_TURTLE_PLACEMENTS = (\[.*?\]);/s)[1]);
assert.equal(certifiedBoundary.length, 170);
assert.equal(certifiedPlacements.length, 101);
const certified = await solveA2Tiling({
  boundary: certifiedBoundary,
  tiles: ["turtle"],
  preferredPlacements: certifiedPlacements,
  nodeLimit: 200,
  marking: new OnlineA2Marking({ maxWitnessTrials: 64, yieldEvery: 8 })
});
assert.equal(certified.result, "yes", "the default promising region must replay its 101-Turtle certificate");
assert.equal(certified.placements.length, 101);
assert.equal(certified.stats.backtracks, 0);

const learned = await solveA2Tiling({
  boundary: makeHexBoundary(20),
  seed: { loop: A2_TILE_LOOPS.hexagon },
  tiles: ["hat", "turtle"],
  maximize: true,
  nodeLimit: 60,
  learningWarmupDepth: 0,
  maxMarkingRevisions: 6
});
assert.ok(learned.placements.length > 0, "growth mode keeps its best live patch");
assert.ok(learned.stats.revision > 0, "exhausted growth branches revise the marking");
assert.ok(learned.stats.supportSites >= learned.stats.revision, "the flexible support grows with learning");

console.log("A2 online tiler checks passed", learned.stats);
