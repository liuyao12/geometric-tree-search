"""Complete bounded certificate grammar -> distant point-value rule receptors.

This is a finite high-level point model, not primitive-square Wang placement.
Every original syntactic command remains present. Separate guard placements
encode the five declared logical rule forms; search sees only t/m values.
Tautology guard instances are compiled by the unchanged native machine.
No host proof evaluator, authored proof or learned pruning runs in search.
"""
import collections,copy,hashlib,json,time
from certificate_boundary_search import canonical,digest,formula_basis,choices
from turtle import CAPACITY,Placement,State,Graph

def word(value):return [*canonical(value),256]
def center(slot,kind):return (4*slot,0 if kind=='command' else 1)
def port(slot,channel,k):return (4*slot+(channel=='command'),100+k)
def assignment(slot,channel,value):return [(port(slot,channel,k),v) for k,v in enumerate(word(value))]
def merge(entries):
    out={}
    for p,v in entries:
        if p in out and out[p]!=v:return None
        out[p]=v
    return tuple(sorted(out.items()))

def compile_guards(spec,oracle,micro_steps=10**9,queries=64):
    """Native acceptance supplies exactly the bounded tautology-rule catalog.

    Unfinished compilation stops before a complete domain can be claimed.
    Other guard families are structural instances of the declared five rules.
    """
    basis,variables=formula_basis(spec);tautologies=[];query_ids=[];began=time.perf_counter()
    for index,f in enumerate(basis):
        if len(query_ids)>=spec.get('compile_queries',queries):
            return dict(status='unknown_compile_budget',basis=basis,variables=variables,tautologies=tautologies,queries=query_ids,seconds=time.perf_counter()-began)
        query_spec=copy.deepcopy(spec);query_spec['target']=f
        record=oracle.query(query_spec,[dict(rule='tautology',formula=f)],True,micro_steps)
        record.update(purpose='tautology_instance',basis_index=index);query_ids.append(record['id'])
        if record['result']['status']=='accepted':tautologies.append(f)
        elif record['result']['status']!='rejected':
            return dict(status='unknown_native_compilation',basis=basis,variables=variables,tautologies=tautologies,queries=query_ids,seconds=time.perf_counter()-began)
    return dict(status='complete',basis=basis,variables=variables,tautologies=tautologies,queries=query_ids,seconds=time.perf_counter()-began)

class Model:
    def __init__(self,spec,compiled):
        if compiled['status']!='complete':raise ValueError('incomplete guard catalog cannot prune')
        self.spec=spec;self.compiled=compiled;self.metrics=collections.Counter();self.dependencies=collections.defaultdict(set);self.cache={};self.align_cache={};self.metadata={};self.conflicts=[]
        self.domains=[choices(spec,j,compiled['basis'],compiled['variables']) for j in range(spec['length'])]
        taut={canonical(f) for f in compiled['tautologies']};began=time.perf_counter()
        for j,commands in enumerate(self.domains):
            self.align_cache[center(j,'command')]=[];self.align_cache[center(j,'guard')]=[]
            for k,c in enumerate(commands):
                entries=assignment(j,'command',c)+assignment(j,'formula',c['formula'])
                self.add((j,0,k,0),entries,c,[])
                f=c['formula'];rule=c['rule'];requirements=[]
                if rule=='axiom':valid=spec['theory']['axioms'][c['name']]==f
                elif rule=='refl':valid=f[0]=='eq' and f[1]==f[2]
                elif rule=='tautology':valid=canonical(f) in taut
                elif rule=='generalize':
                    valid=f[0]=='all' and f[1]==c['variable']
                    if valid:requirements=[(c['source'],f[2])]
                else:
                    valid=False
                    # All implication subformulas with this consequent remain.
                    for variant,implication in enumerate(compiled['basis']):
                        if implication[0]=='imp' and implication[2]==f:
                            wanted=[(c['antecedent'],implication[1]),(c['implication'],implication)]
                            all_entries=entries+[e for i,a in wanted for e in assignment(i,'formula',a)]
                            self.add((j,1,k,variant),all_entries,c,wanted)
                    continue
                if valid:self.add((j,1,k,0),entries+[e for i,a in requirements for e in assignment(i,'formula',a)],c,requirements)
        self.compile_seconds=time.perf_counter()-began
        for p in self.align_cache:self.align_cache[p]=tuple(self.align_cache[p])
    def add(self,key,entries,command,requirements):
        marks=merge(entries)
        if marks is None:self.conflicts.append(dict(key=key,command=command,requirements=requirements,reason='internally unequal marking values'));return
        j,kind,_,_=key;p=center(j,'command' if kind==0 else 'guard')
        c=Placement(key,((p,CAPACITY),),marks,())
        if key in self.cache:raise ValueError('duplicate native receptor placement')
        self.cache[key]=c;self.metadata[key]=dict(slot=j,kind='command' if kind==0 else 'guard',command=command,requirements=requirements)
        self.align_cache[p].append(key)
        for q,_ in c.occupancy+c.marks:self.dependencies[q].add(key)
    def alignments(self,p):return self.align_cache[p]
    def placement(self,key):return self.cache[key]
    def initial(self):
        roots={center(j,k):0 for j in range(self.spec['length']) for k in ('command','guard')}
        return State(marks=dict(assignment(self.spec['length']-1,'formula',self.spec['target'])),generations=roots.copy(),roots=roots.copy(),allowed_points=frozenset(roots))
    def record(self):
        return dict(domains=self.domains,command_counts=list(map(len,self.domains)),complete_words=__import__('math').prod(map(len,self.domains)),placements=[dict(key=k,occupancy=c.occupancy,marks=c.marks,**self.metadata[k]) for k,c in sorted(self.cache.items())],conflicts=self.conflicts,roots=sorted(self.align_cache),encoding='Canonical UTF-8 JSON bytes followed by the distinct integer terminator 256, one exact value per point; no hashes are compared.',transformations='Fixed orientation; each positional type has its one declared translated placement. This finite high-level inventory is not the universal primitive Wang palette.',marking_class='problem-defining logical rule encoding',compile_seconds=self.compile_seconds)

