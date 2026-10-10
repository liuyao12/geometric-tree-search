"""Full independent inventory, point/tree/factor and compiler binding audit."""
import copy,hashlib,json,time
from pathlib import Path
import check_quantified_receptors as A
from quantified_receptor_cases import registry
from audit_serialized_kernel import replay
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def expected_commands(rows,hypotheses):
    rows=A.freeze(rows);hypotheses=A.freeze(hypotheses);out=[dict(rule='assumption',formula=a,index=j) for j,a in enumerate(hypotheses)]
    mapping={j:i for i,j in enumerate(range(-len(hypotheses),0))};bindings=[]
    def emit(r):out.append(r);return len(out)-1
    def expand(proof,external):
        ids=dict(external)
        for j,r in enumerate(proof):
            a=r['formula'];p=r['parameters'];refs=[ids[i] for i in r['refs']];kind=r['kind']
            if kind=='axiom':index=emit(dict(rule='axiom',formula=a,name=p['name']))
            elif kind=='forall-elim':
                edge=emit(dict(rule='instantiate',formula=('imp',p['universal'],a),universal=p['universal'],term=p['term']));index=emit(dict(rule='mp',formula=a,antecedent=refs[0],implication=edge))
            elif kind=='generalize':index=emit(dict(rule='generalize',formula=a,variable=p['variable'],source=refs[0]))
            elif kind=='mp':index=emit(dict(rule='mp',formula=a,antecedent=refs[0],implication=refs[1]))
            elif kind=='projection':
                edge=emit(dict(rule='tautology',formula=('imp',out[refs[0]]['formula'],a)));index=emit(dict(rule='mp',formula=a,antecedent=refs[0],implication=edge))
            elif kind=='family':index=expand(p['expansion'],{k:i for k,i in enumerate(refs,-len(refs))})
            else:raise ValueError('source command kind')
            ids[j]=index
        return ids[len(proof)-1]
    for j,r in enumerate(rows):
        first=len(out);last=expand((r,),{i:mapping[i] for i in r['refs']});mapping[j]=last;bindings.append(dict(source_slot=j,first=first,last=last))
    return out,bindings
def bind_compiled(spec,r):
    d=A.freeze(spec);expected,binding=expected_commands(r['proof'],d['hypotheses']);compiled=r['compiled'];request=A.freeze(compiled['request']);theory=copy.deepcopy(d['theory'])
    if any(A.parser(theory).free(a) for a in d['hypotheses']):
        probe=('imp',('bot',),('bot',));wanted=dict(protocol='gcts-fol-1',theory=theory,target=probe,blocks=[dict(name='discovered-sequent',premises=d['hypotheses'],conclusion=d['target'],proof=expected)],proof=[dict(rule='tautology',formula=probe)])
    else:
        for j,a in enumerate(d['hypotheses']):theory['axioms']['premise-'+str(j)]=a;expected[j]=dict(rule='axiom',formula=a,name='premise-'+str(j))
        wanted=dict(protocol='gcts-fol-1',theory=theory,target=d['target'],blocks=[],proof=expected)
    A.need(request==A.freeze(wanted) and A.freeze(compiled['bindings'])==A.freeze(binding),'entire source-to-command compilation')
    A.need(replay(A.packed(request))['status']=='accepted','independent full command expansion')
    if d['hypotheses']:
        req=A.freeze(r['deduced']['request']);target=d['target']
        for h in reversed(d['hypotheses']):target=('imp',h,target)
        A.need(req['target']==target and req['theory']==d['theory'] and not req['blocks'],'fully discharged original theorem binding')
        A.need(replay(A.packed(req))['status']=='accepted','independent discharged proof')
    return dict(status='accepted',commands=len(expected),deduced_commands=len(r.get('deduced',{}).get('request',{}).get('proof',())))
def factors(rules,spec,r):
    chosen=[];A.need(len(r['frames'])==len(r['placements']),'full factor path')
    for frame,key in zip(r['frames'],r['placements']):
        ds=A.domains(rules,spec,chosen);kind,p,keys=A.decide(ds);key=A.freeze(key)
        A.need((frame['kind'],A.freeze(frame['point']),A.freeze(frame['key']))==(kind,p,key) and key in keys,'actual factor-path scheduler')
        A.need([A.freeze(d['point']) for d in frame['domains']]==sorted(ds),'whole frontier factor domains')
        for d in frame['domains']:
            expected=ds[A.freeze(d['point'])];actual=[];j=d['point'][0]//2;h=len(spec['hypotheses'])
            for rid,masks,distinct in d['blocks']:
                A.need(0<=rid<len(rules) and len(masks)==len(rules[rid]['inputs']),'factor arity')
                A.need(distinct==(len(masks)==2 and rules[rid]['inputs'][0]!=rules[rid]['inputs'][1]),'diagonal semantics')
                import itertools
                choices=[[i for i in range(j+h) if mask&(1<<i)] for mask in masks]
                A.need(all(type(mask) is int and 0<=mask<(1<<(j+h)) for mask in masks),'bounded reference masks')
                actual.extend((j,rid,tuple(i-h for i in refs)) for refs in itertools.product(*choices) if not distinct or refs[0]!=refs[1])
            A.need(actual==expected and d['count']==len(expected),'complete factor expansion and count')
        chosen.append(key)
    return dict(status='complete_factors_replayed',frames=len(chosen))
