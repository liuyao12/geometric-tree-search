"""Direct finite semantic proof tiles on the existing exact point graph.

Every rule occupies one proof cell. Exact scalar markings at output/premise
points bind formula syntax IDs, including distant backward references. All
slot/reference instances are enumerated; no proof proposer supplies a path.
Primitive rules and compiled derived rules decode to the frozen FOL checker.
This is a positional finite tile family with identity transforms, not a
translation-invariant four-edge Wang inventory or a complete PA tactic.
"""
import collections,copy,itertools,time
import logic as L
from turtle import State,Graph,Placement,CAPACITY
from serialized_kernel import canonical,check,problem_hash,PROTOCOL

def cell(slot):return (2*slot,0)
def output(slot):return (2*slot,1)
def frozen(x):return tuple(frozen(a) for a in x) if isinstance(x,(list,tuple)) else x
def body_target(target):
    names=[];a=frozen(target)
    while a[0]=='all':names.append(a[1]);a=a[2]
    return names,a

class Model:
    def __init__(self,catalog,length):
        if type(length) is not int or length<1:raise ValueError('positive proof-cell bound required')
        self.catalog=catalog;self.length=length;self.cache={};self.dependencies=collections.defaultdict(set);self.metrics=collections.Counter();self.align_cache={};self.relations=[]
        for slot in range(length):
            keys=[]
            for r,rule in enumerate(catalog['rules']):
                for refs in itertools.product(range(slot),repeat=len(rule['inputs'])):
                    marks={output(slot):rule['output']};valid=True
                    for i,v in zip(refs,rule['inputs']):
                        p=output(i)
                        if p in marks and marks[p]!=v:valid=False;break
                        marks[p]=v
                    # Repeated references with incompatible formula values
                    # cannot define a function m and are not legal tile types.
                    if not valid:continue
                    key=(slot,r,refs);c=Placement(key,((cell(slot),CAPACITY),),tuple(sorted(marks.items())),())
                    self.cache[key]=c;keys.append(key)
                    for p,_ in c.occupancy+c.marks:self.dependencies[p].add(key)
            self.align_cache[cell(slot)]=tuple(keys)
    def placement(self,key):return self.cache[key]
    def alignments(self,p):return self.align_cache.get(p,())
    def initial(self):
        roots={cell(i):0 for i in range(self.length)}
        return State(roots=roots,generations=dict(roots),marks={output(self.length-1):self.catalog['target_id']},allowed_points=frozenset(roots))

def point_check(model,order,complete=False):
    totals={};marks={output(model.length-1):model.catalog['target_id']};seen=set()
    for key in order:
        if key in seen or key not in model.cache:return False
        seen.add(key);c=model.cache[key]
        for p,v in c.occupancy:
            totals[p]=totals.get(p,0)+v
            if totals[p]>CAPACITY:return False
        for p,v in c.marks:
            if p in marks and marks[p]!=v:return False
            marks[p]=v
    return not complete or all(totals.get(cell(i),0)==CAPACITY for i in range(model.length))

def decode(catalog,keys,length):
    """Logical slot order is separate from the actual geometric placement order."""
    by_slot={k[0]:k for k in keys}
    if set(by_slot)!=set(range(length)) or len(by_slot)!=len(keys):raise ValueError('one proof tile per slot required')
    lines=[];finals=[];definitions={};commands=[]
    def emit(rule,a,**parameters):lines.append(dict(rule=rule,formula=a,**parameters));return len(lines)-1
    for slot in range(length):
        _,r,refs=by_slot[slot];item=catalog['rules'][r];a=catalog['formulas'][item['output']]
        if len(refs)!=len(item['inputs']) or any(type(i) is not int or not 0<=i<slot for i in refs):raise ValueError('invalid earlier reference')
        if any(catalog['rules'][by_slot[i][1]]['output']!=v for i,v in zip(refs,item['inputs'])):raise ValueError('formula port mismatch')
        mapped=[finals[i] for i in refs];recipe=item['recipe'];kind=recipe['kind']
        if kind=='primitive':
            w=copy.deepcopy(recipe['witness']);rule=w.pop('rule');formula=w.pop('formula')
            if frozen(formula)!=frozen(a):raise ValueError('changed primitive output')
            if rule=='mp':w.update(antecedent=mapped[0],implication=mapped[1])
            if rule=='generalize':w['source']=mapped[0]
            j=emit(rule,a,**w)
        elif kind=='copy':
            s=emit('tautology',L.Imp(frozen(a),frozen(a)));j=emit('mp',a,antecedent=mapped[0],implication=s)
        elif kind=='block':
            b=recipe['definition'];definitions[b['name']]=b;j=emit('block',a,name=b['name'],inputs=mapped)
        else:raise ValueError('unknown rule recipe')
        finals.append(j);commands.append(dict(slot=slot,rule=r,refs=refs,final_line=j))
    if catalog['rules'][by_slot[length-1][1]]['output']!=catalog['target_id']:raise ValueError('changed final theorem')
    for x in reversed(catalog.get('close_variables',[])):
        finals[-1]=emit('generalize',L.All(x,frozen(lines[finals[-1]]['formula'])),variable=x,source=finals[-1])
    request=dict(protocol=PROTOCOL,theory=catalog['theory'],target=catalog['target'],blocks=[definitions[n] for n in sorted(definitions)],proof=lines)
    checked=check(canonical(request),expected_problem_sha256=problem_hash(request))
    if checked['status']!='accepted':raise ValueError(('decoded semantic proof rejected',checked))
    return dict(request=request,check=checked,commands=commands)

