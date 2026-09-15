"""Replay relaxed endpoint-cylinder dead points with independent cloud matching."""
import hashlib, importlib.util, json, pathlib, sys
source_path,blocks_path,diagnostic_path,output=map(pathlib.Path,sys.argv[1:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads(source_path.read_text());data=json.loads(blocks_path.read_text());diagnostic=json.loads(diagnostic_path.read_text())
assert diagnostic['sourceModelHash']==data['sourceModelHash']==digest(source_path)
assert diagnostic['blocksHash']==digest(blocks_path)
spec=importlib.util.spec_from_file_location('cloud',pathlib.Path(__file__).with_name('portable-cloud-markings.py'));cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
results=[]
for row,record in zip(data['models'],diagnostic['results'],strict=True):
    assert (row['file'],row['fold'])==(record['file'],record['fold'])
    def decode(id):
        index,left,right=map(int,id.split('/'));assert id=='/'.join(f'{v:016d}' for v in (index,left,right))
        assert 0<=index<len(row['blocks']);b=row['blocks'][index]
        assert 0<=left<len(b['endpointChoices'][0]) and 0<=right<len(b['endpointChoices'][1])
        return b,[left,right]
    failed,indices=decode(record['failed'])
    # This pilot certifies root cylinders only; do not silently advertise a
    # parent-domain count without reconstructing that parent's legal filters.
    assert not record['prefix']
    checked=[]
    for certificate in record['cylinders']:
        if not certificate['certifiedDead']:continue
        erased=certificate['erase'];assert erased in (0,1)
        assert certificate['parentAlternatives']==len(failed['endpointChoices'][erased])
        assert certificate['keptSide']==1-erased and certificate['keptIndex']==indices[1-erased]
        totals={p:0 for p in row['required']};owners=set();marks={}
        for id in record['prefix']+[record['failed']]:
            b,choices=decode(id);assert b['inventory'] not in owners;owners.add(b['inventory'])
            for t in b['t']:totals[t['point']]=totals.get(t['point'],0)+t['value']
            for side in (0,1):
                if id==record['failed'] and side==erased:continue
                c=source['clouds'][b['endpointChoices'][side][choices[side]]['cloud']]
                marks.setdefault(b['markPoints'][side],[]).append(c)
        assert all(v<=row['capacity'] for v in totals.values())
        point=certificate['relaxedDecision']['point'];assert point in row['required'] and totals[point]<row['capacity']
        candidates=0;pair_checks=0;blocked=[]
        for b in row['blocks']:
            if not any(t['point']==point for t in b['t']):continue
            candidates+=1
            if b['inventory'] in owners:blocked.append('inventory');continue
            if any(totals.get(t['point'],0)+t['value']>row['capacity'] for t in b['t']):blocked.append('capacity');continue
            viable=[]
            for side in (0,1):
                count=0
                for choice in b['endpointChoices'][side]:
                    c=source['clouds'][choice['cloud']];possible=True
                    for a in marks.get(b['markPoints'][side],[]):
                        pair_checks+=1
                        if cloud.contains(c,a,2*row['cloudRadius']+1e-10) is None:possible=False;break
                    if possible:count+=1
                viable.append(count)
            assert viable[0]*viable[1]==0, 'Claimed dead point has a possible decorated candidate'
            blocked.append('marking')
        checked.append({'erasedSide':erased,'deadPoint':point,'incidentBlocksChecked':candidates,'pairChecks':pair_checks,'reasons':{k:blocked.count(k) for k in set(blocked)}})
    results.append({'file':row['file'],'fold':row['fold'],'certificates':checked})
report={'scope':__doc__,'sourceModelHash':digest(source_path),'blocksHash':digest(blocks_path),'diagnosticHash':digest(diagnostic_path),'verifierHash':digest(pathlib.Path(__file__)),'results':results,'limits':'Parent-local impossibility in the declared finite pool and guarded cloud predicate. Does not justify transferring exclusions to other configurations. Search remains unchanged.'}
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
