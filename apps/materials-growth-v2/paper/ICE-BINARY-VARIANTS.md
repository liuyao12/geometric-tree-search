# Alternative markings per motif: a useful but biased binary control

14 September 2026. This tests a restricted marking hypothesis, not a discovered
physical rule or a Nature-level result. Same frozen motifs and 300 developmental
validation configurations as ICE-FROZEN-VALIDATION.md.

## What changed

One scalar assignment per geometric motif collapsed to two uninformative classes.
Here each pair motif may carry either of two globally flipped binary marking
variants. The two constituent geometric components define its ports; no chemistry
rule defines those components. For each type, a binary variable specifies whether
its port marks agree or differ. Only selected training tilings supply constraints.

For a cycle witness, compatibility requires the XOR of its type contrasts to be
zero. Within this declared hypothesis class, maximize the number of contrasting
types. Assigning contrast one to all 347 admitted types satisfies the training
constraints and reaches the objective's absolute upper bound. Each type then has
two alternatives: port marks (0,1) or (1,0), transported with its geometry.

An independent solver verifies actual pointwise marking lifts for all 238 selected
training tilings and all 300 selected validation covers, rather than relying only
on the cycle-count reduction. Physical placements remain selectable at most once.

**Important selection bias:** these positive witnesses were constructed as connected
degree-two covers and all have even cycle length. That construction makes maximum
binary contrast feasible. It does not establish a parity law of ice or distinguish
its phases. The 300 validation configurations have now been inspected during method
development; this is not a fresh confirmatory holdout.

## Explicit variants versus relative-mark constraints

Explicitly enumerating both marking variants adds redundant flip choices and
performs poorly. We therefore also implement an exact existential projection.
For a template bit pattern b_c at its points, a placement has an unknown common
flip v_c, and its markings are `m_c(p) = v_c XOR b_c(p)`.

A common point coloring g exists exactly when the relative equations
`g(p) XOR g(q) = b_c(p) XOR b_c(q)` are consistent for every placed candidate.
Given g, recover each placement's flip from any one of its points. Conversely,
compatible explicitly marked placements supply such a g. This proves equivalence
to existence of a decorated lift—not equivalence to the unmarked tiling problem.

The quotient implementation stores parity components and detects inconsistent
relative marks. It retains one candidate per physical placement instead of two
decorated candidates. It does not fix independent component colors prematurely:
their relative orientation remains free until an overlap constrains it. Full
candidate refresh handles distant effects of merging parity components. Cache
state is keyed by the placed prefix and rebuilt after rollback as necessary.

## Results under the same per-case budget

| Search representation | Exact finite covers | Connected positive covers | Unknown |
| --- | --- | --- | --- |
| Unmarked reference | 289 / 300 | 27 | 11 |
| Explicit binary variants | 218 / 300 | 15 | 82 |
| Relative-mark quotient | 289 / 300 | 85 | 11 |

The quotient's connected results by phase are Ih 20/75, II 35/75, VI 13/75 and
VIII 17/75. Budgets remain 10,000 advances / one second per case. The search uses
the full registered pool and is not given selected-cover answers. All supplied
target atoms are roots at generation zero. No connectedness constraint is imposed
on the search itself.

The increase from 27 to 85 connected covers is a useful computational outcome in
this restricted experiment. It is **not** a same-solution-set speedup over the
unmarked problem: the binary hypothesis excludes odd-cycle covers. Expanded and
quotient binary representations do describe the same projected physical solutions,
but no controlled wall-time speedup study is reported here. The quotient uses a
costly full refresh and still leaves most returned covers disconnected.

## Verification

Independent Python checks reconstruct every physical selected placement, exact
capacity-two sums and pointwise binary constraints, and find a compatible binary
coloring for each reported quotient solution. They also verify connectivity and
the absence of duplicate physical placements across marking variants.

The quotient passes 80 small exhaustive tests covering 3,220 candidate-domain
checks against explicit binary assignments, completion equivalence and root
rollback. A separate distant-dependency test merges two parity components and
checks that a candidate touching neither merge endpoint is invalidated, then
restored on undo. The large harness checks global dead/forced/generation priority,
periodic incidence audits and root semantic restoration. Production kernel code
is unchanged; this is a declared research plug-in.

## What this supports—and what remains open

Allowing alternative markings can express constraints unavailable to one fixed
mark per geometric type, and the representation of that freedom matters for
search. This supplies a concrete GCTS marking experiment rather than a species
labeling exercise. However, the hypothesis class and contrast objective are
hand-chosen; the positive selection procedure supplies a strong parity bias.
Useful context-sensitive rule discovery, general t/occurrence learning, independent
trajectory validation and growth without supplied coordinates remain unresolved.

The next test must challenge the hypothesis on positive decompositions not chosen
to make even cycles, and use better justified connection evidence. We must not
generalize the rule to other materials merely because this control admits the
selected ice witnesses.

## Reproduction

```
python ice-binary-marking.py PILOT_DICTIONARY PILOT_COVER WEIGHT_MODEL MARKING FIRST_SELECTION SECOND_SELECTION TARGET_FOLDER/witness-*.json
python verify-ice-binary-marking.py MARKING PILOT_DICTIONARY TRAINING_CHECK training FIRST_SELECTION SECOND_SELECTION TARGET_FOLDER/witness-*.json
python verify-ice-binary-marking.py MARKING VALIDATION_DICTIONARY LIFT_CHECK validation VALIDATION_SELECTION
node ice-binary-reference.mjs VALIDATION_DICTIONARY MARKING ../kernel.mjs EXPANDED_RESULTS
node ice-binary-reference.mjs VALIDATION_DICTIONARY MARKING ../kernel.mjs QUOTIENT_RESULTS quotient
python verify-ice-binary-reference.py VALIDATION_DICTIONARY MARKING QUOTIENT_RESULTS PROVENANCE RESULT_CHECK
node test-binary-marking-quotient.mjs ../kernel.mjs
```

The required earlier artifacts are documented in the thermal, targeted-witness and
frozen-validation reports. Keep binary-marking-quotient.mjs beside the harness.
No atomic coordinates or derived coordinate dictionaries are republished.
