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
starts with empty support and retains every exhausted branch in a permanent
ledger. A transactional update may commit only when every earlier encoded
failure remains rejected and every protected prefix still replays. Unresolved
certificates remain pending instead of being discarded. The live metrics report
observed, encoded, and pending failures alongside support size and mismatch
prunes. The engine integration is regression-tested, but a 3D search speedup is
not yet claimed. See
[`docs/projects/gcts-offline-online-learning.md`](../../docs/projects/gcts-offline-online-learning.md)
for the proof and cutoff semantics.
