"""Learn decorated connection stars at points touched only by pair motifs.

Stars use the existing exact t/m values and observed periodic pair vectors.
They are learned hypotheses, not proved exclusions or physics-derived rules.
"""
from collections import defaultdict,Counter
from itertools import combinations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

def match(source,colors,target,target_colors,eps):
    """Finite correspondence enumeration followed by a proper rotation fit.

    A returned fit certifies the max residual; failure is not an exhaustive
    feasibility certificate for all approximate rotations under an L-infinity norm.
    """
    if Counter(map(tuple,colors))!=Counter(map(tuple,target_colors)):return None
    p=np.asarray(source);q=np.asarray(target);n=len(p)
    pd=np.linalg.norm(p[:,None]-p[None,:],axis=2);qd=np.linalg.norm(q[:,None]-q[None,:],axis=2)
    pn=np.linalg.norm(p,axis=1);qn=np.linalg.norm(q,axis=1)
    options=[[j for j in range(n) if tuple(colors[i])==tuple(target_colors[j]) and abs(pn[i]-qn[j])<=eps+1e-8] for i in range(n)]
    order=sorted(range(n),key=lambda i:len(options[i]));assignment={};used=set()
    def visit(k):
        if k==n:
            perm=[assignment[i] for i in range(n)];u,_,vt=np.linalg.svd(p.T@q[perm]);fix=np.eye(3);fix[-1,-1]=np.linalg.det(u@vt);rotation=u@fix@vt
            error=float(np.linalg.norm(p@rotation-q[perm],axis=1).max())
            return {'permutation':perm,'rotationRow':rotation.tolist(),'residual':error} if error<=eps+1e-8 else None
        i=order[k]
        for j in options[i]:
            if j in used or any(abs(pd[i,h]-qd[j,v])>2*eps+1e-8 for h,v in assignment.items()):continue
            assignment[i]=j;used.add(j);answer=visit(k+1)
            used.remove(j);del assignment[i]
            if answer is not None:return answer
        return None
    return visit(0)

