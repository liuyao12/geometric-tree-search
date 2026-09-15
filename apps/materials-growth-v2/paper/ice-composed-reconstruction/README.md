# Verified finite ice VI reconstruction

This snapshot extends the earlier `../ice-composed-cores/` experiment. The new result is a complete filling of a known 240-atom target, not connected growth or growth beyond the input.

- 80 selected placements; all atomic t-sums equal 1.
- 80 independently checked overlap-field pairs; none incompatible.
- Maximum positional error: 0.1490126779 Å (threshold 0.15 Å).
- Four support components: no connected-growth claim.
- 51 independently verified geometric exclusions, including 41 composed proofs; 281 blocking arguments and maximum proof depth 9.
- 52 restarted searches across both segments; 71.750972375 seconds cumulative acquisition/search, excluding parsing and independent audit. Not a cold-start 1.41-second result.

`results.json` stores the search rounds, selected candidate indices, and proof dependencies. Its original status awaits independent replay; the subsequently produced `state-check.json`, `proof-check.json`, and `resume-check.json` provide that replay and hash linkage. The previous result and proof receipt are preserved in `../ice-composed-cores/`.

The candidate universe is a finite registration pool at known target atoms, not an exhaustive continuous-space search. The search receives no selected cover or mixed-integer answer. Proof exclusions are redundant geometric consequences, not evidence of learned GCTS marking selectivity. The marking radius was developmentally chosen; this is not a held-out family benchmark. Anchors and half weights are not generally learned.

The versioned runner takes `model kernel output [prior-result prior-proof-check]`. Its companion source files are included. The independent state checker takes `--loop coordinates cover dictionary field-library transfer model result output`; the proof checker takes `model result output`. Large input models and coordinates are not republished here; their hashes are recorded in the receipts. This snapshot therefore supplies auditable outputs and code, not a self-contained benchmark download.

The 3D exporter verifies source-frame hashes and atom ordering before exporting only placement support indices. The page retrieves coordinates from the pinned authors' repository and checks their hash. The reveal slider shows prefixes of saved placements, not a recording of all explored branches or physical time. Historical comparison bars are separate experiments and must not be read as a matched timing comparison with this new result.
