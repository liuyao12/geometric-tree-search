"""Verify all-base rescue witnesses against periodic coordinates and clouds.

Uses independent observed-cloud reconstruction and supplied marking bijections.
Checks existence of a positional fit, not completeness of pose enumeration.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from ase.geometry import find_mic

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('verify',Path(__file__).with_name('verify-ice-portable.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
coordinates,cover_path,dictionary_path,selection_path,library_path,baseline_path,pose_path,output=sys.argv[1:]
paths=[coordinates,cover_path,dictionary_path,selection_path,library_path,baseline_path]
corpus,cover,dictionary,selection,library,baseline=map(read,paths);data=read(pose_path)
assert data['inputHashes']=={Path(p).name:sha(p) for p in paths}
assert data['codeHash']==sha(Path(__file__).with_name('ice-all-base-rescue.py'))
for key,path in zip(['coordinates','cover','dictionary','selection'],paths[:4]):assert library['sourceHashes'][key]==sha(path)
assert baseline['inputHashes'][Path(library_path).name]==sha(library_path)
cc={c['id']:c for c in corpus['configurations']};cv={r['id']:r for r in cover['results']}
dc={r['id']:r for r in dictionary['configurations']};ss={r['id']:r for r in selection['results']}
bb={r['id']:r for r in baseline['results']}
expected={cid for cid in cc if not dc[cid]['training']}
assert {r['id'] for r in data['results']}==expected and len(data['results'])==len(expected)
count=0;max_position=0.;max_mark=0.;reports=[]
for row in data['results']:
    cid=row['id'];c=cc[cid];selected=ss[cid]['selected']
    queries,centers=v.local_clouds(c,cv[cid],selected)
    old={r['edge']:r for r in bb[cid]['rows']}
    assert [r['edge'] for r in row['rows']]==selected
    for r in row['rows']:
        occurrence=dc[cid]['occurrences'][r['edge']]
        assert r['savedPoseMatched']==old[r['edge']]['anyPoseMatched']
        assert r['anyPoseMatched']==bool(r['witnesses']) and r['witnessedPoseEntries']==len(r['witnesses'])
        assert not r['savedPoseMatched'] or r['anyPoseMatched']
        for w in r['witnesses']:
            rotation=v.proper(w['rotationRow']);perm=w['permutation']
            assert sorted(perm)==list(range(len(occurrence['ids'])))
            template=dictionary['types'][w['type']]
            actual_ids=[occurrence['ids'][i] for i in perm]
            assert [c['species'][i] for i in actual_ids]==template['species']
            predicted=np.asarray(template['positions'])@rotation
            actual=np.asarray(c['positions'])[actual_ids]
            delta,_=find_mic(actual-actual[0]-(predicted-predicted[0]),c['cell'],pbc=True)
            lifted=actual[0]+predicted-predicted[0]+delta
            translation=(lifted-predicted).mean(axis=0)
            errors=np.linalg.norm(predicted+translation-lifted,axis=1)
            assert errors.max()<=library['positionToleranceAngstrom']+1e-8
            max_position=max(max_position,float(errors.max()))
            ends=v.ends(dict(occurrence,type=w['type'],permutation=perm),cv[cid]['components'],cv[cid]['componentPairs'][r['edge']])
            assert len(w['endpoints'])==2
            for side,item in enumerate(w['endpoints']):
                motif=library['motifs'][item['motif']];base=library['baseMotifs'][motif['base']]
                assert base['pairType']==w['type'] and base['componentSites']==[sites for sites,_ in ends]
                root=ends[side][1];cloud=motif['cloudM'][side];q=queries[root];mapping=item['fit']['permutation']
                assert sorted(mapping)==list(range(len(q['vectors'])))
                assert all(a==q['colors'][j] for a,j in zip(cloud['colors'],mapping))
                residual=np.linalg.norm(np.asarray(cloud['vectors'])@rotation-q['vectors'][mapping],axis=1)
                assert residual.max()<=library['markingRadiusAngstrom']+1e-10
                max_mark=max(max_mark,float(residual.max()));count+=1
    assert row['savedPoseMatched']==sum(r['savedPoseMatched'] for r in row['rows'])
    assert row['anyPoseMatched']==sum(r['anyPoseMatched'] for r in row['rows'])
    reports.append({k:value for k,value in row.items() if k!='rows'})
summary={key:sum(r[key] for r in reports) for key in ['edges','savedPoseMatched','anyPoseMatched','procrustesProposals']}
summary['configurations']=len(reports)
summary['completeConfigurations']=sum(r['edges']==r['anyPoseMatched'] for r in reports)
result=dict(scope=__doc__,poseHash=sha(pose_path),verifierHash=sha(__file__),endpointFitsChecked=count,
            maxPositionResidualAngstrom=max_position,maxMarkResidualAngstrom=max_mark,summary=summary,results=reports,
            limits='Positive witnesses only; no independent exhaustive pose coverage or unknown-as-impossible claim. Alternative training bases and developmental selected covers, not search or blind growth.')
with Path(output).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:value for k,value in result.items() if k!='results'}),flush=True)

