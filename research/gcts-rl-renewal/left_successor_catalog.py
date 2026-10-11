"""Complete bounded contextual grammar, with streaming primitive diagnostics.

Generic infrastructure; the input supplies a closed equation and term bound.
No target proof path or chosen induction variable is supplied. A transferred
equational theorem must come from an actually searched and checked certificate.
"""
import copy,hashlib,time
import logic as L
import induction_receptors_catalog as I
from certificate_boundary_search import canonical

def definition(premises,conclusion,proof):
    d=I.definition(premises,conclusion,proof)
    d['name']='leftSuccessorReceptor'+d['name'][len('inductionReceptor'):]
    return d
def learned_edge_proof(move):
    """One generic congruence edge from a supplied universal equation premise."""
    out=I.Proof();rule=move['rule'];f=rule['formula'];i=out.emit('assumption',f,index=1)
    for x in rule['variables']:
        t=move['bindings'][x];q=L.substitute(f[2],f[1],t);a=out.emit('instantiate',L.Imp(f,q),universal=f,term=t);i=out.mp(i,a);f=q
    left,right=f[1:]
    if move['direction']==-1:
        h=I.fresh(f);q=L.Eq(right,left);rf=out.emit('refl',L.Eq(left,left));a=out.emit('eq_subst',L.Imp(f,L.Imp(L.Eq(left,left),q)),variable=h,template=L.Eq(L.V(h),left),left=left,right=right);i=out.mp(rf,out.mp(i,a));left,right=right,left
    before,after=move['before'],move['after']
    if before!=left or after!=right:
        h=I.fresh(L.Eq(before,after),L.Eq(left,right));template=L.Eq(before,I.replace(before,move['path'],L.V(h)));rf=out.emit('refl',L.Eq(before,before));a=out.emit('eq_subst',L.Imp(L.Eq(left,right),L.Imp(L.Eq(before,before),L.Eq(before,after))),variable=h,template=template,left=left,right=right);i=out.mp(rf,out.mp(i,a))
    if I.freeze(out.lines[-1]['formula'])!=L.Eq(before,after):raise ValueError('generic learned edge target mismatch')
    return out.lines
def rewrite(original,move,hypothesis):
    if move['rule']['origin']!='discovered-lemma':
        d=I.rewrite(original,move,hypothesis);d['name']='leftSuccessorReceptor'+d['name'][len('inductionReceptor'):];return d
    before,after=move['before'],move['after'];p,q=L.Eq(original,before),L.Eq(original,after);H=hypothesis;input_formula=p if H is None else L.Imp(H,p)
    out=I.Proof();source=out.emit('assumption',input_formula,index=0);ei=out.append(learned_edge_proof(move));edge=L.Eq(before,after)
    if H is not None:
        a=out.emit('tautology',L.Imp(edge,L.Imp(H,edge)));ei=out.mp(ei,a)
    hole=I.fresh(p,q,edge);subst=L.Imp(edge,L.Imp(p,q));si=out.emit('eq_subst',subst,variable=hole,template=L.Eq(original,L.V(hole)),left=before,right=after)
    if H is None:out.mp(source,out.mp(ei,si));conclusion=q
    else:
        lift=out.emit('tautology',L.Imp(subst,L.Imp(L.Imp(H,edge),L.Imp(H,L.Imp(p,q)))));consequence=out.mp(ei,out.mp(si,lift));combine=out.emit('tautology',L.Imp(L.Imp(H,L.Imp(p,q)),L.Imp(L.Imp(H,p),L.Imp(H,q))));out.mp(source,out.mp(consequence,combine));conclusion=L.Imp(H,q)
    return definition([input_formula,move['rule']['formula']],conclusion,out.lines)
