"""SOURCE ONLY: V3 bounded exact canonical identity emission, full grammar.

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
import time
from functools import lru_cache
from collections import OrderedDict
from pathlib import Path

DECLARATION = 'fresh-ground-cluster-context-declaration-v1'
WIRE = 'fresh-ground-compact-catalog-v1'
MARKING = 'injective-formula-ordered-mp-offset-v1'
# SOURCE-only recipient profile; original cases remain syntax seeds only.
FIXTURE_SCHEMA = 'hilbert-next-ground-theorem-fixtures-v1'
RECIPIENT_IDS = ('next-inc-equality-line-chain', 'next-inc-two-uniqueness', 'next-inc-derived-middle-guard', 'fresh-inc-point-chain-w', 'fresh-inc-reversed-line-chain')
SEED_CASE_IDS = ('train-pa-right-zero', 'train-pa-right-one', 'train-inc-line', 'train-inc-point', 'train-inc-uniqueness', 'eval-pa-chain', 'eval-pa-nested', 'eval-inc-both-arguments', 'eval-inc-uniqueness-point')
# Explicit pilot selectable profile; the full original12-case declaration
# and all same-theory syntax seeds remain byte-for-byte unchanged.
ACTIVE_CASE_IDS = ('fresh-inc-point-chain-w', 'fresh-inc-reversed-line-chain')
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


class PhaseTelemetry:
    """Pinned, bounded diagnostic emissions; never a licensing authority.

    The caller owns append-only serialization and complete owned-phase clocks.
    Callback return values never affect compilation. Exceptions/cap violations
    propagate; only ROOT can label the resulting partial attempt UNKNOWN.
    """
    def __init__(self, callback, source_bindings):
        self.callback = callback; self.records = 0; self.progress_records = 0
        self.polls = 0; self.last_progress = None
        if callback is None:
            return
        if not callable(callback):
            raise ValueError('optional telemetry must be one source-pinned callable')
        code = getattr(callback, '__code__', None)
        if code is None:
            code = getattr(getattr(callback, '__call__', None), '__code__', None)
        if code is None:
            raise ValueError('telemetry callback has no inspectable reviewed source origin')
        origin = Path(code.co_filename).resolve()
        root = Path(__file__).resolve().parents[2]
        matches = []
        for binding in source_bindings:
            if type(binding) is not dict or set(binding) != {'path', 'sha256', 'bytes'}:
                raise ValueError('exact source-binding pins required for diagnostic origin')
            declared = Path(binding['path'])
            actual = declared if declared.is_absolute() else root / declared
            if actual.resolve() == origin:
                matches.append(binding)
        if len(matches) != 1:
            raise ValueError('one exact telemetry callback source pin must be in authority bindings')
        observed = pin(origin); declared = matches[0]
        if observed['sha256'] != declared['sha256'] or observed['bytes'] != declared['bytes']:
            raise ValueError('telemetry callback source bytes changed')
        self.source_pin = declared
        self.last_progress = time.perf_counter()

    def emit(self, phase, milestone, counters, progress=False):
        if self.callback is None:
            return
        if (type(phase) is not str or type(milestone) is not str
                or not 0 < len(phase) <= 80 or not 0 < len(milestone) <= 80
                or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for ch in phase + milestone)
                or type(counters) is not dict or len(counters) > 12
                or any(type(key) is not str or not 0 < len(key) <= 64
                    or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for ch in key)
                    or type(value) is not int or not 0 <= value <= SENTINEL
                    for key, value in counters.items())):
            raise ValueError('bounded scalar diagnostic event grammar required')
        event = {'phase': phase, 'milestone': milestone, 'counters': dict(counters)}
        if len(canonical(event).encode('utf8')) > 4096:
            raise ValueError('diagnostic event exceeds frozen4096-byte envelope')
        if self.records >= 512 or progress and self.progress_records >= 480:
            raise ValueError('diagnostic event count exceeds frozen bounded envelope')
        self.records += 1
        if progress:
            self.progress_records += 1
        self.callback(event)

    def poll(self, phase, counters):
        if self.callback is None:
            return
        self.polls += 1
        if self.polls % 4096:
            return
        now = time.perf_counter()
        if now - self.last_progress < 1.0:
            return
        self.last_progress = now
        self.emit(phase, 'progress', counters, progress=True)


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


class CanonicalNodeBytes:
    """Per-invocation immutable AST bytes, with a strictly bounded LRU.

    Payload <=8MiB, entries <=16384, individual cached value <=64KiB. The
    separate saturating length memo uses4 bytes per declared DAG node. These
    are allocation-accounting limits, not a proof of process RSS. Oversized
    nodes are streamed exactly, never excluded or treated as invalid syntax.
    """
    PAYLOAD_LIMIT = 8 * 1024 * 1024
    ENTRY_LIMIT = 16384
    NODE_LIMIT = 64 * 1024
    FAST_ROW_LIMIT = 128 * 1024
    LENGTH_SATURATION = FAST_ROW_LIMIT + 1

    def __init__(self, arena):
        self.arena = arena; self.node_count = len(arena.nodes)
        self.lengths = array.array('I', [0]) * self.node_count
        if self.lengths.itemsize != 4:
            raise ValueError('source-bound compact length memo requires4-byte unsigned integer')
        self.values = OrderedDict(); self.payload_bytes = 0

    def scalar(self, value):
        return (quoted(value) if type(value) is str else canonical(value)).encode('utf8')

    def node_length(self, node):
        cached = self.lengths[node]
        if cached:
            return cached
        rec = self.arena.nodes[node]; tag = rec[0]
        if tag in ('var', 'bot'):
            value = rec
        elif tag in ('fun', 'pred'):
            value = (tag, rec[1], tuple(Ref(child) for child in rec[2]))
        elif tag == 'all':
            value = (tag, rec[1], Ref(rec[2]))
        else:
            value = (tag, *(Ref(child) for child in rec[1:]))
        result = self.value_length(value)
        self.lengths[node] = result
        return result

    def value_length(self, value):
        cap = self.LENGTH_SATURATION
        if isinstance(value, Ref):
            return self.node_length(value.node)
        if isinstance(value, dict):
            size = 2
            for i, key in enumerate(sorted(value)):
                size += (1 if i else 0) + len(self.scalar(key)) + 1 + self.value_length(value[key])
                if size >= cap:
                    return cap
            return size
        if isinstance(value, (tuple, list)):
            size = 2
            for i, item in enumerate(value):
                size += (1 if i else 0) + self.value_length(item)
                if size >= cap:
                    return cap
            return size
        return min(cap, len(self.scalar(value)))

    def node_chunks(self, node):
        cached = self.values.get(node)
        if cached is not None:
            self.values.move_to_end(node)
            yield cached
            return
        if self.node_length(node) > self.NODE_LIMIT:
            yield from self.raw_node_chunks(node)
            return
        value = b''.join(self.raw_node_chunks(node))
        # The memoized structural length is an eligibility hint only. This
        # relation check fails UNKNOWN if implementation bytes disagree.
        if len(value) != self.node_length(node):
            raise ValueError('canonical node byte-length relation mismatch')
        while self.values and (self.payload_bytes + len(value) > self.PAYLOAD_LIMIT
                               or len(self.values) >= self.ENTRY_LIMIT):
            _, evicted = self.values.popitem(last=False)
            self.payload_bytes -= len(evicted)
        self.values[node] = value; self.payload_bytes += len(value)
        yield value

    def raw_node_chunks(self, node):
        rec = self.arena.nodes[node]; tag = rec[0]
        yield b'['; yield self.scalar(tag)
        if tag == 'var':
            yield b','; yield self.scalar(rec[1])
        elif tag in ('fun', 'pred'):
            yield b','; yield self.scalar(rec[1]); yield b',['
            for i, child in enumerate(rec[2]):
                if i:
                    yield b','
                yield from self.node_chunks(child)
            yield b']'
        elif tag == 'all':
            yield b','; yield self.scalar(rec[1]); yield b','
            yield from self.node_chunks(rec[2])
        elif tag != 'bot':
            for child in rec[1:]:
                yield b','; yield from self.node_chunks(child)
        yield b']'

    def value_chunks(self, value):
        if isinstance(value, Ref):
            yield from self.node_chunks(value.node)
        elif isinstance(value, dict):
            yield b'{'
            for i, key in enumerate(sorted(value)):
                if i:
                    yield b','
                yield self.scalar(key); yield b':'
                yield from self.value_chunks(value[key])
            yield b'}'
        elif isinstance(value, (tuple, list)):
            yield b'['
            for i, item in enumerate(value):
                if i:
                    yield b','
                yield from self.value_chunks(item)
            yield b']'
        else:
            yield self.scalar(value)

    def clear(self):
        self.values.clear(); self.payload_bytes = 0


class ExactIdentityEmitter:
    """Factor only the unchanged canonical identity and legacy-record bytes.

    Every record is still independently hashed, in the original full recipe
    order. This object is created for one already-fixed arena/registry/theory/
    context/authority epoch and is never shared between declarations. A row
    outside the bounded fast path uses the unchanged original stream_digest.
    """
    def __init__(self, arena, registry, authority, context_id):
        self.arena = arena; self.cache = CanonicalNodeBytes(arena)
        self.registry = registry; self.authority = dict(authority); self.context_id = context_id
        scalar = self.cache.scalar
        first = b'{"formula_registry_sha256":' + scalar(registry)
        common = (b',"marking_version":' + scalar(MARKING)
                  + b',"primitive_authority_epoch":' + scalar(authority['epoch'])
                  + b',"recipe":')
        self.prefix = first + common
        self.assumption_prefix = first + b',"local_context_id":' + scalar(context_id) + common
        self.suffix = b',"recipient_theory_sha256":' + scalar(authority['recipient_theory_sha256']) + b'}'

    def hashes(self, preimage):
        if len(self.arena.nodes) != self.cache.node_count:
            raise ValueError('identity memo requires the complete immutable original AST arena')
        expected = {'recipe', 'primitive_authority_epoch', 'recipient_theory_sha256',
                    'marking_version', 'formula_registry_sha256'}
        witness = preimage['recipe']['primitive_witness']
        premises = preimage['recipe']['ordered_premise_formulas']
        assumption = witness['rule'] == 'assumption'
        if assumption:
            expected.add('local_context_id')
        if (set(preimage) != expected
                or set(preimage['recipe']) != {'primitive_witness', 'ordered_premise_formulas'}
                or preimage['primitive_authority_epoch'] != self.authority['epoch']
                or preimage['recipient_theory_sha256'] != self.authority['recipient_theory_sha256']
                or preimage['marking_version'] != MARKING
                or preimage['formula_registry_sha256'] != self.registry
                or assumption and preimage['local_context_id'] != self.context_id):
            raise ValueError('exact immutable canonical preimage context mismatch')
        size = self.cache.value_length(witness) + self.cache.value_length(premises)
        if size > self.cache.FAST_ROW_LIMIT:
            recipe_hash = stream_digest(preimage, self.arena)
            record_hash = stream_digest({'id': 'primitive-recipe-' + recipe_hash,
                'primitive_witness': witness, 'ordered_premise_formulas': premises,
                'identity_preimage': preimage}, self.arena)
            return recipe_hash, record_hash
        witness_bytes = b''.join(self.cache.value_chunks(witness))
        premise_bytes = b''.join(self.cache.value_chunks(premises))
        if len(witness_bytes) + len(premise_bytes) != size:
            raise ValueError('canonical primitive fragment byte-length relation mismatch')
        identity_parts = (self.assumption_prefix if assumption else self.prefix,
            b'{"ordered_premise_formulas":', premise_bytes,
            b',"primitive_witness":', witness_bytes, b'}', self.suffix)
        identity_hash = hashlib.sha256()
        for part in identity_parts:
            identity_hash.update(part)
        recipe_hash = identity_hash.hexdigest()
        record_hash = hashlib.sha256()
        record_hash.update(b'{"id":' + self.cache.scalar('primitive-recipe-' + recipe_hash)
                           + b',"identity_preimage":')
        for part in identity_parts:
            record_hash.update(part)
        record_hash.update(b',"ordered_premise_formulas":')
        record_hash.update(premise_bytes)
        record_hash.update(b',"primitive_witness":')
        record_hash.update(witness_bytes); record_hash.update(b'}')
        return recipe_hash, record_hash.hexdigest()

    def close(self):
        self.cache.clear()
        self.cache = None


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
    if (fixture.get('schema') != FIXTURE_SCHEMA
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


def compile_to_directory(fixture, instance_id, source_bindings, output_directory, telemetry=None):
    """Whole V1 grammar in exclusive stream artifacts; no model/proof is built.

    Optional telemetry is source-pinned diagnostics only; no logical authority.
    Returned header is small. Output must be a fresh directory. Temporary sort
    runs are implementation scratch, not source/authority omissions. Nothing
    here asserts fit within ROOT's unchanged60s/512MiB full-owned envelope.
    """
    if (type(fixture) is not dict or fixture.get('schema') != FIXTURE_SCHEMA
            or type(instance_id) is not str or instance_id not in ACTIVE_CASE_IDS
            or fixture.get('recipient_case_ids') != list(RECIPIENT_IDS)
            or fixture.get('source_only_seed_case_ids') != list(SEED_CASE_IDS)
            or [case['id'] for case in fixture['cases']] != list(SEED_CASE_IDS + RECIPIENT_IDS)):
        raise ValueError('three new geometry recipients; nine original syntax-only seeds required')
    diagnostic = PhaseTelemetry(telemetry, source_bindings)
    diagnostic.emit('syntax', 'begin', {})
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
    diagnostic.emit('syntax', 'complete', {'formulas': len(fs), 'nodes': len(arena.nodes),
        'seed_terms': len(seed_terms), 'term_roles': len(pools)})
    recipes_order = ExternalOrder(scratch, 'recipes'); instantiations = set(); rounds = []
    replace_cache = {}
    def add_witness(witness, premises=()):
        key = ''.join(tokens([witness_refs(witness), [Ref(x) for x in premises]], arena))
        recipes_order.add(key, [witness, list(premises)])
    for name, literal in sorted(theory['axioms'].items()):
        add_witness({'rule': 'axiom', 'name': name, 'formula': arena.formula(literal, theory)})
    for round_index in range(4):
        diagnostic.emit('instantiation', 'round_begin', {'round': round_index,
            'formulas': len(fs), 'schemes': len(instantiations), 'nodes': len(arena.nodes)})
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
                diagnostic.poll('instantiation', {'round': round_index,
                    'universals': len(universals), 'schemes': len(instantiations),
                    'formulas': len(fs), 'nodes': len(arena.nodes)})
        rounds.append({'round': round_index, 'universal_count': len(universals),
                       'new_distinct_schemes': len(instantiations) - before,
                       'scheme_count': len(instantiations), 'formula_count': len(fs)})
        diagnostic.emit('instantiation', 'round_complete', {'round': round_index,
            'universals': len(universals), 'new_schemes': len(instantiations) - before,
            'schemes': len(instantiations), 'formulas': len(fs), 'nodes': len(arena.nodes)})
    diagnostic.emit('templates', 'begin', {'formulas': len(fs), 'nodes': len(arena.nodes)})
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
        diagnostic.poll('templates', {'atomic_sources': len(atoms), 'templates': len(templates),
            'pairs': len(pairs), 'nodes': len(arena.nodes)})
    diagnostic.emit('templates', 'complete', {'atomic_sources': len(atoms),
        'templates': len(templates), 'pairs': len(pairs), 'nodes': len(arena.nodes)})
    diagnostic.emit('equality_product', 'begin', {'templates': len(templates),
        'pairs': len(pairs), 'declared_product': len(templates) * len(pairs)})
    equality_visits = 0
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
            equality_visits += 1
            diagnostic.poll('equality_product', {'visits': equality_visits,
                'declared_product': len(templates) * len(pairs), 'formulas': len(fs),
                'nodes': len(arena.nodes), 'recipe_records_spooled': recipes_order.count})
        replace_cache.clear()
    equality_count = len(templates) * len(pairs)
    diagnostic.emit('equality_product', 'complete', {'visits': equality_visits,
        'declared_product': equality_count, 'formulas': len(fs), 'nodes': len(arena.nodes),
        'recipe_records_spooled': recipes_order.count})
    # Release memoization state before the complete final sorting/identity pass.
    replace_cache.clear(); abstract_cache.clear(); term_seen.clear(); terms.clear(); instantiations.clear()
    diagnostic.emit('formula_registry', 'begin', {'formulas': len(fs),
        'nodes': len(arena.nodes), 'recipe_records_spooled': recipes_order.count})
    diagnostic.emit('formula_sort', 'begin', {'formulas': len(fs), 'nodes': len(arena.nodes)})
    formula_order = ExternalOrder(scratch, 'formulas')
    for node in fs:
        formula_order.add(arena.text(node), node)
        diagnostic.poll('formula_sort', {'keys_spooled': formula_order.count,
            'sort_runs': len(formula_order.runs), 'formulas': len(fs)})
    diagnostic.emit('formula_sort', 'keys_complete', {'keys_spooled': formula_order.count,
        'sort_runs': len(formula_order.runs), 'formulas': len(fs)})
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
            diagnostic.poll('formula_registry', {'formulas_serialized': code + 1,
                'recipe_records_spooled': recipes_order.count, 'nodes': len(arena.nodes)})
    registry_hasher.update(b']'); registry = registry_hasher.hexdigest()
    diagnostic.emit('formula_registry', 'complete', {'formulas_serialized': len(ordered_ids),
        'recipe_records_spooled': recipes_order.count, 'nodes': len(arena.nodes)})
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
    diagnostic.emit('recipe_identity', 'begin', {'recipe_records_spooled': recipes_order.count,
        'sort_runs': len(recipes_order.runs), 'formulas': len(ordered_ids)})
    diagnostic.emit('recipe_sort', 'begin', {'recipe_records_spooled': recipes_order.count,
        'sort_runs': len(recipes_order.runs)})
    assumptions = {}; recipe_path = output / 'recipes-v1.bin'; recipe_count = 0
    identity_emitter = ExactIdentityEmitter(arena, registry, authority, context_id)
    with recipe_path.open('xb') as stream:
        for index, (witness, premises) in enumerate(recipes_order.ordered()):
            if index == 0:
                diagnostic.emit('recipe_sort', 'first_record_ready', {'recipe_records_spooled': recipes_order.count})
            rule = witness['rule']; refs = witness_refs(witness)
            preimage = {'recipe': {'primitive_witness': refs, 'ordered_premise_formulas': [Ref(x) for x in premises]},
                        'primitive_authority_epoch': authority['epoch'],
                        'recipient_theory_sha256': authority['recipient_theory_sha256'],
                        'marking_version': MARKING, 'formula_registry_sha256': registry}
            if rule == 'assumption':
                preimage['local_context_id'] = context_id; assumptions[witness['index']] = index
            recipe_hash, record_hash = identity_emitter.hashes(preimage)
            identifier = 'primitive-recipe-' + recipe_hash
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
            diagnostic.poll('recipe_identity', {'recipes_serialized': recipe_count,
                'recipe_records_spooled': recipes_order.count, 'assumption_occurrences': len(assumptions)})
    identity_emitter.close()
    diagnostic.emit('recipe_sort', 'complete', {'recipes_serialized': recipe_count})
    diagnostic.emit('recipe_identity', 'complete', {'recipes_serialized': recipe_count,
        'recipe_records_spooled': recipes_order.count, 'assumption_occurrences': len(assumptions)})
    if set(assumptions) != {0, 1, 2} or recipe_count != recipes_order.count:
        raise ValueError('complete recipes and all distinct occurrence identities required')
    diagnostic.emit('nodes', 'begin', {'nodes': len(arena.nodes),
        'formulas': len(ordered_ids), 'recipes': recipe_count})
    nodes_path = output / 'nodes-v1.jsonl.gz'
    with nodes_path.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            for node, rec in enumerate(arena.nodes):
                stream.write((canonical([node, *rec]) + '\n').encode('utf8'))
                diagnostic.poll('nodes', {'nodes_serialized': node + 1, 'nodes': len(arena.nodes)})
    diagnostic.emit('nodes', 'complete', {'nodes_serialized': len(arena.nodes)})
    diagnostic.emit('header', 'begin', {'formulas': len(ordered_ids),
        'recipes': recipe_count, 'nodes': len(arena.nodes)})
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
    diagnostic.emit('header', 'ready_for_serialization', {'formulas': len(ordered_ids),
        'recipes': recipe_count, 'nodes': len(arena.nodes), 'stream_files_closed': 3})
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
