"""Prospective independent finite point/hint oracle; no execution at import.

This source deliberately does not import the producer or its implicit graph.
It uses explicitly enumerated, exact placement point data on tiny fixtures.
Source authority/epoch bindings are checked as data, not promoted to native
authority. A later exact adapter must bind producer records to this schema.
"""
import copy
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def integer(value):
    if type(value) is not int:
        raise ValueError("exact integer required")
    return value


def key(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("exact ordered primitive key required")
    recipe, row, refs = value
    integer(recipe); integer(row)
    if not isinstance(refs, (list, tuple)):
        raise ValueError("ordered references required")
    refs = tuple(integer(x) for x in refs)
    return recipe, row, refs


def points(entries, *, additive):
    out = {}
    for entry in entries:
        if not isinstance(entry, (list, tuple)) or len(entry) != 3:
            raise ValueError("point/value triple required")
        x, y, value = map(integer, entry)
        p = (x, y)
        if additive:
            if value <= 0:
                raise ValueError("positive unit occupancy required")
            out[p] = out.get(p, 0) + value
        else:
            if p in out and out[p] != value:
                raise ValueError("assigned marking conflict")
            out[p] = value
    return out


def compatible(a, b):
    # Explicit assigned zero participates; absence is determined by membership.
    return all(p not in b or b[p] == value for p, value in a.items())


class FiniteOracle:
    """Full-enumeration point model, independent of factorized domains/trails."""

    def __init__(self, required, roots, placements, initial_marks, binding, body_registry):
        self.required = tuple(tuple(map(integer, p)) for p in required)
        if len(set(self.required)) != len(self.required):
            raise ValueError("duplicate required point")
        self.roots = {tuple(map(integer, p)): integer(g) for p, g in roots}
        if set(self.roots) != set(self.required) or any(g < 0 for g in self.roots.values()):
            raise ValueError("complete root generations required")
        self.initial = points(initial_marks, additive=False)
        self.binding = copy.deepcopy(binding)
        # This registry must be independently reconstructed from pinned source
        # bodies by the future adapter. A descriptor's own hash is insufficient.
        self.body_registry = copy.deepcopy(body_registry)
        self.placements = {}
        self.order = []
        for placement in placements:
            k = key(placement["key"])
            if k in self.placements:
                raise ValueError("duplicate full candidate key")
            t = points(placement["t"], additive=True)
            m = points(placement["m"], additive=False)
            if t != {(0, k[1]): 1}:
                raise ValueError("this tiny oracle supports one unit row per placement")
            if not set(t) <= set(self.required):
                raise ValueError("fixture positive support outside finite boundary")
            self.placements[k] = {"t": t, "m": m, "identity": copy.deepcopy(placement["identity"])}
            self.order.append(k)

    def state(self, selected, excluded=()):
        selected = tuple(key(k) for k in selected)
        if len(set(selected)) != len(selected):
            raise ValueError("same primitive identity selected twice")
        total = {p: 0 for p in self.required}
        marks, refs, generations = dict(self.initial), {p: 1 for p in self.initial}, {}
        for k in selected:
            placement = self.placements[k]
            if not compatible(placement["m"], marks):
                raise ValueError("selected marking conflict")
            generation = 1 + min(self.roots[p] for p in placement["t"])
            generations[k] = generation
            for p, v in placement["t"].items():
                total[p] += v
                if total[p] > 1:
                    raise ValueError("selected occupancy overcount")
            for p, v in placement["m"].items():
                marks[p] = v
                refs[p] = refs.get(p, 0) + 1
        excluded = frozenset(key(k) for k in excluded)
        domains = {p: [] for p in self.required if total[p] < 1}
        for k in self.order:
            placement = self.placements[k]
            if k in selected or k in excluded:
                continue
            if not compatible(placement["m"], marks):
                continue
            if any(total[p] + v > 1 for p, v in placement["t"].items()):
                continue
            for p in placement["t"]:
                if p in domains:
                    domains[p].append(k)
        frontier = tuple(domains)
        if not frontier:
            decision = ("complete", None)
        elif any(not domains[p] for p in frontier):
            decision = ("dead", min(p for p in frontier if not domains[p]))
        elif any(len(domains[p]) == 1 for p in frontier):
            decision = ("forced", min(p for p in frontier if len(domains[p]) == 1))
        else:
            decision = ("branch", min(frontier, key=lambda p: (self.roots[p], len(domains[p]), p)))
        return {"selected": selected, "excluded": excluded, "total": total, "marks": marks,
                "mark_refs": refs, "generations": generations, "domains": domains, "decision": decision}

    def compile_descriptor(self, descriptor):
        if descriptor["binding"] != self.binding:
            raise ValueError("stale model/context/registry/authority/body binding")
        if descriptor["body_id"] not in self.body_registry:
            raise ValueError("unadmitted body identity")
        if descriptor["body"] != self.body_registry[descriptor["body_id"]]:
            raise ValueError("self-consistent hash cannot admit altered source body")
        if descriptor["body_sha256"] != sha(descriptor["body"]):
            raise ValueError("altered exact body")
        members = tuple(dict.fromkeys(key(k) for k in descriptor["members"]))
        if not members:
            raise ValueError("nonempty finite cluster required")
        identities = descriptor["identities"]
        if len(identities) != len(members):
            raise ValueError("missing complete primitive identities")
        total, marks = {}, {}
        for k, identity in zip(members, identities):
            placement = self.placements[k]
            if identity != placement["identity"]:
                raise ValueError("same formula is not full decorated identity")
            for p, v in placement["t"].items():
                total[p] = total.get(p, 0) + v
                if total[p] > 1:
                    raise ValueError("distinct constituents overfill")
            if not compatible(placement["m"], marks):
                raise ValueError("internal whole-cluster marking conflict")
            marks.update(placement["m"])
        return {"members": members, "total": total, "marks": marks}

    def hint_view(self, compiled, state):
        pending = tuple(k for k in compiled["members"] if k not in state["selected"])
        # Current graph exclusions participate in whole validity.
        current_keys = {k for domain in state["domains"].values() for k in domain}
        if any(k not in current_keys for k in pending):
            return {"status": "retired", "eligible": (), "pending": pending}
        if not compatible(compiled["marks"], state["marks"]):
            return {"status": "retired", "eligible": (), "pending": pending}
        addition = {}
        for k in pending:
            for p, v in self.placements[k]["t"].items():
                addition[p] = addition.get(p, 0) + v
        if any(state["total"][p] + v > 1 for p, v in addition.items()):
            return {"status": "retired", "eligible": (), "pending": pending}
        if not pending:
            return {"status": "consumed", "eligible": (), "pending": ()}
        kind, point = state["decision"]
        eligible = tuple(k for k in pending if kind == "branch" and k in state["domains"][point])
        return {"status": "ready" if eligible else "waiting", "eligible": eligible, "pending": pending}

    def ordered_domain(self, state, hints):
        kind, point = state["decision"]
        if kind not in ("branch", "forced"):
            return ()
        base = tuple(state["domains"][point])
        if kind == "forced":
            return base
        result = []
        for compiled in hints:
            view = self.hint_view(compiled, state)
            for k in view["eligible"]:
                if k not in result:
                    result.append(k)
        result.extend(k for k in base if k not in result)
        if len(result) != len(base) or set(result) != set(base):
            raise AssertionError("preferred plus fallback must be complete permutation")
        return tuple(result)


def parent_after_child(oracle, parent, attempted, status):
    """Semantic expected state after the child has been fully rolled back.

    This helper does not decide exhaustion. The future independent sequence
    adapter must establish the child's complete finite exhaustion separately.
    """
    if status == "exhausted_finite_marked_subtree":
        k = key(attempted)
        if not any(k in d for d in parent["domains"].values()):
            raise ValueError("child exclusion lacks exact legal parent context")
        return oracle.state(parent["selected"], tuple(parent["excluded"]) + (k,))
    if status in ("unknown_budget", "unknown_resource", "unknown_cancelled"):
        return oracle.state(parent["selected"], parent["excluded"])
    raise ValueError("only complete exhaustion can justify a parent exclusion")
