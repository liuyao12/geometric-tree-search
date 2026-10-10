"""Solution-equivalent coarse capacity points and complete checked metatile types.

This is a new positional point model, not a primitive-scheduler shortcut.
Ownership m-values forbid overlapping expansions. All primitive types remain.
The independent classical control uses binary arc consistency and MRV instead.
"""
import collections,time
import semantic_proof_tiles as S
import proof_clusters as H
from turtle import State,Graph,Placement,CAPACITY

LANES=('base','fine-meta','coarse2-base','coarse2-meta','coarse3-meta','csp')
def owner(slot):return (2*slot,2)
def group_point(group):return (2*group,0)

class Model:
    def __init__(self,c,length,width=1,library=()):
        if width not in (1,2,3):raise ValueError('width must divide exact twelfths')
        self.length=length;self.width=width;self.catalog=c;self.base=S.Model(c,length)
        self.groups=tuple(tuple(range(j,min(j+width,length))) for j in range(0,length,width))
        self.slot_group={slot:g for g,slots in enumerate(self.groups) for slot in slots}
        self.cache={};self.descriptions={};self.dependencies=collections.defaultdict(set);self.align_cache=collections.defaultdict(list);self.metrics=collections.Counter()
        for key in sorted(self.base.cache):self.add((key,),None)
        index=H.Index(c,length,library,max_instances=1000000)
        if not index.complete:raise ValueError('complete metatile inventory required')
        self.index_instances=len(index.instances);self.index_seconds=index.seconds
        for item in index.instances:self.add(tuple(item['members']),item)
        self.align_cache={p:tuple(keys) for p,keys in self.align_cache.items()}
    def add(self,members,item):
        cid=len(self.cache);slots=[k[0] for k in members]
        if len(set(slots))!=len(slots):raise ValueError('duplicate owned primitive slot')
        marks={};occupancy=collections.Counter()
        for key in members:
            for p,v in self.base.placement(key).marks:
                if p in marks and marks[p]!=v:raise ValueError('incompatible internal metatile marks')
                marks[p]=v
            slot=key[0];g=self.slot_group[slot];occupancy[group_point(g)]+=CAPACITY//len(self.groups[g]);marks[owner(slot)]=cid
        placement=Placement(cid,tuple(sorted(occupancy.items())),tuple(sorted(marks.items())),())
        self.cache[cid]=placement;self.descriptions[cid]=dict(members=members,item=item)
        for p,_ in placement.occupancy:self.align_cache[p].append(cid)
        for p,_ in placement.occupancy+placement.marks:self.dependencies[p].add(cid)
    def placement(self,cid):return self.cache[cid]
    def alignments(self,p):return self.align_cache.get(p,())
    def initial(self):
        roots={group_point(g):0 for g in range(len(self.groups))}
        return State(roots=roots,generations=dict(roots),marks={S.output(self.length-1):self.catalog['target_id']},allowed_points=frozenset(roots))
    def expansion(self,ids):return sorted((key for cid in ids for key in self.descriptions[cid]['members']),key=lambda k:k[0])
    def ordering(self,cid):
        d=self.descriptions[cid];item=d['item'];members=d['members']
        return (0 if item else 1,-int(any(k[0]==self.length-1 for k in members)) if item else 0,-len(members),-item['level'] if item else 0,H.digest(item) if item else '',cid)

def search(c,length,width=1,library=(),seconds=5,attempt_limit=50000):
    began=time.perf_counter();model=Model(c,length,width,library);build=time.perf_counter()-began;s=model.initial();g=Graph(model,s);graph_seconds=time.perf_counter()-began-build
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0);best=[];found=None
    peak_points=len(g.domains);peak_candidates=len(g.edges);peak_incidences=sum(map(len,g.domains.values()))
    def visit(state,graph):
        nonlocal best,found,peak_points,peak_candidates,peak_incidences
        stats['nodes']+=1
        node=dict(kind='cutoff',selected=list(state.order))
        if time.perf_counter()-began>seconds:node['cutoff']='wall_entry';return None,node
        kind,p,keys=graph.decision(state);node.update(kind=kind,point=p,graph_sha256=H.digest(graph.fingerprint()))
        peak_points=max(peak_points,len(graph.domains));peak_candidates=max(peak_candidates,len(graph.edges));peak_incidences=max(peak_incidences,sum(map(len,graph.domains.values())))
        if kind=='dead':return False,node
        if len(model.expansion(state.order))>len(model.expansion(best)):best=list(state.order)
        if kind=='empty':found=list(state.order);return True,node
        stats['forced' if kind=='forced' else 'branches']+=1;node['children']=[]
        for cid in sorted(keys,key=model.ordering):
            cost=len(model.descriptions[cid]['members'])
            if stats['base_attempts']+cost>attempt_limit:node['cutoff']='attempts_before_candidate';return None,node
            if time.perf_counter()-began>seconds:node['cutoff']='wall_before_candidate';return None,node
            stats['base_attempts']+=cost;stats['tile_attempts']+=1;child=state.copy();cg=graph.copy();cg.update(model,child,child.place(model.placement(cid)))
            ok,subtree=visit(child,cg);node['children'].append(dict(candidate=cid,tree=subtree))
            if ok is not False:return ok,node
            stats['backtracks']+=1
        return False,node
    ok,tree=visit(s,g);ids=found if found is not None else best;placements=model.expansion(ids)
    if not S.point_check(model.base,placements,ok is True):raise ValueError('coarse state does not expand exactly')
    result=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',width=width,groups=model.groups,selected=ids,placements=placements,
        tile_generations=[1]*len(ids),search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,build_seconds=build,graph_seconds=graph_seconds,index_seconds=model.index_seconds,index_instances=model.index_instances,
        seconds=time.perf_counter()-began,candidate_universe=len(model.cache),base_universe=len(model.base.cache),peak_frontier_points=peak_points,peak_candidate_nodes=peak_candidates,peak_incidences=peak_incidences,metrics=dict(model.metrics),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    if ok:
        t=time.perf_counter();result['decoded']=S.decode(c,placements,length);result['decode_seconds']=time.perf_counter()-t
        result['solution_transactions']=[model.descriptions[cid]['item'] for cid in ids if model.descriptions[cid]['item'] is not None]
    return result

