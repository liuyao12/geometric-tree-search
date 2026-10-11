# Notebook 64: prefix failure markings

The report is `docs/research/gcts-rl-renewal/certified-prefix-markings.html`.
The six compressed observation files preserve both construction stages.
`certified-prefix-source-closure-001.json` binds the Python dependency closure;
the reader data also binds the archived output-only source snapshots.

The pilot reuses the public Notebook 63 native-admitted contexts, semantic
families and frozen policy. Failure labels are newly collected. Consumer
propagation reuses those same current-pilot labels for a paired comparison.
No new RL training or cold native admission is claimed.

To reproduce the two stages, use a separate clean checkout. First save the
current `prefix_failure_markings.py`, `audit_prefix_failure_markings.py` and
`run_prefix_failure_pilot.py`. Restore those three files from
`prefix_output_only_001/` into this directory and run
`python3 research/gcts-rl-renewal/run_prefix_failure_pilot.py` from the project
root. Save its results in the expected ledger's `pilot-output-only/` directory,
including the three restored source files. Then restore the current files and
run `python3 research/gcts-rl-renewal/run_prefix_consumer_pilot.py`.
The ledger directory is `.gcts-active/certified-prefix-markings-20261011`.
Run `audit_prefix_pilots.py` after recording the current five source hashes in
`consumer-pilot-source-pins.json`, as in the published reader metadata.

Time cutoffs can change unresolved outcomes on another machine. Do not relabel
an unresolved teacher as negative. Keep newly reproduced transcripts separate
from the published observations and independently audit them before activation.

For local conformance checks run
`python3 research/gcts-rl-renewal/test_prefix_failure_markings.py`.
For reader data corruption checks run
`node research/gcts-rl-renewal/test_prefix_reader.js`.
The exporter expects a completed independent ledger audit. The browser controls
are an inspection interface; they do not perform proof search or native checking.

The result is negative for acceleration: all tested placement counts stay the
same. Stronger conditional failure constraints remain a proposed next experiment.
