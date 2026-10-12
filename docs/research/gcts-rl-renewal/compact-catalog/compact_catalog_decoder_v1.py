"""SOURCE ONLY: reversible compact catalog views, never a licensing oracle.

No project imports. Exact file pins and complete structure are checked here;
logical, source/resource and model admission require independent future gates.
Individual ASTs/legacy records are expanded only on explicit request. Large
formula/recipe streams stay memory mapped, not expanded into Python lists.
"""
import gzip
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path

WIRE = 'fresh-ground-compact-catalog-v1'
DECLARATION = 'fresh-ground-cluster-context-declaration-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'
RULES = ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
SENTINEL = (1 << 64) - 1
ROW = struct.Struct('<11Q32s32s')
WORD = struct.Struct('<Q')
FIELDS = ['tag', 'output_node', 'output_code', 'input0_code', 'input1_code',
          'p0', 'p1', 'p2', 'p3', 'name_index', 'occurrence_index', 'recipe_digest', 'record_digest']


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def verify_pin(pin):
    if set(pin) != {'path', 'sha256', 'bytes'}:
        raise ValueError('exact closed file pin required')
    path = Path(pin['path'])
    if not path.is_absolute() or str(path.resolve()) != str(path):
        raise ValueError('catalog artifact paths are canonical absolute identities')
    h = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); size += len(block)
    if h.hexdigest() != pin['sha256'] or size != pin['bytes']:
        raise ValueError('closed catalog stream changed')


class Ref:
    __slots__ = ('node',)

    def __init__(self, node):
        self.node = node


