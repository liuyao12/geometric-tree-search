"""Independent, fail-closed TSTP checker for the measured first-order fragment.

Each inference is checked by a *new* finite Herbrand/EUF refutation of its
parents and negated conclusion. A finite grounding that stays satisfiable is
unknown, never evidence against validity. No E inference name is trusted.
Proofs involving E-introduced Skolem/definition symbols are rejected rather
than treating equisatisfiability as logical entailment.
"""
import itertools,json,re,time

TOKEN=re.compile(r"\s*(<=>|<~>|=>|<=|!=|[!?:~&|=(),\[\].]|\$[A-Za-z0-9_]+|[A-Za-z0-9_]+|'(?:\\.|[^'\\])*')")

def tokens(text):
    out=[];p=0
    while p<len(text):
        if not text[p:].strip():break
        m=TOKEN.match(text,p)
        if not m:raise ValueError('unsupported token at '+text[p:p+80])
        out.append(m.group(1));p=m.end()
    return out

class Parser:
    def __init__(self,ts):self.ts=ts;self.i=0
    def peek(self):return self.ts[self.i] if self.i<len(self.ts) else None
    def take(self,t=None):
        a=self.peek()
        if a is None or (t is not None and a!=t):raise ValueError('expected '+str(t)+' got '+str(a))
        self.i+=1;return a
    def term(self):
        name=self.take()
        if name[0].isupper():return ('var',name)
        if name[0] in "'" or not re.fullmatch(r'[a-z][A-Za-z0-9_]*|\$true|\$false',name):raise ValueError('term symbol')
        args=[]
        if self.peek()=='(':
            self.take('(');args.append(self.term())
            while self.peek()==',':self.take(',');args.append(self.term())
            self.take(')')
        return ('fun',name,tuple(args))
    def unary(self):
        t=self.peek()
        if t=='~':self.take();return ('not',self.unary())
        if t in ('!','?'):
            q=self.take();self.take('[');vs=[self.take()]
            while self.peek()==',':self.take();vs.append(self.take())
            self.take(']');self.take(':');f=self.unary()
            for v in reversed(vs):f=('forall' if q=='!' else 'exists',v,f)
            return f
        if t=='(':
            self.take();f=self.formula();self.take(')');return f
        a=self.term()
        if self.peek() in ('=','!='):
            sign=self.take();f=('eq',a,self.term());return ('not',f) if sign=='!=' else f
        if a[0]!='fun':raise ValueError('variable as predicate')
        if a[1]=='$true':return ('top',)
        if a[1]=='$false':return ('bot',)
        return ('pred',a[1],a[2])
    def formula(self):
        f=self.unary();op=self.peek()
        # TPTP has no mixed binary precedence; input/output are parenthesized.
        if op in ('&','|','=>','<=','<=>','<~>'):
            self.take();g=self.formula()
            if op=='<=':return ('imp',g,f)
            if op=='<=>':return ('and',('imp',f,g),('imp',g,f))
            if op=='<~>':return ('not',('and',('imp',f,g),('imp',g,f)))
            return ({'&':'and','|':'or','=>':'imp'}[op],f,g)
        return f
    def metadata(self):
        if self.peek()=='[':
            self.take();xs=[]
            if self.peek()!=']':
                xs.append(self.metadata())
                while self.peek()==',':self.take();xs.append(self.metadata())
            self.take(']');return xs
        n=self.take()
        if n.startswith("'"):n=bytes(n[1:-1],'utf8').decode('unicode_escape')
        if self.peek()!='(':return n
        self.take();xs=[]
        if self.peek()!=')':
            xs.append(self.metadata())
            while self.peek()==',':self.take();xs.append(self.metadata())
        self.take(')');return dict(head=n,args=xs)

def formula_text(text):
    p=Parser(tokens(text));f=p.formula()
    if p.peek() is not None:raise ValueError('trailing formula')
    return f

def records(output):
    start='% SZS output start CNFRefutation';end='% SZS output end CNFRefutation'
    if output.count(start)!=1 or output.count(end)!=1:raise ValueError('missing/ambiguous refutation envelope')
    text=output.split(start,1)[1].split(end,1)[0]
    p=Parser(tokens(text));out=[]
    while p.peek():
        lang=p.take()
        if lang not in ('fof','cnf'):raise ValueError('unsupported language '+lang)
        p.take('(');n=p.take();p.take(',');role=p.take();p.take(',');f=p.formula();p.take(',');source=p.metadata()
        useful=None
        if p.peek()==',':p.take();useful=p.metadata()
        p.take(')');p.take('.')
        out.append(dict(language=lang,name=n,role=role,formula=f,source=source,useful=useful))
    return out

