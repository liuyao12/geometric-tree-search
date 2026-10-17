"""SOURCE ONLY: independent every-record compact catalog qualification.

The producer compiler, decoder and point graph are never imported. A caller
provides the complete independently regenerated grammar. This reader uses its
own DAG reconstruction and sequential binary parsing, verifies exact original
canonical syntax/order/identities and invokes the independent logical authority
on every primitive. No count/hash from the producer is acceptance authority.
"""
import gzip
import hashlib
import json
import struct
from pathlib import Path

ROW = struct.Struct('<11Q32s32s')
WORD = struct.Struct('<Q')
SENTINEL = (1 << 64) - 1
RULES = ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
FIELDS = ['tag', 'output_node', 'output_code', 'input0_code', 'input1_code',
          'p0', 'p1', 'p2', 'p3', 'name_index', 'occurrence_index',
          'recipe_digest', 'record_digest']
HEADER_KEYS = frozenset(('schema', 'declaration_schema', 'status', 'instance_id',
    'split', 'height', 'context', 'context_id', 'target', 'formula_registry_sha256',
    'authority', 'assumption_recipe_indices', 'hypothesis_codes', 'target_code',
    'boundary', 'orientation', 'marking_version', 'source_bindings',
    'declaration_binding', 'syntax_census', 'dimensions', 'streams', 'codec',
    'bodies', 'complete_cluster_inventory', 'target_searches', 'proof_certificates',
    'RNG_draws', 'new_RL_training', 'all_five_qualification', 'native_accepted', 'scope'))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def same(actual, expected, message):
    # Canonical comparison preserves bool-versus-int distinctions.
    need(canonical(actual) == canonical(expected), message)


def unique_object(pairs):
    result = {}
    for name, value in pairs:
        need(name not in result, 'duplicate JSON key')
        result[name] = value
    return result


def parse_json(raw):
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError('nonfinite JSON token ' + value)))


def raw_pin(path, declared=None):
    path = Path(path); h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return dict(path=str(path.resolve()) if declared is None else declared,
                sha256=h.hexdigest(), bytes=size)


def verify_absolute_pin(pin, expected_path=None):
    need(type(pin) is dict and set(pin) == {'path', 'sha256', 'bytes'},
         'exact closed raw pin grammar')
    need(type(pin['path']) is str and type(pin['bytes']) is int and pin['bytes'] >= 0
         and type(pin['sha256']) is str and len(pin['sha256']) == 64
         and all(c in '0123456789abcdef' for c in pin['sha256']), 'typed pin')
    path = Path(pin['path'])
    need(path.is_absolute() and str(path.resolve()) == pin['path'],
         'canonical absolute compact artifact identity')
    if expected_path is not None:
        need(path == Path(expected_path).resolve(), 'exact catalog artifact path')
    same(raw_pin(path), pin, 'exact complete raw bytes changed')
    return path


