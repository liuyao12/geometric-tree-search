"""SOURCE ONLY independent tiny wire/point/feature reference, never imported.

No producer, decoder, graph, lifecycle, features or checker imports are used.
The reference interprets the separately pinned literal synthetic declaration.
Its complete small relations are implementation controls, not theorem admission,
an alternate authored proof, a production grammar reduction or learner data.
"""
from __future__ import annotations
import copy
import gzip
import hashlib
import io
import itertools
import json
import struct
from pathlib import Path

FEATURES = ('bias', 'null', 'ready', 'waiting', 'pair', 'member_fraction',
    'pending_member_fraction', 'selected_member_fraction', 'completed_selected_member_fraction',
    'shared_occurrence_fraction', 'eligible_domain_fraction', 'receptor_fraction',
    'completed_receptor_fraction', 'pending_receptor_fraction', 'repeated_receptor_fraction',
    'earlier_component_receptor_fraction', 'source_gap_mean', 'source_gap_max',
    'assigned_aggregate_mark_fraction', 'free_aggregate_mark_fraction', 'remote_aggregate_mark_fraction',
    'aggregate_span_fraction', 'constrained_pending_output_fraction', 'novel_component_output_fraction',
    'receptor_head_eq_fraction', 'receptor_head_and_fraction', 'receptor_head_pred_fraction',
    'receptor_head_all_fraction', 'pending_by_frontier', 'completed_by_frontier', 'branch_degree_inverse')