def main():
    start=time.perf_counter();path=DOC/'quantified-receptors-001.json';data=json.loads(path.read_bytes());specs,bindings=registry();cases=data['cases'];A.need(len(cases)==12,'external experiment registry')
    for n,p in data['sources'].items():A.need(digest(HERE/n)==p,'measured source '+n)
    family=A.freeze(data['family']);source=cases[0]['runs']['gcts']['proof'];guards=tuple(sorted({r['parameters']['variable'] for r in source if r['kind']=='generalize'}))
    A.need(family==A.freeze(dict(name='universal-mp',proof=source,premises=specs[0]['hypotheses'],conclusion=specs[0]['target'],guards=guards,source='universal-mp')),'actual discovered family provenance')
    expected=[(c,None,()) for c in specs]
    for name,binding,n in (('arithmetic','arithmetic',7),('geometry-family','geometry',4),('geometry-family','geometry',1),('arithmetic','arithmetic',6)):
        c=copy.deepcopy(next(c for c in specs if c['id']==name));c['id']+='-learned-'+str(n);c['length']=n;expected.append((c,family,(bindings[binding],)))
    reports=[];mutations=[]
    for case,(spec,fam,bs) in zip(cases,expected):
        A.need(A.freeze(case['spec'])==A.freeze(spec) and A.freeze(case['family'])==A.freeze(fam) and A.freeze(case['bindings'])==A.freeze(bs),'exact external declaration')
        rules,forms=A.inventory(spec,fam,bs);A.need(A.freeze(case['catalog']['rules'])==A.freeze(rules) and A.freeze(case['catalog']['formulas'])==A.freeze(forms),'whole rule/formula inventory')
        row=dict(id=spec['id'],tree=A.tree(rules,spec,case['runs']['gcts']),positive=[])
        for lane,r in case['runs'].items():
            if r['proof']:
                A.need(A.proof(r['proof'],spec['target'],spec['hypotheses'],spec['theory'])==r['logical'],'complete independent source logic');binding=bind_compiled(spec,r);row['positive'].append(dict(lane=lane,compiler=binding))
        r=case['runs']['gcts']
        if r['proof']:
            row['certificate']=A.certificate(rules,spec,r,r['tiles']);A.need(row['certificate']==r['point_certificate'],'point report');row['factors']=factors(rules,spec,r)
            for kind in ('formula','word','omit','future-reference','factor-count','factor-mask','tree-decision','compiled-target','deduced-target'):
                if kind=='deduced-target' and not spec['hypotheses']:continue
                bad=copy.deepcopy(r)
                if kind=='formula':bad['proof'][0]['formula']=['bot']
                elif kind=='word':bad['tiles'][0]['marks'][0][1]='!'
                elif kind=='omit':bad['placements'].pop()
                elif kind=='future-reference':
                    pos=next((i for i,k in enumerate(bad['placements']) if k[2]),None)
                    if pos is None:continue
                    bad['placements'][pos][2][0]=bad['placements'][pos][0]
                elif kind=='factor-count':bad['frames'][0]['domains'][0]['count']+=1
                elif kind=='factor-mask':
                    block=next((b for f in bad['frames'] for d in f['domains'] for b in d['blocks'] if b[1]),None)
                    if block is None:continue
                    block[1][0]|=1<<30
                elif kind=='tree-decision':bad['search_tree']['point']=[999,0]
                elif kind=='compiled-target':bad['compiled']['request']['target']=['bot']
                else:bad['deduced']['request']['target']=['bot']
                try:
                    if kind.startswith('factor'):factors(rules,spec,bad)
                    elif kind.startswith('tree'):A.tree(rules,spec,bad)
                    elif 'target' in kind:bind_compiled(spec,bad)
                    else:A.certificate(rules,spec,bad,bad['tiles'])
                except (ValueError,IndexError,KeyError):mutations.append(dict(case=spec['id'],kind=kind))
                else:raise ValueError('accepted mutation '+kind)
        reports.append(row);print(spec['id'],'audited',flush=True)
    # A two-object relation with only off-diagonal pairs validates the universal
    # existential premise, and falsifies the captured diagonal conclusion.
    model=dict(domain=[0,1],relation=[[False,True],[True,False]],premise=True,diagonal=False)
    A.need(all(any(row) for row in model['relation']) and not any(model['relation'][i][i] for i in range(2)),'capture countermodel')
    out=dict(version='quantified-receptors-audit-001',source_sha256=digest(__file__),input_sha256=digest(path),helper_sources={n:digest(HERE/n) for n in ('check_quantified_receptors.py','quantified_receptor_cases.py','audit_serialized_kernel.py','serialized_kernel.py')},cases=reports,mutations_rejected=mutations,capture_countermodel=model,seconds=time.perf_counter()-start,
        scope='Independent finite formula/rule grammar with separate substitution implementation; every terminal point tree, positive t/m certificate, factor expansion, family instance and whole compiled source; discharged proofs replayed in the old kernel with exact theory/target binding.')
    (DOC/'quantified-receptors-audit-001.json').write_bytes(A.packed(out)+b'\n');print('audit complete',out['seconds'],len(mutations),flush=True)
if __name__=='__main__':main()
