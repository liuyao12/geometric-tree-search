"""Independent full point-state library, statically copied from our frozen prior audit.

No producer/engine imports, proof search, native checking or CLI dispatch.
Full-state domains are streamed from literal t/m translations, not factors.
"""
import copy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
MARKING="injective-formula-ordered-mp-offset-v1"
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


