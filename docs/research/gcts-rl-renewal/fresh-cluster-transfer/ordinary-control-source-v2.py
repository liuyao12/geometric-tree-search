"""SOURCE ONLY: specialized ordinary search using supplied exact licenses.

This is not the reference GCTS scheduler. It memoizes ground formulas and
re-embeds dependency DAGs. Whole registered group definitions are the only
macro inputs; their physical action menus are not claimed identical after
re-embedding. Every output expands to original zero-port/ordered-MP primitives.
No engine, checker, RNG, model loader or CLI is imported or dispatched.
"""
import copy
import math
import time

VERSION = 'ordinary-exact-licensed-agenda-control-v2'


class BudgetUnknown(Exception):
    pass


def search_candidate(graph, authority, descriptors, core, *, seconds,
                     operation_limit, event_limit, prerequisite_pins):
    """Produce a pending point certificate, never acceptance or unsatisfiability.

    Caller supplies one pristine independently qualified 24-row graph and its
    entire registered pool. Macro definitions are expanded once in their exact
    registered priority order, then zero-port licenses and ordered MP saturate.
    First-witness formula memoization is deliberately incomplete for the
    bounded row problem; failure to fit/realize a proof is always UNKNOWN.
    Full caller resources, independent witness replay and logical checking are
    required separately. Declaration/compilation and pool costs are not waived.
    """
    began = time.perf_counter()
    core.integer(operation_limit); core.integer(event_limit)
    if (type(seconds) not in (int, float) or not math.isfinite(seconds)
            or seconds <= 0 or operation_limit < 1 or event_limit < 1):
        raise ValueError('finite positive ordinary control bounds required')
    if graph.fixture or graph.height != 24 or not prerequisite_pins:
        raise ValueError('actual independently qualified 24-row context required')
    if type(descriptors) is not list:
        raise ValueError('literal complete registered whole pool required')
    pristine = core.canonical(graph.semantic_state())
    seeds = tuple(graph.initial_selected)
    if (tuple(graph.order) != seeds or any(graph.excluded)
            or len(seeds) != len(graph.context['ordered_local_premises'])
            or sorted(k.row for k in seeds) != list(range(len(seeds)))):
        raise ValueError('all original ordered hypotheses in a pristine prefix required')
    seed_by_row = {k.row: k for k in seeds}
    occurrences = [graph.recipes[k.recipe].witness.get('index') for k in seeds]
    if (any(graph.recipes[k.recipe].witness['rule'] != 'assumption' for k in seeds)
            or sorted(occurrences) != list(range(len(seeds)))):
        raise ValueError('exact separately licensed assumption occurrences retained')
    exterior = {(1, row): -1 for row in range(-23, 0)}
    if (set(graph.initial_marks) != set(exterior) | {(1, graph.height - 1)}
            or any(graph.initial_marks[point] != value for point, value in exterior.items())):
        raise ValueError('exact original negative-row sentinels and final target mark required')
    target = graph.initial_marks[1, graph.height - 1]
    if type(target) is not int or not 0 <= target < len(graph.formulas):
        raise ValueError('literal original target code required')
    deadline = began + seconds
    metrics = dict(operations=0, registration_checks=0, primitive_recipe_checks=0,
                   macro_member_checks=0, macro_expansions=0, derived_nodes=0,
                   rounds=0, padding_rows=0, certificate_rows=0)
    events = []; nodes = []; facts = {}; seed_nodes = {}
    macro_records = []; certificate = None; reason = None; ids = set()
    complete_pool_checked = False

    def tick(kind):
        if metrics['operations'] >= operation_limit or time.perf_counter() >= deadline:
            raise BudgetUnknown('ordinary checked operation/time budget')
        metrics['operations'] += 1
        if kind in metrics:
            metrics[kind] += 1

    def event(kind, **fields):
        if len(events) >= event_limit:
            raise BudgetUnknown('ordinary complete event budget')
        events.append(dict(index=len(events), kind=kind, **fields))

    def derive(recipe_index, inputs, origin, seed_row=None):
        recipe = graph.recipes[recipe_index]
        if (len(inputs) != len(recipe.inputs)
                or any(type(n) is not int or not 0 <= n < len(nodes) for n in inputs)
                or tuple(nodes[n]['output'] for n in inputs) != recipe.inputs):
            raise ValueError('exact prior ordered primitive dependencies required')
        if recipe.inputs:
            if (recipe.witness['rule'] != 'mp'
                    or graph.formulas[recipe.inputs[1]] !=
                    ['imp', graph.formulas[recipe.inputs[0]], graph.formulas[recipe.output]]):
                raise ValueError('no extra binary inference rule')
        elif recipe.witness['rule'] not in ('assumption', 'axiom', 'instantiate', 'eq_subst'):
            raise ValueError('no extra zero-port inference rule')
        node = dict(id=len(nodes), recipe=recipe_index, inputs=list(inputs),
                    output=recipe.output, origin=copy.deepcopy(origin), seed_row=seed_row)
        nodes.append(node); metrics['derived_nodes'] += 1
        first = recipe.output not in facts
        if first:
            facts[recipe.output] = node['id']
        event('licensed_dependency_node', node=copy.deepcopy(node), first_formula_witness=first)
        return node['id']

    def materialize(goal_node):
        nonlocal certificate
        needed = set()

        def visit(n):
            if n in needed:
                return
            needed.add(n)
            for dep in nodes[n]['inputs']:
                visit(dep)

        visit(goal_node)
        # Every original occurrence remains physically present even if unused.
        mapping = dict(seed_nodes)
        keys_by_row = dict(seed_by_row)
        ordered = [n for n in sorted(needed) if nodes[n]['seed_row'] is None]
        last = graph.height - 1
        # Place the goal only at the original final boundary; no formula copy rule.
        preceding = [n for n in ordered if n != goal_node]
        free = [row for row in range(last) if row not in keys_by_row]
        if len(preceding) > len(free):
            return 'dependency expansion exceeds the 24-row boundary'
        for n, row in zip(preceding, free):
            tick('primitive_recipe_checks')
            node = nodes[n]
            if any(dep not in mapping or mapping[dep] >= row for dep in node['inputs']):
                return 'dependency expansion lacks a strict prior row embedding'
            keys_by_row[row] = core.Key(node['recipe'], row,
                                       tuple(mapping[dep] for dep in node['inputs']))
            mapping[n] = row
        # Filler is a replay of an original licensed zero-port assumption.
        # This is extra certificate construction work, never a new proof rule.
        filler = seeds[0] if seeds else None
        holes = [row for row in range(last) if row not in keys_by_row]
        if holes and filler is None:
            return 'no original zero-port witness available for boundary padding'
        for row in holes:
            tick('primitive_recipe_checks')
            keys_by_row[row] = core.Key(filler.recipe, row, ())
            metrics['padding_rows'] += 1
        goal = nodes[goal_node]
        if any(dep not in mapping or mapping[dep] >= last for dep in goal['inputs']):
            return 'target witness lacks strict prior dependencies at final boundary'
        keys_by_row[last] = core.Key(goal['recipe'], last,
                                    tuple(mapping[dep] for dep in goal['inputs']))
        marks = dict(graph.initial_marks); totals = {}; placements = []; codes = {}
        for row in range(graph.height):
            tick('primitive_recipe_checks')
            key = keys_by_row[row]; recipe = graph.recipes[key.recipe]
            if any(ref not in codes or codes[ref] != code
                   for ref, code in zip(key.refs, recipe.inputs)):
                return 'padded certificate does not retain its exact prior premise formulas'
            placement = graph.decorate(key)
            for x, y, value in placement['t']:
                totals[x, y] = totals.get((x, y), 0) + value
            for x, y, value in placement['m']:
                if (x, y) in marks and marks[x, y] != value:
                    return 'padded primitive union conflicts with original boundary'
                marks[x, y] = value
            placements.append(placement); codes[row] = recipe.output
        if (totals != {(0, row): 1 for row in range(graph.height)}
                or codes[last] != target):
            return 'complete unit occupancy/original final conclusion mismatch'
        certificate = dict(status='finite_exact_point_tiling_pending_independent_logical_certificate',
                           model_epoch=graph.model_epoch,
                           source_bindings=copy.deepcopy(graph.source_bindings), placements=placements,
                           native_accepted=False, native_authority_activated=False,
                           compiler_correspondence='open')
        metrics['certificate_rows'] = len(placements)
        event('pending_padded_point_certificate', dependency_nodes=sorted(needed),
              node_row_mapping=sorted([n, row] for n, row in mapping.items()),
              certificate_sha256=core.digest(certificate), padding_rows=metrics['padding_rows'])
        return None

    try:
        event('ordinary_begin', model_epoch=graph.model_epoch, target_code=target,
              schedule='registered-priority whole macro definitions, zero-port licenses, repeated ordered-MP sweeps',
              limits=dict(seconds=seconds, operations=operation_limit, events=event_limit))
        # Reconstruct every registered definition before ordinary search; no pool trimming.
        for descriptor in descriptors:
            tick('registration_checks')
            compiled = authority.compile(graph, descriptor)
            if (core.canonical(descriptor) != compiled.text or compiled.identifier in ids):
                raise ValueError('whole macro is not its exact independently qualified registered definition')
            ids.add(compiled.identifier); macro_records.append((compiled, descriptor))
        complete_pool_checked = True
        # Stable equal-priority order matches the original registry insertion.
        macro_records.sort(key=lambda pair: pair[0].priority)
        for key in seeds:
            tick('primitive_recipe_checks')
            n = derive(key.recipe, (), dict(kind='original_assumption_occurrence', key=key.data()), key.row)
            seed_nodes[n] = key.row
        if target not in facts:
            for compiled, descriptor in macro_records:
                local = {row: n for n, row in seed_nodes.items()}
                member_nodes = []
                for key in sorted(compiled.members, key=lambda k: k.row):
                    tick('macro_member_checks')
                    if key.row in seed_by_row:
                        if seed_by_row[key.row] != key:
                            raise ValueError('macro cannot change any original ordered hypothesis occurrence')
                        member_nodes.append(local[key.row]); continue
                    recipe = graph.recipes[key.recipe]
                    if any(ref not in local for ref in key.refs):
                        raise ValueError('whole macro external premise is not an exact original root receptor')
                    n = derive(key.recipe, tuple(local[ref] for ref in key.refs),
                               dict(kind='registered_macro_primitive_expansion',
                                    descriptor_id=compiled.identifier, original_key=key.data()))
                    local[key.row] = n; member_nodes.append(n)
                metrics['macro_expansions'] += 1
                event('whole_macro_expanded', descriptor_id=compiled.identifier,
                      descriptor_sha256=core.digest(descriptor), member_node_ids=member_nodes)
                if target in facts:
                    break
        if target not in facts:
            for recipe in graph.recipes:
                tick('primitive_recipe_checks')
                if not recipe.inputs and recipe.output not in facts:
                    derive(recipe.index, (), dict(kind='licensed_zero_port', recipe_id=recipe.identifier))
        changed = True
        while target not in facts and changed:
            changed = False; metrics['rounds'] += 1
            for recipe in graph.recipes:
                tick('primitive_recipe_checks')
                if (recipe.inputs and recipe.output not in facts
                        and all(code in facts for code in recipe.inputs)):
                    derive(recipe.index, tuple(facts[code] for code in recipe.inputs),
                           dict(kind='licensed_ordered_MP', recipe_id=recipe.identifier))
                    changed = True
                    if target in facts:
                        break
            event('finite_formula_agenda_round', round=metrics['rounds'], facts=sorted(facts), changed=changed)
        if target in facts:
            reason = materialize(facts[target])
            status = 'ordinary_pending_complete_point_certificate' if reason is None else 'unknown_ordinary_boundary_embedding'
        else:
            status = 'unknown_ordinary_declared_fragment'; reason = 'finite formula closure did not find target; no unsatisfiability claim'
    except BudgetUnknown as exc:
        status = 'unknown_ordinary_search_budget'; reason = str(exc); certificate = None
    except Exception as exc:
        status = 'unknown_ordinary_infrastructure_failure'
        reason = type(exc).__name__ + ': ' + str(exc); certificate = None
    unchanged = core.canonical(graph.semantic_state()) == pristine
    if not unchanged:
        status = 'unknown_ordinary_infrastructure_failure'; reason = 'read-only ordinary control changed graph state'; certificate = None
    return dict(schema=VERSION, status=status, reason=reason, model_epoch=graph.model_epoch,
                source_bindings=copy.deepcopy(graph.source_bindings),
                prerequisite_pins=copy.deepcopy(prerequisite_pins),
                registered_macro_ids_checked=sorted(ids),
                complete_registered_pool_checked=complete_pool_checked,
                declared_full_pool_count=len(descriptors), events=events, dependency_nodes=nodes,
                first_formula_witnesses=sorted([code, n] for code, n in facts.items()),
                point_certificate=certificate, graph_unchanged=unchanged,
                metrics=metrics, seconds_through_return_preparation=time.perf_counter() - began,
                limits=dict(seconds=seconds, operations=operation_limit, events=event_limit),
                independent_logical_accepted=False, independent_resources_accepted=False,
                native_queries=0, training_updates=0, RNG_draws=0,
                scope='Specialized ordinary first-witness agenda over the same primitive/macro definitions; re-embedding differs from physical GCTS menus; every proof and resource gate remains pending; all failures UNKNOWN.')
