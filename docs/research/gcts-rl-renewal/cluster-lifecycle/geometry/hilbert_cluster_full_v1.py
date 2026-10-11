"""SOURCE-ONLY prospective actual full-language lifecycle controlled gate.

No target DFS, native/compiler activation or authored24 proof-word loading.
The full source plan is frozen only after tiny producer and independent gates.
The raw iterator is the exact earlier frozen authored direct control, copied with
its source pin; independently owned actual audit remains a separate prerequisite.
"""
import copy
import hashlib
import itertools
import json
import resource
import signal
import sys
import time
from pathlib import Path
import hilbert_cluster_lifecycle_v1 as life
core=life.core
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent

def raw_inventory(data):
    # Direct raw prototype representation reconstructed separately from factors.
    codes = {core.canonical(f): i for i, f in enumerate(data["formula_codes"])}
    rows = []
    for index, r in enumerate(data["recipes"]):
        rows.append({"index": index, "id": r["id"], "witness": r["primitive_witness"],
                     "formulas": r["ordered_premise_formulas"],
                     "output": codes[core.canonical(r["primitive_witness"]["formula"])],
                     "inputs": tuple(codes[core.canonical(f)] for f in r["ordered_premise_formulas"])})
    return rows

def raw_point_iterator(g, row, inventory):
    # Enumerate ALL raw offsets then reject by generic point capacity/agreement.
    # No factor count, strict-prior row masks, core point_data or core legal used.
    if g.totals[row] + 1 > 1:
        return
    for recipe in inventory:
        output = (1, row)
        if output in g.marks and g.marks[output] != recipe["output"]:
            continue
        arity = len(recipe["inputs"])
        offsets = itertools.product(range(1 - g.height, 0), repeat=arity) if arity else [()]
        for pair in offsets:
            marking = {output: recipe["output"]}
            refs = []
            valid = True
            for port, (offset, code) in enumerate(zip(pair, recipe["inputs"])):
                source = row + offset
                point = (1, source)
                if point in marking and marking[point] != code:
                    valid = False; break
                marking[point] = code
                marking[(2 + port, row)] = offset
                refs.append(source)
            if not valid or any(p in g.marks and g.marks[p] != v for p, v in marking.items()):
                continue
            key = core.Key(recipe["index"], row, tuple(refs))
            if key in g.excluded[row]:
                continue
            yield key, [[0, row, 1]], [[x, y, v] for (x, y), v in sorted(marking.items())]

def independently_decorate(g, key, inventory, t, m):
    data = inventory[key.recipe]
    command = copy.deepcopy(data["witness"])
    if key.refs:
        command["antecedent"], command["implication"] = key.refs
    prototype = {"recipe_id": data["id"], "primitive_witness": data["witness"],
                 "ordered_premise_formulas": data["formulas"],
                 "relative_ordered_input_offsets": [ref - key.row for ref in key.refs],
                 "orientation": "identity", "t": [[x, y - key.row, v] for x, y, v in t],
                 "m": [[x, y - key.row, v] for x, y, v in m], "marking_version": core.MARKING_VERSION,
                 "formula_registry_sha256": core.digest(g.formulas),
                 "authority_epoch": core.digest({k: v for k, v in g.authority.items() if k != "epoch"})}
    preimage = {"prototype_id": "primitive-prototype-" + core.digest(prototype),
                "prototype_preimage": prototype, "transform": [0, key.row],
                "context_id": core.digest(g.context), "ordered_input_rows": list(key.refs),
                "primitive_command": command, "t": t, "m": m,
                "authority_epoch": prototype["authority_epoch"],
                "formula_registry_sha256": prototype["formula_registry_sha256"]}
    return {"id": "aggregate-primitive-" + core.digest(preimage), "identity_preimage": preimage}

