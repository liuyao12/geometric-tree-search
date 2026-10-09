"""Explicitly reuse searched motifs as first-class unmarked cluster prototypes.

This exports construction/flattening evidence, not a region-search benchmark.
Old learned markings and policy weights are not imported. New level channels
remain unassigned until their own boundary-conditioned failure learning runs.
"""
import dataclasses,hashlib,json,time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from turtle import Model,SYMMETRIES,sub
from spatial import moved,keys_tuple
import cluster_tiles as c

HERE=Path(__file__).resolve().parent
DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'

def find_pose(model,name,desired):
    desired=tuple(sorted(keys_tuple(desired)));t=model.types[name]
    for o,g in enumerate(SYMMETRIES):
        rotated=moved(t.expansion,g);orientation,point=rotated[0]
        for other,tr in desired:
            if other==orientation:
                offset=sub(tr,point)
                if tuple(sorted(moved(t.expansion,g,offset)))==desired:return name,o,offset
    raise ValueError('no exact child transform')

def main():
    start=time.monotonic();prior=DOCS/'iteration-003.json';d=json.loads(prior.read_text());base=Model()
    types=[c.make_type(base,'base',0,((0,(0,0,0)),))]
    for m in d['spatial_libraries']['diversity']['motifs']:
        types.append(c.make_type(base,f"cluster-{m['id']}",1,m['expansion']))
    model=c.ClusterModel(types);donor=d['grammar_inspection']['diversity']['samples'][0]
    groups=donor['levels'][0]['groups'];parent_group=next(g for g in donor['levels'][1]['groups'] if len(g['children'])>1)
    children=[]
    for i in parent_group['children']:
        group=groups[i];name='base' if group['type']=='singleton' else f"cluster-{group['type']}"
        children.append(find_pose(model,name,[donor['placements'][j] for j in group['base_ids']]))
    parent=c.compose_type(model,'observed-parent',children);types.append(parent);model=c.ClusterModel(types)
    transformed=0
    for t in types:
        for o in range(12):
            state=c.ClusterState();state.place(model.placement((t.identity,o,(0,0,0))),seed=True)
            assert c.verify_state(model,state);transformed+=1
    data={'date':datetime.now(ZoneInfo('America/Los_Angeles')).isoformat(),
          'scope':'first-class aggregate tile construction and replay; no cluster marking learning or region acceleration claim',
          'reuse':{'artifact':'iteration-003.json','sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),
                   'imported':'14 searched motif expansions and one observed parent child map',
                   'markings_imported':False,'policy_imported':False,'known_human_substitution_imported':False},
          'types':[dataclasses.asdict(t) for t in types],'sample_ids':[children[0][0],'observed-parent'],
          'child_expansions':{t.identity:[model.placement(key).expansion for key in t.children] for t in types if t.children},
          'prototype_count':len(types),'transformed_expansions_checked':transformed,
          'base_singleton_fallback':True,'new_marking_status':'all new level channels unassigned; zero/distant/inherited-channel behavior tested with labeled controls',
          'atomic_semantics':'declared cluster tile inventory; global graph scheduler at this level. Sound flattening to base values, not the base macro scheduler',
          'ownership':'shared descriptions coalesce during parent construction; selected cluster placements have disjoint base ownership',
          'next':'learn boundary-conditioned cluster compatibility/failure markings, then matched fixed/movable region benchmarks',
          'source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in HERE.glob('*.py')},
          'seconds':time.monotonic()-start}
    (DOCS/'cluster-types-001.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
    print('exported',len(types),'first-class types;',transformed,'transformed expansions checked;',round(data['seconds'],3),'seconds',flush=True)

if __name__=='__main__':main()
