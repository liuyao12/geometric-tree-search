"""SOURCE ONLY: exact finite declaration, compact storage, no proof route.

Future ROOT-owned invocation is conditional on whole independent source and
resource review. This module has no project imports, search, RNG, child process
or checker. A completed catalog is NOT an independently qualified catalog.
The literal V1 grammar, canonical ordering and identity preimages are retained.
"""
import array
import gzip
import hashlib
import heapq
import json
import struct
from functools import lru_cache
from pathlib import Path

DECLARATION = 'fresh-ground-cluster-context-declaration-v1'
WIRE = 'fresh-ground-compact-catalog-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'
SENTINEL = (1 << 64) - 1
RULES = ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
ROW = struct.Struct('<11Q32s32s')
SORT_BYTES = 4 * 1024 * 1024
AST_FIELDS = frozenset(('formula', 'universal', 'term', 'template', 'left', 'right'))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


@lru_cache(maxsize=1024)
def quoted(value):
    return canonical(value)


def pin(path):
    path = Path(path); h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    return {'path': str(path.resolve()), 'sha256': h.hexdigest(), 'bytes': size}


class Ref:
    __slots__ = ('node',)

    def __init__(self, node):
        self.node = node


class Arena:
    """Hash-consed immutable syntactic nodes, with shared integer children."""
    def __init__(self):
        self.nodes = []; self.index = {}; self.masks = []; self.variables = {}

    def bit(self, name):
        if name not in self.variables:
            self.variables[name] = 1 << len(self.variables)
        return self.variables[name]

    def intern(self, record):
        found = self.index.get(record)
        if found is not None:
            return found
        tag = record[0]
        if tag == 'var':
            mask = self.bit(record[1])
        elif tag in ('fun', 'pred'):
            mask = 0
            for child in record[2]:
                mask |= self.masks[child]
        elif tag == 'all':
            mask = self.masks[record[2]] & ~self.bit(record[1])
        elif tag == 'bot':
            mask = 0
        else:
            mask = 0
            for child in record[1:]:
                mask |= self.masks[child]
        node = len(self.nodes); self.nodes.append(record); self.masks.append(mask)
        self.index[record] = node
        return node

    def term(self, term, theory):
        if type(term) is not list:
            raise ValueError('literal term AST list required')
        if len(term) == 2 and term[0] == 'var' and type(term[1]) is str:
            return self.intern(('var', term[1]))
        if (len(term) != 3 or term[0] != 'fun' or type(term[1]) is not str
                or type(term[2]) is not list or theory['functions'].get(term[1]) != len(term[2])):
            raise ValueError('declared function and exact arity required')
        return self.intern(('fun', term[1], tuple(self.term(x, theory) for x in term[2])))

    def formula(self, formula, theory):
        if type(formula) is not list or not formula:
            raise ValueError('literal formula AST list required')
        tag = formula[0]
        if tag == 'bot' and len(formula) == 1:
            return self.intern(('bot',))
        if tag == 'eq' and len(formula) == 3:
            return self.intern(('eq', self.term(formula[1], theory), self.term(formula[2], theory)))
        if (tag == 'pred' and len(formula) == 3 and type(formula[1]) is str
                and type(formula[2]) is list and theory['predicates'].get(formula[1]) == len(formula[2])):
            return self.intern(('pred', formula[1], tuple(self.term(x, theory) for x in formula[2])))
        if tag == 'all' and len(formula) == 3 and type(formula[1]) is str:
            return self.intern(('all', formula[1], self.formula(formula[2], theory)))
        if ((tag in ('imp', 'and', 'or') and len(formula) == 3)
                or (tag == 'not' and len(formula) == 2)):
            return self.intern((tag, *(self.formula(x, theory) for x in formula[1:])))
        raise ValueError('constructor outside literal fixed FOL language')

    def expanded(self, node):
        rec = self.nodes[node]; tag = rec[0]
        if tag == 'var' or tag == 'bot':
            return list(rec)
        if tag in ('fun', 'pred'):
            return [tag, rec[1], [self.expanded(x) for x in rec[2]]]
        if tag == 'all':
            return [tag, rec[1], self.expanded(rec[2])]
        return [tag, *(self.expanded(x) for x in rec[1:])]

    def tokens(self, node):
        rec = self.nodes[node]; tag = rec[0]
        yield '['; yield quoted(tag)
        if tag == 'var':
            yield ','; yield quoted(rec[1])
        elif tag in ('fun', 'pred'):
            yield ','; yield quoted(rec[1]); yield ',['
            for i, child in enumerate(rec[2]):
                if i:
                    yield ','
                yield from self.tokens(child)
            yield ']'
        elif tag == 'all':
            yield ','; yield quoted(rec[1]); yield ','
            yield from self.tokens(rec[2])
        elif tag != 'bot':
            for child in rec[1:]:
                yield ','; yield from self.tokens(child)
        yield ']'

    def text(self, node):
        return ''.join(self.tokens(node))

    def replace(self, node, variable, replacement, cache):
        if self.masks[replacement]:
            raise ValueError('only closed substitutions; no capture shortcut')
        key = (node, variable, replacement)
        cached = cache.get(key)
        if cached is not None:
            return cached
        if not self.masks[node] & self.bit(variable):
            return node
        rec = self.nodes[node]; tag = rec[0]
        if tag == 'var':
            result = replacement if rec[1] == variable else node
        elif tag in ('fun', 'pred'):
            result = self.intern((tag, rec[1], tuple(self.replace(x, variable, replacement, cache) for x in rec[2])))
        elif tag == 'all':
            result = node if rec[1] == variable else self.intern((tag, rec[1], self.replace(rec[2], variable, replacement, cache)))
        elif tag == 'bot':
            result = node
        else:
            result = self.intern((tag, *(self.replace(x, variable, replacement, cache) for x in rec[1:])))
        cache[key] = result
        return result

    def abstract(self, node, old, hole, cache):
        key = (node, old)
        cached = cache.get(key)
        if cached is not None:
            return cached
        if node == old:
            return hole
        rec = self.nodes[node]; tag = rec[0]
        if tag in ('fun', 'pred'):
            result = self.intern((tag, rec[1], tuple(self.abstract(x, old, hole, cache) for x in rec[2])))
        elif tag == 'eq':
            result = self.intern((tag, self.abstract(rec[1], old, hole, cache), self.abstract(rec[2], old, hole, cache)))
        else:
            result = node
        cache[key] = result
        return result


