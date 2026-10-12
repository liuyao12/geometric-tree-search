"""Full finite static audit, independent of every geometry producer/checker.

Imports only our frozen v1 independent checker and Python's standard library.
An explicit source/input freeze is mandatory. This CLI must not run before
root reviews that freeze. It invokes no engine, solver, search or native code.
"""
import argparse
import copy
import gc
import gzip
import hashlib
import json
import resource
import signal
import sys
import time
from collections import Counter
from pathlib import Path

import independent_aggregate_audit_v1 as base

ROOT = Path(__file__).resolve().parents[2]
MARKING_VERSION = "injective-formula-ordered-mp-offset-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def equal(actual, expected, label):
    # Serialized exact comparison also distinguishes False/0 and True/1.
    base.require(canonical(actual) == canonical(expected), label)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        base.require(key not in result, "duplicate JSON dictionary key")
        result[key] = value
    return result


def load(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=object_pairs)


def save(path, value):
    base.require(not path.exists(), "immutable output already exists: " + str(path))
    opener = gzip.open if str(path).endswith(".gz") else open
    # Streaming serialization, not a second full pretty-printed string.
    with opener(path, "wt", encoding="utf-8") as handle:
        for chunk in json.JSONEncoder(sort_keys=True, separators=(",", ":"),
                                      ensure_ascii=False).iterencode(value):
            handle.write(chunk)
        handle.write("\n")


def file_pin(path):
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            hasher.update(chunk)
            size += len(chunk)
    return {"path": str(path.relative_to(ROOT)), "sha256": hasher.hexdigest(), "bytes": size}


def check_pins(pins):
    for pin in pins:
        equal(file_pin(ROOT / pin["path"]), {k: pin[k] for k in ("path", "sha256", "bytes")},
              "changed frozen input/source: " + pin["path"])


def decoded_hash(path):
    result = hashlib.sha256()
    size = 0
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            result.update(chunk)
            size += len(chunk)
    return {"sha256": result.hexdigest(), "bytes": size}


def body(declaration):
    return {key: value for key, value in declaration.items() if key != "name"}


def mapped_expression(expression, constants):
    if expression[0] == "fun":
        base.require(expression[2] == [] and expression[1] in constants,
                     "unsupported source function/map")
        return copy.deepcopy(constants[expression[1]])
    if expression[0] == "var":
        return copy.deepcopy(expression)
    if expression[0] == "pred":
        return ["pred", expression[1], [mapped_expression(x, constants) for x in expression[2]]]
    if expression[0] == "all":
        return ["all", expression[1], mapped_expression(expression[2], constants)]
    return [expression[0]] + [mapped_expression(x, constants) for x in expression[1:]]


def transported_body(source, record):
    constants = record["constant_map"]
    result = {"premises": [mapped_expression(f, constants) for f in source["premises"]],
              "conclusion": mapped_expression(source["conclusion"], constants), "proof": []}
    expression_fields = {"formula", "universal", "term", "left", "right", "template"}
    for source_command in source["proof"]:
        command = {}
        for key, value in source_command.items():
            if key in expression_fields:
                command[key] = mapped_expression(value, constants)
            elif key == "name" and source_command["rule"] == "block":
                base.require(value in record["dependency_name_map"], "missing dependency transport")
                command[key] = record["dependency_name_map"][value]
            elif key == "name" and source_command["rule"] == "axiom":
                base.require(value in record["axiom_name_map"], "missing axiom-name transport")
                command[key] = record["axiom_name_map"][value]
            else:
                command[key] = copy.deepcopy(value)
        result["proof"].append(command)
    return result


def symbolic_source_gate(certificate, schemas):
    source_checker = base.SymbolicChecker(schemas["source_theory"])
    source_blocks = {}
    for declaration in schemas["blocks"]:
        source_checker.admit(declaration)
        source_blocks[declaration["name"]] = declaration
    checker = base.SymbolicChecker(certificate["recipient_theory"])
    record_by_name, aliases, receipts = {}, [], []
    for rank, record in enumerate(certificate["records"]):
        name = record["definition"]["name"]
        base.require(name not in record_by_name and record["source_block"] in source_blocks,
                     "duplicate/unbound transported declaration")
        source = source_blocks[record["source_block"]]
        equal(digest(body(source)), record["source_body_sha256"], "source-body binding")
        equal(digest(body(record["definition"])), record["body_sha256"], "mapped-body binding")
        equal(sorted(record["constant_map"]), sorted(schemas["source_theory"]["functions"]),
              "incomplete constant map")
        for key, value in record["constant_map"].items():
            checker.term(value, closed=True)
            allowed = ("P", "Q", "R") if key in ("A", "B", "C") else ("l", "m", "n")
            base.require(key in ("A", "B", "C", "u", "v") and value[1] in allowed,
                         "map is not closed role-preserving")
        for axiom_name, axiom in schemas["source_theory"]["axioms"].items():
            image_name = record["axiom_name_map"].get(axiom_name)
            base.require(image_name in checker.axioms, "missing recipient axiom")
            equal(mapped_expression(axiom, record["constant_map"]), checker.axioms[image_name],
                  "axiom image differs from frozen guarded I.2")
        equal(transported_body(source, record), body(record["definition"]),
              "full literal closed-constant transport mismatch")
        direct = []
        for command in record["definition"]["proof"]:
            if command["rule"] == "block" and command["name"] not in direct:
                direct.append(command["name"])
        equal(record["dependencies"], direct, "complete ordered direct-dependency list")
        base.require(all(dependency in record_by_name for dependency in direct),
                     "non-prior dependency declaration")
        for source_dependency, target_dependency in record["dependency_name_map"].items():
            base.require(source_dependency in source_blocks and target_dependency in record_by_name,
                         "unavailable dependency alias")
            aliases.append({"owner": name, "source_dependency": source_dependency,
                            "target_dependency": target_dependency,
                            "target_body_sha256": record_by_name[target_dependency]["body_sha256"]})
        receipt = checker.admit(record["definition"])
        receipt["rank"] = rank
        receipt["logical_commands"] = [{"index": index, "rule": command["rule"],
            "command_sha256": digest(command), "formula_sha256": digest(command["formula"]),
            "strict_prior_ordered_references": ([command["antecedent"], command["implication"]]
                if command["rule"] == "mp" else command["inputs"] if command["rule"] == "block" else [])}
            for index, command in enumerate(record["definition"]["proof"])]
        receipts.append(receipt)
        record_by_name[name] = record
    equal(aliases, certificate["dependency_aliases"], "complete dependency alias ledger")
    return checker, record_by_name, receipts