def learn(d,r,folder,alternatives):
    spec=importlib.util.spec_from_file_location('compound',Path(__file__).with_name('boron-compound-proposals.py'))
    comp=importlib.util.module_from_spec(spec);spec.loader.exec_module(comp)
    geometry=comp.load_geometry(d,folder);point_data=[];training=[]
    for f,cfg in enumerate(d['configurations']):
        face=set();at=defaultdict(list);xyz=geometry[f][0]
        for j,o in enumerate(cfg['occurrences']):
            typ=d['types'][o['type']]
            if typ['kind']!='pair':face.update(o['ids']);continue
            for u,p in enumerate(o['ids']):
                a=r['roleOfSite'][typ['offset']+u];b=r['roleOfSite'][typ['offset']+1-u]
                color=[o['type'],r['weightsByRole'][a],r['weightsByRole'][b],r['scalarLabelsByRole'][a],r['scalarLabelsByRole'][b]]
                at[p].append({'candidate':j,'vector':(xyz[j][1-u]-xyz[j][u]).tolist(),'color':color})
        rows={p:edges for p,edges in at.items() if p not in face};point_data.append(rows)
        covers=[r['selected'][f]]+[run['selected'] for run in alternatives['runs'] if run['fold']==f]
        training.append([set(c) for c in covers])
    library=[];bycolors=defaultdict(list);observations=[];eps=d['epsilonAngstrom']
    for f,points in enumerate(point_data):
        for p,edges in points.items():
            seen=set()
            for ci,cover in enumerate(training[f]):
                chosen=[e for e in edges if e['candidate'] in cover];ids=tuple(e['candidate'] for e in chosen)
                if ids in seen:continue
                seen.add(ids);assert sum(e['color'][1] for e in chosen)==r['capacity']
                vectors=[e['vector'] for e in chosen];colors=[e['color'] for e in chosen];key=tuple(sorted(map(tuple,colors)))
                fit=None;li=None
                for index in bycolors[key]:
                    fit=match(library[index]['vectors'],library[index]['colors'],vectors,colors,eps)
                    if fit is not None:li=index;break
                if li is None:
                    li=len(library);library.append({'vectors':vectors,'colors':colors,'sources':[]});bycolors[key].append(li)
                    fit=match(vectors,colors,vectors,colors,eps);assert fit is not None
                source={'fold':f,'point':p,'cover':ci,'candidates':list(ids),'fit':fit}
                library[li]['sources'].append(source);observations.append((f,p,li))
        print(json.dumps({'trainingFold':f,'libraryClasses':len(library),'observations':len(observations)}),flush=True)
    folds=[]
    for f,points in enumerate(point_data):
        nodes=[];subset_tests=0
        for p,edges in sorted(points.items()):
            states=[]
            for size in range(1,len(edges)+1):
                for selected in combinations(edges,size):
                    if sum(e['color'][1] for e in selected)!=r['capacity']:continue
                    colors=[e['color'] for e in selected];key=tuple(sorted(map(tuple,colors)))
                    vectors=[e['vector'] for e in selected];subset_tests+=1;witnesses=[]
                    for li in bycolors[key]:
                        template=library[li];fit=match(template['vectors'],template['colors'],vectors,colors,eps)
                        if fit is not None:witnesses.append({'library':li,**fit})
                    if witnesses:states.append({'candidates':[e['candidate'] for e in selected],'witnesses':witnesses,
                                              'sourceFolds':sorted({s['fold'] for w in witnesses for s in library[w['library']]['sources']})})
            assert states,('training point has no learned star',f,p)
            for cover in training[f]:assert any(set(s['candidates'])=={e['candidate'] for e in edges if e['candidate'] in cover} for s in states)
            nodes.append({'point':p,'incident':edges,'states':states})
        bypoint={n['point']:n for n in nodes};copies=0;excluded=0
        for j,o in enumerate(d['configurations'][f]['occurrences']):
            multiplicity=1
            for p in o['ids']:
                if p in bypoint:multiplicity*=sum(j in s['candidates'] for s in bypoint[p]['states'])
            copies+=multiplicity;excluded+=multiplicity==0
        folds.append({'fold':f,'file':d['configurations'][f]['file'],'nodes':nodes,'subsetTests':subset_tests,
                      'expandedCandidateCount':copies,'excludedBaseCandidates':excluded})
        print(json.dumps({'fold':f,'junctionPoints':len(nodes),'states':sum(len(n['states']) for n in nodes),
                          'multipleStatePoints':sum(len(n['states'])>1 for n in nodes),'expandedCandidates':copies,'excludedBaseCandidates':excluded}),flush=True)
    return {'scope':__doc__,'epsilonAngstrom':eps,'library':library,'folds':folds,
            'limits':['Only points with no incident face motif are constrained.',
                      'All configurations contribute to the base dictionary, t/m and junction library.',
                      'Training uses original and alternative covers; unobserved legal covers may be excluded.',
                      'Observed finite poses only; no blind growth or complete continuous correspondence claim.']}

if __name__=='__main__':
    inp,learned,folder,alt,out=map(Path,sys.argv[1:6]);d=json.loads(inp.read_text());lr=json.loads(learned.read_text());a=json.loads(alt.read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert lr['inputHash']==a['inputHash']==digest(inp) and a['learningHash']==digest(learned)
    original_only=sys.argv[6:] == ['--original-only'];assert not sys.argv[6:] or original_only
    result=learn(d,lr['result'],folder,{'runs':[]} if original_only else a)
    if original_only:result['trainingPolicy']='six-original-fillings'
    result.update(inputHash=digest(inp),learningHash=digest(learned),alternativeHash=digest(alt))
    with out.open('x') as f:json.dump(result,f)
