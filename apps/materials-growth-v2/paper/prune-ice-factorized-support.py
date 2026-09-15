import copy,hashlib,importlib.util,json,pathlib,sys,time
source_path,blocks_path,output,proof_path=map(pathlib.Path,sys.argv[1:5])
assert sys.argv[5:] in ([],['--full-cloud'])
full_cloud=bool(sys.argv[5:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('support',pathlib.Path(__file__).with_name('factorized-complement-support.py'));support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
source=json.loads(source_path.read_text());data=json.loads(blocks_path.read_text());assert data['sourceModelHash']==digest(source_path)
filtered=copy.deepcopy(data);reports=[];proofs=[]
for row,new in zip(data['models'],filtered['models']):
    start=time.monotonic();proof=support.prune(row,source['clouds'],full_cloud=full_cloud);proofs.append(proof)
    lookup={};before=0;after=0
    for i,(b,c) in enumerate(zip(row['blocks'],new['blocks'])):
        before+=len(b['endpointChoices'][0])*len(b['endpointChoices'][1])
        c['endpointChoices']=[[dict(b['endpointChoices'][side][j],originalIndex=j) for j in proof['allowed'][i][side]] for side in (0,1)]
        c['candidateCount']=str(len(c['endpointChoices'][0])*len(c['endpointChoices'][1]));after+=int(c['candidateCount'])
        lookup[b['id']]=[{j:k for k,j in enumerate(proof['allowed'][i][side])} for side in (0,1)]
    for lift in new['trainingLifts']:
        for c in lift['selected']:
            maps=lookup[c['block']];c['left']=maps[0][c['left']];c['right']=maps[1][c['right']]
    report={'file':row['file'],'fold':row['fold'],'before':str(before),'after':str(after),'removedEndpointRecords':len(proof['removals']),'passes':proof['passes'],'trainingLiftsPreserved':len(new['trainingLifts']),'seconds':time.monotonic()-start,'fullCloud':full_cloud,'pairChecks':proof['pairChecks']};reports.append(report);print(json.dumps(report),flush=True)
filtered['supportPreprocessing']={'originalBlocksHash':digest(blocks_path),'moduleHash':digest(pathlib.Path(support.__file__)),'reports':reports,'scope':'Necessary complement pruning of a finite half-weight model; fullCloud identifies optional bijection checks. Survivors retain original cloud values. Not new learned markings.'}
with output.open('x') as f:json.dump(filtered,f)
with proof_path.open('x') as f:json.dump({'originalBlocksHash':digest(blocks_path),'sourceModelHash':digest(source_path),'filteredHash':digest(output),'proofs':proofs,'reports':reports},f)
