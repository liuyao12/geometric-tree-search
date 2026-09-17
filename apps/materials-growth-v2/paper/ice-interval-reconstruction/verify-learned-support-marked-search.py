"""Independent value reconstruction and common-interval replay, plus geometry receipt.

The geometry verifier is invoked separately. Every candidate marking is rebuilt
from frozen training codes and its learned type, not trusted from the adapter.
"""
import hashlib,json,subprocess,sys,tempfile
from collections import defaultdict
from pathlib import Path

coordp,supportp,markp,basep,poolp,resultp,out=map(Path,sys.argv[1:])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
support,mark,base,pool,result=[json.loads(p.read_text()) for p in [supportp,markp,basep,poolp,resultp]]
assert pool['sourcePoolHash']==sha(basep)
assert pool['marking']['hash']==sha(markp) and result['marking']==pool['marking']
assert mark['sourceHashes'][supportp.name]==sha(supportp)
assert result['poolHash']==sha(poolp)
channels=pool['marking']['channels'];values=next(r['values'] for r in mark['runs'] if r['channels']==channels)
assert mark['radius']==pool['marking']['radius']==.5
assert pool['marking']['action']=='identity'
by_type=defaultdict(list)
for index,a in enumerate(support['anchors']):by_type[a['type']].append(index)
assert len(values)==len(support['anchors']) and all(len(v)==channels for v in values)
assert [r['id'] for r in base['models']]==[r['id'] for r in pool['models']]==[r['id'] for r in result['results']]
rows=[]
for original,entry,run in zip(base['models'],pool['models'],result['results'],strict=True):
    assert entry['geometry']==original['geometry']
    assert {k:v for k,v in entry['model'].items() if k!='candidates'}=={k:v for k,v in original['model'].items() if k!='candidates'}
    assert len(entry['model']['candidates'])==len(original['model']['candidates'])
    reconstructed={}
    for candidate,source in zip(entry['model']['candidates'],original['model']['candidates'],strict=True):
        assert not source['m']
        assert {k:v for k,v in candidate.items() if k!='m'}=={k:v for k,v in source.items() if k!='m'}
        g=entry['geometry'][candidate['id']];indices=by_type[g['type']]
        assert len(indices)==len(g['ids'])
        expected=[]
        for index,atom in zip(indices,g['ids'],strict=True):
            for channel,v in enumerate(values[index]):
                assert isinstance(v,int)
                expected.append(dict(point=f'a:{atom}',channel=str(channel),lo=v-.5,hi=v+.5))
        assert candidate['m']==expected
        reconstructed[candidate['id']]=expected
    intervals=defaultdict(list)
    for key in run['selected']:
        for m in reconstructed[key]:intervals[m['point'],m['channel']].append((int(2*m['lo']),int(2*m['hi'])))
    for key,boxes in intervals.items():assert max(v[0] for v in boxes)<=min(v[1] for v in boxes),(run['id'],key)
    rows.append(dict(id=run['id'],status=run['status'],complete=run['complete'],selected=len(run['selected']),
                     checkedCandidateCount=len(reconstructed),checkedPointChannels=len(intervals),
                     sharedPointChannels=sum(len(v)>1 for v in intervals.values())))
with tempfile.TemporaryDirectory(prefix='gcts-marked-geometry-') as tmp:
    checkp=Path(tmp)/'check.json'
    subprocess.run([sys.executable,str(Path(__file__).with_name('verify-learned-support-gap-repair.py')),'--search',str(coordp),str(supportp),str(poolp),str(resultp),str(checkp)],check=True,capture_output=True,text=True)
    geometry=json.loads(checkp.read_text())
assert len(geometry['rows'])==len(rows)
report=dict(markingHash=sha(markp),supportHash=sha(supportp),sourcePoolHash=sha(basep),poolHash=sha(poolp),searchHash=sha(resultp),
            verifierHash=sha(Path(__file__)),channels=channels,rows=rows,geometryReplay=geometry,
            limits='Exact doubled-integer common interval checks and independent tolerance-based geometry replay. All candidate t-data, order and geometry match the unmarked source. Source marking training validity is a separate receipt. A found cover need not equal a supplied training/calibration cover or have connected support. No hypothesis necessity, held-out condition provenance or speedup established.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(dict(channels=channels,configurations=len(rows),complete=sum(r['complete'] for r in rows),allCandidateMarkingsChecked=True)))
