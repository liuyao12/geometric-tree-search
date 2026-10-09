"""Data-driven diversity and rarity features; no named metatile families.

Selection bins use size and reflection balance, invariant under the declared
lattice group. All bins remain eligible. This changes only a finite proposal
library and finite patch partitions, never base candidate domains or legality.
"""
import math
from collections import Counter,defaultdict
from turtle import SYMMETRIES,Model
from spatial import keys_tuple,canonical,adjacency,connected_sets,interface

def hand(o):
    p=SYMMETRIES[o][1]
    return sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))%2

def category(keys):
    n=sum(hand(o) for o,tr in keys)
    return len(keys),min(n,len(keys)-n)

def mine(model,donors,max_size=4,per_category=2):
    counts=Counter();provenance=defaultdict(set);occurrences=0
    for donor in donors:
        if donor["status"]!="consistent_finite_patch": continue
        keys=keys_tuple(donor["placements"])
        for ids in connected_sets(adjacency(model,keys),max_size):
            sig=canonical([keys[i] for i in ids]);counts[sig]+=1;provenance[sig].add(donor["seed"]);occurrences+=1
    bins=defaultdict(list)
    for sig,n in counts.items():
        if len(provenance[sig])>=2:bins[category(sig)].append(sig)
    selected=[]
    for cat,shapes in sorted(bins.items()):
        ordered=sorted(shapes,key=lambda s:(-counts[s],s))[:per_category]
        selected.extend(ordered)
    library=[{"id":i,"count":counts[s],"donor_seeds":sorted(provenance[s]),"category":category(s),
              "expansion":s,"interface":interface(model,s)} for i,s in enumerate(selected)]
    return library,{"connected_subsets":occurrences,"distinct_shapes":len(counts),"categories":len(bins),
                    "selected_types":len(library),"per_category":per_category,
                    "mixed_handed_types":sum(category(s)[1]>0 for s in selected),
                    "scope":"invariant feature diversity; no known metatile family or substitution supplied"}

def partition(model,placements,library,levels=4):
    """Rarity-weighted first grouping; later adjacent pairs remain hypotheses."""
    keys=keys_tuple(placements);graph=adjacency(model,keys);n=len(keys)
    populations=Counter(hand(o) for o,tr in keys)
    info={i:-math.log(populations[hand(o)]/n) for i,(o,tr) in enumerate(keys)}
    catalog={keys_tuple(m["expansion"]):m for m in library};candidates=[]
    for ids in connected_sets(graph,max((len(s) for s in catalog),default=1)):
        sig=canonical([keys[i] for i in ids])
        if sig in catalog:
            m=catalog[sig]
            score=sum(info[i] for i in ids)*(len(ids)-1)/len(ids)*math.log1p(m["count"])
            candidates.append((-score,tuple(sorted(ids)),m["id"]))
    used=set();groups=[]
    for _,ids,typ in sorted(candidates):
        if not used.intersection(ids):used.update(ids);groups.append({"base_ids":list(ids),"type":typ})
    covered=len(used)
    groups.extend({"base_ids":[i],"type":"singleton"} for i in range(n) if i not in used)
    history=[]
    for level in range(levels):
        for g in groups:g["interface"]=interface(model,[keys[i] for i in g["base_ids"]])
        assert sorted(i for g in groups for i in g["base_ids"])==list(range(n))
        history.append({"level":level+1,"groups":groups,"verified_partition":True})
        if level+1==levels:break
        pending=set(range(len(groups)));parents=[]
        for i in range(len(groups)):
            if i not in pending:continue
            pending.remove(i);a=set(groups[i]["base_ids"])
            choices=[j for j in pending if any(graph[k]&set(groups[j]["base_ids"]) for k in a)]
            children=[i]
            if choices:
                j=min(choices,key=lambda j:(len(groups[j]["base_ids"]),j));pending.remove(j)
                a.update(groups[j]["base_ids"]);children.append(j)
            parents.append({"base_ids":sorted(a),"children":children,"type":"observed_parent"})
        groups=parents
    return {"levels":history,"first_level_motif_tiles":covered,"base_tiles":n,
            "scope":"rarity-weighted finite grouping; no stationary recursive production certified"}
