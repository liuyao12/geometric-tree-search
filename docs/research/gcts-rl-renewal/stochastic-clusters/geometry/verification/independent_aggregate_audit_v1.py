"""Independent, fail-closed symbolic/point audit. No project imports or engines.

This first version provides the prospective 24-row audit and bounded toy
fixtures. Its CLI deliberately does not run the real design audit: that phase
needs a separately frozen input/resource gate after root review.
"""
import argparse
import copy
import hashlib
import json
import platform
import resource
import signal
import sys
import time
from pathlib import Path


class Rejected(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Rejected(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def exact_keys(value, keys, label):
    require(isinstance(value, dict) and set(value) == set(keys), label + ": fields")


def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)


def symbol(value):
    return isinstance(value, str) and bool(value)


def free_variables(value, bound=frozenset()):
    if value[0] == "var":
        return set() if value[1] in bound else {value[1]}
    if value[0] in ("fun", "pred"):
        return set().union(*(free_variables(x, bound) for x in value[2]))
    if value[0] == "all":
        return free_variables(value[2], bound | {value[1]})
    return set().union(*(free_variables(x, bound) for x in value[1:]))


def substitute_closed(value, variable, replacement):
    """Free substitution; replacement is independently required closed.

    The binder with the replaced name stops traversal. Closed replacements
    cannot be captured, so no fresh-name convention is silently assumed.
    """
    if value[0] == "var":
        return copy.deepcopy(replacement if value[1] == variable else value)
    if value[0] in ("fun", "pred"):
        return [value[0], value[1],
                [substitute_closed(x, variable, replacement) for x in value[2]]]
    if value[0] == "all":
        return copy.deepcopy(value) if value[1] == variable else [
            "all", value[1], substitute_closed(value[2], variable, replacement)]
    return [value[0]] + [substitute_closed(x, variable, replacement)
                         for x in value[1:]]


class SymbolicChecker:
    """The declared six-rule nullary relation, independently reconstructed.

    This is a host symbolic checker, not the native/Wang checker. It rejects
    unsupported constructors, open instantiation terms, unknown fields,
    non-nullary functions, forward/cyclic declarations and malformed formulas.
    """
    def __init__(self, theory):
        exact_keys(theory, ("functions", "predicates", "axioms", "schemas"), "theory")
        require(theory["schemas"] == [], "unsupported schema")
        self.theory = copy.deepcopy(theory)
        self.functions = {}
        self.predicates = {}
        self.axioms = {}
        require(isinstance(theory["functions"], dict)
                and isinstance(theory["predicates"], dict)
                and isinstance(theory["axioms"], dict), "signature/axiom dictionaries")
        for name, arity in theory["functions"].items():
            require(symbol(name) and integer(arity) and arity == 0 and name not in self.functions,
                    "non-nullary or duplicate function")
            self.functions[name] = arity
        for name, arity in theory["predicates"].items():
            require(symbol(name) and integer(arity) and arity >= 0
                    and name not in self.predicates, "invalid predicate declaration")
            self.predicates[name] = arity
        for name, formula in theory["axioms"].items():
            require(symbol(name) and name not in self.axioms,
                    "duplicate axiom")
            self.formula(formula, closed=True)
            self.axioms[name] = copy.deepcopy(formula)
        self.definitions = {}
        self.definition_receipts = []

    def term(self, value, closed=False):
        require(isinstance(value, list) and value, "malformed term")
        if value[0] == "var":
            require(len(value) == 2 and symbol(value[1]), "invalid variable")
        else:
            require(len(value) == 3 and value[0] == "fun" and symbol(value[1])
                    and value[1] in self.functions and value[2] == [],
                    "unsupported or undeclared term")
        require(not closed or not free_variables(value), "open replacement term")

    def formula(self, value, closed=False):
        require(isinstance(value, list) and value, "malformed formula")
        tag = value[0]
        if tag == "pred":
            require(len(value) == 3 and value[1] in self.predicates
                    and isinstance(value[2], list)
                    and len(value[2]) == self.predicates[value[1]],
                    "unknown predicate or arity mismatch")
            for term in value[2]:
                self.term(term)
        elif tag == "eq":
            require(len(value) == 3, "equality arity")
            self.term(value[1])
            self.term(value[2])
        elif tag == "not":
            require(len(value) == 2, "negation arity")
            self.formula(value[1])
        elif tag in ("and", "imp"):
            require(len(value) == 3, "binary connective arity")
            self.formula(value[1])
            self.formula(value[2])
        elif tag == "all":
            require(len(value) == 3 and symbol(value[1]), "universal arity")
            self.formula(value[2])
        else:
            raise Rejected("unsupported formula constructor: " + repr(tag))
        require(not closed or not free_variables(value), "open asserted formula")

    @staticmethod
    def prior(index, formulas):
        require(integer(index) and 0 <= index < len(formulas), "non-prior reference")
        return formulas[index]

    def command(self, command, formulas, ordered_context):
        require(isinstance(command, dict) and "rule" in command
                and "formula" in command, "malformed command")
        rule = command["rule"]
        result = command["formula"]
        self.formula(result, closed=True)
        if rule == "assumption":
            exact_keys(command, ("rule", "formula", "index"), rule)
            index = command["index"]
            require(integer(index) and 0 <= index < len(ordered_context),
                    "assumption occurrence outside ordered context")
            require(result == ordered_context[index], "assumption formula mismatch")
        elif rule == "axiom":
            exact_keys(command, ("rule", "formula", "name"), rule)
            require(command["name"] in self.axioms
                    and result == self.axioms[command["name"]],
                    "axiom is not exact frozen declaration")
        elif rule == "instantiate":
            exact_keys(command, ("rule", "formula", "term", "universal"), rule)
            universal, term = command["universal"], command["term"]
            self.formula(universal, closed=True)
            self.term(term, closed=True)
            require(universal[0] == "all", "instantiation source not universal")
            expected = ["imp", universal,
                        substitute_closed(universal[2], universal[1], term)]
            require(result == expected, "invalid universal-instantiation tautology")
        elif rule == "eq_subst":
            exact_keys(command, ("rule", "formula", "left", "right", "template",
                                 "variable"), rule)
            left, right = command["left"], command["right"]
            self.term(left, closed=True)
            self.term(right, closed=True)
            require(symbol(command["variable"]), "invalid template variable")
            self.formula(command["template"])
            require(free_variables(command["template"]) <= {command["variable"]},
                    "unclosed template parameter")
            expected = ["imp", ["eq", left, right], ["imp",
                substitute_closed(command["template"], command["variable"], left),
                substitute_closed(command["template"], command["variable"], right)]]
            require(result == expected, "invalid equality-substitution tautology")
        elif rule == "mp":
            exact_keys(command, ("rule", "formula", "antecedent", "implication"), rule)
            antecedent = self.prior(command["antecedent"], formulas)
            implication = self.prior(command["implication"], formulas)
            require(implication == ["imp", antecedent, result], "invalid ordered MP")
        elif rule == "block":
            exact_keys(command, ("rule", "formula", "name", "inputs"), rule)
            require(command["name"] in self.definitions, "unavailable prior declaration")
            declaration = self.definitions[command["name"]]
            require(isinstance(command["inputs"], list), "block reference list")
            inputs = [self.prior(index, formulas) for index in command["inputs"]]
            require(inputs == declaration["premises"],
                    "ordered block arity, multiplicity or formula mismatch")
            require(result == declaration["conclusion"], "block result mismatch")
        else:
            raise Rejected("unsupported rule: " + repr(rule))
        return copy.deepcopy(result)

    def proof(self, commands, ordered_context, conclusion=None):
        require(isinstance(commands, list) and commands, "empty proof")
        for formula in ordered_context:
            self.formula(formula, closed=True)
        formulas = []
        for command in commands:
            formulas.append(self.command(command, formulas, ordered_context))
        require(conclusion is None or formulas[-1] == conclusion, "proof endpoint mismatch")
        return formulas

    def admit(self, declaration):
        exact_keys(declaration, ("name", "premises", "conclusion", "proof"), "definition")
        name = declaration["name"]
        require(symbol(name) and name not in self.definitions,
                "non-distinct declaration identity")
        require(isinstance(declaration["premises"], list), "premise list")
        self.formula(declaration["conclusion"], closed=True)
        self.proof(declaration["proof"], declaration["premises"],
                   declaration["conclusion"])
        self.definitions[name] = copy.deepcopy(declaration)
        receipt = {"name": name, "definition_sha256": digest(declaration),
                   "commands": len(declaration["proof"]),
                   "ordered_premise_occurrences": len(declaration["premises"])}
        self.definition_receipts.append(receipt)
        return receipt


def formula_registry(formulas, checker):
    require(isinstance(formulas, list), "formula registry list")
    codes = {}
    for code, formula in enumerate(formulas):
        checker.formula(formula, closed=True)
        key = canonical(formula)
        require(key not in codes, "noninjective formula registry")
        codes[key] = code
    return codes


def compile_primitive(command, row, prior_commands, codes):
    """Reconstruct every t/m value from exact command and numeric references."""
    require(integer(row) and row >= 0 and len(prior_commands) == row,
            "noncontiguous primitive row")
    require(command["rule"] in ("assumption", "axiom", "instantiate", "eq_subst", "mp"),
            "unexpanded block in primitive placement")
    require(canonical(command["formula"]) in codes, "unregistered output formula")
    values = {(1, row): codes[canonical(command["formula"])]}
    inputs = []
    if command["rule"] == "mp":
        inputs = [command["antecedent"], command["implication"]]
        for port, source in enumerate(inputs):
            require(integer(source) and 0 <= source < row, "non-prior geometric reference")
            key = canonical(prior_commands[source]["formula"])
            require(key in codes, "unregistered reference formula")
            point = (1, source)
            require(point not in values or values[point] == codes[key],
                    "internal primitive mark conflict")
            values[point] = codes[key]
            values[(2 + port, row)] = source - row
    return {"t": [[0, row, 1]], "m": [[x, y, v] for (x, y), v in sorted(values.items())],
            "ordered_inputs": inputs}


def placement_identity(placement, context, formula_codes, authority):
    """Full independent identity. Legacy printed IDs are only separate labels."""
    return {"identity_schema": "independent-full-decorated-placement-v1",
            "row": placement["row"], "command": placement["command"],
            "ordered_inputs": placement["ordered_inputs"],
            "t": placement["t"], "m": placement["m"], "context": context,
            "formula_codes": formula_codes, "source_authority": authority}


def point_union(placements, required_points=None, fixed_marks=(), exact=False):
    """All supports are checked, including marking-only points off boundary.

    Missing markings have no assignment. An explicitly assigned zero is kept.
    Capacity is one at all occupied points, not merely the required points.
    This function alone makes no logical inference or proof-validity claim.
    """
    totals, marks = {}, {}
    for placement in placements:
        seen_t, seen_m = set(), set()
        for x, y, value in placement["t"]:
            require(integer(x) and integer(y) and integer(value) and value >= 0,
                    "noninteger/negative t value")
            require((x, y) not in seen_t, "duplicate t assignment")
            seen_t.add((x, y))
            totals[(x, y)] = totals.get((x, y), 0) + value
            require(totals[(x, y)] <= 1, "t overcapacity")
        for x, y, value in placement["m"]:
            require(integer(x) and integer(y) and integer(value), "noninteger m value")
            require((x, y) not in seen_m, "duplicate m assignment")
            seen_m.add((x, y))
            require((x, y) not in marks or marks[(x, y)] == value,
                    "assigned m conflict")
            marks[(x, y)] = value
    for x, y, value in fixed_marks:
        require(integer(x) and integer(y) and integer(value), "noninteger fixed marking")
        require((x, y) not in marks or marks[(x, y)] == value, "fixed marking conflict")
        marks[(x, y)] = value
    if exact:
        require(required_points is not None, "missing exact region")
        require(isinstance(required_points, list) and all(
            isinstance(point, list) and len(point) == 2 and all(integer(x) for x in point)
            for point in required_points), "noninteger required point coordinate")
        required = {tuple(point) for point in required_points}
        require(len(required) == len(required_points), "duplicate required point")
        require(all(totals.get(point, 0) == 1 for point in required), "unfilled required point")
    return {"t": [[x, y, v] for (x, y), v in sorted(totals.items()) if v != 0],
            "m": [[x, y, v] for (x, y), v in sorted(marks.items())]}


def distinct_union(groups, identities):
    selected = {}
    for group in groups:
        for label, placement in group:
            full = identities[label]
            require(all(full[key] == placement[key] for key in
                        ("row", "command", "ordered_inputs", "t", "m")),
                    "label points to a different full decorated placement")
            require(label not in selected or selected[label][0] == full,
                    "false sharing under one label")
            selected[label] = (full, placement)
    return [entry[1] for _, entry in sorted(selected.items())]


def validate_port(port, placements, codes):
    exact_keys(port, ("high_level_port", "input_row", "reader_row", "primitive_input_port",
                     "formula_code", "receptor_mark_point", "reader_port_point",
                     "reader_port_value"), "ordered receptor port")
    source, reader, slot = port["input_row"], port["reader_row"], port["primitive_input_port"]
    require(integer(source) and integer(reader) and integer(slot)
            and 0 <= source < reader < len(placements) and slot in (0, 1),
            "invalid ordered receptor reference")
    require(integer(port["high_level_port"]) and port["high_level_port"] >= 0
            and integer(port["formula_code"]) and integer(port["reader_port_value"]),
            "noninteger port index, formula code or offset")
    require(all(isinstance(port[key], list) and len(port[key]) == 2
                and all(integer(x) for x in port[key])
                for key in ("receptor_mark_point", "reader_port_point")),
            "noninteger port coordinate")
    command = placements[reader]["command"]
    require(command["rule"] == "mp", "port reader not MP")
    actual_source = command["antecedent"] if slot == 0 else command["implication"]
    require(source == actual_source, "ordered port points to different reference")
    require(port["receptor_mark_point"] == [1, source]
            and port["reader_port_point"] == [2 + slot, reader]
            and port["reader_port_value"] == source - reader
            and port["formula_code"] == codes[canonical(placements[source]["command"]["formula"])],
            "port projection mismatch")


class ExpansionForest:
    """Literal local proof DAG first, row embedding second.

    Seed occurrence nodes are distinct even when their formulas agree. Nodes
    are interned by exact primitive payload plus ordered child *identities*,
    never by conclusions. Donor occurrence metadata is retained separately.
    This structural reconstruction does not read the producer's trace or rows.
    """
    def __init__(self, checker, ordered_context):
        self.checker = checker
        self.nodes = {}
        self.rows = []
        self.row_of = {}
        self.owners = []
        self.provenance = []
        self.trace = []
        for occurrence, formula in enumerate(ordered_context):
            key = canonical({"seed_occurrence": occurrence, "formula": formula})
            command = {"rule": "assumption", "index": occurrence, "formula": formula}
            self.nodes[key] = {"payload": command, "children": []}
            self.rows.append(key)
            self.row_of[key] = occurrence
            self.owners.append([])
            self.provenance.append([{"kind": "external_local_premise", "index": occurrence}])

    def build_tree(self, name, supplied, cluster, path, events):
        require(name in self.checker.definitions, "unknown expansion definition")
        declaration = self.checker.definitions[name]
        require([self.nodes[key]["payload"]["formula"] for key in supplied]
                == declaration["premises"], "expansion ordered interface mismatch")
        local, members = [], set()
        for index, command in enumerate(declaration["proof"]):
            event = {"cluster": cluster, "source_definition": name,
                     "source_command": index, "call_path": path}
            rule = command["rule"]
            if rule == "assumption":
                key = supplied[command["index"]]
                event.update(kind="assumption_alias", premise_index=command["index"])
            elif rule == "block":
                inputs = [local[prior] for prior in command["inputs"]]
                key, descendants = self.build_tree(command["name"], inputs, cluster,
                                                   path + [index], events)
                members |= descendants
                event.update(kind="expanded_block_call", ordered_input_nodes=inputs)
            else:
                payload = copy.deepcopy(command)
                children = []
                if rule == "mp":
                    children = [local[payload.pop("antecedent")],
                                local[payload.pop("implication")]]
                key = canonical({"primitive_payload": payload,
                                 "ordered_children": [json.loads(child) for child in children]})
                if key not in self.nodes:
                    self.nodes[key] = {"payload": payload, "children": children}
                members.add(key)
                event.update(kind="primitive_occurrence")
            require(self.nodes[key]["payload"]["formula"] == command["formula"],
                    "expanded local endpoint mismatch")
            local.append(key)
            events.append((key, event))
        require(local and self.nodes[local[-1]]["payload"]["formula"] == declaration["conclusion"],
                "expanded declaration endpoint mismatch")
        return local[-1], members

    def embed_call(self, name, input_rows, cluster):
        require(all(integer(row) and 0 <= row < len(self.rows) for row in input_rows),
                "unavailable high-level input row")
        events = []
        output, members = self.build_tree(name, [self.rows[row] for row in input_rows],
                                          cluster, [], events)
        for key, item in events:
            event = copy.deepcopy({k: v for k, v in item.items()
                                   if k != "ordered_input_nodes"})
            if item["kind"] == "primitive_occurrence":
                reused = key in self.row_of
                if not reused:
                    require(all(child in self.row_of for child in self.nodes[key]["children"]),
                            "primitive child missing before row embedding")
                    self.row_of[key] = len(self.rows)
                    self.rows.append(key)
                    self.owners.append([])
                    self.provenance.append([])
                event["kind"] = "reused_exact_primitive_placement" if reused else "primitive_body_row"
            require(key in self.row_of, "unembedded alias or block endpoint")
            row = self.row_of[key]
            event["global_row"] = row
            if item["kind"] == "expanded_block_call":
                event["ordered_inputs"] = [self.row_of[key] for key in item["ordered_input_nodes"]]
            if item["kind"] == "primitive_occurrence":
                self.provenance[row].append(copy.deepcopy(event))
                if cluster not in self.owners[row]:
                    self.owners[row].append(cluster)
            self.trace.append(event)
        return self.row_of[output], sorted(self.row_of[key] for key in members)

    def commands(self):
        commands = []
        for key in self.rows:
            node = self.nodes[key]
            command = copy.deepcopy(node["payload"])
            if command["rule"] == "mp":
                command["antecedent"], command["implication"] = [
                    self.row_of[child] for child in node["children"]]
            commands.append(command)
        return commands


def inspect_design(example, original_formula_codes, authority):
    """Prospective real-data checker. Never called by this version's CLI."""
    context = example["context"]
    exact_keys(context, ("theory", "ordered_local_premises"), "recipient context")
    require(example["context_id"] == digest(context), "context ID mismatch")
    checker = SymbolicChecker(context["theory"])
    for source in example["source_bodies"]:
        declaration = source["definition"]
        require(source["name"] == declaration["name"]
                and source["definition_sha256"] == digest(declaration)
                and source["body_sha256"] == digest({key: value for key, value
                    in declaration.items() if key != "name"}),
                "source declaration/body digest mismatch")
        checker.admit(declaration)
    formulas = example["formula_codes"]
    require(formulas[:len(original_formula_codes)] == original_formula_codes
            and example["original_code_prefix_count"] == len(original_formula_codes),
            "formula registry prefix mismatch")
    codes = formula_registry(formulas, checker)
    require(example["new_intermediate_codes"] == len(formulas) - len(original_formula_codes),
            "new formula-code count mismatch")
    placements = example["primitive_placements"]
    ordered_context = context["ordered_local_premises"]
    commands = []
    full_identities = {}
    for row, placement in enumerate(placements):
        require(integer(placement["row"]) and placement["row"] == row,
                "primitive row ordering mismatch")
        command = placement["command"]
        checker.command(command, [c["formula"] for c in commands], ordered_context)
        expected = compile_primitive(command, row, commands, codes)
        require(all(placement[key] == value for key, value in expected.items()),
                "t/m primitive compilation mismatch")
        legacy = "primitive-" + digest({"command": command, "context_id": example["context_id"]}) + "@" + str(row)
        require(placement["id"] == legacy and legacy not in full_identities,
                "legacy ID recipe or uniqueness mismatch")
        full_identities[legacy] = placement_identity(placement, context, formulas, authority)
        commands.append(copy.deepcopy(command))
    require(len(ordered_context) <= len(placements), "missing local seed rows")
    for index, premise in enumerate(ordered_context):
        require(commands[index] == {"rule": "assumption", "index": index, "formula": premise},
                "ordered seed occurrence mismatch")
    for command in commands[len(ordered_context):]:
        require(command["rule"] != "assumption", "undeclared extra seed placement")
    forest = ExpansionForest(checker, ordered_context)
    independent_member_rows = []
    for cluster in example["clusters"]:
        output_row, member_rows = forest.embed_call(cluster["source_definition"],
            cluster["ordered_inputs"], cluster["name"])
        require(output_row == cluster["conclusion_row"], "literal expansion endpoint row mismatch")
        independent_member_rows.append(member_rows)
    require(forest.commands() == commands, "complete literal expansion commands mismatch")
    require(forest.trace == example["expansion_trace"], "complete expansion occurrence trace mismatch")
    require(forest.owners == [p["cluster_owners"] for p in placements]
            and forest.provenance == [p["source_provenance"] for p in placements],
            "primitive owner/alias provenance mismatch")
    by_label = {p["id"]: p for p in placements}
    groups = []
    for cluster_number, cluster in enumerate(example["clusters"]):
        ids = cluster["constituent_ids"]
        require(len(ids) == len(set(ids)) and all(label in by_label for label in ids),
                "invalid constituent set")
        members = [by_label[label] for label in ids]
        require(sorted(p["row"] for p in members) == cluster["distinct_rows"],
                "cluster rows mismatch")
        require(cluster["distinct_rows"] == independent_member_rows[cluster_number],
                "literal expansion member-set mismatch")
        aggregate = point_union(members)
        require(cluster["t"] == aggregate["t"] and cluster["m"] == aggregate["m"],
                "cluster aggregate mismatch")
        require(cluster["source_definition"] in checker.definitions,
                "unknown source interface")
        declaration = checker.definitions[cluster["source_definition"]]
        input_rows = cluster["ordered_inputs"]
        require([SymbolicChecker.prior(index, [c["formula"] for c in commands])
                 for index in input_rows] == declaration["premises"],
                "cluster interface ordered premises mismatch")
        require(commands[cluster["conclusion_row"]]["formula"] == declaration["conclusion"],
                "cluster endpoint mismatch")
        ports = cluster["ordered_receptor_ports"]
        require([p["high_level_port"] for p in ports] == list(range(len(input_rows)))
                and [p["input_row"] for p in ports] == input_rows,
                "receptor occurrence order/multiplicity mismatch")
        for port in ports:
            validate_port(port, placements, codes)
        groups.append([(label, by_label[label]) for label in ids])
    inference_union = distinct_union(groups, full_identities)
    composition = example["composition"]
    require(len(groups) == 2, "this prospective checker requires exactly two displayed clusters")
    first_rows, second_rows = map(set, independent_member_rows)
    shared_rows = sorted(first_rows & second_rows)
    require(composition["shared_rows"] == shared_rows
            and composition["shared_constituent_ids"] == [placements[row]["id"] for row in shared_rows],
            "shared-row/identity census mismatch")
    counts = {"first_cluster_units": len(first_rows), "second_cluster_units": len(second_rows),
              "naive_addition_units": len(first_rows) + len(second_rows),
              "distinct_union_units": len(first_rows | second_rows),
              "second_new_units_after_first": len(second_rows - first_rows)}
    require(all(integer(composition[key]) and composition[key] == value
                for key, value in counts.items()), "aggregate unit census mismatch")
    require(composition["first_output_is_second_input"] is True
            and integer(composition["second_incidence_port_uses_row"])
            and composition["second_incidence_port_uses_row"] == example["clusters"][0]["conclusion_row"]
            and example["clusters"][1]["ordered_inputs"][1] == example["clusters"][0]["conclusion_row"],
            "displayed cluster continuation mismatch")
    actual = point_union(inference_union)
    require(composition["derived_aggregate"]["t"] == actual["t"]
            and composition["derived_aggregate"]["m"] == actual["m"],
            "composition union mismatch")
    boundary = example["declared_example_boundary"]
    require(integer(boundary["rows"]) and boundary["rows"] == len(placements)
            and boundary["required"] == [[0, row] for row in range(len(placements))]
            and all(all(integer(v) for v in point) for point in boundary["root_generations"])
            and boundary["root_generations"] == [[0, row, 0] for row in range(len(placements))]
            and integer(boundary["premise_seed_generation"]) and boundary["premise_seed_generation"] == 0
            and boundary["initially_selected_premise_placements"] == [
                placements[row]["id"] for row in range(len(ordered_context))]
            and boundary["orientation"] == "identity", "declared point boundary/seed mismatch")
    exact = point_union(placements, boundary["required"], boundary["fixed_target_m"], exact=True)
    require(composition["full_with_premise_seeds"]["t"] == exact["t"]
            and composition["full_with_premise_seeds"]["m"] == exact["m"],
            "full primitive region mismatch")
    return {"status": "static_symbolic_and_point_check_only",
            "definitions": checker.definition_receipts,
            "primitive_rows": len(placements), "formula_codes": len(formulas),
            "full_identity_sha256": digest(full_identities),
            "native_correspondence": "open", "complete_candidate_graph": "not checked",
            "expansion_occurrences": len(forest.trace),
            "expansion_occurrence_correspondence": "complete literal tree/row comparison",
            "identity_scope": "legacy labels unchanged; full t/m, registry and common authority pinned externally"}


def rejected(call):
    try:
        call()
    except Rejected as failure:
        return str(failure)
    raise AssertionError("corrupt fixture accepted")


def fixtures():
    """Tiny authored fixture data; these are test inputs, not target proofs."""
    constant = lambda name: ["fun", name, []]
    point = lambda term: ["pred", "Point", [term]]
    line = lambda term: ["pred", "Line", [term]]
    a, b, c = point(constant("P")), line(constant("l")), point(constant("Q"))
    universal = ["all", "x", point(["var", "x"])]
    theory = {"functions": {"P": 0, "Q": 0, "l": 0},
              "predicates": {"Point": 1, "Line": 1},
              "axioms": {"toy-universal": universal}, "schemas": []}
    context = [a, a, ["imp", a, b]]
    commands = [{"rule": "assumption", "index": i, "formula": copy.deepcopy(f)}
                for i, f in enumerate(context)] + [
        {"rule": "mp", "antecedent": 0, "implication": 2, "formula": b},
        {"rule": "mp", "antecedent": 1, "implication": 2, "formula": b}]
    return {"theory": theory, "ordered_context": context, "commands": commands,
            "formulas": [a, ["imp", a, b], b, c, universal],
            "repeated_interface": {"name": "repeated", "premises": [a, a],
                "conclusion": a, "proof": [
                    {"rule": "assumption", "index": 0, "formula": a},
                    {"rule": "assumption", "index": 1, "formula": a}]}}


def run_fixtures(data):
    checker = SymbolicChecker(data["theory"])
    commands = data["commands"]
    context = data["ordered_context"]
    checker.proof(commands, context)
    codes = formula_registry(data["formulas"], checker)
    placements = [{"row": row, "command": copy.deepcopy(command),
                   **compile_primitive(command, row, commands[:row], codes)}
                  for row, command in enumerate(commands)]
    results = []

    def passed(name, **facts):
        results.append({"name": name, "status": "passed", **facts})

    point_union(placements, [[0, i] for i in range(5)], exact=True)
    passed("valid_ordered_MP_and_points", primitive_rows=5)
    authority = {"kind": "toy_symbolic_axioms", "sha256": digest(data["theory"])}
    identities = [placement_identity(p, {"theory": data["theory"],
                    "ordered_local_premises": context}, data["formulas"], authority)
                  for p in placements]
    require(identities[0] != identities[1] and identities[3] != identities[4],
            "same formula merged distinct decorated identity")
    passed("same_formula_distinct_seed_and_MP_identities",
           seed_identity_sha256=[digest(identities[0]), digest(identities[1])],
           MP_identity_sha256=[digest(identities[3]), digest(identities[4])])

    bad_commands = copy.deepcopy(commands)
    bad_commands[3]["formula"] = data["formulas"][3]
    bad_placements = [{"row": row, "command": command,
                       **compile_primitive(command, row, bad_commands[:row], codes)}
                      for row, command in enumerate(bad_commands)]
    point_union(bad_placements, [[0, i] for i in range(5)], exact=True)
    message = rejected(lambda: checker.proof(bad_commands, context))
    passed("point_consistent_invalid_inference", point_consistency=True,
           symbolic_acceptance=False, rejection=message,
           exact_corrupt_commands=bad_commands, exact_corrupt_placements=bad_placements)

    checker.admit(data["repeated_interface"])
    repeated = {"rule": "block", "name": "repeated", "inputs": [0, 0],
                "formula": context[0]}
    checker.command(repeated, [context[0]], context)
    collapsed = {**repeated, "inputs": [0]}
    passed("repeated_ordered_port_multiplicity", actual_input_occurrences=[0, 0],
           rejection=rejected(lambda: checker.command(collapsed, [context[0]], context)))
    paired = {"name": "paired_MP", "premises": context,
              "conclusion": commands[-1]["formula"], "proof": commands}
    checker.admit(paired)
    forest = ExpansionForest(checker, context)
    endpoint, members = forest.embed_call("paired_MP", [0, 1, 2], "first")
    require(endpoint == 4 and members == [3, 4] and forest.commands() == commands,
            "toy DAG/row reconstruction mismatch")
    endpoint2, members2 = forest.embed_call("paired_MP", [0, 1, 2], "second")
    require(endpoint2 == 4 and members2 == [3, 4] and len(forest.rows) == 5,
            "toy duplicate primitive interning mismatch")
    alias_output, alias_members = forest.embed_call("repeated", [0, 0], "alias-only")
    require(alias_output == 0 and alias_members == [] and len(forest.rows) == 5,
            "ordered local alias introduced occupancy")
    passed("literal_DAG_expansion_and_zero_occupancy_seed_alias",
           inference_members=[3, 4], shared_identical_members=[3, 4],
           alias_endpoint=0, alias_new_occupancy=0,
           trace_occurrences=len(forest.trace))

    universal = data["formulas"][4]
    good_inst = {"rule": "instantiate", "universal": universal,
                 "term": ["fun", "P", []], "formula": ["imp", universal, context[0]]}
    checker.command(good_inst, [], [])
    open_inst = {**good_inst, "term": ["var", "x"]}
    wrong_inst = {**good_inst, "formula": ["imp", universal, data["formulas"][2]]}
    passed("instantiation_closed_term_and_exact_substitution",
           open_term_rejection=rejected(lambda: checker.command(open_inst, [], [])),
           wrong_formula_rejection=rejected(lambda: checker.command(wrong_inst, [], [])))

    left, right = ["fun", "P", []], ["fun", "Q", []]
    shadow = ["all", "x", ["pred", "Point", [["var", "x"]]]]
    require(substitute_closed(shadow, "x", left) == shadow, "binder shadow changed")
    template = ["all", "y", ["eq", ["var", "x"], ["var", "y"]]]
    target_template = ["all", "y", ["eq", left, ["var", "y"]]]
    require(substitute_closed(template, "x", left) == target_template,
            "closed replacement or nested binder mismatch")
    eq = {"rule": "eq_subst", "left": left, "right": right,
          "template": template, "variable": "x", "formula": ["imp", ["eq", left, right],
              ["imp", target_template, substitute_closed(template, "x", right)]]}
    checker.command(eq, [], [])
    unsupported = {**eq, "template": ["eq", ["var", "x"], ["var", "z"]]}
    captured = {**eq, "left": ["var", "y"]}
    passed("substitution_scope_shadow_and_capture_fail_closed",
           extra_parameter_rejection=rejected(lambda: checker.command(unsupported, [], [])),
           capture_replacement_rejection=rejected(lambda: checker.command(captured, [], [])))

    slot = {"high_level_port": 0, "input_row": 0, "reader_row": 3, "primitive_input_port": 0,
            "formula_code": codes[canonical(context[0])], "receptor_mark_point": [1, 0],
            "reader_port_point": [2, 3], "reader_port_value": -3}
    validate_port(slot, placements, codes)
    bad_slot = {**slot, "primitive_input_port": 1, "reader_port_point": [3, 3]}
    passed("ordered_reference_port", rejection=rejected(
        lambda: validate_port(bad_slot, placements, codes)))
    nonprior = {**commands[3], "antecedent": 3}
    passed("strict_prior_reference", rejection=rejected(
        lambda: checker.command(nonprior, [c["formula"] for c in commands[:3]], context)))

    shared = copy.deepcopy(placements[3])
    member_groups = [[("same", shared)], [("same", shared)]]
    union = distinct_union(member_groups, {"same": identities[3]})
    require(len(union) == 1, "shared identity counted twice")
    point_union(union)
    passed("shared_set_union_versus_naive_t_addition", distinct_count=1,
           naive_rejection=rejected(lambda: point_union([shared, shared])))
    passed("label_false_sharing_rejected", rejection=rejected(lambda: distinct_union(
        [[("same", placements[3])], [("same", placements[4])]], {"same": identities[3]})))
    try:
        require(identities[3] == identities[4], "same formula is not decorated identity")
    except Rejected as failure:
        passed("formula_only_false_sharing", rejection=str(failure))
    else:
        raise AssertionError("false sharing identity accepted")

    zero = {"t": [[0, 0, 1]], "m": [[100, 100, 0]]}
    absent = {"t": [[0, 1, 1]], "m": []}
    one = {"t": [[0, 2, 1]], "m": [[100, 100, 1]]}
    actual = point_union([zero, absent])
    require([100, 100, 0] in actual["m"], "assigned zero lost")
    passed("absence_is_not_assigned_zero_and_all_support_checked",
           compatible_absence=True, preserved_assignment=[100, 100, 0],
           exterior_conflict_rejection=rejected(lambda: point_union([zero, absent, one])))

    passed("formula_registry_injectivity", rejection=rejected(
        lambda: formula_registry(data["formulas"] + [context[0]], checker)))
    wrong_axiom = {"rule": "axiom", "name": "toy-universal", "formula": context[0]}
    passed("exact_named_axiom", rejection=rejected(lambda: checker.command(wrong_axiom, [], [])))
    passed("unsupported_quantifier_feature", rejection=rejected(
        lambda: checker.formula(["ex", "x", context[0]])))
    passed("declared_predicate_arity", rejection=rejected(
        lambda: checker.formula(["pred", "Point", []])))
    bool_theory = copy.deepcopy(data["theory"])
    bool_theory["functions"]["P"] = False
    passed("bool_function_arity_rejected", rejection=rejected(
        lambda: SymbolicChecker(bool_theory)))
    bool_mark = {"t": [[0, 0, 1]], "m": [[1, 0, False]]}
    passed("bool_assigned_mark_rejected", rejection=rejected(lambda: point_union([bool_mark])))
    passed("bool_fixed_mark_and_required_coordinate_rejected",
           fixed_mark_rejection=rejected(lambda: point_union([], fixed_marks=[[1, 0, False]])),
           required_rejection=rejected(lambda: point_union([], [[False, 0]], exact=True)))
    bool_port = {**slot, "formula_code": False}
    passed("bool_port_formula_code_rejected", rejection=rejected(
        lambda: validate_port(bool_port, placements, codes)))
    cycle = {"name": "cycle", "premises": [], "conclusion": context[0],
             "proof": [{"rule": "block", "name": "cycle", "inputs": [], "formula": context[0]}]}
    passed("cyclic_or_forward_block_unavailable", rejection=rejected(lambda: checker.admit(cycle)))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--toy-plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    began = time.perf_counter()
    plan_path = Path(args.toy_plan)
    plan = json.loads(plan_path.read_bytes())
    require(plan["scope"] == "bounded_toy_fixtures_only_no_real_design_validation", "toy gate scope")
    for item in plan["pins"]:
        path = Path(item["path"])
        require(hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"],
                "toy gate pin mismatch: " + str(path))
    fixture_path = Path(plan["fixture_path"])
    data = json.loads(fixture_path.read_bytes())
    cap = plan["limits"]["wall_seconds"]

    def timeout(signum, frame):
        raise TimeoutError("bounded toy gate timeout")

    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, cap)
    result = {"plan_sha256": hashlib.sha256(plan_path.read_bytes()).hexdigest(),
              "scope": plan["scope"], "no_project_imports": True,
              "native_queries": 0, "search_runs": 0, "solver_runs": 0}
    try:
        result["fixtures"] = run_fixtures(data)
        result["status"] = "passed_bounded_toy_fixtures_only"
    except Exception as failure:
        result["status"] = "unknown_or_failed_toy_gate"
        result["failure"] = type(failure).__name__ + ": " + str(failure)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
    elapsed = time.perf_counter() - began
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak = int(rss if sys.platform == "darwin" else rss * 1024)
    result["costs"] = {"worker_seconds_before_receipt_write": elapsed,
                       "kernel_peak_rss_bytes": peak,
                       "startup_and_final_receipt_write": "not included",
                       "authoring_preparation": "unmeasured; not zero",
                       "OS_memory_limit": "not asserted; final kernel peak gate"}
    if elapsed > cap or peak > plan["limits"]["peak_rss_bytes"]:
        result["status"] = "unknown_resource_gate"
    result["runtime"] = {"python": sys.version, "platform": platform.platform()}
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("status", "costs")}, indent=2))
    return 0 if result["status"] == "passed_bounded_toy_fixtures_only" else 1


if __name__ == "__main__":
    raise SystemExit(main())