def free(f,bound=frozenset()):
    if f[0]=='var':return set() if f[1] in bound else {f[1]}
    if f[0]=='fun':return set().union(*(free(t,bound) for t in f[2]))
    if f[0]=='pred':return set().union(*(free(t,bound) for t in f[2]))
    if f[0] in ('forall','exists'):return free(f[2],bound|{f[1]})
    return set().union(*(free(a,bound) for a in f[1:] if isinstance(a,tuple)))

def closed(f):
    for v in sorted(free(f),reverse=True):f=('forall',v,f)
    return f

def alpha(f,binders=()):
    """Bound variable names are immaterial; free names remain significant."""
    h=f[0]
    if h=='var':
        for i,v in enumerate(reversed(binders)):
            if f[1]==v:return ('bound',i)
        return f
    if h in ('forall','exists'):return (h,alpha(f[2],binders+(f[1],)))
    if h in ('fun','pred'):return (h,f[1],tuple(alpha(t,binders) for t in f[2]))
    return (h,*(alpha(a,binders) if isinstance(a,tuple) else a for a in f[1:]))

def nnf(f,positive=True):
    h=f[0]
    if h=='not':return nnf(f[1],not positive)
    if h=='imp':return nnf(('or',('not',f[1]),f[2]),positive)
    if h in ('and','or'):
        q=h if positive else {'and':'or','or':'and'}[h]
        return (q,nnf(f[1],positive),nnf(f[2],positive))
    if h in ('forall','exists'):
        q=h if positive else {'forall':'exists','exists':'forall'}[h]
        return (q,f[1],nnf(f[2],positive))
    if h in ('top','bot'):return (h if positive else {'top':'bot','bot':'top'}[h],)
    if h not in ('eq','pred'):raise ValueError('unexpected atom')
    return ('lit',positive,f)

def substitute(t,env):
    if t[0]=='var':return env.get(t[1],t)
    if t[0]=='fun':return ('fun',t[1],tuple(substitute(a,env) for a in t[2]))
    if t[0]=='pred':return ('pred',t[1],tuple(substitute(a,env) for a in t[2]))
    if t[0]=='eq':return ('eq',substitute(t[1],env),substitute(t[2],env))
    raise ValueError('substitution atom')

def clauses_from(formulas):
    counter=[0];skolem=[]
    def name(prefix):counter[0]+=1;return '__checker_'+prefix+str(counter[0])
    def sk(f,env,universals):
        h=f[0]
        if h=='forall':
            v=('var',name('u'));return sk(f[2],{**env,f[1]:v},universals+[v])
        if h=='exists':
            n=name('s');skolem.append((n,len(universals)));t=('fun',n,tuple(universals))
            return sk(f[2],{**env,f[1]:t},universals)
        if h in ('and','or'):return (h,sk(f[1],env,universals),sk(f[2],env,universals))
        if h=='lit':return ('lit',f[1],substitute(f[2],env))
        return f
    def cnf(f):
        if f[0]=='top':return []
        if f[0]=='bot':return [()]
        if f[0]=='lit':return [((f[1],f[2]),)]
        a,b=cnf(f[1]),cnf(f[2])
        if f[0]=='and':return a+b
        product=[x+y for x in a for y in b]
        if len(product)>200000:raise ValueError('clausification limit')
        return product
    clauses=[]
    for f in formulas:clauses+=cnf(sk(nnf(closed(f)),{},[]))
    return clauses,skolem

def atom_terms(atom):
    args=atom[2] if atom[0]=='pred' else atom[1:]
    out=set()
    def visit(t):
        if t[0]=='fun':
            for a in t[2]:visit(a)
            out.add(t)
    for t in args:visit(t)
    return out

def grounding(formulas):
    clauses,skolem=clauses_from(formulas)
    pool=set()
    for c in clauses:
        for sign,a in c:
            pool.update(t for t in atom_terms(a) if not free(t))
    if not pool:pool.add(('fun','__checker_nonempty',()))
    initial=sorted(pool,key=repr)
    for n,arity in skolem:
        for args in itertools.product(initial,repeat=arity):pool.add(('fun',n,args))
    pool=sorted(pool,key=repr);out=set()
    for clause in clauses:
        vs=sorted(set().union(*(free(a) for s,a in clause)))
        if len(pool)**len(vs)>200000:raise ValueError('grounding limit')
        for values in itertools.product(pool,repeat=len(vs)):
            env=dict(zip(vs,values));ground=frozenset((s,substitute(a,env)) for s,a in clause)
            if any((not s,a) in ground for s,a in ground):continue
            out.add(tuple(sorted(ground,key=repr)))
    return sorted(out,key=repr),pool

