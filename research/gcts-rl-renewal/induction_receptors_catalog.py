"""Complete finite contextual equation inference grammar, with native admission.

Infrastructure is authored: finite term grammar, one-edge equality deductions,
and a generic induction inference. No target proof sequence is supplied. The
target contributes alternative interfaces; the point solver selects a proof.
"""
import copy, hashlib, itertools, json, time
import logic as L
from certificate_boundary_search import canonical

def freeze(x):
    return tuple(freeze(v) for v in x) if isinstance(x,list) else x
def thaw(x):
    return [thaw(v) for v in x] if isinstance(x,tuple) else x
def size(t): return 1+sum(size(v) for v in t[2]) if t[0]=='fun' else 1
def term_grammar(functions,variables,bound):
    """Every signature term with at most bound nodes; variables are eigen names."""
    by={1:{('var',v) for v in variables}|{('fun',f,()) for f,a in functions.items() if a==0}}
    for n in range(2,bound+1):
        out=set()
        for f,a in sorted(functions.items()):
            if not a:continue
            for parts in itertools.product(range(1,n),repeat=a):
                if sum(parts)!=n-1:continue
                for children in itertools.product(*(by[k] for k in parts)):out.add(('fun',f,tuple(children)))
        by[n]=out
    return tuple(sorted(set().union(*by.values()),key=lambda t:canonical(thaw(t))))
def close(f,names):
    for x in reversed(names): f=L.All(x,f)
    return f
def occupied(f):
    if f[0]=='all':return {f[1]}|occupied(f[2])
    if f[0]=='eq':return L.term_free(f[1])|L.term_free(f[2])
    if f[0]=='pred':return set().union(*(L.term_free(t) for t in f[2]))
    return set().union(*(occupied(v) for v in f[1:])) if len(f)>1 else set()
def fresh(*formulas):
    used=set().union(*(occupied(f) for f in formulas));i=0
    while 'indHole'+str(i) in used:i+=1
    return 'indHole'+str(i)
class Proof:
    def __init__(self):self.lines=[]
    def emit(self,rule,formula,**kw):
        self.lines.append(dict(rule=rule,formula=thaw(formula),**{k:thaw(v) for k,v in kw.items()}));return len(self.lines)-1
    def mp(self,a,b):
        p,q=map(lambda i:freeze(self.lines[i]['formula']),(a,b))
        if q[0]!='imp' or q[1]!=p:raise ValueError('builder modus ponens mismatch')
        return self.emit('mp',q[2],antecedent=a,implication=b)
    def append(self,lines):
        offset=len(self.lines)
        for row in lines:
            c=copy.deepcopy(row)
            for k in ('antecedent','implication') if c['rule']=='mp' else ('source',) if c['rule']=='generalize' else ():
                c[k]+=offset
            if c['rule']=='block':c['inputs']=[i+offset for i in c['inputs']]
            self.lines.append(c)
        return len(self.lines)-1
def deduce(lines,hypothesis):
    """Generic Hilbert deduction, including safe generalization via distribution.

    Input has a single local assumption H. It is removed from the output. The
    variable side condition is explicit and independently checked natively.
    Blocks must be expanded first; silently treating referenced lemmas as axioms
    is forbidden.
    """
    H=freeze(hypothesis);out=Proof();lift={};plain={};dependent=[]
    def lifted(index):
        if index in lift:return lift[index]
        a=freeze(lines[index]['formula']);q=out.emit('tautology',L.Imp(a,L.Imp(H,a)));lift[index]=out.mp(plain[index],q);return lift[index]
    for index,row in enumerate(lines):
        a=freeze(row['formula']);goal=L.Imp(H,a);r=row['rule']
        dep=r=='assumption' or r=='mp' and (dependent[row['antecedent']] or dependent[row['implication']]) or r=='generalize' and dependent[row['source']]
        dependent.append(dep)
        if r=='generalize' and row['variable'] in L.free(H):raise ValueError('eigenvariable occurs free in discharged hypothesis')
        if r=='block':raise ValueError('expand local lemma references before deduction')
        if not dep:
            fields={k:v for k,v in row.items() if k not in ('rule','formula')}
            for k in ('antecedent','implication') if r=='mp' else ('source',) if r=='generalize' else ():fields[k]=plain[fields[k]]
            plain[index]=out.emit(r,a,**fields);continue
        if r=='assumption':
            if row['index']!=0 or a!=H:raise ValueError('deduction has undeclared local assumption')
            i=out.emit('tautology',goal)
        elif r=='mp':
            b=freeze(lines[row['antecedent']]['formula']);ba=L.Imp(b,a)
            schema=L.Imp(L.Imp(H,ba),L.Imp(L.Imp(H,b),goal))
            ai,bi=lifted(row['antecedent']),lifted(row['implication'])
            q=out.emit('tautology',schema);i=out.mp(ai,out.mp(bi,q))
        elif r=='generalize':
            x=row['variable']
            if x in L.free(H):raise ValueError('eigenvariable occurs free in discharged hypothesis')
            src=lifted(row['source']);p=freeze(lines[row['source']]['formula'])
            g=out.emit('generalize',L.All(x,L.Imp(H,p)),variable=x,source=src)
            d=out.emit('distribute',L.Imp(L.All(x,L.Imp(H,p)),goal),variable=x,antecedent=H,consequent=p)
            i=out.mp(g,d)
        else:raise ValueError('unexpected dependent rule')
        lift[index]=i
    if not lines:raise ValueError('empty deduction')
    last=lifted(len(lines)-1)
    if last!=len(out.lines)-1:raise ValueError('deduction final conclusion mismatch')
    return out.lines
