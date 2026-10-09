"""Bounded Horn/equality saturation and extracted Hilbert proof certificates.

Generic proposal adaptation: no geometric oracle or theorem-specific proof.
Facts have derivation DAGs; only the solved goal's closure is materialized.
Unknown rounds/facts are search controls, never impossibility markings.
"""
import hashlib,itertools,time
import logic as L
from proof_block_search import Proof,deduce,freeze,required_blocks
from serialized_kernel import canonical,check,problem_hash,PROTOCOL

def match(p,a,variables,env):
    if p[0]=='var' and p[1] in variables:
        if p[1] in env:return env[p[1]]==a
        env[p[1]]=a;return True
    if len(p)!=len(a) or p[0]!=a[0]:return False
    for x,y in zip(p[1:],a[1:]):
        if isinstance(x,tuple):
            if not isinstance(y,tuple) or len(x)!=len(y):return False
            # Term/formula tags versus argument lists.
            if x and isinstance(x[0],str):
                if not match(x,y,variables,env):return False
            elif not all(match(s,t,variables,env) for s,t in zip(x,y)):return False
        elif x!=y:return False
    return True
def instance(formula,env):
    # All bindings refer to free target variables. Rename quantified axiom
    # variables first to avoid simultaneous-substitution capture/collisions.
    for x,t in env.items():formula=L.substitute(formula,x,t)
    return formula
def parts(a):return parts(a[1])+parts(a[2]) if a[0]=='and' else [a]
def terms(a):
    out=set()
    def term(t):
        out.add(t)
        if t[0]=='fun':
            for x in t[2]:term(x)
    def formula(f):
        if f[0]=='eq':term(f[1]);term(f[2])
        elif f[0]=='pred':
            for x in f[2]:term(x)
        elif f[0]=='all':formula(f[2])
        elif f[0]=='not':formula(f[1])
        elif f[0] in ('imp','and','or'):formula(f[1]);formula(f[2])
    formula(a);return out
def clauses(theory,library):
    out=[]
    for name,u,origin in [(n,a,'axiom') for n,a in theory['axioms'].items()]+[(b['name'],b['conclusion'],'block') for b in library]:
        u=freeze(u);renamed=u;names=[];j=0
        while renamed[0]=='all':
            x='hornBound'+str(j);j+=1;names.append(x);renamed=L.substitute(renamed[2],renamed[1],L.V(x))
        pre=[];body=renamed
        while body[0]=='imp':pre.extend(parts(body[1]));body=body[2]
        out.append(dict(name=name,universal=u,variables=names,premises=pre,conclusion=body,origin=origin))
    return out
