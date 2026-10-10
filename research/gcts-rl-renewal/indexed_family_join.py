"""Exact syntax indexes for the unchanged finite family join.

Indexes belong to one immutable model/library snapshot. They affect proposal
construction only, never the base graph, degree counts or allowed fallback.
Cold construction and caches are charged to each independent solve.
"""
import collections,itertools,time
import adaptive_receptor_clusters as C
import movable_proof_regions as M
import quantified_receptors as Q

def parameters(a):
    if a[0]=='meta':return {str(a[1])}
    return set().union(*(parameters(v) for v in a[1:])) if len(a)>1 else set()

class Join:
    def __init__(self,model,library):
        began=time.perf_counter();self.model=model;self.library=tuple(sorted(library,key=lambda t:(-len(t['pattern']),t['name'])))
        self.context=model.context_hash();self.library_pin=C.digest([(t['name'],t['pattern'],t['level']) for t in self.library])
        self.nodes={};self.node_ids={};self.query_cache={};self.aggregate_cache={};self.digests={};self.trace=[];self.metrics=collections.Counter()
        for t in self.library:
            ids=[]
            for node in t['pattern']:
                identity=C.digest({k:node[k] for k in ('kind','inputs','output')});ids.append(identity)
                if identity in self.nodes:continue
                variables=set().union(*(parameters(a) for a in tuple(node['inputs'])+(node['output'],)))
                self.nodes[identity]=dict(node=node,variables=tuple(sorted(variables)),compiled=False)
            self.node_ids[t['name']]=tuple(ids)
        self.build_seconds=time.perf_counter()-began

    def query(self,identity,env):
        node=self.nodes[identity]
        if not node['compiled']:
            began=time.perf_counter();p=node['node'];rows=[];inverse=collections.defaultdict(set)
            for rid,r in enumerate(self.model.catalog['rules']):
                if r['kind']!=p['kind']:continue
                self.metrics['syntax_rule_tests']+=1;local={}
                if all(C.match(a,b,local) for a,b in zip(p['inputs'],r['inputs'])) and C.match(p['output'],r['output'],local):
                    index=len(rows);rows.append((rid,local))
                    for k,v in local.items():inverse[k,v].add(index)
            node.update(compiled=True,rows=tuple(rows),inverse=dict(inverse));self.metrics['ground_matches']+=len(rows)
            self.build_seconds+=time.perf_counter()-began
        bound=tuple((k,env[k]) for k in node['variables'] if k in env);key=(identity,bound)
        self.trace.append(dict(node=identity,bound=bound));self.metrics['queries']+=1
        if key in self.query_cache:self.metrics['query_cache_hits']+=1;return self.query_cache[key]
        indices=None
        for k,v in bound:
            found=node['inverse'].get((k,v),set());indices=found if indices is None else indices&found
        result=tuple(node['rows'][i] for i in range(len(node['rows'])) if indices is None or i in indices)
        self.query_cache[key]=result;self.metrics['query_cache_misses']+=1;return result

    def __call__(self,model,state,graph,point,library,limit=32):
        if model is not self.model:raise ValueError('one model per index')
        available={i:a for i,a in graph.ports.items() if i<0 or Q.cell(i) in state.totals}
        by_formula=collections.defaultdict(list)
        for i,a in sorted(available.items()):by_formula[a].append(i)
        slots=[j for j in range(model.bound) if Q.cell(j) in graph.domains];pool={};scanned=0
        for t in self.library:
            for embedding in itertools.combinations(slots,len(t['pattern'])):
                if point[0]//2 not in embedding:continue
                partial=[((),{},{})]
                for i,node in enumerate(t['pattern']):
                    following=[];j=embedding[i]
                    for members,env,outside in partial:
                        matches=self.query(self.node_ids[t['name']][i],env);scanned+=len(matches)
                        for rid,local in matches:
                            binding=dict(env,**local);r=model.catalog['rules'][rid];choices=[]
                            for (kind,ref),a in zip(node['refs'],r['inputs']):
                                if kind=='inside':
                                    if ref>=i:raise ValueError('acyclic fragment')
                                    choices.append((embedding[ref],))
                                elif str(ref) in outside:
                                    v=outside[str(ref)];choices.append((v,) if available.get(v)==a and v<j else ())
                                else:choices.append(tuple(v for v in by_formula.get(a,()) if v<j))
                            for refs in itertools.product(*choices):
                                key=(j,rid,refs)
                                if key not in graph.domains[Q.cell(j)]:continue
                                ext=dict(outside);okay=True
                                for (kind,ref),v in zip(node['refs'],refs):
                                    if kind=='outside':
                                        if str(ref) in ext and ext[str(ref)]!=v:okay=False;break
                                        ext[str(ref)]=v
                                if okay:following.append((members+(key,),binding,ext))
                    partial=following
                    if not partial:break
                for members,env,outside in partial:
                    if members in pool:self.metrics['duplicate_expansions']+=1;continue
                    if members in self.aggregate_cache:self.metrics['aggregate_cache_hits']+=1;union=self.aggregate_cache[members]
                    else:
                        self.metrics['aggregate_cache_misses']+=1
                        try:union=C.aggregate(model,members)
                        except ValueError:union=None
                        self.aggregate_cache[members]=union
                    if union is None or any(p in state.marks and state.marks[p]!=v for p,v in union['marks']):continue
                    pool[members]=dict(template=t['name'],members=members,bindings=env,outside=outside,level=t['level'],**union)
        def ordering(item):
            key=(item['template'],item['members'])
            if key in self.digests:self.metrics['item_digest_hits']+=1
            else:self.digests[key]=C.digest(item);self.metrics['item_digest_misses']+=1
            return (-int(model.catalog['rules'][item['members'][-1][1]]['output']==model.target),-len(item['members']),self.digests[key])
        result=sorted(pool.values(),key=ordering)
        return result[:limit],dict(compatible=len(result),scanned=scanned,truncated=max(0,len(result)-limit))

    def finish(self):
        if self.model.context_hash()!=self.context or C.digest([(t['name'],t['pattern'],t['level']) for t in self.library])!=self.library_pin:
            raise ValueError('index snapshot changed')
        return dict(context=self.context,library_pin=self.library_pin,build_seconds=self.build_seconds,
            nodes={k:dict(node=v['node'],variables=v['variables'],rows=v['rows']) for k,v in self.nodes.items() if v['compiled']},
            queries=self.trace,metrics=dict(self.metrics),scope='Per-solve immutable syntax index; all caches cold. Semantic scan count preserves the full-enumeration definition.')