def equation(name,formula,origin='axiom'):
    vars=[];body=formula
    while body[0]=='all':vars.append(body[1]);body=body[2]
    if body[0]!='eq':return None
    return dict(name=name,formula=formula,variables=vars,body=body,origin=origin)
def locations(t,path=()):
    yield path,t
    if t[0]=='fun':
        for i,u in enumerate(t[2]):yield from locations(u,path+(i,))
def replace(t,path,value):
    if not path:return value
    args=list(t[2]);args[path[0]]=replace(args[path[0]],path[1:],value)
    return ('fun',t[1],tuple(args))
def subst_term(t,bindings):
    if t[0]=='var':return bindings.get(t[1],t)
    return ('fun',t[1],tuple(subst_term(a,bindings) for a in t[2]))
def bind(pattern,t,variables,result):
    if pattern[0]=='var' and pattern[1] in variables:
        if pattern[1] in result:return result if result[pattern[1]]==t else None
        return dict(result,**{pattern[1]:t})
    if pattern[0]!=t[0] or pattern[1]!=t[1]:return None
    if pattern[0]=='var':return result
    if len(pattern[2])!=len(t[2]):return None
    for a,b in zip(pattern[2],t[2]):
        result=bind(a,b,variables,result)
        if result is None:return None
    return result
def moves(terms,rules):
    allowed=set(terms);result={}
    for before in terms:
        for path,sub in locations(before):
            for rule in rules:
                for direction in (1,-1):
                    left,right=rule['body'][1:] if direction==1 else rule['body'][1:][::-1]
                    bindings=bind(left,sub,set(rule['variables']),{})
                    if bindings is None:continue
                    missing=[x for x in rule['variables'] if x not in bindings]
                    for values in itertools.product(terms,repeat=len(missing)):
                        env=dict(bindings,**dict(zip(missing,values)))
                        after=replace(before,path,subst_term(right,env))
                        if after not in allowed or after==before:continue
                        m=dict(before=before,after=after,path=path,bindings=env,direction=direction,rule=rule)
                        result[canonical(thaw_record(m))]=m
    return [result[k] for k in sorted(result)]
