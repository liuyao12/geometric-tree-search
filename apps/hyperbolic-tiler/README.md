# Hyperbolic Tiling Lab

A browser-only visual experiment in the `geometric-tree-search` project.

Live app: https://liuyao12.github.io/geometric-tree-search/apps/hyperbolic-tiler/

Direct search: https://liuyao12.github.io/geometric-tree-search/apps/hyperbolic-tiler/?mode=search&m=2&seed=1&radius=1.8

## Two deliberately different experiments

- **Known tiling** displays a finite window of the explicit infinite tiling. Its animation reveals the construction; it is not tree search.
- **Live search** uses genuine depth-first geometric search from a single seed tile. Trial placements, immediate rejections, accepted placements, exhausted subtrees, and removal of earlier placements are separate visible events. The construction formula is not used by `Search`.

Choose a Poincare disk, upper-half-plane, or Klein view; drag to pan by a hyperbolic isometry; use the wheel to change display scale. Play/Pause, Step, Reset, search seed, target radius, optional symbolic angle pruning, a search-tree display, an event log, and JSON patch/trace exports are included. The trace contains every event, not just the recent events shown in the log.

The app is static and has no remote runtime dependencies. Serve this directory with any static server, or open `index.html` in a browser that allows local scripts. `standalone.html` in the downloadable distribution inlines its assets; it need not be committed to the repository.

## Exact prototiles and construction

Use curvature -1, with metric `(dx^2 + dy^2)/y^2` in the upper half-plane. For `m = 2, 3, 4`, the vertices of `P_m` in cyclic order are

```
(0,1), (1,1), ..., (m,1), (m,m), (0,m).
```

All sides are **geodesic segments**, not horocycle segments. The lower m edges and the upper edge have common hyperbolic length `2 asinh(1/2)`; the two lateral edges have length `log(m)`. The prototile is convex and has reflection symmetry. It has m+3 sides.

The explicit tiling consists of the isometric copies

```
z -> m^k (z + m*j),  k,j in Z.
```

Adjacent tiles in one row meet along the lateral sides. The upper side of each tile coincides with one of the m lower sides in the next row. The bounding geodesics partition the strips between successive piecewise-geodesic row boundaries; their heights tend to zero and infinity in the two directions. This gives coverage of the whole upper half-plane without positive-area overlaps.

The m=2 pentagon is a concrete coordinate instance of the convex modification of the Boroczky binary construction. The m=3 hexagon and m=4 heptagon are **derived generalizations**, not asserted to be specific examples from Margulis and Mozes's paper.

### Angles and weak aperiodicity

Let `alpha = atan(1/2)`. The bottom end corners have angle `a = pi/2-alpha`, intermediate bottom corners have `b = pi-2alpha`, and the two top corners have `c = pi/2+alpha`. Thus

```
area(P_m) = 2(m-1) alpha.
```

The number `alpha/pi` is irrational: `exp(2i alpha) = (3+4i)/5` is not one of the roots of unity in Q(i). A complete vertex must therefore contain exactly one of the corner multisets `a+a+c+c` or `b+c+c`. The optional angle test checks whether each current multiset can extend to either one; it is a necessary local condition, not a sufficient extension test.

The irrational area/pi ratio rules out tilings with a cocompact symmetry group: a torsion-free orientation-preserving finite-index subgroup would give a closed hyperbolic surface of area `4 pi (g-1)` tiled by a finite number of copies. The explicit tiling nevertheless has the infinite-order symmetry `z -> mz`. This is **weak aperiodicity**, not strong aperiodicity.

## Search algorithm and its scope

1. Start from a single tile containing the disk origin.
2. Recompute exposed whole sides. Select the side whose Klein segment is closest to the origin among the sides meeting the open target disk.
3. Match each equal-length prototile side in reversed boundary direction by a Poincare-disk Mobius isometry. Deduplicate coincident placements. These presets are reflection-symmetric, so orientation-preserving copies already include reflected shapes.
4. Test positive-area overlap using separating axes of the convex Klein polygons; reject non-edge-to-edge contacts (T-junctions). Optionally apply the symbolic vertex-angle test.
5. Accept a legal candidate, recurse, and actually remove it when its subtree is exhausted. Candidate order is a deterministic seeded shuffle.
6. Stop successfully when no exposed side meets the open target disk. Since the origin lies in the initial tile and all finite-union boundary components consist of exposed sides, the disk is then covered, to the stated numerical tolerances. Tiles may extend beyond the disk; there is no prescribed outer polygon.

