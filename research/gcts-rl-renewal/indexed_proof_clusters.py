"""Complete indexed joins of learned proof families and translated contacts.

This changes enumeration cost, not the inventory, ranking or logical rules.
Every original base tile and every compatible translated learned instance
is retained. Both search lanes use the same cluster inventory. No policy or
formula, witness, reachability or resource filter narrows the join.
"""
import collections,time
import induction_clusters as H
import induction_proof_tiles as T
import semantic_proof_tiles as S
import coarse_proof_tiles as M
from proof_clusters import digest
from turtle import Graph,Placement

def instances(c,n,library):
    buckets=collections.defaultdict(list)
    for rid,r in enumerate(c['rules']):buckets[digest(H.family(r))].append(rid)
    result={}
    for pattern in library:
        for start in range(n-pattern['span']+1):
            partial=[((),{})];columns=set()
            for node in pattern['nodes']:
                slot=start+node['offset'];refs=tuple(start+j for j in node['refs'])
                if not 0<=slot<n or any(j<0 or j>=slot for j in refs):partial=[];break
                relation=[]
                for rid in buckets[digest(node['family'])]:
                    r=c['rules'][rid]
                    if len(refs)!=len(r['inputs']):continue
                    ports={slot:r['output']};valid=True
                    for j,f in zip(refs,r['inputs']):
                        if j in ports and ports[j]!=f:valid=False;break
                        ports[j]=f
                    if valid:relation.append(((slot,rid,refs),ports))
                if not relation:partial=[];break
                new_columns=set(relation[0][1]);shared=tuple(sorted(columns&new_columns));index=collections.defaultdict(list)
                for key,ports in relation:
                    if set(ports)!=new_columns:raise ValueError('fixed contact columns')
                    index[tuple(ports[p] for p in shared)].append((key,ports))
                following=[]
                for members,ports in partial:
                    for key,more in index[tuple(ports[p] for p in shared)]:following.append((members+(key,),ports|more))
                partial=following;columns.update(new_columns)
                if not partial:break
            for members,_ in partial:
                if members not in result:result[members]=dict(members=members,patterns=[],start=start)
                result[members]['patterns'].append(pattern['name'])
    return [result[k] for k in sorted(result)]

class Model(T.Model):
    def __init__(self,c,n,library=(),marked=True):
        certificate=T.supports(c) if marked else None
        super().__init__(c,n,support_certificate=certificate)
        began=time.perf_counter();self.library=library;self.instances=instances(c,n,library);self.instantiation_seconds=time.perf_counter()-began
        self.align_cache={p:list(ids) for p,ids in self.align_cache.items()};lookup={d['members'][0]:cid for cid,d in self.descriptions.items()}
        for item in self.instances:
            cid=len(self.cache);weights=collections.Counter();marks={}
            for key in item['members']:
                part=self.cache[lookup[key]]
                for p,v in part.occupancy:weights[p]+=v
                for p,v in part.marks:
                    if p[1]==2:continue
                    if p in marks and marks[p]!=v:raise ValueError('incompatible cluster point values')
                    marks[p]=v
                marks[(2*key[0],2)]=cid
            if any(v>12 for v in weights.values()):raise ValueError('distinct constituent cells')
            t=Placement(cid,tuple(sorted(weights.items())),tuple(sorted(marks.items())),())
            self.cache[cid]=t;self.descriptions[cid]=dict(members=item['members'],item=item)
            for p,_ in t.occupancy:self.align_cache[p].append(cid)
            for p,_ in t.occupancy+t.marks:self.dependencies[p].add(cid)
        self.align_cache={p:tuple(ids) for p,ids in self.align_cache.items()}
    def ordering(self,cid):
        d=self.descriptions[cid];item=d['item'];members=d['members']
        return (0 if item else 1,-int(any(k[0]==self.length-1 for k in members)) if item else 0,-len(members),cid)

