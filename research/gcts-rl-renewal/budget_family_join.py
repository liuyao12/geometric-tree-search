"""Cold exact receptor join with structural ordering and scale-balanced hints.

Every matching expansion is validated against the decorated point graph. A
bounded proposal pool shares its slots across observed cluster sizes. Complete
base candidates and fallback are untouched. Formula-word hashes no longer
break ordering ties; shape and original placement keys do.
"""
import collections,itertools
import adaptive_receptor_clusters as C
import movable_proof_regions as M
import quantified_receptors as Q
from quantifier_family_join import Join as Original

class Join(Original):
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
            if key in self.digests:self.metrics['item_order_hits']+=1
            else:self.digests[key]=True;self.metrics['item_order_misses']+=1
            slots=tuple(k[0] for k in item['members'])
            return (-int(model.catalog['rules'][item['members'][-1][1]]['output']==model.target),
                    -len(item['members']),max(slots)-min(slots),item['members'],item['template'])
        result=sorted(pool.values(),key=ordering)
        groups=collections.defaultdict(list)
        for item in result:groups[len(item['members'])].append(item)
        # The proposal cap gives every observed scale a share. It changes no
        # original domain, pruning decision, placement or fallback alternative.
        balanced=[]
        sizes=sorted(groups,reverse=True)
        for index in range(max(map(len,groups.values()),default=0)):
            balanced.extend(groups[size][index] for size in sizes if index<len(groups[size]))
        return balanced[:limit],dict(compatible=len(result),scanned=scanned,truncated=max(0,len(result)-limit))

