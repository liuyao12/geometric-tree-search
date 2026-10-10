"""Complete positional GCTS with exact copy rollback and retained cutoffs."""
import collections
import time

import dependency_budget as B
import movable_proof_regions as M


def search(model, attempts=50000, seconds=60):
    started = time.perf_counter()
    initial = model.initial()
    graph = B.Graph(model, initial)
    metrics = collections.Counter()
    found = None
    best = initial

    def visit(state, incidence):
        nonlocal found, best
        kind, p, keys = incidence.decision(state)
        metrics['nodes'] += 1
        metrics['peak_candidates'] = max(metrics['peak_candidates'],
                                        sum(len(d) for d in incidence.domains.values()))
        tree = dict(kind=kind, point=p, children=[],
                    census=[(q, len(d), state.generations[q])
                            for q, d in sorted(incidence.domains.items())])
        if time.perf_counter()-started > seconds:
            tree['cutoff'] = 'entry_wall'
            return None, tree
        if len(state.order) > len(best.order) and kind != 'dead':
            best = state
        if kind == 'dead':
            metrics['dead'] += 1
            return False, tree
        if kind == 'empty':
            found = state
            return True, tree
        metrics[kind] += 1
        for key in keys:
            if metrics['attempts'] >= attempts or time.perf_counter()-started > seconds:
                tree['cutoff'] = 'before_placement'
                return None, tree
            metrics['attempts'] += 1
            child, following = state.copy(), incidence.copy()
            following.update(model, child, child.place(model.placement(key)))
            okay, sub = visit(child, following)
            tree['children'].append(dict(key=key, tree=sub))
            if okay is not False:
                return okay, tree
            metrics['backtracks'] += 1
        return False, tree

    okay, tree = visit(initial, graph)
    selected = found or best
    rows, endpoint = M.decode(model, selected.order) if found else (None, None)
    return dict(status='finite_exact_proof_region' if okay else
                'unknown_search_budget' if okay is None else 'exhausted_finite_region',
                placements=selected.order, tile_generations=selected.tile_generations,
                proof=rows, endpoint=endpoint, metrics=dict(metrics),
                graph_metrics=dict(model.metrics), search_tree=tree,
                candidate_universe=model.cardinality(),
                seconds=time.perf_counter()-started,
                limits=dict(attempts=attempts, seconds=seconds))
