"""Learn co-occurrence of geometric junction classes across selected pair motifs.

Class-only connection hypothesis; relative frame/port coupling is not learned.
All original and alternative training decompositions must remain representable.
"""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

inp,learned,alt,junction_path,out=map(Path,sys.argv[1:])
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];alternatives=json.loads(alt.read_text());j=json.loads(junction_path.read_text())
assert j['inputHash']==digest(inp) and j['learningHash']==digest(learned) and j['alternativeHash']==digest(alt)
classes={}
for li,entry in enumerate(j['library']):
    for source in entry['sources']:
        key=(source['fold'],source['point'],tuple(sorted(source['candidates'])))
        assert key not in classes;classes[key]=li
rules=defaultdict(set);covers=[]
for f,cfg in enumerate(d['configurations']):
    nodes={n['point']:n for n in j['folds'][f]['nodes']}
    records=[r['selected'][f]]+[x['selected'] for x in alternatives['runs'] if x['fold']==f];covers.append(records)
    for ci,selected in enumerate(records):
        chosen=set(selected);labels={p:classes[f,p,tuple(sorted(chosen&{e['candidate'] for e in n['incident']}))] for p,n in nodes.items()}
        for candidate in selected:
            o=cfg['occurrences'][candidate]
            if len(o['ids'])!=2 or not all(p in nodes for p in o['ids']):continue
            a,b=(labels[p] for p in o['ids']);rules[o['type'],a,b].add((f,ci))
            typ=d['types'][o['type']];u,v=[r['roleOfSite'][typ['offset']+k] for k in range(2)]
            if (r['weightsByRole'][u],r['scalarLabelsByRole'][u])==(r['weightsByRole'][v],r['scalarLabelsByRole'][v]):rules[o['type'],b,a].add((f,ci))
folds=[]
for f,cfg in enumerate(d['configurations']):
    nodes={n['point']:n for n in j['folds'][f]['nodes']};edges=[]
    for candidate,o in enumerate(cfg['occurrences']):
        if len(o['ids'])!=2 or not all(p in nodes for p in o['ids']):continue
        p,q=o['ids'];left=nodes[p];right=nodes[q];allowed=[];witnesses=[]
        for a,sa in enumerate(left['states']):
            if candidate not in sa['candidates']:continue
            for b,sb in enumerate(right['states']):
                if candidate not in sb['candidates']:continue
                witness=next(((wa['library'],wb['library']) for wa in sa['witnesses'] for wb in sb['witnesses'] if (o['type'],wa['library'],wb['library']) in rules),None)
                if witness is not None:allowed.append([a,b]);witnesses.append(list(witness))
        edges.append({'candidate':candidate,'points':[p,q],'type':o['type'],'allowedPresentStates':allowed,'classWitnesses':witnesses})
    checked=0
    for selected in covers[f]:
        chosen=set(selected);labels={}
        for p,n in nodes.items():
            actual=chosen&{e['candidate'] for e in n['incident']}
            labels[p]=next(i for i,s in enumerate(n['states']) if set(s['candidates'])==actual)
        for edge in edges:
            if edge['candidate'] not in chosen:continue
            assert [labels[p] for p in edge['points']] in edge['allowedPresentStates'];checked+=1
    fold={'fold':f,'file':cfg['file'],'edges':edges,'trainingConnectionsChecked':checked,
          'candidatePairsWithNoObservedClassConnection':sum(not e['allowedPresentStates'] for e in edges),
          'allowedStatePairs':sum(len(e['allowedPresentStates']) for e in edges)}
    folds.append(fold);print(json.dumps({k:v for k,v in fold.items() if k!='edges'}),flush=True)
result={'scope':__doc__,'inputHash':digest(inp),'learningHash':digest(learned),'alternativeHash':digest(alt),'junctionHash':digest(junction_path),
        'rules':[{'type':t,'leftClass':a,'rightClass':b,'sourceRecords':[list(s) for s in sorted(sources)]} for (t,a,b),sources in sorted(rules.items())],
        'folds':folds,'limits':['Class witnesses may differ between neighbors when tolerance classes overlap.',
                              'No relative frame or port correspondence is imposed beyond existing geometric fits.',
                              'Only connections between two pair-only junction points are constrained.',
                              'Rules are learned restrictions, not proved necessary for every original filling.']}
with out.open('x') as f:json.dump(result,f)
print(json.dumps({'directedClassConnectionRules':len(rules)}))
