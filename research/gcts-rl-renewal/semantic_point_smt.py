"""Explicitly specialized Z3 control on the same complete exact point model."""
import collections,time
from certificate_boundary_search import digest

def solve(model,seconds=30,disabled=False):
    began=time.perf_counter()
    if disabled:return dict(status='unknown_search_budget',proof=None,placements=[],seconds=time.perf_counter()-began,scope='Declared zero-search control.')
    import z3
    solver=z3.Solver();solver.set(random_seed=0)
    keys=sorted(model.cache);xs={k:z3.Bool('c_'+str(i)) for i,k in enumerate(keys)}
    points=sorted(set(model.initial().marks)|{p for c in model.cache.values() for p,v in c.marks})
    values={p:z3.Int('m_'+str(i)) for i,p in enumerate(points)}
    for p,ks in sorted(model.align_cache.items()):
        solver.add(z3.PbEq([(xs[k],1) for k in ks],1))
    for p,v in sorted(model.initial().marks.items()):solver.add(values[p]==v)
    # Group equal implications, preserving every original assignment. This
    # reduces duplicated assertion nodes, not the candidate universe:
    # (c1 -> m=v) and (c2 -> m=v) iff ((c1 or c2) -> m=v).
    groups=collections.defaultdict(list)
    for k,c in sorted(model.cache.items()):
        for p,v in c.marks:groups[(p,v)].append(k)
    grouped=[dict(point=p,value=v,keys=ks) for (p,v),ks in sorted(groups.items())]
    group_sha=digest(grouped);memberships=sum(len(row['keys']) for row in grouped)
    complete=True
    for (p,v),ks in sorted(groups.items()):
        if time.perf_counter()-began>=seconds:complete=False;break
        solver.add(z3.Implies(z3.Or([xs[k] for k in ks]),values[p]==v))
    encode=time.perf_counter()-began
    if not complete or encode>=seconds:
        return dict(status='unknown_encoding_budget',proof=None,placements=[],
                    seconds=encode,encode_seconds=encode,z3_version=z3.get_version_string(),
                    boolean_variables=len(xs),marking_integer_variables=len(values),
                    value_groups=len(groups),mark_assignment_memberships=memberships,
                    group_encoding_sha256=group_sha,complete_encoding=complete,
                    scope='Encoding exceeded the declared wall budget. No partial encoding was submitted to the solver.')
    solver.set(timeout=max(1,int((seconds-encode)*1000)))
    check=time.perf_counter();status=solver.check()
    query_seconds=time.perf_counter()-check;selected=[];proof=None
    if status==z3.sat:
        answer=solver.model();selected=[k for k in keys if z3.is_true(answer.eval(xs[k],model_completion=True))]
        verify_selected(model,selected);proof=model.decode(selected);label='smt_exact_point_region'
    elif status==z3.unsat:label='solver_unsat_finite_point_region'
    else:label='unknown_solver_budget'
    stats={str(solver.statistics().keys()[i]):str(solver.statistics()[i][1]) for i in range(len(solver.statistics()))}
    elapsed=time.perf_counter()-began;serialize=time.perf_counter();sexpr=solver.sexpr();serialization=time.perf_counter()-serialize
    return dict(status=label,proof=proof,placements=selected,seconds=elapsed,encode_seconds=encode,
                query_seconds=query_seconds,z3_version=z3.get_version_string(),boolean_variables=len(xs),
                marking_integer_variables=len(values),constraints=len(solver.assertions()),smtlib=sexpr,statistics=stats,
                complete_encoding=True,value_groups=len(groups),mark_assignment_memberships=memberships,
                group_encoding_sha256=group_sha,smtlib_serialization_seconds=serialization,
                reason_unknown=solver.reason_unknown() if status==z3.unknown else None,
                scope='Z3 specialized control with one Boolean per original placement, unit-capacity equality at every required center, and exact shared marking-value equalities. Same finite region/inventory as GCTS, different decision algorithm. Root proof receives separate whole native checking; solver UNSAT is cross-checked against independently audited GCTS exhaustion where available.')

def verify_selected(model,placements):
    values=dict(model.initial().marks);totals={}
    if len(set(placements))!=len(placements):raise ValueError('duplicate SMT placement')
    for k in placements:
        c=model.placement(k)
        for p,v in c.occupancy:totals[p]=totals.get(p,0)+v
        for p,v in c.marks:
            if p in values and values[p]!=v:raise ValueError('SMT mark mismatch')
            values[p]=v
    if set(totals)!=set(model.align_cache) or any(v!=12 for v in totals.values()):raise ValueError('SMT capacity mismatch')
    return dict(points=len(totals),mark_points=len(values))
