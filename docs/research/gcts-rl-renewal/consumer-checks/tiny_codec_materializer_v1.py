"""SOURCE ONLY synthetic codec materializer; no project imports, CLI or worker.

No author has invoked this module. ROOT may separately review/admit a bounded
future serialization phase. The borrowed wire schema is required to exercise
the frozen decoder/24-row constructor. It does not confer the production
nine-context grammar, a theorem, a mined lemma or training/evaluation authority.
"""
from __future__ import annotations
import copy
import gzip
import hashlib
import json
import struct
from pathlib import Path

SCHEMA = 'synthetic-24row-three-occurrence-consumer-mechanism-fixture-v1'
WIRE = 'fresh-ground-compact-catalog-v1'
DECLARATION = 'fresh-ground-cluster-context-declaration-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'
RULES = ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
SENTINEL = (1 << 64) - 1
ROW = struct.Struct('<11Q32s32s')
WORD = struct.Struct('<Q')
FIELDS = ['tag', 'output_node', 'output_code', 'input0_code', 'input1_code',
          'p0', 'p1', 'p2', 'p3', 'name_index', 'occurrence_index',
          'recipe_digest', 'record_digest']


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def read_pin(pin):
    if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
            or type(pin['path']) is not str or type(pin['sha256']) is not str
            or type(pin['bytes']) is not int or pin['bytes'] < 0):
        raise ValueError('complete raw closed pin required')
    path = Path(pin['path'])
    if not path.is_absolute() or str(path.resolve()) != str(path):
        raise ValueError('synthetic raw pins use canonical ABS path identity')
    data = path.read_bytes()
    if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
        raise ValueError('closed synthetic fixture/source bytes changed')
    return data


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(data).hexdigest(),
            'bytes': len(data)}


def select_declaration(fixture, instance_id):
    """Only the explicitly declared complete tiny grammar, never a production subset."""
    if (fixture['schema'] != SCHEMA or fixture['height'] != 24
            or fixture['orientation'] != 'identity' or fixture['marking_version'] != MARKING
            or fixture['production_theorem_admission'] is not False
            or fixture['proof_search_authorized'] is not False
            or fixture['native_admission'] is not False):
        raise ValueError('synthetic mechanism scope must stay explicit')
    cases = [case for case in fixture['cases'] if case['id'] == instance_id]
    if len(cases) != 1:
        raise ValueError('one exact declared synthetic case')
    case = copy.deepcopy(cases[0]); forms = fixture['head_forms']
    if set(forms) != {'pred', 'eq', 'and', 'all'} or case['head'] not in forms:
        raise ValueError('all four exact feature-head controls required')
    if type(case['goal_axiom_count']) is not int or case['goal_axiom_count'] not in (0, 1, 2):
        raise ValueError('exact prospective synthetic boundary degree control')
    conclusion = fixture['conclusion_form']; target = fixture['boundary_target']
    axioms = {'body-output': copy.deepcopy(conclusion)}
    for name, formula in sorted(forms.items()):
        axioms['head-' + name] = copy.deepcopy(formula)
        axioms['implication-' + name] = ['imp', copy.deepcopy(formula), copy.deepcopy(conclusion)]
    for occurrence in range(case['goal_axiom_count']):
        axioms['goal-' + str(occurrence)] = copy.deepcopy(target)
    head = copy.deepcopy(forms[case['head']])
    theory = {'axioms': axioms, 'axiom_schemas': {},
              'signature': copy.deepcopy(fixture['signature'])}
    hypotheses = [head, copy.deepcopy(head), ['imp', copy.deepcopy(head), copy.deepcopy(conclusion)]]
    return case, theory, hypotheses, copy.deepcopy(target)


def all_subformulas(formulas):
    result = {}
    def visit(formula):
        tag = formula[0]
        if tag not in ('bot', 'pred', 'eq', 'not', 'imp', 'and', 'or', 'all'):
            raise ValueError('literal synthetic formula constructor')
        result[canonical(formula)] = copy.deepcopy(formula)
        if tag in ('not', 'all'):
            visit(formula[-1])
        elif tag in ('imp', 'and', 'or'):
            visit(formula[1]); visit(formula[2])
    for formula in formulas:
        visit(formula)
    return [result[text] for text in sorted(result)]