def search(c,n,library=(),seconds=15,attempt_limit=50000,marked=True):
    began=time.perf_counter();model=Model(c,n,library,marked);build=time.perf_counter()-began
    state=model.initial();graph=Graph(model,state);graph_seconds=time.perf_counter()-began-build
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,tile_attempts=0,macro_attempts=0);found=None;best=[]
    peaks=[len(graph.domains),len(graph.edges),sum(map(len,graph.domains.values()))]
    def visit(s,g):
        nonlocal found,best
        stats['nodes']+=1;t=dict(kind='cutoff',selected=list(s.order))
        if time.perf_counter()-began>seconds:t['cutoff']='wall_entry';return None,t
        kind,p,choices=g.decision(s);t.update(kind=kind,point=p,graph_sha256=digest(g.fingerprint()))
        peaks[1]=max(peaks[1],len(g.edges));peaks[2]=max(peaks[2],sum(map(len,g.domains.values())))
        if kind=='dead':return False,t
        if len(model.expansion(s.order))>len(model.expansion(best)):best=list(s.order)
        if kind=='empty':found=list(s.order);return True,t
        stats['forced' if kind=='forced' else 'branches']+=1;t['children']=[]
        for cid in sorted(choices,key=model.ordering):
            cost=len(model.descriptions[cid]['members'])
            if stats['base_attempts']+cost>attempt_limit:t['cutoff']='attempts_before_candidate';return None,t
            if time.perf_counter()-began>seconds:t['cutoff']='wall_before_candidate';return None,t
            stats['base_attempts']+=cost;stats['tile_attempts']+=1;stats['macro_attempts']+=int(cost>1)
            child=s.copy();cg=g.copy();cg.update(model,child,child.place(model.placement(cid)))
            ok,sub=visit(child,cg);t['children'].append(dict(candidate=cid,tree=sub))
            if ok is not False:return ok,t
            stats['backtracks']+=1
        return False,t
    ok,tree=visit(state,graph);selected=found if found is not None else best;placements=model.expansion(selected)
    if not S.point_check(model.base,placements,ok is True):raise ValueError('motifs expand to the original exact point model')
    r=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked,
      selected=selected,placements=placements,tile_generations=[1]*len(selected),search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,
      build_seconds=build,graph_seconds=graph_seconds,seconds=time.perf_counter()-began,base_universe=len(model.base.cache),candidate_universe=len(model.cache),motif_instances=len(model.instances),instantiation_seconds=model.instantiation_seconds,
      support_certificate=model.support_certificate,library_sha256=digest(library),peak_frontier_points=peaks[0],peak_candidate_nodes=peaks[1],peak_incidences=peaks[2],metrics=dict(model.metrics),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    if ok:
        start=time.perf_counter();r['decoded']=S.decode(c,placements,n);r['decode_seconds']=time.perf_counter()-start
        r['solution_motifs']=[dict(candidate=cid,**model.descriptions[cid]) for cid in selected if model.descriptions[cid]['item'] is not None]
    return r

