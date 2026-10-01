# Ammann–Beenker point-marking search

Live page: [Ammann–Beenker](https://liuyao12.github.io/geometric-tree-search/apps/penrose-model-set/ammann-beenker.html).
Added as the third cyclotomic tiling page on 2026-10-01.

## Algebra and inventory

The field is \(K=\mathbb Q(\zeta_8)=\mathbb Q(i,\sqrt2)\), where
\(\zeta_8=e^{\pi i/4}\). Coordinates use the independent integral basis
\(1,\zeta_8,\zeta_8^2,\zeta_8^3\) and relation \(\zeta_8^4=-1\).
The ring \(\mathbb Z[i,\sqrt2]\) is a proper subring of
\(\mathbb Z[\zeta_8]\); the corresponding fields are equal. The real
subfield is \(\mathbb Q(\sqrt2)\), and the inflation factor is
\(1+\sqrt2\). The star map is \(\zeta_8\mapsto\zeta_8^3\).
The octagonal window construction explains the geometry but is not a
proposal oracle or a restriction in this search.

There are unit squares and unit rhombs of acute angle \(\pi/4\).
The complete unmarked catalog has \(6\) oriented geometries. Rotations
are multiples of \(\pi/4\); both reflected rhomb decorations are included.
Each transformed decorated placement can occur at most once. Selected tile
shapes are allowed rather than required.

The positive-support domain is \(\tfrac12\mathbb Z[\zeta_8]\), with
translations in \(\mathbb Z[\zeta_8]\). Doubled coordinates are integer
vectors and overflow raises an error. This is a discrete coordinate domain
in four dimensions, dense under its physical embedding. Each rhomb has
corner weights \((1,3,1,3)\), each square \((2,2,2,2)\), and each edge
midpoint weight \(4\), all over capacity \(8\). Exact parity checks
exclude alignments requiring half-integral translations.

## Supplied markings

The implementation transcribes the edge arrows and shaded vertex pieces
in Tatham's Figure 36, including both reflected rhombs. At a common vertex,
pieces must form one of the rotations of the complete house shown in
Figure 14. This is the combined edge/vertex rule described by Grimm.
The edge-only comparison is weaker: for example, a periodic grid of squares
with all horizontal arrows rightward and vertical arrows upward satisfies it.

A house is represented, at an arbitrary drawing scale, by the polygon

\[
(\sqrt2,0),(0,\sqrt2),(-\sqrt2,0),(-1,0),(-1,-1),(1,-1),(1,0).
\]

In successive open sectors of angle \(\pi/4\), its outer boundary has
unit outward normals indexed by \((1,1,3,3,4,6,6,0)\). These integer
indices encode the polygon pieces exactly; no floating-point geometry is
used to classify a fragment. A rhomb with vertices
\((0,1,1+\zeta_8,\zeta_8)\) has sector-normal words
\((0),(1,3,4),(5),(5,6,0)\). The reflected decoration changes the acute
words to \((1)\) and \((4)\). For the square with vertices
\((0,1,1+i,i)\), the words are \((0,2),(2,4),(4,6),(6,0)\).

Every completion orientation compatible with a piece is represented.
This replaces the existential choice of a full house by explicit finite
marking variants: \(904\) oriented templates in full mode, versus
\(12\) with edge arrows only. These variants are not new geometric shapes.
A marking has an edge channel at each midpoint and a house channel at each
vertex. The edge value is its absolute direction index; the house value
is its rotation from the displayed reference house. Overlapping assigned
values must agree. Assigned zero is distinct from an absent channel.

Under rotation by \(r\pi/4\), both values increase by \(r\) modulo
\(8\). Reflection across the real axis sends an edge value \(e\) to
\(-e\), and a house value \(h\) to \(4-h\), modulo \(8\).
Translations preserve values. Tests verify catalog closure under rotation
and reflection.

These are published problem-defining markings. They are not learned data,
a discovery of the arrows, or a result of the pair-corona training protocol.
The UI draws the complete house chosen at each vertex, including unfinished
boundary vertices. It also permits inspection of the exact point and values.

## Search contract and limitations

The engine uses the shared complete point–candidate graph, with every
selected orientation and positive-support alignment enumerated. Candidate
records retain the contribution weights. Selection follows global degree
zero, global degree one, then earliest generation; minimum degree breaks
generation ties only. Tile generations and point generations follow the
master reference and roll back with placements.

GCTS maintains the global marking field with reference counts and removes
conflicting candidates at every incident frontier point. All marking
support and corner dependencies are within the corresponding tile footprint,
so the shared spatial dependency index is sufficient for this adapter.

An additional exact finite relaxation fills the unoccupied sectors at a
candidate's corners using the complete selected decorated corner palette,
conditioned on the shared house value and radial edge directions. Failure
is a proved local obstruction; success is not proof of global extension.
This constraint prunes through the graph. Its bounded cache survives
rollback, is scoped to the fixed catalog, and resets on every new run.
It is not a trained marking. The baseline uses the same point model,
marking catalog, scheduler and ordering, with pairwise marking checks and
without corner-completion propagation.

All active placements, point totals, marking references, generations and
graph changes roll back exactly. A failed child is excluded only in its
parent context. Optional diagnostic tracing detects repeated decorated
attempts in an identical parent state; it is disabled in the browser to
avoid retaining an unbounded trace.

The default seed is the first oriented rhomb with the house choices
\((5,3,2,2)\). This is an explicitly fixed decorated root, not an exhaustive
search over all possible root decorations. The UI seed input changes only
candidate ordering. No window or substitution construction supplies moves.
When that rhomb is not selected, the first selected template is used.
Exhaustion applies to this fixed seeded problem, not the unrestricted tile set.

Only exposed support is activated; no fair coverage of the whole infinite
module is claimed. Milestones pause only with no known dead frontier point,
and preserve the search stack. A budget stop is unknown. Polygon separation
and edge-to-edge checks are supplemental numerical geometric controls with
absolute tolerance \(10^{-9}\). Exact coordinate and marking arithmetic
does not turn these controls into a certified geometric solver.

## Verification

`tests/fixtures/ammann-beenker-star.json` records the eight-rhomb example
from Tatham's Figure 14. The sector normals were independently extracted
from the PDF's shaded vector paths, rather than generated by this catalog.
Every decorated tile must occur in the catalog; all full and partial stars
must pass matching and completion. This checks the delicate reflection and
vertex-piece transcription against a separate published example.

`tests/test_ammann_beenker.mjs` additionally checks cyclotomic arithmetic,
complete support alignments and parity, candidate uniqueness, scheduling,
budget semantics, incremental domains against fresh enumeration, exact
rollback including the marking field, and independent polygon-clipping
replay of a grown patch. The default full-rule run reaches \(80\) tiles
in \(451\) proposals, with \(372\) backtracks and \(198\) forced moves;
no decorated attempt repeats in the same parent. A continuation run reached
\(100\) tiles in \(604\) proposals. These are deterministic finite-growth
regressions for one seed, not speedup or infinite-extension certificates.

## Sources

- Jagannathan and Duneau, [Properties of the Ammann–Beenker tiling and its
  square periodic approximants](https://arxiv.org/html/2308.07701v2),
  Sections 2.1–2.3, for projection, the internal plane and silver inflation.
- Tatham, [Finite-state transducers for substitution tilings](https://arxiv.org/abs/2512.16595),
  version 2, Figures 14 and 36, for the complete edge/house decorations.
- Grimm, [A Program Package for Aperiodic Tilings](https://www.iucr.org/__data/assets/pdf_file/0006/6378/iucrcompcomm_jan2005.pdf),
  IUCr Computing Commission Newsletter 5 (2005), pages 10–15, for the
  combined edge/vertex rule and its aperiodic role.
