# Knots as Reidemeister tiles: GCTS + RL research plan

> **Research target:** classify exact cubic-lattice knots using lattice realizations of Reidemeister tiles and generic brute force helped by online GCTS. The viewer is only a certificate presentation tool. See the [current lattice classifier subgoals](lattice-classifier.html). A validated reference corpus now covers 2,977 prime types through 12 crossings plus the unknot; classification and local lattice tile integration are not yet implemented. The diagram pilot below is a separate control.

> Current viewer: the search now uses **brute force + online GCTS**, with no knot-specific search hints. See the [online search contract](online-search.html). The implementation below documents the earlier specialized control, retained as `solveSpecialized`; its offline seam learner, coloring shortcut, and RL policy are not used by the current viewer.

The search object is a movie assembled from **Reidemeister-move tiles**. Input
knots are piecewise-linear embedded circles with edges parallel to coordinate
axes. Their diagrams come from projecting the lattice embedding; the extra
coordinate records time. A successful tile sequence is a certificate of
ambient isotopy. The objective is either equivalence to a second knot or
equivalence to the unknot.

The first executable pilot is the [Reidemeister Tile Lab](../../apps/knot-movie/).
It searches exact signed planar diagrams using all three move types, including
expansions. It implements whole-diagram seam markings, a cold RL proposal
control, rational-direction source projections, and independently replayable
certificates. It is a foundation for the local tile system, not a completed
general knot classifier or a geometric animation of every frame.

## 1. Resolve the tile geometry

The proposed geometries are compatible:

\[
C=[0,1]^3\times[0,1]\subset\mathbb R^3\times\mathbb R
\]

is a four-dimensional space-time cube. With the spatial projection

\[
\pi(x,y,z)=\left(\frac{x-y}{\sqrt2},
\frac{x+y-2z}{\sqrt6}\right),
\]

the image of a spatial unit cube is a regular hexagon, and
\((\pi,\mathrm{id})(C)\) is a three-dimensional hexagonal prism. The
projected coordinate directions are three directions at equal angles.

**Recommended architecture:** author and display Reidemeister tiles in
diagram space-time as hexagonal cylinders; retain rectilinear spatial lifts
and four-dimensional verification cells as certificate data. One move may
occupy a block of cells. A cube or cylinder is a support container; a
Reidemeister tile is the decorated local transition carried by that support.
Do not require every move to fit one unit cube.

Different spatial cubes can project onto overlapping hexagons. Projection
forgets depth and is not an injective identification of cells. Depth labels,
strand identities, and unchanged exterior collars must survive projection.
An arbitrary tiling of cylinders is not automatically a valid knot movie.