def literal_expansion(record, record_by_name):
    """Iterative local-call-frame interpreter, independently from producer walk."""
    declaration = record["definition"]
    inputs = ["input:" + str(i) for i in range(len(declaration["premises"]))]
    formulas = dict(zip(inputs, declaration["premises"]))
    leaves, aliases, calls = [], [], []

    def frame(name, supplied, path, return_event=None):
        block = record_by_name[name]["definition"]
        equal([formulas[key] for key in supplied], block["premises"], "local ordered input binding")
        return {"name": name, "block": block, "supplied": supplied, "path": path,
                "cursor": 0, "local": [], "return_event": return_event}

    stack = [frame(declaration["name"], inputs, [])]
    output = None
    while stack:
        active = stack[-1]
        commands = active["block"]["proof"]
        if active["cursor"] == len(commands):
            base.require(active["local"], "empty expansion call")
            output = active["local"][-1]
            equal(formulas[output], active["block"]["conclusion"], "literal call endpoint")
            stack.pop()
            if stack:
                event = active["return_event"]
                event.update(output_node=output, leaf_interval=[event.pop("leaf_start"), len(leaves)],
                             new_macro_occupancy=0)
                calls.append(event)
                stack[-1]["local"].append(output)
            continue
        index = active["cursor"]
        command = commands[index]
        active["cursor"] += 1
        source_record = record_by_name[active["name"]]
        occurrence = {"definition": active["name"], "command_index": index,
                      "path": active["path"] + [index],
                      "source_body_sha256": source_record["source_body_sha256"],
                      "mapped_body_sha256": source_record["body_sha256"]}
        rule = command["rule"]
        if rule == "block":
            children = [active["local"][prior] for prior in command["inputs"]]
            event = {"source_occurrence": occurrence, "dependency_name": command["name"],
                     "ordered_input_nodes": children, "leaf_start": len(leaves)}
            base.require(command["name"] not in [x["name"] for x in stack], "cyclic expansion")
            stack.append(frame(command["name"], children, active["path"] + [index], event))
            continue
        if rule == "assumption":
            node = active["supplied"][command["index"]]
            aliases.append({"source_occurrence": occurrence,
                            "ordered_assumption_index": command["index"], "alias_to": node,
                            "formula": command["formula"], "t": [], "m": [], "new_occupancy": 0})
        else:
            children = [active["local"][command[key]] for key in ("antecedent", "implication")] if rule == "mp" else []
            node = "leaf:" + str(len(leaves))
            witness = {key: value for key, value in command.items()
                       if key not in ("antecedent", "implication")}
            leaves.append({"node": node, "source_occurrence": occurrence,
                           "primitive_witness": witness, "ordered_input_nodes": children,
                           "ordered_premise_formulas": [formulas[key] for key in children],
                           "formula": command["formula"]})
            formulas[node] = command["formula"]
        equal(formulas[node], command["formula"], "literal local command formula")
        active["local"].append(node)
    return {"definition_name": declaration["name"], "family": record["family"],
            "constant_map": record["constant_map"], "source_block": record["source_block"],
            "source_body_sha256": record["source_body_sha256"], "mapped_body_sha256": record["body_sha256"],
            "ordered_dependencies": record["dependencies"], "ordered_local_premises": declaration["premises"],
            "conclusion": declaration["conclusion"], "input_nodes": inputs, "leaves": leaves,
            "assumption_aliases": aliases, "recursive_calls": calls, "output_node": output}


def recipe_key(witness, premises):
    return {"primitive_witness": {key: value for key, value in witness.items()
                                  if key not in ("antecedent", "implication")},
            "ordered_premise_formulas": premises}


def reconstruct_palette(expansions, original, theory, authority):
    known = {canonical(formula) for formula in original["formula_codes"]}
    extras, grouped = {}, {}
    for expansion in expansions:
        for formula in expansion["ordered_local_premises"] + [x["formula"] for x in expansion["leaves"]]:
            if canonical(formula) not in known:
                extras[canonical(formula)] = formula
        for leaf in expansion["leaves"]:
            key = canonical(recipe_key(leaf["primitive_witness"], leaf["ordered_premise_formulas"]))
            if key not in grouped:
                grouped[key] = {**json.loads(key), "source_occurrence_aliases": []}
            grouped[key]["source_occurrence_aliases"].append({"root_definition": expansion["definition_name"],
                "leaf_node": leaf["node"], **leaf["source_occurrence"]})
    formula_codes = original["formula_codes"] + [extras[key] for key in sorted(extras)]
    registry = digest(formula_codes)
    code_lookup = base.formula_registry(formula_codes, base.SymbolicChecker(theory))
    for occurrence, formula in enumerate(original["context"]["ordered_local_premises"]):
        key = canonical(recipe_key({"rule": "assumption", "index": occurrence, "formula": formula}, []))
        base.require(key not in grouped, "unexpected source leaf assumption")
        grouped[key] = {**json.loads(key), "source_occurrence_aliases": [],
                        "scope": "recipient ordered local premise only"}
    recipes = []
    for key in sorted(grouped):
        recipe = grouped[key]
        preimage = {"recipe": json.loads(key), "primitive_authority_epoch": authority["epoch"],
                    "recipient_theory_sha256": digest(theory), "marking_version": MARKING_VERSION,
                    "formula_registry_sha256": registry}
        if recipe["primitive_witness"]["rule"] == "assumption":
            preimage["local_context_id"] = digest(original["context"])
        recipe = {**recipe, "identity_preimage": preimage,
                  "id": "primitive-recipe-" + digest(preimage)}
        recipes.append(recipe)
    lookup = {canonical(recipe_key(x["primitive_witness"], x["ordered_premise_formulas"])): x for x in recipes}
    return formula_codes, code_lookup, recipes, lookup