class IndependentReader:
    """Whole reversible syntax bijection, independent of source decoder APIs."""
    def __init__(self, grammar, header, header_path):
        self.grammar = grammar; self.header = header; self.path = Path(header_path).resolve()
        need(type(header) is dict and set(header) == HEADER_KEYS, 'closed header grammar')
        dimensions = grammar.dimensions
        same(header['dimensions'], dimensions, 'full regenerated catalog dimensions')
        expected_names = sorted({*grammar.theory['axioms'], grammar.syntax_census['template_variable']})
        self.names = expected_names
        codec = header['codec']
        need(type(codec) is dict and set(codec) == {'node_count', 'formula_word_bytes',
             'byte_order', 'recipe_row_bytes', 'sentinel', 'rules', 'names', 'recipe_fields'},
             'closed codec grammar')
        need(type(codec['node_count']) is int and codec['node_count'] > 0, 'exact node census')
        for name, value in dict(formula_word_bytes=8, byte_order='little',
                recipe_row_bytes=152, sentinel=SENTINEL, rules=list(RULES),
                names=expected_names, recipe_fields=FIELDS).items():
            same(codec[name], value, 'exact reversible codec field ' + name)
        need(type(header['streams']) is dict and set(header['streams']) == {'nodes', 'formulas', 'recipes'},
             'all complete stream files')
        self.streams = {}
        filenames = dict(nodes='nodes-v1.jsonl.gz', formulas='formulas-v1.u64le.bin',
                         recipes='recipes-v1.bin')
        for name, pin in header['streams'].items():
            self.streams[name] = verify_absolute_pin(pin, self.path.parent / filenames[name])
        same(header['streams']['formulas']['bytes'], WORD.size * len(grammar.formulas),
             'entire formula stream length')
        same(header['streams']['recipes']['bytes'], ROW.size * len(grammar.records),
             'entire primitive stream length')
        self.nodes = []; self.kinds = bytearray(); seen = set()
        expected_nodes = {value for value in grammar.arena.values if value and
            type(value[0]) is str and value[0] in ('var', 'fun', 'bot', 'pred', 'eq',
                                                   'all', 'not', 'imp', 'and', 'or')}
        with gzip.open(self.streams['nodes'], 'rb') as stream:
            for line in stream:
                value = parse_json(line)
                need(type(value) is list and len(value) >= 2
                     and type(value[0]) is int and value[0] == len(self.nodes),
                     'contiguous exact node identifiers')
                same(line.decode('utf8'), canonical(value) + '\n', 'canonical full node line')
                ast, kind = self.node(value[1:])
                need(ast not in seen, 'injective full syntactic DAG')
                seen.add(ast); self.nodes.append(ast); self.kinds.append(kind)
        same(len(self.nodes), codec['node_count'], 'complete DAG node count')
        need(seen == expected_nodes, 'exact full independently generated AST-node bijection')
        self.node_index = {value: i for i, value in enumerate(self.nodes)}
        del seen, expected_nodes
        self.formula_nodes = []
        with self.streams['formulas'].open('rb') as stream:
            for formula in grammar.formulas:
                raw = stream.read(WORD.size)
                need(len(raw) == WORD.size, 'complete formula word')
                index = WORD.unpack(raw)[0]
                need(index < len(self.nodes) and self.kinds[index] == 1,
                     'typed registry formula node')
                need(self.nodes[index] == formula, 'entire original canonical formula order')
                self.formula_nodes.append(index)
            need(stream.read(1) == b'', 'no unread formula tail')

    def child(self, index, kind):
        need(type(index) is int and 0 <= index < len(self.nodes), 'strict prior node reference')
        need(self.kinds[index] == kind, 'exact term/formula child type')
        return self.nodes[index]

    def node(self, record):
        need(record and type(record[0]) is str, 'tagged AST constructor')
        tag = record[0]; arena = self.grammar.arena; theory = self.grammar.theory
        def name(value):
            need(type(value) is str and bool(value), 'nonempty syntactic name')
            return value
        if tag == 'var' and len(record) == 2:
            return arena.node(tag, name(record[1])), 0
        if tag == 'bot' and len(record) == 1:
            return arena.node(tag), 1
        if tag in ('fun', 'pred') and len(record) == 3:
            table = theory['functions' if tag == 'fun' else 'predicates']
            symbol = name(record[1]); args = record[2]
            need(symbol in table and type(args) is list and len(args) == table[symbol],
                 'original signature and exact arity')
            return arena.node(tag, symbol, tuple(self.child(n, 0) for n in args)), int(tag == 'pred')
        if tag == 'all' and len(record) == 3:
            return arena.node(tag, name(record[1]), self.child(record[2], 1)), 1
        if tag == 'eq' and len(record) == 3:
            return arena.node(tag, self.child(record[1], 0), self.child(record[2], 0)), 1
        if (tag in ('imp', 'and', 'or') and len(record) == 3
                or tag == 'not' and len(record) == 2):
            return arena.node(tag, *(self.child(n, 1) for n in record[1:])), 1
        raise ValueError('node outside exact original signature/constructor grammar')

    def census(self):
        source = self.header['syntax_census']
        need(type(source) is dict and set(source) == {'seed_term_nodes', 'term_pool_nodes',
            'instantiation_rounds', 'template_variable', 'closed_atomic_source_count',
            'equality_pair_nodes', 'atomic_template_nodes', 'equality_scheme_count'}, 'closed syntax census')
        def references(ids, kind):
            need(type(ids) is list, 'literal full node-reference list')
            result = []
            for index in ids:
                need(type(index) is int and 0 <= index < len(self.nodes)
                     and self.kinds[index] == kind, 'typed census reference')
                result.append(self.nodes[index])
            return result
        expected = self.grammar.syntax_census
        need(type(source['term_pool_nodes']) is dict, 'full term-role table')
        pairs = source['equality_pair_nodes']
        need(type(pairs) is list and all(type(p) is list and len(p) == 2 for p in pairs),
             'all ordered equality operand pairs')
        decoded = dict(seed_terms=references(source['seed_term_nodes'], 0),
            term_pools={k: references(v, 0) for k, v in source['term_pool_nodes'].items()},
            instantiation_rounds=source['instantiation_rounds'],
            template_variable=source['template_variable'],
            closed_atomic_source_count=source['closed_atomic_source_count'],
            equality_pairs=[references(pair, 0) for pair in pairs],
            atomic_templates=references(source['atomic_template_nodes'], 1),
            equality_scheme_count=source['equality_scheme_count'])
        same(decoded, expected, 'whole original term/round/atom/template/pair census')

    def recipe_fields(self, index):
        grammar = self.grammar; record = grammar.records[index]; rule = record[0]
        recipe, record_hash, output, inputs = grammar.recipe(index, logical_check=True)
        params = [SENTINEL] * 4; name = occurrence = SENTINEL
        if rule == 'axiom':
            name = self.names.index(record[2])
        elif rule == 'instantiate':
            params[:2] = [self.node_index[record[2]], self.node_index[record[3]]]
        elif rule == 'eq_subst':
            params[:3] = [self.node_index[record[3]], self.node_index[record[4]], self.node_index[record[5]]]
            name = self.names.index(record[2])
        elif rule == 'assumption':
            occurrence = record[2]
        fields = [RULES.index(rule), self.node_index[record[1]], output,
            inputs[0] if inputs else SENTINEL, inputs[1] if inputs else SENTINEL,
            *params, name, occurrence, bytes.fromhex(recipe['id'].split('primitive-recipe-')[1]),
            bytes.fromhex(record_hash)]
        return ROW.pack(*fields), recipe['id'], record_hash

    def licenses(self, license_output):
        """Every original primitive is checked and every wire byte compared."""
        identifiers = []; logical_counts = {rule: 0 for rule in RULES}
        with self.streams['recipes'].open('rb') as stream:
            for index, record in enumerate(self.grammar.records):
                expected, identifier, record_hash = self.recipe_fields(index)
                actual = stream.read(ROW.size)
                need(len(actual) == ROW.size and actual == expected,
                     'complete independently licensed152-byte primitive record ' + str(index))
                identifiers.append(identifier); logical_counts[record[0]] += 1
                value = dict(recipe_index=index, recipe_id=identifier, rule=record[0],
                    record_sha256=record_hash, logical_accepted=True, native_accepted=False,
                    status='accepted_independent_exact_primitive_license')
                license_output.write((canonical(value) + '\n').encode('utf8'))
            need(stream.read(1) == b'', 'no unread primitive tail')
        need(len(set(identifiers)) == len(identifiers), 'full unique primitive identifiers')
        return identifiers, logical_counts

    def header_semantics(self, identifiers):
        grammar = self.grammar; header = self.header
        expected = dict(schema='fresh-ground-compact-catalog-v1',
            declaration_schema='fresh-ground-cluster-context-declaration-v1',
            status='complete_declared_catalog_pending_independent_qualification',
            instance_id=grammar.instance_id, split=grammar.split, height=24,
            context=grammar.context, context_id=grammar.context_id, target=grammar.target,
            formula_registry_sha256=grammar.registry_sha, authority=grammar.authority,
            assumption_recipe_indices=grammar.assumptions,
            hypothesis_codes=[grammar.codes[grammar.arena.intern(f)] for f in grammar.gamma],
            target_code=grammar.target_code, orientation='identity',
            marking_version='injective-formula-ordered-mp-offset-v1',
            source_bindings=grammar.source_bindings, declaration_binding=grammar.declaration_binding,
            dimensions=grammar.dimensions, bodies=[], complete_cluster_inventory=[],
            target_searches=0, proof_certificates=0, RNG_draws=0, new_RL_training=False,
            all_five_qualification=False, native_accepted=False,
            scope='Exact full original declared finite grammar in reversible compact streams; '
                'full theory/schema data retained, no induction/generalization/tautology/reflexivity recipe. '
                'Empty initial cluster library and independent qualification pending.')
        for name, value in expected.items():
            same(header[name], value, 'independent exact header semantic field ' + name)
        boundary = dict(required=[[0, r] for r in range(24)],
            root_generations=[[0, r, 0] for r in range(24)],
            fixed_exterior_m=[[1, r, -1] for r in range(-23, 0)],
            fixed_target_m=[[1, 23, grammar.target_code]],
            fixed_initial_local_seeds=[dict(recipe_id=identifiers[index], row=r, generation=0)
                for r, index in enumerate(grammar.assumptions)],
            all_root_obligations_generation_zero=True)
        same(header['boundary'], boundary, 'full exact fixed/free boundary and occurrence seeds')
        self.census()
