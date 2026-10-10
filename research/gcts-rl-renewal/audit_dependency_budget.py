"""Independently certify synthesis and replay every primary search tree."""
import copy
import hashlib
import json
import statistics
import time
from pathlib import Path

import check_dependency_budget as V
from dependency_budget_artifact import load
from dependency_budget_cases import registry
from serialized_kernel import check,canonical,problem_hash
from audit_serialized_kernel import replay as primitive_replay

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic(c,r,cert):
    fields=('status','placements','tile_generations','proof','endpoint','metrics',
            'graph_metrics','search_tree','candidate_universe','limits','tiles','root_marks')
    return dict(spec=c['spec'],catalog=c['catalog'],
                certificate={k:v for k,v in cert.items() if k!='seconds'} if cert else None,
                result={k:r[k] for k in fields})


def audit(data):
    began=time.perf_counter();nodes=0;positives=0;repeated=0;statements=[];mutations=[]
    V.N(data['lanes']==['base','budget'] and data['repetitions']==4 and
        data['limits']==dict(attempts=50000,seconds=60), 'whole declared comparison')
    for i,(c,spec) in enumerate(zip(data['cases'],registry())):
        V.N(V.F(c['spec'])==V.F(spec), 'exact statement-only case input')
        rules,forms=V.A.A.inventory(spec)
        V.N(V.F(rules)==V.F(c['catalog']['rules']) and
            V.F(forms)==V.F(c['catalog']['formulas']), 'complete original finite grammar')
        required=V.certificate(rules,spec,c['certificate'])
        outcomes={}
        for lane in data['lanes']:
            r=c['runs'][lane];mapping=required if lane=='budget' else None
            V.N(r['limits']==data['limits'], 'matched attempt/wall limits')
            V.N(V.F(r['root_marks'])==V.F(sorted(V.initial(spec,mapping).items())), 'all original and budget root values')
            checked=V.replay(rules,spec,r,mapping);nodes+=checked['nodes'];outcomes[lane]=r['status']
            universe=sum(sum(1 for refs in __import__('itertools').product(range(-len(spec['hypotheses']),j),repeat=len(rule['inputs']))
                if all(refs[a]!=refs[b] or rule['inputs'][a]==rule['inputs'][b] for a in range(len(refs)) for b in range(a)))
                for j in range(spec['bound']) for rule in rules)+spec['bound']+1+spec['bound']+int(bool(spec['hypotheses']))
            V.N(r['candidate_universe']==universe, 'unchanged underlying placement universe')
            digest=hashlib.sha256(canonical(semantic(c,r,c['certificate'] if lane=='budget' else None))).hexdigest()
            V.N(digest==r['semantic_sha256'], 'complete retained semantic trace digest')
            t=c['timings'][lane];values=[]
            for j,sample in enumerate(t['samples']):
                order=['base','budget'] if (i+j)%2==0 else ['budget','base']
                V.N(sample['order']==order and sample['repetition']==j and sample['semantic_sha256']==digest and
                    sample['status']==r['status'] and sample['attempts']==r['metrics'].get('attempts',0), 'balanced cold observations bound to full primary trace')
                V.N(sample['seconds']>=sample['preparation_seconds']+sample['search_seconds']+sample['positive_check_seconds']>=0 and
                    sample['preparation_seconds']>=sample['synthesis_seconds']+sample['certification_seconds']>=0 and
                    sample['peak_process_rss_bytes']>0, 'observed inclusive clocks and fresh process memory')
                values.append(sample['seconds']);repeated+=1
            V.N(len(values)==4 and t['median_seconds']==statistics.median(values) and
                t['min_seconds']==min(values) and t['max_seconds']==max(values), 'literal measured summaries')
            if r['proof'] is not None:
                req=r['compact']['request'];payload=canonical(req);pin=problem_hash(req)
                V.N(check(payload,max_work=None,expected_problem_sha256=pin)['status']=='accepted' and
                    primitive_replay(payload,pin)['status']=='accepted', 'both independent primitive proof kernels')
                positives+=1
        control=c['controls']['saturation']
        if control['proof'] is not None:
            V.A.A.proof(control['proof'],spec['target'],spec['hypotheses'],spec['theory'])
            V.N(control['fits_region_bound']==(len(control['proof'])<=spec['bound']), 'classical proof bound')
            if control['fits_region_bound']:
                witness=control['region_certificate'];V.A.certificate(rules,spec,witness,witness['tiles'])
        statements.append(dict(id=spec['id'],outcomes=outcomes,necessary=required[V.F(spec['target'])]))
        print(spec['id'],'full primary trees and greatest fixed point replayed',flush=True)
        if i==3:
            def reject(name,fn):
                try:fn()
                except (ValueError,KeyError,TypeError,IndexError):mutations.append(name)
                else:raise ValueError('corruption accepted: '+name)
            for field in ('context','given','rule','round','required'):
                broken=copy.deepcopy(c['certificate'])
                if field=='context':broken['context_sha256']='!'
                elif field=='given':broken['given']=[]
                elif field=='rule':broken['eligible_rules'].pop()
                elif field=='round':broken['rounds'][0][broken['target']]=[]
                else:broken['required'][broken['target']]+=1
                reject('certificate-'+field,lambda b=broken:V.certificate(rules,spec,b))
            for field in ('census','order','budget-mark','root','target'):
                r=copy.deepcopy(c['runs']['budget'])
                if field=='census':r['search_tree']['census'][0][1]+=1
                elif field=='order':r['search_tree']['children'][0]['key'][1]=999999
                elif field=='budget-mark':
                    value=next(v for v in r['tiles'][0]['marks'] if v[0][0]==-3000);value[1]=1
                elif field=='root':r['root_marks'].pop()
                else:r['proof'][-1]['formula']=['bot']
                if field=='root':reject(field,lambda r=r:V.N(V.F(r['root_marks'])==V.F(sorted(V.initial(spec,required).items())), 'root values'))
                else:reject(field,lambda r=r:V.replay(rules,spec,r,required))
    V.N(len(statements)==len(registry()), 'all cases audited')
    return dict(status='passed',searches=2*len(statements),independent_states=nodes,
                primitive_certificates_including_duplicates=positives,observations=repeated,
                cases=statements,mutations_rejected=mutations,seconds=time.perf_counter()-began,
                scope='Every fixed-point round and local inductive redundancy obligation, complete original grammar, literal distant assignments, full primary domain censuses, complete base order and tri-state cutoffs, positive original and decorated point certificates, both primitive kernels. Complete repeat trees are retained privately and semantic-digest bound; they and physical wall clocks are not independently replayed. Classical negative closure traces are not fully replayed.')


def main():
    path=DOC/'dependency-budget-001.json';data=load(path)
    for name,pin in data['sources'].items():V.N(sha(HERE/name)==pin, 'measured source '+name)
    out=audit(data);out.update(version='dependency-budget-audit-001',input_sha256=sha(path),
        source_sha256=sha(__file__),helpers={n:sha(HERE/n) for n in ('check_dependency_budget.py','check_movable_regions.py',
        'check_quantified_receptors.py','audit_serialized_kernel.py','dependency_budget_artifact.py','receptor_attention_artifact.py')})
    (DOC/'dependency-budget-audit-001.json').write_bytes(canonical(out)+b'\n');print(json.dumps(out),flush=True)


if __name__=='__main__':main()
