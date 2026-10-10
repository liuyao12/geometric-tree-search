"""Fresh finite quantified searches, discovered family transfer and controls."""
import collections,copy,hashlib,json,resource,time
from pathlib import Path
import quantified_receptors as Q
import check_quantified_receptors as A
from quantified_receptor_cases import registry
from audit_serialized_kernel import replay
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def execute(c,family=None,bindings=()):
    start=time.perf_counter();catalog=Q.inventory(c['theory'],c['hypotheses'],c['terms'],c['variables'],c['rounds'],family,bindings,c['generalization_rounds']);build=time.perf_counter()-start
    rules,forms=A.inventory(c,family,bindings)
    if rules!=catalog['rules'] or forms!=catalog['formulas']:raise ValueError('complete independent grammar')
    runs={};model=None
    for lane in ('gcts','chronological','saturation'):
        m=Q.Model(catalog,c['target'],c['length'],c['hypotheses'])
        r=Q.search(m,seconds=8,node_limit=30000) if lane=='gcts' else Q.chronological(m,seconds=8,node_limit=30000) if lane=='chronological' else Q.saturation(m)
        if r['proof']:
            r['logical']=A.proof(r['proof'],c['target'],c['hypotheses'],c['theory'])
            compiled=Q.compile_request(r['proof'],c['target'],c['hypotheses'],c['theory']);r['compiled']=compiled
            before=time.perf_counter();independent=replay(canonical(compiled['request']));r['independent_host_seconds']=time.perf_counter()-before
            if independent['status']!='accepted':raise ValueError('independent primitive expansion')
            if c['hypotheses']:
                r['deduced']=Q.compile_request(r['proof'],c['target'],c['hypotheses'],c['theory'],True)
                if replay(canonical(r['deduced']['request']))['status']!='accepted':raise ValueError('fully discharged theorem')
        if lane=='gcts':
            model=m
            if r['proof']:
                r['tiles']=[dict(key=k,occupancy=m.placement(k).occupancy,marks=m.placement(k).marks) for k in r['placements']]
                r['point_certificate']=A.certificate(rules,c,r,r['tiles']);frames=[];s=m.initial();g=Q.Graph(m,s)
                for key in r['placements']:
                    kind,p,keys=g.decision(s);frames.append(dict(kind=kind,point=p,key=key,domains=[dict(point=p,count=len(d),blocks=d.blocks) for p,d in sorted(g.domains.items())]));g.update(m,s,s.place(m.placement(key)))
                r['frames']=frames
        runs[lane]=r
    return dict(spec=c,family=family,bindings=bindings,catalog=catalog,build_seconds=build,runs=runs)
def main():
    start=time.perf_counter();sources={n:digest(HERE/n) for n in ('run_quantified_receptors.py','quantified_receptors.py','quantified_receptor_cases.py','check_quantified_receptors.py','test_quantified_receptors.py','logic.py','serialized_kernel.py','audit_serialized_kernel.py','turtle.py')}
    specs,bindings=registry();source=execute(specs[0]);proof=source['runs']['gcts']['proof']
    if not proof or any(r['kind']=='family' for r in proof):raise ValueError('fresh primitive family source')
    family=dict(name='universal-mp',proof=proof,premises=specs[0]['hypotheses'],conclusion=specs[0]['target'],guards=tuple(sorted({r['parameters']['variable'] for r in proof if r['kind']=='generalize'})),source='universal-mp')
    cases=[source];print(specs[0]['id'],source['runs']['gcts']['metrics'],flush=True)
    for c in specs[1:]:
        row=execute(c);cases.append(row);print(c['id'],row['runs']['gcts']['status'],row['runs']['gcts']['metrics'],flush=True)
    for name,key,bound in (('arithmetic','arithmetic',7),('geometry-family','geometry',4),('geometry-family','geometry',1),('arithmetic','arithmetic',6)):
        c=copy.deepcopy(next(c for c in specs if c['id']==name));c['id']+='-learned-'+str(bound);c['length']=bound;row=execute(c,family,[bindings[key]]);cases.append(row);print(c['id'],row['runs']['gcts']['metrics'],flush=True)
    out=dict(version='quantified-receptors-001',sources=sources,family=family,cases=cases,seconds=time.perf_counter()-start,peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='Finite query-independent signature/theory/hypothesis/term/quantifier envelopes; actual zero/one scope markings; exact single-slot domains; fresh learned predicate family; no RL lane, no learned redundant constraint synthesis, no universal completeness claim.')
    if any(digest(HERE/n)!=pin for n,pin in sources.items()):raise ValueError('measured sources changed')
    (DOC/'quantified-receptors-001.json').write_bytes(canonical(out)+b'\n');print('complete',out['seconds'],flush=True)
if __name__=='__main__':main()
