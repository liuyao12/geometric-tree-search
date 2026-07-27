# GCTS for group presentations: search over diagrams and surfaces

## Executive answer

There are two related projects here, and it is important not to conflate them.

1. **The ordinary word problem searches for a disc.**  For a finite
   presentation

   \[
   P=\langle X\mid R\rangle
   \]

   and a word \(w\), van Kampen's lemma says that \(w=1\) in \(P\) exactly
   when there is a finite, simply connected polygonal diagram whose outside
   boundary reads \(w\), and whose faces read cyclic conjugates of elements of
   \(R^{\pm1}\).  The topology is fixed; what must be discovered is the
   combinatorial disc, including its internal identifications.

2. **Variable topology appears in the natural extensions.**  Annuli certify
   conjugacy.  A genus-\(g\) surface with one boundary component certifies that
   a word is a product of \(g\) commutators.  Closed surfaces map into the
   presentation complex when searching for surface subgroups.  Here the genus,
   number of boundary components, orientability, and decomposition into bands
   or pairs of pants are genuinely part of the search.

The proposed extension is therefore **Surface GCTS (S-GCTS)**: replace a tile
placement state by a partially paired collection of relator polygons, and
replace Euclidean coordinates by a combinatorial-map boundary state.  Learn a
grammar of useful bands, seams, and boundary types.  Every claimed solution is
checked independently as a finite combinatorial certificate.  Learned rules
may order the search freely, but may prune it only after being converted into
an exact lower bound or an exhaustively proved no-good.

This cannot solve the word problem for arbitrary finite presentations: the
uniform problem is undecidable.  The right claims are bounded completeness,
speed on selected decidable families, and discovery of independently
verifiable surface certificates.

## The geometric object

Treat each relator \(r=x_1\cdots x_k\) as an oriented \(k\)-gon.  Reversing the
orientation reads \(r^{-1}\).  Edges may be sewn only when their labels are
inverse and their orientations oppose.  The resulting object is a **map of a
polygonal surface into the presentation complex**, not necessarily an embedded
tiling in the plane.

A convenient exact representation uses darts (or oriented half-edges):

- a permutation \(\rho\) records cyclic order around each polygon;
- a partial involution \(\alpha\) pairs sewn darts;
- unpaired darts form the current frontier;
- labels in \(X^{\pm1}\) enforce legal sewing;
- cycles of the induced vertex and boundary permutations recover vertices and
  boundary components.

For a completed orientable map,

\[
\chi=V-E+F=2-2g-b,
\]

so genus \(g\) and boundary count \(b\) are computed rather than guessed from
a drawing.  A certificate contains the relator/orientation of every face and
the edge-pairing table.  A small verifier checks labels, incidences, boundary
words, connectedness, orientability, and Euler characteristic.

The search state should be

\[
S=(\partial S,\Pi_V,\rho_\partial,\chi,\mathcal B,\mathcal N),
\]

where \(\partial S\) is the labelled frontier, \(\Pi_V\) is the partial vertex
identification, \(\rho_\partial\) gives cyclic order on each boundary
component, \(\mathcal B\) records open bands/corridors, and \(\mathcal N\) is
the set of exact learned no-goods already applicable.  States are canonicalized
under renaming of internal vertices, cyclic shifts and inversions of relators,
presentation automorphisms supplied by the user, and permutation of
indistinguishable boundary components.

### Complete bounded moves

For a fixed face bound \(A\) and genus bound \(g\), a complete enumerator needs
more than the visually natural move "attach one face along one boundary arc."
Some diagrams cannot be exposed by a shelling that keeps every intermediate
state a disc.  Use a partial-pairing search with these primitive moves:

1. add an oriented relator polygon;
2. pair two compatible frontier darts, including darts already in the same
   component;
3. close a vertex when its incident cyclic order is determined;
4. freely reduce a boundary spur while retaining the corresponding certificate
   operation;
5. close the final boundary against the requested word.

Connectivity and topology are checked incrementally.  Disc-only search keeps
orientability, \(b=1\) at completion, and \(\chi=1\).  Allowing temporarily
several frontier components avoids an accidental shellability restriction.
Enumerating all face multisets and all compatible pairings is finite, hence
complete under the stated bounds, though of course expensive.

### GCTS moves and learned geometry

The useful search does not operate dart by dart all the time.  It learns or
mines macros such as:

- a **relator band**: a chain of faces carrying a generator from one frontier
  arc to another;
- a **corridor**: a maximal band forced by an HNN-extension letter;
- a **grid patch**: two transverse commuting bands;
- a **pair of pants**: one boundary component splitting into two;
- a **handle macro**: two labelled seams whose gluing lowers \(\chi\) by two;
- a **cap**: a repeatedly observed boundary type with an exact stored filling.

This is the surface analogue of a learned marking.  The learned object is not
primarily a section over a fixed geometry; it is an equivariant grammar or
cost-to-fill function on labelled frontier types.  A useful decomposition is

\[
\widehat C(S)=C_{\rm exact}(S)+C_{\rm learned}(S),
\]

where \(C_{\rm exact}\) contains admissible lower bounds (abelianized flow,
parity, curvature, corridor counts, and small exact frontier tables) and
\(C_{\rm learned}\) only orders equally legal branches.  A learned failure may
be promoted to a pruning rule only after exhaustive completion below explicit
area/genus/frontier-width bounds.

This preserves the strongest feature of GCTS: the final proof does not depend
on trusting the learner.

## Concrete benchmark ladder

### 0. Certificate and canonicalization tests

Use the following before any learning.

| Presentation | Input family | Known structure | What it tests |
| --- | --- | --- | --- |
| \(\langle a\mid a^q\rangle\) | \(a^{kq}\) | chain of \(q\)-gons | orientation, repeated faces |
| \(\langle a,b\mid aba^{-1}b^{-1}\rangle\cong\mathbb Z^2\) | \(a^m b^n a^{-m}b^{-n}\) | \(m\times n\) grid, area \(mn\) | pairing, symmetry, exact area |
| genus-two surface group \(\langle a,b,c,d\mid[a,b][c,d]\rangle\) | conjugates/products of the relator | sewn octagons | nontrivial cyclic order |

For every positive instance, store the construction history and independently
verify the resulting pairing table.  Produce negative instances certified by
abelianization or a small finite quotient, rather than merely by a timeout.

**Pass criterion:** reproduce the rectangular \(\mathbb Z^2\) minimum areas
through at least \(m,n\leq 8\), with identical canonical keys for randomly
renamed versions of the same partial map.

### 1. A control family where learning should not be needed