def congruence_conflict(assignment,atoms):
    terms=set()
    for a in atoms:terms.update(atom_terms(a))
    parent={t:t for t in terms}
    def root(t):
        while parent[t]!=t:t=parent[t]
        return t
    def merge(a,b):
        a,b=root(a),root(b)
        if a==b:return False
        parent[a]=b;return True
    for a,v in assignment.items():
        if a[0]=='eq' and v:merge(a[1],a[2])
    changed=True
    while changed:
        changed=False;seen={}
        for t in sorted(terms,key=repr):
            k=(t[1],tuple(root(a) for a in t[2]))
            if k in seen:changed=merge(t,seen[k]) or changed
            else:seen[k]=t
    predicates={}
    for a,v in assignment.items():
        if a[0]=='eq':
            if not v and root(a[1])==root(a[2]):return True
        else:
            k=(a[1],tuple(root(t) for t in a[2]))
            if k in predicates and predicates[k]!=v:return True
            predicates[k]=v
    return False

def relation_conflict(assignment,atoms):
    """Independent replay: relation closure instead of union-find."""
    terms=sorted(set().union(*(atom_terms(a) for a in atoms)),key=repr)
    relation={(t,t) for t in terms}
    for a,v in assignment.items():
        if a[0]=='eq' and v:relation.update(((a[1],a[2]),(a[2],a[1])))
    old=None
    while old!=len(relation):
        old=len(relation)
        for a in terms:
            related=[b for b in terms if (a,b) in relation]
            relation.update((b,c) for b in related for c in related)
        for a,b in itertools.product(terms,repeat=2):
            if a[1]==b[1] and len(a[2])==len(b[2]) and all((x,y) in relation for x,y in zip(a[2],b[2])):relation.add((a,b))
    preds=[(a,v) for a,v in assignment.items() if a[0]=='pred']
    for a,v in assignment.items():
        if a[0]=='eq' and not v and (a[1],a[2]) in relation:return True
    for (a,v),(b,w) in itertools.product(preds,repeat=2):
        if v!=w and a[1]==b[1] and len(a[2])==len(b[2]) and all((x,y) in relation for x,y in zip(a[2],b[2])):return True
    return False

def refute(clauses,node_limit=200000):
    atoms=sorted({a for c in clauses for s,a in c},key=repr);indices={a:i for i,a in enumerate(atoms)};nodes=[0]
    def search(asn):
        nodes[0]+=1
        if nodes[0]>node_limit:raise ValueError('checker node limit')
        for i,c in enumerate(clauses):
            if all(a in asn and asn[a]!=s for s,a in c):return ['clause',i]
        if congruence_conflict(asn,atoms):return ['euf']
        active=[(s,a) for c in clauses if not any(asn.get(a)==s for s,a in c) for s,a in c if a not in asn]
        if not active:return None
        counts={a:sum(b==a for s,b in active) for s,a in active}
        # Unit literals are tried first, but both truth branches are certified.
        units=[a for c in clauses if not any(asn.get(a)==s for s,a in c) for unresolved in [[a for s,a in c if a not in asn]] if len(unresolved)==1 for a in unresolved]
        a=units[0] if units else min(counts,key=lambda a:(-counts[a],repr(a)))
        lo=search({**asn,a:False})
        if lo is None:return None
        hi=search({**asn,a:True})
        if hi is None:return None
        return ['split',indices[a],lo,hi]
    tree=search({});return dict(status='refuted' if tree is not None else 'unknown_ground_satisfiable',atoms=atoms,tree=tree,nodes=nodes[0])

def replay_refutation(clauses,proof):
    atoms=sorted({a for c in clauses for s,a in c},key=repr)
    if atoms!=proof['atoms']:raise ValueError('atom identity')
    def visit(t,asn):
        if not isinstance(t,list) or not t:raise ValueError('malformed refutation')
        if t[0]=='clause':
            if len(t)!=2 or type(t[1]) is not int or not 0<=t[1]<len(clauses):raise ValueError('clause leaf')
            if not all(a in asn and asn[a]!=s for s,a in clauses[t[1]]):raise ValueError('clause does not conflict')
        elif t[0]=='euf':
            if len(t)!=1 or not relation_conflict(asn,atoms):raise ValueError('invalid equality conflict')
        elif t[0]=='split':
            if len(t)!=4 or type(t[1]) is not int or not 0<=t[1]<len(atoms):raise ValueError('branch')
            a=atoms[t[1]]
            if a in asn:raise ValueError('repeated split')
            visit(t[2],{**asn,a:False});visit(t[3],{**asn,a:True})
        else:raise ValueError('unknown refutation step')
    visit(proof['tree'],{});return True

