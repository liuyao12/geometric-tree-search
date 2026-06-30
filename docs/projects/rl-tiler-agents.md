# RL tiler agents

The interactive 3D tiler should stay responsive and human-directed. Expensive policy
searches, including RL training, should run offline against the headless engine and
then be surfaced later as selectable move-prediction agents in the app.

## View of the decision problem

A tiling step can be treated as a two-stage, almost two-dimensional prediction:

1. choose an active frontier point;
2. choose one legal candidate placement attached to that point.

The existing frontier/candidate graph already exposes this structure in the engine
messages and traces. A learned agent can score either frontier nodes, candidate
nodes, or frontier-candidate edges.

## Offline training / evaluation loop

Use the headless scripts rather than the browser UI:

```bash
node scripts/run-tiler-cli.mjs --figure cube::0 \
  --move-order coverage --branch-details --trace runs/cube-coverage.ndjson

node scripts/benchmark-tiler-policies.mjs --figures cube::0 \
  --policies coverage,isohedral,crystal,balanced \
  --target 80 --output runs/cube-policy-benchmark.json
```

The benchmark harness compares fixed policies under the same target, caps, and
lattice. Those policies are baselines for a learned/RL agent. A future training
script can consume branch-detail traces as demonstrations, or run the same engine
loop while replacing `move_order` with an agent-scored frontier/candidate edge.

## Browser integration target

Once agents exist, the app should expose a separate **Agent** selector, for example:

- built-in heuristic only;
- trained polycube agent;
- trained D3-polycube agent;
- user-supplied local/remote agent.

The app should request an agent suggestion only for the current frontier/candidate
graph and keep the fallback heuristics available when an agent is missing or slow.
