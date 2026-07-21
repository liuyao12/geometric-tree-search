# 3D Lattice Tiler

Standalone JavaScript port of the Observable notebook:

https://observablehq.com/@liuyao12/3d-lattice-tiler

Run from the repository root with any static server, for example:

```bash
python3 -m http.server 5174
```

Then open:

```text
http://127.0.0.1:5174/apps/3d-lattice-tiler/
```

The port keeps the notebook search engine in `engine.js` and moves the page UI and batched Three.js rendering into `app.js`.

The **Learn failure markings** control enables the online GCTS learner. It
starts empty and retains every exhausted branch as a translation-equivariant
geometric clause. Optional rank-local pair markings remain transactional: an
update may commit only when every earlier encoded failure remains rejected and
every protected prefix still replays. The live metrics report clauses,
observed/encoded failures, and geometric prunes.

The in-page **Growth curve** runs the same selected tiles and target three
times in a worker: naive DFS, complete geometric GCTS, and GCTS with exhaustive
online-agent ordering plus cluster/template proposals. It plots measured best
tile count against wall-clock time; it does not manufacture an expected
ordering. The headless 1-Cross regression currently reaches eight tiles in
roughly 9.2 s / 5.6 s / 0.6 s respectively when the three modes contend for the
same machine, but the chart intentionally remeasures the user's system. See
[`docs/projects/gcts-offline-online-learning.md`](../../docs/projects/gcts-offline-online-learning.md)
for the proof and cutoff semantics.
