# Penrose tiling with marking controls

Published app: <https://liuyao12.github.io/geometric-tree-search/penrose-model-set/>.
Use GitHub Pages for previews and publication.

The main demo uses one canvas and one live search worker, following the control
layout of `GCTS-I.html`. Start/Pause, Step and Reset control genuine DFS growth
in ℤ[ζ₅]. The **Tiling with marking** checkbox controls whether marking
constraints are enforced. Changing it, the direction count, seed, target or
budget restarts the search from the same seed and pauses. Show/Hide marking,
color by direction and line weight only change rendering.

Marking settings allow 1, 3 or all 5 direction families. The partial settings
use the first families in the fixed cyclotomic frame and are weaker diagnostic
rules, not the full Ammann rule. Every tile retains its complete five-stripe
prototile decoration; unenforced directions are gray. All five is the default
when enabling enforcement. Direction channels are distinct from coordinate
lattice rank. Hiding stripes never disables enforcement.

Geometry always checks exact non-overlap, corner capacity and a single simple
outer boundary. There is no window oracle or precomputed target tiling.
Unmarked rhombs allow more tilings, including periodic ones; adding constraints
does not guarantee a faster search. A finite patch or budget stop is not a
proof about infinite tileability. Worker compute time excludes playback delay
and rendering.

`reference.html` preserves the window-certified P1/P2/P3 catalog and fixed
marking reference, powered by the existing `app.js`.

Validation from the repository root:

```sh
node scripts/test-penrose-marking-settings.mjs
node scripts/test-penrose-demo-controls.mjs
node scripts/test-penrose-growth.mjs
node scripts/test-penrose-growth-worker.mjs
node scripts/test-penrose-ammann.mjs
```

The controller test uses a DOM/worker transport double, without a local browser
preview. The worker integration test loads the actual worker module.