class NodeTable:
    """Producer DAG insertion is deterministic; no project syntax helper used."""
    def __init__(self):
        self.nodes = []; self.indices = {}

    def intern(self, value):
        text = canonical(value)
        if text in self.indices:
            return self.indices[text]
        tag = value[0]
        if tag in ('var', 'bot'):
            record = copy.deepcopy(value)
        elif tag in ('fun', 'pred'):
            record = [tag, value[1], [self.intern(child) for child in value[2]]]
        elif tag == 'all':
            record = [tag, value[1], self.intern(value[2])]
        elif tag in ('eq', 'imp', 'and', 'or', 'not'):
            record = [tag, *[self.intern(child) for child in value[1:]]]
        else:
            raise ValueError('unsupported synthetic node constructor')
        index = len(self.nodes); self.nodes.append(record); self.indices[text] = index
        return index


def emit_catalog(*, fixture_pin, instance_id, output_directory, source_bindings):
    """Future ROOT-owned serializer only; no inference or returned proof acceptance.

    ROOT authenticates the exact frozen fixture/materializer closure and raw
    input before invocation. The independent oracle must regenerate this entire
    grammar without calling these helpers. All outputs are exclusive and all
    serialization/hash/close work belongs to the future bounded owned phase.
    """
    fixture = json.loads(read_pin(fixture_pin))
    if type(source_bindings) is not list or not source_bindings:
        raise ValueError('full separately reviewed source/input closure required')
    if len({record['path'] for record in source_bindings}) != len(source_bindings):
        raise ValueError('distinct exact source pins')
    for record in source_bindings:
        read_pin(record)
    if fixture_pin not in source_bindings:
        raise ValueError('raw exact fixture belongs to authority closure')
    case, theory, hypotheses, target = select_declaration(fixture, instance_id)
    formulas = all_subformulas([*theory['axioms'].values(), *hypotheses, target])
    codes = {canonical(formula): code for code, formula in enumerate(formulas)}
    nodes = NodeTable(); formula_nodes = [nodes.intern(formula) for formula in formulas]
    recipes = []
    for name, formula in sorted(theory['axioms'].items()):
        recipes.append(({'rule': 'axiom', 'name': name, 'formula': formula}, []))
    for formula in formulas:
        if formula[0] == 'imp':
            if codes[canonical(formula[1])] == codes[canonical(formula)]:
                raise ValueError('genuine MP antecedent/implication codes must differ')
            recipes.append(({'rule': 'mp', 'formula': formula[2]}, [formula[1], formula]))
    for occurrence, formula in enumerate(hypotheses):
        recipes.append(({'rule': 'assumption', 'index': occurrence, 'formula': formula}, []))
    recipes.sort(key=lambda record: canonical(record))
    if len({canonical(record) for record in recipes}) != len(recipes):
        raise ValueError('complete distinct command occurrence identities')
    registry = digest(formulas); context = {'theory': theory, 'ordered_local_premises': hypotheses}
    context_id = digest(context)
    grammar = copy.deepcopy(fixture['complete_tiny_grammar'])
    authority = {'activated': False, 'native_accepted': False,
                 'recipient_theory_sha256': digest(theory), 'declaration_schema': DECLARATION,
                 'finite_grammar_sha256': digest(grammar), 'source_bindings': copy.deepcopy(source_bindings),
                 'logical_qualification': 'pending independent synthetic mechanism fixture audit; never production theorem admission'}
    authority['epoch'] = digest(authority)
    out = Path(output_directory)
    if not out.is_absolute() or str(out.resolve()) != str(out):
        raise ValueError('future ROOT owns one canonical ABS exclusive output namespace')
    if out.exists():
        raise ValueError('synthetic output is once-only; existing outcomes stay immutable')
    out.mkdir(parents=True)
    node_path = out / 'nodes-v1.jsonl.gz'; formula_path = out / 'formulas-v1.bin'; recipe_path = out / 'recipes-v1.bin'
    with node_path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
            for index, record in enumerate(nodes.nodes):
                compressed.write((canonical([index, *record]) + '\n').encode('utf8'))
    with formula_path.open('xb') as stream:
        for node in formula_nodes:
            stream.write(WORD.pack(node))
    names = sorted(theory['axioms']); name_codes = {name: index for index, name in enumerate(names)}
    assumptions = {}; recipe_ids = []
    with recipe_path.open('xb') as stream:
        for index, (witness, premises) in enumerate(recipes):
            preimage = {'recipe': {'primitive_witness': witness, 'ordered_premise_formulas': premises},
                        'primitive_authority_epoch': authority['epoch'],
                        'recipient_theory_sha256': authority['recipient_theory_sha256'],
                        'marking_version': MARKING, 'formula_registry_sha256': registry}
            if witness['rule'] == 'assumption':
                preimage['local_context_id'] = context_id; assumptions[witness['index']] = index
            recipe_hash = digest(preimage); identifier = 'primitive-recipe-' + recipe_hash
            record = {'id': identifier, 'primitive_witness': witness,
                      'ordered_premise_formulas': premises, 'identity_preimage': preimage}
            output = codes[canonical(witness['formula'])]; inputs = [codes[canonical(f)] for f in premises]
            fields = [RULES.index(witness['rule']), formula_nodes[output], output,
                      inputs[0] if inputs else SENTINEL, inputs[1] if inputs else SENTINEL,
                      SENTINEL, SENTINEL, SENTINEL, SENTINEL,
                      name_codes[witness['name']] if witness['rule'] == 'axiom' else SENTINEL,
                      witness['index'] if witness['rule'] == 'assumption' else SENTINEL]
            stream.write(ROW.pack(*fields, bytes.fromhex(recipe_hash), bytes.fromhex(digest(record))))
            recipe_ids.append(identifier)
    if set(assumptions) != {0, 1, 2}:
        raise ValueError('exact distinct ordered occurrence licenses required')
    target_code = codes[canonical(target)]
    header = {'schema': WIRE, 'declaration_schema': DECLARATION,
        'status': 'synthetic_complete_mechanism_fixture_pending_independent_audit_not_production',
        'synthetic_mechanism_control': True, 'production_theorem_admission': False,
        'instance_id': instance_id, 'split': 'mechanism-control', 'height': 24,
        'context': context, 'context_id': context_id, 'target': target,
        'formula_registry_sha256': registry, 'authority': authority,
        'assumption_recipe_indices': [assumptions[i] for i in range(3)],
        'hypothesis_codes': [codes[canonical(f)] for f in hypotheses], 'target_code': target_code,
        'boundary': {'required': [[0, r] for r in range(24)],
            'root_generations': [[0, r, 0] for r in range(24)],
            'fixed_exterior_m': [[1, r, -1] for r in range(-23, 0)],
            'fixed_target_m': [[1, 23, target_code]],
            'fixed_initial_local_seeds': [{'recipe_id': recipe_ids[assumptions[i]], 'row': i, 'generation': 0} for i in range(3)],
            'all_root_obligations_generation_zero': True},
        'orientation': 'identity', 'marking_version': MARKING, 'source_bindings': copy.deepcopy(source_bindings),
        'declaration_binding': {'fixture_sha256': digest(fixture), 'selected_sha256': digest(case),
                              'grammar_sha256': digest(grammar), 'theory_key': 'synthetic-mechanism'},
        'syntax_census': {'tiny_complete_axiom_count': len(theory['axioms']),
                         'tiny_complete_implication_count': sum(f[0] == 'imp' for f in formulas),
                         'universal_instantiation_recipes': 0, 'equality_substitution_recipes': 0},
        'dimensions': {'logical_rows': 24, 'formula_count': len(formulas),
            'primitive_license_count': len(recipes), 'non_assumption_witness_count': len(recipes) - 3, 'source_body_count': 0},
        'streams': {'nodes': pin(node_path), 'formulas': pin(formula_path), 'recipes': pin(recipe_path)},
        'codec': {'node_count': len(nodes.nodes), 'formula_word_bytes': 8, 'byte_order': 'little',
                  'recipe_row_bytes': ROW.size, 'sentinel': SENTINEL, 'rules': list(RULES),
                  'names': names, 'recipe_fields': FIELDS},
        'bodies': [], 'complete_cluster_inventory': [], 'target_searches': 0, 'proof_certificates': 0,
        'RNG_draws': 0, 'new_RL_training': False, 'all_five_qualification': False, 'native_accepted': False,
        'scope': fixture['scope']}
    header_path = out / 'catalog-header-v1.json'
    with header_path.open('xb') as stream:
        stream.write((canonical(header) + '\n').encode('utf8'))
    return {'schema': 'synthetic-codec-materialization-result-v1', 'header_pin': pin(header_path),
            'stream_pins': copy.deepcopy(header['streams']), 'complete_tiny_dimensions': header['dimensions'],
            'materialization_complete': True, 'independent_fixture_accepted': False,
            'production_theorem_admission': False, 'dynamic_qualified': False,
            'proof_certificates': 0, 'target_searches': 0, 'RNG_draws': 0, 'training_updates': 0,
            'scope': 'Future serializer output only; no inference acceptance or production licensing.'}