def csp_search(c,n,library=(),seconds=15,attempt_limit=50000,marked=True):
    """Same resource constraints and learned motifs offered to classical AC/MRV.

    Complete original variable domains are retained. A motif simultaneously
    assigns its original constituent values; every ordinary value is still tried
    after failed proposals. Motifs do not change classical support semantics.
    """
    began=time.perf_counter();binary=M.Binary(c,n);certificate=T.supports(c) if marked else None
    if certificate is not None:
        bounds=certificate['bound']
        for i,row in enumerate(binary.keys):
            for j,key in enumerate(row):
                slot,rid,refs=key;r=c['rules'][rid]
                contacts=((slot,r['output']),)+tuple(zip(refs,r['inputs']))
                if any(bounds[f] is None or bounds[f]>p+1 for p,f in contacts):binary.initial[i]&=~(1<<j)
    instantiation_start=time.perf_counter();motifs=instances(c,n,library);instantiation_seconds=time.perf_counter()-instantiation_start;index={key:(i,j) for i,row in enumerate(binary.keys) for j,key in enumerate(row)}
    values=[tuple(index[key] for key in item['members']) for item in motifs];by_slot=collections.defaultdict(list)
    for mid,assignment in enumerate(values):
        for i,j in assignment:by_slot[i].append(mid)
    build=time.perf_counter()-began
    stats=collections.Counter(nodes=0,branches=0,forced=0,backtracks=0,base_attempts=0,macro_attempts=0,support_tests=0,removed_values=0,revisions=0);found=None;used=[]
    def order(mid):
        item=motifs[mid];return (-int(any(k[0]==n-1 for k in item['members'])),-len(item['members']),mid)
    def visit(incoming,path):
        nonlocal found,used
        stats['nodes']+=1;ds=list(incoming);tree=dict(kind='ac',incoming=[hex(x) for x in incoming],revisions=[],children=[])
        if not all(ds):tree.update(kind='dead',domains=[hex(x) for x in ds]);return False,tree
        queue=collections.deque((i,j) for i in range(n) for j in range(n) if i!=j)
        while queue:
            if time.perf_counter()-began>seconds:tree.update(cutoff='wall_ac',domains=[hex(x) for x in ds]);return None,tree
            i,j=queue.popleft();removed=0
            for k in M.indices(ds[i]):
                stats['support_tests']+=1
                if not binary.support(i,k,j)&ds[j]:removed|=1<<k
            stats['revisions']+=1;stats['removed_values']+=M.count(removed);tree['revisions'].append((i,j,hex(removed)));ds[i]&=~removed
            if not ds[i]:tree.update(kind='dead',domains=[hex(x) for x in ds]);return False,tree
            if removed:queue.extend((k,i) for k in range(n) if k!=i and k!=j)
        tree['domains']=[hex(x) for x in ds]
        if all(M.count(x)==1 for x in ds):
            found=[binary.keys[i][next(M.indices(mask))] for i,mask in enumerate(ds)];used=list(path);tree['kind']='empty';return True,tree
        i=min((i for i in range(n) if M.count(ds[i])>1),key=lambda i:(M.count(ds[i]),i));tree.update(kind='branch',slot=i);stats['branches']+=1
        offered=sorted((mid for mid in by_slot[i] if all(ds[j]&(1<<k) for j,k in values[mid])),key=order)
        choices=[('motif',mid,values[mid]) for mid in offered]+[('base',k,((i,k),)) for k in M.indices(ds[i])]
        for kind,choice,assignment in choices:
            cost=len(assignment)
            if stats['base_attempts']+cost>attempt_limit:tree['cutoff']='attempts_before_candidate';return None,tree
            if time.perf_counter()-began>seconds:tree['cutoff']='wall_before_candidate';return None,tree
            stats['base_attempts']+=cost;stats['macro_attempts']+=int(kind=='motif');child=list(ds)
            for j,k in assignment:child[j]=1<<k
            okay,sub=visit(child,path+([choice] if kind=='motif' else []));tree['children'].append(dict(mode=kind,choice=choice,tree=sub))
            if okay is not False:return okay,tree
            stats['backtracks']+=1
        return False,tree
    ok,tree=visit(binary.initial,[])
    r=dict(status='finite_exact_proof_tiling' if ok else 'unknown_search_budget' if ok is None else 'exhausted_finite_proof_envelope',marked=marked,support_certificate=certificate,
      placements=found or [],search_tree=tree if ok is not None else None,partial_tree=tree if ok is None else None,build_seconds=build,seconds=time.perf_counter()-began,
      base_universe=len(binary.model.cache),candidate_universe=len(binary.model.cache),motif_instances=len(motifs),instantiation_seconds=instantiation_seconds,library_sha256=digest(library),limits=dict(seconds=seconds,base_attempts=attempt_limit),**stats)
    if ok:
        if not S.point_check(binary.model,found,True):raise ValueError('classical witness expands to exact original points')
        start=time.perf_counter();r['decoded']=S.decode(c,found,n);r['decode_seconds']=time.perf_counter()-start;r['used_motif_proposals']=used
    return r
