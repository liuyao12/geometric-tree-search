# Bent-arm first-corona search control

This is a specialized finite voxel/SAT control, not a conforming GCTS growth
benchmark. The target is a full touching first corona, allowing proper cubic
rotations and integer translations. Face, edge, and vertex contacts all count.
A budget expiration remains unknown.

The prototype is one of the 72 fixed-length, 25-cube bend classes in the
coordinate census. `corona.build` enumerates every nonoverlapping placement
meeting the root's complete voxel halo. Its `by` incidence map records every
candidate covering each voxel. Coverage is required at every halo voxel, and
at-most-one constraints apply at every voxel occupied by any candidate,
including voxels outside the halo. This finite reduction is specialized to
unit lattice cubes; it is not a general weighted-point engine.

The sequential-counter encoding uses the existing `corona.py` formula.
The native-cardinality encoding keeps the same candidate universe and voxel
incidences and supplies each nonoverlap constraint directly to the solver.
The optional incremental-coverage mode starts with nonoverlap constraints,
then adds batches of eight uncovered halo requirements, ordered by original
candidate count. These intermediate formulas are relaxations. An intermediate
UNSAT would exclude a full corona; an intermediate SAT is never reported as a
corona unless every halo voxel is covered. This is not generation-first GCTS
scheduling. CDCL chooses decisions and manages backtracking internally; there
are no geometric learned markings, GCTS generation numbers, or GCTS rollback
claims in this experiment.

Every positive witness is checked both by `corona.verify` and a separate
coordinate checker using quarter-turn-generated orientations, disjoint voxel
sets, and all cube-vertex sectors. The checker accepts the previously verified
ring-octocube first corona and rejects deliberately missing coverage and a
duplicated overlapping tile. Both native-cardinality solvers also freshly find
verified ring-octocube coronas, each with 30 surrounding tiles; the coordinates
are in [the positive-control record](../../data/bent-six-arm/variants/first-coronas/ring-positive-control.json). The new negative certificates are regenerated
with proof logging; a separate rectangular placement enumeration audits the
candidate universe, then DRAT-trim checks the UNSAT proof. Unchecked negative
screening outputs remain explicitly unverified.

The recorded runs use Python 3.12.14 and `python-sat==1.9.dev5`.

Recorded solver times exclude formula construction and solver setup, which
are recorded separately. Runs may execute concurrently and use different
phase preferences, encodings, and budgets. They are existence probes, not a
controlled solver-speed comparison. Kissat is given a conflict budget because
this binding does not support timed interruption or incremental solve calls;
its run must not be described as a wall-time-limited search.

Run records and checked proof files are linked from
[bend variants](bent-arm-variants.html). The summary generator independently
rechecks any positive witness before presenting a positive lower bound.
