# Structural lane contract (2026-09-07)

Discovery and expansion are separate. Neither a tile-count target nor a shell
target bounds discovery. After a certificate, both lanes enumerate its translated
orbit until the display criterion is met. A clock/node/safety stop is not a
negative certificate. In the comparison workers clock pauses preserve the live
generator, including exact domain, candidate rows, remaining weights and DFS stack.

## Exact supported model

One polycube on Z³, FCC or the refined half-grid (scaled unit-cell exact cover), or one integer-weight Z³
lattice function (exact weighted cover, with distinct allowed placements). The
orientation list is preprocessed by the existing lattice symmetry code. No tile
IDs or catalogue certificates inform domain enumeration.

Translational enumerates determinants 1,2,…, every column HNF at each determinant,
and every rooted cover of each quotient. Each fixed-domain tree is finite, with
no per-domain cutoff. A pause does not skip the rest of that tree. Determinants
incompatible with tile mass are omitted by exact arithmetic. For refined polycube
lattices, both period bases and placement residues must belong to the configured
translation lattice. This is systematic
but can be much slower than a heuristic certificate finder.

For Isohedral let S be the allowed tile-transitive symmetry group and T its
translation subgroup. The linear-part map embeds S/T into the allowed finite
point group H. Thus there are at most |H| tile orbits modulo T (indeed no more
than [S:T]). T has full rank because finitely many bounded tile representatives
and a lower-rank translation subgroup cannot cover Z³. Its index D therefore
satisfies D·capacity = m·tile_mass, with m ≤ |H|. Enumerating all these HNFs and
all their covers is a finite decision procedure. Each cover must additionally
pass the root-to-every-tile, whole-quotient symmetry test. A failed symmetry test
does NOT discard the other covers of that HNF. A₂ matrices must preserve the
layer foliation; the bound is six (proper) or twelve (with reflections), not an
assumption that the tile lacks stabilizers.

Background: the point group is the quotient by translations, as described in
the [GAP crystallographic-group manual](https://www.math.rwth-aachen.de/~GAP/WWW2/Gap3/Manual3/C060S001.htm).
The finite motif bound above is the application to this fixed lattice action.

`no_isohedral_tiling` has `can_tile_isohedrally: false` but `can_tile: null`.
It must never become a claim that no tiling of any kind exists.

## Explicit limitation

Mixed systems and the older floating/irrational
geometric representations still use a one-sided geometric certificate search.
That fallback revisits growing search limits and never issues a negative
isohedral decision. It is not covered by the exact completeness theorem above.
Extending the exact decider to those representations remains necessary before
claiming complete isohedral decisions for the entire catalogue.

Tests: `node scripts/test-structural-domain-search.mjs` exercises HNF counts,
quotient arithmetic, finite exhaustion, unbounded continuation, count and shell
expansion in both lanes, and the former premature Translational goal stop.
