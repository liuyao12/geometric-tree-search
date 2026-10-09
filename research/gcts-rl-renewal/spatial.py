"""Cold spatial motif mining and exact hierarchical point interfaces.

Adjacency means shared positive t-support, not polygon intersection. All twelve
declared scalar symmetries and translations are quotiented. A hierarchy here
partitions an already verified finite patch; it is NOT a substitution rule.
"""
from collections import Counter,defaultdict
from turtle import (Model,State,Graph,BASE,CAPACITY,SYMMETRIES,add,sub,transform,
                    compose,verify_patch)

def keys_tuple(keys): return tuple((int(o),tuple(tr)) for o,tr in keys)

def moved(keys,g,tr=(0,0,0)):
    return tuple((SYMMETRIES.index(compose(g,SYMMETRIES[o])),add(transform(p,g),tr)) for o,p in keys)

def canonical(keys):
    keys=keys_tuple(keys)
    candidates=[]
    for g in SYMMETRIES:
        transformed=moved(keys,g)
        origin=min(tr for _,tr in transformed)
        candidates.append(tuple(sorted((o,sub(tr,origin)) for o,tr in transformed)))
    return min(candidates)

def interface(model,keys):
    keys=keys_tuple(keys)
    if not verify_patch(model,keys): raise ValueError("invalid or multiply counted expansion")
    totals=Counter(); marks={}
    for key in keys:
        c=model.placement(key)
        totals.update(dict(c.occupancy)); marks.update(c.marks)
    return {"tiles":len(keys),"occupancy":[[p,v] for p,v in sorted(totals.items())],
            "marking":[[p,v] for p,v in sorted(marks.items())],
            "frontier":[[p,v,CAPACITY-v] for p,v in sorted(totals.items()) if v<CAPACITY],
            "completed_points":sum(v==CAPACITY for v in totals.values()),
            "units":sum(totals.values())}

def adjacency(model,keys):
    incident=defaultdict(list)
    for i,key in enumerate(keys):
        for p,v in model.placement(key).occupancy: incident[p].append(i)
    out={i:set() for i in range(len(keys))}
    for ids in incident.values():
        for i in ids: out[i].update(set(ids)-{i})
    return out

def connected_sets(graph,max_size):
    level={frozenset((i,)) for i in graph}
    for size in range(2,max_size+1):
        level={s|{j} for s in level for i in s for j in graph[i] if j not in s}
        yield from sorted(level,key=lambda s:tuple(sorted(s)))

def mine(model,donors,max_size=4,limit=24,min_donors=2):
    counts=Counter(); provenance=defaultdict(set); occurrences=[]
    for donor in donors:
        if donor["status"]!="consistent_finite_patch": continue
        keys=keys_tuple(donor["placements"])
        cache=[]
        for ids in connected_sets(adjacency(model,keys),max_size):
            signature=canonical([keys[i] for i in ids])
            counts[signature]+=1; provenance[signature].add(donor["seed"])
            cache.append((ids,signature))
        occurrences.append((donor,cache))
    ordered=sorted((s for s in counts if len(provenance[s])>=min_donors),
                   key=lambda s:(-(len(s)-1)*counts[s],-len(provenance[s]),s))[:limit]
    library=[{"id":i,"count":counts[s],"donor_seeds":sorted(provenance[s]),"expansion":s,
              "interface":interface(model,s)} for i,s in enumerate(ordered)]
    return library,{"connected_subsets":sum(len(c) for _,c in occurrences),"distinct_shapes":len(counts),
                    "recurrent_shapes":sum(len(v)>=min_donors for v in provenance.values()),
                    "selected_types":len(library),"min_distinct_donors":min_donors,
                    "max_base_tiles":max_size,"canonical_action":"all 12 symmetries + translation"}

def partition(model,placements,library,levels=3):
    """Exact disjoint base expansions; learned motifs guide the first grouping.

    Higher levels greedily pair adjacent groups. They expose candidate parent
    shapes for inspection, but are not frozen recurrent grammar productions.
    """
    keys=keys_tuple(placements); graph=adjacency(model,keys)
    catalog={keys_tuple(m["expansion"]):m for m in library}
    candidates=[]
    max_size=max((len(s) for s in catalog),default=1)
    for ids in connected_sets(graph,max_size):
        sig=canonical([keys[i] for i in ids])
        if sig in catalog:
            m=catalog[sig]; candidates.append((-(len(ids)-1)*m["count"],tuple(sorted(ids)),m["id"]))
    used=set(); groups=[]
    for _,ids,typ in sorted(candidates):
        if not used.intersection(ids): groups.append({"base_ids":list(ids),"type":typ}); used.update(ids)
    covered=len(used)
    groups.extend({"base_ids":[i],"type":"singleton"} for i in range(len(keys)) if i not in used)
    history=[]
    for level in range(levels):
        for group in groups:
            group["interface"]=interface(model,[keys[i] for i in group["base_ids"]])
        ids=[i for g in groups for i in g["base_ids"]]
        assert sorted(ids)==list(range(len(keys))) and len(ids)==len(set(ids))
        history.append({"level":level+1,"groups":groups,"verified_partition":True})
        if level+1==levels: break
        remaining=set(range(len(groups))); parents=[]
        for i in range(len(groups)):
            if i not in remaining: continue
            remaining.remove(i); a=set(groups[i]["base_ids"])
            partners=[j for j in remaining if any(graph[k]&set(groups[j]["base_ids"]) for k in a)]
            children=[i]
            if partners:
                j=min(partners,key=lambda j:(len(groups[j]["base_ids"]),j)); remaining.remove(j)
                a.update(groups[j]["base_ids"]); children.append(j)
            parents.append({"base_ids":sorted(a),"children":children,"type":"observed_parent"})
        groups=parents
    return {"levels":history,"first_level_motif_tiles":covered,"base_tiles":len(keys),
            "scope":"finite disjoint hierarchy; upper parent types not a recurrent substitution grammar"}

class Proposer:
    """Symmetry-complete alignments of mined motifs; singleton fallback retained."""
    def __init__(self,library):
        self.aligned=defaultdict(set)
        for motif in library:
            expansion=keys_tuple(motif["expansion"])
            for g in SYMMETRIES:
                seq=moved(expansion,g)
                for o,p in seq:
                    self.aligned[o].add(tuple(sorted((q,sub(tr,p)) for q,tr in seq)))
    def __call__(self,model,state,graph,keys,library,remaining):
        actions={(k,) for k in keys}
        for key in keys:
            for relative in self.aligned[key[0]]:
                if len(relative)>remaining: continue
                expanded=tuple((o,add(p,key[1])) for o,p in relative)
                model.metrics["cluster_validation_attempts"]+=1
                trial=state.copy()
                try:
                    for k in expanded: trial.place(model.placement(k))
                except ValueError: continue
                if not verify_patch(model,trial.order): continue
                # Plan through the actual complete graph, returning a schedulable
                # prefix when a forced move outside the proposed cluster occurs.
                child=state.copy(); child_graph=graph.copy(); pending=set(expanded); seq=[]
                while pending:
                    kind,_,domain=child_graph.decision(child)
                    if kind in ("dead","empty"): break
                    available=pending.intersection(domain)
                    if not available: break
                    k=key if not seq else min(available)
                    if k not in available: break
                    seq.append(k); pending.remove(k)
                    child_graph.update(model,child,child.place(model.placement(k)))
                if len(seq)>1: actions.add(tuple(seq))
        return sorted(actions)
