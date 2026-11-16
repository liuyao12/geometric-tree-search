# First-order proof discovery with GCTS and a numeric policy

The experiment accepts equality-free first-order clauses and searches for a
refutation. Clauses represent the axioms and the negated conjecture. A proof
is an independently checked resolution and factoring derivation of the
empty clause. Terms, clauses, actions, policy weights and proof certificates
are data structures. The experiment runs locally in Python and makes no
model or network calls.

The scheduler uses an exact index of complementary predicate/arity pairs.
An exact lifted unification check handles the pairs that pass a rigid-clash
test, and factoring is available. Learned and fixed choices reorder a bounded shortlist of
pending clauses. FIFO slots recur independently of the policy. A run may
stop before finding a proof. Any sound countermodel is a separate verdict.

Training starts with zero weights and uses checked episode rewards and
counted inference work. A distinct calibration split selects one fixed
control and one learned seed. All weights are frozen before evaluation on
separate generated families and external clauses. The control arms share
the same exact kernel and checker. Time-to-proof includes scheduling,
search and proof replay. Policy fitting and dataset generation are outside
the per-problem time budget. The timer starts with parsed input clauses.

## Run the experiment

From this directory, use Python 3.10 or newer:

```sh
python3 -B run.py ./results
python3 -B audit.py ./results
python3 -B report.py ./results ./reader
```

`results/summary.json` contains the protocol and headline metrics.
`results/traces.json` contains all exact inputs, training episodes, held-out
measurements and returned proof DAGs. `results/policies.json` records the
policy weights and calibration choices. When available, `results/example.json`
pairs a formal input with a standalone certificate.

The first benchmark uses only equality-free refutations. Adding equality
inferences and explicit induction will require separate checker rules and
benchmark families.

The six verbatim files in `data/` are from the TPTP v10.0.0 Problem Library,
copyright Geoff Sutcliffe and Christian Suttner. The source links and
SHA-256 hashes are in `data/tptp-manifest.json`. The parser uses the final
marked negated conjecture as the guidance seed. The original clause order
is preserved for these six files. [TPTP redistribution terms](https://seetptp.tptp.org/file/TPTPWorld/TPTP/Documents/ReadMe)

## Relay curriculum follow-up

The follow-up compares six easier-to-harder tiers of guarded relays with a
shuffled schedule over the same cases and per-episode seeds. Both learn from
the same checked reward, starting at zero weights. A separate three-way
witness-join family selects one seed per schedule, and the models are
written and frozen before generating three new held-out families. Those
families cover odd-cycle coloring, nested term assembly and finite
injection. Six explicit finite models give satisfiable controls. Size-first
is the primary comparator. The follow-up keeps the original search kernel
and time and activation limits.

```sh
python3 -B curriculum.py ./curriculum-results
python3 -B curriculum_report.py ./curriculum-results ./curriculum-reader
```

The first command also runs the saved-data proof audit on the generated
curriculum cohort.

## A theorem library from an arithmetic boundary

This run starts with an empty library and two named targets: every natural
number greater than one has a prime divisor, and there is a prime above
every natural number. Search aligns marked term positions on a lattice and
grows resolution and factoring steps from the negated goal. A fixed
grammar generates auxiliary statements and candidate witnesses. Verified
theorems become new boundary clauses for the next stage of the same run.

The declared boundary consists of elementary order, divisibility,
multiplication and primality laws. Ordinary and strong induction are
trusted inference schemas. The run uses these arithmetic laws directly
and uses fixed scheduling, so it measures theorem discovery and reuse.
The proof replay validates the witnesses, induction obligations and lemma
admission order, and an independent clause checker verifies the refutations.

```sh
python3 -B prime_run.py ./prime-results
python3 -B prime_run.py ./prime-results --verify
python3 -B prime_report.py ./prime-results ./prime-reader
```

`boundary.json` declares the input laws and search bounds.
`certificate.json` records the attempt order, induction steps and exact
proofs. `verification.json` records which dependency leaves the checker
replayed, including whether the final proof used the newly admitted
prime-divisor theorem.