def text(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(text(value).encode('utf8')).hexdigest()


def closed_bytes(record):
    if type(record) is not dict or set(record) != {'path', 'sha256', 'bytes'}:
        raise ValueError('exact independent closed raw pin')
    path = Path(record['path'])
    if not path.is_absolute() or str(path.resolve()) != str(path):
        raise ValueError('independent raw identity is canonical ABS')
    value = path.read_bytes()
    if type(record['bytes']) is not int or len(value) != record['bytes'] or hashlib.sha256(value).hexdigest() != record['sha256']:
        raise ValueError('raw pin disagrees with closed bytes')
    return value


def reconstruct(fixture, case_id, expected_source_bindings):
    """Independently derive all tiny formulas, witnesses, context and identities."""
    if (fixture.get('schema') != 'synthetic-24row-three-occurrence-consumer-mechanism-fixture-v1'
            or fixture.get('height') != 24 or fixture.get('production_theorem_admission') is not False
            or fixture.get('proof_search_authorized') is not False or fixture.get('native_admission') is not False):
        raise ValueError('explicit tiny mechanism declaration, not production approval')
    selected = [item for item in fixture['cases'] if item['id'] == case_id]
    if len(selected) != 1:
        raise ValueError('exact independently selected tiny case')
    case = selected[0]; atoms = fixture['head_forms']; output = fixture['conclusion_form']
    if set(atoms) != {'all', 'and', 'eq', 'pred'} or case['head'] not in atoms:
        raise ValueError('all four literal head controls')
    n = case['goal_axiom_count']
    if type(n) is not int or n not in (0, 1, 2):
        raise ValueError('exact tiny boundary multiplicity')
    axioms = {'body-output': output}
    for kind in ('all', 'and', 'eq', 'pred'):
        axioms['head-' + kind] = atoms[kind]
        axioms['implication-' + kind] = ['imp', atoms[kind], output]
    for number in range(n):
        axioms['goal-' + str(number)] = fixture['boundary_target']
    theory = {'axioms': axioms, 'signature': fixture['signature'], 'axiom_schemas': {}}
    premise = atoms[case['head']]
    gamma = [premise, premise, ['imp', premise, output]]
    unique = {}
    pending = [*axioms.values(), *gamma, fixture['boundary_target']]
    while pending:
        item = pending.pop(); kind = item[0]
        if kind not in ('bot', 'eq', 'pred', 'not', 'imp', 'and', 'or', 'all'):
            raise ValueError('independent formula constructor check')
        key = text(item)
        if key in unique:
            continue
        unique[key] = item
        if kind in ('imp', 'and', 'or'):
            pending.extend(item[1:])
        elif kind in ('not', 'all'):
            pending.append(item[-1])
    formulas = [copy.deepcopy(unique[key]) for key in sorted(unique)]
    codes = {text(value): index for index, value in enumerate(formulas)}
    rows = []
    for name in sorted(axioms):
        rows.append(({'name': name, 'formula': axioms[name], 'rule': 'axiom'}, []))
    for implication in formulas:
        if implication[0] == 'imp':
            inputs = [implication[1], implication]
            if text(inputs[0]) == text(inputs[1]):
                raise ValueError('synthetic genuine MP must retain different formula codes')
            rows.append(({'formula': implication[2], 'rule': 'mp'}, inputs))
    rows.extend(({'index': index, 'formula': formula, 'rule': 'assumption'}, []) for index, formula in enumerate(gamma))
    rows = sorted(rows, key=text)
    if len({text(row) for row in rows}) != len(rows):
        raise ValueError('independent complete occurrence recipe census')
    context = {'ordered_local_premises': gamma, 'theory': theory}
    authority = {'activated': False, 'native_accepted': False,
        'recipient_theory_sha256': sha(theory), 'declaration_schema': 'fresh-ground-cluster-context-declaration-v1',
        'finite_grammar_sha256': sha(fixture['complete_tiny_grammar']),
        'source_bindings': copy.deepcopy(expected_source_bindings),
        'logical_qualification': 'pending independent synthetic mechanism fixture audit; never production theorem admission'}
    authority['epoch'] = sha(authority)
    records = []; assumed = {}
    for position, (command, premises) in enumerate(rows):
        before = {'recipe': {'primitive_witness': command, 'ordered_premise_formulas': premises},
                  'primitive_authority_epoch': authority['epoch'],
                  'recipient_theory_sha256': sha(theory),
                  'marking_version': 'injective-formula-ordered-mp-offset-v1',
                  'formula_registry_sha256': sha(formulas)}
        if command['rule'] == 'assumption':
            before['local_context_id'] = sha(context); assumed[command['index']] = position
        record = {'id': 'primitive-recipe-' + sha(before), 'primitive_witness': command,
                  'ordered_premise_formulas': premises, 'identity_preimage': before}
        records.append({'record': copy.deepcopy(record), 'output': codes[text(command['formula'])],
                        'inputs': [codes[text(formula)] for formula in premises]})
    if sorted(assumed) != [0, 1, 2]:
        raise ValueError('exact three occurrence IDs independently rebuilt')
    return {'case': copy.deepcopy(case), 'theory': copy.deepcopy(theory), 'context': copy.deepcopy(context),
            'formulas': formulas, 'recipes': records, 'authority': authority,
            'target_code': codes[text(fixture['boundary_target'])],
            'hypothesis_codes': [codes[text(formula)] for formula in gamma],
            'assumption_recipe_indices': [assumed[i] for i in range(3)]}


def audit_raw_catalog(*, fixture_pin, case_id, header_pin, expected_source_bindings):
    """Future complete tiny raw gate; no borrowed producer/decoder helper authority."""
    fixture = json.loads(closed_bytes(fixture_pin)); header = json.loads(closed_bytes(header_pin))
    header_keys = {'schema', 'declaration_schema', 'status', 'synthetic_mechanism_control',
        'production_theorem_admission', 'instance_id', 'split', 'height', 'context', 'context_id',
        'target', 'formula_registry_sha256', 'authority', 'assumption_recipe_indices',
        'hypothesis_codes', 'target_code', 'boundary', 'orientation', 'marking_version',
        'source_bindings', 'declaration_binding', 'syntax_census', 'dimensions', 'streams',
        'codec', 'bodies', 'complete_cluster_inventory', 'target_searches', 'proof_certificates',
        'RNG_draws', 'new_RL_training', 'all_five_qualification', 'native_accepted', 'scope'}
    if type(header) is not dict or set(header) != header_keys or header['scope'] != fixture['scope']:
        raise ValueError('entire explicit synthetic header shape and scope required')
    for source in expected_source_bindings:
        closed_bytes(source)
    if fixture_pin not in expected_source_bindings:
        raise ValueError('actual fixture bytes belong to exact raw authority closure')
    expected = reconstruct(fixture, case_id, expected_source_bindings)
    if (header.get('synthetic_mechanism_control') is not True
            or header.get('production_theorem_admission') is not False
            or header.get('status') != 'synthetic_complete_mechanism_fixture_pending_independent_audit_not_production'
            or header.get('instance_id') != case_id or header.get('split') != 'mechanism-control'
            or header.get('context') != expected['context'] or header.get('authority') != expected['authority']
            or header.get('source_bindings') != expected_source_bindings
            or header.get('context_id') != sha(expected['context'])
            or header.get('target') != fixture['boundary_target']
            or header.get('formula_registry_sha256') != sha(expected['formulas'])
            or header.get('target_code') != expected['target_code']
            or header.get('hypothesis_codes') != expected['hypothesis_codes']
            or header.get('assumption_recipe_indices') != expected['assumption_recipe_indices']):
        raise ValueError('full synthetic declaration/context/authority relation differs')
    if (header.get('height') != 24 or header.get('orientation') != 'identity'
            or header.get('schema') != 'fresh-ground-compact-catalog-v1'
            or header.get('declaration_schema') != 'fresh-ground-cluster-context-declaration-v1'
            or header.get('marking_version') != 'injective-formula-ordered-mp-offset-v1'
            or header.get('bodies') != [] or header.get('complete_cluster_inventory') != []
            or header.get('target_searches') != 0 or header.get('proof_certificates') != 0
            or header.get('RNG_draws') != 0 or header.get('new_RL_training') is not False
            or header.get('all_five_qualification') is not False or header.get('native_accepted') is not False):
        raise ValueError('codec shape and explicit non-scientific scope differ')
    streams = header['streams']
    if set(streams) != {'nodes', 'formulas', 'recipes'} or any(Path(p['path']).parent != Path(header_pin['path']).parent for p in streams.values()):
        raise ValueError('all three exact streams in same exclusive namespace')
    raw = {role: closed_bytes(record) for role, record in streams.items()}
    # Decode every strictly-prior DAG child independently; reject duplicate ASTs.
    decoded = []; node_rows = []
    with gzip.GzipFile(fileobj=io.BytesIO(raw['nodes']), mode='rb') as stream:
        uncompressed_nodes = stream.read(65537)
    if len(uncompressed_nodes) > 65536:
        raise ValueError('tiny literal node control exceeds declared64KiB diagnostic bound; not a production cap')
    for line in uncompressed_nodes.splitlines():
        row = json.loads(line)
        if type(row) is not list or len(row) < 2 or row[0] != len(decoded):
            raise ValueError('continuous complete node records')
        kind = row[1]; rest = row[2:]
        def prior(index):
            if type(index) is not int or not 0 <= index < len(decoded):
                raise ValueError('strict-prior raw DAG child')
            return copy.deepcopy(decoded[index])
        if kind == 'bot' and not rest:
            value = [kind]
        elif kind == 'var' and len(rest) == 1 and type(rest[0]) is str:
            value = [kind, rest[0]]
        elif kind in ('fun', 'pred') and len(rest) == 2 and type(rest[0]) is str and type(rest[1]) is list:
            value = [kind, rest[0], [prior(child) for child in rest[1]]]
        elif kind == 'all' and len(rest) == 2 and type(rest[0]) is str:
            value = [kind, rest[0], prior(rest[1])]
        elif (kind in ('eq', 'imp', 'and', 'or') and len(rest) == 2) or (kind == 'not' and len(rest) == 1):
            value = [kind, *[prior(child) for child in rest]]
        else:
            raise ValueError('raw AST constructor grammar')
        if any(text(value) == text(old) for old in decoded):
            raise ValueError('DAG must be injective, not formula-only dedup')
        decoded.append(value); node_rows.append(row)
    # Independently rebuild exact postorder expected node sequence.
    closure = []; seen = set()
    def visit(value):
        key = text(value)
        if key in seen:
            return
        if value[0] in ('fun', 'pred'):
            for child in value[2]: visit(child)
        elif value[0] == 'all':
            visit(value[2])
        elif value[0] not in ('var', 'bot'):
            for child in value[1:]: visit(child)
        seen.add(key); closure.append(copy.deepcopy(value))
    for formula in expected['formulas']: visit(formula)
    if decoded != closure:
        raise ValueError('complete deterministic node order/bijection differs')
    if len(raw['formulas']) != 8 * len(expected['formulas']):
        raise ValueError('complete formula stream size')
    formula_nodes = [struct.unpack_from('<Q', raw['formulas'], 8 * i)[0] for i in range(len(expected['formulas']))]
    if any(type(index) is not int or index >= len(decoded) for index in formula_nodes):
        raise ValueError('complete formula node index')
    if [decoded[index] for index in formula_nodes] != expected['formulas']:
        raise ValueError('every canonical formula/code must match, not samples')
    names = sorted(expected['theory']['axioms']); sentinel = (1 << 64) - 1
    rule_codes = {'axiom': 0, 'mp': 3, 'assumption': 4}; count = len(expected['recipes'])
    if len(raw['recipes']) != 152 * count:
        raise ValueError('complete152-byte recipe stream')
    for i, recipe in enumerate(expected['recipes']):
        record = recipe['record']; command = record['primitive_witness']; inputs = recipe['inputs']; output = recipe['output']
        want = (rule_codes[command['rule']], formula_nodes[output], output,
                inputs[0] if inputs else sentinel, inputs[1] if inputs else sentinel,
                sentinel, sentinel, sentinel, sentinel,
                names.index(command['name']) if command['rule'] == 'axiom' else sentinel,
                command['index'] if command['rule'] == 'assumption' else sentinel,
                bytes.fromhex(sha(record['identity_preimage'])), bytes.fromhex(sha(record)))
        if struct.unpack_from('<11Q32s32s', raw['recipes'], 152 * i) != want:
            raise ValueError('complete raw recipe command/ordered ports/identity digest differs')
        if inputs and inputs[0] == inputs[1]:
            raise ValueError('equal-code generic control must not be encoded as genuine MP')
    dimensions = {'logical_rows': 24, 'formula_count': len(expected['formulas']),
                  'primitive_license_count': count, 'non_assumption_witness_count': count - 3, 'source_body_count': 0}
    codec = {'node_count': len(decoded), 'formula_word_bytes': 8, 'byte_order': 'little',
        'recipe_row_bytes': 152, 'sentinel': sentinel,
        'rules': ['axiom', 'instantiate', 'eq_subst', 'mp', 'assumption'], 'names': names,
        'recipe_fields': ['tag', 'output_node', 'output_code', 'input0_code', 'input1_code',
            'p0', 'p1', 'p2', 'p3', 'name_index', 'occurrence_index', 'recipe_digest', 'record_digest']}
    seed_indices = expected['assumption_recipe_indices']
    boundary = {'required': [[0, row] for row in range(24)], 'root_generations': [[0, row, 0] for row in range(24)],
        'fixed_exterior_m': [[1, row, -1] for row in range(-23, 0)],
        'fixed_target_m': [[1, 23, expected['target_code']]],
        'fixed_initial_local_seeds': [{'recipe_id': expected['recipes'][seed_indices[i]]['record']['id'], 'row': i, 'generation': 0} for i in range(3)],
        'all_root_obligations_generation_zero': True}
    if header['codec'] != codec or header['dimensions'] != dimensions or header['boundary'] != boundary:
        raise ValueError('full codec/census/boundary and occurrence seeds differ')
    if header['declaration_binding'] != {'fixture_sha256': sha(fixture), 'selected_sha256': sha(expected['case']),
            'grammar_sha256': sha(fixture['complete_tiny_grammar']), 'theory_key': 'synthetic-mechanism'}:
        raise ValueError('independently reconstructed tiny declaration binding')
    if header['syntax_census'] != {'tiny_complete_axiom_count': len(expected['theory']['axioms']),
            'tiny_complete_implication_count': sum(formula[0] == 'imp' for formula in expected['formulas']),
            'universal_instantiation_recipes': 0, 'equality_substitution_recipes': 0}:
        raise ValueError('complete literal tiny grammar census')
    return expected, {'schema': 'independent-synthetic-codec-relation-v1', 'tiny_relation_pass': True,
        'case_id': case_id, 'dimensions': dimensions, 'header_pin': copy.deepcopy(header_pin),
        'fixture_pin': copy.deepcopy(fixture_pin), 'whole_stream_pins': copy.deepcopy(streams),
        'production_theorem_admission': False, 'dynamic_qualified': False, 'proof_accepted': False,
        'resource_accepted': False, 'scope': 'Future complete tiny raw relation only; ROOT still owns independent/resource admission.'}


def audit_authored_mechanism_bodies(data, bodies, draft_projection, inventory_mode):
    """Independent exact synthetic templates only; never promote receipt status.

    The caller must authenticate the raw codec relation before passing data.
    No body producer/lifecycle/proposer/checker helper is called by this oracle.
    """
    if inventory_mode not in ('ports-and-sharing', 'capacity64', 'overfull65'):
        raise ValueError('exact tiny mechanism inventory')
    head, implication = data['context']['ordered_local_premises'][0], data['context']['ordered_local_premises'][2]
    output = implication[2]
    if implication != ['imp', head, output]: raise ValueError('literal genuine MP')
    zero = [r for r in data['recipes'] if r['record']['primitive_witness'] ==
        {'rule': 'axiom', 'name': 'head-' + head[0], 'formula': head}]
    mp = [r for r in data['recipes'] if r['record']['primitive_witness'] ==
        {'rule': 'mp', 'formula': output} and r['record']['ordered_premise_formulas'] == [head, implication]]
    if len(zero) != 1 or len(mp) != 1 or mp[0]['inputs'][0] == mp[0]['inputs'][1]:
        raise ValueError('all exact independent tiny recipe witnesses')
    if inventory_mode == 'ports-and-sharing':
        declarations = [('control-replenish', [(zero[0], 2, [])]),
            ('control-MP', [(mp[0], 2, [0, 1])]),
            ('control-redundant-share', [(zero[0], 2, []), (mp[0], 3, [0, 1])])]
    else:
        declarations = [('capacity-control-' + str(i), [(zero[0], 2, [])])
                        for i in range(64 if inventory_mode == 'capacity64' else 65)]
    expected_bodies, definitions = [], []
    for name, source in declarations:
        members = [{'row': row, 'recipe_id': r['record']['id'], 'formula_code': r['output'],
                    'ordered_inputs': reads} for r, row, reads in source]
        aliases = sorted({ref for _, _, reads in source for ref in reads} - {row for _, row, _ in source})
        values = {}; ports = []
        for recipe, _, reads in source:
            for ref, code in zip(reads, recipe['inputs']):
                if ref in aliases:
                    if ref in values and values[ref] != code: raise ValueError('conflicting external alias')
                    values[ref] = code
        for index, row in enumerate(aliases):
            readers = [{'reader_row': physical_row, 'primitive_input_port': port, 'formula_code': code}
                for recipe, physical_row, reads in source
                for port, (ref, code) in enumerate(zip(reads, recipe['inputs'])) if ref == row]
            ports.append({'high_level_port': index, 'input_row': row, 'formula_code': values[row],
                          'new_occupancy': 0, 'readers': readers})
        body = {'kind': 'authored_primitive_proposal_not_closed_lemma', 'name': name,
            'canonical_input_rows': aliases, 'premise_codes': [values[row] for row in aliases],
            'primitive_members': members, 'dependency_bindings': [], 'native_accepted': False,
            'ordered_receptor_ports': ports}
        body['source_body_sha256'] = sha(body); body['mapped_body_sha256'] = body['source_body_sha256']
        conclusion = source[-1][0]['output']
        definition = {'name': name, 'canonical_input_rows': aliases, 'premise_codes': body['premise_codes'],
            'primitive_members': members, 'source_body_sha256': body['source_body_sha256'],
            'mapped_body_sha256': body['mapped_body_sha256'], 'canonical_conclusion_row': source[-1][1],
            'conclusion_code': conclusion, 'conclusion_ast': data['formulas'][conclusion],
            'premise_ast': [data['formulas'][code] for code in body['premise_codes']],
            'synthetic_mechanism_control': True, 'production_theorem_admission': False,
            'closed_lemma': False, 'automatically_discovered': False, 'native_accepted': False,
            'fixture_instance_id': data['case']['id'], 'inventory_mode': inventory_mode}
        body['full_frozen_definition_sha256'] = sha(definition)
        body['earlier_expansion_closure'] = {'kind': 'synthetic_authored_primitive_control_not_closed_proof',
            'primitive_members': members, 'recursive_named_body_dependencies': [],
            'accepted_training_proof_pins': [], 'production_theorem_admission': False}
        expected_bodies.append(body); definitions.append(definition)
    projection = {'status': 'pending_independent_synthetic_body_projection_audit_not_production',
        'native_accepted': False, 'formula_registry_sha256': sha(data['formulas']),
        'declared_source_body_count': len(expected_bodies), 'definitions': definitions,
        'synthetic_mechanism_control': True, 'production_theorem_admission': False,
        'inventory_mode': inventory_mode}
    if bodies != expected_bodies or draft_projection != projection:
        raise ValueError('entire independently reconstructed authored body/projection relation')
    return {'schema': 'independent-synthetic-authored-body-relation-v1', 'tiny_relation_pass': True,
        'declared_bodies': len(expected_bodies), 'inventory_mode': inventory_mode,
        'production_theorem_admission': False, 'resource_accepted': False, 'closed_lemma': False,
        'projection_promoted': False}


def key_tuple(value):
    if not isinstance(value, (tuple, list)) or len(value) != 3 or not isinstance(value[2], (tuple, list)):
        raise ValueError('exact full key triple')
    if any(type(v) is not int for v in [value[0], value[1], *value[2]]):
        raise ValueError('exact integer key fields')
    return value[0], value[1], tuple(value[2])


def key_data(key):
    return [key[0], key[1], list(key[2])]


class LiteralPointReference:
    """Small exhaustive point assignments; no factor/mask/cache algorithm reused."""
    def __init__(self, independently_reconstructed):
        data = copy.deepcopy(independently_reconstructed)
        self.data = data; self.recipes = data['recipes']; self.height = 24
        self.totals = [0] * 24; self.marks = {(1, row): -1 for row in range(-23, 0)}
        self.marks[1, 23] = data['target_code']; self.refs = {p: 1 for p in self.marks}
        self.selected = {}; self.order = []; self.roots = [0] * 24
        self.excluded = [set() for _ in range(24)]; self.trail = []
        for row, index in enumerate(data['assumption_recipe_indices']): self.apply((index, row, ()), generation=0)
        self.trail.clear(); self.initial = tuple(self.order)
        self.model_epoch = sha({'height': 24, 'context': data['context'], 'registry': sha(data['formulas']),
            'authority': data['authority']['epoch'], 'recipes': [r['record']['id'] for r in self.recipes],
            'fixed_marks': [[1, row, -1] for row in range(-23, 0)] + [[1, 23, data['target_code']]],
            'roots': tuple(self.roots), 'seed_keys': [key_data(k) for k in self.initial],
            'marking_version': 'injective-formula-ordered-mp-offset-v1', 'fixture': False,
            'source_bindings': data['authority']['source_bindings']})

    def point_data(self, raw_key):
        index, row, reads = key_tuple(raw_key)
        if not 0 <= index < len(self.recipes) or not 0 <= row < 24:
            raise ValueError('literal key outside complete tiny universe')
        recipe = self.recipes[index]
        if len(reads) != len(recipe['inputs']) or any(not 0 <= r < row for r in reads):
            raise ValueError('all strict-prior ordered ports')
        marks = {(1, row): recipe['output']}
        for position, (ref, code) in enumerate(zip(reads, recipe['inputs'])):
            if (1, ref) in marks and marks[1, ref] != code:
                raise ValueError('local point-value disagreement rejects unequal-input alias')
            marks[1, ref] = code; marks[2 + position, row] = ref - row
        return [[0, row, 1]], [[*p, v] for p, v in sorted(marks.items())]

    def legal(self, raw_key, *, ignore_exclusion=False):
        try:
            k = key_tuple(raw_key); points, marks = self.point_data(k)
            return (self.totals[k[1]] == 0 and (ignore_exclusion or k not in self.excluded[k[1]])
                and all((x, y) not in self.marks or self.marks[x, y] == value for x, y, value in marks))
        except (ValueError, IndexError, TypeError): return False

    def candidates(self, row, *, ignore_exclusion=False):
        values = []
        for index, recipe in enumerate(self.recipes):
            references = itertools.product(range(row), repeat=2) if recipe['inputs'] else [()]
            for reads in references:
                key = (index, row, tuple(reads))
                if self.legal(key, ignore_exclusion=ignore_exclusion): values.append(key)
        return values

    def decision(self):
        active = [(row, len(self.candidates(row))) for row in range(24) if self.totals[row] == 0]
        if not active: return ['complete', None, 0, None]
        for kind, count in (('dead', 0), ('forced', 1)):
            matches = [row for row, degree in active if degree == count]
            if matches:
                row = min(matches); return [kind, row, count, self.generation(row)]
        row, count = min(active, key=lambda pair: (self.generation(pair[0]), pair[1], pair[0]))
        return ['branch', row, count, self.generation(row)]

    def generation(self, row):
        return min([self.roots[row], *[g for key, g in self.selected.items() if key[1] == row]])

    def save(self):
        return copy.deepcopy((self.totals, self.marks, self.refs, self.selected, self.order, self.excluded))

    def apply(self, raw_key, *, generation=None):
        """Literal transaction control, not a substitute for executor scheduling."""
        key = key_tuple(raw_key)
        if not self.legal(key): raise ValueError('literal legal transaction required')
        before = self.save(); self.trail.append(before)
        self.totals[key[1]] += 1
        self.selected[key] = self.generation(key[1]) + 1 if generation is None else generation
        self.order.append(key)
        for x, y, value in self.point_data(key)[1]:
            self.marks[x, y] = value; self.refs[x, y] = self.refs.get((x, y), 0) + 1

    def exclude(self, raw_key):
        """Synthetic exclusion transaction only; not evidence of an exhausted child."""
        key = key_tuple(raw_key)
        if not self.legal(key): raise ValueError('literal restored-parent legal key')
        self.trail.append(self.save()); self.excluded[key[1]].add(key)

    def checkpoint(self): return len(self.trail)

    def rollback(self, depth):
        if type(depth) is not int or not 0 <= depth <= len(self.trail): raise ValueError('literal snapshot depth')
        while len(self.trail) > depth:
            self.totals, self.marks, self.refs, self.selected, self.order, self.excluded = self.trail.pop()

    def state(self):
        return {'totals': list(self.totals), 'marks': [[*p, v, self.refs[p]] for p, v in sorted(self.marks.items())],
            'order': [key_data(k) for k in self.order],
            'selected_generations': [[key_data(k), self.selected[k]] for k in sorted(self.selected)],
            'roots': list(self.roots), 'excluded': [[key_data(k) for k in sorted(values)] for values in self.excluded],
            'model_epoch': self.model_epoch}

    def feature_state(self):
        by_row = {key[1]: key for key in self.order}; usable = {}
        for row in sorted(by_row):
            key = by_row[row]; recipe = self.recipes[key[0]]
            if all(usable.get(ref) == code for ref, code in zip(key[2], recipe['inputs'])):
                usable[row] = recipe['output']
        roots = {self.recipes[k[0]]['output'] for k in self.initial}
        return {'selected': by_row, 'complete': usable, 'root_codes': roots,
                'distinct_nonroot_codes': set(usable.values()) - roots,
                'frontier': self.totals.count(0)}

    def decorate(self, raw_key):
        key = key_tuple(raw_key); recipe = self.recipes[key[0]]; t, m = self.point_data(key)
        witness = copy.deepcopy(recipe['record']['primitive_witness']); command = copy.deepcopy(witness)
        if recipe['inputs']:
            command['antecedent'], command['implication'] = key[2]
        prototype = {'recipe_id': recipe['record']['id'], 'primitive_witness': witness,
            'ordered_premise_formulas': recipe['record']['ordered_premise_formulas'],
            'relative_ordered_input_offsets': [r - key[1] for r in key[2]], 'orientation': 'identity',
            't': [[x, y - key[1], v] for x, y, v in t], 'm': [[x, y - key[1], v] for x, y, v in m],
            'marking_version': 'injective-formula-ordered-mp-offset-v1',
            'formula_registry_sha256': sha(self.data['formulas']), 'authority_epoch': self.data['authority']['epoch']}
        preimage = {'prototype_id': 'primitive-prototype-' + sha(prototype), 'prototype_preimage': prototype,
            'transform': [0, key[1]], 'context_id': sha(self.data['context']), 'ordered_input_rows': list(key[2]),
            'primitive_command': command, 't': t, 'm': m, 'authority_epoch': self.data['authority']['epoch'],
            'formula_registry_sha256': sha(self.data['formulas'])}
        return {'id': 'aggregate-primitive-' + sha(preimage), 'identity_preimage': preimage,
                'key': key_data(key), 'command': command, 't': t, 'm': m}


class LiteralLifecycleReference:
    """Independent whole literal revalidation and paired snapshot semantics.

    The descriptor registry must first be independently admitted from all tiny
    authored body templates and full single/pair enumeration. This class checks
    every primitive identity/t/m and current remote point effect; it does not
    elevate a caller-supplied registry into complete or logical authority.
    """
    def __init__(self, point_reference, admitted_descriptors):
        if type(admitted_descriptors) not in (list, tuple) or len(admitted_descriptors) > 64:
            raise ValueError('full tiny64 capacity, never truncate65')
        self.point = point_reference
        self.descriptors = [copy.deepcopy(item) for _, item in sorted(enumerate(admitted_descriptors),
            key=lambda pair: (pair[1]['fixed_priority'], pair[0]))]
        if len({d['descriptor_id'] for d in self.descriptors}) != len(self.descriptors):
            raise ValueError('distinct whole source descriptor identities')
        self.hints = [{'status': 'waiting', 'reason': None, 'eligible': [],
                       'decision': ['unresolved', None, 0, None], 'revision': 0} for _ in self.descriptors]
        self.revision = 0; self.trail = []
        self.resync(); self.trail.clear()

    def view(self, descriptor, decision):
        keys = [key_tuple(k) for k in descriptor['members']]
        if len(keys) != len(set(keys)):
            raise ValueError('complete whole union has distinct physical members')
        decoded = [self.point.decorate(k) for k in keys]
        if descriptor['full_member_ids'] != [item['id'] for item in decoded]:
            raise ValueError('every source member full identity independently reconstructed')
        t, marks = {}, {}
        for item in decoded:
            for x, y, value in item['t']: t[x, y] = t.get((x, y), 0) + value
            for x, y, value in item['m']:
                if (x, y) in marks and marks[x, y] != value: raise ValueError('literal inconsistent union')
                marks[x, y] = value
        if descriptor['aggregate_t'] != [[*p, v] for p, v in sorted(t.items())] or any(v > 1 for v in t.values()):
            raise ValueError('exact primitive positive-support union')
        # Root/output receptor reads are already present in the primitive union;
        # validate every projected ordered reader without adding hypotheses.
        for component in descriptor['components']:
            for port in component['ordered_receptor_ports']:
                if port['new_occupancy'] != 0: raise ValueError('receptor cannot seed occupancy')
                point = (1, port['input_row']); code = port['formula_code']
                if point not in marks or marks[point] != code: raise ValueError('complete receptor marking matches primitive read')
                for reader in port['readers']:
                    row = reader['reader_row']; position = reader['primitive_input_port']
                    matches = [k for k in keys if k[1] == row]
                    if (len(matches) != 1 or position not in (0, 1)
                            or matches[0][2][position] != port['input_row']
                            or self.point.recipes[matches[0][0]]['inputs'][position] != code
                            or reader['formula_code'] != code
                            or reader['offset_value'] != port['input_row'] - row):
                        raise ValueError('all ordered port/reader offsets and aliases independently checked')
        if descriptor['aggregate_m'] != [[*p, v] for p, v in sorted(marks.items())]:
            raise ValueError('every distant aggregate marking, no extra/missing point')
        reason = None; pending = []; extra = {}
        for key, identity in zip(keys, descriptor['full_member_ids']):
            if key in self.point.selected:
                if self.point.decorate(key)['id'] != identity: reason = 'selected_identity_mismatch'; break
                continue
            if not self.point.legal(key): reason = 'pending_member_illegal'; break
            pending.append(key)
            for x, y, value in self.point.point_data(key)[0]:
                extra[x, y] = extra.get((x, y), 0) + value
                if self.point.totals[y] + extra[x, y] > 1: reason = 'pending_aggregate_overcapacity'; break
            if reason is not None: break
        if reason is None:
            for x, y, value in descriptor['aggregate_m']:
                if (x, y) in self.point.marks and self.point.marks[x, y] != value:
                    reason = 'aggregate_remote_mark_conflict'; break
        if reason is not None:
            status, eligible = 'retired', []
        elif not pending:
            status, eligible = 'consumed', []
        else:
            eligible = [key_data(k) for k in pending if decision[0] == 'branch' and k[1] == decision[1]]
            status = 'ready' if eligible else 'waiting'
        return {'status': status, 'reason': reason, 'eligible': eligible,
                'decision': list(decision), 'revision': self.revision}

    def resync(self, decision=None):
        decision = self.point.decision() if decision is None else decision
        self.trail.append(('revision', self.revision)); self.revision += 1
        for index, descriptor in enumerate(self.descriptors):
            old = self.hints[index]
            if old['status'] == 'retired':
                new = {'status': 'retired', 'reason': old['reason'], 'eligible': [],
                       'decision': list(decision), 'revision': self.revision}
            else: new = self.view(descriptor, decision)
            if old != new:
                self.trail.append(('state', index, copy.deepcopy(old))); self.hints[index] = new
        return decision

    def checkpoint(self):
        return self.point.checkpoint(), len(self.trail), self.revision

    def rollback(self, checkpoint):
        point_depth, depth, revision = checkpoint; self.point.rollback(point_depth)
        if type(depth) is not int or not 0 <= depth <= len(self.trail): raise ValueError('literal paired depth')
        while len(self.trail) > depth:
            item = self.trail.pop()
            if item[0] == 'revision': self.revision = item[1]
            else: self.hints[item[1]] = item[2]
        if self.revision != revision: raise ValueError('literal revision rollback')

    def ordered(self, decision):
        self.resync(decision); base = self.point.candidates(decision[1])
        preferred = [key_tuple(k) for hint in self.hints if hint['status'] == 'ready' for k in hint['eligible']]
        if decision[0] == 'forced': preferred = []
        if any(k not in base for k in preferred): raise ValueError('literal preference remains in complete chosen domain')
        seen = set(); result = []
        for key in preferred + base:
            if key not in seen: seen.add(key); result.append(key)
        return result


def literal_feature_menu(reference, descriptors, hints, decision):
    """Independent scalar definitions for all31 features; never call borrowed features."""
    if decision[0] != 'branch' or len(descriptors) != len(hints):
        raise ValueError('complete branch menu and hints required')
    state = reference.feature_state(); selected = state['selected']; complete = state['complete']
    records = {record['descriptor_id']: (record, hint) for record, hint in zip(descriptors, hints)}
    if len(records) != len(descriptors): raise ValueError('every distinct whole descriptor retained')
    ids = sorted(['NULL'] + [name for name, (_, hint) in records.items() if hint['status'] in ('ready', 'waiting')])
    def divide(a, b): return a / max(1, b)
    vectors = []
    for name in ids:
        vector = {field: 0.0 for field in FEATURES}
        if name == 'NULL':
            vector['null'] = 1.0; vectors.append(vector); continue
        descriptor, hint = records[name]; members = [key_tuple(k) for k in descriptor['members']]
        components = descriptor['components']; pending = [k for k in members if k[1] not in selected]
        eligible = [key_tuple(k) for k in hint['eligible']]
        if len(members) != len(set(members)) or any(k not in pending or k[1] != decision[1] for k in eligible):
            raise ValueError('whole union and exact pending chosen-row eligibility')
        occupied = [k for k in members if k[1] in selected]
        if any(selected[k[1]] != k for k in occupied): raise ValueError('exact selected-key identity, not same formula')
        ports = [port for component in components for port in component['ordered_receptor_ports']]
        tokens = [token for component in components for token in component['ordered_input_bindings']]
        if len(ports) != len(tokens): raise ValueError('all ordered receptor occurrences')
        rows = [port['input_row'] for port in ports]; codes = [port['formula_code'] for port in ports]
        heads = [reference.data['formulas'][code][0] for code in codes]
        gaps = [k[1] - r for k in members for r in k[2]]
        marks = descriptor['aggregate_m']; assigned = sum((x, y) in reference.marks for x, y, _ in marks)
        if any((x, y) in reference.marks and reference.marks[x, y] != value for x, y, value in marks):
            raise ValueError('remote conflict cannot enter a feature menu')
        remote = sum(y not in {k[1] for k in members} for _, y, _ in marks)
        receptor_done = sum(complete.get(row) == code for row, code in zip(rows, codes))
        count = len(members); port_count = len(ports); occurrences = descriptor['component_member_occurrences']
        shared = descriptor['shared_member_count']; h = 24
        if shared != occurrences - count: raise ValueError('full occurrence/deduplicated union relation')
        vector.update({'bias': 1.0, 'ready': float(hint['status'] == 'ready'), 'waiting': float(hint['status'] == 'waiting'),
            'pair': float(len(components) == 2), 'member_fraction': divide(count, h),
            'pending_member_fraction': divide(len(pending), count), 'selected_member_fraction': divide(len(occupied), count),
            'completed_selected_member_fraction': divide(sum(k[1] in complete for k in occupied), count),
            'shared_occurrence_fraction': divide(shared, occurrences), 'eligible_domain_fraction': divide(len(hint['eligible']), decision[2]),
            'receptor_fraction': divide(port_count, 2 * h), 'completed_receptor_fraction': divide(receptor_done, port_count),
            'pending_receptor_fraction': divide(port_count - receptor_done, port_count),
            'repeated_receptor_fraction': divide(port_count - len(set(rows)), port_count),
            'earlier_component_receptor_fraction': divide(sum(t['kind'] == 'earlier_component_output' for t in tokens), port_count),
            'source_gap_mean': divide(sum(gaps), len(gaps) * h), 'source_gap_max': divide(max(gaps, default=0), h),
            'assigned_aggregate_mark_fraction': divide(assigned, len(marks)), 'free_aggregate_mark_fraction': divide(len(marks) - assigned, len(marks)),
            'remote_aggregate_mark_fraction': divide(remote, len(marks)),
            'aggregate_span_fraction': divide(max((m[1] for m in marks), default=0) - min((m[1] for m in marks), default=0), 2 * h),
            'constrained_pending_output_fraction': divide(sum((1, k[1]) in reference.marks for k in pending), max(1, len(pending))),
            'novel_component_output_fraction': divide(sum(c['conclusion_code'] not in set(complete.values()) for c in components), len(components)),
            'pending_by_frontier': divide(len(pending), count) * divide(state['frontier'], h),
            'completed_by_frontier': divide(receptor_done, port_count) * divide(state['frontier'], h),
            'branch_degree_inverse': 1.0 / (1.0 + decision[2])})
        for kind in ('eq', 'and', 'pred', 'all'):
            vector['receptor_head_' + kind + '_fraction'] = divide(heads.count(kind), port_count)
        if set(vector) != set(FEATURES) or any(not 0.0 <= value <= 1.0 for value in vector.values()):
            raise ValueError('independent all31 scalar range')
        vectors.append(vector)
    return {'action_ids': ids, 'feature_vectors': vectors, 'available_rows': sorted(complete),
            'maximum_fact_potential': len(state['distinct_nonroot_codes']), 'features_version': 'family-graph-receptor-features-v1'}
