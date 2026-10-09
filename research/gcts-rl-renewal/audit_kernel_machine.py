"""Independent rule enumeration and saved first-order Wang certificate replay."""
import copy,hashlib,json,time
from pathlib import Path
import logic,proof_search,lazy_wang,wang
import kernel_search
from kernel_machine import Catalog,KernelMachine,immutable

def components(formulas,templates):
    fs=set();ts=set();vs=set()
    def term(t):
        ts.add(t)
        if t[0]=='var': vs.add(t[1])
        else:
            for a in t[2]: term(a)
    def formula(a):
        fs.add(a);k=a[0]
        if k=='all': vs.add(a[1]);formula(a[2])
        elif k=='eq': term(a[1]);term(a[2])
        elif k=='pred':
            for t in a[2]:term(t)
        elif k=='not':formula(a[1])
        elif k in ('and','or','imp'):formula(a[1]);formula(a[2])
    for a in formulas+templates: formula(a)
    return fs,ts,vs

def audit_catalog(c):
    """Different enumeration: construct schemas, then intersect with catalog."""
    fs,ts,vs=components(c.formulas,c.templates);vs.update(c.variables)
    expected=set()
    def record(a,rule,premises=()):
        if a in c.index and all(p in c.index for p in premises):
            expected.add((rule,tuple(c.index[p] for p in premises),c.index[a]))
    for name,a in c.kernel.axioms.items(): record(a,'axiom')
    for a in c.formulas:
        if logic.tautology(a):record(a,'tautology')
    for t in ts:record(logic.Eq(t,t),'refl')
    for a in fs:
        if a[0]=='all':
            for t in c.terms:record(logic.Imp(a,logic.substitute(a[2],a[1],t)),'instantiate')
        if a[0]=='imp':record(a[2],'mp',(a[1],a))
        for x in c.variables:record(logic.All(x,a),'generalize',(a,))
    for x in vs:
        for p in fs:
            if x in logic.free(p):continue
            for q in fs:record(logic.Imp(logic.All(x,logic.Imp(p,q)),logic.Imp(p,logic.All(x,q))),'distribute')
    for x in c.variables:
        for p in c.templates:
            for s in ts:
                for t in ts:record(logic.Imp(logic.Eq(s,t),logic.Imp(logic.substitute(p,x,s),logic.substitute(p,x,t))),'eq_subst')
    actual=set()
    for item in c.inferences:
        w=item.witness;rule=w['rule'];a=c.formulas[item.conclusion]
        if w['formula']!=a:raise ValueError('changed rule conclusion')
        if rule=='mp':
            if len(item.premises)!=2 or c.formulas[item.premises[1]]!=logic.Imp(c.formulas[item.premises[0]],a):raise ValueError('invalid MP')
        elif rule=='generalize':
            if len(item.premises)!=1 or a!=logic.All(w['variable'],c.formulas[item.premises[0]]):raise ValueError('invalid generalization')
        elif item.premises or not c.kernel.check([w],a):raise ValueError('invalid kernel schema')
        actual.add((rule,item.premises,item.conclusion))
    if expected!=actual:raise ValueError(f'catalog inventory mismatch: missing {len(expected-actual)}, extra {len(actual-expected)}')
    return {'distinct_rule_relations':len(actual),'schema_witnesses':len(c.inferences),
            'kinds':sorted({r[0] for r in actual})}

