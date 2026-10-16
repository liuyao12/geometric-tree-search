"""Bounded goal/context grammar for symbolic Hilbert witness proofs.

Uniform backward syntax productions enumerate a finite rule hypergraph. They
are authored logical constructs, not a supplied derivation. Every production
in the declared envelope is retained, including cycles. Search chooses the
inferences, cell positions and earlier references. No interpretation is read.
"""
import collections, hashlib, itertools, time
import logic as L
import hilbert_incidence_tiles as B
import quantified_proof_rules as Q
import semantic_proof_catalogs as C
from proof_block_search import Proof
from serialized_kernel import canonical
from euclidean_proof_tiles import consume

def existential(a):
    if a[0]=='not' and a[1][0]=='all' and a[1][2][0]=='not':
        return a[1][1], a[1][2][1]
    return None

def problem(name):
    P=lambda x:B.pred('Point',x);R=lambda x:B.pred('Line',x);I=lambda x,y:B.pred('Inc',x,y)
    if name=='line-has-point':
        h=R('u');q=Q.exists('p0',Q.both(P('p0'),I('p0','u')));vs=['u']
        sorts=dict(point=['p0','p1'],line=['u','l0','l1'])
        source='Consequence of planar Hilbert I.3'
    elif name=='unique-joining-line':
        h=B.conjunction([P('a'),P('b'),L.Not(L.Eq(L.V('a'),L.V('b')))])
        d=lambda x:B.conjunction([R(x),I('a',x),I('b',x)])
        q=Q.exists('l0',Q.both(d('l0'),L.All('l1',L.Imp(d('l1'),L.Eq(L.V('l1'),L.V('l0'))))))
        vs=['a','b'];sorts=dict(point=['a','b','p0','p1'],line=['l0','l1'])
        source='Existence and uniqueness of the line through two distinct points, planar Hilbert I.1-I.2'
    else:raise ValueError(name)
    return dict(name=name,hypothesis=h,goal=q,target=B.close(vs,L.Imp(h,q)),variables=vs,sorts=sorts,source=source)

def instances(theory,metadata,sorts):
    domains=dict(sorts,object=sorts['point']+sorts['line']);clauses=[];sources=[]
    for name,a in theory['axioms'].items():
        binders=metadata[name]['binders'];names=list(binders)
        for values in itertools.product(*(domains[binders[x]] for x in names)):
            bindings=dict(zip(names,values));body=a
            # Capture avoidance can rename later binders. Always consume the
            # CURRENT outer binder, never substitute its old metadata label.
            for value in values:
                body=L.substitute(body[2],body[1],L.V(value))
            base=dict(axiom=name,bindings=bindings,instance=body)
            for ci,head,ps,q in B.orientations(body):
                clauses.append(dict(base,kind='axiom-clause',clause=ci,head=head,premises=ps,conclusion=q))
            if body[0]=='imp' and existential(body[2]):sources.append((body[1],body[2]))
    return clauses,sorted(set(sources),key=repr)

def source_block(theory,row,context):
    out=Proof();inputs=[L.Imp(context,p) for p in row['premises']]
    refs=[out.emit('assumption',p,index=i) for i,p in enumerate(inputs)]
    a=theory['axioms'][row['axiom']];j=out.emit('axiom',a,name=row['axiom'])
    for value in row['bindings'].values():
        b=L.substitute(a[2],a[1],L.V(value));k=out.emit('instantiate',L.Imp(a,b),universal=a,term=L.V(value));j=out.mp(j,k);a=b
    if a!=row['instance']:raise ValueError('hygienic source mismatch')
    edge=row['conclusion']
    for p in reversed(row['premises']):edge=L.Imp(p,edge)
    k=out.emit('tautology',L.Imp(a,edge));j=out.mp(j,k)
    k=out.emit('tautology',L.Imp(edge,L.Imp(context,edge)));j=out.mp(j,k)
    for ref in refs:j=consume(out,context,j,ref)
    q=L.Imp(context,row['conclusion'])
    if out.lines[j]['formula']!=q:raise ValueError('source block output')
    return Q.block(inputs,q,out.lines)

def nodes(a):
    if a[0] in ('pred','eq','bot'):return 1
    if a[0]=='all':return 1+nodes(a[2])
    return 1+sum(nodes(x) for x in a[1:])

