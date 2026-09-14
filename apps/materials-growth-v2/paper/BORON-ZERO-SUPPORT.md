# Certified impossible placements do not resolve the hard boron searches

14 September 2026. Fixed-model proof preprocessing, not learned transferable
markings or a replacement for the reference tree search.

## Construction

Use only the original t-contribution matrix A, full required target b, and
one binary variable per stored candidate. No selected training witness or
marking is supplied to the investigation. Repeated linear programs maximize
the sum of currently investigated variables under `A x=b, 0<=x<=1`.
Numerically positive variables are removed from investigation, not from search.
They are not claimed to admit an integer completion.

For the remaining set U, construct rational multipliers satisfying
`A^T y+z >= 1_U`, `z>=0`. An exact bound `b^T y+sum(z)<1` implies every binary
selection variable in U is zero in any exact completion. All three exported
exclusion certificates have bound exactly zero. Floating-point solver output
alone never justifies a removal.

| Model | Full candidates | Certified excluded | Search, both marking lanes |
| --- | ---: | ---: | --- |
| α | 108 | 0 | Complete, connected |
| β-105 | 1,458 | 0 | Complete, connected |
| β-106 | 4,779 | 486 | Budget unknown |
| γ | 486 | 162 | Complete, connected; all forced |
| τ-105 | 2,916 | 0 | Complete, connected |
| τ-106 | 7,884 | 1,026 | Budget unknown |

The generator's recorded LP/certificate-loop times sum to about 0.38 seconds
on this host. That excludes matrix construction, input loading, independent
verification and search; it is not an end-to-end timing comparison. Retained
candidates are not certified individually extensible.

## Search integration and verification

The unchanged production kernel is used by the research harness with a static
constraint callback. Every candidate remains in the declared pool. Certified
exclusions remove incidence edges through the kernel's normal legality path.
The global dead/forced/earliest-generation order remains intact, using the
previously audited linear scheduler and justified parent-local exclusions.
No LP is called during search. All target atoms remain generation-zero roots.

Before installing the callback, a JavaScript checker scales every rational to
BigInt arithmetic and verifies all candidate-column inequalities and the bound.
A separate Python Fraction checker independently reconstructs them from the
source data and confirms that all six original training witnesses survive.
A small exhaustive control checks all four subsets of a two-candidate model,
eight corrupted-certificate rejections, incomplete-pool rejection, forced
placement and root rollback. This is not an exhaustive test of all large-model
search traces.

Twelve runs use 100,000 advances / 15 seconds each, with and without markings.
The harness independently rebuilds graph and reverse incidence every 100
advances and at terminal states. Final t/m sums, connectedness of completed
results, certificate hashes, source hashes, absence of excluded selections and
root rollback are checked. The callback is fixed for the lifetime of each run;
dynamic pool changes or proof transfer are not supported by this experiment.

The removed candidates preserve the exact complete solution sets. Nonetheless,
both difficult structures remain unresolved. γ's sole branch disappears, but
that is not a demonstrated total-cost speedup. This control shows that removing
these globally impossible single placements alone is insufficient; it does not
prove that all stronger static preprocessing would fail.

## Scientific scope

These are known-coordinate, finite-pool, full-target proofs. They are not
geometrically transferable motif prohibitions, a same-condition family model,
or coordinate-blind growth. No artificial marking anchors or chemical rules
were introduced. The production growth app is unchanged. The remaining goal
requires useful restrictions on combinations and shared geometric connections,
not just a larger catalogue of single-placement exclusions.

```
python boron-zero-support.py INPUT LEARNING PROOF
python verify-boron-zero-support.py INPUT LEARNING PROOF CHECK
node test-certified-zero-support.mjs KERNEL
node boron-face-reference-search.mjs INPUT LEARNING KERNEL SEARCH_DIR linear-exclusions 100000 15 id - PROOF
python verify-boron-zero-support-search.py INPUT LEARNING PROOF SEARCH_DIR SEARCH_CHECK
```

Use `precheck-v2.json` and the original `periodic-connected-c12-v1.json`.
Earlier source-hash-bound studies require their original published source
revision; the optional proof argument extends the current research harness.
