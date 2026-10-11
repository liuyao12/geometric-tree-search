"""Complete implicit point graph for the frozen primitive proof-row grammar.

This is authored host infrastructure. It neither activates a native authority nor
asserts native/compiler correspondence. Production loading requires exact frozen
source-model and independent finite logical-audit bytes. Synthetic fixtures are
explicitly a different, point-contract-only language.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

MARKING_VERSION = "injective-formula-ordered-mp-offset-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def integer(value):
    if type(value) is not int:
        raise ValueError("exact integer required; boolean is not an integer value")
    return value


def pin(path):
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            h.update(block)
    return {"sha256": h.hexdigest(), "bytes": path.stat().st_size}


def read_json(path):
    path = Path(path)
    with (gzip.open(path, "rt") if path.suffix == ".gz" else path.open()) as stream:
        return json.load(stream)


def set_bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask -= bit


@dataclass(frozen=True, order=True)
class Key:
    recipe: int
    row: int
    refs: tuple[int, ...] = ()

    def data(self):
        return [self.recipe, self.row, list(self.refs)]


@dataclass(frozen=True)
class Recipe:
    index: int
    identifier: str
    witness_text: str
    premise_texts: tuple[str, ...]
    output: int
    inputs: tuple[int, ...]

    @property
    def witness(self):
        return json.loads(self.witness_text)

    @property
    def formulas(self):
        return [json.loads(x) for x in self.premise_texts]


@dataclass(frozen=True)
class Factor:
    recipe: int
    left: int
    right: int
    different: bool
    count: int


@dataclass(frozen=True)
class Domain:
    factors: tuple[Factor, ...]
    base_count: int
    excluded_legal: tuple[Key, ...]
    count: int


@dataclass(frozen=True)
class Decision:
    kind: str
    row: int | None
    count: int
    generation: int | None


class PointGraph:
    """Unit occupancy, identity orientation and vertical translation only.

    Complete incidence is implicit: candidate (recipe,row,ordered refs) has one
    positive edge, to (0,row), with contribution one. The reverse dependency
    index is the exact parametric row relation below, not a display bound.
    """

    def __init__(self, *, height, formulas, recipe_data, context, authority,
                 fixed_marks=(), roots=None, seed_keys=(), fixture=False,
                 source_bindings=None):
        self.height = integer(height)
        if self.height < 1:
            raise ValueError("positive finite height required")
        self.fixture = fixture
        self.formulas = copy.deepcopy(formulas)
        codes = {canonical(f): i for i, f in enumerate(formulas)}
        if len(codes) != len(formulas):
            raise ValueError("formula values must be injective")
        self.registry_sha = digest(formulas)
        self.context = copy.deepcopy(context)
        self.context_id = digest(context)
        self.authority = copy.deepcopy(authority)
        if authority.get("activated") is not False or authority.get("native_accepted") is not False:
            raise ValueError("native authority is inactive in this infrastructure")
        self.authority_epoch = authority["epoch"]
        without_epoch = {k: v for k, v in authority.items() if k != "epoch"}
        if digest(without_epoch) != self.authority_epoch:
            raise ValueError("stale authority epoch")
        self.source_bindings = copy.deepcopy(source_bindings or {})
        self.recipes = []
        ids = set()
        for index, data in enumerate(recipe_data):
            witness, premises = data["primitive_witness"], data["ordered_premise_formulas"]
            rule = witness["rule"]
            if len(premises) not in (0, 2):
                raise ValueError("this frozen grammar has zero or two ordered ports")
            if len(premises) == 2:
                if rule == "mp":
                    if premises[1] != ["imp", premises[0], witness["formula"]]:
                        raise ValueError("point-consistent but logically invalid MP interface")
                elif not (fixture and rule == "opaque_pair"):
                    raise ValueError("only literal ordered MP has production input ports")
            elif rule == "mp" or rule not in ("axiom", "instantiate", "eq_subst", "assumption", "fixture_zero"):
                raise ValueError("invalid zero-port primitive")
            if rule == "fixture_zero" and not fixture:
                raise ValueError("fixture language cannot enter production inventory")
            if rule == "assumption":
                k = integer(witness["index"])
                hypotheses = context["ordered_local_premises"]
                if not 0 <= k < len(hypotheses) or hypotheses[k] != witness["formula"]:
                    raise ValueError("assumption is not an exact recipient hypothesis")
            identifier = data["id"]
            if identifier in ids:
                raise ValueError("duplicate recipe identity")
            ids.add(identifier)
            try:
                out = codes[canonical(witness["formula"])]
                inputs = tuple(codes[canonical(f)] for f in premises)
            except KeyError as error:
                raise ValueError("formula outside injective registry") from error
            self.recipes.append(Recipe(index, identifier, canonical(witness),
                                       tuple(map(canonical, premises)), out, inputs))
        self.recipes = tuple(self.recipes)
        self.recipe_index = {r.identifier: r.index for r in self.recipes}
        self.roots = tuple(0 for _ in range(height)) if roots is None else tuple(roots)
        if len(self.roots) != height or any(type(x) is not int or x < 0 for x in self.roots):
            raise ValueError("every required point has an explicit nonnegative root generation")
        self.initial_marks = {}
        for x, y, value in fixed_marks:
            point = (integer(x), integer(y)); integer(value)
            if point in self.initial_marks and self.initial_marks[point] != value:
                raise ValueError("inconsistent fixed marking")
            self.initial_marks[point] = value
        self.model_epoch = digest({"height": height, "context": context, "registry": self.registry_sha,
                                   "authority": self.authority_epoch, "recipes": [r.identifier for r in self.recipes],
                                   "fixed_marks": [[*p, v] for p, v in sorted(self.initial_marks.items())],
                                   "roots": self.roots, "seed_keys": [k.data() for k in seed_keys],
                                   "marking_version": MARKING_VERSION, "fixture": fixture,
                                   "source_bindings": self.source_bindings})
        self.totals = [0] * height
        self.marks = dict(self.initial_marks)
        self.mark_refs = {p: 1 for p in self.initial_marks}
        self.selected = {}  # Exact compact identities, with placed generations.
        self.order = []
        self.excluded = [set() for _ in range(height)]
        self.trail = []
        self.domains = [self._domain(row) for row in range(height)]
        self.metrics = {"domain_refreshes": height, "placements": 0, "forced": 0,
                        "branches": 0, "backtracks": 0, "attempts": 0,
                        "lazy_id_constructions": 0, "proposal_validations": 0,
                        "proposal_rejections": 0}
        for key in seed_keys:
            recipe = self._recipe_key(key)
            if recipe.witness["rule"] != "assumption":
                raise ValueError("fixed seeds are only declared recipient assumptions")
            self._apply_legal(key, generation=0)
        # Fixed initialization is not a branch transaction and cannot be undone.
        self.trail.clear()
        self.initial_selected = tuple(self.order)

    def _recipe_key(self, key):
        if not isinstance(key, Key) or type(key.recipe) is not int or type(key.row) is not int:
            raise ValueError("exact candidate key required")
        if not 0 <= key.recipe < len(self.recipes) or not 0 <= key.row < self.height:
            raise ValueError("candidate outside declared alignment domain")
        recipe = self.recipes[key.recipe]
        if len(key.refs) != len(recipe.inputs) or any(type(x) is not int or not 0 <= x < key.row for x in key.refs):
            raise ValueError("ordered references must all be strictly prior")
        return recipe

    def point_data(self, key):
        recipe = self._recipe_key(key)
        values = {(1, key.row): recipe.output}
        for port, (ref, code) in enumerate(zip(key.refs, recipe.inputs)):
            if (1, ref) in values and values[(1, ref)] != code:
                raise ValueError("inconsistent local marking function")
            values[(1, ref)] = code
            values[(2 + port, key.row)] = ref - key.row
        return ([[0, key.row, 1]], [[x, y, v] for (x, y), v in sorted(values.items())])

    def _compatible(self, point, value):
        return point not in self.marks or self.marks[point] == value

    def _input_mask(self, row, code, port):
        # All strict-prior source rows, including currently untouched rows.
        mask = 0
        for ref in range(row):
            if self._compatible((1, ref), code):
                mask |= 1 << ref
        point = (2 + port, row)
        if point in self.marks:
            ref = row + self.marks[point]
            mask &= (1 << ref) if 0 <= ref < row else 0
        return mask

    def _factors(self, row):
        if self.totals[row] == 1:
            return ()
        factors = []
        for recipe in self.recipes:
            if not self._compatible((1, row), recipe.output):
                continue
            if not recipe.inputs:
                factors.append(Factor(recipe.index, 0, 0, False, 1))
            else:
                left = self._input_mask(row, recipe.inputs[0], 0)
                right = self._input_mask(row, recipe.inputs[1], 1)
                different = recipe.inputs[0] != recipe.inputs[1]
                count = left.bit_count() * right.bit_count()
                if different:
                    count -= (left & right).bit_count()
                if count:
                    factors.append(Factor(recipe.index, left, right, different, count))
        return tuple(factors)

    def _base_legal_from_factors(self, key, factors):
        recipe = self._recipe_key(key)
        for f in factors:
            if f.recipe != key.recipe:
                continue
            if not recipe.inputs:
                return True
            a, b = key.refs
            return bool((f.left >> a) & 1 and (f.right >> b) & 1 and (not f.different or a != b))
        return False

    def _domain(self, row):
        factors = self._factors(row)
        removed = tuple(sorted(k for k in self.excluded[row]
                               if self._base_legal_from_factors(k, factors)))
        count = sum(f.count for f in factors)
        return Domain(factors, count, removed, count - len(removed))

    def _refresh(self, rows):
        for row in sorted(set(rows)):
            self.domains[row] = self._domain(row)
            self.metrics["domain_refreshes"] += 1

    def affected_rows(self, point):
        x, y = point
        if x == 0 and 0 <= y < self.height:
            return range(y, y + 1)
        if x == 1 and 0 <= y < self.height:
            # Formula marks constrain their own output and every later source reader.
            return range(y, self.height)
        if x in (2, 3) and 0 <= y < self.height:
            return range(y, y + 1)
        return ()

    def candidates(self, row):
        integer(row)
        if not 0 <= row < self.height:
            raise ValueError("point outside required domain")
        domain = self.domains[row]
        for factor in domain.factors:
            recipe = self.recipes[factor.recipe]
            if not recipe.inputs:
                key = Key(recipe.index, row)
                if key not in self.excluded[row]:
                    yield key
            else:
                for a in set_bits(factor.left):
                    for b in set_bits(factor.right):
                        if factor.different and a == b:
                            continue
                        key = Key(recipe.index, row, (a, b))
                        if key not in self.excluded[row]:
                            yield key

    def legal(self, key):
        try:
            self._recipe_key(key)
            return (key not in self.excluded[key.row]
                    and self._base_legal_from_factors(key, self.domains[key.row].factors))
        except (ValueError, IndexError, TypeError):
            return False

    def point_generation(self, row):
        gens = [self.roots[row]] + [g for k, g in self.selected.items() if k.row == row]
        return min(gens)

    def decision(self):
        frontier = [r for r, total in enumerate(self.totals) if total < 1]
        dead = [r for r in frontier if self.domains[r].count == 0]
        if dead:
            return Decision("dead", min(dead), 0, self.point_generation(min(dead)))
        forced = [r for r in frontier if self.domains[r].count == 1]
        if forced:
            row = min(forced)
            return Decision("forced", row, 1, self.point_generation(row))
        if not frontier:
            return Decision("complete", None, 0, None)
        row = min(frontier, key=lambda r: (self.point_generation(r), self.domains[r].count, r))
        return Decision("branch", row, self.domains[row].count, self.point_generation(row))

    def checkpoint(self):
        return len(self.trail)

    def _apply_legal(self, key, generation=None):
        # Catalog transaction checker only. Executor.step enforces the decision.
        if not self.legal(key) or key in self.selected:
            raise ValueError("candidate is not currently legal")
        _, marking = self.point_data(key)
        before = [(tuple((x, y)), self.marks.get((x, y)), self.mark_refs.get((x, y), 0))
                  for x, y, _ in marking]
        affected = {key.row}
        self.totals[key.row] += 1
        placed_generation = 1 + self.point_generation(key.row) if generation is None else integer(generation)
        self.selected[key] = placed_generation
        self.order.append(key)
        for x, y, value in marking:
            point = (x, y)
            if point in self.marks and self.marks[point] != value:
                raise AssertionError("implicit domain admitted incompatible marking")
            if point not in self.marks:
                self.marks[point] = value
                affected.update(self.affected_rows(point))
            self.mark_refs[point] = self.mark_refs.get(point, 0) + 1
        self.trail.append(("place", key, before, tuple(sorted(affected))))
        self._refresh(affected)
        self.metrics["placements"] += 1

    def exclude_failed_child(self, key):
        if not self.legal(key):
            raise ValueError("failed child exclusion requires exact restored parent context")
        self.excluded[key.row].add(key)
        self.trail.append(("exclude", key))
        self._refresh((key.row,))

    def rollback(self, checkpoint):
        integer(checkpoint)
        if not 0 <= checkpoint <= len(self.trail):
            raise ValueError("invalid checkpoint")
        affected = set()
        while len(self.trail) > checkpoint:
            entry = self.trail.pop()
            if entry[0] == "exclude":
                key = entry[1]
                self.excluded[key.row].remove(key)
                affected.add(key.row)
            else:
                _, key, before, rows = entry
                if self.order.pop() != key:
                    raise AssertionError("placement trail/order disagreement")
                del self.selected[key]
                self.totals[key.row] -= 1
                for point, value, refs in before:
                    if refs:
                        self.marks[point] = value
                        self.mark_refs[point] = refs
                    else:
                        del self.marks[point]
                        del self.mark_refs[point]
                affected.update(rows)
        self._refresh(affected)

    def semantic_state(self):
        # Metrics intentionally describe cumulative work and are not rolled back.
        return {"totals": list(self.totals), "marks": [[*p, v, self.mark_refs[p]] for p, v in sorted(self.marks.items())],
                "order": [k.data() for k in self.order],
                "selected_generations": [[k.data(), self.selected[k]] for k in sorted(self.selected)],
                "roots": list(self.roots), "excluded": [[k.data() for k in sorted(s)] for s in self.excluded],
                "domains": [{"factors": [[f.recipe, f.left, f.right, f.different, f.count] for f in d.factors],
                              "base_count": d.base_count, "excluded_legal": [k.data() for k in d.excluded_legal],
                              "count": d.count} for d in self.domains], "model_epoch": self.model_epoch}

    def decorate(self, key):
        recipe = self._recipe_key(key)
        t, m = self.point_data(key)
        command = recipe.witness
        if recipe.inputs and command["rule"] == "mp":
            command.update(antecedent=key.refs[0], implication=key.refs[1])
        elif recipe.inputs:  # Explicitly nonlogical synthetic fixture only.
            command["ordered_refs"] = list(key.refs)
        prototype = {"recipe_id": recipe.identifier, "primitive_witness": recipe.witness,
                     "ordered_premise_formulas": recipe.formulas,
                     "relative_ordered_input_offsets": [ref - key.row for ref in key.refs],
                     "orientation": "identity", "t": [[x, y - key.row, v] for x, y, v in t],
                     "m": [[x, y - key.row, v] for x, y, v in m], "marking_version": MARKING_VERSION,
                     "formula_registry_sha256": self.registry_sha, "authority_epoch": self.authority_epoch}
        preimage = {"prototype_id": "primitive-prototype-" + digest(prototype),
                    "prototype_preimage": prototype, "transform": [0, key.row],
                    "context_id": self.context_id, "ordered_input_rows": list(key.refs),
                    "primitive_command": command, "t": t, "m": m,
                    "authority_epoch": self.authority_epoch, "formula_registry_sha256": self.registry_sha}
        self.metrics["lazy_id_constructions"] += 1
        return {"id": "aggregate-primitive-" + digest(preimage), "identity_preimage": preimage,
                "key": key.data(), "command": command, "t": t, "m": m}

    def validate_cluster(self, keys, model_epoch):
        self.metrics["proposal_validations"] += 1
        if model_epoch != self.model_epoch:
            raise ValueError("stale cluster model/context/registry/authority")
        members = tuple(dict.fromkeys(keys))  # Exact shared placements once, ordered ports intact.
        total, marking = {}, {}
        for key in members:
            t, m = self.point_data(key)
            if key not in self.selected and not self.legal(key):
                raise ValueError("cluster constituent is not in complete legal base domain")
            for x, y, value in t:
                point = (x, y)
                total[point] = total.get(point, 0) + value
                if total[point] > 1:
                    raise ValueError("distinct cluster placements overfill positive support")
            for x, y, value in m:
                point = (x, y)
                if point in marking and marking[point] != value:
                    raise ValueError("cluster internally inconsistent marking")
                marking[point] = value
                if not self._compatible(point, value):
                    raise ValueError("cluster conflicts with remote current marking")
        return members

    def candidates_with_preferences(self, row, members=()):
        seen = set()
        for key in members:
            if key.row == row and key not in seen and self.legal(key):
                seen.add(key)
                yield key
        for key in self.candidates(row):
            if key not in seen:
                yield key

    def bind_template(self, template, ordered_input_rows, member_rows):
        """Explicit body-preserving family embedding; not a sampled degree catalog.

        Input aliases have no occupancy. Exact common primitive keys may share
        previously placed rows. This method proposes keys only, never executes.
        """
        inputs = template["canonical_input_rows"]
        members = template["primitive_members"]
        if len(inputs) != len(ordered_input_rows) or len(members) != len(member_rows):
            raise ValueError("complete ordered template binding required")
        if any(type(r) is not int or not 0 <= r < self.height for r in (*ordered_input_rows, *member_rows)):
            raise ValueError("template rows outside declared boundary")
        if any(a >= b for a, b in zip(member_rows, member_rows[1:])):
            raise ValueError("primitive source-body order must be preserved")
        mapping = dict(zip(inputs, ordered_input_rows))
        mapping.update((member["row"], row) for member, row in zip(members, member_rows))
        keys = []
        for member, row in zip(members, member_rows):
            recipe = self.recipe_index[member["recipe_id"]]
            refs = tuple(mapping[s] for s in member["ordered_inputs"])
            keys.append(Key(recipe, row, refs))
        bound = self.validate_cluster(keys, self.model_epoch)
        return {"definition": template["name"], "members": bound, "model_epoch": self.model_epoch,
                "ordered_input_rows": tuple(ordered_input_rows),
                "authority": "host_static_source_relation_only_not_native_accepted"}

    def point_certificate(self):
        if self.totals != [1] * self.height:
            raise ValueError("incomplete finite region")
        # Reconstruct exact union independently of incremental reference counts.
        total, marking = {}, dict(self.initial_marks)
        placements = []
        for key in sorted(self.selected, key=lambda k: k.row):
            placement = self.decorate(key)
            placements.append(placement)
            for x, y, value in placement["t"]:
                total[(x, y)] = total.get((x, y), 0) + value
            for x, y, value in placement["m"]:
                point = (x, y)
                if point in marking and marking[point] != value:
                    raise AssertionError("inconsistent reconstructed certificate")
                marking[point] = value
        if total != {(0, r): 1 for r in range(self.height)} or marking != self.marks:
            raise AssertionError("incremental/reconstructed point certificate mismatch")
        return {"status": "finite_exact_point_tiling_pending_independent_logical_certificate",
                "model_epoch": self.model_epoch, "source_bindings": self.source_bindings,
                "placements": placements, "native_accepted": False,
                "native_authority_activated": False, "compiler_correspondence": "open"}


class Executor:
    """Primitive scheduler, validated continuation hints and complete fallback."""

    def __init__(self, graph):
        self.graph = graph

    def step(self, key):
        decision = self.graph.decision()
        if decision.kind not in ("forced", "branch") or key.row != decision.row:
            raise ValueError("candidate cannot bypass global reference scheduler")
        if decision.kind == "forced" and next(self.graph.candidates(decision.row)) != key:
            raise ValueError("forced candidate mismatch")
        self.graph._apply_legal(key)
        self.graph.metrics["attempts"] += 1
        self.graph.metrics["forced" if decision.kind == "forced" else "branches"] += 1

    def solve(self, *, max_attempts, seconds, proposals=()):
        """Budget cutoffs are unknown; child exclusions are parent-local only.

        No production call is authorized until root's separate actual-model gate.
        The proposal list is an immutable preference set, not a proof seed.
        """
        deadline = time.perf_counter() + seconds
        start_attempts = self.graph.metrics["attempts"]
        initial = self.graph.checkpoint()
        try:
            preferences = self.graph.validate_cluster(proposals, self.graph.model_epoch) if proposals else ()
        except ValueError:
            self.graph.metrics["proposal_rejections"] += 1
            preferences = ()  # Invalid advice cannot remove the complete base fallback.

        def walk():
            checkpoint = self.graph.checkpoint()
            while True:
                # Dead/complete checks precede pause; a budget never means impossible.
                decision = self.graph.decision()
                if decision.kind == "dead":
                    self.graph.rollback(checkpoint)
                    return "exhausted_finite_marked_subtree"
                if decision.kind == "complete":
                    return "finite_exact_point_tiling"
                if self.graph.metrics["attempts"] - start_attempts >= max_attempts or time.perf_counter() >= deadline:
                    self.graph.rollback(checkpoint)
                    return "unknown_budget"
                candidate = next(self.graph.candidates_with_preferences(decision.row, preferences))
                if decision.kind == "forced":
                    self.step(candidate)
                    continue
                parent = self.graph.checkpoint()
                self.step(candidate)
                status = walk()
                if status == "finite_exact_point_tiling":
                    return status
                self.graph.rollback(parent)
                if status == "unknown_budget":
                    self.graph.rollback(checkpoint)
                    return status
                self.graph.metrics["backtracks"] += 1
                self.graph.exclude_failed_child(candidate)
                # Exclusion can change a distant global forced/dead decision.

        status = walk()
        if status != "finite_exact_point_tiling":
            self.graph.rollback(initial)
        return {"status": status, "attempts": self.graph.metrics["attempts"] - start_attempts,
                "certificate": self.graph.point_certificate() if status == "finite_exact_point_tiling" else None}


def frozen_model(root, plan):
    """Exact-byte finite source/audit authority gate; no native activation.

    This function constructs the actual graph, and must not be called before the
    distinct actual-model execution gate is reviewed by root.
    """
    root = Path(root)
    roles = {}
    for entry in plan["inputs"]:
        path = root / entry["path"]
        if pin(path) != {k: entry[k] for k in ("sha256", "bytes")}:
            raise ValueError("frozen input changed: " + entry["path"])
        roles[entry["role"]] = path
    data = read_json(roles["primitive_model"])
    audit = read_json(roles["primitive_logical_audit"])
    if audit["status"] != "passed_independent_finite_static_symbolic_and_aggregate_audit":
        raise ValueError("exact finite primitive logical audit not accepted")
    model_pin = next(e for e in plan["inputs"] if e["role"] == "primitive_model")
    audited_models = [e["current_pin"] for e in audit["independent_serialization_correspondence"]]
    if {k: model_pin[k] for k in ("path", "sha256", "bytes")} not in audited_models:
        raise ValueError("logical audit does not bind these exact primitive-model bytes")
    if digest(data["formula_codes"]) != data["formula_registry_sha256"]:
        raise ValueError("stale formula registry")
    authority = data["authority"]
    model = next(m for m in data["models"] if m["height"] == 24)
    if len(data["recipes"]) != 229 or len(data["formula_codes"]) != 217:
        raise ValueError("full frozen inventory required")
    if model["primitive_recipe_ids"] != [r["id"] for r in data["recipes"]]:
        raise ValueError("incomplete or reordered primitive inventory")
    if model["orientation"] != "identity" or model["context_id"] != digest(model["context"]):
        raise ValueError("orientation/context mismatch")
    if model["authority_epoch"] != authority["epoch"]:
        raise ValueError("authority mismatch")
    for recipe in data["recipes"]:
        expected = {"recipe": {"primitive_witness": recipe["primitive_witness"],
                               "ordered_premise_formulas": recipe["ordered_premise_formulas"]},
                    "primitive_authority_epoch": authority["epoch"],
                    "recipient_theory_sha256": authority["recipient_theory_sha256"],
                    "marking_version": MARKING_VERSION, "formula_registry_sha256": data["formula_registry_sha256"]}
        if recipe["primitive_witness"]["rule"] == "assumption":
            expected["local_context_id"] = model["context_id"]
        if recipe["identity_preimage"] != expected or recipe["id"] != "primitive-recipe-" + digest(expected):
            raise ValueError("stale recipe witness/interface identity")
    boundary = model["boundary"]
    if boundary["required"] != [[0, r] for r in range(24)] or boundary["root_generations"] != [[0, r, 0] for r in range(24)]:
        raise ValueError("all required root obligations must be explicit generation zero")
    if boundary["fixed_exterior_m"] != [[1, r, -1] for r in range(-23, 0)]:
        raise ValueError("full exterior formula sentinel required")
    indices = {r["id"]: i for i, r in enumerate(data["recipes"])}
    seeds = tuple(Key(indices[s["recipe_id"]], s["row"]) for s in boundary["fixed_initial_local_seeds"])
    if len(seeds) != 3 or sorted(k.row for k in seeds) != [0, 1, 2] or len(model["context"]["ordered_local_premises"]) != 3:
        raise ValueError("only exact three recipient hypothesis seeds are allowed")
    return PointGraph(height=24, formulas=data["formula_codes"], recipe_data=data["recipes"],
                      context=model["context"], authority=authority,
                      fixed_marks=boundary["fixed_exterior_m"] + boundary["fixed_target_m"],
                      seed_keys=seeds, source_bindings={e["role"]: {k: e[k] for k in ("path", "sha256", "bytes")}
                                                      for e in plan["inputs"]})
