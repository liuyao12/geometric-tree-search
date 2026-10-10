"""Independent finite trees, exact points, source bindings and discharge audit."""
import copy,hashlib,json,time
from pathlib import Path
import check_movable_regions as A
import check_adaptive_clusters as V
from check_compact_contexts import certificate
from compact_context_cases import registry

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    began=time.perf_counter();path=DOC/'compact-contexts-001.json';data=json.loads(path.read_bytes());checks=[]
    for n,pin in data['sources'].items():A.need(digest(HERE/n)==pin,'frozen measured source '+n)
    specs=registry();A.need(len(data['cases'])==len(specs),'complete external registry')
    for s,c in zip(specs,data['cases']):
        A.need(A.freeze(s)==A.freeze(c['spec']),'declarative statement binding')
        rules,forms=A.A.inventory(s);A.need(A.freeze(rules)==A.freeze(c['catalog']['rules']) and A.freeze(forms)==A.freeze(c['catalog']['formulas']),'entire query-independent grammar')
        r=c['result'];row=dict(id=s['id'],tree=A.tree(rules,s,r))
        if r['proof'] is not None:
            row['points']=A.certificate(rules,s,r,r['tiles']);row['compact']=certificate(s,r)
            if c['expanded_comparison']:
                A.need(c['expanded_comparison']['commands']==row['compact']['old_expanded_commands'],'measured small adapter count')
        checks.append(row);print(s['id'],'audited',flush=True)
    donor=next(c for c in data['cases'] if c['spec']['id']=='branch-donor');templates={}
    for t in data['library']:
        A.need(A.freeze(t['source']['result'])==A.freeze(donor['result']) and A.freeze(t['source']['spec'])==A.freeze(donor['spec'])
            and A.freeze(t['source']['catalog'])==A.freeze(donor['catalog']),'fresh actual donor provenance')
        members=A.freeze(t['source']['members']);proof=sorted((A.freeze(k) for k in donor['result']['placements'] if k[1]>=0))
        A.need(any(proof[i:i+len(members)]==list(members) for i in range(len(proof))),'actual source window')
        pattern=V.pattern_for(A.freeze(donor['catalog']['rules']),members)
        A.need(A.freeze(t['pattern'])==pattern and t['name']=='receptor-cluster-'+V.digest(pattern)[:20]
            and t['level']==1 and not t['children'],'whole non-chain formula abstraction')
        templates[t['name']]=t
    transfer=data['transfer'];rules,_=A.A.inventory(transfer['spec']);tr=[]
    for lane,r in transfer['runs'].items():
        tr.append(dict(lane=lane,tree=V.result(rules,transfer['spec'],templates,r),compact=certificate(transfer['spec'],r)))
    sample=next(c for c in data['cases'] if c['spec']['id']=='ambient-y');mutations=[]
    for name in ('source-reference','source-target','context','added-axiom','target','helper','output-map','source-binding','group','closure','cost','point'):
        bad=copy.deepcopy(sample);c=bad['result']['compact']
        if name=='source-reference':bad['result']['proof'][0]['refs'][0]=0
        elif name=='source-target':bad['spec']['target']=['bot']
        elif name=='context':c['context']=['bot']
        elif name=='added-axiom':c['request']['theory']['axioms']['hidden']=['imp',['bot'],['bot']]
        elif name=='target':c['request']['target']=['bot']
        elif name=='helper':c['request']['proof'][0]['formula']=['bot']
        elif name=='output-map':c['conditional_map']['0']+=1
        elif name=='source-binding':c['source_bindings'][0]['last']+=1
        elif name=='group':c['groups'][0]['first']+=1
        elif name=='closure':c['closure_variables']=[]
        elif name=='cost':c['commands']+=1
        else:bad['result']['tiles'][0]['marks'][0][1]='!'
        try:
            if name=='point':A.certificate(A.freeze(bad['catalog']['rules']),bad['spec'],bad['result'],bad['result']['tiles'])
            else:certificate(bad['spec'],bad['result'])
        except (ValueError,KeyError,IndexError,TypeError):mutations.append(name)
        else:raise ValueError('accepted mutation '+name)
    # The open hypothesis P(x) holds at one assignment, but not at every object.
    countermodel=dict(domain=[0,1],assignment_x=0,p_values=[True,False],premise=True,conclusion=False)
    out=dict(version='compact-contexts-audit-001',status='passed',input_sha256=digest(path),source_sha256=digest(__file__),
        helpers={n:digest(HERE/n) for n in ('check_compact_contexts.py','check_movable_regions.py','check_adaptive_clusters.py','audit_quantified_receptors.py')},
        cases=checks,transfer=tr,templates=len(templates),mutations_rejected=mutations,scope_countermodel=countermodel,
        independent_states=sum(c['tree']['nodes'] for c in checks)+sum(c['tree']['nodes'] for c in tr),seconds=time.perf_counter()-began)
    (DOC/'compact-contexts-audit-001.json').write_bytes(A.A.packed(out)+b'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('cases','transfer','helpers')}),flush=True)
if __name__=='__main__':main()
