# Boron configuration holdout: coverage does not yet transfer

14 September 2026. Follow-up to the shared three-site filling experiment.

For each of the six models, construct a new dictionary from the other five
configurations only. Learn their shared positive t-values and scalar m-values,
freeze both, then register three-site supports in the omitted configuration.
All six training fits pass exact rational filling. None of the six omitted
configurations passes the current **first-match, all-matched-occurrences** test.

| Omitted configuration | Frozen types | Matched / proposed supports | Exactly filled atoms | Underfilled | Overfilled |
| --- | ---: | ---: | ---: | ---: | ---: |
| alpha | 851 | 91 / 148 | 0 / 12 | 12 | 0 |
| beta-105 | 846 | 1335 / 1419 | 3 / 105 | 96 | 6 |
| beta-106 | 730 | 1210 / 1442 | 5 / 106 | 70 | 31 |
| gamma | 829 | 216 / 412 | 0 / 28 | 24 | 4 |
| tau-105 | 822 | 2558 / 2838 | 6 / 210 | 128 | 76 |
| tau-106 | 633 | 2287 / 2888 | 0 / 212 | 165 | 47 |

All frozen training scalar markings have one class. Consequently the lack of
marking conflicts in the held-out inputs is uninformative. This test reveals
both unrecognized geometric supports and a failure of the chosen frozen
weights to fill the held-out configurations under this occurrence rule.

## Separation and verification

Each learner process receives a file containing only its five training inputs.
The holdout is not used to create types, select the tolerance, train t/m values,
or modify the library after training. The 0.01 Å tolerance and radius multiplier
1.35 were inherited from the prior all-input development experiment; this is
therefore a development holdout, not a pristine preregistered test set.

The verifier independently checks that each training file equals exactly the
intended five source configurations and that every template has an exact
originating occurrence in those training inputs. It checks the frozen
dictionary's hash, all training and test poses, periodic-image congruence,
proper rotations, and exact rational t/m arithmetic. Training poses remain
approximate geometric registrations even though point-ID filling is exact.

All models come from one supplement, so leaving out a configuration is not
independent-source validation. They are elemental-boron structural controls,
not a documented common-temperature/pressure ensemble. Known test coordinates
and periodic cells are used to propose and register supports; this is not
coordinate-blind growth.

## What failure means—and does not mean

For each observed support, registration selects the first acceptable template
and site permutation, and includes every matched occurrence. It does not search
over other acceptable templates, role correspondences, or subsets of placements.
Unmatched support counts are failures of this registration procedure, not
certified geometric impossibilities. A Kabsch pose failing maximum error does
not rule out every minimax-tolerance pose.

In particular, **0/6 here does not establish that tree search cannot reconstruct
these inputs**. Alternative placement selection and correspondence enumeration
are the next required tests. Neither passing training coverage nor failing this
restricted replay resolves the intended reconstruction problem. No changes were
made to the production growth engine.

## Reproduce

Keep `boron-leave-one-out.py`, `boron-triple-precheck.py`,
`ice-motif-dictionary.py`, `presearch-markings.py`, `verify-boron-triples.py`, and
`verify-boron-leave-one-out.py` together. Use the audited source coordinates
produced by `boron-input-audit.py` and the dependencies in the three-site report.

```
python boron-leave-one-out.py boron-data/input-audit.json boron-holdout
python verify-boron-leave-one-out.py boron-data/input-audit.json boron-holdout
```

The runner uses two worker processes and refuses to overwrite the output
directory. It exports training inputs, logs, frozen dictionaries, registered
test occurrences, and a summary. The public summary omits source geometry.
