"""Learn joint geometry of neighboring junctions, including their relative frame.

One proper rotation must fit the entire two-junction neighborhood. The rooted
connecting vector is distinguished; arm indices are not geometric features.
This is a restricted observed-connection hypothesis, not redundant pruning.
"""
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def joined(left, sa, right, sb, candidate):
    """Both stars in the left root's frame, with opaque side/color labels."""
    le={e['candidate']:e for e in left['incident']}
    re={e['candidate']:e for e in right['incident']}
    delta=np.asarray(le[candidate]['vector'])
    assert np.linalg.norm(delta+re[candidate]['vector'])<1e-7
    vectors=[delta.tolist()];colors=[[-1]]
    for side,node,state in [(0,le,sa),(1,re,sb)]:
        for cid in state['candidates']:
            e=node[cid]
            vectors.append((np.asarray(e['vector'])+(delta if side else 0)).tolist())
            colors.append([side,*e['color']])
    return vectors,colors

def fit_valid(source, target, fit, epsilon):
    p=np.asarray(source);q=np.asarray(target);rot=np.asarray(fit['rotationRow'])
    return bool(np.linalg.norm(p@rot-q[fit['permutation']],axis=1).max()<=epsilon+1e-8)

def main():
    inp,learned,alt,junction_path,connection_path,out=map(Path,sys.argv[1:])
    d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result']
    alternatives=json.loads(alt.read_text());j=json.loads(junction_path.read_text());old=json.loads(connection_path.read_text())
    for key,path in [('inputHash',inp),('learningHash',learned),('alternativeHash',alt),('junctionHash',junction_path)]:
        assert old[key]==digest(path)
    spec=importlib.util.spec_from_file_location('junction_learner',Path(__file__).with_name('boron-junction-learning.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    epsilon=j['epsilonAngstrom'];library=[];groups=defaultdict(list);classes={};covers=[]
    for li,entry in enumerate(j['library']):
        for source in entry['sources']:
            classes[source['fold'],source['point'],frozenset(source['candidates'])]=li
    allnodes=[{n['point']:n for n in fold['nodes']} for fold in j['folds']]
    for f,cfg in enumerate(d['configurations']):
        nodes=allnodes[f];records=[r['selected'][f]]+[x['selected'] for x in alternatives['runs'] if x['fold']==f];covers.append(records)
        for ci,record in enumerate(records):
            chosen=set(record);labels={p:next(i for i,s in enumerate(n['states']) if set(s['candidates'])==chosen&{e['candidate'] for e in n['incident']}) for p,n in nodes.items()}
            for cid in record:
                o=cfg['occurrences'][cid]
                if len(o['ids'])!=2 or not all(p in nodes for p in o['ids']):continue
                typ=d['types'][o['type']];roles=r['roleOfSite'][typ['offset']:typ['offset']+2]
                reversible=len({(r['weightsByRole'][u],r['scalarLabelsByRole'][u]) for u in roles})==1
                for reverse in range(2 if reversible else 1):
                    p,q=o['ids'][::(-1 if reverse else 1)];left,right=nodes[p],nodes[q]
                    sa,sb=left['states'][labels[p]],right['states'][labels[q]]
                    key=(o['type'],classes[f,p,frozenset(sa['candidates'])],classes[f,q,frozenset(sb['candidates'])])
                    vectors,colors=joined(left,sa,right,sb,cid);fit=None;index=None
                    for li in groups[key]:
                        entry=library[li];fit=mod.match(entry['vectors'],entry['colors'],vectors,colors,epsilon)
                        if fit is not None:index=li;break
                    if index is None:
                        index=len(library);groups[key].append(index)
                        library.append({'key':list(key),'vectors':vectors,'colors':colors,'sources':[]})
                        fit=mod.match(vectors,colors,vectors,colors,epsilon);assert fit
                    library[index]['sources'].append({'fold':f,'cover':ci,'candidate':cid,'points':[p,q],'states':[labels[p],labels[q]],'fit':fit})
        print(json.dumps({'trainingFold':f,'jointTemplates':len(library)}),flush=True)
    folds=[];fit_tests=0;cache={}
    for f,cfg in enumerate(d['configurations']):
        nodes=allnodes[f];edges=[]
        for oldedge in old['folds'][f]['edges']:
            cid=oldedge['candidate'];left,right=[nodes[p] for p in oldedge['points']]
            allowed=[];witnesses=[];geometric=[]
            for a,b in oldedge['allowedPresentStates']:
                sa,sb=left['states'][a],right['states'][b];vectors,colors=joined(left,sa,right,sb,cid)
                keys=sorted({(oldedge['type'],wa['library'],wb['library']) for wa in sa['witnesses'] for wb in sb['witnesses']})
                answer=None
                for key in keys:
                    # Rounded coordinates only index a cache. Every cached positive
                    # fit is rechecked on the unrounded target; negatives are not cached.
                    cachekey=(key,tuple(map(tuple,colors)),tuple(np.asarray(vectors).round(9).ravel()))
                    if cachekey in cache:
                        li,fit=cache[cachekey]
                        if fit_valid(library[li]['vectors'],vectors,fit,epsilon):answer=(li,fit);break
                    for li in groups[key]:
                        entry=library[li];fit_tests+=1
                        fit=mod.match(entry['vectors'],entry['colors'],vectors,colors,epsilon)
                        if fit is not None:answer=(li,fit);cache[cachekey]=answer;break
                    if answer:break
                if answer:
                    li,fit=answer;allowed.append([a,b]);witnesses.append(library[li]['key'][1:]);geometric.append({'template':li,**fit})
            edges.append({**oldedge,'allowedPresentStates':allowed,'classWitnesses':witnesses,'geometricWitnesses':geometric})
        checked=0
        for record in covers[f]:
            chosen=set(record);labels={p:next(i for i,s in enumerate(n['states']) if set(s['candidates'])==chosen&{e['candidate'] for e in n['incident']}) for p,n in nodes.items()}
            for edge in edges:
                if edge['candidate'] in chosen:
                    assert [labels[p] for p in edge['points']] in edge['allowedPresentStates'],('training rejected',f,edge['candidate'])
                    checked+=1
        row={'fold':f,'file':cfg['file'],'edges':edges,'trainingConnectionsChecked':checked,'allowedStatePairs':sum(len(e['allowedPresentStates']) for e in edges),'candidatePairsWithNoObservedClassConnection':sum(not e['allowedPresentStates'] for e in edges)}
        folds.append(row);print(json.dumps({k:v for k,v in row.items() if k!='edges'}),flush=True)
    result={k:old[k] for k in ['inputHash','learningHash','alternativeHash','junctionHash']}
    result.update(scope=__doc__,classConnectionHash=digest(connection_path),epsilonAngstrom=epsilon,library=library,folds=folds,fitTests=fit_tests,
                  limits=['All six input structures and generated alternatives are training data.','Only pair-only junctions are constrained.','Local geometric witnesses may differ across adjacent edges; no global latent frame assignment is asserted.','A rejected approximate registration is not an infeasibility proof for continuous rotations.'])
    with out.open('x') as stream:json.dump(result,stream)
    print(json.dumps({'templates':len(library),'fitTests':fit_tests}),flush=True)

if __name__=='__main__':main()