def entails(parents,child):
    began=time.perf_counter();cs,pool=grounding(parents+[('not',child)])
    p=refute(cs)
    if p['status']=='refuted':replay_refutation(cs,p)
    return dict(status='checked' if p['status']=='refuted' else 'unknown',ground_clauses=len(cs),ground_terms=len(pool),refutation=p,seconds=time.perf_counter()-began)

def leaves(source):
    if isinstance(source,str):return [source]
    if not isinstance(source,dict) or source.get('head')!='inference' or len(source['args'])!=3:raise ValueError('opaque inference source')
    return [p for a in source['args'][2] for p in leaves(a)]

def symbol_names(f):
    if f[0] in ('fun','pred'):return {f[1]}|set().union(*(symbol_names(t) for t in f[2]))
    if f[0]=='var':return set()
    return set().union(*(symbol_names(a) for a in f[1:] if isinstance(a,tuple)))

def validate_signature(f,mapping):
    if f[0] in ('fun','pred'):
        signature=mapping['function_arities'] if f[0]=='fun' else mapping['predicate_arities']
        if signature.get(f[1])!=len(f[2]):raise ValueError('undeclared symbol or arity')
        for t in f[2]:validate_signature(t,mapping)
    elif f[0]!='var':
        for a in f[1:]:
            if isinstance(a,tuple):validate_signature(a,mapping)

def native_formula(f,mapping):
    """Direct AST conversion independent of the producer's TPTP printer."""
    h=f[0]
    if h=='var':return ('var',f[1])
    if h=='fun':return ('fun',mapping['functions'][f[1]],tuple(native_formula(a,mapping) for a in f[2]))
    if h=='pred':return ('pred',mapping['predicates'][f[1]],tuple(native_formula(a,mapping) for a in f[2]))
    if h in ('all','forall','exists'):return ('forall' if h!='exists' else 'exists',f[1],native_formula(f[2],mapping))
    if h in ('bot','top'):return (h,)
    if h in ('eq','imp','and','or','not'):return (h,*(native_formula(a,mapping) for a in f[1:]))
    raise ValueError('unsupported native AST')

def check_output(output,mapping,input_path):
    began=time.perf_counter();rs=records(output);known={};checks=[]
    expected={e['name']:(e,native_formula(e['formula'],mapping)) for e in mapping['entries']}
    allowed=set(mapping['functions'].values())|set(mapping['predicates'].values())
    conjectures=set();negations=set();used_inputs=[]
    for r in rs:
        n=r['name'];s=r['source'];f=r['formula']
        if n in known:raise ValueError('duplicate step '+n)
        if symbol_names(f)-allowed:raise ValueError('unaccounted introduced symbol')
        validate_signature(f,mapping)
        if isinstance(s,dict) and s.get('head')=='file':
            if len(s['args'])!=2 or s['args'][0]!=input_path or s['args'][1] not in expected:raise ValueError('input identity')
            e,want=expected[s['args'][1]]
            if r['role']!=e['role'] or alpha(f)!=alpha(want):raise ValueError('input formula/role mismatch')
            if e['role']=='conjecture':conjectures.add(n)
            else:used_inputs.append(e['name'])
            checks.append(dict(name=n,status='checked_input',original_name=e['original_name']))
        else:
            ps=list(dict.fromkeys(leaves(s)))
            if any(p not in known for p in ps):raise ValueError('forward/missing parent')
            rule=s['args'][0]
            if rule=='assume_negation':
                if len(ps)!=1 or ps[0] not in conjectures or alpha(nnf(f))!=alpha(nnf(known[ps[0]]['formula'],False)):raise ValueError('incorrect conjecture negation')
                if r['role']!='negated_conjecture':raise ValueError('negation role')
                negations.add(n);ch=dict(status='checked_negation',seconds=0)
            else:
                if any(p in conjectures for p in ps):raise ValueError('conjecture used as premise')
                ch=entails([closed(known[p]['formula']) for p in ps],closed(f))
                if ch['status']!='checked':raise ValueError('unverified entailment '+n+' '+str(rule))
            checks.append(dict(name=n,rule=rule,parents=ps,**ch))
        known[n]=r
    if not rs or rs[-1]['formula']!=('bot',) or not negations:raise ValueError('no checked contradiction from negated goal')
    return dict(status='checked_complete_derivation',steps=len(rs),checked_inputs=len(used_inputs),used_lemma_inputs=[n for n in used_inputs if expected[n][0]['role']=='lemma'],checks=checks,seconds=time.perf_counter()-began,
                scope='Every listed source and inference, including preprocessing, independently checked. Local validity uses certified finite Herbrand/EUF refutations; no E rule name or SZS status establishes acceptance. Unsupported introduced symbols fail closed.')