class Binary:
    """Full original finite domains; absent marks supply universal compatibility."""
    def __init__(self,c,length):
        self.model=S.Model(c,length);self.keys=[sorted(k for k in self.model.cache if k[0]==i) for i in range(length)]
        self.marks=[[dict(self.model.cache[k].marks) for k in keys] for keys in self.keys];self.index=[];self.all=[];self.support_cache={}
        for values in self.marks:
            full=(1<<len(values))-1;present=collections.defaultdict(int);by_value=collections.defaultdict(lambda:collections.defaultdict(int))
            for k,m in enumerate(values):
                for p,v in m.items():present[p]|=1<<k;by_value[p][v]|=1<<k
            self.all.append(full);self.index.append((present,by_value))
        self.initial=list(self.all);p=S.output(length-1);v=c['target_id']
        for i,(present,values) in enumerate(self.index):self.initial[i]&=(self.all[i]^present[p])|values[p][v]
    def support(self,i,k,j):
        key=(i,k,j)
        if key not in self.support_cache:
            full=self.all[j];present,values=self.index[j];mask=full
            for p,v in self.marks[i][k].items():mask&=(full^present[p])|values[p][v]
            self.support_cache[key]=mask
        return self.support_cache[key]

def indices(mask):
    while mask:
        low=mask&-mask;yield low.bit_length()-1;mask^=low
def count(mask):return bin(mask).count('1')
def csp_search(c,length,seconds=5,attempt_limit=50000):
    began=time.perf_counter();binary=Binary(c,length);build=time.perf_counter()-began;stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,support_tests=0,removed_values=0,revisions=0);found=None
    def visit(incoming):
        nonlocal found
        stats['nodes']+=1;domains=list(incoming);tree=dict(kind='ac',incoming=[hex(x) for x in incoming],revisions=[],children=[]);queue=collections.deque((i,j) for i in range(length) for j in range(length) if i!=j)
        if not all(domains):tree.update(kind='dead',domains=[hex(x) for x in domains]);return False,tree
        while queue:
            if time.perf_counter()-began>seconds:tree.update(cutoff='wall_ac',domains=[hex(x) for x in domains]);return None,tree
            i,j=queue.popleft();removed=0
            for k in indices(domains[i]):
                stats['support_tests']+=1
                if not binary.support(i,k,j)&domains[j]:removed|=1<<k
            stats['revisions']+=1;stats['removed_values']+=count(removed);tree['revisions'].append((i,j,hex(removed)));domains[i]&=~removed
            if not domains[i]:tree.update(kind='dead',domains=[hex(x) for x in domains]);return False,tree
            if removed:queue.extend((k,i) for k in range(length) if k!=i and k!=j)
        tree['domains']=[hex(x) for x in domains]
        if all(count(x)==1 for x in domains):
            found=[binary.keys[i][next(indices(mask))] for i,mask in enumerate(domains)];tree['kind']='empty';return True,tree
        i=min((i for i in range(length) if count(domains[i])>1),key=lambda i:(count(domains[i]),i));tree.update(kind='branch',slot=i);stats['branches']+=1
        for k in indices(domains[i]):
            if stats['base_attempts']>=attempt_limit:tree['cutoff']='attempts_before_candidate';return None,tree
            if time.perf_counter()-began>seconds:tree['cutoff']='wall_before_candidate';return None,tree
            stats['base_attempts']+=1;child=list(domains);child[i]=1<<k;ok,sub=visit(child);tree['children'].append(dict(value=k,tree=sub))
            if ok is not False:return ok,tree
            stats['backtracks']+=1
        return False,tree
    ok,tree=visit(binary.initial);result=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,
        placements=found or [],solution_transactions=[],build_seconds=build,seconds=time.perf_counter()-began,candidate_universe=len(binary.model.cache),base_universe=len(binary.model.cache),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    if ok:
        if not S.point_check(binary.model,found,True):raise ValueError('CSP solution does not expand exactly')
        t=time.perf_counter();result['decoded']=S.decode(c,found,length);result['decode_seconds']=time.perf_counter()-t
    return result
