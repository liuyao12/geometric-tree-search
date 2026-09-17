# Tolerant markings: training agreement without calibration retention

This tests whether the exact-equality collapse can be avoided by error-tolerant m-values on the same learned t-support. It can—but the tested codes fail to preserve the supplied calibration tilings. They are not promoted to the growth engine.

## Declared model

Use the independently replayed 80-frame overlap graph. On each connected component, choose a first landmark with maximum graph eccentricity, then further landmarks by farthest-point selection; ties use anchor index. An anchor's channel value is its integer shortest-path distance to a landmark. No calibration labels or negative examples select landmarks. One, two, four and eight channels are tested as disclosed model settings, not inferred channel counts.

Each assigned value represents the closed interval [m−1/2,m+1/2]. Multiple channels form Cartesian-product boxes (L-infinity), not the previous Gaussian RKHS balls. Agreement requires a common intersection at each source atom, equivalently a range of at most 1 in every channel. This is not a transitive chain of pairwise matches. Along an observed graph edge, distance-to-landmark values differ by at most 1, which guarantees training agreement. Rotations act on anchor coordinates, leaving these scalar channels invariant.

## Results

| Channels | Abstract compatible anchor pairs separated | Training tilings retained | Calibration tilings retained among t-valid cases |
| --- | ---: | ---: | ---: |
| 1 | 101,496 / 630,763 | 80 / 80 | 0 / 3 |
| 2 | 199,309 / 630,763 | 80 / 80 | 0 / 3 |
| 4 | 277,102 / 630,763 | 80 / 80 | 0 / 3 |
| 8 | 373,843 / 630,763 | 80 / 80 | 0 / 3 |

The pair counts enumerate same-species, t-capacity-compatible prototype anchor pairs including self pairs. They are **not** counts of geometrically realizable connections, invalid material connections, or candidates pruned during search. More separated pairs do not establish scientific usefulness.

Independent source-coordinate replay checks exact rational t filling and common marking boxes on every supplied pose. Only three of twenty calibration configurations already pass the learned t-support; all three are rejected by every tested marking. The remaining seventeen are not attributed to m-learning. These checks concern their supplied tilings, not the impossibility of another tiling under the new code. The upstream geometric dictionary already saw the calibration frames; no genuinely held-out performance claim is possible.

Source replay also identifies 213 distinct overlap pairs in those three t-valid calibration tilings that were absent from the 9,168 training pairs: 35 in c00021, 122 in c01021 and 56 in c01523. These are positive configurations with new pair identities, not evidence of forbidden connections. This is direct evidence against labeling every unobserved pair invalid.

Corruption controls reject a training disagreement, an altered radius, and a mismatched support hash. A separate interval control illustrates why overlap along a chain is insufficient.

## Interpretation and remaining work

The exact-equality diagnostic was not a general impossibility result: nonconstant tolerant codes exist. This construction nevertheless overfits training overlap topology. It uses no labeled negative connections and has no evidence that its new rejections are desirable. It does not jointly learn m-support, t-support, motif variants or the tolerance; the inherited support/pose biases remain. No tree search was run with this code, and no acceleration is claimed.

Useful progress now requires marking features or context-dependent variants that preserve unseen positive configurations, evaluated separately from support failures. Increasing channel count or maximizing abstract pair separation alone is insufficient.

## Evidence

- [Markings and frozen training-graph landmarks](markings.json)
- [Independent per-configuration replay](check.json)
- [Learner](learn-tolerant-support-markings.py)
- [Verifier](verify-tolerant-support-markings.py)
- [Corruption controls](test-tolerant-support-markings.py)

The learner takes `support equality-graph graph-check output`; the verifier takes `coordinates dictionary library support markings output`. Larger coordinate-bearing input artifacts remain local and are identified by hashes.
