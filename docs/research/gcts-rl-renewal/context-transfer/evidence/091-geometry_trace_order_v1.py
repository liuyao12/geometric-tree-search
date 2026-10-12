"""Independent declared fixed ordering; no producer ForwardOrder import."""
import hashlib
from full_point_oracle_v1 import canonical, need
from geometry_trace_point_v1 import key_data


def ast_size(value):
    if type(value) is not list:
        return 0
    tag = value[0]
    if tag in ("var", "bot"):
        return 1
    if tag in ("fun", "pred"):
        return 1 + sum(ast_size(v) for v in value[2])
    if tag == "all":
        return 1 + ast_size(value[2])
    return 1 + sum(ast_size(v) for v in value[1:])


def stream_sha(keys):
    h = hashlib.sha256()
    for k in keys:
        h.update((canonical(key_data(k)) + "\n").encode())
    if not keys:
        h.update(b"\n")
    return h.hexdigest()


def ordered_keys(state, formulas, choice, mode):
    keys = list(state.candidates(choice[1]))
    need(len(keys) == choice[2] and len(set(keys)) == len(keys), "complete ordered point domain")
    if mode == "base" or choice[0] == "forced":
        return keys, keys
    need(mode == "fixed-forward" and choice[0] == "branch", "declared order mode")
    index = {canonical(f): i for i, f in enumerate(formulas)}
    proved = {state.recipes[k[0]]["output"] for k in state.selected}
    selected_rows = {k[1] for k in state.selected}
    def score(k):
        recipe = state.recipes[k[0]]; w = recipe["witness"]
        universal = index.get(canonical(w["universal"])) if w["rule"] == "instantiate" else None
        equality = index.get(canonical(w["formula"][1])) if w["rule"] == "eq_subst" else None
        antecedent = index.get(canonical(w["formula"][2][1])) if w["rule"] == "eq_subst" else None
        if recipe["output"] in proved: tier = 6
        elif w["rule"] == "mp" and all(r in selected_rows for r in k[2]): tier = 0
        elif w["rule"] == "instantiate" and universal in proved: tier = 1
        elif w["rule"] == "eq_subst" and equality in proved and antecedent in proved: tier = 2
        elif w["rule"] == "axiom": tier = 3
        elif w["rule"] == "eq_subst" and equality in proved: tier = 4
        else: tier = 5
        return tier, ast_size(w["formula"]), canonical(w), k[0], k[2]
    arranged = sorted(keys, key=score)
    need(len(arranged) == len(keys) and set(arranged) == set(keys), "complete fixed fallback permutation")
    return keys, arranged
