"""Replay every scheduler lane using the independent lattice/proof verifier."""
import importlib.util
import json
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify_escalation',root/'scripts/verify-lattice-escalation.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def verify_schedules(report):
    assert len(report['cases'])==2 and len(report['lanes'])==4
    assert {l['id'] for l in report['lanes']}=={'balanced-gcts','adaptive-gcts','balanced-brute','adaptive-brute'}
    normalized=dict(report,lanes=[dict(l,lane='extension-transfer' if l['marked'] else 'unmarked') for l in report['lanes']])
    for lane in report['lanes']:
        assert lane['schedule']==('balanced' if lane['id'].startswith('balanced') else 'smaller-frontier')
        assert lane['marked']==lane['id'].endswith('gcts')
        summary=next(s for s in report['summary'] if s['lane']==lane['id'])
        assert summary['identified']==sum(bool(r['certificate']) for r in lane['runs'])
        assert summary['unknown']==sum(not r['certificate'] for r in lane['runs'])
        assert summary['nodes']==sum(r['stats'].get('nodes',0) for r in lane['runs'])
        assert abs(summary['totalMs']-sum(r['totalMs'] for r in lane['runs']))<0.00001
    return module.verify_benchmark(normalized)
if __name__=='__main__':
    path=Path(sys.argv[1]);report=json.loads(path.read_text());result=verify_schedules(report);print(json.dumps(result))
    if '--record' in sys.argv[2:]:
        report['independentVerification']=result;path.write_text(json.dumps(report,separators=(',',':'))+'\n')