class Limit(Exception):pass
def search(catalog,length,node_limit=50000,seconds=5,diagnostics=12):
    began=time.perf_counter();model=Model(catalog,length);build_seconds=time.perf_counter()-began;state=model.initial();graph=Graph(model,state)
    graph_seconds=time.perf_counter()-began-build_seconds;nodes=branches=forced=backtracks=attempts=0;peak_nodes=len(graph.edges);peak_incidences=sum(map(len,graph.domains.values()));found=None;best=state.copy();samples=[]
    def visit(s,g):
        nonlocal nodes,branches,forced,backtracks,attempts,found,best,peak_nodes,peak_incidences
        nodes+=1
        if nodes>node_limit or time.perf_counter()-began>seconds:raise Limit()
        kind,p,keys=g.decision(s);peak_nodes=max(peak_nodes,len(g.edges));peak_incidences=max(peak_incidences,sum(map(len,g.domains.values())))
        if len(samples)<diagnostics:samples.append(dict(order=list(s.order),kind=kind,point=p,degrees={str(q):len(v) for q,v in g.domains.items()}))
        if kind=='dead':return False,dict(kind=kind,point=p)
        if len(s.order)>len(best.order):best=s.copy()
        if kind=='empty':
            if not point_check(model,s.order,True):raise ValueError('incomplete target reached empty graph')
            found=s;return True,dict(kind=kind)
        if kind=='forced':forced+=1
        else:branches+=1
        tree=dict(kind=kind,point=p,children=[])
        for key in keys:
            attempts+=1;child=s.copy();child_graph=g.copy();child_graph.update(model,child,child.place(model.placement(key)))
            ok,subtree=visit(child,child_graph);tree['children'].append(dict(key=key,tree=subtree))
            if ok:return True,tree
            backtracks+=1
        return False,tree
    tree=None
    try:
        ok,tree=visit(state,graph);status='finite_exact_proof_tiling' if ok else 'exhausted_finite_proof_envelope'
    except Limit:status='unknown_search_budget'
    selected=found or best
    if not point_check(model,selected.order,found is not None):raise ValueError('invalid saved point state')
    result=dict(status=status,placements=selected.order,tile_generations=selected.tile_generations,nodes=nodes,branches=branches,forced=forced,backtracks=backtracks,attempts=attempts,
        build_seconds=build_seconds,graph_seconds=graph_seconds,seconds=time.perf_counter()-began,candidate_universe=len(model.cache),peak_candidate_nodes=peak_nodes,peak_incidences=peak_incidences,
        metrics=dict(model.metrics),samples=samples,limits=dict(nodes=node_limit,seconds=seconds),search_tree=tree,
        scope='direct complete finite point search; distant formula markings define the proof problem, not a learned redundant pruning rule; geometric selection order can differ from logical slot order')
    if found is not None:
        before=time.perf_counter();result['decoded']=decode(catalog,selected.order,length);result['decode_seconds']=time.perf_counter()-before
    return result

def symbolic_search(catalog,length,node_limit=50000,seconds=5):
    """Specialized chronological DFS over exactly the same finite proof grammar.

    This control uses symbolic known-prefix tests, not the reference geometric
    scheduler. It enumerates the same full valid logical certificates. It is
    not an unmarked run of the same point-candidate graph.
    """
    began=time.perf_counter();nodes=branches=attempts=backtracks=0;found=None
    def visit(keys,values):
        nonlocal nodes,branches,attempts,backtracks,found
        nodes+=1
        if nodes>node_limit or time.perf_counter()-began>seconds:raise Limit()
        j=len(keys)
        if j==length:found=list(keys);return True
        choices=[]
        for r,rule in enumerate(catalog['rules']):
            if j==length-1 and rule['output']!=catalog['target_id']:continue
            domains=[[i for i,v in enumerate(values) if v==p] for p in rule['inputs']]
            for refs in itertools.product(*domains):choices.append((j,r,refs))
        if len(choices)>1:branches+=1
        for key in choices:
            attempts+=1
            if visit(keys+[key],values+[catalog['rules'][key[1]]['output']]):return True
            backtracks+=1
        return False
    try:ok=visit([],[]);status='symbolic_proof_found' if ok else 'exhausted_finite_proof_envelope'
    except Limit:status='unknown_search_budget'
    result=dict(status=status,nodes=nodes,branches=branches,attempts=attempts,backtracks=backtracks,seconds=time.perf_counter()-began,placements=found,limits=dict(nodes=node_limit,seconds=seconds),scope='specialized chronological symbolic control; same proof grammar and finite length, different scheduler and representation')
    if found is not None:
        before=time.perf_counter();result['decoded']=decode(catalog,found,length);result['decode_seconds']=time.perf_counter()-before
    return result