def tokens(value, arena):
    """Exactly the original json.dumps canonical preimage, without AST copies."""
    if isinstance(value, Ref):
        yield from arena.tokens(value.node)
    elif isinstance(value, dict):
        yield '{'
        for i, key in enumerate(sorted(value)):
            if i:
                yield ','
            yield quoted(key); yield ':'; yield from tokens(value[key], arena)
        yield '}'
    elif isinstance(value, (tuple, list)):
        yield '['
        for i, item in enumerate(value):
            if i:
                yield ','
            yield from tokens(item, arena)
        yield ']'
    else:
        yield canonical(value)


def stream_digest(value, arena):
    h = hashlib.sha256(); fragments = []; length = 0
    for token in tokens(value, arena):
        fragments.append(token); length += len(token)
        if length >= 65536:
            h.update(''.join(fragments).encode('utf8')); fragments = []; length = 0
    if fragments:
        h.update(''.join(fragments).encode('utf8'))
    return h.hexdigest()


def witness_refs(compact):
    return {key: Ref(value) if key in AST_FIELDS else value for key, value in compact.items()}


class ExternalOrder:
    """Bounded canonical-key runs; one complete key is transient, never sampled."""
    def __init__(self, directory, label):
        self.directory = Path(directory); self.label = label
        self.lines = []; self.bytes = 0; self.runs = []; self.count = 0

    def add(self, key, value):
        if '\t' in key or '\n' in key:
            raise ValueError('canonical JSON key cannot contain literal separator')
        line = key + '\t' + canonical(value) + '\n'
        self.lines.append(line); self.bytes += len(line.encode('utf8')); self.count += 1
        if self.bytes >= SORT_BYTES:
            self.flush()

    def flush(self):
        if not self.lines:
            return
        path = self.directory / (self.label + '-run-' + str(len(self.runs)) + '.txt')
        self.lines.sort()
        with path.open('x', encoding='utf8', newline='') as stream:
            stream.writelines(self.lines)
        self.runs.append(path); self.lines = []; self.bytes = 0

    def ordered(self):
        self.flush(); streams = []; level = 0
        # Keep the file-descriptor and merge-head envelope finite too. These
        # are representation passes, never candidate/inventory filtering.
        while len(self.runs) > 32:
            successors = []
            for start in range(0, len(self.runs), 32):
                group = self.runs[start:start + 32]
                target = self.directory / (self.label + '-merge-' + str(level) + '-' + str(start) + '.txt')
                opened = []
                try:
                    opened = [path.open('r', encoding='utf8', newline='') for path in group]
                    with target.open('x', encoding='utf8', newline='') as stream:
                        stream.writelines(heapq.merge(*opened))
                finally:
                    for stream in opened:
                        stream.close()
                for path in group:
                    path.unlink()
                successors.append(target)
            self.runs = successors; level += 1
        try:
            streams = [path.open('r', encoding='utf8', newline='') for path in self.runs]
            previous = None
            for line in heapq.merge(*streams):
                key, value = line.rstrip('\n').split('\t', 1)
                if key == previous:
                    raise ValueError('duplicate complete canonical primitive/formula key')
                previous = key
                yield json.loads(value)
        finally:
            for stream in streams:
                stream.close()
            for path in self.runs:
                path.unlink()


