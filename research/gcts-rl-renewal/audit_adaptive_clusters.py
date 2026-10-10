"""Audit fresh tree/family provenance, actual transactions and RL updates."""
import copy
import hashlib
import json
import time
from pathlib import Path

import check_adaptive_clusters as V

HERE=Path(__file__).resolve().parent
DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(data):
    started=time.perf_counter()
    templates={t['name']:t for t in data['library']}
    checks=[]
    for donor in data['donors']:
        rules,_=V.A.A.inventory(donor['spec'])
        V.N(V.F(rules)==V.F(donor['catalog']['rules']),'independent donor inventory')
        checks.append(V.result(rules,donor['spec'],templates,donor['result']))
    known={};sources={V.digest(d['result']):d for d in data['donors']}
    for t in data['library']:
        source=t['source'];pin=V.digest(source['result'])
        V.N(pin in sources,'actual fresh donor trace required')
        donor=sources[pin]
        V.N(V.F(source['spec'])==V.F(donor['spec']) and V.F(source['catalog'])==V.F(donor['catalog']),
            'whole donor binding')
        members=V.F(source['members']);proof=sorted((V.F(k) for k in donor['result']['placements'] if k[1]>=0),key=lambda k:k[0])
        V.N(any(proof[i:i+len(members)]==list(members) for i in range(len(proof))), 'actual proof fragment')
        pattern=V.pattern_for(V.F(donor['catalog']['rules']),members)
        V.N(V.F(t['pattern'])==pattern and t['name']=='receptor-cluster-'+V.digest(pattern)[:20], 'learned formula abstraction')
        children=[];inside={k[0]:i for i,k in enumerate(members)}
        for tr in donor['result']['solution_transactions']:
            if tr['item']['template'] in known and set(V.F(tr['item']['members']))<=set(members):
                children.append(dict(template=tr['item']['template'],offsets=[inside[k[0]] for k in V.F(tr['item']['members'])]))
        V.N(V.F(t['children'])==V.F(children),'hierarchy from executed source transaction')
        V.N(t['level']==1+max((known[ch['template']]['level'] for ch in children),default=0),'acyclic hierarchy level')
        known[t['name']]=t
    weights=[0.0]*5;baseline=0.0;draws=0
    training_ids={s['id'] for s in data['training']['specs']}
    for episode in data['training']['episodes']:
        spec=episode['spec'];rules,_=V.A.A.inventory(spec)
        V.N(spec in data['training']['specs'],'declared training problem')
        V.N(V.F(rules)==V.F(episode['catalog']['rules']),'independent training inventory')
        V.close(weights,episode['weights_before']);V.close(weights,episode['result']['weights'])
        checks.append(V.result(rules,spec,templates,episode['result']))
        weights,baseline=V.training_update(weights,baseline,episode['result'],episode['update'])
        V.N(abs(baseline-episode['baseline_after'])<1e-12,'moving reward baseline')
        draws+=len(episode['result']['policy_events'])
    V.close(weights,data['training']['weights']);V.N(baseline==data['training']['baseline'],'frozen final policy')
    positive=0;transactions=0
    for c in data['cases']:
        spec=c['spec'];V.N(spec['id'] not in training_ids,'held-out problem IDs')
        rules,_=V.A.A.inventory(spec)
        V.N(V.F(rules)==V.F(c['catalog']['rules']),'independent evaluation inventory')
        statuses=set()
        for lane,r in c['runs'].items():
            if lane=='rl':V.close(weights,r['weights'])
            if lane=='zero':V.close([0.0]*5,r['weights'])
            checks.append(V.result(rules,spec,templates,r));statuses.add(r['status'])
            positive+=r['status']=='finite_exact_proof_region'
            transactions+=r['metrics'].get('accepted_transactions',0)
        V.N(len(statuses)==1,'all methods reach the same bounded outcome')
        sat=c['saturation']
        if sat['proof']:
            V.A.A.proof(sat['proof'],spec['target'],spec['hypotheses'],spec['theory'])
            V.N(sat['fits_region_bound']==(len(sat['proof'])<=spec['bound']),'saturation proof-length scope')
            if sat['fits_region_bound']:
                region=sat['region_certificate']
                V.A.certificate(rules,spec,region,region['tiles'])
                V.N(V.F(region['proof'])==V.F(sat['proof']), 'same saturation proof')
                V.N(V.replay(V.P(region['compiled']['request']))['status']=='accepted','saturation kernel check')
                V.N(V.F(region['compiled']['request']['target'])==V.F(spec['target']), 'saturation conclusion')
                request=V.F(region['compiled']['request']);h=len(spec['hypotheses'])
                expected_theory=dict(V.F(spec['theory']),axioms={**V.F(spec['theory']['axioms']),
                    **{'premise-'+str(i):V.F(a) for i,a in enumerate(spec['hypotheses'])}})
                commands=[dict(rule='axiom',formula=V.F(a),name='premise-'+str(i)) for i,a in enumerate(spec['hypotheses'])]
                commands.extend(dict(rule='mp',formula=V.F(row['formula']),antecedent=row['refs'][0]+h,implication=row['refs'][1]+h) for row in sat['proof'])
                V.N(request['theory']==expected_theory and not request['blocks'] and V.F(request['proof'])==V.F(commands),
                    'entire saturation theory, hypotheses and commands bound')
    # Controllers can propose hints; their complete-tree results cannot depend
    # on accepting corrupted interfaces, aggregates, base rows or policy draws.
    sample=next(c for c in data['cases'] if c['spec']['id']=='heldout-compound')
    mutations=[]
    def rejection(name,fn):
        try:fn()
        except (ValueError,KeyError,IndexError,TypeError):mutations.append(name)
        else:raise ValueError('mutation accepted '+name)
    r=sample['runs']['fixed'];rules=V.F(sample['catalog']['rules'])
    trial=r['solution_transactions'][0]
    def altered_item(field):
        item=copy.deepcopy(trial['item'])
        if field=='capacity':item['occupancy'][0][1]=11
        elif field=='mark':item['marks'][0][1]='!'
        elif field=='binding':item['bindings'][next(iter(item['bindings']))]=['bot']
        elif field=='outside':item['outside'][next(iter(item['outside']))]=999
        else:item['members'][0][1]=99999
        # Reconstruct the actual transaction's start context from its trace tree.
        def find(tree,chosen=()):
            for tr in tree['proposals']:
                if tr==trial:return chosen
                if 'tree' in tr:
                    next_chosen=V.transaction(rules,sample['spec'],tr['item'],tr['trace'],V.F(chosen))
                    got=find(tr['tree'],next_chosen)
                    if got is not None:return got
            for ch in tree['children']:
                got=find(ch['tree'],V.F(chosen)+(V.F(ch['key']),))
                if got is not None:return got
            return None
        chosen=find(r['search_tree'])
        V.N(chosen is not None,'actual proposal context')
        V.item(rules,sample['spec'],templates,item,V.F(chosen))
    for field in ('capacity','mark','binding','outside','rule'):
        rejection('cluster-'+field,lambda f=field:altered_item(f))
    for field in ('selected','draw','gradient','return'):
        episode=copy.deepcopy(data['training']['episodes'][0]);er=episode['result']
        if field=='selected':er['policy_events'][0]['selected']=999
        elif field=='draw':er['policy_events'][0]['draw']=.000001
        elif field=='gradient':er['policy_events'][0]['gradient'][0]+=1
        else:episode['update']['reward']+=1
        if field=='return':
            rejection(field,lambda e=episode:V.training_update(e['weights_before'],e['update']['baseline_before'],e['result'],e['update']))
        else:
            rejection(field,lambda e=episode:V.result(V.F(e['catalog']['rules']),e['spec'],templates,e['result']))
    bad=copy.deepcopy(sample['runs']['base']);bad['search_tree']['children'][0]['key'][1]=99999
    rejection('base-alternative',lambda:V.result(rules,sample['spec'],templates,bad))
    return dict(status='passed',searches=len(checks),independent_states=sum(c['nodes'] for c in checks),
                templates=len(templates),levels=sorted({t['level'] for t in templates.values()}),
                on_policy_draws=draws,evaluation_positive_proofs=positive,
                evaluation_accepted_transactions=transactions,mutations_rejected=mutations,
                seconds=time.perf_counter()-started)


def main():
    path=DOC/'adaptive-clusters-001.json';data=json.loads(path.read_bytes())
    for n,pin in data['sources'].items():V.N(digest(HERE/n)==pin,'frozen measured source '+n)
    result=audit(data)
    result.update(version='adaptive-clusters-audit-001',input_sha256=digest(path),
                  source_sha256=digest(__file__),checker_sha256=digest(HERE/'check_adaptive_clusters.py'))
    (DOC/'adaptive-clusters-audit-001.json').write_bytes(V.P(result)+b'\n')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
