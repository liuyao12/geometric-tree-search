"""Independent movie, local-proof, and aggregate-budget evidence checks."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/knot-classifier'))
from verify_lattice_movie import verify
from verify_extension_proofs import verify_report


def verify_benchmark(report):
    started=time.monotonic()
    assert not report['incomplete'] and report['region'] is None
    cases=report['cases'];bounds=report['bounds'];movies=0
    assert len({(c['evaluatorKnot'],c['seedPair']) for c in cases})==len(cases)
    for c in cases:
        a,b=c['provenance'];assert a['source']==b['source']
        assert a['target']==c['source'] and b['target']==c['target']
        assert c['sourceSeed']!=c['targetSeed']
        for p in (a,b):
            assert p['options']['region'] is None and len(p['steps'])==5
            verify(p);movies+=1
    for lane in report['lanes']:
        assert [r['caseIndex'] for r in lane['runs']]==list(range(len(cases)))
        for r in lane['runs']:
            assert [a['depth'] for a in r['attempts']]==list(range(len(r['attempts'])))
            assert r['stats'].get('nodes',0)==sum(a['stats'].get('nodes',0) for a in r['attempts'])
            assert r['stats'].get('nodes',0)<=bounds['nodeCap']
            assert all(a['status']=='exhausted-finite-search' for a in r['attempts'][:-1])
            cert=r['certificate']
            if cert:
                c=cases[r['caseIndex']]
                assert cert['source']==c['source'] and cert['target']==c['target']
                assert cert['options']['region'] is None
                assert cert['options']['depth']<=bounds['maxDepth']
                assert cert['options']['depth']==r['attempts'][-1]['depth']
                assert r['status']=='equivalent'
                verify(cert);movies+=1
            else:assert r['knotEquivalence']=='unknown'
            if lane['lane']=='unmarked':assert r['extensions'] is None
            else:
                assert r['extensions']['validationMode']=='immutable-native-proof-cache-v1'
                assert r['extensions']['fullAudits']==0
        if lane['lane']=='extension-transfer':
            assert lane['runs'][0]['initialVersion']==0
            for a,b in zip(lane['runs'],lane['runs'][1:]):assert a['extensions']['version']==b['initialVersion']
    result=dict(verify_report(report),movies=movies,cases=len(cases),wallMs=1000*(time.monotonic()-started))
    if report.get('additionalStages'):
        originals={(c['evaluatorKnot'],c['seedPair']):c for c in cases}
        for stage in report['additionalStages']:
            for c in stage['cases']:assert c==originals[(c['evaluatorKnot'],c['seedPair'])]
        result['additionalStageVerification']=[verify_benchmark(stage) for stage in report['additionalStages']]
        result['totalMovies']=movies+sum(s['movies'] for s in result['additionalStageVerification'])
        result['totalResolvedLabels']=result['resolvedLabels']+sum(s['resolvedLabels'] for s in result['additionalStageVerification'])
    for expected in report.get('cumulativeSummary',[]):
        runs=[];latest={}
        for stage in [report]+report.get('additionalStages',[]):
            lane=next(l for l in stage['lanes'] if l['lane']==expected['lane'])
            for run in lane['runs']:
                c=stage['cases'][run['caseIndex']];latest[(c['evaluatorKnot'],c['seedPair'])]=run;runs.append(run)
        assert expected['identified']==sum(bool(r['certificate']) for r in latest.values())
        assert expected['unknown']==sum(not r['certificate'] for r in latest.values())
        assert expected['nodes']==sum(r['stats'].get('nodes',0) for r in runs)
        assert abs(expected['totalMs']-sum(r['totalMs'] for r in runs))<0.00001
    return result


if __name__=='__main__':
    path=Path(sys.argv[1]);report=json.loads(path.read_text());result=verify_benchmark(report);print(json.dumps(result))
    if '--record' in sys.argv[2:]:
        report['independentVerification']=result
        path.write_text(json.dumps(report,separators=(',',':'))+'\n')