def grammar(p,theory,metadata,context_depth=2,formula_nodes=160,context_transport=False):
    clauses,sources=instances(theory,metadata,p['sorts']);by_head=collections.defaultdict(list)
    for row in clauses:by_head[row['conclusion']].append(row)
    target=L.Imp(p['hypothesis'],p['goal']);needed={target};queue=collections.deque([target]);contexts={p['hypothesis']:0};rows=[];tauts={}
    def taut(a):
        if a not in tauts:tauts[a]=L.tautology(a)
        return tauts[a]
    def extend(g,a):
        depth=contexts[g]+1
        if depth>context_depth:return None
        new=Q.both(g,a);contexts[new]=min(depth,contexts.get(new,depth));return new
    def add(inputs,q,operation,**parameters):
        if any(nodes(a)>formula_nodes for a in inputs+[q]):return
        rows.append(dict(inputs=inputs,output=q,operation=operation,parameters=parameters))
        for a in inputs:
            if a not in needed:needed.add(a);queue.append(a)
    while queue:
        f=queue.popleft()
        if taut(f):
            add([],f,'tautology');continue
        if f[0]=='all':
            add([f[2]],f,'generalize',variable=f[1]);continue
        if f[0]!='imp' or f[1] not in contexts:raise ValueError('outside contextual grammar')
        g,q=f[1:]
        if context_transport and contexts[g]>0:
            parent,assumption=g[1:]
            add([L.Imp(parent,L.Imp(assumption,q))],f,'propositional')
        for row in by_head[q]:
            add([L.Imp(g,a) for a in row['premises']],f,'axiom-clause',row=row,context=g)
        if q[0]=='and':add([L.Imp(g,q[1]),L.Imp(g,q[2])],f,'propositional')
        if q[0]=='imp':
            expanded=extend(g,q[1])
            if expanded is not None:add([L.Imp(expanded,q[2])],f,'propositional')
            e=existential(q[1])
            if e and e[0] not in L.free(g)|L.free(q[2]):
                x,body=e;expanded=extend(g,body)
                if expanded is not None:add([L.All(x,L.Imp(expanded,q[2]))],f,'exists-eliminate',context=g,variable=x,body=body,conclusion=q[2])
        if q[0]=='all' and q[1] not in L.free(g):
            x,body=q[1:]
            if body[0]=='imp':
                expanded=extend(g,body[1])
                if expanded is not None:add([L.All(x,L.Imp(expanded,body[2]))],f,'forall-scope',context=g,variable=x,body=body[1],conclusion=body[2])
            add([L.All(x,L.Imp(g,body))],f,'forall-distribute',context=g,variable=x,body=body)
        e=existential(q)
        if e:
            x,body=e
            # A declared, theorem-independent existential introduction
            # fragment: use the formula's own binder as a free parameter.
            add([L.Imp(g,body)],f,'exists-introduce',context=g,variable=x,body=body,term=L.V(x))
        # Accessible existential sources are syntactic axiom instances whose
        # guard follows propositionally from this context. They are not a
        # model or a list of previously discovered witnesses.
        if contexts[g]<context_depth and q[0]!='imp':
            local=[]
            def conjuncts(a):
                if existential(a):local.append((a,a))
                if a[0]=='and':conjuncts(a[1]);conjuncts(a[2])
            conjuncts(g)
            for guard,e in sorted(set(sources+local),key=repr):
                if e==q or not taut(L.Imp(g,guard)):continue
                x,body=existential(e)
                if x in L.free(g)|L.free(q):continue
                add([L.Imp(g,e),L.Imp(g,L.Imp(e,q))],f,'propositional')
    # Productions are deterministic but a formula can be requested more than
    # once. Exact duplicate rule instances are one type in this inventory.
    unique={canonical(r):r for r in rows};rows=[unique[k] for k in sorted(unique)]
    return rows,needed,contexts,len(clauses),len(sources)

def catalog(p,omit=(),context_depth=2,formula_nodes=160,context_transport=False):
    began=time.perf_counter();theory,metadata=B.foundation(omit)
    rows,fs,contexts,clause_count,source_count=grammar(p,theory,metadata,context_depth,formula_nodes,context_transport);rules=[]
    for r in rows:
        op=r['operation'];ps=r['inputs'];q=r['output'];params=r['parameters']
        if op in ('tautology','generalize'):
            witness=dict(rule=op,formula=q,**params)
            recipe=dict(kind='primitive',witness=witness)
        else:
            if op=='axiom-clause':b=source_block(theory,params['row'],params['context'])
            elif op=='propositional':b=Q.propositional(ps,q)
            elif op=='exists-introduce':b=Q.exists_intro(params['context'],params['variable'],params['body'],params['term'])
            elif op=='exists-eliminate':b=Q.exists_eliminate(params['context'],params['variable'],params['body'],params['conclusion'])
            elif op=='forall-scope':b=Q.forall_scope(params['context'],params['variable'],params['body'],params['conclusion'])
            elif op=='forall-distribute':b=Q.forall_distribute(params['context'],params['variable'],params['body'])
            else:raise ValueError(op)
            if b['premises']!=ps or b['conclusion']!=q:raise ValueError('compiled interface mismatch')
            recipe=dict(kind='block',operation=op,inference=params,definition=b)
        rules.append((ps,q,recipe))
    conf=dict(kind='bounded-contextual-quantified-Hilbert',metadata=metadata,sorts=p['sorts'],hypothesis=p['hypothesis'],goal=p['goal'],omit=list(omit),context_depth=context_depth,formula_nodes=formula_nodes,context_transport=context_transport,clauses=clause_count,existential_sources=source_count,contexts=[dict(formula=g,depth=d) for g,d in sorted(contexts.items(),key=lambda x:repr(x[0]))],productions=len(rows),source=B.SOURCE,
        scope='Complete recursive backward syntax envelope within declared context and formula bounds: tautology leaves; all sorted source clause orientations with hygienic outer instantiation; conjunction, implication context, universal scope/distribution and root generalization; binder-parameter existential introduction; guarded accessible-source existential elimination. Cycles retained. No general equality-substitution production or fairness/completeness claim.',orientation='identity only; fixed proof direction; translation only; no rotation/reflection')
    c=C.catalog(theory,p['target'],fs,rules,p['variables'],conf);c['build_seconds']=time.perf_counter()-began
    return c
