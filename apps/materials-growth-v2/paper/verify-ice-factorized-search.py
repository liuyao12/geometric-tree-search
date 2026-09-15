"""Independent selected-state replay; no claim about unvisited search states."""
import hashlib, importlib.util, json, pathlib, sys
source_path, blocks_path, directory, output = map(pathlib.Path, sys.argv[1:])
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads(source_path.read_text()); data=json.loads(blocks_path.read_text())
assert data['sourceModelHash']==digest(source_path)
spec=importlib.util.spec_from_file_location('cloud', pathlib.Path(__file__).with_name('portable-cloud-markings.py'))
cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
results=[]
for row in data['models']:
    path=directory/f"{row['fold']}.json"; run=json.loads(path.read_text())
    assert run['sourceModelHash']==digest(source_path) and run['blocksHash']==digest(blocks_path)
    assert run['result']['file']==row['file'] and run['result']['fold']==row['fold']
    totals={p:0 for p in row['required']}; marks={}; owners=set(); ids=set()
    for choice in run['selected']:
        assert isinstance(choice['index'],int) and 0<=choice['index']<len(row['blocks'])
        b=row['blocks'][choice['index']]
        if run['result'].get('ordering')=='coupled-observed':
            assert b['endpointChoices'][0][choice['left']]['sourceCandidate']==b['endpointChoices'][1][choice['right']]['sourceCandidate'], 'Unobserved endpoint pairing'
        assert b['id']==choice['block'] and b['inventory'] not in owners
        owners.add(b['inventory'])
        expected='/'.join(f'{x:016d}' for x in (choice['index'],choice['left'],choice['right']))
        assert choice['id']==expected and expected not in ids;ids.add(expected)
        for t in b['t']: totals[t['point']]=totals.get(t['point'],0)+t['value']
        for side,key in enumerate(('left','right')):
            i=choice[key];assert 0<=i<len(b['endpointChoices'][side])
            c=b['endpointChoices'][side][i]
            marks.setdefault(b['markPoints'][side],[]).append(source['clouds'][c['cloud']])
    assert all(0<=v<=row['capacity'] for v in totals.values())
    complete=all(v==row['capacity'] for v in totals.values())
    assert complete==run['result']['scalarComplete']
    assert len(ids)==run['result']['selected']
    assert all(len(json.loads(w['point']))==2 and json.loads(w['point'])[1]=='portable' for w in run['commonWitnesses'])
    witnesses={json.loads(w['point'])[0]:w['witness'] for w in run['commonWitnesses']}
    assert len(witnesses)==len(run['commonWitnesses'])
    checks=0
    if run['result']['markingStatus']=='verified-common-values':
        assert set(witnesses)==set(marks)
        for point,assignments in marks.items():
            for a in assignments:
                assert cloud.contains(a,witnesses[point],row['cloudRadius']) is not None
                checks+=1
    else: assert not witnesses
    supports=[{t['point'] for t in row['blocks'][c['index']]['t']} for c in run['selected']]
    remaining=set(range(len(supports)));components=0
    while remaining:
        components+=1;front=[remaining.pop()]
        while front:
            i=front.pop();neighbors={j for j in remaining if supports[i]&supports[j]}
            remaining-=neighbors;front.extend(neighbors)
    selected_blocks={c['block'] for c in run['selected']}
    same_cover=[lift['name'] for lift in row['trainingLifts'] if {c['block'] for c in lift['selected']}==selected_blocks]
    results.append({'file':row['file'],'fold':row['fold'],'selected':len(ids),'complete':complete,'verifiedAssignments':checks,'commonValues':len(witnesses),'positiveSupportComponents':components,'matchingTrainingSupportCovers':same_cover,'runHash':digest(path)})
report={'scope':__doc__,'sourceModelHash':digest(source_path),'blocksHash':digest(blocks_path),'verifierHash':digest(pathlib.Path(__file__)),'membershipModuleHash':digest(pathlib.Path(cloud.__file__)),'results':results,'limits':'Checks selected t sums, shared inventory and supplied common cloud witnesses. Does not prove continuous-pose completeness, training transfer, or material provenance.'}
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