def expected_authority(certificate, roles):
    authority = {"label": "inactive_static_structural_transport", "activated": False,
        "native_accepted": False,
        "source_primitive_soundness": "requires independent logical audit for this finite inventory",
        "source_certificate_pin": file_pin(roles["transport_certificate"]),
        "source_structural_audit_pin": file_pin(roles["transport_audit"]),
        "reviewed_source_argument_pin": file_pin(roles["source_argument"]),
        "reviewed_source_argument_review_pin": file_pin(roles["source_argument_review"]),
        "original_native_donor_binding": certificate["source_native_binding"],
        "recipient_theory_sha256": digest(certificate["recipient_theory"]),
        "native_program_and_compiler_correspondence": "open"}
    return {**authority, "epoch": digest(authority)}


def placed_identity(command, refs, premises, row, recipe, context_id, authority, codes, registry):
    base.require(base.integer(row) and row >= 0 and len(refs) == len(premises), "placement arity/row")
    values = {(1, row): codes[base.canonical(command["formula"])]}
    ports = []
    for port, (source, formula) in enumerate(zip(refs, premises)):
        base.require(base.integer(source) and 0 <= source < row, "placement strict-prior reference")
        code = codes[base.canonical(formula)]
        base.require((1, source) not in values or values[(1, source)] == code,
                     "internal reference marking conflict")
        values[(1, source)] = code
        values[(2 + port, row)] = source - row
        ports.append({"port_index": port, "input_row": source, "formula_code": code,
                      "receptor_point": [1, source], "offset_mark_point": [2 + port, row],
                      "offset_value": source - row})
    t = [[0, row, 1]]
    m = [[x, y, value] for (x, y), value in sorted(values.items())]
    prototype = {"recipe_id": recipe["id"], "primitive_witness": recipe["primitive_witness"],
                 "ordered_premise_formulas": recipe["ordered_premise_formulas"],
                 "relative_ordered_input_offsets": [source - row for source in refs],
                 "orientation": "identity", "t": [[0, 0, 1]],
                 "m": [[x, y - row, value] for x, y, value in m],
                 "marking_version": MARKING_VERSION, "formula_registry_sha256": registry,
                 "authority_epoch": authority["epoch"]}
    preimage = {"prototype_id": "primitive-prototype-" + digest(prototype),
                "prototype_preimage": prototype, "transform": [0, row], "context_id": context_id,
                "ordered_input_rows": refs, "primitive_command": command, "t": t, "m": m,
                "authority_epoch": authority["epoch"], "formula_registry_sha256": registry}
    return {"id": "aggregate-primitive-" + digest(preimage), "row": row, "recipe_id": recipe["id"],
            "command": command, "ordered_inputs": refs, "t": t, "m": m, "ordered_ports": ports,
            "identity_preimage": preimage, "donor_occurrence_provenance": []}


def checked_aggregate(placements):
    unique = {}
    for placement in placements:
        key = placement["id"]
        if key in unique:
            equal(placement["identity_preimage"], unique[key]["identity_preimage"], "false ID sharing")
            for field in ("row", "command", "ordered_inputs", "t", "m"):
                equal(placement[field], unique[key][field], "false decorated sharing: " + field)
        unique[key] = placement
    point = base.point_union(list(unique.values()))
    return {"constituent_ids": sorted(unique), **point}


def receptor_ports(expansion, rows, placements):
    by_row = {p["row"]: p for p in placements}
    readers_by_node = {node: [] for node in expansion["input_nodes"]}
    for leaf in expansion["leaves"]:
        for port, input_node in enumerate(leaf["ordered_input_nodes"]):
            if input_node in readers_by_node:
                reader = by_row[rows[leaf["node"]]]
                projection = {key: value for key, value in reader["ordered_ports"][port].items()
                              if key != "port_index"}
                readers_by_node[input_node].append({"reader_row": reader["row"],
                    "primitive_input_port": port, "reader_placement_id": reader["id"], **projection})
    return [{"high_level_port": occurrence, "input_node": node, "input_row": rows[node],
             "formula": expansion["ordered_local_premises"][occurrence],
             "readers": readers_by_node[node], "new_occupancy": 0, "adds_macro_offset_mark": False}
            for occurrence, node in enumerate(expansion["input_nodes"])]