def compare_complete(g, inventory, *, label, representatives=None):
    rows = []
    for row in range(g.height):
        counted, per_recipe = 0, [0] * len(inventory)
        checksum = hashlib.sha256()
        sentinel = object()
        direct = raw_point_iterator(g, row, inventory)
        for implicit, raw in itertools.zip_longest(g.candidates(row), direct, fillvalue=sentinel):
            if implicit is sentinel or raw is sentinel:
                raise AssertionError("complete candidate iterator length mismatch: " + label)
            key, t, m = raw
            if implicit != key or g.point_data(implicit) != (t, m):
                raise AssertionError("complete raw candidate/t/m mismatch: " + label)
            checksum.update((core.canonical([key.data(), t, m]) + "\n").encode())
            counted += 1
            per_recipe[key.recipe] += 1
            if representatives is not None:
                representatives.setdefault((key.recipe, "first"), (key, t, m))
                representatives[(key.recipe, "last")] = (key, t, m)
        assert counted == g.domains[row].count
        assert (counted == 0) == (g.domains[row].count == 0)
        assert (counted == 1) == (g.domains[row].count == 1)
        rows.append({"row": row, "frontier": g.totals[row] < 1, "degree": counted,
                     "per_recipe_degree": per_recipe, "complete_key_t_m_stream_sha256": checksum.hexdigest()})
    return {"label": label, "rows": rows, "candidate_nodes": sum(r["degree"] for r in rows),
            "incidence_edges": sum(r["degree"] for r in rows),
            "frontier_points": sum(r["frontier"] for r in rows),
            "candidate_node_incidence_reason": "each primitive placement has exactly one unit positive-support edge"}

def independent_decision(g, comparison):
    rows = [r for r in comparison["rows"] if r["frontier"]]
    if any(r["degree"] == 0 for r in rows):
        row = min(r["row"] for r in rows if r["degree"] == 0)
        kind, count = "dead", 0
    elif any(r["degree"] == 1 for r in rows):
        row = min(r["row"] for r in rows if r["degree"] == 1)
        kind, count = "forced", 1
    elif not rows:
        return core.Decision("complete", None, 0, None)
    else:
        def generation(r):
            return min([g.roots[r]] + [generation for key, generation in g.selected.items() if key.row == r])
        selected = min(rows, key=lambda r: (generation(r["row"]), r["degree"], r["row"]))
        row, kind, count = selected["row"], "branch", selected["degree"]
    gen = min([g.roots[row]] + [generation for key, generation in g.selected.items() if key.row == row])
    return core.Decision(kind, row, count, gen)

def identity_control(g, key, inventory):
    data = inventory[key.recipe]
    marking = {(1, key.row): data["output"]}
    for port, (ref, code) in enumerate(zip(key.refs, data["inputs"])):
        if (1, ref) in marking and marking[(1, ref)] != code:
            raise ValueError("independent identity control found local conflict")
        marking[(1, ref)] = code
        marking[(2 + port, key.row)] = ref - key.row
    t = [[0, key.row, 1]]
    m = [[x, y, v] for (x, y), v in sorted(marking.items())]
    assert g.point_data(key) == (t, m)
    expected = independently_decorate(g, key, inventory, t, m)
    actual = g.decorate(key)
    assert actual["id"] == expected["id"] and actual["identity_preimage"] == expected["identity_preimage"]
    return {"key": key.data(), "id": actual["id"], "preimage_sha256": core.digest(expected["identity_preimage"])}

