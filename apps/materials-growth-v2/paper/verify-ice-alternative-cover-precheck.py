"""Replay alternative t-covers and frozen-marking positive witnesses independently.

Rebuilds observed clouds independently, checks every accepted endpoint, and
replays every degree-preserving swap and verifies exact t coverage. Does not
certify completeness of the new endpoint match lists or blind generalization.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import linear_sum_assignment
import networkx as nx

def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('geometry',Path(__file__).with_name('verify-ice-portable.py'))
geometry=importlib.util.module_from_spec(spec);spec.loader.exec_module(geometry)
coords,cover_path,dictionary_path,selection_path,library_path,paired_path,alternative_path,result_path,output=sys.argv[1:]
corpus,cover,dictionary,selection,library,paired,data=map(read,[coords,cover_path,dictionary_path,selection_path,library_path,paired_path,result_path])
for key,path in zip(['coordinates','cover','dictionary','selection'],[coords,cover_path,dictionary_path,selection_path]):
    assert data['sourceHashes'][key]==library['sourceHashes'][key]==sha(path)
assert data['portableHash']==paired['portableHash']==sha(library_path)
for name,digest in data['codeHashes'].items():assert sha(Path(__file__).with_name(name))==digest
cv={r['id']:r for r in cover['results']};dc={r['id']:r for r in dictionary['configurations']}
ss={r['id']:r for r in selection['results']};rr={r['id']:r for r in data['results']};pr={r['id']:r for r in paired['results']}
alternative=read(alternative_path)
assert data['alternativeCoverHash']==sha(alternative_path)
assert alternative['originalSelectionHash']==sha(selection_path) and alternative['coverHash']==sha(cover_path) and alternative['dictionaryHash']==sha(dictionary_path)
assert alternative['codeHash']==sha(Path(__file__).with_name('ice-alternative-training-covers.py'))
original_selection=ss
ss={r['id']:r for r in alternative['results']}
expected={c['id'] for c in corpus['configurations'] if dc[c['id']]['training']}
assert set(rr)==set(ss)==expected and len(rr)==len(data['results'])==len(expected)
swap_count=0;changed=0
for cid,row in ss.items():
    pairs=cv[cid]['componentPairs'];selected=set(original_selection[cid]['selected'])
    def check_cover(chosen):
        graph=nx.Graph();graph.add_nodes_from(range(len(cv[cid]['components'])))
        totals=[0]*dc[cid]['atoms']
        for e in chosen:
            assert dc[cid]['occurrences'][e]['matched']
            graph.add_edge(*pairs[e])
            for atom in dc[cid]['occurrences'][e]['ids']:totals[atom]+=1
        assert nx.is_connected(graph) and all(degree==2 for _,degree in graph.degree)
        assert all(value==2 for value in totals)
    check_cover(selected)
    for swap in row['swaps']:
        before=set(swap['remove']);after=set(swap['add'])
        assert len(before)==len(after)==2 and before<=selected and not after&selected
        selected=(selected-before)|after
        check_cover(selected);swap_count+=1
    assert selected==set(row['selected']) and len(selected)==len(row['selected'])
    changed+=selected!=set(original_selection[cid]['selected'])
origins=defaultdict(set)
for row in library['trainingRegistrations']:
    assert dc[row['id']]['training']
    for item in row['selected']:origins[item['motif']].add(row['id'])
count=0;max_residual=0.;summaries=[]
for conf in corpus['configurations']:
    cid=conf['id']
    if cid not in expected:continue
    row=rr[cid];selected=ss[cid]['selected']
    clouds,_=geometry.local_clouds(conf,cv[cid],selected)
    assert row['training']==dc[cid]['training']
    assert [r['edge'] for r in row['registrations']]==selected
    prior={r['edge']:r for r in pr[cid]['registrations']}
    coupled=0;factorized=0;external=0
    for item in row['registrations']:
        occurrence=dc[cid]['occurrences'][item['edge']]
        ends=geometry.ends(occurrence,cv[cid]['components'],cv[cid]['componentPairs'][item['edge']])
        assert item['roots']==[root for _,root in ends]
        rotation=geometry.proper(occurrence['rotationRow'])
        a,b=item['endpointMatches'];assert len(a)==len(set(a)) and len(b)==len(set(b))
        assert item['coupledMatches']==sorted(set(a)&set(b))
        assert item['factorized']==bool(a and b)
        assert item['otherConfigurationFactorized']==all(any(origins[mi]-{cid} for mi in side) for side in [a,b])
        for side,ids in enumerate([a,b]):
            query=clouds[ends[side][1]]
            for mi in ids:
                motif=library['motifs'][mi];base=library['baseMotifs'][motif['base']]
                assert motif['base']==item['base'] and base['pairType']==occurrence['type']
                assert base['componentSites']==[sites for sites,_ in ends]
                mark=motif['cloudM'][side];vectors=np.asarray(mark['vectors'])@rotation
                distances=np.linalg.norm(vectors[:,None,:]-query['vectors'][None,:,:],axis=2)
                colors=np.asarray([[a==b for b in query['colors']] for a in mark['colors']])
                allowed=colors & (distances<=library['markingRadiusAngstrom']+1e-10)
                ii,jj=linear_sum_assignment((~allowed).astype(int))
                assert len(ii)==len(vectors)==len(query['vectors']) and allowed[ii,jj].all()
                max_residual=max(max_residual,float(distances[ii,jj].max()));count+=1
        coupled+=bool(item['coupledMatches']);factorized+=item['factorized'];external+=item['otherConfigurationFactorized']
    assert row['edges']==len(selected) and row['coupledEdges']==coupled and row['factorizedEdges']==factorized and row['otherConfigurationEdges']==external
    assert row['coupledComplete']==(coupled==len(selected)) and row['factorizedComplete']==(factorized==len(selected))
    summaries.append({k:v for k,v in row.items() if k!='registrations'})
expected={}
for training,name in [(True,'training'),(False,'developmental')]:
    group=[r for r in summaries if r['training']==training]
    expected[name]=dict(configurations=len(group),**{key:sum(r[key] for r in group) for key in ['edges','coupledEdges','factorizedEdges','otherConfigurationEdges','coupledComplete','factorizedComplete']})
assert expected==data['summary']
result=dict(scope=__doc__,alternativeCoverHash=sha(alternative_path),swapsReplayed=swap_count,changedConfigurations=changed,resultHash=sha(result_path),pairedPrecheckHash=sha(paired_path),verifierHash=sha(__file__),
            acceptedEndpointFitsChecked=count,maxMarkResidualAngstrom=max_residual,summary=expected,results=summaries)
with Path(output).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)

