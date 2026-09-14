"""Learn site-resolved scalar decorations and enumerate witnessed self-orientations.

All six selected fillings train; fixed observed atom-ID pool, not blind growth.
t keeps its original symmetry ties; m need not share them. This is a restricted
decorated-pose experiment, not exhaustive continuous pose enumeration.
"""
import hashlib
import json
import sys
from pathlib import Path


def labels(n,edges):
    graph=[set() for _ in range(n)]
    for a,b in edges:graph[a].add(b);graph[b].add(a)
    out=[None]*n;next_label=0
    for root in range(n):
        if out[root] is not None:continue
        out[root]=next_label;todo=[root]
        while todo:
            a=todo.pop()
            for b in graph[a]:
                if out[b] is None:out[b]=next_label;todo.append(b)
        next_label+=1
    return out


inp,learned,dest=map(Path,sys.argv[1:])
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result']
n=sum(len(t['positions']) for t in d['types']);edges=[]
for cfg,selected in zip(d['configurations'],r['selected']):
    groups=[[] for _ in range(cfg['atoms'])]
    for j in selected:
        o=cfg['occurrences'][j];offset=d['types'][o['type']]['offset']
        for u,p in enumerate(o['ids']):groups[p].append(offset+u)
    for group in groups:
        assert group
        edges.extend((group[0],v) for v in group[1:])
site_labels=labels(n,edges)
sym_edges=[(t['offset']+a,t['offset']+b) for t in d['types'] for a,b in t['ties']]
tied=labels(n,edges+sym_edges)
old=[r['scalarLabelsByRole'][q] for q in r['roleOfSite']]
assert all((tied[a]==tied[b])==(old[a]==old[b]) for a in range(n) for b in range(n))
models=[]
for fold,cfg in enumerate(d['configurations']):
    unmarked=[];marked=[];identity=[];variant_counts=[]
    for j,o in enumerate(cfg['occurrences']):
        typ=d['types'][o['type']];offset=typ['offset'];size=len(o['ids'])
        t=[{'point':str(p),'value':r['weightsByRole'][r['roleOfSite'][offset+u]]} for u,p in enumerate(o['ids'])]
        unmarked.append({'id':str(j).zfill(6),'t':t,'m':[]})
        perms=[list(range(size))]+[w['permutation'] for w in typ['selfFits']]
        if typ['kind']!='finite-face':perms.append([1,0])
        seen=set();count=0
        for perm in perms:
            assert sorted(perm)==list(range(size))
            assert all(r['weightsByRole'][r['roleOfSite'][offset+u]]==r['weightsByRole'][r['roleOfSite'][offset+v]] for u,v in enumerate(perm))
            m=sorted([{'point':str(o['ids'][v]),'lo':site_labels[offset+u],'hi':site_labels[offset+u]} for u,v in enumerate(perm)],key=lambda x:int(x['point']))
            key=tuple((x['point'],x['lo']) for x in m)
            if key in seen:continue
            seen.add(key);cid=f'{j:06d}:{count:03d}'
            if count==0:identity.append(cid)
            marked.append({'id':cid,'t':t,'m':m});count+=1
        variant_counts.append(count)
    models.append({'fold':fold,'file':cfg['file'],'capacity':r['capacity'],'required':[str(p) for p in range(cfg['atoms'])],
                   'unmarked':unmarked,'marked':marked,'trainingSelected':[identity[j] for j in r['selected'][fold]],
                   'variantCounts':variant_counts})
out={'scope':__doc__,'inputHash':hashlib.sha256(inp.read_bytes()).hexdigest(),'learningHash':hashlib.sha256(learned.read_bytes()).hexdigest(),
     'siteVariables':n,'siteClasses':len(set(site_labels)),'symmetryTiedClasses':len(set(tied)),
     'siteLabels':site_labels,'models':models}
dest.write_text(json.dumps(out)+'\n')
print(json.dumps({'siteVariables':n,'siteClasses':len(set(site_labels)),'symmetryTiedClasses':len(set(tied)),
                 'models':[{'file':m['file'],'physicalCandidates':len(m['unmarked']),'decoratedCandidates':len(m['marked'])} for m in models]},indent=2))
