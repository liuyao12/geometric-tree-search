"""Mined unary formula contexts and typed term/binder parameters.

Alpha normalization is used only by the proposal matcher. Actual formula words,
ground rules, references and ambient scope markings are never normalized away.
Every proposed instance still expands to the original full-capacity placements.
Context holes replace free occurrences of the designated term; bound variables
use de Bruijn distances so filling a hole cannot capture an inserted variable.
"""
import itertools
import logic as L
import movable_proof_regions as M
import adaptive_receptor_clusters as C
import check_movable_regions as A

def normal_term(t,binders=()):
    if t[0]=='var':return ('bound',binders.index(t[1])) if t[1] in binders else t
    return ('fun',t[1],tuple(normal_term(v,binders) for v in t[2]))

def normal(a,binders=()):
    if a[0]=='all':return ('all',normal(a[2],(a[1],)+binders))
    if a[0]=='pred':return ('pred',a[1],tuple(normal_term(t,binders) for t in a[2]))
    if a[0]=='eq':return ('eq',normal_term(a[1],binders),normal_term(a[2],binders))
    return (a[0],)+tuple(normal(v,binders) for v in a[1:])

def bound(t):return t[0]=='bound' or (t[0]=='fun' and any(bound(v) for v in t[2]))

def terms(a):
    def inside(t):
        if not bound(t):yield t
        if t[0]=='fun':
            for v in t[2]:yield from inside(v)
    if a[0]=='pred':
        for t in a[2]:yield from inside(t)
    elif a[0]=='eq':
        yield from inside(a[1]);yield from inside(a[2])
    else:
        for v in a[1:]:yield from terms(v)

def transform(a,term_map):
    def term(t):
        mapped=term_map(t)
        if mapped!=t:return mapped
        return ('fun',t[1],tuple(term(v) for v in t[2])) if t[0]=='fun' else t
    if a[0]=='pred':return ('pred',a[1],tuple(term(t) for t in a[2]))
    if a[0]=='eq':return ('eq',term(a[1]),term(a[2]))
    return (a[0],)+tuple(transform(v,term_map) for v in a[1:])

def context(a,t):return transform(a,lambda v:('hole',) if v==t else v)
def fill(a,t):return transform(a,lambda v:t if v==('hole',) else v)
def contains_hole(a):return ('hole',) in set(terms(a))

def bind(env,key,value):
    if key in env:return env if env[key]==value else None
    return dict(env,**{key:value})

def term_match(p,t,env):
    if p[0]=='tmeta':return bind(env,p[1],t)
    if t[0]!='fun' or len(p[2])!=len(t[2]):return None
    env=bind(env,p[1],('symbol',t[1],len(t[2])))
    for q,v in zip(p[2],t[2]):
        if env is None:return None
        env=term_match(q,v,env)
    return env

def resolve(p,env):
    if p[0]=='tmeta':return env.get(p[1])
    symbol=env.get(p[1]);args=[resolve(v,env) for v in p[2]]
    return ('fun',symbol[1],tuple(args)) if symbol and all(v is not None for v in args) else None

def formula_matches(p,a,env):
    kind=p[0]
    if kind=='fmeta':
        e=bind(env,p[1],normal(a));return [] if e is None else [e]
    if kind=='papply':
        normalized=normal(a);known=resolve(p[2],env)
        candidates=[known] if known is not None else sorted(set(terms(normalized)),key=C.digest)
        out=[]
        for t in candidates:
            e=term_match(p[2],t,env)
            if e is None:continue
            if p[1] in e:
                if fill(e[p[1]],t)==normalized:out.append(e)
            else:
                template=context(normalized,t)
                if contains_hole(template):out.append(dict(e,**{p[1]:template}))
        return out
    if kind!=a[0]:return []
    if kind=='all':
        e=term_match(p[1],L.V(a[1]),env)
        return [] if e is None else formula_matches(p[2],a[2],e)
    if kind=='eq':
        e=term_match(p[1],a[1],env)
        e=term_match(p[2],a[2],e) if e is not None else None
        return [] if e is None else [e]
    states=[env]
    for q,v in zip(p[1:],a[1:]):states=[e for s in states for e in formula_matches(q,v,s)]
    return states if len(p)==len(a) else []