def core(spec,transferred=()):
    began=time.perf_counter();target=I.freeze(spec['target']);variables=[];body=target
    while body[0]=='all':variables.append(body[1]);body=body[2]
    if body[0]!='eq' or len(set(variables))!=len(variables) or L.free(body)-set(variables):raise ValueError('closed distinctly quantified equation required')
    terms=I.term_grammar(spec['theory']['functions'],variables,spec['term_bound']);equations=[q for n,f in sorted(spec['theory']['axioms'].items()) for q in [I.equation(n,I.freeze(f))] if q]
    for entry in transferred:
        if entry['theory']!=spec['theory']:raise ValueError('transferred theorem must retain the exact original theory')
        q=I.equation(entry['name'],I.freeze(entry['conclusion']),'discovered-lemma')
        if not q:raise ValueError('only proved universal equations are transferred by this interface')
        equations.append(q)
    axiom_moves=I.moves(terms,equations);contexts=[dict(original=body[1],hypothesis=None,goal=body,closure=variables,kind='direct',variable=None)]
    if 'nat-induction' in spec['theory']['schemas'] and spec.get('enable_induction',True):
        for x in variables:
            others=[v for v in variables if v!=x];base=L.substitute(body,x,L.F('zero'));step=L.substitute(body,x,L.F('succ',L.V(x)));contexts += [dict(original=base[1],hypothesis=None,goal=base,closure=others,kind='base',variable=x),dict(original=step[1],hypothesis=body,goal=L.Imp(body,step),closure=others+[x],kind='step',variable=x)]
    formulas={};rules=[];definitions={};seen=set();descriptors=[]
    def add_formula(f):formulas[canonical(I.thaw(f))]=I.thaw(f)
    def add(premises,conclusion,command,kind,description):
        key=canonical(I.thaw_record([premises,conclusion,command]));add_formula(conclusion)
        for p in premises:add_formula(p)
        if key in seen:return
        seen.add(key);rules.append(dict(premises=I.thaw_record(premises),conclusion=I.thaw_record(conclusion),command=command,kind=kind,description=I.thaw_record(description)))
    def block(d,description):definitions[d['name']]=d;add(d['premises'],d['conclusion'],dict(rule='block',formula=d['conclusion'],name=d['name']),'derived',description)
    for entry in transferred:
        block(dict(name=entry['name'],premises=[],conclusion=entry['conclusion'],proof=entry['proof']),dict(operation='transferred-searched-theorem',source_request_sha256=entry['request_sha256']))
    for ctx in contexts:
        orig,H=ctx['original'],ctx['hypothesis']
        if orig not in terms:raise ValueError('context starting term exceeds declared grammar')
        wrap=lambda f:L.Imp(H,f) if H is not None else f
        for t in terms:add_formula(wrap(L.Eq(orig,t)))
        seed=wrap(L.Eq(orig,orig));out=I.Proof();i=out.emit('refl',L.Eq(orig,orig))
        if H is None:add([],seed,out.lines[0],'primitive',dict(operation='reflexivity',context=ctx))
        else:a=out.emit('tautology',L.Imp(L.Eq(orig,orig),seed));out.mp(i,a);block(definition([],seed,out.lines),dict(operation='conditional-reflexivity',context=ctx))
        available=axiom_moves
        if H is not None:available=available+I.moves(terms,[I.equation('induction-hypothesis',H,'assumption')])
        descriptors.append(I.thaw_record(dict(ctx,move_count=len(available))))
        for move in available:block(rewrite(orig,move,H),dict(operation='conditional-rewrite' if H is not None else 'rewrite',context=ctx,move=move))
        for t in terms:
            f=wrap(L.Eq(orig,t))
            for x in reversed(ctx['closure']):q=L.All(x,f);add([f],q,dict(rule='generalize',formula=I.thaw(q),variable=x),'primitive',dict(operation='generalize',context=ctx,eigenvariable=x));f=q
    if 'nat-induction' in spec['theory']['schemas'] and spec.get('enable_induction',True):
        for x in variables:
            d=I.induction_rule(variables,body,x);d['name']='leftSuccessorReceptor'+d['name'][len('inductionReceptor'):];block(d,dict(operation='induction',variable=x,template=body))
    return dict(spec=spec,terms=I.thaw_record(terms),variables=variables,basis=[formulas[k] for k in sorted(formulas)],rules=sorted(rules,key=canonical),definitions=[definitions[k] for k in sorted(definitions)],contexts=descriptors,build_seconds=time.perf_counter()-began,primitive_storage='complete deterministic stream; no primitive instances are searched by the contextual adaptation',scope='Every bounded term, equation direction/occurrence/substitution, contextual generalization and every target-variable induction alternative. Transferred items are actually searched theorems, never inserted as axioms. Generic infrastructure supplies no target proof path.')
def primitive_stream(c):
    # Each (universal formula, term) pair and each (implication, variable) pair
    # is unique because basis, terms and variable names are unique. Streaming
    # changes storage/order only; it does not sample or truncate the catalog.
    for raw in c['basis']:
        f=I.freeze(raw)
        if f[0]=='all':
            for raw_term in c['terms']:
                t=I.freeze(raw_term);q=L.Imp(f,L.substitute(f[2],f[1],t));yield dict(rule='instantiate',formula=I.thaw(q),universal=raw,term=raw_term)
        if f[0]=='imp':
            for x in c['variables']:
                if x not in L.free(f[1]):yield dict(rule='distribute',formula=I.thaw(L.Imp(L.All(x,f),L.Imp(f[1],L.All(x,f[2])))),variable=x,antecedent=I.thaw(f[1]),consequent=I.thaw(f[2]))
    body=I.freeze(c['spec']['target'])
    while body[0]=='all':body=body[2]
    if 'nat-induction' in c['spec']['theory']['schemas']:
        for x in c['variables']:yield dict(rule='induction',formula=I.thaw(I.induction_schema(x,body)),variable=x,template=I.thaw(body))
def prospective_points(c,length):
    n1=sum(len(r['premises'])==1 for r in c['rules']);n2=sum(len(r['premises'])==2 for r in c['rules']);target=c['spec']['target'];last=sum(r['conclusion']==target for r in c['rules']);placements=0
    for j in range(length):placements+=2*(len(c['rules']) if j+1<length else last)+2+n1*(j+1)+n2*(2*j)
    return dict(length=length,roots=4*length,placements=placements,inference_templates=len(c['rules']),one_input_templates=n1,two_input_templates=n2,last_row_alternatives=last,complete_words=pow(len(c['rules']),length-1)*last,status='prospective complete inventory count; no model constructed before native admission')
