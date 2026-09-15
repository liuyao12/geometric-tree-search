"""Independent necessary-support propagation using verified conservative adjacency.

No cloud-distance calculation: an empty domain even in this larger adjacency
model certifies failure of the declared finite paired model, not the material.
"""
import hashlib
import json
from pathlib import Path
import sys
import argparse
import importlib.util
from functools import lru_cache

parser=argparse.ArgumentParser();parser.add_argument('directory',type=Path);parser.add_argument('output',type=Path)
parser.add_argument('--relation',type=Path);parser.add_argument('--relation-check',type=Path)
parser.add_argument('--full-cloud',action='store_true')
args=parser.parse_args();directory,output=args.directory,args.output
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
if args.full_cloud:
    spec=importlib.util.spec_from_file_location('cloud',Path(__file__).with_name('portable-cloud-markings.py'))
    cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)
relation=read(args.relation) if args.relation else None
if relation:
    assert args.relation_check and read(args.relation_check)['relationHash']==sha(args.relation)
for phase in ['Ih','II','VI']:
    path=directory/phase
    data=read(path/'filtered.json'); index=read(path/'index.json'); check=read(path/'index-check.json')
    full_source=read(path/'source.json') if args.full_cloud else None
    if full_source:assert data['sourceModelHash']==sha(path/'source.json')
    if relation:assert read(path/'source.json')['portableHash']==relation['libraryHash']
    assert check['indexHash']==sha(path/'index.json')
    assert check['blocksHash']==index['blocksHash']==sha(path/'filtered.json')
    for model, graph in zip(data['models'],index['models'],strict=True):
        assert model['file']==graph['file'] and model['capacity']==2
        blocks=model['blocks']; record_id={tuple(r):i for i,r in enumerate(graph['records'])}
        @lru_cache(maxsize=300000)
        def compatible_clouds(a,b):
            return cloud.contains(full_source['clouds'][a],full_source['clouds'][b],2*model['cloudRadius']+1e-8) is not None
        candidates=[]; owners={}
        for bi,b in enumerate(blocks):
            assert all(t['value']==1 for t in b['t'])
            right={c['sourceCandidate']:j for j,c in enumerate(b['endpointChoices'][1])}
            assert len(right)==len(b['endpointChoices'][1])
            for i,c in enumerate(b['endpointChoices'][0]):
                if relation:
                    permitted=set(relation['neighbors'][c['sourceMotif']])
                    js=[j for j,d in enumerate(b['endpointChoices'][1]) if d['sourceMotif'] in permitted]
                else:js=[right[c['sourceCandidate']]] if c['sourceCandidate'] in right else []
                for j in js:
                    ends=[record_id[bi,0,i],record_id[bi,1,j]]
                    ci=len(candidates);candidates.append((bi,ends))
                    for endpoint in ends:owners.setdefault(endpoint,set()).add(ci)
        # Establish that each marking anchor requires exactly two incident
        # placements in any full filling, using a positive-support witness.
        for point in {p for b in blocks for p in b['markPoints']}:
            incident={i for i,b in enumerate(blocks) if point in b['markPoints']}
            assert any({i for i,b in enumerate(blocks) if any(t['point']==p for t in b['t'])}==incident for p in model['required'])
        # Share endpoint support instead of expanding the Cartesian set of
        # partner candidates. Existence at a live endpoint means at least one
        # live paired candidate contains it; candidate identities remain intact.
        adjacency={}
        for e in owners:
            bi,side,_=graph['records'][e];supported=set()
            for other in graph['neighbors'][e]:
                if other not in owners:continue
                bj,os,_=graph['records'][other]
                assert blocks[bi]['markPoints'][side]==blocks[bj]['markPoints'][os]
                if blocks[bi]['inventory']!=blocks[bj]['inventory']:
                    if args.full_cloud:
                        a=blocks[bi]['endpointChoices'][side][graph['records'][e][2]]['cloud']
                        b=blocks[bj]['endpointChoices'][os][graph['records'][other][2]]['cloud']
                        if not compatible_clouds(min(a,b),max(a,b)):continue
                    supported.add(other)
            adjacency[e]=supported
        live=set(range(len(candidates)));passes=0
        while True:
            active_endpoints={e for i in live for e in candidates[i][1]}
            supported={e for e in active_endpoints if adjacency[e]&active_endpoints}
            removed={i for i in live if any(e not in supported for e in candidates[i][1])}
            if not removed:break
            live-=removed;passes+=1
        covered={t['point'] for i in live for t in blocks[candidates[i][0]]['t']}
        dead=sorted(set(model['required'])-covered)
        rows.append(dict(phase=phase,file=model['file'],initialPairs=len(candidates),remainingPairs=len(live),
                         passes=passes,deadRequiredPoints=dead,restrictedRootFailureCertified=bool(dead),
                         blocksHash=sha(path/'filtered.json'),indexHash=sha(path/'index.json'),indexCheckHash=sha(path/'index-check.json')))
report=dict(scope=__doc__,results=rows,codeHash=sha(Path(__file__)),
            limits='Relies on separately verified complete conservative index and prior factorized preprocessing. No conclusion from a nonempty fixed point. Does not certify floating-point geometric exactness or impossibility outside the paired finite learned hypothesis.')
if args.full_cloud:report.update(fullCloud=True,scope='Independent necessary-support propagation with full colored-cloud matching at a conservatively padded two-radius threshold.',cloudModuleHash=sha(Path(cloud.__file__)))
if relation:
    report.update(relationHash=sha(args.relation),relationCheckHash=sha(args.relation_check),
                  scope='Independent necessary-support propagation for the one-step geometric substitution relation, using verified conservative adjacency.',
                  limits='Conditional on the complete conservative index and prior factorized preprocessing. Root failure applies only to this finite learned substitution hypothesis. Nonempty support proves neither a filling nor actual cloud compatibility.',
                  hypothesis='One-step geometric endpoint substitution, not exact pairing. Nonempty conservative support does not prove a filling or actual cloud compatibility.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps([dict(phase=r['phase'],file=r['file'],initial=r['initialPairs'],remaining=r['remainingPairs'],dead=len(r['deadRequiredPoints'])) for r in rows]))