def matches(node,r,env=None):
    if node['kind']!=r['kind'] or len(node['inputs'])!=len(r['inputs']) or len(node['guards'])!=len(r['guards']):return []
    states=[dict(env or {})]
    for key,p in node['parameters'].items():
        value=L.V(r['parameters'][key]) if key=='variable' else r['parameters'][key]
        if key=='side':states=states if p==value else [];continue
        states=[e for s in states for e in [term_match(p,value,s)] if e is not None]
    for p,x in zip(node['guards'],r['guards']):states=[e for s in states for e in [term_match(p,L.V(x),s)] if e is not None]
    for p,a in zip(tuple(node['inputs'])+(node['output'],),tuple(r['inputs'])+(r['output'],)):
        states=[e for s in states for e in formula_matches(p,a,s)]
    unique={C.digest(e):e for e in states};return [unique[k] for k in sorted(unique)]

class Abstract:
    def __init__(self,rows):
        self.free={};self.predicates={};self.functions={};self.binders={};self.serial=0
        for r in rows:
            if r['kind']=='generalize':self.binders[r['output']]=self.variable(r['parameters']['variable'])
    def fresh(self):
        key='T'+str(self.serial);self.serial+=1;return ('tmeta',key)
    def variable(self,x):
        if x not in self.free:self.free[x]=self.fresh()
        return self.free[x]
    def term(self,t,local):
        if t[0]=='var':return local[t[1]] if t[1] in local else self.variable(t[1])
        name=(t[1],len(t[2]));self.functions.setdefault(name,'F'+str(len(self.functions)))
        return ('fapply',self.functions[name],tuple(self.term(v,local) for v in t[2]))
    def formula(self,a,local=None):
        local=dict(local or {});k=a[0]
        if k=='all':
            if a not in self.binders:self.binders[a]=self.fresh()
            v=self.binders[a];local[a[1]]=v
            return ('all',v,self.formula(a[2],local))
        if k=='pred':
            if len(a[2])>1:raise ValueError('mining supports nullary or unary donor predicates')
            identity=(a[1],len(a[2]));self.predicates.setdefault(identity,'P'+str(len(self.predicates)))
            key=self.predicates[identity]
            return ('papply',key,self.term(a[2][0],local)) if a[2] else ('fmeta',key)
        if k=='eq':return ('eq',self.term(a[1],local),self.term(a[2],local))
        return (k,)+tuple(self.formula(v,local) for v in a[1:])
    def node(self,r,refs):
        params={k:(v if k=='side' else self.variable(v) if k=='variable' else self.term(v,{}))
                for k,v in r['parameters'].items() if k!='universal'}
        return dict(kind=r['kind'],parameters=params,guards=[self.variable(x) for x in r['guards']],
            inputs=[self.formula(a) for a in r['inputs']],output=self.formula(r['output']),refs=refs)

def promote(spec,catalog,result,library=(),maximum=6):
    if result['proof'] is None:raise ValueError('mine only freshly completed proofs')
    tiles=[A.tile(catalog['rules'],spec,k) for k in result['placements']]
    checked=A.certificate(catalog['rules'],spec,result,tiles)
    rows=sorted((M.freeze(k) for k in result['placements'] if k[1]>=0),key=lambda k:k[0])
    old={t['name']:t for t in library};known={C.digest(t['pattern']) for t in library};out=[]
    for first in range(len(rows)):
        for size in range(2,min(maximum,len(rows)-first)+1):
            window=rows[first:first+size];rules=[catalog['rules'][k[1]] for k in window]
            if any(r['kind'] not in ('mp','forall-elim','generalize','projection') for r in rules):continue
            abstract=Abstract(rules);inside={k[0]:i for i,k in enumerate(window)};outside={};pattern=[]
            try:
                for (_,rid,refs),r in zip(window,rules):
                    contacts=[]
                    for ref in refs:
                        if ref in inside:contacts.append(('inside',inside[ref]))
                        else:outside.setdefault(ref,len(outside));contacts.append(('outside',outside[ref]))
                    pattern.append(abstract.node(r,contacts))
            except ValueError:continue
            identity=C.digest(pattern)
            if identity in known:continue
            children=[]
            for done in result.get('solution_hints',()):
                item=done['item'];members=M.freeze(item['members'])
                if item['template'] in old and set(members)<set(window):
                    children.append(dict(template=item['template'],offsets=[inside[k[0]] for k in members],hint_id=done['id'],kind='completed_ordering_hint'))
            level=1+max((old[c['template']]['level'] for c in children),default=0)
            out.append(dict(name='quantifier-family-'+identity[:20],pattern=pattern,children=children,level=level,
                source=dict(spec=spec,catalog=catalog,result=result,members=window,check=checked)))
            known.add(identity)
    return out
