"""Independent complete primitive-graph audit; execution needs root approval.

The kernel is only the implementation under test. Raw domains, state updates,
identities and logical command checks are independently reconstructed here.
No producer import, DFS, policy training, native query or compiler activation.
"""
import copy
import gzip
import hashlib
import importlib.util
import itertools
import json
import resource
import signal
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MARKING = "injective-formula-ordered-mp-offset-v1"


def need(condition, label):
    if not condition:
        raise ValueError(label)


def integer(value):
    need(type(value) is int, "exact integer; bool rejected")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def pin(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return dict(sha256=h.hexdigest(), bytes=Path(path).stat().st_size)


def read(path):
    with (gzip.open(path, "rt") if Path(path).suffix == ".gz" else Path(path).open()) as stream:
        return json.load(stream)


def imported(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def freeze_check(plan):
    for entry in plan["sources"] + plan["inputs"] + plan["preserved_files"]:
        need(pin(ROOT / entry["path"]) == {k: entry[k] for k in ("sha256", "bytes")},
             "frozen independent source/input: " + entry["path"])


def points(recipe, row, refs, height):
    integer(row)
    need(0 <= row < height and len(refs) == len(recipe["inputs"]), "key alignment/arity")
    marking = {(1, row): recipe["output"]}
    for port, (ref, code) in enumerate(zip(refs, recipe["inputs"])):
        integer(ref)
        need(0 <= ref < row, "strict ordered prior reference")
        need((1, ref) not in marking or marking[(1, ref)] == code, "local mark conflict")
        marking[(1, ref)] = code
        marking[(2 + port, row)] = ref - row
    return [[0, row, 1]], [[x, y, v] for (x, y), v in sorted(marking.items())]


class State:
    """Independent unit-capacity state; no production update/trail helpers."""
    def __init__(self, height, recipes, fixed, roots, epoch):
        self.height, self.recipes, self.roots, self.epoch = height, recipes, roots, epoch
        self.totals = [0] * height
        self.marks, self.refs, self.selected, self.order = {}, {}, {}, []
        self.excluded = [set() for _ in range(height)]
        for x, y, value in fixed:
            integer(x); integer(y); integer(value)
            p = (x, y)
            need(p not in self.marks or self.marks[p] == value, "fixed mark conflict")
            self.marks[p], self.refs[p] = value, 1

    def compatible(self, marking):
        return all((x, y) not in self.marks or self.marks[(x, y)] == value for x, y, value in marking)

    def apply(self, key, generation=None):
        recipe, row, refs = key
        integer(recipe)
        need(0 <= recipe < len(self.recipes) and key not in self.selected and key not in self.excluded[row],
             "distinct complete inventory key")
        t, m = points(self.recipes[recipe], row, refs, self.height)
        need(self.totals[row] + 1 <= 1 and self.compatible(m), "capacity/remote marking")
        gen = 1 + min([self.roots[row]] + [g for k, g in self.selected.items() if k[1] == row]) \
            if generation is None else integer(generation)
        self.totals[row] += 1
        self.selected[key] = gen
        self.order.append(key)
        for x, y, value in m:
            p = (x, y)
            self.marks[p] = value
            self.refs[p] = self.refs.get(p, 0) + 1

    def raw_candidates(self, row):
        """Every raw negative-offset prototype, tested solely by t/m data.

        Negative source rows are rejected by declared exterior formula marks,
        rather than a hidden semantic strict-prior shortcut in enumeration.
        """
        if self.totals[row] + 1 > 1:
            return
        for index, recipe in enumerate(self.recipes):
            if (1, row) in self.marks and self.marks[(1, row)] != recipe["output"]:
                continue
            raw = itertools.product(range(1 - self.height, 0), repeat=len(recipe["inputs"]))
            for offsets in raw:
                m = {(1, row): recipe["output"]}
                valid = True
                refs = tuple(row + offset for offset in offsets)
                for port, (ref, code, offset) in enumerate(zip(refs, recipe["inputs"], offsets)):
                    if (1, ref) in m and m[(1, ref)] != code:
                        valid = False
                        break
                    m[(1, ref)] = code
                    m[(2 + port, row)] = offset
                if not valid or any(p in self.marks and self.marks[p] != v for p, v in m.items()):
                    continue
                key = (index, row, refs)
                if key in self.excluded[row]:
                    continue
                # The full exterior domain must have eliminated every negative ref.
                need(all(0 <= r < row for r in refs), "exterior reduction to strict prior failed")
                yield key, [[0, row, 1]], [[x, y, v] for (x, y), v in sorted(m.items())]

    def semantic(self):
        # Factor representation is reconstructed for state equality only. Domain
        # completeness/count authority comes from raw_candidates, not this count.
        domains = []
        for row in range(self.height):
            factors = []
            if not self.totals[row]:
                for index, recipe in enumerate(self.recipes):
                    if (1, row) in self.marks and self.marks[(1, row)] != recipe["output"]:
                        continue
                    if not recipe["inputs"]:
                        factors.append([index, 0, 0, False, 1])
                        continue
                    permitted = []
                    for port, code in enumerate(recipe["inputs"]):
                        options = [r for r in range(row)
                                   if ((1, r) not in self.marks or self.marks[(1, r)] == code)
                                   and ((2 + port, row) not in self.marks or self.marks[(2 + port, row)] == r - row)]
                        permitted.append(options)
                    different = recipe["inputs"][0] != recipe["inputs"][1]
                    count = sum(1 for a in permitted[0] for b in permitted[1] if not different or a != b)
                    if count:
                        factors.append([index, sum(1 << r for r in permitted[0]),
                                        sum(1 << r for r in permitted[1]), different, count])
            count = sum(f[4] for f in factors)
            need(not self.excluded[row], "this actual recorded control has no child exclusions")
            domains.append(dict(factors=factors, base_count=count, excluded_legal=[], count=count))
        kd = lambda key: [key[0], key[1], list(key[2])]
        return dict(totals=self.totals, marks=[[x, y, v, self.refs[(x, y)]] for (x, y), v in sorted(self.marks.items())],
                    order=[kd(k) for k in self.order], selected_generations=[[kd(k), self.selected[k]] for k in sorted(self.selected)],
                    roots=self.roots, excluded=[[] for _ in range(self.height)], domains=domains, model_epoch=self.epoch)


def decorate(key, t, m, inventory, context, authority, registry):
    index, row, refs = key
    recipe = inventory[index]
    witness = recipe["witness"]
    command = copy.deepcopy(witness)
    if refs:
        need(command["rule"] == "mp", "production ordered ports require MP")
        command.update(antecedent=refs[0], implication=refs[1])
    proto = dict(recipe_id=recipe["id"], primitive_witness=witness,
                 ordered_premise_formulas=recipe["premises"],
                 relative_ordered_input_offsets=[r - row for r in refs], orientation="identity",
                 t=[[x, y - row, v] for x, y, v in t], m=[[x, y - row, v] for x, y, v in m],
                 marking_version=MARKING, formula_registry_sha256=registry, authority_epoch=authority)
    preimage = dict(prototype_id="primitive-prototype-" + digest(proto), prototype_preimage=proto,
                    transform=[0, row], context_id=digest(context), ordered_input_rows=list(refs),
                    primitive_command=command, t=t, m=m, authority_epoch=authority, formula_registry_sha256=registry)
    return dict(id="aggregate-primitive-" + digest(preimage), identity_preimage=preimage,
                key=[index, row, list(refs)], command=command, t=t, m=m)


def validate_model(data, symbolic):
    formulas, recipes = data["formula_codes"], data["recipes"]
    need(len(formulas) == 217 and len(recipes) == 229, "complete frozen primitive inventory")
    registry = digest(formulas)
    need(registry == data["formula_registry_sha256"], "registry binding")
    codes = {canonical(f): i for i, f in enumerate(formulas)}
    need(len(codes) == len(formulas), "formula injectivity")
    authority = data["authority"]
    need(authority["activated"] is False and authority["native_accepted"] is False, "inactive native authority")
    need(authority["epoch"] == digest({k: v for k, v in authority.items() if k != "epoch"}), "authority epoch")
    model = next(m for m in data["models"] if m["height"] == 24)
    context = model["context"]
    checker = symbolic.SymbolicChecker(context["theory"])
    for formula in formulas:
        checker.formula(formula, closed=True)
    need(len(context["ordered_local_premises"]) == 3, "only global recipient context")
    for formula in context["ordered_local_premises"]:
        checker.formula(formula, closed=True)
    need(model["context_id"] == digest(context) and model["authority_epoch"] == authority["epoch"], "context/authority binding")
    need(authority["recipient_theory_sha256"] == digest(context["theory"]), "recipient theory hash")
    need(model["orientation"] == "identity" and model["transform_grammar"] == "vertical integer translation only", "transformation grammar")
    need(model["mp_offset_domain"] == [-23, -1] and model["positive_support_alignment_domain"] == [0, 23], "complete alignment grammar")
    need(model["primitive_recipe_ids"] == [r["id"] for r in recipes], "exact recipe order")
    inventory, identifiers, counts = [], set(), {}
    for i, r in enumerate(recipes):
        witness, premises = r["primitive_witness"], r["ordered_premise_formulas"]
        for formula in premises:
            checker.formula(formula, closed=True)
        expected = dict(recipe=dict(primitive_witness=witness, ordered_premise_formulas=premises),
                        primitive_authority_epoch=authority["epoch"], recipient_theory_sha256=digest(context["theory"]),
                        marking_version=MARKING, formula_registry_sha256=registry)
        if witness["rule"] == "assumption":
            expected["local_context_id"] = digest(context)
        need(r["identity_preimage"] == expected and r["id"] == "primitive-recipe-" + digest(expected)
             and r["id"] not in identifiers, "full recipe identity")
        identifiers.add(r["id"])
        command = copy.deepcopy(witness)
        if witness["rule"] == "mp":
            need(len(premises) == 2, "complete ordered MP ports")
            command.update(antecedent=0, implication=1)
            checker.command(command, premises, context["ordered_local_premises"])
        else:
            need(premises == [] and witness["rule"] in ("axiom", "instantiate", "eq_subst", "assumption"), "zero-port primitive rule")
            checker.command(command, [], context["ordered_local_premises"])
        inventory.append(dict(id=r["id"], witness=witness, premises=premises,
                              output=codes[canonical(witness["formula"])], inputs=tuple(codes[canonical(f)] for f in premises)))
        counts[witness["rule"]] = counts.get(witness["rule"], 0) + 1
    boundary = model["boundary"]
    for triple in boundary["root_generations"] + boundary["fixed_target_m"] + boundary["fixed_exterior_m"]:
        need(len(triple) == 3, "exact boundary triple")
        for value in triple:
            integer(value)
    for pair in boundary["required"]:
        need(len(pair) == 2, "exact required point")
        for value in pair:
            integer(value)
    need(boundary["required"] == [[0, r] for r in range(24)]
         and boundary["root_generations"] == [[0, r, 0] for r in range(24)]
         and boundary["fixed_exterior_m"] == [[1, r, -1] for r in range(-23, 0)], "exact complete roots/exterior")
    target = boundary["fixed_target_m"]
    need(len(target) == 1 and target[0][:2] == [1, 23] and 0 <= target[0][2] < len(formulas), "fixed target formula code")
    ids = {r["id"]: i for i, r in enumerate(inventory)}
    seeds = []
    for seed in boundary["fixed_initial_local_seeds"]:
        integer(seed["row"]); integer(seed["generation"])
        idx = ids[seed["recipe_id"]]
        w = inventory[idx]["witness"]
        need(w["rule"] == "assumption" and seed["generation"] == 0 and w["index"] == seed["row"], "ordered seed occurrence")
        seeds.append((idx, seed["row"], ()))
    need(sorted(k[1] for k in seeds) == [0, 1, 2] and counts.get("assumption") == 3, "only three recipient seeds")
    mp = [r for r in inventory if r["inputs"]]
    zero = len(inventory) - len(mp)
    raw = 24 * (zero + len(mp) * 23 ** 2)
    strict = zero * 24 + len(mp) * sum(r * r for r in range(24))
    conflict = sum(r["inputs"][0] != r["inputs"][1] for r in mp) * sum(range(24))
    need(model["counts"]["raw_positive_support_alignments"] == raw
         and model["counts"]["locally_consistent_strict_prior_bindings"] == strict - conflict, "complete finite grammar census")
    return model, inventory, checker, seeds, counts


def compare(graph, state, inventory, recorded, representatives=None):
    """Stream every original candidate once; never materialize a candidate set."""
    need(graph.semantic_state() == state.semantic(), "complete independent state/refcount/domain equality")
    rows = []
    for row in range(24):
        count, byrecipe, checksum = 0, [0] * len(inventory), hashlib.sha256()
        sentinel = object()
        for got, raw in itertools.zip_longest(graph.candidates(row), state.raw_candidates(row), fillvalue=sentinel):
            need(got is not sentinel and raw is not sentinel, "complete iterator length")
            key, t, m = raw
            need((got.recipe, got.row, got.refs) == key and graph.point_data(got) == (t, m), "complete exact key/t/m comparison")
            checksum.update((canonical([[key[0], row, list(key[2])], t, m]) + "\n").encode())
            byrecipe[key[0]] += 1
            count += 1
            if representatives is not None:
                representatives.setdefault((key[0], "first"), (key, t, m))
                representatives[(key[0], "last")] = (key, t, m)
        need(count == graph.domains[row].count, "complete count/zero/singleton")
        rows.append(dict(row=row, frontier=state.totals[row] < 1, degree=count,
                         per_recipe_degree=byrecipe, complete_key_t_m_stream_sha256=checksum.hexdigest()))
    answer = dict(label=recorded["label"], rows=rows, candidate_nodes=sum(r["degree"] for r in rows),
                  incidence_edges=sum(r["degree"] for r in rows), frontier_points=sum(r["frontier"] for r in rows),
                  candidate_node_incidence_reason="each primitive placement has exactly one unit positive-support edge")
    need(answer == recorded, "entire recorded full-domain census/digests")
    return answer


def decision(state, comparison):
    frontier = [r for r in comparison["rows"] if r["frontier"]]
    if not frontier:
        return dict(kind="complete", row=None, count=0, generation=None)
    dead = [r for r in frontier if r["degree"] == 0]
    forced = [r for r in frontier if r["degree"] == 1]
    if dead or forced:
        chosen = min(dead or forced, key=lambda r: r["row"])
        kind = "dead" if dead else "forced"
    else:
        chosen = min(frontier, key=lambda r: (min([state.roots[r["row"]]] +
                     [g for k, g in state.selected.items() if k[1] == r["row"]]), r["degree"], r["row"]))
        kind = "branch"
    row = chosen["row"]
    generation = min([state.roots[row]] + [g for k, g in state.selected.items() if k[1] == row])
    return dict(kind=kind, row=row, count=chosen["degree"], generation=generation)


def check_identity(core, graph, state, key, inventory, recorded=None):
    t, m = points(inventory[key[0]], key[1], key[2], state.height)
    expected = decorate(key, t, m, inventory, graph.context, graph.authority_epoch, graph.registry_sha)
    actual = graph.decorate(core.Key(*key))
    need(actual == expected, "lazy full identity/command/t/m preimage")
    receipt = dict(key=expected["key"], id=expected["id"], preimage_sha256=digest(expected["identity_preimage"]))
    if recorded is not None:
        need(receipt == recorded, "recorded lazy full identity")
    return receipt


def reject(action, label):
    try:
        action()
    except Exception as exc:
        if isinstance(exc, (ValueError, TypeError, IndexError, KeyError)) or type(exc).__name__ == "Rejected":
            return dict(name=label, rejected=True, rejection_type=type(exc).__name__)
        raise
    raise ValueError("corruption accepted: " + label)


def whole_control(data, model, inventory, checker, seeds, state, core, source_bindings, recorded):
    """Authored word loaded only after all generic domain/scheduler probes."""
    placements = data["placements"]
    need(len(placements) == 24 and [p["row"] for p in placements] == list(range(24)), "whole authored row order")
    commands, rebuilt, ids = [], [], []
    initial = copy.deepcopy(state)
    graph = core.PointGraph(height=24, formulas=state.formulas, recipe_data=state.recipe_data,
            context=model["context"], authority=state.authority, fixed_marks=state.fixed,
            seed_keys=tuple(core.Key(*k) for k in seeds), source_bindings=source_bindings)
    byid = {r["id"]: i for i, r in enumerate(inventory)}
    for row, p in enumerate(placements):
        refs = tuple(p["ordered_inputs"])
        key = (byid[p["recipe_id"]], row, refs)
        t, m = points(inventory[key[0]], row, refs, 24)
        expected = decorate(key, t, m, inventory, model["context"], state.authority["epoch"], digest(state.formulas))
        need(all(p[field] == expected[field] for field in ("id", "identity_preimage", "command", "t", "m")), "authored decorated placement equality")
        need(graph.decorate(core.Key(*key)) == expected, "authored kernel identity")
        checker.command(expected["command"], [c["formula"] for c in commands], model["context"]["ordered_local_premises"])
        commands.append(expected["command"])
        if key not in initial.selected:
            initial.apply(key)
            graph._apply_legal(core.Key(*key))
        else:
            need(row in (0, 1, 2), "only exact seeds may be already present")
        rebuilt.append(expected); ids.append(expected["id"])
    target = state.formulas[model["boundary"]["fixed_target_m"][0][2]]
    checker.proof(commands, model["context"]["ordered_local_premises"], target)
    need(initial.totals == [1] * 24, "whole exact t occupancy")
    need(graph.semantic_state() == initial.semantic(), "whole exact point/refcount/domain state")
    certificate = dict(status="finite_exact_point_tiling_pending_independent_logical_certificate",
                       model_epoch=state.epoch, source_bindings=source_bindings, placements=rebuilt,
                       native_accepted=False, native_authority_activated=False, compiler_correspondence="open")
    need(graph.point_certificate() == certificate, "whole original point certificate reconstruction")
    need(digest(certificate) == recorded["point_certificate_sha256"] and digest(ids) == recorded["full_id_stream_sha256"], "original whole certificate/ID bindings")
    # Each corruption is an actual fresh checked object, without changing old data.
    mutations = []
    mp_row = next(i for i, c in enumerate(commands) if c["rule"] == "mp")
    bad = copy.deepcopy(commands); bad[mp_row]["antecedent"], bad[mp_row]["implication"] = bad[mp_row]["implication"], bad[mp_row]["antecedent"]
    mutations.append(reject(lambda: checker.proof(bad, model["context"]["ordered_local_premises"], target), "swapped_ordered_MP_references"))
    bad = copy.deepcopy(commands); bad[mp_row]["antecedent"] = mp_row
    mutations.append(reject(lambda: checker.proof(bad, model["context"]["ordered_local_premises"], target), "forward_MP_reference"))
    bad = copy.deepcopy(commands); bad[mp_row]["formula"] = commands[mp_row]["formula"] if commands[mp_row]["formula"] != target else commands[0]["formula"]
    # Select a distinct registered conclusion for a point-consistent but invalid MP.
    wrong = next(f for f in state.formulas if f != commands[mp_row]["formula"])
    bad[mp_row]["formula"] = wrong
    wrong_recipe = copy.deepcopy(inventory[byid[placements[mp_row]["recipe_id"]]])
    wrong_recipe["witness"] = copy.deepcopy(bad[mp_row])
    wrong_recipe["output"] = state.formulas.index(wrong)
    wrong_t, wrong_m = points(wrong_recipe, mp_row, tuple(placements[mp_row]["ordered_inputs"]), 24)
    need(wrong_t == [[0, mp_row, 1]] and len({(x, y) for x, y, _ in wrong_m}) == len(wrong_m),
         "invalid logical command still has a locally consistent marking function")
    rejected = reject(lambda: checker.command(bad[mp_row], [c["formula"] for c in commands[:mp_row]], model["context"]["ordered_local_premises"]), "point_consistent_invalid_MP_conclusion")
    rejected.update(locally_consistent_point_shape_only=True, mutated_t=wrong_t, mutated_m=wrong_m)
    mutations.append(rejected)
    p = rebuilt[mp_row]
    # False IDs/authority/registry and offset claims are independently rejected by exact full identity comparison.
    for label, mutate in (
        ("stale_authority", lambda p: p["identity_preimage"].update(authority_epoch="corrupt")),
        ("stale_registry", lambda p: p["identity_preimage"].update(formula_registry_sha256="corrupt")),
        ("wrong_ordered_port_offset", lambda p: p["m"].append([2, mp_row, 0])),
        ("false_shared_identity", lambda p: p.update(id=rebuilt[0]["id"]))):
        altered = copy.deepcopy(p); mutate(altered)
        mutations.append(reject(lambda altered=altered: need(altered == p, "altered decorated object"), label))
    repeated = copy.deepcopy(initial)
    mutations.append(reject(lambda: repeated.apply((byid[placements[0]["recipe_id"]], 0, ())), "shared_placement_t_overcount"))
    altered_context = copy.deepcopy(model["context"]["ordered_local_premises"])
    altered_context[0], altered_context[1] = altered_context[1], altered_context[0]
    mutations.append(reject(lambda: checker.proof(commands, altered_context, target), "ordered_seed_alias_mismatch"))
    return dict(rows=24, commands_sha256=digest(commands), point_certificate_sha256=digest(certificate),
                full_id_stream_sha256=digest(ids), target=target, every_command_independently_checked=True,
                fresh_native_acceptance=False, discovery="authored catalog control only", mutations=mutations)


def run(plan):
    freeze_check(plan)
    roles = {entry["role"]: ROOT / entry["path"] for entry in plan["inputs"]}
    producer_plan = read(roles["producer_plan"])
    recorded = read(roles["producer_outcome"])
    life = read(roles["producer_lifetime"])
    need(recorded["status"] == "passed_authored_full_primitive_point_graph_controls_pending_independent_audit", "terminal actual producer")
    need(recorded["plan_sha256"] == pin(roles["producer_plan"])["sha256"], "producer plan binding")
    supervision = read(roles["producer_supervision"])
    need(life["status"] == "passed_authored_full_primitive_graph_full_lifetime"
         and life["plan_sha256"] == pin(roles["producer_plan"])["sha256"]
         and life["supervision_sha256"] == pin(roles["producer_supervision"])["sha256"]
         and life["process_return_code"] == 0 and life["supervisor_wait_reaped"]
         and life["full_supervisor_process_seconds_including_receipt_write"] <= 180
         and life["conservative_host_peak_bytes"] <= 536870912,
         "producer owned lifetime")
    need(supervision["status"] == "passed_bounded_authored_full_primitive_point_graph_controls"
         and supervision["exit_code"] == 0 and supervision["owned_child_terminal_wait_reaped"]
         and supervision["resource_reason"] is None and supervision["watchdog_error"] is None
         and supervision["plan_sha256"] == pin(roles["producer_plan"])["sha256"],
         "producer supervision/reaped child")
    data = read(roles["primitive_model"])
    symbolic = imported(roles["independent_symbolic_checker"], "new_full_graph_symbolic_checker")
    model, inventory, checker, seeds, rules = validate_model(data, symbolic)
    audit = read(roles["primitive_logical_audit"])
    need(audit["status"] == "passed_independent_finite_static_symbolic_and_aggregate_audit", "prior independent logical gate")
    prior_life = read(roles["primitive_logical_audit_lifetime"])
    need(prior_life["status"] == "passed_full_lifetime_static_audit_gate"
         and prior_life["child_terminal_reaped"] and prior_life["child_exit_code"] == 0
         and prior_life["failure"] is None and prior_life["conservative_sum_peak_rss_bytes"] <= 536870912
         and dict(path=str(roles["primitive_logical_audit"].relative_to(ROOT)), **pin(roles["primitive_logical_audit"])) in prior_life["output_bindings"],
         "prior independent full-lifetime/logical-output binding")
    model_pin = dict(path=str(roles["primitive_model"].relative_to(ROOT)), **pin(roles["primitive_model"]))
    need(model_pin in [e["current_pin"] for e in audit["independent_serialization_correspondence"]], "prior exact model closure")
    source_bindings = {e["role"]: {k: e[k] for k in ("path", "sha256", "bytes")} for e in producer_plan["inputs"]}
    need(recorded["source_bindings"] == source_bindings, "original exact source bindings")
    fixed = model["boundary"]["fixed_exterior_m"] + model["boundary"]["fixed_target_m"]
    epoch = digest(dict(height=24, context=model["context"], registry=digest(data["formula_codes"]), authority=data["authority"]["epoch"],
                        recipes=[r["id"] for r in inventory], fixed_marks=sorted(fixed), roots=[0] * 24,
                        seed_keys=[[i, row, []] for i, row, _ in seeds], marking_version=MARKING, fixture=False, source_bindings=source_bindings))
    need(epoch == recorded["model_epoch"], "independent model epoch")
    state = State(24, inventory, fixed, [0] * 24, epoch)
    for key in seeds:
        state.apply(key, generation=0)
    initial = copy.deepcopy(state)
    core = imported(roles["kernel_under_test"], "new_full_graph_kernel_under_test")
    graph = core.PointGraph(height=24, formulas=data["formula_codes"], recipe_data=data["recipes"], context=model["context"], authority=data["authority"],
                            fixed_marks=fixed, seed_keys=tuple(core.Key(*k) for k in seeds), source_bindings=source_bindings)
    need(digest(state.semantic()) == recorded["initial_semantic_state_sha256"], "independent initial full state digest")
    comparisons, representatives, identities = [], {}, []
    checkpoint = graph.checkpoint()
    comparisons.append(compare(graph, state, inventory, recorded["complete_comparisons"][0], representatives))
    for _, (key, t, m) in sorted(representatives.items()):
        identities.append(check_identity(core, graph, state, key, inventory, recorded["lazy_identity_checks"][len(identities)]))
    prefix = []
    for index in range(8):
        expected_decision = decision(state, comparisons[-1])
        got = graph.decision()
        need(dict(kind=got.kind, row=got.row, count=got.count, generation=got.generation) == expected_decision, "full reference scheduler")
        need(expected_decision["kind"] in ("branch", "forced"), "generic prefix must stop before dead/complete")
        key = next(state.raw_candidates(expected_decision["row"]))[0]
        identities.append(check_identity(core, graph, state, key, inventory, recorded["lazy_identity_checks"][len(identities)]))
        core.Executor(graph).step(core.Key(*key))
        state.apply(key)
        prefix.append(dict(key=[key[0], key[1], list(key[2])], decision=expected_decision))
        comparisons.append(compare(graph, state, inventory, recorded["complete_comparisons"][index + 1]))
    need(prefix == recorded["generic_prefix"] and state.totals != [1] * 24, "generic eight prefix exact/nonproof")
    graph.rollback(checkpoint); state = copy.deepcopy(initial)
    comparisons.append(compare(graph, state, inventory, recorded["complete_comparisons"][9]))
    mp = next(k for row in reversed(range(24)) for k, _, _ in state.raw_candidates(row) if inventory[k[0]]["inputs"])
    need([mp[0], mp[1], list(mp[2])] == recorded["catalog_only_probes"]["remote_mp_key"], "complete catalog MP selection")
    axiom = next(i for i, r in enumerate(inventory) if r["witness"]["rule"] == "axiom")
    zero = (axiom, 3, ())
    need(inventory[axiom]["output"] == 0 and [axiom, 3, []] == recorded["catalog_only_probes"]["formula_zero_key"], "assigned zero catalog selection")
    for key, transaction_index, rollback_index in ((mp, 10, 11), (zero, 12, 13)):
        identities.append(check_identity(core, graph, state, key, inventory, recorded["lazy_identity_checks"][len(identities)]))
        graph._apply_legal(core.Key(*key)); state.apply(key)
        comparisons.append(compare(graph, state, inventory, recorded["complete_comparisons"][transaction_index]))
        graph.rollback(checkpoint); state = copy.deepcopy(initial)
        comparisons.append(compare(graph, state, inventory, recorded["complete_comparisons"][rollback_index]))
    need(identities == recorded["lazy_identity_checks"] and len(identities) == 468, "all original identity checks")
    # These attributes are audit convenience only, not identity or state data.
    state.formulas, state.recipe_data, state.authority, state.fixed = data["formula_codes"], data["recipes"], data["authority"], fixed
    witness = read(roles["authored_witness_control"])
    whole = whole_control(witness, model, inventory, checker, seeds, state, core, source_bindings, recorded["authored_witness_control"])
    freeze_check(plan)
    return dict(status="passed_independent_full_primitive_graph_state_identity_and_authored_logical_word_audit",
                producer_outcome_sha256=pin(roles["producer_outcome"])["sha256"], model_epoch=epoch,
                inventory=dict(recipes=229, formula_codes=217, prior_named_definitions=171, independently_checked_rule_counts=rules),
                complete_comparisons=comparisons, complete_state_count=len(comparisons),
                every_candidate_comparisons=sum(c["candidate_nodes"] for c in comparisons),
                exact_zero_singleton_and_full_incidence_counts_checked=True, full_initial_state_sha256=digest(initial.semantic()),
                lazy_identities=identities, generic_prefix=prefix, authored_word=whole,
                scope="Exact frozen guarded Hilbert-incidence fragment, 24-row primitive point grammar and fourteen recorded finite states. Generic eight branch prefix has no proof-search claim; remote MP and assigned-zero are separate catalog probes. Full complete candidate iteration checked against independent raw t/m translations; every primitive recipe and authored word separately checked logically.",
                limitations=["Finite controls do not prove every possible execution state; prior independent tiny controls cover global dead/forced/generation adversaries and exclusions.",
                             "Frozen v2 fixed preference-set lifecycle gap remains; no full cluster-continuation conformance.",
                             "Authored24 word is a verification control, not a newly searched proof or RL outcome.",
                             "Host symbolic logic and exact point acceptance; native/compiler/Wang correspondence remains open.",
                             "No proof search, no subtree exhaustion, no learned hint or authority activation."],
                target_searches=0, native_queries=0, training_episodes=0, compiler_activations=0)


def main():
    began = time.perf_counter()
    planpath = HERE / "geometry-full-independent-plan-v1.json"
    plan = read(planpath)
    output = ROOT / plan["result_path"]
    need(not output.exists(), "immutable audit output")
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("independent full graph internal lifetime")))
    signal.setitimer(signal.ITIMER_REAL, plan["child_seconds"])
    result = dict(status="failed_or_unknown_independent_full_graph_audit")
    try:
        result = run(plan)
    except Exception as exc:
        result.update(failure_type=type(exc).__name__, failure=str(exc))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
        result.update(plan_sha256=pin(planpath)["sha256"], child_seconds_before_receipt_write=time.perf_counter() - began,
                      child_kernel_peak_bytes=peak, source_authoring_wall_time="uninstrumented; not zero")
        if result["child_seconds_before_receipt_write"] > plan["child_seconds"] or peak > plan["peak_bytes"]:
            result["status"] = "unknown_independent_full_graph_resource_budget"
        with output.open("x") as stream:
            json.dump(result, stream, indent=2); stream.write("\n")
        print(json.dumps({k: result[k] for k in ("status", "child_seconds_before_receipt_write", "child_kernel_peak_bytes")}), flush=True)


if __name__ == "__main__":
    main()