class CompactCatalog:
    def __init__(self, header_path):
        self.header_path = Path(header_path).resolve()
        self.header = json.loads(self.header_path.read_bytes())
        header = self.header; codec = header['codec']; dimensions = header['dimensions']
        if (header['schema'] != WIRE or header['declaration_schema'] != DECLARATION
                or header['height'] != 24 or header['marking_version'] != MARKING
                or codec['formula_word_bytes'] != 8 or codec['byte_order'] != 'little'
                or codec['recipe_row_bytes'] != ROW.size or codec['sentinel'] != SENTINEL
                or codec['rules'] != list(RULES) or codec['recipe_fields'] != FIELDS
                or set(header['streams']) != {'nodes', 'formulas', 'recipes'}):
            raise ValueError('exact reversible compact codec required')
        self.formula_count = dimensions['formula_count']; self.recipe_count = dimensions['primitive_license_count']
        if (type(self.formula_count) is not int or self.formula_count <= 0
                or type(self.recipe_count) is not int or self.recipe_count < 3
                or dimensions != {'logical_rows': 24, 'formula_count': self.formula_count,
                    'primitive_license_count': self.recipe_count,
                    'non_assumption_witness_count': self.recipe_count - 3, 'source_body_count': 0}):
            raise ValueError('declared complete catalog counts required')
        for pin in header['streams'].values():
            verify_pin(pin)
            if Path(pin['path']).parent != self.header_path.parent:
                raise ValueError('all exact stream files belong to this fresh catalog')
        if (header['streams']['formulas']['bytes'] != 8 * self.formula_count
                or header['streams']['recipes']['bytes'] != ROW.size * self.recipe_count):
            raise ValueError('complete fixed-size stream lengths required')
        self.names = tuple(codec['names'])
        if list(self.names) != sorted(set(self.names)) or not all(type(name) is str for name in self.names):
            raise ValueError('injective sorted command-name table required')
        self.nodes = []
        with gzip.open(header['streams']['nodes']['path'], 'rb') as stream:
            for line in stream:
                value = json.loads(line)
                if type(value) is not list or value[0] != len(self.nodes):
                    raise ValueError('contiguous complete node stream required')
                node = self._node_record(value[1:])
                self.nodes.append(node)
        if len(self.nodes) != codec['node_count']:
            raise ValueError('complete node count mismatch')
        self._formula_file = Path(header['streams']['formulas']['path']).open('rb')
        self._recipe_file = Path(header['streams']['recipes']['path']).open('rb')
        self._formula_map = mmap.mmap(self._formula_file.fileno(), 0, access=mmap.ACCESS_READ)
        self._recipe_map = mmap.mmap(self._recipe_file.fileno(), 0, access=mmap.ACCESS_READ)

    def _node_record(self, value):
        if not value or type(value[0]) is not str:
            raise ValueError('tagged AST node required')
        tag = sys.intern(value[0]); count = len(self.nodes)
        def child(node):
            if type(node) is not int or not 0 <= node < count:
                raise ValueError('strictly prior DAG child required')
            return node
        if tag == 'bot' and len(value) == 1:
            return (tag,)
        if tag == 'var' and len(value) == 2 and type(value[1]) is str:
            return (tag, sys.intern(value[1]))
        if tag in ('fun', 'pred') and len(value) == 3 and type(value[1]) is str and type(value[2]) is list:
            return (tag, sys.intern(value[1]), tuple(child(x) for x in value[2]))
        if tag == 'all' and len(value) == 3 and type(value[1]) is str:
            return (tag, sys.intern(value[1]), child(value[2]))
        if ((tag in ('eq', 'imp', 'and', 'or') and len(value) == 3)
                or (tag == 'not' and len(value) == 2)):
            return (tag, *(child(x) for x in value[1:]))
        raise ValueError('node constructor outside exact compact AST codec')

    def close(self):
        self._formula_map.close(); self._recipe_map.close()
        self._formula_file.close(); self._recipe_file.close()

    def node_record(self, node):
        if type(node) is not int or not 0 <= node < len(self.nodes):
            raise ValueError('exact node index required')
        return self.nodes[node]

    def node_for_formula_code(self, code):
        if type(code) is not int or not 0 <= code < self.formula_count:
            raise ValueError('complete formula code required')
        node = WORD.unpack_from(self._formula_map, code * WORD.size)[0]
        self.node_record(node)
        return node

    def expand_node(self, node):
        rec = self.node_record(node); tag = rec[0]
        if tag in ('var', 'bot'):
            return list(rec)
        if tag in ('fun', 'pred'):
            return [tag, rec[1], [self.expand_node(child) for child in rec[2]]]
        if tag == 'all':
            return [tag, rec[1], self.expand_node(rec[2])]
        return [tag, *(self.expand_node(child) for child in rec[1:])]

    def formula(self, code):
        return self.expand_node(self.node_for_formula_code(code))

    def node_tokens(self, node):
        rec = self.node_record(node); tag = rec[0]
        yield '['; yield canonical(tag)
        if tag == 'var':
            yield ','; yield canonical(rec[1])
        elif tag in ('fun', 'pred'):
            yield ','; yield canonical(rec[1]); yield ',['
            for i, child in enumerate(rec[2]):
                if i:
                    yield ','
                yield from self.node_tokens(child)
            yield ']'
        elif tag == 'all':
            yield ','; yield canonical(rec[1]); yield ','
            yield from self.node_tokens(rec[2])
        elif tag != 'bot':
            for child in rec[1:]:
                yield ','; yield from self.node_tokens(child)
        yield ']'

    def tokens(self, value):
        if isinstance(value, Ref):
            yield from self.node_tokens(value.node)
        elif isinstance(value, dict):
            yield '{'
            for i, key in enumerate(sorted(value)):
                if i:
                    yield ','
                yield canonical(key); yield ':'; yield from self.tokens(value[key])
            yield '}'
        elif isinstance(value, (tuple, list)):
            yield '['
            for i, item in enumerate(value):
                if i:
                    yield ','
                yield from self.tokens(item)
            yield ']'
        else:
            yield canonical(value)

    def registry_tokens(self):
        yield '['
        for code in range(self.formula_count):
            if code:
                yield ','
            yield from self.node_tokens(self.node_for_formula_code(code))
        yield ']'

    def row(self, index):
        if type(index) is not int or not 0 <= index < self.recipe_count:
            raise ValueError('complete recipe index required')
        fields = ROW.unpack_from(self._recipe_map, index * ROW.size)
        tag, node, output, i0, i1, p0, p1, p2, p3, name, occurrence = fields[:11]
        if tag >= len(RULES) or self.node_for_formula_code(output) != node:
            raise ValueError('exact output code/node relation required')
        params = (p0, p1, p2, p3)
        if tag == 3:
            if (i0 == SENTINEL or i1 == SENTINEL or any(x != SENTINEL for x in params)
                    or name != SENTINEL or occurrence != SENTINEL):
                raise ValueError('exact binary MP row grammar required')
            self.node_for_formula_code(i0); self.node_for_formula_code(i1)
        elif i0 != SENTINEL or i1 != SENTINEL:
            raise ValueError('only MP has ordered input ports')
        if tag == 0:
            if name >= len(self.names) or any(x != SENTINEL for x in params) or occurrence != SENTINEL:
                raise ValueError('exact named-axiom row required')
        elif tag == 1:
            self.node_record(p0); self.node_record(p1)
            if p2 != SENTINEL or p3 != SENTINEL or name != SENTINEL or occurrence != SENTINEL:
                raise ValueError('exact instantiation row required')
        elif tag == 2:
            for param in (p0, p1, p2):
                self.node_record(param)
            if p3 != SENTINEL or name >= len(self.names) or occurrence != SENTINEL:
                raise ValueError('exact equality-scheme row required')
        elif tag == 4:
            if occurrence not in (0, 1, 2) or name != SENTINEL or any(x != SENTINEL for x in params):
                raise ValueError('exact indexed local-assumption row required')
        return fields

    def recipe_meta(self, index):
        fields = self.row(index); tag, node, output, i0, i1 = fields[:5]
        return {'identifier': 'primitive-recipe-' + fields[11].hex(), 'rule': RULES[tag],
                'output': output, 'inputs': (i0, i1) if tag == 3 else ()}

    def compact_witness(self, index):
        row = self.row(index); tag, node, output, i0, i1, p0, p1, p2, p3, name, occurrence = row[:11]
        witness = {'rule': RULES[tag], 'formula': Ref(node)}
        if tag == 0:
            witness['name'] = self.names[name]
        elif tag == 1:
            witness.update(universal=Ref(p0), term=Ref(p1))
        elif tag == 2:
            witness.update(variable=self.names[name], template=Ref(p0), left=Ref(p1), right=Ref(p2))
        elif tag == 4:
            witness['index'] = occurrence
        return witness

    def witness(self, index):
        return {key: self.expand_node(value.node) if isinstance(value, Ref) else value
                for key, value in self.compact_witness(index).items()}

    def premises(self, index):
        return [self.formula(code) for code in self.recipe_meta(index)['inputs']]

    def identity_preimage_refs(self, index):
        row = self.row(index); authority = self.header['authority']
        result = {'recipe': {'primitive_witness': self.compact_witness(index),
                            'ordered_premise_formulas': [Ref(self.node_for_formula_code(code))
                                for code in self.recipe_meta(index)['inputs']]},
                  'primitive_authority_epoch': authority['epoch'],
                  'recipient_theory_sha256': authority['recipient_theory_sha256'],
                  'marking_version': self.header['marking_version'],
                  'formula_registry_sha256': self.header['formula_registry_sha256']}
        if row[0] == 4:
            result['local_context_id'] = self.header['context_id']
        return result

    def identity_tokens(self, index):
        yield from self.tokens(self.identity_preimage_refs(index))

    def recipe_record_tokens(self, index):
        preimage = self.identity_preimage_refs(index)
        yield from self.tokens({'id': self.recipe_meta(index)['identifier'],
            'primitive_witness': preimage['recipe']['primitive_witness'],
            'ordered_premise_formulas': preimage['recipe']['ordered_premise_formulas'],
            'identity_preimage': preimage})

    def recipe_record(self, index):
        preimage = json.loads(''.join(self.identity_tokens(index)))
        return {'id': self.recipe_meta(index)['identifier'],
                'primitive_witness': preimage['recipe']['primitive_witness'],
                'ordered_premise_formulas': preimage['recipe']['ordered_premise_formulas'],
                'identity_preimage': preimage}

    def license_record(self, index):
        row = self.row(index); meta = self.recipe_meta(index)
        return {'recipe_index': index, 'recipe_id': meta['identifier'], 'rule': meta['rule'],
                'record_sha256': row[12].hex(), 'logical_accepted': False, 'native_accepted': False,
                'status': 'pending independent exact primitive license'}

    def recipe_index_for_id(self, identifier):
        if type(identifier) is not str or not identifier.startswith('primitive-recipe-'):
            raise ValueError('exact primitive identity required')
        try:
            digest = bytes.fromhex(identifier[len('primitive-recipe-'):])
        except ValueError:
            raise ValueError('exact primitive SHA256 identity required')
        if len(digest) != 32:
            raise ValueError('exact primitive SHA256 identity required')
        found = None
        for index in range(self.recipe_count):
            if self.row(index)[11] == digest:
                if found is not None:
                    raise ValueError('duplicate complete primitive identity')
                found = index
        if found is None:
            raise ValueError('primitive identity absent from complete catalog')
        return found