def canonical_embedding(expansion, checker, recipes, authority, codes, registry):
    context = {"theory": checker.theory, "ordered_local_premises": expansion["ordered_local_premises"]}
    context_id = digest(context)
    rows = {node: index for index, node in enumerate(expansion["input_nodes"])}
    seeds, commands = [], []
    for index, formula in enumerate(expansion["ordered_local_premises"]):
        command = {"rule": "assumption", "index": index, "formula": formula}
        preimage = {"kind": "fixed_local_context_seed", "context_id": context_id,
                    "command": command, "orientation": "identity", "transform": [0, index],
                    "t": [[0, index, 1]], "m": [[1, index, codes[base.canonical(formula)]]],
                    "formula_registry_sha256": registry, "marking_version": MARKING_VERSION,
                    "authority_epoch": authority["epoch"]}
        seeds.append({"id": "local-boundary-seed-" + digest(preimage), "identity_preimage": preimage,
                      "row": index, "formula": formula, "t": preimage["t"], "m": preimage["m"],
                      "generation": 0, "scope": "this definition local context, not an added recipient axiom"})
        checker.command(command, [x["formula"] for x in commands], context["ordered_local_premises"])
        commands.append(command)
    placements = []
    for leaf in expansion["leaves"]:
        row = len(commands)
        refs = [rows[node] for node in leaf["ordered_input_nodes"]]
        command = copy.deepcopy(leaf["primitive_witness"])
        if command["rule"] == "mp":
            command["antecedent"], command["implication"] = refs
        checker.command(command, [x["formula"] for x in commands], context["ordered_local_premises"])
        recipe = recipes[canonical(recipe_key(command, leaf["ordered_premise_formulas"]))]
        placement = placed_identity(command, refs, leaf["ordered_premise_formulas"], row,
                                    recipe, context_id, authority, codes, registry)
        expected = base.compile_primitive(command, row, commands, codes)
        equal({key: placement[key] for key in ("t", "m", "ordered_inputs")}, expected,
              "independent second primitive point reconstruction")
        placement["donor_occurrence_provenance"] = [leaf["source_occurrence"]]
        placements.append(placement)
        commands.append(command)
        rows[leaf["node"]] = row
    endpoint = rows[expansion["output_node"]]
    equal(commands[endpoint]["formula"], expansion["conclusion"], "canonical primitive endpoint")
    # Inference union has no premise occupancy; full local boundary includes it.
    full = [{"t": seed["t"], "m": seed["m"]} for seed in seeds] + placements
    base.point_union(full, [[0, row] for row in range(len(commands))], exact=True)
    return {"context": context, "context_id": context_id, "ordered_input_seeds": seeds,
            "node_rows": rows, "primitive_placements": placements,
            "cluster_aggregate": checked_aggregate(placements),
            "ordered_receptor_ports": receptor_ports(expansion, rows, placements),
            "conclusion_row": endpoint, "local_boundary_rows": len(commands),
            "boundary_context_is_not_the_global_three_premise_recipient": True}


def grammar_certificate(height, recipes, codes, original, authority, registry):
    # Counts are derived from exact recipe interfaces, using closed-form sums.
    # No full candidate catalog, eligibility graph or search is constructed.
    mp = [r for r in recipes if r["primitive_witness"]["rule"] == "mp"]
    zero = [r for r in recipes if r["primitive_witness"]["rule"] != "mp"]
    prototype_count = len(zero) + len(mp) * (height - 1) * (height - 1)
    squares = (height - 1) * height * (2 * height - 1) // 6
    prior = len(zero) * height + len(mp) * squares
    diagonal = sum(canonical(r["ordered_premise_formulas"][0]) !=
                   canonical(r["ordered_premise_formulas"][1]) for r in mp)
    conflicts = diagonal * height * (height - 1) // 2
    target = ["pred", "Incident", [["fun", "R", []], ["fun", "n", []]]]
    boundary = {"required": [[0, row] for row in range(height)],
        "root_generations": [[0, row, 0] for row in range(height)],
        "fixed_initial_local_seeds": [{"recipe_id": r["id"], "row": r["primitive_witness"]["index"], "generation": 0}
                                      for r in zero if r["primitive_witness"]["rule"] == "assumption"],
        "fixed_target_m": [[1, height - 1, codes[base.canonical(target)]]],
        "fixed_exterior_m": [[1, row, -1] for row in range(1 - height, 0)],
        "all_root_obligations_generation_zero": True}
    return {"height": height, "context": original["context"], "context_id": digest(original["context"]),
        "boundary": boundary, "primitive_recipe_ids": [r["id"] for r in recipes],
        "orientation": "identity", "transform_grammar": "vertical integer translation only",
        "prototype_origin": [0, 0], "mp_offset_domain": [1 - height, -1],
        "mp_offset_order": ["antecedent", "implication"], "positive_support_alignment_domain": [0, height - 1],
        "strict_prior_recipient_binding": "0 <= antecedent_row, implication_row < output_row < height",
        "assumption_availability": "Only the three declared local hypotheses; each may be cited again at any row. No interface-specific hypotheses are added.",
        "prototype_identity_recipe": "full recipe witness, ordered formulas/offsets, exact relative t/m, registry, orientation and authority",
        "placement_identity_recipe": "prototype plus vertical transform, exact placed t/m, literal primitive command, ordered refs and recipient context",
        "counts": {"raw_prototypes": prototype_count, "raw_positive_support_alignments": prototype_count * height,
                   "strict_prior_bindings_before_local_mark_agreement": prior,
                   "inconsistent_local_mark_functions": conflicts,
                   "locally_consistent_strict_prior_bindings": prior - conflicts},
        "counts_are_grammar_census_not_initial_legal_graph_degrees": True,
        "materialized_complete_placement_catalog": False,
        "initial_graph_and_t_m_dependency_indexes": "not_constructed",
        "base_fallback": "future executor must enumerate all recipes and both ordered prior references, no sampled or cluster-only domains",
        "authority_epoch": authority["epoch"], "formula_registry_sha256": registry,
        "semantic_relation_to_5_macro_rows": "different primitive boundary, not an exact macro-board bijection",
        "conditional_padding_lift": {"maximum_leaf_count_per_old_macro": 13, "old_macro_height": 5,
            "maximum_unshared_primitive_leaves": 65, "status": "conditional one-way proposed lift only; not constructed or proved here",
            "conditions": ["macro certificate is valid", "all used bodies are these expanded definitions",
                           "local premises preserved", "all references rebased strictly prior",
                           "valid I.2 axiom padding inserted before final conclusion",
                           "recipient primitive inventory includes every expanded recipe"]}}