def thaw_record(x):
    if isinstance(x,dict):return {k:thaw_record(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [thaw_record(v) for v in x]
    return x
def edge_proof(move):
    """One equality edge, not a searched multi-edge derivation."""
    out=Proof();rule=move['rule'];f=rule['formula']
    i=out.emit('axiom',f,name=rule['name']) if rule['origin']=='axiom' else out.emit('assumption',f,index=0)
    for x in rule['variables']:
        t=move['bindings'][x];q=L.substitute(f[2],f[1],t)
        a=out.emit('instantiate',L.Imp(f,q),universal=f,term=t);i=out.mp(i,a);f=q
    left,right=f[1:]
    if move['direction']==-1:
        h=fresh(f);q=L.Eq(right,left);rf=out.emit('refl',L.Eq(left,left))
        a=out.emit('eq_subst',L.Imp(f,L.Imp(L.Eq(left,left),q)),variable=h,template=L.Eq(L.V(h),left),left=left,right=right)
        i=out.mp(rf,out.mp(i,a));left,right=right,left
    before,after=move['before'],move['after']
    if before!=left or after!=right:
        h=fresh(L.Eq(before,after),L.Eq(left,right));template=L.Eq(before,replace(before,move['path'],L.V(h)))
        rf=out.emit('refl',L.Eq(before,before));a=out.emit('eq_subst',L.Imp(L.Eq(left,right),L.Imp(L.Eq(before,before),L.Eq(before,after))),variable=h,template=template,left=left,right=right)
        i=out.mp(rf,out.mp(i,a))
    if freeze(out.lines[-1]['formula'])!=L.Eq(before,after):raise ValueError('edge expansion mismatch')
    return out.lines
def definition(premises,conclusion,proof):
    d=dict(premises=thaw_record(premises),conclusion=thaw_record(conclusion),proof=proof)
    return dict(name='inductionReceptor'+hashlib.sha256(canonical(d)).hexdigest(),**d)
def rewrite(original,move,hypothesis=None):
    before,after=move['before'],move['after'];p,q=L.Eq(original,before),L.Eq(original,after)
    out=Proof();H=hypothesis;input_formula=p if H is None else L.Imp(H,p)
    source=out.emit('assumption',input_formula,index=0)
    edge=L.Eq(before,after);proof=edge_proof(move);ei=out.append(proof if H is None else deduce(proof,H))
    hole=fresh(p,q,edge);subst=L.Imp(edge,L.Imp(p,q))
    si=out.emit('eq_subst',subst,variable=hole,template=L.Eq(original,L.V(hole)),left=before,right=after)
    if H is None:out.mp(source,out.mp(ei,si));conclusion=q
    else:
        lift=out.emit('tautology',L.Imp(subst,L.Imp(L.Imp(H,edge),L.Imp(H,L.Imp(p,q)))))
        consequence=out.mp(ei,out.mp(si,lift))
        combine=out.emit('tautology',L.Imp(L.Imp(H,L.Imp(p,q)),L.Imp(L.Imp(H,p),L.Imp(H,q))))
        out.mp(source,out.mp(consequence,combine));conclusion=L.Imp(H,q)
    return definition([input_formula],conclusion,out.lines)
def induction_schema(x,p):
    base=L.substitute(p,x,L.F('zero'));step=L.All(x,L.Imp(p,L.substitute(p,x,L.F('succ',L.V(x)))))
    return close(L.Imp(('and',base,step),L.All(x,p)),sorted(L.free(p)-{x}))
def induction_rule(variables,body,x):
    params=[v for v in variables if v!=x];base=L.substitute(body,x,L.F('zero'));step=L.All(x,L.Imp(body,L.substitute(body,x,L.F('succ',L.V(x)))))
    premises=[close(base,params),close(step,params)];out=Proof();src=[]
    for j,formula in enumerate(premises):
        i=out.emit('assumption',formula,index=j);f=formula
        for y in params:
            q=L.substitute(f[2],f[1],L.V(y));a=out.emit('instantiate',L.Imp(f,q),universal=f,term=L.V(y));i=out.mp(i,a);f=q
        src.append(i)
    conj=('and',base,step);a=out.emit('tautology',L.Imp(base,L.Imp(step,conj)));ci=out.mp(src[1],out.mp(src[0],a))
    schema=induction_schema(x,body);si=out.emit('induction',schema,variable=x,template=body)
    for y in sorted(L.free(body)-{x}):
        q=L.substitute(schema[2],schema[1],L.V(y));a=out.emit('instantiate',L.Imp(schema,q),universal=schema,term=L.V(y));si=out.mp(si,a);schema=q
    result=out.mp(ci,si);f=L.All(x,body)
    a=out.emit('instantiate',L.Imp(f,body),universal=f,term=L.V(x));result=out.mp(result,a)
    for y in reversed(variables):result=out.emit('generalize',L.All(y,freeze(out.lines[result]['formula'])),variable=y,source=result)
    return definition(premises,close(body,variables),out.lines)
def catalog(spec):
    """Complete within a declared contextual equational adaptation, not full FOL.

    Every bounded term, axiom, orientation, occurrence and missing substitution
    is retained. All target-bound variables are induction alternatives. Open
    eigen terms remain available although the external target is closed.
    """
    began=time.perf_counter();target=freeze(spec['target']);variables=[];body=target
    while body[0]=='all':variables.append(body[1]);body=body[2]
    if body[0]!='eq' or len(set(variables))!=len(variables) or L.free(body)-set(variables):raise ValueError('closed distinctly quantified equation required')
    terms=term_grammar(spec['theory']['functions'],variables,spec['term_bound'])
    equations=[q for n,f in sorted(spec['theory']['axioms'].items()) for q in [equation(n,freeze(f))] if q]
    axiom_moves=moves(terms,equations);contexts=[dict(original=body[1],hypothesis=None,goal=body,closure=variables,kind='direct',variable=None)]
    if 'nat-induction' in spec['theory']['schemas'] and spec.get('enable_induction',True):
        for x in variables:
            others=[v for v in variables if v!=x];base=L.substitute(body,x,L.F('zero'));step=L.substitute(body,x,L.F('succ',L.V(x)))
            contexts += [dict(original=base[1],hypothesis=None,goal=base,closure=others,kind='base',variable=x),dict(original=step[1],hypothesis=body,goal=L.Imp(body,step),closure=others+[x],kind='step',variable=x)]
    formulas={};rules=[];definitions={};seen=set();descriptors=[]
    def add_formula(f):formulas[canonical(thaw(f))]=thaw(f)
    def add(premises,conclusion,command,kind,description):
        key=canonical(thaw_record([premises,conclusion,command]));add_formula(conclusion)
        for p in premises:add_formula(p)
        if key in seen:return
        seen.add(key);rules.append(dict(premises=thaw_record(premises),conclusion=thaw_record(conclusion),command=command,kind=kind,description=thaw_record(description)))
    def block(d,description):
        definitions[d['name']]=d;add(d['premises'],d['conclusion'],dict(rule='block',formula=d['conclusion'],name=d['name']), 'derived',description)
    for ctx in contexts:
        orig,H=ctx['original'],ctx['hypothesis']
        if orig not in terms:raise ValueError('context starting term exceeds declared grammar')
        wrap=lambda f:L.Imp(H,f) if H is not None else f
        for t in terms:add_formula(wrap(L.Eq(orig,t)))
        seed=wrap(L.Eq(orig,orig));out=Proof();i=out.emit('refl',L.Eq(orig,orig))
        if H is None:add([],seed,out.lines[0],'primitive',dict(operation='reflexivity',context=ctx))
        else:
            a=out.emit('tautology',L.Imp(L.Eq(orig,orig),seed));out.mp(i,a);block(definition([],seed,out.lines),dict(operation='conditional-reflexivity',context=ctx))
        available=axiom_moves
        if H is not None:available=available+moves(terms,[equation('induction-hypothesis',H,'assumption')])
        descriptors.append(thaw_record(dict(ctx,move_count=len(available))))
        for move in available:block(rewrite(orig,move,H),dict(operation='conditional-rewrite' if H is not None else 'rewrite',context=ctx,move=move))
        # Generalize every available contextual equation, not just the goal.
        for t in terms:
            f=wrap(L.Eq(orig,t))
            for x in reversed(ctx['closure']):
                q=L.All(x,f);add([f],q,dict(rule='generalize',formula=thaw(q),variable=x),'primitive',dict(operation='generalize',context=ctx,eigenvariable=x));f=q
    if 'nat-induction' in spec['theory']['schemas'] and spec.get('enable_induction',True):
        for x in variables:block(induction_rule(variables,body,x),dict(operation='induction',variable=x,template=body))
    # A complete explicit primitive-scheme diagnostic catalog is exposed as
    # zero-input alternatives. Distribution parameters use every implication
    # occurring in the finite contextual formula basis, with each eigen name.
    primitive=[];seed_formulas=list(formulas.values())
    for raw in seed_formulas:
        f=freeze(raw)
        if f[0]=='all':
            for t in terms:
                q=L.Imp(f,L.substitute(f[2],f[1],t));primitive.append(dict(rule='instantiate',formula=thaw(q),universal=raw,term=thaw(t)))
        if f[0]=='imp':
            for x in variables:
                if x in L.free(f[1]):continue
                q=L.Imp(L.All(x,f),L.Imp(f[1],L.All(x,f[2])))
                primitive.append(dict(rule='distribute',formula=thaw(q),variable=x,antecedent=thaw(f[1]),consequent=thaw(f[2])))
    for x in variables:
        if 'nat-induction' in spec['theory']['schemas']:primitive.append(dict(rule='induction',formula=thaw(induction_schema(x,body)),variable=x,template=thaw(body)))
    primitive=list({canonical(c):c for c in primitive}.values())
    # Primitive schemes are a separate documented finite catalog. The measured
    # equation grammar uses their complete native expansions inside definitions;
    # it does not pretend to search their arbitrary FOL combinations.
    return dict(spec=spec,terms=thaw_record(terms),variables=variables,basis=[formulas[k] for k in sorted(formulas)],rules=sorted(rules,key=lambda r:canonical(r)),definitions=[definitions[k] for k in sorted(definitions)],primitive_schemes=sorted(primitive,key=canonical),contexts=descriptors,build_seconds=time.perf_counter()-began,scope='Complete contextual-equation adaptation: every bounded term and one-edge axiom/IH rewrite, every context-equation generalization, every target-variable induction interface. Generic deduction is authored infrastructure; no target proof or chosen rewrite path is supplied. The separate primitive-scheme catalog is exposed but is not the searched grammar.')