Generate random \(C'(1/6)\) presentations and null words by inserting conjugates
of relators.  Greendlinger's condition gives a strong classical Dehn reduction,
so S-GCTS should not claim an algorithmic victory here.

**Purpose:** detect overhead and unsound pruning.  The learned policy should
rediscover long boundary overlaps; a hand-coded Dehn baseline should remain
hard to beat.  If S-GCTS reports a dramatic advantage, first suspect an unfair
instance generator or leaked construction histories.

### 2. The first serious target: Baumslag--Solitar corridors

Use

\[
BS(1,2)=\langle a,t\mid tat^{-1}=a^2\rangle
\]

and the short trivial words

\[
w_n=[t^n a t^{-n},a].
\]

The word length is linear in \(n\), while ordinary van Kampen fillings expose
exponentially expanding \(t\)-corridors.  This makes a clean test of the central
claim: a dart-level or face-level search should blow up, whereas a learned
"doubling band" macro has a short recursive description.

Train on small \(n\), but test on larger held-out \(n\) and on scrambled words
obtained through free reductions, cyclic shifts, inversion, and insertion of
small cancelling diagrams.  Do not let the policy see \(n\) as a privileged
feature.  Compare:

1. breadth-first relator rewriting;
2. unlearned bounded diagram enumeration;
3. Knuth--Bendix/automatic-group tooling where it succeeds;
4. S-GCTS with exact corridor recognition but no learning;
5. S-GCTS with mined recursive macros;
6. a presentation-specific Britton/normal-form implementation as the honest
   specialist ceiling.

Measure wall time, expanded states, peak memory, certificate size before and
after macro expansion, and independently verified face area.  The credible
win is over generic diagram enumeration and generic rewriting.  Beating the
specialized normal form is possible as an engineering result but is not
required to validate S-GCTS.

**Go criterion:** at least a tenfold reduction in expanded states on every
held-out \(w_n\) beyond the training range, with zero false pruning on the full
small-instance census.  **Stop criterion:** the gain disappears after removing
exact duplicate boundary words; that would mean the method learned ordinary
string memoization rather than surface geometry.

### 3. Band interaction rather than a single learned trick

After \(BS(1,2)\), use:

- \(B_3=\langle a,b\mid aba=bab\rangle\), with random known-null braid words;
- the Higman presentation
  \(\langle a,b,c,d\mid a^{-1}ba=b^2,\ b^{-1}cb=c^2,\
  c^{-1}dc=d^2,\ d^{-1}ad=a^2\rangle\);
- balanced presentations used as difficult Knuth--Bendix examples;
- random HNN extensions with one or two stable letters and certified positive
  and negative instances.

The Higman family is valuable because four corridor types interact cyclically.
It asks whether the learner can discover a grammar of compatible bands rather
than one hard-coded doubling rule.  It should be treated as a performance
benchmark, not advertised as an open word problem.

### 4. The experiment where topology really is learned

For a word \(w\in[G,G]\), search for the least \(g\) such that a genus-\(g\)
surface with one boundary maps to the presentation complex with boundary
\(w\).  This is exactly the commutator length \(\operatorname{cl}_G(w)\).

Start with free groups, where faces are absent and the entire problem is edge
pairing and surface topology.  The decision problem with \(g\) as part of the
input is NP-complete, while fixed-genus and specialized algorithms give strong
baselines.  Thus it is difficult enough to expose a genuine search advantage
without any ambiguity about certificate checking.

Benchmark protocol:

- train on random products of one to three commutators in \(F_2,F_3\);
- hold out word lengths, generator ranks, and mapping-class-style scramblings;
- canonicalize chord diagrams under dihedral symmetry;
- compare genus-by-genus exhaustive pairing, cyclic-block-interchange methods,
  SAT/ILP encoding, and S-GCTS;
- require both an upper certificate (the sewn surface) and an independently
  certified lower bound before claiming the exact minimum genus.

This is the best first publication target: **faster exact commutator length on
a public, generated benchmark**, not a claim that NP-completeness has been
evaded.

## A modified formulation: topology as a latent program

The tiling formulation learns a compatible field on translates of a fixed
tile.  The surface formulation should instead learn a distribution over
**topological programs**:

\[
z=(g,b,o;\ T;\ \text{band/pants decomposition}),
\]

where \(g\) is genus, \(b\) the number of boundary components, \(o\) the
orientability flag, and \(T\) a decomposition tree.  Conditional on \(z\), a
second equivariant model scores the exact labelled sewings.  In symbols,

\[
p(D\mid P,w)=\sum_z p(z\mid P,w)\,p(D\mid z,P,w).
\]

This is not used as a probabilistic proof.  It is a way to order an exact
enumeration:

1. propose a topology and coarse decomposition;
2. refine it into bands/pants and then dart pairings;
3. verify the completed finite map;
4. on failure, extract the smallest frontier signature whose bounded
   completion set is empty;
5. canonicalize that signature and reuse it as a geometric no-good.

The most important width parameter is probably not area but **frontier width**
or diagram depth: the maximum number of unresolved darts/bands across the
chosen construction order.  This mirrors the observation that random van
Kampen diagrams can have useful depth structure even when the ambient group is
not hyperbolic.  A practical solver should therefore run iterative deepening
over

\[
(\text{genus},\text{area},\text{frontier width},\text{macro depth})
\]

rather than area alone.

## Route toward an open problem

### Conservative target: exact commutator-length records

Computing commutator length is NP-complete even in nonabelian free groups.
There is room for an exact solver that handles longer or higher-genus public
instances than existing exhaustive methods.  A new exact value for a
previously unresolved explicit word would be a modest but real mathematical
result.  This route has clean certificates and should precede any broad open
conjecture.

The solver must not infer a lower bound from failure to find a surface.  Lower
bounds should come from an exhaustive smaller-genus search, an exact SAT/ILP
unsatisfiability certificate, or an appropriate dual/quasimorphism
certificate.

### Ambitious target: certified surfaces in hyperbolic groups

Gromov's question asks whether every one-ended word-hyperbolic group contains
a closed hyperbolic surface subgroup.  It remains a broad research direction,
and computational experiments on explicit presentations already exist.  An
S-GCTS program can contribute without pretending to settle the conjecture:

1. choose explicit small one-ended hyperbolic presentations from a published
   census;
2. search for a closed labelled surface by learned pants/band decomposition;
3. require a separately checkable \(\pi_1\)-injectivity criterion, for example
   a combinatorial local isometry into a nonpositively curved complex, or a
   presentation-specific small-cancellation certificate;
4. publish the face-pairing table and verifier.

Merely finding a closed surface map is not enough: compressible surfaces are
easy to produce.  The injectivity verifier is the hard mathematical boundary
of this project.  Restricting the first search to targets with an exact local
criterion turns discovery into a finite, trustworthy computation.

The stretch claim should therefore be: **find a new explicit, certified
surface subgroup in a presentation for which no such surface was previously
known**, not "solve the surface subgroup conjecture."

## Experimental hygiene

- Split by construction grammar, not randomly by word.  Otherwise relator
  insertion leaves near-duplicates across train and test.
- Include certified nontrivial words.  A positive-only benchmark measures
  proof reconstruction, not the decision problem.
- Report bounded outcomes as `proved trivial`, `proved nontrivial by external
  certificate`, or `unknown within bounds`; never turn timeout into
  nontriviality.
- Expand every macro before final verification.  Store both compressed and
  expanded certificate sizes.
- Compare canonical state counts as well as time.  This separates algorithmic
  gain from implementation language and low-level optimization.
- Ablate word-only features, topology, exact no-goods, and learned macros.  The
  method earns the name S-GCTS only if topology/band transfer survives the
  word-only ablation.

## Minimal implementation sequence

1. Implement the dart-pairing certificate format and verifier.
2. Implement exhaustive bounded search for disc and once-bordered orientable
   surface topology.
3. Pass the cyclic, \(\mathbb Z^2\), and genus-two certificate tests.
4. Add canonical frontier hashing and exact bounded no-goods.
5. Add explicit band/corridor discovery; benchmark \(BS(1,2)\).
6. Mine macros from successful and failed searches, freezing them before the
   held-out evaluation.
7. Add genus search in free groups and compare with SAT/ILP.
8. Only after those results, select a hyperbolic surface-subgroup census and
   build the presentation-specific injectivity verifier.

## References and existing baselines

- The [KBMAG manual](https://gap-packages.github.io/kbmag/doc/chap2.html)
  documents Knuth--Bendix completion, automatic structures, and certified word
  reduction baselines.
- Myasnikov and Ushakov's
  [Random van Kampen diagrams and algorithmic problems in groups](https://doi.org/10.1515/GCC.2011.006)
  motivates diagram depth as an algorithmically meaningful filling measure.
- Ivanov's
  [bounded and precise word problems](https://arxiv.org/abs/1606.08036)
  gives complexity results and specialized bracket calculus for bounded diagram
  questions, including Baumslag--Solitar presentations.
- Brady and Bridson's
  [super-exponential Dehn-function construction](https://arxiv.org/abs/0902.0082)
  includes the linear-length/exponential-area Baumslag--Solitar commutator
  mechanism used by the corridor benchmark.
- Heuer's
  [Computing commutator length is hard](https://arxiv.org/abs/2001.10230)
  proves NP-completeness for free groups and groups retracting onto them.
- Kharlampovich and Vdovina's
  [fixed-genus commutator-length algorithm](https://arxiv.org/abs/1504.04261)
  is an essential exact comparison.
- Kisil's
  [Gromov Conjecture on Surface Subgroups: Computational Experiments](https://arxiv.org/abs/1001.1460)
  supplies precedent and possible instance-generation ideas for the stretch
  project.
- Wilton's
  [Surface groups among cubulated hyperbolic and one-relator groups](https://arxiv.org/abs/2406.02121)
  is a recent marker for what is known in important subclasses and helps avoid
  selecting a supposedly open target already covered by theory.

## Bottom line

The tentative idea is viable after one change of emphasis:

> GCTS should learn and memoize **frontier topology and filling grammar**, not
> a geometric embedding of the finished surface.

The fastest falsifiable route is

\[
\mathbb Z^2\text{ grids}\ \longrightarrow\ BS(1,2)\text{ corridors}
\ \longrightarrow\ \text{free-group commutator length}.
\]

The first tests exactness, the second tests transferable geometric macros, and
the third tests genuine topology learning against a hard exact problem.  A
surface-subgroup search should be treated as the subsequent open-problem track,
with \(\pi_1\)-injectivity—not surface generation—as the decisive certificate.
