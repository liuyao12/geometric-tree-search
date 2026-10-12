"""Independent replay of the multi-seed benchmark; no solver implementation."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'research/knot-classifier'))
from verify_lattice_movie import verify
from verify_extension_proofs import verify_report


def verify_benchmark(report):
    started = time.monotonic()
    assert not report['incomplete']
    bounds = report['bounds']
    assert bounds['region'] is None and report['region'] is None
    cases = report['cases']
    assert len({(c['evaluatorKnot'], c['seedPair']) for c in cases}) == len(cases)
    movies = 0
    for c in cases:
        assert c['sourceSeed'] != c['targetSeed']
        a, b = c['provenance']
        assert a['source'] == b['source']
        assert a['target'] == c['source'] and b['target'] == c['target']
        for provenance in (a, b):
            assert len(provenance['steps']) == report['stepsPerIndependentScramble']
            assert provenance['options']['region'] is None
            verify(provenance)
            movies += 1
    for lane in report['lanes']:
        assert [r['caseIndex'] for r in lane['runs']] == list(range(len(cases)))
        for run in lane['runs']:
            certificate = run['certificate']
            if certificate:
                c = cases[run['caseIndex']]
                assert certificate['source'] == c['source'] and certificate['target'] == c['target']
                assert certificate['options']['region'] is None
                assert certificate['options']['depth'] == bounds['maxDepth']
                assert certificate['options']['maxEdges'] == bounds['maxEdges']
                assert run['knotEquivalence'] == 'equivalent'
                verify(certificate)
                movies += 1
            else:
                assert run['knotEquivalence'] == 'unknown'
        if lane['lane'] == 'unmarked':
            assert all(r['extensions'] is None for r in lane['runs'])
        else:
            assert lane['runs'][0]['extensions']['initialVersion'] == 0
            for previous, current in zip(lane['runs'], lane['runs'][1:]):
                assert previous['extensions']['version'] == current['extensions']['initialVersion']
    proofs = verify_report(report)
    return dict(proofs, movies=movies, cases=len(cases), wallMs=1000*(time.monotonic()-started))


if __name__ == '__main__':
    path = Path(sys.argv[1])
    report = json.loads(path.read_text())
    result = verify_benchmark(report)
    print(json.dumps(result))
    if '--record' in sys.argv[2:]:
        report['independentVerification'] = result
        path.write_text(json.dumps(report, separators=(',', ':')) + '\n')