The spatial history of a knot is a swept annulus in space-time. It must come
from embeddings at every time. An arbitrary embedded annulus connecting two
knots in four dimensions gives **concordance**, which is weaker than isotopy.
Births, deaths, saddles, strand passages, cutting and reconnection are excluded.
See [Livingston's survey](https://arxiv.org/abs/math/0307077).

## 2. Subgoals, dependencies, and acceptance gates

| Subgoal | Work and concrete deliverable | Acceptance gate | Current status |
| --- | --- | --- | --- |
| A. Knot contract | Single component, unoriented knots; preserve chirality; exact lattice coordinates; validated signed planar diagrams | Reject self-intersections, invalid crossing decorations and nonplanar signed words; cyclic/relabelled/reversed words agree; mirror trefoils remain distinct keys | Implemented for bounded inputs; multiple links and oriented equivalence deferred |
| B. Reidemeister inventory | Types I and II in both directions; type III; identity tiles for stationary time slots | Local disk tests, inverse replay, sign/overpass preservation, complete variant tests and external oracle comparison | All types implemented and exercised; broader external comparison remains |
| C. Bounded point solver | A faithful finite diagram-seam reduction; full candidate incidence; global dead/forced checks; generation-first scheduling; rollback | Same answers as independent exhaustive path recursion; budget stops remain unknown; frozen rules and repeatable rollback | Small exact pilot implemented with full graph reconstruction |
| D. Exact failure learning | Exhaustive suffix labels; compile failures to ordinary point-marking mismatches; retain proof context | Every rejected seam has no completion under its exact bounds; same bounded solutions with and without guards | Specialized backward-reachability control implemented |
| E. RL cluster proposals | Cold learning, composable move sequences, inspectable base expansion, complete fallback | Replay every proposal; no policy removes base candidates; include training/validation cost in comparisons | Small tabular Q control implemented; general learned cluster library deferred |
| F. Local hexagonal model | Diagram patches, side collars, strand ports, crossing/depth channels, stationary tiles, refinement templates | Prove faithful correspondence between point-value tilings and legal movies; no accidental strand births or reconnections | Next research step; depends on A–C |
| G. Local GCTS synthesis | Learn sparse local point values from unmarked extension tests; allow individually absent components | Full resolved pair/cluster catalog replay; explicit proof scopes; no timeout promoted to negative | Planned; depends on F |
| H. Geometric movies | Faithful planar layout; rectilinear lifts; collision-free realization of each move; projected playback | Independent space-time replay; every intermediate knot embedded; diagram events match the declared tile | Source projection implemented; full-frame realization and interpolation deferred |
| I. Classification and scaling | Invariant filters, expanding positive search, classical negative certificates, benchmark corpus | Positive movie or independently verified negative proof; unresolved instances stay unknown; fair total-cost comparisons | Fox coloring obstruction implemented; complete decision procedure deferred |

Prioritize **F**, then **H**, then **G**. Whole-state seams already give a sound
control, but meaningful GCTS research requires a local interface that transfers
between different diagrams. A larger policy model should wait until that
interface and the movie verifier are stable.

## 3. Exact representation and primitive moves

Each input crossing has an identifier, an over/under flag, and an oriented
crossing sign. The knot traversal gives a signed Gauss word. The sign convention
is the sign of the determinant of the projected over-strand tangent followed
by the under-strand tangent. This is consistent across the projector and the
diagram engine; the label convention itself does not affect equivalence.

Construct a ribbon graph using incoming/outgoing half-edges at every crossing.
The cyclic rotation at a crossing is determined by its sign. Require the Euler
characteristic of the associated connected surface to be that of the sphere.
This rejects signed words representing higher-genus virtual diagrams.

The current local disk checks are:

- Type I deletes a monogon, or inserts its inverse on any edge interval.
- Type II deletes an empty bigon whose two strands have consistent over/under
  roles and opposite crossing signs. Insertion enumerates interval pairs,
  sign and strand-order variants, including both orders at a shared cyclic gap,
  and verifies the new crossings bound a cancellable bigon.
- Type III flips the three sides of an empty triangular face. The three
  strands must have consistent top/middle/bottom order. Cyclic over/under
  triangles are rejected. Crossing signs and overpass identities persist.
- An identity tile holds a diagram between time slots; it is stationary filler,
  not a Reidemeister move or a counted move in the exported certificate.

Canonicalization permits relabelling crossings, cyclic shifts and reversal of
the entire knot traversal. It does not quotient by reflection. Equivalent
candidate outcomes are deduplicated only as complete signed diagram states;
the exported move is independently replayed from its canonical input.

No edge-length reduction or crossing reduction is used as a legality rule.
Expansions remain available. This matters for diagrams that must become more
complex before they simplify.

## 4. Current point-value reduction and its precise scope

For a horizon \(H\), crossing cap \(C\), source \(D_0\), and target
\(D_H\), enumerate every reachable signed diagram at each layer, with every
allowed Reidemeister transition and identity hold. Stop with **unknown** if
catalog construction exceeds its state budget. A partial catalog cannot support
dead or forced conclusions.

The required point domain is

\[
Q=\{q_0,\ldots,q_{H-1}\}.
\]

A transition placement \(c=(i,D,D')\) has the exact point function

\[
t_c(q_j)=\begin{cases}1&j=i,\\0&j\ne i.\end{cases}
\]

It assigns marking values on two additional seam points:

\[
m_c(s_i)=\operatorname{key}(D),\qquad
m_c(s_{i+1})=\operatorname{key}(D').
\]

The fixed exterior marking assigns the source and target at the endpoint seams.
Exact coverage selects one tile per slot; equality at shared seam points joins
the transitions into a movie. Seam points are marking-only points, and their
dependencies are checked even though they are outside the coverage frontier.
The placement universe and transforms are finite and explicitly authored; the
only placement transform here is identity. This is an exact finite point model,
not a claim that every local geometrical hexagonal tiling has been encoded.

Every required slot is an activated root obligation with generation zero.
Global degree-zero checks precede every singleton placement, and singleton
propagation precedes branching. All generations are equal in this reduction,
so minimum degree is a permitted tie-breaker. The present implementation
reconstructs the entire forward/reverse incidence graph and marking state from
an immutable selected-placement list. Rollback is exact; incremental indexing
and nontrivial generation propagation are future work.

The whole knot must not be replaced by an isolated local arc when constructing
a failure key. An exterior tangle can change whether a local simplification
extends to the target. Include the boundary context in every future local rule.

## 5. Failure markings: implemented control and intended GCTS

The pilot starts with no learned guards. Exhaustive backward reachability on
the complete layered transition graph labels each diagram seam by whether it
can reach the target in its remaining horizon under the crossing cap.
Terminal failure means the target boundary does not match; earlier failure
requires every outgoing transition to lead to a failed suffix.

For a proved failed state \(D\) at time \(i\), introduce a marking-only
guard point \(f_{i,D}\). The exterior assigns

\[
m_{\mathrm{ext}}(f_{i,D})=0,
\]

and every transition ending at that seam assigns

\[
m_c(f_{i,D})=1.
\]

The ordinary marking-agreement test removes those candidates from the shared
point graph. There is no runtime failure-clause scanner replacing the marking
comparison. Guards are frozen before marked search. Scope includes target,
horizon, crossing cap, candidate rules and version. They are redundant for
that exact finite problem; they say nothing about larger caps or horizons.
The guard proof DAG records failed states and outgoing candidate identities.
No learned assignments are bundled into source files or silently reused.

**This is a specialized global seam control, analogous to finite-state dynamic
programming.** It is not the master contract's local neighboring-pair marking
synthesis protocol, and no runtime advantage is claimed. Full backward labeling
already resolves finite reachability; this pilot tests its encoding as genuine
point values and supplies a correctness baseline.

The next learner should enumerate neighboring Reidemeister tiles and larger
boundary-collared patches; label them using unmarked bounded extension search;
synthesize sparse equality/mismatch channels after each resolved result; permit
individual absent values; replay the full resolved catalog; and activate a
frozen marking with explicit scope. A local rule supported only by samples is
a hypothesis and may guide ordering, but must not certify inequivalence.

## 6. RL proposals and evaluation

The current policy is cold tabular Q-learning with a small state feature:
crossing count and move type. Training starts from random legal scrambles of
the unknot, with all allowed move types available. Reaching the unknot rewards
the trajectory. The policy composes up to three moves; each proposal has a
base expansion and is replayed before supplying candidate-order preferences.
The aggregate point contributions and union of markings must also agree with
the live graph, including fixed failure guards and any already selected shared
placement. Proposals never change candidate degrees or bypass global propagation.

This is intentionally weak and is not a learned knot classifier. The current
examples are correctness controls, not a held-out evaluation corpus. Failure
labels use all resolved states of the current finite catalog; that learning
protocol is distinct from RL policy evaluation.

Next, train a policy on boundary-decorated ribbon-graph observations and
variable-length tile clusters, including irregular patches and temporary
expansions. Export transformations, base expansions, boundary ports, marking
versions and training provenance. Split RL evaluation by underlying knot and
scrambling generator, not just by rendering or crossing names. Permit arbitrary
legal cluster composition rather than a fixed untangling strategy vocabulary.

Compare the unmarked point solver, exact marking lane, marking-plus-RL lane,
direct graph reachability and classical knot tools on identical inputs and
bounds. Include candidate catalog construction, failure labeling, training,
proposal construction and validation, certificate verification, and peak
memory. Current timings include the first five compute stages and JS replay,
but do not yet measure memory or separate independent Python verification time.
Do not infer a speedup from more removed candidates. The small controls show
no branch reduction; RL training adds overhead.

## 7. Lattice input, projection, and the movie

The importer accepts an array of integer spatial vertices, or an object with
`vertices`. Consecutive vertices must differ along exactly one coordinate axis.
Long edges are expanded to unit edges, and repeated unit vertices are rejected.
For unit cubic-lattice edges, any intersection occurs at a lattice vertex, so
this certifies an embedded single closed polygon.

The source projector first attempts the exact body diagonal. Degenerate
overlaps, endpoint crossings and multiple crossings trigger a small rational
direction perturbation. Integer determinants classify crossings; rational
depth comparison determines the overpass. Arbitrary-precision rational comparisons
order the crossing events. Floating point is used only for display coordinates.
Coordinate
and length limits keep the integer operations inside exact safe-integer range;
coincident crossing checks use arbitrary-precision integers.

The browser shows the faithful source projection and a **schematic signed
ribbon graph** for each verified movie seam. The ribbon layout is not a planar
knot drawing: only the numbered crossing disks are knot crossings. Smooth
geometric untangling and removal of incidental projection crossings remain
subgoal H. Do not interpolate arbitrary vertex lists between frames and call
that a certified isotopy.

For H, require each local Reidemeister tile to carry a regular planar patch and
an axis-aligned spatial lift, plus a collision-free piecewise-linear isotopy.
Subdivide space-time as needed. Match unchanged lateral collars and depths.
Projection perturbations and planar rearrangements are recorded display
operations; a strand passage cannot be disguised as moving away a crossing.

## 8. Classification semantics

There are three global outcomes:

1. **Equivalent:** a verified Reidemeister movie reaches the exact target
   signed diagram, including an empty target diagram for the unknot.
2. **Inequivalent:** an independently justifiable invariant or stronger negative
   certificate differs. The pilot computes the dimension of Fox colorings over
   \(\mathbb F_3\), using
   \(2x_{\mathrm{over}}-x_{\mathrm{in}}-x_{\mathrm{out}}=0\).
   Different dimensions distinguish the trefoil from the unknot; equal
   dimensions do not establish equivalence or identify a knot.
3. **Unknown:** unresolved bounds, resource exhaustion or equal invariant values
   without a positive movie. Complete finite exhaustion is reported separately,
   but general knot equivalence remains unknown.

Fox-coloring background: [Knot Colorings: Coloring and Goeritz matrices](https://arxiv.org/abs/1910.08044).
Mirror knots remain separate inputs, although the pilot's coloring obstruction
does not distinguish mirror trefoils. A full classifier needs more invariants
and a classical certified negative lane, potentially normal-surface methods
and certified knot-complement comparisons. Expanding positive movie search
alone is a semidecision procedure and does not guarantee termination on
inequivalent pairs. None of the current finite bounds establishes general
completeness. BFACF lattice isotopies can serve as geometric comparison
controls, not replacements for the user's Reidemeister tiles; see
[Janse van Rensburg and Rechnitzer](https://arxiv.org/abs/1011.3847).

## 9. Reproduce and independently verify

From the repository root, using an installed Node runtime:

```sh
node tests/test_knot_movie.mjs
node scripts/benchmark-knot-movie.mjs --certificates=/tmp/knot-movies.json
python3 research/knot-classifier/verify_movie.py /tmp/knot-movies.json
```

Browser-exported JSON uses the same independent verifier. It reconstructs
ribbon faces and checks expansion tiles by inverse disk deletion, without
calling the JS move enumerator, candidate graph, policy or marking learner.
Certificate replay currently establishes diagram equivalence, not a full
spatial space-time mesh certificate.

Initial exhaustive smoke evidence: 223 reachable planar diagram keys; 688 move
checks, including 18 type-III transitions; inverse existence and Fox-coloring
preservation; tiny bounded searches agree with direct path recursion; every
learned failed seam independently exhausts at its remaining depth; corrupted
movies and nonplanar words are rejected; catalog/search budget checks return
unknown. These are finite tests, not a proof that the move implementation is
complete for arbitrary crossing counts.

## 10. Conformance record and open gaps

Read the [master contract](../../docs/basic-tiling-algorithm.md) before extending
this engine. The present finite reduction has exact integer point contributions,
assigned marking values including explicit zero, all required roots activated,
full point/candidate incidence, marking-only dependencies, global scheduler
ordering, immutable rollback, frozen guards, candidate fallback and certificate
replay. The browser and policy consume the same candidate engine.

Remaining gaps: local hexagonal point functions and faithful spatial reduction;
incremental dependencies and trails; nontrivial growth-generation tests;
fractional/shared-support tests for a future local engine; pair-marking synthesis
and activation gate; externally cross-checked move completeness; independent
negative-certificate export; full geometric movie playback; persistent proof
and cluster libraries; memory accounting; held-out RL benchmarks; an actual
complete classifier. Preserve the seam-control benchmark semantics while
developing that local engine.