def prove(theory,target,library=(),max_rounds=12,max_facts=1500,max_matches=200000):
    began=time.perf_counter();target=freeze(target);variables=[];body=target
    while body[0]=='all':variables.append(body[1]);body=body[2]
    premise=body[1] if body[0]=='imp' else None;goal=body[2] if premise else body
    facts={};matches=0;rules=clauses(theory,library);events=[];pool=sorted(terms(body),key=repr)
    def add(a,why):
        if a in facts:return False
        if len(facts)>=max_facts:raise OverflowError('fact budget')
        facts[a]=why
        if a[0]=='and':add(a[1],('part',a,0));add(a[2],('part',a,1))
        return True
    if premise:add(premise,('assumption',))
    for t in pool:add(L.Eq(t,t),('refl',))
    try:
        solved=False
        for roundno in range(max_rounds):
            changed=False
            for r in rules:
                snapshots=list(facts);buckets={}
                for a in snapshots:buckets.setdefault((a[0],a[1] if a[0]=='pred' else None),[]).append(a)
                states=[({},[])]
                for p in r['premises']:
                    nxt=[]
                    for env,used in states:
                        pattern=instance(p,env)
                        for a in buckets.get((p[0],p[1] if p[0]=='pred' else None),[]):
                            matches+=1
                            if matches>max_matches:raise OverflowError('match budget')
                            e=dict(env)
                            if match(pattern,a,set(r['variables'])-env.keys(),e):nxt.append((e,used+[a]))
                    states=nxt
                    if not states:break
                for env,used in states:
                    missing=[x for x in r['variables'] if x not in env]
                    for values in itertools.product(pool,repeat=len(missing)):
                        e=dict(env,**dict(zip(missing,values)));a=instance(r['conclusion'],e)
                        changed=add(a,('clause',r,e,used)) or changed
            # Equality symmetry/transitivity have ordinary eq_subst witnesses.
            eqs=[a for a in facts if a[0]=='eq']
            for a in eqs:changed=add(L.Eq(a[2],a[1]),('symmetry',a)) or changed
            by_left={}
            for a in eqs:by_left.setdefault(a[1],[]).append(a)
            for a in eqs:
                for b in by_left.get(a[2],[]):changed=add(L.Eq(a[1],b[2]),('transitivity',a,b)) or changed
            events.append(dict(round=roundno+1,facts=len(facts),matches=matches))
            if all(a in facts for a in parts(goal)):solved=True;break
            if not changed:break
    except OverflowError as exc:return dict(status='unknown_search_budget',reason=str(exc),events=events,facts=len(facts),matches=matches,seconds=time.perf_counter()-began)
    if not solved:return dict(status='unknown_horn_fragment_or_round_budget',events=events,facts=len(facts),matches=matches,seconds=time.perf_counter()-began)
    out=Proof();memo={};used_clauses=[]
    def conjunction(a):
        if a in memo:return memo[a]
        if a[0]!='and':return emit(a)
        l=conjunction(a[1]);r=conjunction(a[2]);s=out.emit('tautology',L.Imp(a[1],L.Imp(a[2],a)));i=out.mp(r,out.mp(l,s));memo[a]=i;return i
    def emit(a):
        if a in memo:return memo[a]
        why=facts[a];kind=why[0]
        if kind=='assumption':i=out.emit('assumption',a,index=0)
        elif kind=='refl':i=out.emit('refl',a)
        elif kind=='part':
            parent=why[1];j=emit(parent);s=out.emit('tautology',L.Imp(parent,a));i=out.mp(j,s)
        elif kind=='clause':
            r,env,used=why[1:];indices=[emit(v) for v in used];u=r['universal']
            i=out.emit('axiom',u,name=r['name']) if r['origin']=='axiom' else out.emit('block',u,name=r['name'],inputs=[])
            for x in r['variables']:
                t=env[x];v=L.substitute(u[2],u[1],t);s=out.emit('instantiate',L.Imp(u,v),universal=u,term=t);i=out.mp(i,s);u=v
            # A clause antecedent may itself be a conjunction. Reassemble it
            # from the matched primitive facts, without treating it as an axiom.
            while u[0]=='imp':
                j=conjunction(u[1]);i=out.mp(j,i);u=u[2]
            used_clauses.append(dict(name=r['name'],origin=r['origin'],bindings=env,conclusion=a))
        elif kind=='symmetry':
            b=why[1];j=emit(b);r=out.emit('refl',L.Eq(b[1],b[1]));template=L.Eq(L.V('hornHole'),b[1]);s=out.emit('eq_subst',L.Imp(b,L.Imp(out.lines[r]['formula'],a)),variable='hornHole',template=template,left=b[1],right=b[2]);i=out.mp(r,out.mp(j,s))
        else:
            b,c=why[1:];j=emit(b);k=emit(c);template=L.Eq(b[1],L.V('hornHole'));s=out.emit('eq_subst',L.Imp(c,L.Imp(b,a)),variable='hornHole',template=template,left=c[1],right=c[2]);i=out.mp(j,out.mp(k,s))
        memo[a]=i;return i
    final=conjunction(goal)
    if final!=len(out.lines)-1:
        s=out.emit('tautology',L.Imp(goal,goal));out.mp(final,s)
    lines=deduce(out.lines,premise) if premise else out.lines
    closed=Proof();i=closed.append(lines)
    for x in reversed(variables):i=closed.emit('generalize',L.All(x,closed.lines[i]['formula']),variable=x,source=i)
    d=dict(protocol=PROTOCOL,theory=theory,target=target,blocks=required_blocks(closed.lines,library),proof=closed.lines);checked=check(canonical(d),expected_problem_sha256=problem_hash(d))
    if checked['status']!='accepted':raise ValueError(('Horn certificate rejected',checked))
    return dict(status='accepted_proposal',request=d,check=checked,events=events,facts=len(facts),matches=matches,root_lines=len(closed.lines),used_clauses=used_clauses,seconds=time.perf_counter()-began)
def promote(found,library):
    d=found['request'];name='euclid-block-'+hashlib.sha256(canonical(d['target'])).hexdigest()[:12];b=dict(name=name,premises=[],conclusion=d['target'],proof=d['proof'])
    probe=dict(d,blocks=d['blocks']+[b],proof=[dict(rule='block',formula=b['conclusion'],name=name,inputs=[])])
    if check(canonical(probe),expected_problem_sha256=problem_hash(probe))['status']!='accepted':raise ValueError('block promotion rejected')
    library.append(b);return name
