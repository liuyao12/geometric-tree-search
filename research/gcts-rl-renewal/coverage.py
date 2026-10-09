"""Fair core activation with backtracking across growth checkpoints.

The finite requested radii are a prefix of a fair A2 exhaustion. Checkpoints
complete their core and retain a viable EXPOSED frontier: finite patches, not
exact tilings of the full active growth domain and not plane certificates.
Earlier placement alternatives stay on the stack when the next core activates.
"""
import random,time
from turtle import Model,State,Graph,rooted,verify_patch,Limit,action_features

def hexagon(radius):
    return {(x,y,-x-y) for x in range(-radius,radius+1) for y in range(-radius,radius+1)
            if max(abs(x),abs(y),abs(x+y))<=radius}

def activate(model,state,graph,points):
    """Mutate a CHILD transaction only; roots/generations belong to the snapshot."""
    for p in points:
        state.roots[p]=0;state.generations[p]=0
    graph.update(model,state,points)

def search(model,radii=(2,4,6),seed=0,node_limit=5000,seconds=20,policy=None,library=(),proposal_provider=None):
    if not radii or any(type(r) is not int or r<0 for r in radii) or tuple(sorted(set(radii)))!=tuple(radii):
        raise ValueError("strictly increasing nonnegative integer radii required")
    cores=[hexagon(r) for r in radii];rng=random.Random(seed);start=time.monotonic()
    nodes=branches=forced=backtracks=activations=0;found=None;best=None;best_stage=-1
    initial=rooted(model);graph=Graph(model,initial);activate(model,initial,graph,cores[0]);activations+=1
    def visit(state,g,stage,path):
        nonlocal nodes,branches,forced,backtracks,activations,found,best,best_stage
        nodes+=1
        if nodes>node_limit or time.monotonic()-start>seconds:raise Limit()
        kind,point,keys=g.decision(state)
        if kind=="dead":return False
        if best is None or stage>best_stage or (stage==best_stage and len(state.order)>len(best.order)):
            best=state.copy();best_stage=stage
        if all(state.totals.get(p,0)==12 for p in cores[stage]):
            assert verify_patch(model,state.order,cores[stage])
            checkpoint={"radius":radii[stage],"required_core_points":len(cores[stage]),"tiles":len(state.order),
                        "placements":state.order.copy(),"tile_generations":state.tile_generations.copy(),
                        "frontier_points":len(g.domains),"verified_core":True}
            if stage+1==len(radii):found=(state,path+[checkpoint]);return True
            child,child_graph=state.copy(),g.copy()
            activate(model,child,child_graph,cores[stage+1]);activations+=1
            return visit(child,child_graph,stage+1,path+[checkpoint])
        if kind=="empty":raise AssertionError("unsatisfied root disappeared")
        if kind=="forced":actions=[(keys[0],)]
        else:
            branches+=1
            actions=proposal_provider(model,state,g,keys,library,8) if proposal_provider else [(k,) for k in keys]
            rng.shuffle(actions)
            if policy:actions.sort(key=lambda seq:sum(policy.weights[k]*v for k,v in action_features(model,state,g,seq).items()),reverse=True)
        for seq in actions:
            child,child_graph=state.copy(),g.copy();executed=0
            for key in seq:
                step_kind,_,domain=child_graph.decision(child)
                if step_kind in ("dead","empty") or key not in domain:break
                if step_kind=="forced":forced+=1
                child_graph.update(model,child,child.place(model.placement(key)));executed+=1
            if executed and visit(child,child_graph,stage,path):return True
            backtracks+=1
        return False
    try:
        visit(initial,graph,0,[]);status="consistent_finite_patch_with_core_coverage" if found else "exhausted_search_without_exported_failure_tree"
    except (Limit,RecursionError):status="unknown_budget"
    state=found[0] if found else best or initial;final_graph=Graph(model,state)
    assert verify_patch(model,state.order)
    result={"status":status,"seed":seed,"radii":radii,"nodes":nodes,"branches":branches,"forced":forced,
            "backtracks":backtracks,"core_activations":activations,"seconds":time.monotonic()-start,
            "placements":state.order,"tile_generations":state.tile_generations,"tiles":len(state.order),
            "frontier_points":len(final_graph.domains),"checkpoints":found[1] if found else [],
            "verified_point_patch":True,"exposed_frontier_viable":all(final_graph.domains.values()),
            "scope":"finite cores filled with viable exposed frontier; no infinite construction"}
    return result