def main():
    started=time.perf_counter()
    signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('actual lifecycle conformance alarm')))
    signal.alarm(170)
    planpath=HERE/'full-language-plan-v1.json'
    plan=json.loads(planpath.read_text())
    for p in plan['sources']+plan['inputs']+plan['preserved_files']:
        if core.pin(ROOT/p['path'])!={k:p[k] for k in ('sha256','bytes')}:
            raise ValueError('frozen full-language lifecycle pin mismatch: '+p['path'])
    roles={p['role']:ROOT/p['path'] for p in plan['inputs']}
    tiny=core.read_json(roles['new_tiny_lifecycle_lifetime'])
    tiny_independent=core.read_json(roles['new_tiny_lifecycle_independent_result'])
    if tiny['status']!='passed_authored_tiny_lifecycle_full_lifetime':
        raise ValueError('tiny producer prerequisite incomplete')
    if tiny_independent['status']!=plan['tiny_independent_accepted_status']:
        raise ValueError('tiny independent prerequisite incomplete')
    data=core.read_json(roles['primitive_model']); inventory=raw_inventory(data)
    g=core.frozen_model(ROOT,plan)
    if len(g.recipes)!=229 or len(g.formulas)!=217 or g.height!=24:
        raise ValueError('full unchanged language is mandatory')
    if len(g.initial_selected)!=3 or any(g.selected[k]!=0 for k in g.initial_selected):
        raise ValueError('actual recipient hypothesis seeds stay generation zero')
    family_started=time.perf_counter()
    family=life.frozen_family_authority(g,plan)
    family_preparation_seconds=time.perf_counter()-family_started
    # The loader preserves all171 immutable body schemas; it discards the example
    # and does not read the authored witness control, even though old pins remain.
    if len(family.bodies)!=171:raise ValueError('complete source body registry required')
    axiom=next(r.index for r in g.recipes if r.witness['rule']=='axiom')
    if g.recipes[axiom].output!=0:raise ValueError('assigned formula zero control changed')
    ax3,ax4,ax8=(core.Key(axiom,row) for row in (3,4,8))
    # A universal-uniqueness family attaches to the existing first guard. This is
    # not the authored24 chain or an authored target proof word. No body is run as
    # an atomic macro, and no new proof search is launched by this controlled gate.
    family_name=next(name for name,text in family.bodies
                     if json.loads(text)['premise_codes']==[g.marks[1,0]]
                     and len(json.loads(text)['primitive_members'])==10)
    # Fixed distant MP control is selected by full domain, away from all selected
    # rows and uniqueness body rows; no target conclusion formula is requested.
    distant=next(k for k in g.candidates(22) if g.recipes[k.recipe].inputs
                 and min(k.refs)>=13)
    other=next(k for k in g.candidates(22) if k.recipe==distant.recipe and k!=distant
               and min(k.refs)>=13)
    descriptor_started=time.perf_counter()
    bodies=[json.loads(t) for _,t in family.bodies]
    bodies += [life.primitive_body(g,'fixed-shared-single-axiom',[ax3]),
               life.primitive_body(g,'fixed-shared-two-axioms',[ax3,ax4]),
               life.primitive_body(g,'fixed-waiting-later-axiom',[ax8]),
               life.primitive_body(g,'fixed-distant-mp-and-legal-sibling',[ax4,distant])]
    authority=life.BodyAuthority.build(g,json.loads(family.source_text),bodies)
    specs=[('fixed-shared-single-axiom',(),(3,),0),
           ('fixed-shared-two-axioms',(),(3,4),1),
           (family_name,(0,),tuple(range(3,13)),2),
           ('fixed-waiting-later-axiom',(),(8,),3),
           ('fixed-distant-mp-and-legal-sibling',authority.body('fixed-distant-mp-and-legal-sibling')['canonical_input_rows'],(4,22),4)]
    descriptors=[authority.expected(g,*spec) for spec in specs]
    c=life.Controller(g,authority,descriptors); e=life.Executor(c)
    descriptor_preparation_seconds=time.perf_counter()-descriptor_started
    comparisons,states,operations,identities=[],[],[],[]

    def snapshot(label):
        comparison=compare_complete(g,inventory,label=label)
        if g.decision()!=independent_decision(g,comparison):raise AssertionError('scheduler mismatch')
        comparison['lifecycle_metrics']=dict(c.metrics)
        if g.decision().kind in ('branch','forced'):
            d=g.decision(); base=list(g.candidates(d.row)); ordering=list(c.ordered(d))
            if len(ordering)!=len(base) or set(ordering)!=set(base):
                raise AssertionError('preferred plus fallback is not a full permutation')
            if d.kind=='forced' and ordering!=base:raise AssertionError('hint bypassed forced choice')
            comparison['decision_ordering']=[k.data() for k in ordering]
        comparisons.append(comparison)
        states.append({'label':label,'state':c.semantic_state()})

    def transaction(name,payload,call):
        before=c.semantic_state(); call()
        operations.append({'name':name,'payload':payload,'before':before,'after':c.semantic_state()})

    snapshot('full_initial_registry_and_graph')
    original=c.semantic_state(); root=c.checkpoint()
    assert c.states[0].status=='ready' and c.states[3].status=='waiting'
    transaction('scheduler-fixed-first-axiom',ax3.data(),lambda:e.step(ax3))
    snapshot('shared_exact_member_after_branch_action')
    assert c.states[0].status=='consumed' and c.states[1].status=='ready'
    assert c.states[2].status!='retired' and g.totals[3]==1
    transaction('scheduler-fixed-next-axiom',ax4.data(),lambda:e.step(ax4))
    snapshot('whole_uniqueness_family_retired_with_legal_siblings')
    assert c.states[1].status=='consumed' and c.states[2].status=='retired'
    assert any(g.legal(k) for k in c.descriptors[2].members if k not in g.selected)
    transaction('paired-full-parent-rollback',list(root),lambda:c.rollback(root))
    snapshot('full_parent_graph_and_hints_revived')
    assert c.semantic_state()==original and c.states[2].status!='retired'

    # A fixed literal MP reads the first two uniqueness member formulas remotely.
    # Its catalog-only placement occupies row21, and its source m-values create
    # global forced moves at3/4 without authored/exhaustion exclusions. It is not
    # an atomic cluster execution or an alternate proof-search scheduler.
    body=authority.body(family_name)
    primitive=body['primitive_members'][2]
    forced_remote=core.Key(g.recipe_index[primitive['recipe_id']],21,(3,4))
    assert g.recipes[forced_remote.recipe].inputs==(0,g.recipes[c.descriptors[2].members[1].recipe].output)
    root=c.checkpoint(); original=c.semantic_state()
    transaction('catalog-remote-mark-forced-control',forced_remote.data(),
                lambda:(g._apply_legal(forced_remote),c.resync()))
    snapshot('remote_marks_global_forced_before_hint_action')
    assert g.decision().kind=='forced' and g.decision().row==3
    assert c.states[2].status=='waiting'
    try:e.step(ax8)
    except ValueError:pass
    else:raise AssertionError('hint bypassed a distant forced point')
    transaction('scheduler-forced-shared-axiom',ax3.data(),lambda:e.step(ax3))
    snapshot('after_global_forced_shared_member')
    assert c.states[0].status=='consumed' and c.states[2].status!='retired'
    next_forced=next(g.candidates(g.decision().row))
    assert g.decision().kind=='forced' and g.decision().row==4
    transaction('scheduler-forced-instantiation',next_forced.data(),lambda:e.step(next_forced))
    snapshot('after_second_global_forced_family_member')
    assert c.states[2].status!='retired'
    transaction('paired-remote-forced-control-rollback',list(root),lambda:c.rollback(root))
    snapshot('remote_forced_parent_revived')
    assert c.semantic_state()==original

    # Same recipe/formula at the same row with different ordered references has
    # a different full identity. Low-level catalog transaction, no scheduler claim.
    assert g.recipes[distant.recipe].output==g.recipes[other.recipe].output
    identities.extend([identity_control(g,k,inventory) for k in (distant,other)])
    assert identities[-2]['id']!=identities[-1]['id']
    root=c.checkpoint(); original=c.semantic_state()
    transaction('catalog-same-output-different-identity',other.data(),
                lambda:(g._apply_legal(other),c.resync()))
    snapshot('whole_distant_cluster_retired_legal_axiom_sibling')
    assert c.states[4].status=='retired' and g.legal(ax4)
    transaction('paired-distant-catalog-rollback',list(root),lambda:c.rollback(root))
    snapshot('distant_hint_revived_exact_shared_state')
    assert c.semantic_state()==original

    # Source body substitution and omitted whole-authority metadata are rejected
    # before any point candidate can be preferred. These do not alter the graph.
    bad=copy.deepcopy(descriptors[2])
    # An entirely point-consistent alternate body of valid repeated axioms has
    # freshly recomputed full IDs/cache. It still cannot replace the registered
    # uniqueness body by changing its descriptor's primitive member array.
    malformed=tuple(core.Key(axiom,k.row) for k in c.descriptors[2].members)
    values=[g.decorate(k) for k in malformed]
    bad['members']=[k.data() for k in malformed]
    bad['full_member_ids']=[v['id'] for v in values]
    bad['full_identity_preimages']=[v['identity_preimage'] for v in values]
    t,m=life._union(g,malformed)
    bad['aggregate_t']=[list(x) for x in t];bad['aggregate_m']=[list(x) for x in m]
    bad['descriptor_id']='whole-cluster-'+core.digest({k:v for k,v in bad.items() if k!='descriptor_id'})
    rejected=[]
    try:authority.compile(g,bad)
    except (ValueError,KeyError,TypeError,IndexError):rejected.append('valid-primitive-altered-family-body')
    else:raise AssertionError('altered family body accepted')
    for field in ('model_epoch','context_id','authority_epoch','formula_registry_sha256'):
        bad=copy.deepcopy(descriptors[2]);bad['graph_binding'][field]='stale'
        try:authority.compile(g,bad)
        except (ValueError,KeyError,TypeError,IndexError):rejected.append('stale-'+field)
        else:raise AssertionError('stale descriptor accepted')
    snapshot('post_rejection_unchanged_complete_graph')
    if len(comparisons)>12:raise AssertionError('predeclared complete-state ceiling exceeded')
    if g.totals==[1]*24:raise AssertionError('controlled gate must not complete a proof region')
    for p in plan['sources']+plan['inputs']+plan['preserved_files']:
        if core.pin(ROOT/p['path'])!={k:p[k] for k in ('sha256','bytes')}:
            raise ValueError('final frozen pin mismatch')
    result={'status':'passed_authored_full_language_lifecycle_controls_pending_independent_audit',
            'comparisons':comparisons,'states':states,'controlled_operations':operations,
            'authority_registry':{'graph_binding':json.loads(authority.graph_text),
                'source_bindings':json.loads(authority.source_text),
                'bodies':[[n,json.loads(t)] for n,t in authority.bodies],'epoch':authority.epoch},
            'descriptors':descriptors,'rejected_corruptions':rejected,'identities':identities,
            'full_source_bodies':len(family.bodies),'complete_primitive_recipes':len(g.recipes),
            'formula_values':len(g.formulas),'required_rows':g.height,
            'controlled_states':len(comparisons),
            'all_state_candidate_key_t_m_comparisons':sum(v['candidate_nodes'] for v in comparisons),
            'graph_metrics':g.metrics,'lifecycle_metrics':c.metrics,
            'preparation_costs':{'family_registry_seconds':family_preparation_seconds,
                                 'root_descriptor_registry_and_controller_seconds':descriptor_preparation_seconds,
                                 'timers_are_within_this_process':True},
            'worker_seconds_before_receipt_write':time.perf_counter()-started,
            'actual_target_DFS_searches':0,'authored24_words_used_as_hints':0,'native_queries':0,
            'new_RL_training':False,'native_authority_activated':False,
            'scope':'controlled graph/hint transactions, not proof discovery or native/compiler correspondence'}
    path=HERE/'full-language-outcome-v1.json'
    if path.exists():raise ValueError('immutable actual outcome exists')
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('comparisons','states','controlled_operations','authority_registry','descriptors','identities')}),flush=True)

if __name__=='__main__':main()