def select_case(fixture, instance_id, arena):
    if (fixture.get('schema') != 'fresh-ground-theorem-fixtures-v1'
            or fixture.get('source_only') is not True
            or fixture.get('execution_authorized') is not False):
        raise ValueError('exact frozen source-only fixture required')
    matches = [case for case in fixture['cases'] if case['id'] == instance_id]
    if len(matches) != 1:
        raise ValueError('one exact declared instance only')
    case = matches[0]; theory = fixture['theories'][case['theory']]
    premises = [fixture['literal_formulas'][name] for name in case['hypotheses']]
    target = fixture['literal_formulas'][case['target']]
    if case['rows'] != 24 or len(premises) != 3:
        raise ValueError('all24 rows and three distinct ordered occurrences required')
    for formula in [*theory['axioms'].values(), *premises, target]:
        if arena.masks[arena.formula(formula, theory)]:
            raise ValueError('closed literal theory, premises and target required')
    return {'instance_id': instance_id, 'split': case['split'], 'theory_key': case['theory'],
            'theory': theory, 'ordered_hypotheses': premises, 'target': target, 'rows': 24,
            'structural_tag': case['structural_tag']}


def compile_to_directory(fixture, instance_id, source_bindings, output_directory):
    """Whole V1 grammar in exclusive stream artifacts; no model/proof is built.

    Returned header is small. Output must be a fresh directory. Temporary sort
    runs are implementation scratch, not source/authority omissions. Nothing
    here asserts fit within ROOT's unchanged60s/512MiB full-owned envelope.
    """
    output = Path(output_directory).resolve(); output.mkdir()
    scratch = output / 'sort-scratch'; scratch.mkdir()
    arena = Arena(); selected = select_case(fixture, instance_id, arena)
    theory = selected['theory']; grammar = fixture['finite_grammars'][selected['theory_key']]
    if grammar['instantiation_rounds'] != 4 or grammar['equality_layers'] != 1:
        raise ValueError('exact four snapshot rounds and one equality layer')
    fs = set(); terms = set(); names = set(); term_seen = set(); seed_phase = True
    def collect_term(node):
        # Closed instantiation and all-occurrence abstraction introduce no
        # new source variable/binder names. Later term pools are frozen.
        if not seed_phase:
            return
        if node in term_seen:
            return
        term_seen.add(node); rec = arena.nodes[node]
        if rec[0] == 'var':
            names.add(rec[1])
        else:
            if not arena.masks[node]:
                terms.add(node)
            for child in rec[2]:
                collect_term(child)
    def add_formula(node):
        if node in fs:
            return
        fs.add(node); rec = arena.nodes[node]; tag = rec[0]
        if tag == 'all':
            names.add(rec[1]); add_formula(rec[2])
        elif tag in ('imp', 'and', 'or', 'not'):
            for child in rec[1:]:
                add_formula(child)
        elif tag in ('eq', 'pred'):
            for child in rec[2] if tag == 'pred' else rec[1:]:
                collect_term(child)
    for formula in theory['axioms'].values():
        add_formula(arena.formula(formula, theory))
    for case in fixture['cases']:
        if case['theory'] == selected['theory_key']:
            context = select_case(fixture, case['id'], arena)
            for formula in [*context['ordered_hypotheses'], context['target']]:
                add_formula(arena.formula(formula, theory))
    seed_terms = sorted(terms, key=arena.text)
    seed_phase = False; term_seen.clear(); terms.clear()
    def numeral(node):
        rec = arena.nodes[node]
        return (rec == ('fun', 'zero', ()) or rec[0] == 'fun' and rec[1] == 'succ'
                and len(rec[2]) == 1 and numeral(rec[2][0]))
    pools = {}
    for role, definition in sorted(grammar['term_roles'].items()):
        if definition == 'all_closed_seed_subterms':
            pools[role] = tuple(seed_terms)
        elif definition == 'closed_seed_numerals':
            pools[role] = tuple(node for node in seed_terms if numeral(node))
        elif type(definition) is list:
            pools[role] = tuple(node for node in seed_terms if arena.nodes[node][0] == 'fun'
                                and not arena.nodes[node][2] and arena.nodes[node][1] in definition)
            if {arena.nodes[node][1] for node in pools[role]} != set(definition):
                raise ValueError('complete declared parameter pool missing')
        else:
            raise ValueError('unknown exact finite term role')
    recipes_order = ExternalOrder(scratch, 'recipes'); instantiations = set(); rounds = []
    replace_cache = {}
    def add_witness(witness, premises=()):
        key = ''.join(tokens([witness_refs(witness), [Ref(x) for x in premises]], arena))
        recipes_order.add(key, [witness, list(premises)])
    for name, literal in sorted(theory['axioms'].items()):
        add_witness({'rule': 'axiom', 'name': name, 'formula': arena.formula(literal, theory)})
    for round_index in range(4):
        before = len(instantiations)
        universals = sorted((node for node in fs if arena.nodes[node][0] == 'all'), key=arena.text)
        for universal in universals:
            rec = arena.nodes[universal]
            if rec[1] not in grammar['binder_roles']:
                raise ValueError('undeclared finite binder role')
            for term in pools[grammar['binder_roles'][rec[1]]]:
                formula = arena.intern(('imp', universal, arena.replace(rec[2], rec[1], term, replace_cache)))
                command = (formula, universal, term)
                if command not in instantiations:
                    instantiations.add(command)
                    add_witness({'rule': 'instantiate', 'formula': formula, 'universal': universal, 'term': term})
                add_formula(formula)
        rounds.append({'round': round_index, 'universal_count': len(universals),
                       'new_distinct_schemes': len(instantiations) - before,
                       'scheme_count': len(instantiations), 'formula_count': len(fs)})
    variable = 'hole0'; suffix = 0
    while variable in names:
        suffix += 1; variable = 'hole' + str(suffix)
    hole = arena.intern(('var', variable)); atoms = [node for node in fs
        if arena.nodes[node][0] in ('eq', 'pred') and not arena.masks[node]]
    replace_cache.clear()
    pairs = set(); templates = set(); abstract_cache = {}
    for atom in atoms:
        rec = arena.nodes[atom]
        if rec[0] == 'eq':
            pairs.add((rec[1], rec[2]))
        local_terms = set()
        def local(node):
            if not arena.masks[node]:
                local_terms.add(node)
            if arena.nodes[node][0] == 'fun':
                for child in arena.nodes[node][2]:
                    local(child)
        for node in rec[2] if rec[0] == 'pred' else rec[1:]:
            local(node)
        for old in local_terms:
            template = arena.abstract(atom, old, hole, abstract_cache)
            if template == atom or not arena.masks[template] & arena.bit(variable):
                raise ValueError('all-occurrence abstraction must change an actual subterm')
            templates.add(template)
        abstract_cache.clear()
    # This is the entire nonrecursive layer. Newly generated equality operands
    # never grow pairs/templates; every original ordered pair remains present.
    for template in templates:
        for left, right in pairs:
            formula = arena.intern(('imp', arena.intern(('eq', left, right)), arena.intern(('imp',
                arena.replace(template, variable, left, replace_cache),
                arena.replace(template, variable, right, replace_cache)))))
            add_witness({'rule': 'eq_subst', 'formula': formula, 'variable': variable,
                         'template': template, 'left': left, 'right': right})
            add_formula(formula)
        replace_cache.clear()
    equality_count = len(templates) * len(pairs)
    # Release memoization state before the complete final sorting/identity pass.
    replace_cache.clear(); abstract_cache.clear(); term_seen.clear(); terms.clear(); instantiations.clear()
    formula_order = ExternalOrder(scratch, 'formulas')
    for node in fs:
        formula_order.add(arena.text(node), node)
    ordered_ids = array.array('Q'); codes = array.array('Q', [SENTINEL]) * len(arena.nodes)
    registry_hasher = hashlib.sha256()
    registry_hasher.update(b'[')
    formula_path = output / 'formulas-v1.u64le.bin'
    with formula_path.open('xb') as stream:
        for code, node in enumerate(formula_order.ordered()):
            if code:
                registry_hasher.update(b',')
            for token in arena.tokens(node):
                registry_hasher.update(token.encode('utf8'))
            ordered_ids.append(node); codes[node] = code; stream.write(struct.pack('<Q', node))
            rec = arena.nodes[node]
            if rec[0] == 'imp':
                add_witness({'rule': 'mp', 'formula': rec[2]}, (rec[1], node))
    registry_hasher.update(b']'); registry = registry_hasher.hexdigest()
    for occurrence, literal in enumerate(selected['ordered_hypotheses']):
        add_witness({'rule': 'assumption', 'index': occurrence, 'formula': arena.formula(literal, theory)})
    context = {'theory': theory, 'ordered_local_premises': selected['ordered_hypotheses']}
    context_id = digest(context)
    authority = {'activated': False, 'native_accepted': False,
                 'recipient_theory_sha256': digest(theory), 'declaration_schema': DECLARATION,
                 'finite_grammar_sha256': digest(grammar), 'source_bindings': source_bindings,
                 'logical_qualification': 'pending independent complete witness/context gate'}
    authority['epoch'] = digest(authority)
    names_table = sorted({*theory['axioms'], variable}); name_codes = {name: i for i, name in enumerate(names_table)}
    assumptions = {}; recipe_path = output / 'recipes-v1.bin'; recipe_count = 0
    with recipe_path.open('xb') as stream:
        for index, (witness, premises) in enumerate(recipes_order.ordered()):
            rule = witness['rule']; refs = witness_refs(witness)
            preimage = {'recipe': {'primitive_witness': refs, 'ordered_premise_formulas': [Ref(x) for x in premises]},
                        'primitive_authority_epoch': authority['epoch'],
                        'recipient_theory_sha256': authority['recipient_theory_sha256'],
                        'marking_version': MARKING, 'formula_registry_sha256': registry}
            if rule == 'assumption':
                preimage['local_context_id'] = context_id; assumptions[witness['index']] = index
            recipe_hash = stream_digest(preimage, arena)
            identifier = 'primitive-recipe-' + recipe_hash
            legacy_record = {'id': identifier, 'primitive_witness': refs,
                             'ordered_premise_formulas': [Ref(x) for x in premises], 'identity_preimage': preimage}
            record_hash = stream_digest(legacy_record, arena)
            inp = [codes[node] for node in premises]
            if len(inp) not in (0, 2) or (rule == 'mp') != bool(inp):
                raise ValueError('exact zero-port/binary ordered MP grammar')
            params = [SENTINEL] * 4; name_code = SENTINEL; occurrence = SENTINEL
            if rule == 'axiom':
                name_code = name_codes[witness['name']]
            elif rule == 'instantiate':
                params[:2] = [witness['universal'], witness['term']]
            elif rule == 'eq_subst':
                params[:3] = [witness['template'], witness['left'], witness['right']]
                name_code = name_codes[witness['variable']]
            elif rule == 'assumption':
                occurrence = witness['index']
            fields = [RULES.index(rule), witness['formula'], codes[witness['formula']],
                      inp[0] if inp else SENTINEL, inp[1] if inp else SENTINEL,
                      *params, name_code, occurrence]
            stream.write(ROW.pack(*fields, bytes.fromhex(recipe_hash), bytes.fromhex(record_hash)))
            recipe_count += 1
    if set(assumptions) != {0, 1, 2} or recipe_count != recipes_order.count:
        raise ValueError('complete recipes and all distinct occurrence identities required')
    nodes_path = output / 'nodes-v1.jsonl.gz'
    with nodes_path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            for node, rec in enumerate(arena.nodes):
                stream.write((canonical([node, *rec]) + '\n').encode('utf8'))
    target_code = codes[arena.formula(selected['target'], theory)]
    boundary = {'required': [[0, r] for r in range(24)],
                'root_generations': [[0, r, 0] for r in range(24)],
                'fixed_exterior_m': [[1, r, -1] for r in range(-23, 0)],
                'fixed_target_m': [[1, 23, target_code]],
                'fixed_initial_local_seeds': [{'recipe_id': 'primitive-recipe-' + _recipe_hash_at(recipe_path, assumptions[r]),
                    'row': r, 'generation': 0} for r in range(3)],
                'all_root_obligations_generation_zero': True}
    pair_order = sorted(pairs, key=lambda pair: ''.join(tokens([Ref(x) for x in pair], arena)))
    template_order = sorted(templates, key=arena.text)
    header = {'schema': WIRE, 'declaration_schema': DECLARATION,
        'status': 'complete_declared_catalog_pending_independent_qualification',
        'instance_id': instance_id, 'split': selected['split'], 'height': 24,
        'context': context, 'context_id': context_id, 'target': selected['target'],
        'formula_registry_sha256': registry, 'authority': authority,
        'assumption_recipe_indices': [assumptions[r] for r in range(3)],
        'hypothesis_codes': [codes[arena.formula(f, theory)] for f in selected['ordered_hypotheses']],
        'target_code': target_code, 'boundary': boundary, 'orientation': 'identity',
        'marking_version': MARKING, 'source_bindings': source_bindings,
        'declaration_binding': {'fixture_sha256': digest(fixture), 'selected_sha256': digest(selected),
                                'grammar_sha256': digest(grammar), 'theory_key': selected['theory_key']},
        'syntax_census': {'seed_term_nodes': seed_terms, 'term_pool_nodes': {key: list(value) for key, value in pools.items()},
            'instantiation_rounds': rounds, 'template_variable': variable,
            'closed_atomic_source_count': len(atoms), 'equality_pair_nodes': [list(pair) for pair in pair_order],
            'atomic_template_nodes': template_order, 'equality_scheme_count': equality_count},
        'dimensions': {'logical_rows': 24, 'formula_count': len(ordered_ids),
                       'primitive_license_count': recipe_count, 'non_assumption_witness_count': recipe_count - 3,
                       'source_body_count': 0},
        'streams': {'nodes': pin(nodes_path), 'formulas': pin(formula_path), 'recipes': pin(recipe_path)},
        'codec': {'node_count': len(arena.nodes), 'formula_word_bytes': 8, 'byte_order': 'little',
                  'recipe_row_bytes': ROW.size, 'sentinel': SENTINEL, 'rules': list(RULES), 'names': names_table,
                  'recipe_fields': ['tag', 'output_node', 'output_code', 'input0_code', 'input1_code',
                      'p0', 'p1', 'p2', 'p3', 'name_index', 'occurrence_index', 'recipe_digest', 'record_digest']},
        'bodies': [], 'complete_cluster_inventory': [], 'target_searches': 0,
        'proof_certificates': 0, 'RNG_draws': 0, 'new_RL_training': False,
        'all_five_qualification': False, 'native_accepted': False,
        'scope': 'Exact full original declared finite grammar in reversible compact streams; '
                 'full theory/schema data retained, no induction/generalization/tautology/reflexivity recipe. '
                 'Empty initial cluster library and independent qualification pending.'}
    header_path = output / 'catalog-v1.json'
    with header_path.open('xb') as stream:
        stream.write((canonical(header) + '\n').encode('utf8'))
    scratch.rmdir()
    return header


def _recipe_hash_at(path, index):
    with Path(path).open('rb') as stream:
        stream.seek(index * ROW.size)
        raw = stream.read(ROW.size)
    if len(raw) != ROW.size:
        raise ValueError('complete fixed-row primitive record required')
    return ROW.unpack(raw)[11].hex()