def census(expansions, certificate, recipes, formula_codes, original):
    families = Counter(e["family"] for e in expansions)
    return {"named_definitions": len(expansions),
        "source_body_leaf_occurrences": sum(len(e["leaves"]) for e in expansions),
        "family_counts": dict(families),
        "family_leaf_counts": {family: sorted({len(e["leaves"]) for e in expansions if e["family"] == family})
                               for family in sorted(families)},
        "maximum_body_leaf_count": max(len(e["leaves"]) for e in expansions),
        "primitive_recipe_types": len(recipes),
        "primitive_recipe_rules": dict(Counter(r["primitive_witness"]["rule"] for r in recipes)),
        "formula_codes": len(formula_codes), "preserved_authored_formula_prefix": len(original["formula_codes"]),
        "assumption_alias_occurrences": sum(len(e["assumption_aliases"]) for e in expansions),
        "recursive_block_call_occurrences": sum(len(e["recursive_calls"]) for e in expansions),
        "duplicate_premise_interfaces": sum(len({canonical(f) for f in e["ordered_local_premises"]})
                                           < len(e["ordered_local_premises"]) for e in expansions),
        "noninjective_constant_maps": sum(len({canonical(v) for v in r["constant_map"].values()})
                                           < len(r["constant_map"]) for r in certificate["records"])}


class StreamingObject:
    """Standard-library decoder with a bounded retained top-level record.

    This does not trust producer framing: every delimiter/key is parsed, all
    duplicate keys are rejected, and the final JSON/file end is checked.
    A whole 'records' array is never simultaneously retained. Other top-level
    fields and one individual record may use at most the predeclared buffer.
    """
    def __init__(self, handle, max_buffer=16777216):
        self.handle = handle
        self.buffer = ""
        self.position = 0
        self.eof = False
        self.limit = max_buffer
        self.decoder = json.JSONDecoder(object_pairs_hook=object_pairs)

    def fill(self):
        base.require(not self.eof, "unexpected JSON end")
        more = self.handle.read(65536)
        if not more:
            self.eof = True
            return False
        self.buffer += more
        base.require(len(self.buffer) <= self.limit, "per-record JSON buffer gate exceeded")
        return True

    def whitespace(self):
        while True:
            while self.position < len(self.buffer) and self.buffer[self.position].isspace():
                self.position += 1
            if self.position < len(self.buffer) or self.eof:
                return
            self.fill()

    def peek(self):
        self.whitespace()
        return self.buffer[self.position] if self.position < len(self.buffer) else None

    def token(self, character):
        base.require(self.peek() == character, "invalid JSON delimiter: expected " + character)
        self.position += 1

    def value(self):
        self.whitespace()
        while True:
            try:
                value, end = self.decoder.raw_decode(self.buffer, self.position)
                self.position = end
                return value
            except json.JSONDecodeError:
                base.require(not self.eof and self.fill(), "malformed or truncated JSON value")

    def trim(self):
        self.buffer = self.buffer[self.position:]
        self.position = 0

    def entries(self):
        self.token("{")
        seen = set()
        while self.peek() != "}":
            key = self.value()
            base.require(isinstance(key, str) and key not in seen, "duplicate/invalid top-level key")
            seen.add(key)
            self.token(":")
            if key == "records":
                self.token("[")
                index = 0
                while self.peek() != "]":
                    value = self.value()
                    yield "record", index, value
                    index += 1
                    self.trim()
                    if self.peek() != "]":
                        self.token(",")
                self.token("]")
                yield "record_count", key, index
            else:
                value = self.value()
                yield "field", key, value
            self.trim()
            if self.peek() != "}":
                self.token(",")
        self.token("}")
        base.require(self.peek() is None and self.eof, "trailing data after JSON object")