def fingerprint(state):
    return digest(dict(totals=sorted(state.totals.items()),marks=sorted(state.marks.items()),generations=sorted(state.generations.items()),roots=sorted(state.roots.items()),selected=sorted(state.selected),order=state.order,tile_generations=state.tile_generations,allowed_points=sorted(state.allowed_points)))

def search(model,attempts=2000,seconds=120):
    began=time.perf_counter();initial=model.initial();graph=Graph(model,initial);root_state=fingerprint(initial);root_graph=graph.fingerprint();metrics=collections.Counter();found=None
    def visit(state,g):
        nonlocal found
        kind,p,keys=g.decision(state);metrics['nodes']+=1
        tree=dict(kind=kind,point=p,census=[dict(point=q,generation=state.generations[q],keys=sorted(cs)) for q,cs in sorted(g.domains.items())],state_sha256=fingerprint(state),children=[])
        if kind=='dead':metrics['dead']+=1;return False,tree
        if kind=='empty':found=state;return True,tree
        metrics[kind]+=1
        for k in keys:
            if metrics['attempts']>=attempts or time.perf_counter()-began>=seconds:tree['cutoff']='before_placement';return None,tree
            metrics['attempts']+=1;child=state.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(k)))
            ok,sub=visit(child,cg);tree['children'].append(dict(key=k,tree=sub))
            if ok is not False:return ok,tree
            metrics['backtracks']+=1
        return False,tree
    okay,tree=visit(initial,graph);proof=None
    if found:
        command_keys=sorted(k for k in found.order if k[1]==0)
        if len(command_keys)!=model.spec['length']:raise ValueError('all command obligations')
        proof=[model.metadata[k]['command'] for k in command_keys]
    restored=fingerprint(initial)==root_state and graph.fingerprint()==root_graph
    if not restored:raise ValueError('exact root rollback')
    return dict(status='finite_marked_proof_region' if okay else 'unknown_search_budget' if okay is None else 'exhausted_finite_marked_region',proof=proof,placements=found.order if found else [],tile_generations=found.tile_generations if found else [],tree=tree,metrics=dict(metrics),graph_metrics=dict(model.metrics),seconds=time.perf_counter()-began,root_state_sha256=root_state,root_restored=restored,limits=dict(attempts=attempts,seconds=seconds),scope='Reference complete frontier-point/candidate scheduler on a high-level proof-rule model, not square-by-square search of the native Wang execution. No RL or learned failure marking.')
