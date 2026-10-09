"""A deliberately narrow blind substitution control: integer self-inflations.

Failure does not rule out multiple metatile types, algebraic inflation, changed
boundaries, or combinatorial substitution. No known rule is imported.
"""
import time
from turtle import Model,State,Graph,VERTICES,point_data,verify_patch,Limit

def probe(scale,node_limit=10000,seconds=20):
    start = time.monotonic()
    vertices = tuple(tuple(scale*x for x in p) for p in VERTICES)
    desired = point_data(vertices)
    initial = State(totals={p:12-v for p,v in desired.items()},roots={p:0 for p in desired},
                    generations={p:0 for p in desired},allowed_points=frozenset(desired))
    model = Model()
    nodes = 0
    witness = None
    def visit(state,graph):
        nonlocal nodes,witness
        nodes += 1
        if nodes>node_limit or time.monotonic()-start>seconds: raise Limit()
        kind,p,keys = graph.decision(state)
        if kind=="dead": return False
        if kind=="empty": witness = state.order; return True
        for key in keys:
            child,g = state.copy(),graph.copy()
            g.update(model,child,child.place(model.placement(key)))
            if visit(child,g): return True
        return False
    try:
        visit(initial,Graph(model,initial))
        status = "finite_exact_self_inflation" if witness else "exhausted_finite_self_inflation"
    except Limit: status = "unknown_budget"
    if witness:
        from collections import Counter
        actual = Counter()
        for key in witness:
            for p,v in model.placement(key).occupancy: actual[p] += v
        assert dict(actual)==desired and verify_patch(model,witness)
    return {"scale":scale,"status":status,"nodes":nodes,"seconds":time.monotonic()-start,
            "required_points":len(desired),"placements":witness,
            "scope":"integer dilation of single turtle outline; fixed exterior point contributions",
            "claim":"restricted control only; does not decide general substitution existence"}