def shared_example(original, expansions, checker, recipes, authority, codes, registry):
    # Use independently checked v1 DAG interning to derive the row word, then
    # attach v2 full decorated identities; donor occurrences stay separate.
    forest = base.ExpansionForest(checker, original["context"]["ordered_local_premises"])
    members = []
    for cluster in original["clusters"]:
        output, rows = forest.embed_call(cluster["source_definition"], cluster["ordered_inputs"], cluster["name"])
        equal(output, cluster["conclusion_row"], "legacy forest output row")
        members.append(rows)
    commands = forest.commands()
    checker.proof(commands, original["context"]["ordered_local_premises"], commands[-1]["formula"])
    placements = []
    context_id = digest(original["context"])
    for row, command in enumerate(commands):
        refs = [command["antecedent"], command["implication"]] if command["rule"] == "mp" else []
        premise_formulas = [commands[source]["formula"] for source in refs]
        recipe = recipes[canonical(recipe_key(command, premise_formulas))]
        placement = placed_identity(command, refs, premise_formulas, row, recipe,
                                    context_id, authority, codes, registry)
        if command["rule"] == "assumption":
            placement["donor_occurrence_provenance"] = [{"kind": "recipient_local_premise", "index": row}]
        placements.append(placement)
    clusters = []
    expansion_by_name = {e["definition_name"]: e for e in expansions}
    for cluster, distinct_rows in zip(original["clusters"], members):
        expansion = expansion_by_name[cluster["source_definition"]]
        rows = dict(zip(expansion["input_nodes"], cluster["ordered_inputs"]))
        # Match each literal occurrence to its independently derived full
        # command/reference row, not to a formula. All occurrences are retained.
        available = {canonical(p["command"]): p["row"] for p in placements
                     if p["command"]["rule"] != "assumption"}
        for leaf in expansion["leaves"]:
            command = copy.deepcopy(leaf["primitive_witness"])
            if command["rule"] == "mp":
                command["antecedent"], command["implication"] = [rows[n] for n in leaf["ordered_input_nodes"]]
            base.require(canonical(command) in available, "missing legacy exact-command occurrence")
            row = available[canonical(command)]
            base.require(row in distinct_rows, "legacy occurrence outside its cluster")
            rows[leaf["node"]] = row
            placements[row]["donor_occurrence_provenance"].append(leaf["source_occurrence"])
        actual_members = [placements[row] for row in distinct_rows]
        clusters.append({"name": cluster["name"], "definition_name": expansion["definition_name"],
            "ordered_inputs": cluster["ordered_inputs"], "node_rows": rows,
            "conclusion_row": rows[expansion["output_node"]], "aggregate": checked_aggregate(actual_members),
            "ordered_receptor_ports": receptor_ports(expansion, rows, actual_members),
            "legacy_constituent_ids": cluster["constituent_ids"]})
    correspondence = []
    for row, (placement, old) in enumerate(zip(placements, original["primitive_placements"])):
        for key in ("row", "command", "ordered_inputs", "t", "m"):
            equal(placement[key], old[key], "legacy primitive field: " + key)
        legacy = "primitive-" + digest({"command": placement["command"], "context_id": context_id}) + "@" + str(row)
        equal(legacy, old["id"], "legacy printed identity")
        correspondence.append({"row": row, "legacy_id": legacy, "full_decorated_id": placement["id"],
                               "legacy_identity_scope": "command/context and row only; not registry/authority"})
    first = set(clusters[0]["aggregate"]["constituent_ids"])
    second = set(clusters[1]["aggregate"]["constituent_ids"])
    base.point_union(placements, original["declared_example_boundary"]["required"],
                     original["declared_example_boundary"]["fixed_target_m"], exact=True)
    return {"status": "static_authored_example_reconstructed", "context": original["context"],
        "context_id": context_id, "placements": placements, "clusters": clusters,
        "legacy_label_correspondence": correspondence, "shared_constituent_ids": sorted(first & second),
        "shared_rows": [p["row"] for p in placements if p["id"] in first & second],
        "first_units": len(first), "second_units": len(second), "distinct_derived_units": len(first | second),
        "new_second_units": len(second - first), "derived_aggregate": checked_aggregate(placements[3:]),
        "full_aggregate_with_three_seeds": checked_aggregate(placements),
        "authored_design_not_a_discovered_chained_proof": True,
        "native_acceptance": "not_run", "search_conformance": "not_run"}


def mutate_controls(checker, canonical_sample, recipes, original, authority, codes, formula_codes):
    controls = []
    for result in base.run_fixtures(base.fixtures()):
        controls.append({"name": "retained_toy_" + result["name"], **{k: v for k, v in result.items() if k != "name"}})

    def reject(name, callback, **data):
        reason = base.rejected(callback)
        controls.append({"name": name, "status": "passed_rejected", "reason": reason, **data})

    sample = canonical_sample["primitive_placements"][-1]
    stale = copy.deepcopy(sample["identity_preimage"])
    stale["authority_epoch"] = "0" * 64
    reject("actual_stale_authority_even_with_rehashed_label", lambda: equal(stale, sample["identity_preimage"],
        "placement authority is not common frozen closure"), mutant_id="aggregate-primitive-" + digest(stale))
    changed_registry = copy.deepcopy(sample["identity_preimage"])
    changed_registry["formula_registry_sha256"] = "0" * 64
    reject("actual_stale_registry_even_with_rehashed_label", lambda: equal(changed_registry, sample["identity_preimage"],
        "placement registry is not the full injective closure"), mutant_id="aggregate-primitive-" + digest(changed_registry))
    recipe = recipes[0]
    changed_recipe = copy.deepcopy(recipe["identity_preimage"])
    changed_recipe["primitive_authority_epoch"] = "0" * 64
    reject("actual_recipe_stale_authority", lambda: equal(changed_recipe, recipe["identity_preimage"], "recipe epoch mismatch"))
    reject("actual_formula_registry_duplicate", lambda: base.formula_registry(formula_codes + [formula_codes[0]], checker))

    # Use an actual final MP and rebuild its markings/ID around an invalid
    # claimed conclusion. It has no later consumer: point union still passes.
    local = canonical_sample["ordered_input_seeds"]
    commands = [s["identity_preimage"]["command"] for s in local] + [p["command"] for p in canonical_sample["primitive_placements"]]
    final = len(commands) - 1
    base.require(commands[final]["rule"] == "mp", "mutation fixture requires actual final MP")
    wrong = ["eq", ["fun", "P", []], ["fun", "P", []]]
    base.require(wrong != commands[final]["formula"], "mutation conclusion unchanged")
    bad = copy.deepcopy(commands)
    bad[final]["formula"] = wrong
    bad_codes = dict(codes)
    bad_codes.setdefault(base.canonical(wrong), len(bad_codes))
    points = [{**base.compile_primitive(command, row, bad[:row], bad_codes)} for row, command in enumerate(bad)]
    base.point_union(points, [[0, row] for row in range(len(bad))], exact=True)
    reject("actual_point_consistent_invalid_final_MP", lambda: checker.proof(bad, canonical_sample["context"]["ordered_local_premises"]),
           point_consistency=True, symbolic_acceptance=False, mutated_command=bad[final],
           mutated_primitive_points=points[final])
    reversed_refs = copy.deepcopy(commands[final])
    reversed_refs["antecedent"], reversed_refs["implication"] = reversed_refs["implication"], reversed_refs["antecedent"]
    reject("actual_reversed_ordered_MP_references", lambda: checker.command(reversed_refs,
        [c["formula"] for c in commands[:final]], canonical_sample["context"]["ordered_local_premises"]))
    duplicate = copy.deepcopy(sample)
    duplicate["m"] = copy.deepcopy(duplicate["m"]) + [[200, 200, 0]]
    reject("actual_hidden_marking_change_under_same_id", lambda: checked_aggregate([sample, duplicate]))
    reject("actual_naive_shared_occupancy_overcount", lambda: base.point_union([sample, sample]))

    before = ["all", "x", ["all", "x", ["pred", "Point", [["var", "x"]]]]]
    after = base.substitute_closed(before[2], "x", ["fun", "P", []])
    equal(after, before[2], "shadowing must stop free substitution")
    bad_instance = {"rule": "instantiate", "universal": before, "term": ["fun", "P", []],
                    "formula": ["imp", before, ["all", "x", ["pred", "Point", [["fun", "P", []]]]]]}
    reject("shadowed_binder_wrong_instantiation", lambda: checker.command(bad_instance, [], []))
    return controls


