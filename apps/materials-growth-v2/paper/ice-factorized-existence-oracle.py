"""Positive-witness existence diagnostic, NOT the reference tree-search benchmark.

Independent endpoint choices let a pair of selected blocks choose one verified
common cloud at each anchor. A binary feasibility model coordinates these local
pairs. Any positive result is lifted to full decorated candidates for replay.
Missing witnesses or solver failure never prove the original model impossible.
"""
import collections,hashlib,importlib.util,json,pathlib,sys,time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import lil_matrix
source_path,blocks_path,index_path,index_check_path,directory=map(pathlib.Path,sys.argv[1:6])
assert sys.argv[6:] in ([],['--connected'])
connected=bool(sys.argv[6:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads(source_path.read_text());data=json.loads(blocks_path.read_text());index=json.loads(index_path.read_text());check=json.loads(index_check_path.read_text())
assert index['sourceModelHash']==digest(source_path) and index['blocksHash']==digest(blocks_path) and check['indexHash']==digest(index_path)
spec=importlib.util.spec_from_file_location('cloud',pathlib.Path(__file__).with_name('portable-cloud-markings.py'));cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
directory.mkdir();results=[]
for row,graph in zip(data['models'],index['models'],strict=True):
    start=time.monotonic();blocks=row['blocks'];n=len(blocks);pairs={};tested=0
    assert row['capacity']==2 and all(t['value']==1 for b in blocks for t in b['t'])
    for a,neighbors in enumerate(graph['neighbors']):
        i,side,j=graph['records'][a];b=blocks[i];point=b['markPoints'][side]
        for other in neighbors:
            if other<=a:continue
            k,s,l=graph['records'][other];c=blocks[k]
            assert c['markPoints'][s]==point and b['inventory']!=c['inventory']
            key=(point,min(i,k),max(i,k))
            if key in pairs:continue
            ca=source['clouds'][b['endpointChoices'][side][j]['cloud']];cb=source['clouds'][c['endpointChoices'][s][l]['cloud']];tested+=1
            witness=cloud.propose_common_witness([ca,cb],row['cloudRadius'])
            if witness['status']=='verified-witness':pairs[key]={'point':point,'ends':[[i,side,j],[k,s,l]],'witness':witness['witness']}
    values=list(pairs.values());anchors=sorted({p for b in blocks for p in b['markPoints']});constraints=[];lower=[];upper=[]
    def add(entries,lo,hi):constraints.append(entries);lower.append(lo);upper.append(hi)
    for point in row['required']:add({i:1 for i,b in enumerate(blocks) if any(t['point']==point for t in b['t'])},2,2)
    for inventory in {b['inventory'] for b in blocks}:add({i:1 for i,b in enumerate(blocks) if b['inventory']==inventory},0,1)
    for point in anchors:
        add({n+j:1 for j,p in enumerate(values) if p['point']==point},1,1)
        for i,b in enumerate(blocks):
            if point not in b['markPoints']:continue
            entries={i:-1};entries.update({n+j:1 for j,p in enumerate(values) if p['point']==point and any(end[0]==i for end in p['ends'])});add(entries,0,0)
    compile_seconds=time.monotonic()-start;solve_start=time.monotonic()
    cuts=0;accepted=False
    while time.monotonic()-solve_start<30:
        matrix=lil_matrix((len(constraints),n+len(values)))
        for r,entries in enumerate(constraints):
            for col,v in entries.items():matrix[r,col]=v
        answer=milp(np.zeros(n+len(values)),integrality=np.ones(n+len(values)),bounds=Bounds(0,1),constraints=LinearConstraint(matrix.tocsr(),lower,upper),options={'time_limit':max(.01,30-(time.monotonic()-solve_start))})
        if answer.x is None:break
        chosen={i for i in range(n) if answer.x[i]>.5};components=[]
        while chosen:
            first=chosen.pop();atoms={t['point'] for t in blocks[first]['t']};pending=True
            while pending:
                touching={i for i in chosen if atoms&{t['point'] for t in blocks[i]['t']}}
                pending=bool(touching)
                for i in touching:atoms.update(t['point'] for t in blocks[i]['t'])
                chosen-=touching
            components.append(atoms)
        if not connected or len(components)==1:accepted=True;break
        # Optional connected-cover question only. Every connected cover must
        # cross each nontrivial atom partition from the disconnected witness.
        for atoms in components:
            crossing={i:1 for i,b in enumerate(blocks) if atoms&{t['point'] for t in b['t']} and {t['point'] for t in b['t']}-atoms}
            add(crossing,1,np.inf);cuts+=1
    solve_seconds=time.monotonic()-solve_start;selected=[];witnesses=[]
    if accepted:
        x=np.rint(answer.x).astype(int);assert np.max(np.abs(x-answer.x))<1e-5
        actual=matrix@x;assert np.all(actual>=np.array(lower)) and np.all(actual<=np.array(upper))
        choices={i:[None,None] for i in range(n) if x[i]}
        for j,p in enumerate(values):
            if not x[n+j]:continue
            witnesses.append({'point':json.dumps([p['point'],'portable']),'witness':p['witness']})
            for i,side,k in p['ends']:assert choices[i][side] is None;choices[i][side]=k
        for i,(a,b) in choices.items():
            assert a is not None and b is not None
            selected.append({'id':'/'.join(f'{v:016d}' for v in (i,a,b)),'index':i,'block':blocks[i]['id'],'left':a,'right':b})
    result={'file':row['file'],'fold':row['fold'],'solver':'scipy-milp-positive-existence-oracle','referenceSearch':False,'connectedCoverRequested':connected,'connectivityCuts':cuts,'compileSeconds':compile_seconds,'solveSeconds':solve_seconds,'witnessPairs':len(values),'testedPairs':tested,'solverStatus':int(answer.status),'selected':len(selected),'scalarComplete':bool(selected),'markingStatus':'verified-common-values' if selected else 'unknown','commonValues':len(witnesses),'status':'complete-awaiting-independent-verification' if selected else 'unknown-original-model'}
    payload={'sourceModelHash':digest(source_path),'blocksHash':digest(blocks_path),'indexHash':digest(index_path),'oracleHash':digest(pathlib.Path(__file__)),'result':result,'selected':selected,'commonWitnesses':witnesses}
    with (directory/f"{row['fold']}.json").open('x') as f:json.dump(payload,f)
    results.append(result);print(json.dumps(result),flush=True)
with (directory/'summary.json').open('x') as f:json.dump({'scope':__doc__,'sourceModelHash':digest(source_path),'blocksHash':digest(blocks_path),'results':results,'limits':'Positive witnesses only. Optional connected-cover query is explicitly separate from the base point-value model. No reference-search speedup, continuous-pose completeness or negative impossibility claim.'},f,indent=2)