**Limitations:** this is finite-region, edge-to-edge search in floating-point arithmetic. It is not a proof of infinite tilability, an exhaustive search of non-edge-to-edge tilings, or a formally checked certificate. Disk-coordinate vertex welding uses tolerance 1e-8; overlap uses a Klein separating-axis tolerance 1e-10. Numerical precision deteriorates near the ideal boundary, so search radius is limited to 3. A 600-tile safety limit is reported as a limit, not as a negative result. Animation stops at 50,000 recorded events rather than dropping any history.

Panning changes the viewpoint, not the computed patch. The finite construction window is not dynamically regenerated around a new camera center. Recenter restores the original view. Rendered geodesics are adaptively subdivided to subpixel accuracy; collision checks use the exact straight-segment representation in the Klein model (evaluated numerically).

The geometry engine is independent of the DOM. The `family()` function supplies the verified vertex data. A new non-family tile requires its own angle-feasibility rule (or no angle pruning), and a tile without reflection symmetry requires reflected candidate generation if reflections are allowed.

## Regression tests and a reproducible benchmark

```
node --test apps/hyperbolic-tiler/test.cjs
```

Thirteen tests cover side lengths, congruence, Klein convexity, non-overlap of the explicit construction, successful disk coverage, exact replay of the placement/removal stack, genuine backtracking, angle counts, overlap and T-junction rejection, deterministic seeds, and the safety-limit outcome.

Measured with seed 1 and target radius 1.8 (no wall-clock animation included):

| Tile | Angle pruning | Final tiles | Candidates tried | Immediate rejections | Backtracked placements |
| --- | --- | ---: | ---: | ---: | ---: |
| Binary pentagon | Off | 30 | 249 | 139 | 81 |
| Binary pentagon | On | 30 | 54 | 25 | 0 |
| Ternary hexagon | Off | 21 | 135 | 78 | 37 |
| Ternary hexagon | On | 21 | 36 | 16 | 0 |
| Quaternary heptagon | Off | 10 | 59 | 39 | 11 |
| Quaternary heptagon | On | 11 | 37 | 22 | 5 |

These are small reproducible experiments, not universal complexity claims. Pruning can alter the subsequent PRNG state and the found patch, even with the same initial seed. Different valid patches can cover the disk with different numbers of boundary tiles.

Browser smoke tests additionally checked all three models, actual DOM-controlled completion of the binary search, the displayed 81 backtracks, and responsive layout at 390px width. `browser-test.py` in the downloadable distribution requires Python Playwright and Chromium; it uses inline assets for an offline test.

## Sources and pending catalogue work

- N. Dolbilin and D. Frettloh, *Properties of Boroczky tilings in high-dimensional hyperbolic spaces*, arXiv:0705.0291. Figure 1 and the paragraph immediately following describe the geodesic convex modification. https://arxiv.org/abs/0705.0291
- G. A. Margulis and S. Mozes, *Aperiodic tilings of the hyperbolic plane by convex polygons*, Israel Journal of Mathematics 107 (1998), 319-325. https://doi.org/10.1007/BF02764015
- K. Ahara, S. Akiyama, H. Hayashi and K. Komatsu, *Strongly nonperiodic hyperbolic tilings using single vertex configuration*, Hiroshima Mathematical Journal 48 (2018), 133-140. This paper studies a Margulis-Mozes rhombus. https://doi.org/10.32917/hmj/1533088825

The exact vertex specifications of the additional Margulis-Mozes examples have not been verified for this implementation. They are **not** silently replaced with invented shapes. The present catalogue intentionally stops at the verified binary shape and the two explicitly derived variants above.
