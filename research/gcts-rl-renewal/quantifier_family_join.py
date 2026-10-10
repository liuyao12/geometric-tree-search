"""Exact quantified-context matching over the frozen complete family join.

The frozen indexed join supplies positional embeddings, complete receptor
availability and aggregate validation. Only its syntax table construction is
extended. Enumeration is a measured control with the same resulting pools.
"""
import collections,time
import adaptive_receptor_clusters as C
from indexed_family_join import Join as Base
import quantifier_family_patterns as P

FIELDS=('kind','inputs','output','parameters','guards')

def variables(v):
    if isinstance(v,dict):return set().union(*(variables(x) for x in v.values()))
    if not isinstance(v,(tuple,list)):return set()
    own={v[1]} if v and v[0] in ('tmeta','papply','fmeta','fapply') else set()
    return own|set().union(*(variables(x) for x in v))

class Join(Base):
    def __init__(self,model,library,enumerated=False):
        began=time.perf_counter();self.model=model;self.library=tuple(sorted(library,key=lambda t:(-len(t['pattern']),t['name'])))
        self.context=model.context_hash();self.library_pin=C.digest([(t['name'],t['pattern'],t['level']) for t in self.library])
        self.enumerated=enumerated;self.nodes={};self.node_ids={};self.query_cache={};self.aggregate_cache={};self.digests={};self.trace=[];self.metrics=collections.Counter()
        for t in self.library:
            ids=[]
            for node in t['pattern']:
                identity=C.digest({k:node[k] for k in FIELDS});ids.append(identity)
                if identity not in self.nodes:self.nodes[identity]=dict(node=node,variables=tuple(sorted(variables({k:node[k] for k in FIELDS}))),compiled=False)
            self.node_ids[t['name']]=tuple(ids)
        self.build_seconds=time.perf_counter()-began

    def query(self,identity,env):
        node=self.nodes[identity];p=node['node']
        if self.enumerated:
            return tuple((rid,e) for rid,r in enumerate(self.model.catalog['rules'])
                         for e in P.matches(p,r) if all(k not in env or env[k]==v for k,v in e.items()))
        if not node['compiled']:
            began=time.perf_counter();rows=[];inverse=collections.defaultdict(set)
            for rid,r in enumerate(self.model.catalog['rules']):
                if r['kind']!=p['kind']:continue
                self.metrics['syntax_rule_tests']+=1
                for local in P.matches(p,r):
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

    def finish(self):
        checked=super().finish()
        if self.enumerated:return None
        checked['scope']='Cold solve-local typed terms and unary formula contexts; alpha normalization in proposals only. Original ground rules and exact markings govern every placement.'
        return checked