def audit(plan, roles):
    times = {}
    began = time.perf_counter()
    producer_plan = load(roles["scientific_producer_plan"])
    checkpoint = load(roles["production_checkpoint"])
    equal(checkpoint["status"], "bounded_static_production_passed_independent_audit_pending", "production gate unknown")
    check_pins(producer_plan["inputs"] + producer_plan["sources"] + producer_plan["preserved_files"])
    check_pins(checkpoint["data_pins"] + [checkpoint[k] for k in (
        "plan_v1_pin", "repair_plan_v2_pin", "production_pin", "supervision_pin", "outer_lifetime_pin",
        "serialization_correspondence_pin")])
    serialization = []
    for current, historical in (("expansions", "historical_expansions"),
                                 ("model", "historical_model"),
                                 ("example_correspondence", "historical_example")):
        decoded = decoded_hash(roles[current])
        equal(decoded, decoded_hash(roles[historical]), "exact historical/current decoded JSON bytes")
        serialization.append({"current_pin": file_pin(roles[current]), "historical_pin": file_pin(roles[historical]),
                              "decoded_exact_bytes": decoded,
                              "historical_resource_status": "unknown_memory_over_budget_not_reclassified"})
    certificate = load(roles["transport_certificate"])
    schemas = load(roles["source_schemas"])
    original = load(roles["authored_example"])
    checker, by_name, symbolic_receipts = symbolic_source_gate(certificate, schemas)
    expansions = [literal_expansion(record, by_name) for record in certificate["records"]]
    times["source_transport_logic_and_literal_expansion"] = time.perf_counter() - began
    authority = expected_authority(certificate, roles)
    formulas, codes, palette, recipe_lookup = reconstruct_palette(expansions, original, checker.theory, authority)
    registry = digest(formulas)
    counts = census(expansions, certificate, palette, formulas, original)
    times["registry_recipe_census_after_source_phase"] = time.perf_counter() - began - sum(times.values())
    common = {"version": plan["scientific_output_version"], "plan_pin": file_pin(roles["scientific_producer_plan"]),
              "authority": authority, "input_bindings": producer_plan["inputs"], "formula_registry_sha256": registry}
    model = load(roles["model"])
    models = [grammar_certificate(height, palette, codes, original, authority, registry) for height in (24, 65)]
    expected_model = {**common, "status": "declared_parametric_primitive_model_not_complete_graph",
        "formula_codes": formulas, "recipes": palette, "models": models,
        "primitive_palette_alias_rule": "Full witness and ordered formula interface equality; all named source definitions and donor occurrences remain distinct records.",
        "graph_required_before_any_search": ["enumerate complete placement universe and all t/m dependencies",
            "compare independent graph and exact rollback", "enforce global dead then forced then earliest generation",
            "validate proposal continuation with same complete base fallback"],
        "aggregate_family_embedding_obligations": ["ordered body-preserving primitive embeddings",
            "local premises earlier than their actual readers, not necessarily before unrelated leaves",
            "input aliases have no occupancy", "shared full decorated placements counted once",
            "a concrete family embedding translates rigidly only", "complete finite embedding enumeration remains open"]}
    equal(model, expected_model, "full palette/model/schema/authority/census reconstruction")
    del model, expected_model
    gc.collect()
    times["parametric_model_and_recipe_check"] = time.perf_counter() - began - sum(times.values())
    original_catalog = load(roles["row_catalog"])
    legacy_receipt = base.inspect_design(original, original_catalog["formula_codes"], authority)
    del original_catalog
    expected_example = shared_example(original, expansions, checker, recipe_lookup, authority, codes, registry)
    actual_example = load(roles["example_correspondence"])
    equal(actual_example, {**common, **expected_example}, "complete new/legacy authored 24-row correspondence")
    del actual_example
    times["legacy_and_full24_example"] = time.perf_counter() - began - sum(times.values())
    # Stream and discard each actual canonical record after complete checking.
    expected_headers = {**common, "status": "static_expansion_produced_pending_independent_audit",
        "counts": counts, "formula_codes": formulas, "original_dependency_aliases": certificate["dependency_aliases"]}
    checked_fields, record_receipts = set(), []
    record_count = 0
    mutation_sample = None
    with gzip.open(roles["expansions"], "rt", encoding="utf-8") as handle:
        parser = StreamingObject(handle, plan["limits"]["json_record_buffer_characters"])
        for kind, key, value in parser.entries():
            if kind == "field":
                base.require(key in expected_headers, "unexpected expansion header")
                equal(value, expected_headers[key], "expansion header: " + key)
                checked_fields.add(key)
            elif kind == "record_count":
                equal(value, len(expansions), "complete expansion record count")
            else:
                base.require(key == record_count and key < len(expansions), "unexpected record order/count")
                expected = expansions[key]
                embedding = canonical_embedding(expected, checker, recipe_lookup, authority, codes, registry)
                with_recipe_ids = [dict(leaf, recipe_id=recipe_lookup[canonical(recipe_key(
                    leaf["primitive_witness"], leaf["ordered_premise_formulas"]))]["id"]) for leaf in expected["leaves"]]
                full = {**expected, "leaves": with_recipe_ids, "canonical_embedding": embedding}
                equal(value, full, "all fields of full literal/canonical record " + str(key))
                record_receipts.append({"rank": key, "definition_name": expected["definition_name"],
                    "full_expected_record_sha256": digest(full), "leaves": len(with_recipe_ids),
                    "aliases": len(expected["assumption_aliases"]), "recursive_calls": len(expected["recursive_calls"]),
                    "canonical_aggregate_sha256": digest(embedding["cluster_aggregate"]),
                    "leaf_checks": [{"node": leaf["node"], "witness_sha256": digest(leaf["primitive_witness"]),
                        "ordered_input_nodes": leaf["ordered_input_nodes"], "source_occurrence": leaf["source_occurrence"],
                        "primitive_row": embedding["node_rows"][leaf["node"]],
                        "full_placement_id": placement["id"], "full_preimage_sha256": digest(placement["identity_preimage"]),
                        "point_and_logical_acceptance": True}
                        for leaf, placement in zip(with_recipe_ids, embedding["primitive_placements"])]})
                if expected["family"] == "searched-incidence-transport" and mutation_sample is None:
                    mutation_sample = embedding
                record_count += 1
                del value, full, embedding
    equal(sorted(checked_fields), sorted(expected_headers), "all expansion top-level fields present")
    equal(record_count, len(expansions), "every source body checked")
    times["streamed_all_canonical_records"] = time.perf_counter() - began - sum(times.values())
    controls = mutate_controls(checker, mutation_sample, palette, original, authority, codes, formulas)
    times["actual_and_toy_corruptions"] = time.perf_counter() - began - sum(times.values())
    # Reconcile exact producer summaries, retaining the failed first budget.
    equal(counts, checkpoint["counts"], "independently derived versus producer census")
    equal({str(model["height"]): model["counts"] for model in models}, checkpoint["model_grammar_counts"],
          "independently derived versus producer parametric grammar counts")
    return {"status": "passed_independent_finite_static_symbolic_and_aggregate_audit",
        "scope": "Complete frozen source-body expansion/canonical aggregation and declared parametric grammar; no graph, search, native or compiler correspondence.",
        "counts": counts, "model_grammar_counts": {str(model["height"]): model["counts"] for model in models},
        "source_logical_receipts": symbolic_receipts, "records": record_receipts,
        "legacy24_receipt": legacy_receipt, "full24_example_sha256": digest(expected_example),
        "shared_rows": expected_example["shared_rows"], "shared_units": len(expected_example["shared_rows"]),
        "mutations_and_toys": controls, "corruption_count": len(controls), "stage_seconds": times,
        "source_authority": authority,
        "production_costs_retained": {"checkpoint_pin": file_pin(roles["production_checkpoint"]),
            "prior_v1_unknown": checkpoint["prior_v1_unknown"],
            "cumulative_production_outer_seconds": checkpoint["cumulative_production_outer_seconds"],
            "v2_conservative_host_peak_bytes": checkpoint["v2_conservative_host_peak_bytes"]},
        "independent_serialization_correspondence": serialization,
        "native_queries": 0, "searches": 0, "solvers": 0, "engine_activation": False,
        "remaining_gaps": checkpoint["remaining_gaps"],
        "identity_scope": "Old IDs remain command/context/@row labels; fresh full identities bind exact t/m, registry and common authority, with donor provenance retained separately.",
        "cost_scope": "Full worker startup/final write and supervisor cost are charged by the separate lifetime receipt; stage timers precede final report serialization. Authoring preparation is unmeasured, not zero."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    began = time.perf_counter()
    plan_path = Path(args.plan)
    plan = load(plan_path)
    base.require(plan["scope"] == "independent_full171_static_audit_no_activation", "full audit scope")
    check_pins(plan["sources"] + plan["inputs"])
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("full static audit timeout")))
    signal.setitimer(signal.ITIMER_REAL, plan["limits"]["worker_alarm_seconds"])
    roles = {pin["role"]: ROOT / pin["path"] for pin in plan["inputs"] if "role" in pin}
    report = audit(plan, roles)
    check_pins(plan["sources"] + plan["inputs"])
    report["plan_pin"] = file_pin(plan_path)
    report["worker_seconds_before_report_write"] = time.perf_counter() - began
    report["kernel_peak_rss_bytes_before_write"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss *
                                                       (1 if sys.platform == "darwin" else 1024))
    save(ROOT / plan["outputs"]["audit"], report)
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps({"status": report["status"], "counts": report["counts"],
                      "seconds_before_report_write": report["worker_seconds_before_report_write"]}), flush=True)


if __name__ == "__main__":
    main()