def audit(path):
    start=time.monotonic();d=json.loads(Path(path).read_text());base=Path(__file__).parent
    for source,digest in d['sources'].items():
        if hashlib.sha256((base/source).read_bytes()).hexdigest()!=digest:raise ValueError('changed source: '+source)
    catalogs=[];certificates=placements=tampers=0; decoded=[]
    external={p['id']:p for p in kernel_search.problems(3)}
    if {p['id'] for p in d['problems']}!=set(external):raise ValueError('changed evaluation problem set')
    for problem in d['problems']:
        ext=external[problem['id']];c=ext['catalog'];target=ext['target'];m=KernelMachine(c,target)
        if immutable(problem['declaration'])!=c.declaration() or immutable(problem['target'])!=target:raise ValueError('changed external mathematical problem')
        expected=[{'premises':r.premises,'conclusion':r.conclusion,'rule':r.witness['rule']} for r in c.inferences]
        if immutable(problem['inferences'])!=immutable(expected):raise ValueError('changed displayed inference inventory')
        if problem['certificate_length']!=8 or problem['height']!=384:raise ValueError('changed rectangle bounds')
        catalogs.append({'id':problem['id'],**audit_catalog(c)})
        for run in problem['runs']:
            if not run.get('verified'):continue
            cert=run['certificate'];rows,tiles=proof_search.unpack(cert)
            pattern=m.pattern(problem['certificate_length']);height=problem['height']
            if cert['height']!=height or cert['width']!=len(pattern) or cert['marking']!=run['marking']:raise ValueError('rectangle metadata changed')
            if not lazy_wang.independent_check(m.compiler,pattern,m.accepting_row(len(pattern)),rows,tiles,
                                              extended=run['marking']=='redundant-neighbor-values'):raise ValueError('invalid accepting rectangle')
            offset=len(c.formulas)+4;commands=m.parse(rows[0][offset:offset+problem['certificate_length']])
            proof=c.proof(commands,target)
            # Rebuild derivation from an external theory and check the stored proof.
            if immutable(run['kernel_proof'])!=immutable(proof) or not c.kernel.check(proof,target):raise ValueError('changed decoded proof')
            certificates+=1;placements+=len(tiles);decoded.append({'id':problem['id'],'lane':run['lane'],'commands':len(commands),'lines':len(proof)})
            changed=copy.deepcopy(proof);changed[-1]['formula']=('bot',)
            if c.kernel.check(changed,('bot',)):raise ValueError('altered target accepted')
            tampers+=1
            try:c.proof((),target)
            except ValueError:tampers+=1
            else:raise ValueError('empty certificate accepted')
            bad_rows=list(rows);bad_rows[-1]=rows[0]
            if lazy_wang.independent_check(m.compiler,pattern,m.accepting_row(len(pattern)),bad_rows,tiles):raise ValueError('changed final row accepted')
            tampers+=1
            bad_pattern=list(pattern);bad_pattern[3]=('1',)
            if lazy_wang.independent_check(m.compiler,tuple(bad_pattern),m.accepting_row(len(pattern)),rows,tiles,
                                          extended=run['marking']=='redundant-neighbor-values'):raise ValueError('changed initial fact boundary accepted')
            tampers+=1
    training={p['id']:p for p in kernel_search.problems(2)};training_proofs=0
    for episode in d['training']['episodes']:
        p=training[episode['problem']];c=p['catalog'];m=KernelMachine(c,p['target'])
        commands=tuple(episode['commands']);result=m.run(m.tokens(commands))
        if (result['status']=='accept')!=episode['verified']:raise ValueError('changed training result')
        if episode['verified']:c.proof(commands,p['target']);training_proofs+=1
    control=d['arithmetic_control'];c=Catalog.from_declaration(control['declaration']);target=immutable(control['target'])
    from replay_proofs import arithmetic_kernel
    external_kernel=arithmetic_kernel()
    if c.kernel.axioms!=external_kernel.axioms or c.kernel.functions!=external_kernel.functions or c.kernel.predicates!=external_kernel.predicates:raise ValueError('changed arithmetic theory')
    if not external_kernel.check(immutable(control['original_proof']),target):raise ValueError('invalid arithmetic witness')
    commands=tuple(control['commands']);proof=c.proof(commands,target);m=KernelMachine(c,target);r=m.run(m.tokens(commands))
    if r['status']!='accept' or r['steps']!=control['machine_steps'] or immutable(proof)!=immutable(control['decoded_proof']):raise ValueError('arithmetic compiler replay failed')
    arithmetic_catalog=audit_catalog(c)
    return {'catalogs':catalogs,'checked_rectangles':certificates,'point_placements_checked':placements,
            'training_sequences_replayed':len(d['training']['episodes']),'training_proofs_replayed':training_proofs,
            'arithmetic_control':{'kernel_lines':len(proof),'literal_machine_steps':r['steps'],'catalog':arithmetic_catalog},
            'decoded_proofs':decoded,'tampered_certificates_rejected':tampers,'seconds':time.monotonic()-start,
            'scope':'exact finite envelopes, literal TM computations, complete point rectangles and externally fixed kernel proofs; no formalized infinite theorem'}

if __name__=='__main__':
    import sys
    print(json.dumps(audit(sys.argv[1] if len(sys.argv)>1 else 'docs/research/gcts-rl-renewal/kernel-machine-001.json'),indent=2))
