"""Compact exact positive leaves, synthesis tables and real root conflicts."""
import hashlib
import json
from pathlib import Path
from dependency_budget_artifact import load
import check_dependency_budget as V
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'


def project(data,audit):
    cases=[];costs={lane:0. for lane in data['lanes']}
    for c in data['cases']:
        runs={}
        for lane,r in c['runs'].items():
            names=('status','placements','tile_generations','proof','endpoint','metrics','graph_metrics','candidate_universe',
                   'tiles','root_marks','compact','point_check','seconds','grammar_seconds','synthesis_seconds',
                   'certification_seconds','preparation_seconds','positive_check_seconds','total_seconds','limits','semantic_sha256')
            out={k:r[k] for k in names if k in r};out['initial_census']=r['search_tree']['census'];timeline=[]
            if r['proof'] is not None:
                node=r['search_tree']
                for key in r['placements']:
                    timeline.append(dict(kind=node['kind'],point=node['point'],key=key,census=node['census']))
                    node=next(ch['tree'] for ch in node['children'] if ch['key']==key)
                timeline.append(dict(kind=node['kind'],point=node['point'],key=None,census=node['census']))
            out['timeline']=timeline;runs[lane]=out
            costs[lane]+=sum(sample['seconds'] for sample in c['timings'][lane]['samples'])
        rules,spec=c['catalog']['rules'],c['spec'];required=V.certificate(rules,spec,c['certificate'])
        raw=V.A.domains(V.F(rules),V.F(spec));key=(1,-1,())
        V.N(key in raw[(2,0)],'actual original root candidate')
        original=V.tile(V.F(rules),V.F(spec),key,None);marked=V.tile(V.F(rules),V.F(spec),key,required)
        roots=V.initial(spec,required);conflicts=[(p,v,roots[p]) for p,v in marked['marks'] if p in roots and roots[p]!=v]
        V.N(conflicts and all(p[0]==-3000 for p,_,_ in conflicts),'actual synthesized distant conflicts')
        control={k:v for k,v in c['controls']['saturation'].items() if k!='region_certificate'}
        cases.append(dict(spec=spec,catalog=c['catalog'],certificate=c['certificate'],runs=runs,timings=c['timings'],
            control=control,rejection=dict(key=key,original=original,marked=marked,conflicts=conflicts)))
    return dict(version='dependency-budget-reader-001',lanes=data['lanes'],limits=data['limits'],cases=cases,
                audit=audit,seconds=data['seconds'],evaluation_observed_seconds=costs,
                scope=data['scope'],timing_scope=data['timing_scope'],
                projection_scope='Actual complete positive leaves, original and decorated tile/root assignments, full greatest-fixed-point tables and a literal original root candidate excluded by the new marking. Failed primary trees, partial cutoffs and full incidence counts are independently audited in the raw hash-bound stages.')


def main():
    path=DOC/'dependency-budget-001.json';data=load(path);audit=json.loads((DOC/'dependency-budget-audit-001.json').read_text())
    if audit['status']!='passed' or audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('exact independent audit required')
    (DOC/'dependency-budget-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')


if __name__=='__main__':main()
