"""UNEXECUTED separate proof-neutral cold Q controls worker proposal.

ROOT alone supplies genuine plans/reviews/conformance/activation and executes.
Only this wrapper, calibration callable, current driver, unchanged graph and
independent checker execute. Scientific subject/master and original producer7
remain raw provenance. No production driver search, library/rank/RL.
One20 includes all successful work and output; only honest failure rollback and
metadata may use whole55/500 inside owned60/512 and genuine caller90.
"""
import hashlib
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import types

ROOT=Path(__file__).resolve().parents[2]
SCHEMA='ROOT-Q-first-proof-neutral-controls-worker-plan-v1'
SCOPE='proof-neutral-cold-Q-initial-passive-rollback-and-calibration-controls-only'
COMMAND='ROOT-Q-first-proof-neutral-controls'
AUTHOR='/root/hilbert_ordering_diagnosis'
LIMITS=dict(whole_seconds=60,peak_bytes=536870912,caller_seconds=90,control_seconds=20)
MAX_METADATA=64*1048576
RECEIPT='Q-proof-neutral-controls-worker-receipt-v1.json'
DRIVER_REVIEW={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-search-independent-source-20261014/typed-Source-review-v4.json', 'sha256': 'e8cc81d11fe1f3a0b80229124d799cdef4beea06851b6ee6085b7325a1f29968', 'bytes': 4185}
CALIBRATION={'bytes': 20900, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-conformance-source-20261014/Q_first_proof_controls_v1.py', 'sha256': 'b4fb14e8eddc9a10ccb4ccb09891c069feff82cf7e2e58fffec4bb8caef24612'}
SCIENTIFIC_SUBJECT={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-allocation-endpoint-slice-source-20261014/Q_first_selected_cold_worker_endpoint_slice_v14.py', 'sha256': 'afde50a50a53176ad893b2ccf95f8e0a2a6da900a4a9d8336c4cc9c8a65697e3', 'bytes': 159170}
SOURCE_ROLES={'worker','calibration','driver','point_graph','independent_checker','scientific_worker_subject','master'}
EXECUTED_ROLES=('worker','calibration','driver','point_graph','independent_checker')
AUDITOR={'bytes': 46514, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/independent_Q_semantics_v1.py', 'sha256': '1717c716842886935c838a825b9c088810935acf101943e15eba6c5af7aec1c3'}
MASTER={'bytes': 21657, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md', 'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}
PRODUCER_SOURCES={'catalogue': {'bytes': 10187, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_catalog_v1.py', 'sha256': '2db11af0d7206afd4e1c10b53b97c16f98064c14fd1e57a9a2ca34c0a602348a'}, 'controls': {'bytes': 19742, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_v3.py', 'sha256': '4e28fadd9c76ba6664e485fa2c5aa97beaa08639986b6d56aae50395b006e638'}, 'kernel': {'bytes': 10323, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_kernel_v1.py', 'sha256': '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'}, 'master': {'bytes': 21657, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md', 'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}, 'payload': {'bytes': 5435, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/q_preparation_owned_graph_v3.py', 'sha256': 'ee2088bf60709f6c0c5a78297841bd0684674369fa9d3c08119b96a59caa88ad'}, 'point_graph': {'bytes': 28531, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py', 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'}, 'worker': {'bytes': 37266, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-source-20261014/arithmetic_Q_streamed_controls_worker_v7.py', 'sha256': '75d5d80701a0815d78e182a5cb7eb99412bff5b48a5b936a8850b625743de48d'}}
FROZEN_INPUTS={'declaration': {'bytes': 2683, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/Q-declaration-v1.json', 'sha256': 'e28e914fc01100fd75c12f1b271ec6ead107f211b4c91060d98c95e524d46fcc'}, 'initial_oracle_domains': {'bytes': 8295473, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-initial-oracle-domains-v2.json', 'sha256': '03c42ca0083d5e40363d5237d69af56df4ebe3b3ae7d88fa3720fae3390d6969'}, 'initial_state': {'bytes': 8296118, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-initial-state-witness-v2.json', 'sha256': 'c7e8cfd099b1b80ae170b6c35591d68d56f37aecb38f1bcf7b567d2e019acbb9'}, 'producer_ROOT_final_decision': {'bytes': 2810, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/preparation-ROOT-final-decision-v1.json', 'sha256': 'ba68f21a9a8bcc32402d6057d6bfff1b443a8c95207ade185fef194a9406fd49'}, 'producer_ROOT_reconciled_disposition': {'bytes': 8797, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/ROOT-actual-Q-streamed-controls-reconciled-disposition-v2.json', 'sha256': 'e52a47fe3ffa562a81d2084150eacec11c11be87e96def01ee728afaa4bd88ef'}, 'producer_evidence': {'bytes': 11000, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-controls-evidence-v1.json', 'sha256': '1c4069230b761d905046810f012f9d5ab6f4bf814674bdb90d3cb0ceaf8f6bb7'}, 'producer_preparation': {'bytes': 38376960, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-preparation-provisional-v1.json', 'sha256': '0321a462025357d188793bd45a44670adc20776e9ba30574049d77a8b5935d3a'}, 'producer_receipt': {'bytes': 5595, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-output-v1/Q-controls-result-v1.json', 'sha256': 'a6cc241c7c5408951979981f5de6c8e2d0d6be38cdbfe0fe16a365fa3085ede4'}, 'producer_worker_plan': {'bytes': 16547, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-streamed-controls-progress-20261014/worker-plan-v1.json', 'sha256': 'f44b778167aeefbcb561d60279f4ece55552639f6e58d6f31a53cd778aeba4d9'}, 'finite_ROOT_admission': {'bytes': 8563, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-audit-shared-wire-progress-20261014/ROOT-actual-independent-Q-shared-wire-audit-reconciled-disposition-v2.json', 'sha256': '80dee8b9ec1bca398c24d61c10a026a82f73c8886cdeeb0ed9bf9ea5cf9c1ff1'}, 'finite_audit_certificate': {'bytes': 5789, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-audit-shared-wire-progress-20261014/worker-output-v1/Q-independent-audit-certificate-provisional-v1.json', 'sha256': '3c3aefa4ff9d918a43a8b73d94fd6cebf0741e6203e0d47f3a44fbd716c7bc87'}, 'actual_word_controls_ROOT': {'bytes': 6796, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-word-controls-progress-20261014/ROOT-actual-unrelated-word-controls-reconciled-disposition-v1.json', 'sha256': 'f254219dc8e7324a7d15f9ff50661de627d207eca08660bca354e73978d39fd1'}, 'driver_contract': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-search-source-20261014/source-contract-v4.json', 'sha256': 'f7968455c47cfc5af2288483088f44bc6ff9298f05d7839fcfe2bbaadf4d934c', 'bytes': 31853}, 'driver_handoff': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-search-source-20261014/handoff-v4.json', 'sha256': '53c8118923e44a4220eacec25a6b14760638ef4f780154b9f534d90223b3690c', 'bytes': 13719}, 'checker_contract': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-independent-mathematical-audit-source-20261014/source-contract-v1.json', 'sha256': 'de26586799af2c8143fe744590dc2d76789836735342a8d6b582583d3b870e51', 'bytes': 16116}, 'calibration_fixtures': {'bytes': 44944, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-conformance-source-20261014/complete-fixtures-v1.json', 'sha256': '33653a01161786fd95760d75a3d35ecfbafc2fa56afe41d776c3d96c84edde7d'}, 'calibration_contract': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-conformance-source-20261014/source-contract-v3.json', 'sha256': '4a0e8e9e5107c5401ac2593a324870ecbd4d138528f95ff5d09686ff59080abe', 'bytes': 20920}, 'calibration_handoff': {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-conformance-source-20261014/handoff-v3.json', 'sha256': 'b498a38dec17564cf59147bb4ae3d3fecca2db4180b2d446bc6533f603b2db55', 'bytes': 12465}, 'calibration_coverage': {'bytes': 6818, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-conformance-source-20261014/result-and-coverage-schema-v1.json', 'sha256': '7d3fc5439f5f7dafcef082db3e206ce74ce55a0f21dcb67d0faa1b89d0c6adb0'}, 'minimal_controls_plan': {'bytes': 14279, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-search-independent-source-20261014/minimal-control-acceptance-plan-v1.json', 'sha256': 'a80011e2d89cc345a72a1ea92bcffcd7726bd403e927066388e238b785adc370'}}
DRIVER={'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-Q-first-proof-search-source-20261014/Q_first_selected_proof_v3.py', 'sha256': '8dcfa3d82ecd374c70a2a931c0a0c2334fb5e8be3d2a0fc104d66079d4fb5426', 'bytes': 46691}
GRAPH={'bytes': 28531, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py', 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567'}
CURRENT={'complete_frozen_grammar': {'equality_operand_pairs': 'all_ordered_pairs', 'equality_template_other_terms': 'complete_operand_pool', 'generalization_sources': 'all_resulting_parameter_scoped_equality_atoms', 'hole_context_node_bound': 2, 'instantiation_rounds': 2, 'target_and_axiom_open_subterms': True, 'target_seed_is_formula_only': True, 'term_node_bound': 3}, 'formula_registry_sha256': '4a12ada631861b1637b7d5e17e76c45b9a942816c412f5a6f0fc48c1698eb7fe', 'initial_domain_candidate_count': 36734657, 'initial_rows': 24, 'meaning': '11147/16200 are authenticated complete actual observations, not shortcuts or desired counts. Use the whole admitted raw registry/recipes/preimages and all24 domains. No recompile/trim, no stronger induction/FOL/PA/native authority.', 'model_epoch': '3a8854e0e0137d125dfa8af8870be04e4242ec2e7036b6bb8977cd33ad1454f9', 'observed_full_formula_count': 11147, 'observed_full_recipe_count': 16200, 'ordered_Gamma': [], 'parameters': ['n'], 'primitive_authority_epoch': '4ac41a90b9655036e2e7ed6cd7d9a971b9097d6b2c7d0f70e8408b8d93a54039', 'rules': ['axiom', 'assumption', 'instantiate', 'eq_subst', 'mp', 'generalize'], 'target': ['all', 'n', ['eq', ['fun', 'add', [['var', 'n'], ['fun', 'succ', [['fun', 'zero', []]]]]], ['fun', 'succ', [['var', 'n']]]]], 'target_latex': '\\forall n\\,\\bigl(n+S(0)=S(n)\\bigr)'}

def need(value, label):
    if not value:
        raise ValueError(label)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def pin(path):
    path = Path(path)
    need(path.is_absolute() and str(path.resolve()) == str(path) and not path.is_symlink(), 'canonical ABS pin')
    h = hashlib.sha256(); count = 0; before = path.stat()
    with path.open('rb') as stream:
        for raw in iter(lambda: stream.read(65536), b''):
            h.update(raw); count += len(raw)
    after = path.stat()
    need((before.st_dev,before.st_ino,before.st_mtime_ns,before.st_size) ==
         (after.st_dev,after.st_ino,after.st_mtime_ns,after.st_size), 'whole stable raw bytes')
    return dict(path=str(path), sha256=h.hexdigest(), bytes=count)

def verify(record):
    need(type(record) is dict and set(record) == {'path','sha256','bytes'}
         and type(record['bytes']) is int and record['bytes'] >= 0
         and type(record['sha256']) is str and len(record['sha256']) == 64
         and all(c in '0123456789abcdef' for c in record['sha256'])
         and pin(record['path']) == record, 'typed canonical full pin')
    return record

def parse(raw):
    def unique(pairs):
        result = {}
        for name, value in pairs:
            need(name not in result, 'duplicate JSON field'); result[name] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError('nonfinite JSON '+token)))

def read(record, maximum=MAX_METADATA):
    verify(record)
    with Path(record['path']).open('rb') as stream:
        raw = stream.read(maximum+1)
        need(len(raw) <= maximum and stream.read(1) == b'', 'whole bounded raw buffer, no prefix')
    need(len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256'],
         'parse the authenticated same raw buffer')
    value = parse(raw); verify(record); return value

def normalize(record):
    path = Path(record['path']); actual = path if path.is_absolute() else ROOT/path
    return dict(record, path=str(actual))

def value_state(value):
    """Detect ordinary namespace/default mutation without accepting origin claims."""
    if value is None or type(value) in (str, int, bool, float, list, dict, tuple):
        try: return canonical(value)
        except (TypeError, ValueError): pass
    return None

def executable_state(module, *, class_roots=()):
    state = []; namespaces = []; mros = []; seen_classes = set()
    def keys(owner):
        return tuple(k for k in vars(owner) if not k.startswith('__') and k != '_NEXT_CAPSULE')
    def add(owner, name, value):
        if isinstance(value, (staticmethod, classmethod)): value = value.__func__
        code = value.__code__ if inspect.isfunction(value) else None
        defaults = (value_state(value.__defaults__), value_state(value.__kwdefaults__)) if code else None
        closure = tuple((cell.cell_contents, value_state(cell.cell_contents))
                        for cell in (value.__closure__ or ())) if code else None
        state.append((owner, name, value, code, defaults, closure, value_state(value)))
        if isinstance(value, property):
            # The descriptor object can stay unchanged while its getter code mutates.
            for accessor in ('fget', 'fset', 'fdel'):
                add(value, accessor, getattr(value, accessor))
    def record_class(value):
        # Generated methods may dispatch through super() or a captured base_type.
        # Preserve every actual MRO class/method, not just that class object's ID.
        for parent in value.__mro__:
            if parent is object or parent in seen_classes: continue
            seen_classes.add(parent); mros.append((parent, parent.__mro__))
            namespaces.append((parent, keys(parent)))
            for field, child in vars(parent).items():
                if field not in ('__dict__', '__weakref__'): add(parent, field, child)
    namespaces.append((module, keys(module)))
    for name, value in vars(module).items():
        if name.startswith('__') or name == '_NEXT_CAPSULE': continue
        add(module, name, value)
        if isinstance(value, type) and value.__module__ == module.__name__:
            record_class(value)
    for value in class_roots:
        need(isinstance(value, type), 'actual generated endpoint class')
        record_class(value)
    return namespaces, state, mros

def unchanged_executable(state):
    namespaces, records, mros = state
    for owner, original_mro in mros:
        need(owner.__mro__ == original_mro and all(a is b for a, b in zip(owner.__mro__, original_mro)),
             'compiled generated endpoint inheritance changed')
    for owner, names in namespaces:
        need(tuple(k for k in vars(owner) if not k.startswith('__') and k != '_NEXT_CAPSULE') == names,
             'compiled namespace gained or lost bindings')
    for owner, name, original, code, defaults, closure, data in records:
        actual = getattr(owner, name) if isinstance(owner, property) else vars(owner).get(name)
        if isinstance(actual, (staticmethod, classmethod)): actual = actual.__func__
        need(actual is original, 'compiled namespace/function identity changed')
        if code is not None:
            need(actual.__code__ is code and
                 (value_state(actual.__defaults__), value_state(actual.__kwdefaults__)) == defaults,
                 'compiled executable/defaults changed; co_filename is insufficient')
            current = actual.__closure__ or ()
            need(len(current) == len(closure) and all(cell.cell_contents is old and value_state(cell.cell_contents) == text
                 for cell, (old, text) in zip(current, closure)), 'compiled source closure changed')
        if data is not None: need(value_state(actual) == data, 'compiled source constant changed')

def json_blockable(value):
    # A C-json block is a bounded existing subtree: at most512 scalar/container
    # visits,32768 total string characters and4096 bits per integer. This test
    # retains references only; oversized containers are streamed recursively.
    stack=[value];visits=0;characters=0
    while stack:
        child=stack.pop();visits+=1
        if visits>512:return False
        if type(child) is str:
            characters+=len(child)
            if characters>32768:return False
        elif type(child) is int:
            if child.bit_length()>4096:return False
        elif child is None or type(child) in (bool,float):pass
        elif type(child) is dict:
            if len(child)>512:return False
            for name,item in child.items():
                if type(name) is not str:return False
                stack.append(name);stack.append(item)
                if len(stack)>512:return False
        elif type(child) in (list,tuple):
            if len(child)>512:return False
            stack.extend(child)
            if len(stack)>512:return False
        else:return False
    return True

def json_chunks(value):
    # Full canonical JSON: C blocks only for bounded existing subtrees. No full
    # model/state copy, JSON string or UTF-8 buffer is constructed here.
    if json_blockable(value):
        yield canonical(value)
    elif type(value) is dict:
        yield '{'
        for index,name in enumerate(sorted(value)):
            need(type(name) is str,'literal JSON object keys')
            if index:yield ','
            yield canonical(name)+':'
            yield from json_chunks(value[name])
        yield '}'
    elif type(value) in (list,tuple):
        yield '['
        for start in range(0,len(value),32):
            block=value[start:start+32]
            if start:yield ','
            if json_blockable(block):yield canonical(block)[1:-1]
            else:
                for offset,item in enumerate(block):
                    if offset:yield ','
                    yield from json_chunks(item)
        yield ']'
    else:yield canonical(value)

def syntax_array(value):
    # Storage recognizer only: no signature, capture, rule or grammar decision.
    # Unknown/malformed shapes are retained unchanged for the independent audit.
    if type(value) is not list or not value or type(value[0]) is not str:
        return False
    lengths={'var':2,'fun':3,'bot':1,'eq':3,'pred':3,'all':3,'not':2,'imp':3,'and':3,'or':3}
    return value[0] in lengths and len(value)==lengths[value[0]]

def syntax_atom_key(value):
    # Python False==0 and 0.0==-0.0 must never merge different JSON values/types.
    if value is None:return ('null',)
    if type(value) is bool:return ('bool',value)
    if type(value) is int:return ('int',value)
    if type(value) is float:
        if not math.isfinite(value):return None
        return ('float',value.hex())
    if type(value) is str:return ('str',value)
    return None

def share_syntax_value(value, memo, identities):
    """Value-preserving sharing inside a recognized literal syntax tree only.

    Keys retain every typed scalar and every ordered list child. Returned wire
    nodes remain actual lists, never tuples/codes/alpha-equivalence classes.
    Dictionaries or unexpected objects are not interned. Record/occurrence,
    port arrays, recipe and model identities remain separate containers.
    """
    def tree(node):
        if type(node) is not list:
            key=syntax_atom_key(node)
            return node,key
        old=identities.get(id(node))
        if old is not None and old[0] is node:
            return node,old[1]
        children=[];keys=[]
        for child in node:
            shared,key=tree(child)
            if key is None:
                return node,None
            children.append(shared);keys.append(key)
        key=('list',tuple(keys))
        if key in memo:
            return memo[key],key
        node[:]=children
        memo[key]=node;identities[id(node)]=(node,key)
        return node,key
    if type(value) is not list:
        # Dictionary children already passed through object_pairs_hook. No
        # dictionary record is coalesced, including duplicate Gamma occurrences.
        return value
    if syntax_array(value):
        shared,_=tree(value)
        return shared
    # Root arrays of syntax (registry/Gamma/ports) preserve their original length
    # and order. Pure scalar metadata/factor arrays have no syntax to share.
    for index,child in enumerate(value):
        if type(child) is list:
            value[index]=share_syntax_value(child,memo,identities)
    return value

def parse_shared_syntax(text):
    """Exactly one complete stdlib JSON parse; duplicate-field rules unchanged."""
    need(type(text) is str,'one already authenticated lossless UTF-8 text buffer')
    memo={};identities={}
    def unique(pairs):
        result={}
        for name,value in pairs:
            need(name not in result,'duplicate JSON field')
            result[name]=share_syntax_value(value,memo,identities)
        return result
    result=json.loads(text,object_pairs_hook=unique,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError('nonfinite JSON '+token)))
    # Caches belong to this parse only. They do not become persistent authority,
    # runtime input, a second decoded model or a source-level theorem inventory.
    memo.clear();identities.clear()
    return result

def read_lossless_preparation(record, maximum=MAX_METADATA):
    """Authenticate raw bytes, decode losslessly, release bytes BEFORE JSON.

    The decoded text is the exact authenticated buffer's UTF-8 content. No
    pathname reread becomes parse authority. Syntax sharing changes allocation
    only, and full canonical value seals still bracket the actual audit.
    """
    verify(record)
    with Path(record['path']).open('rb') as stream:
        raw=stream.read(maximum+1)
        need(len(raw)<=maximum and stream.read(1)==b'','whole bounded raw input, no prefix')
    need(len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256'],
         'one exact authenticated raw preparation buffer')
    # Same byte-to-text rule as stdlib json.loads(bytes), including its lossless
    # surrogate handling; the fixed producer witness is UTF-8.
    text=raw.decode(json.detect_encoding(raw),'surrogatepass')
    del raw
    value=parse_shared_syntax(text)
    del text
    verify(record)
    return value

def function_state(fn):
    need(inspect.isfunction(fn), 'actual Python function endpoint')
    return (fn, fn.__code__, id(fn.__defaults__), tuple(id(v) for v in fn.__defaults__ or ()),
        id(fn.__kwdefaults__), tuple((k,id(v)) for k,v in sorted((fn.__kwdefaults__ or {}).items())),
        tuple((id(cell),id(cell.cell_contents)) for cell in fn.__closure__ or ()))

def value_digest(value, tick):
    # Whole canonical data seal, no second preparation parse or full JSON copy.
    h=hashlib.sha256(); since_boundary=0
    tick()
    for chunk in json_chunks(value):
        raw=chunk.encode('utf8')
        need(len(raw)<=4*1048576, 'bounded canonical data-seal chunk')
        h.update(raw); since_boundary+=len(raw)
        if since_boundary>=65536:
            tick(); since_boundary=0
    tick(); return h.hexdigest()

def authenticate_named(value, closure):
    # Walk raw pins in an already named parsed input only. Never decode ancestors.
    if type(value) is dict:
        if set(value)=={'path','sha256','bytes'}:
            record=normalize(value); verify(record)
            need(closure.get(record['path'])==record, 'every named-reader raw pin explicitly closed')
            return
        for child in value.values():
            authenticate_named(child,closure)
    elif type(value) is list:
        for child in value:
            authenticate_named(child,closure)

def validate_producer(documents, closure):
    receipt=documents['producer_receipt']; evidence=documents['producer_evidence']
    decision=documents['producer_ROOT_final_decision']; seal=documents['producer_ROOT_reconciled_disposition']
    producer_plan=documents['producer_worker_plan']
    need(receipt['schema']=='cold-Q-preparation-controls-receipt-v1' and receipt['stage']=='preparation'
         and receipt['stage_completed'] is True and receipt['all_direct_children_terminal_and_reaped'] is True,
         'whole original producer receipt complete')
    need(receipt['prepared']==FROZEN_INPUTS['producer_preparation'] and receipt['evidence']==FROZEN_INPUTS['producer_evidence']
         and receipt['worker_plan']==FROZEN_INPUTS['producer_worker_plan'], 'actual original result/evidence/source plan coupling')
    need(decision['schema']=='ROOT-fresh-catalog-stage-final-decision-v1'
         and decision['status']=='accepted_complete_owned_stage' and decision['ROOT_final_accepted'] is True
         and len(decision['predicates'])==14 and all(v is True for v in decision['predicates'].values())
         and normalize(decision['worker'])==FROZEN_INPUTS['producer_receipt'], 'genuine original ROOT14 resource closure')
    need(seal['schema']=='ROOT-Q-actual-complete-producer-controls-reconciled-disposition-v2'
         and seal['author_identity']=='/root' and seal['ROOT_complete_scoped_controls_accepted'] is True
         and normalize(seal['resource_qualification'])==FROZEN_INPUTS['producer_ROOT_final_decision']
         and normalize(seal['preparation'])==FROZEN_INPUTS['producer_preparation']
         and normalize(seal['worker_receipt'])==FROZEN_INPUTS['producer_receipt'], 'literal original reconciled ROOT custody')
    need(seal['catalogue_mathematically_admitted'] is False and seal['target_proofs_accepted'] is False
         and seal['target_searches']==0 and seal['native_accepted'] is False and seal['RL_training_runs']==0,
         'producer controls are not mathematical proof/catalogue authority')
    need(producer_plan['sources']==PRODUCER_SOURCES and producer_plan['limits']==LIMITS
         and evidence['sources']==PRODUCER_SOURCES and evidence['worker_plan']==FROZEN_INPUTS['producer_worker_plan']
         and evidence['prepared']==FROZEN_INPUTS['producer_preparation'], 'same exact full producer seven-role ledger')
    for name in ('independent_mathematical_catalogue_admission','universal_theorem_discovered','scientific_search_activation'):
        need(receipt[name] is False and evidence[name] is False,'original stronger acceptance remains false')
    owner_pin=normalize(receipt['owner_plan'])
    need(owner_pin==normalize(decision['plan']) and closure.get(owner_pin['path'])==owner_pin,'named actual producer owner plan')
    owner=read(owner_pin); authenticate_named(owner,closure)
    need(owner['schema']=='ROOT-guard-native-owned-plan-v1' and owner['stage']=='preparation'
         and owner['limits']==LIMITS,'original resource plan, no change of limits')
    need(normalize(owner['runtime_binary'])==producer_plan['runtime']['binary'], 'same original producer runtime')
    for raw in producer_plan['closure']+owner['closure']:
        record=normalize(raw); verify(record)
        need(closure.get(record['path'])==record,'every explicit original worker/owner raw closure retained')
    return owner_pin


def checked_buffer(record, maximum=MAX_METADATA):
    verify(record)
    path=Path(record['path']); before=path.stat()
    with path.open('rb') as stream:
        raw=stream.read(maximum+1)
        need(len(raw)<=maximum and stream.read(1)==b'', 'whole bounded cached raw buffer EOF')
    after=path.stat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==
         (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'one immutable read')
    need(len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256'],
         'only authenticated same buffer becomes parse/compile authority')
    return raw


def load_cached(record, name, raw, *, role, registration):
    # Owned once-only transition: no cache exemption while a new authenticated
    # module becomes visible. Register and seal the exact object before the
    # caller's mandatory post-load guard can inspect sys.modules.
    need(type(registration) is dict and registration['sealed'] is False
         and role in EXECUTED_ROLES and role!='worker'
         and registration['sources'][role]==record
         and registration['source_buffers'][role] is raw,
         'exact owned role and cached buffer, no arbitrary registration')
    need(role not in registration['modules'] and role not in registration['module_anchors'],
         'one original source module transition, no resealing changed authority')
    need(type(raw) is bytes and len(raw)==record['bytes']
         and hashlib.sha256(raw).hexdigest()==record['sha256'], 'exact cached execution buffer')
    need(name not in sys.modules, 'exclusive module identity')
    spec=importlib.util.spec_from_file_location(name,record['path'])
    need(spec is not None, 'raw-source metadata spec')
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module
    exec(compile(raw,record['path'],'exec'),module.__dict__)
    need(module.__file__==record['path'] and module.__name__==name
         and type(module) is types.ModuleType and sys.modules[name] is module,
         'exact cached raw module object/effective origin')
    # Snapshot the original namespaces/classMRO/properties/code/defaults/cells
    # once, before any graph/runtime/observer/control constructor is called.
    original_snapshot=executable_state(module)
    original_functions=exact_function_anchors(original_snapshot)
    registration['modules'][role]=module
    registration['module_anchors'][role]=module
    registration['snapshots'].append(original_snapshot)
    registration['functions'].append(original_functions)
    verify(record)
    return module


def exact_function_anchors(state):
    result=[]
    for _,records,_ in (state,):
        for owner,name,fn,code,_,_,_ in records:
            if code is None:
                continue
            descriptor=getattr(owner,name) if isinstance(owner,property) else vars(owner).get(name)
            effective=getattr(owner,name)
            binding=('class',effective.__self__,effective.__func__) if isinstance(descriptor,classmethod) else ('direct',effective)
            result.append((owner,name,descriptor,fn,function_state(fn),binding))
    return tuple(result)


def check_exact_functions(anchors):
    for owner,name,descriptor,fn,anchor,binding in anchors:
        current=getattr(owner,name) if isinstance(owner,property) else vars(owner).get(name)
        need(current is descriptor and function_state(fn)==anchor, 'function/default-entry/closure/accessor changed')
        effective=getattr(owner,name)
        if binding[0]=='class':
            need(getattr(effective,'__self__',None) is binding[1]
                 and getattr(effective,'__func__',None) is binding[2], 'effective classmethod changed')
        else:
            need(effective is binding[1], 'effective function/accessor changed')


def endpoint_anchor(obj):
    # Actual generated/dataclass endpoint roots are captured after construction,
    # before first use. No subsequent changed executable state is re-anchored.
    klass=type(obj)
    methods=[]; names=set()
    for parent in klass.__mro__:
        if parent is object:
            continue
        for name,descriptor in vars(parent).items():
            if name in names:
                continue
            names.add(name)
            if isinstance(descriptor,property):
                methods.append((name,'property',descriptor,None,None))
            else:
                fn=descriptor.__func__ if isinstance(descriptor,(staticmethod,classmethod)) else descriptor
                if inspect.isfunction(fn):
                    effective=getattr(obj,name)
                    if isinstance(effective,types.MethodType):
                        methods.append((name,'bound',descriptor,effective.__self__,effective.__func__))
                    else:
                        methods.append((name,'direct',descriptor,None,effective))
    return (obj,klass,klass.__mro__,tuple(methods))


def check_endpoint(obj, anchor):
    original,klass,mro,methods=anchor
    need(obj is original and type(obj) is klass and klass.__mro__==mro
         and all(a is b for a,b in zip(klass.__mro__,mro)), 'constructed endpoint/type/MRO identity changed')
    namespace=getattr(obj,'__dict__',{})
    for name,kind,descriptor,receiver,function in methods:
        need(name not in namespace, 'instance executable/property shadow forbidden')
        found=next((vars(parent)[name] for parent in mro if name in vars(parent)),None)
        need(found is descriptor,'constructed class descriptor changed')
        if kind=='property':
            continue
        effective=getattr(obj,name)
        if kind=='bound':
            need(getattr(effective,'__self__',None) is receiver and getattr(effective,'__func__',None) is function,
                 'effective bound method endpoint changed')
        else:
            need(effective is function,'effective static/direct endpoint changed')


def construct_owned(name, *, registration, guarded_call, arguments=(), keywords):
    # One owned transition encloses the unchanged complete initializer. No
    # object is visible to source_guard until all of its original endpoint and
    # field records (including the observer's own point Boundary) are ready.
    original_state=function_state; state_code=original_state.__code__
    original_reject=need; reject_code=original_reject.__code__
    original_call=guarded_call; call_anchor=original_state(original_call)
    original_helpers=tuple((field,globals()[field],globals()[field].__code__,
                            original_state(globals()[field])) for field in
        ('need','endpoint_anchor','check_endpoint','unchanged_executable','check_exact_functions'))
    tables=('objects','object_anchors','fixed_fields','mutable_fields')
    original_tables=tuple((field,registration[field]) for field in tables)
    need(type(registration) is dict and registration['sealed'] is False
         and type(arguments) is tuple and type(keywords) is dict,
         'exact once-only owned construction before setup is sealed')
    need(all(type(table) is dict for _,table in original_tables)
         and all(set(table)==set(registration['objects']) for _,table in original_tables),
         'every already published object has its complete guard records')
    specifications={
        'graph':('point_graph','PointGraph',
            ('height','fixture','formulas','registry_sha','context','context_id','authority','authority_epoch',
             'source_bindings','recipes','recipe_index','roots','initial_marks','model_epoch','initial_selected'),
            ('totals','marks','mark_refs','selected','order','excluded','trail','domains','metrics')),
        'runtime':('driver','Runtime',
            ('began','deadline','guard','guard_anchor','clock','usage','state_function','state_code','reject','reject_code'),()),
        'observer':('driver','FirstSelectedProofObserver',
            ('graph','catalogue','declaration','checker','runtime','binding','primitives','target_code','point_boundary'),('counts',)),
        'events':('driver','OwnedEvents',('directory','runtime'),('pins','partial','serialization'))}
    need(type(name) is str and name in specifications,'only the four declared original constructor roots')
    role,class_name,fixed_names,mutable_names=specifications[name]
    module=registration['modules'][role]
    need(module is registration['module_anchors'][role],'original raw-bound constructor module')
    klass=vars(module).get(class_name)
    need(type(klass) is type and any(owner is klass for snapshot in registration['snapshots']
         for owner,_ in snapshot[0]),'exact class was source/MRO/property sealed before construction')
    names=(name,'point_boundary') if name=='observer' else (name,)
    need(all(key not in table for key in names for _,table in original_tables),
         'original object endpoints registered once, never resealed')
    initializer=klass.__init__; initializer_anchor=original_state(initializer)
    obj=object.__new__(klass)
    if function_state is not original_state or original_state.__code__ is not state_code:
        raise ValueError('original state validator changed before constructor delegation')
    if need is not original_reject or original_reject.__code__ is not reject_code:
        raise ValueError('original rejector changed before constructor delegation')
    if original_call.__code__ is not call_anchor[1] or original_state(original_call)!=call_anchor:
        raise ValueError('original guarded constructor caller changed')
    returned=original_call(initializer,obj,*arguments,**keywords)
    if function_state is not original_state or original_state.__code__ is not state_code:
        raise ValueError('original state validator changed during constructor')
    if need is not original_reject or original_reject.__code__ is not reject_code:
        raise ValueError('original rejector changed during constructor')
    if original_call.__code__ is not call_anchor[1] or original_state(original_call)!=call_anchor:
        raise ValueError('guarded constructor caller authority changed')
    if any(globals().get(field) is not fn or fn.__code__ is not code for field,fn,code,_ in original_helpers):
        raise ValueError('owned constructor endpoint validators changed')
    if any(original_state(fn)!=anchor for _,fn,_,anchor in original_helpers):
        raise ValueError('owned constructor validator defaults/cells changed')
    need(returned is None and type(obj) is klass and klass.__init__ is initializer
         and original_state(initializer)==initializer_anchor,'complete unchanged original initializer returned')
    need(all(registration[field] is table for field,table in original_tables),
         'original owned object registries retain identity during construction')
    # Compare the original pre-constructor module/class/accessor/code seals;
    # endpoint_anchor captures effective instance bindings, not new authority.
    for snapshot in registration['snapshots']:
        unchanged_executable(snapshot)
    for anchors in registration['functions']:
        check_exact_functions(anchors)
    pending=[(name,obj,klass,fixed_names,mutable_names)]
    if name=='observer':
        child=obj.point_boundary; boundary_class=registration['modules']['independent_checker'].Boundary
        need(type(child) is boundary_class and any(owner is boundary_class
             for snapshot in registration['snapshots'] for owner,_ in snapshot[0]),
             'only the actual internally initialized independent point Boundary')
        pending.append(('point_boundary',child,boundary_class,
            ('deadline','maximum_visits','guard','_callback_state','_state_code','_need','_need_code','_clock','anchor'),()))
    prepared=[]
    for key,endpoint,expected_class,fixed,mutable in pending:
        need(type(endpoint) is expected_class,'exact initialized endpoint type')
        if key=='observer':
            need(type(endpoint.counts) is dict,'original observer mutable counter kind remains dict')
        if key=='events':
            need(all(type(getattr(endpoint,field)) is list for field in mutable),
                 'original event ledger container kinds remain list')
        anchor=endpoint_anchor(endpoint); check_endpoint(endpoint,anchor)
        fixed_record=tuple((field,getattr(endpoint,field)) for field in fixed)
        mutable_record=tuple((field,getattr(endpoint,field),type(getattr(endpoint,field))) for field in mutable)
        prepared.append((key,endpoint,anchor,fixed_record,mutable_record))
    # No callback or constructor occurs in publication. Prepare every guard
    # table first and publish objects LAST; the enclosing guarded call then
    # performs its mandatory complete source/endpoint/inner-clock postcheck.
    for key,endpoint,anchor,fixed_record,mutable_record in prepared:
        registration['object_anchors'][key]=anchor
        registration['fixed_fields'][key]=fixed_record
        registration['mutable_fields'][key]=mutable_record
    for key,endpoint,_,_,_ in prepared:
        registration['objects'][key]=endpoint
    return obj


def source_cache_guard(sources, modules, anchors):
    expected={sources[role]['path']:sources[role] for role in EXECUTED_ROLES}
    seen=[]
    for name,module in list(sys.modules.items()):
        file=getattr(module,'__file__',None)
        if type(file) is not str:
            continue
        lexical=Path(file); lexical=lexical if lexical.is_absolute() else ROOT/lexical
        if not str(lexical).startswith(str(ROOT)+os.sep):
            continue
        path=str(lexical.resolve())
        need(path in expected and not path.endswith(('.pyc','.pyo')), 'only exact five control execution roles; raw subject/provenance not allowlist')
        need(name==__name__ or any(module is item for item in modules.values()),'exact cached module identity')
        verify(expected[path]); seen.append(expected[path])
    need(all(modules[role] is anchors[role] and sys.modules.get(modules[role].__name__) is modules[role]
             for role in modules), 'raw compiled module origins retained')
    return sorted({record['path']:record for record in seen}.values(),key=lambda record:record['path'])


def preflight(plan_path, owner_path):
    plan_pin,owner_pin=pin(plan_path),pin(owner_path)
    plan=parse(checked_buffer(plan_pin,2*1048576)); owner=parse(checked_buffer(owner_pin,2*1048576))
    fields={'schema','stage','activation','outdir','sources','inputs','source_review','limits',
            'allowed_runtime','source_cache_gate','raw_closure'}
    need(type(plan) is dict and set(plan)==fields and plan['schema']==SCHEMA and plan['stage']=='replay'
         and plan['limits']==LIMITS,'strict literal11-field separate controls-only leaf')
    need(set(plan['sources'])==SOURCE_ROLES and plan['sources']['worker']==pin(Path(__file__).resolve())
         and plan['sources']['driver']==DRIVER and plan['sources']['point_graph']==GRAPH
         and plan['sources']['independent_checker']==AUDITOR and plan['sources']['master']==MASTER
         and plan['sources']['calibration']==CALIBRATION
         and plan['sources']['scientific_worker_subject']==SCIENTIFIC_SUBJECT,
         'exact five-execution/scientific-subject+master raw map')
    need(type(plan['inputs']) is dict and plan['inputs']==FROZEN_INPUTS,
         'original full inputs plus literal calibration only; no future controls admission or scientific leaf')
    gate=dict(executed_roles=list(EXECUTED_ROLES),raw_only_producer_provenance=PRODUCER_SOURCES,
        master_raw_only=True,scientific_worker_subject_raw_only=True,allow_project_bytecode=False,compile_kernel_or_catalogue=False,
        execute_producer_preparation_or_controls=False)
    need(plan['source_cache_gate']==gate,'explicit source-only provenance separate from execution allowlist')
    a=plan['activation']
    need(type(a) is dict and set(a)=={'schema','author_identity','ROOT_owned_once_only','scope','target_searches',
        'native_queries','RL_updates','proof_routes_supplied','library_used','rank_used','finite_catalogue_ROOT',
        'word_controls_ROOT','scientific_worker_subject','sources'},'exact controls-only purpose fields')
    expected_activation=dict(schema='ROOT-Q-first-proof-neutral-controls-activation-v1',author_identity='/root',
        ROOT_owned_once_only=True,scope=SCOPE,target_searches=0,native_queries=0,RL_updates=0,
        proof_routes_supplied=0,library_used=False,rank_used=False,
        finite_catalogue_ROOT=FROZEN_INPUTS['finite_ROOT_admission'],
        word_controls_ROOT=FROZEN_INPUTS['actual_word_controls_ROOT'],
        scientific_worker_subject=SCIENTIFIC_SUBJECT,sources=plan['sources'])
    need(canonical(a)==canonical(expected_activation),
        'explicit non-search controls-only once-only purpose; no future scientific activation')
    need(plan_path.parent==owner_path.parent,'one flat new namespace')
    output=Path(plan['outdir'])
    need(output.is_absolute() and output==output.resolve() and output.parent==plan_path.parent
         and not output.exists(),'fresh absent output, no retry/warm state')
    closure={}
    for record in plan['raw_closure']:
        verify(record); need(record['path'] not in closure,'unique full canonical raw closure')
        closure[record['path']]=record
    need(list(closure)==sorted(closure),'sorted closed sources/inputs/reviews/runtime')
    reviews=plan['source_review']
    need(type(reviews) is dict and set(reviews)=={'ROOT','worker_independent','driver_independent','checker_independent','calibration_independent'},
         'actual typed current role-specific reviews; no fabricated slots')
    need(reviews['driver_independent']==DRIVER_REVIEW,'exact newly frozen current V2 peer pass, V1 negative never admissible')
    for record in [*plan['sources'].values(),*plan['inputs'].values(),*reviews.values(),*PRODUCER_SOURCES.values()]:
        verify(record); need(closure.get(record['path'])==record,'every direct source/input/review/raw producer pin closed')
    runtime=plan['allowed_runtime']
    need(type(runtime) is dict and set(runtime)=={'binary','resource_extension','python_version','platform'}
         and runtime['python_version']==[3,9,6] and runtime['platform']=='darwin'
         and list(sys.version_info[:3])==[3,9,6] and sys.platform=='darwin','exact original runtime semantics')
    for role in ('binary','resource_extension'):
        verify(runtime[role]); need(closure.get(runtime[role]['path'])==runtime[role],'canonical runtime closed')
    need(str(Path(sys.executable).resolve())==runtime['binary']['path']
         and str(Path(resource.__file__).resolve())==runtime['resource_extension']['path'],'actual binary/resource extension')
    argv=[runtime['binary']['path'],'-B',plan['sources']['worker']['path'],COMMAND,str(plan_path),str(owner_path)]
    need(type(owner) is dict and set(owner)=={'schema','stage','runtime_binary','worker','argv','worker_receipt',
        'limits','closure','ROOT_source_review','scope'} and owner['schema']=='ROOT-guard-native-owned-plan-v1'
        and owner['stage']=='replay' and owner['limits']==LIMITS and owner['scope']==SCOPE and owner['argv']==argv,
         'strict unchanged generic10-field owner/literal six argv')
    need(normalize(owner['runtime_binary'])==runtime['binary'] and normalize(owner['ROOT_source_review'])==reviews['ROOT']
         and reviews['ROOT']['path']==str(plan_path.parent/'ROOT-source-review-v1.json'),'local genuine ROOT review/runtime')
    need((ROOT/owner['worker']).resolve()==Path(plan['sources']['worker']['path'])
         and (ROOT/owner['worker_receipt']).resolve()==output/RECEIPT,'literal worker/final receipt')
    owner_closure={}
    for raw in owner['closure']:
        record=normalize(raw); verify(record)
        need(record['path'] not in owner_closure,'unique owner raw closure')
        owner_closure[record['path']]=record
    need(all(owner_closure.get(path)==record for path,record in closure.items())
         and owner_closure.get(plan_pin['path'])==plan_pin,'whole worker+leaf closure in owner')
    for role,record in reviews.items():
        review=read(record); authenticate_named(review,closure)
        need(review.get('source_only') is True and review.get('source_review_passed') is True
             and review.get('all_checks_passed') is True and review.get('scientific_calls')==0,
             'genuine successful current Source review, never runtime authority')
        if role in ('ROOT','worker_independent'):
            need(review.get('schema')=='Q-first-proof-neutral-cold-controls-worker-Source-review-v1'
                 and review.get('scope')=='Q-first-proof-neutral-cold-controls-worker-Source'
                 and review.get('author_identity')==AUTHOR and review.get('reviewer_identity')!=AUTHOR
                 and review.get('sources')==plan['sources'],'typed exact current cold worker review')
        elif role=='driver_independent':
            need(review.get('schema')=='Q-first-selected-proof-observer-driver-Source-review-v1'
                 and review.get('scope')=='Q-first-selected-proof-observer-driver-Source'
                 and review.get('author_identity')=='/root/arithmetic_induction'
                 and review.get('reviewer_identity')!='/root/arithmetic_induction'
                 and review.get('source')==DRIVER and review.get('source_contract')==FROZEN_INPUTS['driver_contract'],
                 'unchanged current driver genuine distinct-author pass')
        elif role=='calibration_independent':
            need(review.get('schema')=='Q-first-proof-neutral-conformance-Source-review-v1'
                 and review.get('scope')=='Q-first-proof-neutral-conformance-Source'
                 and review.get('author_identity')=='/root/arithmetic_induction'
                 and review.get('reviewer_identity')!='/root/arithmetic_induction'
                 and review.get('source')==CALIBRATION and review.get('whole_fixtures')==FROZEN_INPUTS['calibration_fixtures']
                 and review.get('source_contract')==FROZEN_INPUTS['calibration_contract'],
                 'genuine whole callable+literal-fixture Source review')
        else:
            need(review.get('schema')=='independent-Q-mathematical-auditor-Source-review-v1'
                 and review.get('scope')=='complete-finite-Q-catalogue-primitive-domain-and-word-checker-Source'
                 and review.get('author_identity')==AUTHOR and review.get('reviewer_identity')!=AUTHOR
                 and review.get('sources')=={'independent_auditor':AUDITOR,'master':MASTER}
                 and review.get('source_contract')==FROZEN_INPUTS['checker_contract'],'exact old independent checker Source custody')
    return plan,owner,output,plan_pin,owner_pin,closure,owner_closure


def validate_admitted(documents, closure):
    # Named metadata only, every pinned descendant raw-verified but not decoded.
    finite=documents['finite_ROOT_admission']; certificate=documents['finite_audit_certificate']
    words=documents['actual_word_controls_ROOT']
    need(finite['schema']=='ROOT-actual-independent-Q-shared-wire-audit-reconciled-disposition-v2'
         and finite['author_identity']=='/root' and finite['ROOT_complete_independent_audit_accepted'] is True
         and finite['mathematical_catalogue_admitted'] is True
         and normalize(finite['audit_certificate'])==FROZEN_INPUTS['finite_audit_certificate'],
         'actual finite mathematical ROOT admission, not producer-only controls')
    need(certificate['schema']=='independent-complete-Q-catalogue-point-audit-v1'
         and certificate['completed'] is True and certificate['all_catalogue_primitive_and_initial_domains_accepted'] is True
         and certificate['source_bindings']==PRODUCER_SOURCES,'whole independent finite certificate/original7')
    need(words['author_identity']=='/root' and words['ROOT_controls_qualified'] is True
         and words['resource14_accepted'] is True and words['Q_target_searches']==0
         and words['discovered_target_proofs']==0 and words['rank_computations']==0
         and words['native_queries']==0 and words['RL_runs']==0,
         'actual unrelated68 mechanics gate is not Q target authority')
    for field in ('target_proofs_accepted','native_accepted','full24_accepted','full_PA_accepted','induction_accepted'):
        need(finite[field] is False,'prior finite admission preserves proof scopes false')
    for name in ('model_epoch','primitive_authority_epoch','formula_registry_sha256'):
        need(certificate[name]==CURRENT[name],'exact original admitted identity epoch')
    # Actual own resource ROOT chain and every explicit old owner closure.
    resource_pin=normalize(finite['resource_qualification'])
    need(closure.get(resource_pin['path'])==resource_pin,'named finite resource chain')
    decision=read(resource_pin); authenticate_named(decision,closure)
    need(decision['ROOT_final_accepted'] is True and len(decision['predicates'])==14
         and all(value is True for value in decision['predicates'].values()),'actual complete finite ROOT14 gate')
    for pin_name in ('worker_plan','owner_plan'):
        record=normalize(finite[pin_name]); need(closure.get(record['path'])==record,'named finite worker/owner plan')
        data=read(record); authenticate_named(data,closure)
        records=data.get('raw_closure',data.get('closure',[]))
        for raw in records:
            value=normalize(raw); need(closure.get(value['path'])==value,'full prior explicit closure retained'); verify(value)
    # The word root is a named actual mechanics gate; preserve the entire
    # explicit worker/owner raw closure without parsing its authored fixtures
    # or invoking its suite. It never supplies target commands to this worker.
    word_resource=normalize(words['resource_qualification'])
    need(closure.get(word_resource['path'])==word_resource,'named actual word resource decision closed')
    word_decision=read(word_resource); authenticate_named(word_decision,closure)
    need(word_decision['ROOT_final_accepted'] is True and len(word_decision['predicates'])==14
         and all(value is True for value in word_decision['predicates'].values()),'actual unrelated mechanics ROOT14')
    for pin_name in ('worker_plan','owner_plan'):
        record=normalize(words[pin_name]); need(closure.get(record['path'])==record,'named word worker/owner plan')
        data=read(record); authenticate_named(data,closure)
        for raw in data.get('raw_closure',data.get('closure',[])):
            value=normalize(raw); verify(value)
            need(closure.get(value['path'])==value,'whole actual word explicit raw closure retained')
    return certificate


def make_recipe_allocation_guard(*, graph_module, driver_module, graph, runtime,
                                source_records, cached_source_buffers,
                                module_anchors, full_guard, phase_evidence):
    # The existing guarded caller authenticates/anchors this factory before
    # entry and after return. No module or Source file is loaded here.
    original_state = function_state
    state_code = original_state.__code__
    original_need = need
    need_code = original_need.__code__
    original_isfunction = inspect.isfunction
    isfunction_code = original_isfunction.__code__
    isfunction_anchor = original_state(original_isfunction)
    original_function_type = types.FunctionType
    # Original native lookup primitives are captured under the cold caller's
    # complete preguard; their closure identities are caller-sealed before use.
    # Entry custody must not resolve a newly shadowed globals/type/vars/tuple.
    original_globals, original_vars = globals, vars
    original_type, original_tuple = type, tuple
    original_dict, original_dict_get = dict, dict.get
    original_code_type = types.CodeType
    original_ValueError = ValueError
    original_module_type = types.ModuleType
    original_clock = time.perf_counter
    original_usage = resource.getrusage
    original_self = resource.RUSAGE_SELF
    original_getframe = sys._getframe
    original_modules = sys.modules
    module_bindings = tuple((name, globals()[name]) for name in
                            ('json', 'sys', 'time', 'resource', 'types', 'inspect'))
    helpers = tuple((name, globals()[name], globals()[name].__code__,
                     original_state(globals()[name])) for name in
        ('need', 'function_state', 'canonical', 'value_state', 'executable_state', 'unchanged_executable',
         'exact_function_anchors', 'check_exact_functions', 'endpoint_anchor', 'check_endpoint'))
    original_need(type(full_guard) is original_function_type
                  and full_guard is runtime.guard and full_guard.__globals__ is globals()
                  and full_guard.__module__ == __name__
                  and full_guard.__code__.co_filename == make_recipe_allocation_guard.__code__.co_filename,
                  'allocation endpoint slice belongs to the original cold caller, not a supplied callback')
    full_anchor = original_state(full_guard)
    # Mutable counters are diagnostic output only, not guard or proof authority.
    original_need(type(phase_evidence) is dict and phase_evidence == {
        'schema': 'Q-private-allocation-phase-evidence-v1',
        'factory_started': False, 'factory_returned': False,
        'factory_capture_seconds': None, 'boundary_entries': 0,
        'boundary_returns': 0, 'last_started_recipe_index': None,
        'last_returned_boundary_recipe_index': None,
        'completed_recipe_comparisons_observed': 0,
        'completed_boundary_inclusive_seconds': 0.0, 'constructor_returned': False,
        'constructor_recipe_interfaces': None}, 'fresh diagnostic counter wire only')
    phase_started = original_clock()
    phase_evidence['factory_started'] = True
    original_need(graph_module is module_anchors['point_graph']
                  and driver_module is module_anchors['driver']
                  and type(graph) is graph_module.PointGraph and type(runtime) is driver_module.Runtime,
                  'exact originally loaded module and initialized object endpoints')
    original_need(set(module_anchors) == set(EXECUTED_ROLES) - {'worker'},
                  'exact original executed role ledger, no additional allocation executable')
    buffers = []
    for role, module in module_anchors.items():
        record = source_records[role]
        raw = cached_source_buffers[role]
        original_need(type(raw) is bytes and len(raw) == record['bytes']
                      and hashlib.sha256(raw).hexdigest() == record['sha256']
                      and module.__file__ == record['path'] and original_modules.get(module.__name__) is module,
                      'once authenticated original cached bytes and module identity')
        buffers.append((role, module, module.__name__, module.__file__, raw,
                        record['path'], record['sha256'], record['bytes']))
    buffers = tuple(buffers)
    original_need(graph_module.json is json and driver_module.json is json
                  and runtime.clock is original_clock and runtime.usage is original_usage,
                  'exact delegated JSON modules and native clock/resource endpoints')
    recipes = graph.recipes
    recipe_class = graph_module.Recipe
    original_need(type(recipes) is tuple and type(recipe_class) is type,
                  'entire original immutable recipe container')
    fields = ('index', 'identifier', 'witness_text', 'premise_texts', 'output', 'inputs')
    recipe_records = []
    for index, recipe in enumerate(recipes):
        if (time.perf_counter is not original_clock or resource.getrusage is not original_usage
                or original_clock() >= runtime.deadline
                or original_clock() - runtime.began >= 55
                or original_usage(original_self).ru_maxrss >= 524288000):
            raise TimeoutError('whole allocation-slice capture exceeds original limits')
        original_need(type(recipe) is recipe_class and set(vars(recipe)) == set(fields)
                      and recipe.index == index, 'complete original Recipe records, never a shortlist')
        recipe_records.append((recipe, tuple((name, getattr(recipe, name), type(getattr(recipe, name)))
                                             for name in fields)))
    recipe_records = tuple(recipe_records)
    runtime_fields = tuple((name, getattr(runtime, name)) for name in driver_module.Runtime.__slots__)
    original_need(runtime.deadline == runtime.began + 20, 'same original absolute20, no new window')
    original_began, original_deadline = runtime.began, runtime.deadline
    observer_class = driver_module.FirstSelectedProofObserver
    initializer = observer_class.__init__
    initializer_anchor = original_state(initializer)
    driver_functions = tuple((name, getattr(driver_module, name),
                              original_state(getattr(driver_module, name)))
                             for name in ('canonical', 'need', 'function_state', 'invoke'))
    # This is an explicit reachable endpoint census for the actual strict
    # canonical dumps and str-only Recipe getters. It does not traverse every
    # unused JSON/module constant and serialize values at every local boundary.
    # The unchanged full guard still snapshots those namespaces at32/end.
    json_modules = (json, json.decoder, json.scanner, json.encoder)
    json_aliases = ((json, 'decoder', json.decoder), (json, 'scanner', json.scanner),
                   (json, 'encoder', json.encoder),
                   (json.decoder, 'scanner', json.scanner))
    json_function_names = ((json, ('dumps', 'loads', 'detect_encoding')),
        (json.decoder, ('JSONObject', 'JSONArray', 'py_scanstring', '_decode_uXXXX')),
        (json.encoder, ('py_encode_basestring', 'py_encode_basestring_ascii', '_make_iterencode')),
        (json.scanner, ('py_make_scanner',)))
    json_functions = tuple((owner, name, vars(owner)[name],
                            original_state(vars(owner)[name]))
                           for owner, names in json_function_names for name in names)
    json_binding_names = ((json, ('JSONEncoder', 'JSONDecoder', 'JSONDecodeError')),
        (json.decoder, ('JSONDecoder', 'JSONDecodeError', 'scanstring', 'c_scanstring')),
        (json.encoder, ('JSONEncoder', 'c_make_encoder', 'encode_basestring',
                        'encode_basestring_ascii', 'c_encode_basestring', 'c_encode_basestring_ascii')),
        (json.scanner, ('make_scanner', 'c_make_scanner')))
    json_bindings = tuple((owner, name, vars(owner)[name])
                         for owner, names in json_binding_names for name in names)
    original_need(json.encoder.c_make_encoder is not None
                  and json.encoder.encode_basestring is json.encoder.c_encode_basestring
                  and json.encoder.encode_basestring_ascii is json.encoder.c_encode_basestring_ascii
                  and json.decoder.scanstring is json.decoder.c_scanstring,
                  'this declared slice requires original native JSON hooks, no fallback exemption')
    # Small actually reachable constant tables are sealed by literal identity
    # and ordered entries, without delegated JSON canonicalization of them.
    json_constants = []
    for owner, names in ((json.decoder, ('_CONSTANTS', 'BACKSLASH', 'WHITESPACE_STR')),
                         (json.encoder, ('ESCAPE_DCT', 'INFINITY'))):
        for name in names:
            value = vars(owner)[name]
            entries = tuple((key, child, type(child)) for key, child in value.items()) if type(value) is dict else None
            json_constants.append((owner, name, value, type(value), entries))
    json_constants = tuple(json_constants)
    decoder = json._default_decoder
    original_need(type(decoder) is json.JSONDecoder, 'actual default decoder, never a replacement')
    decoder_anchor = endpoint_anchor(decoder)
    decoder_names = tuple(vars(decoder))
    decoder_fields = tuple((name, value, type(value)) for name, value in vars(decoder).items())
    decoder_functions = tuple((value, original_state(value)) for _, value, _ in decoder_fields
                              if original_isfunction(value))
    scanner = decoder.scan_once
    scanner_type = type(scanner)
    scanner_mro = scanner_type.__mro__
    original_need(scanner_type is json.scanner.c_make_scanner and scanner_type.__module__ == '_json',
                  'original native scanner only')
    scanner_call = next((vars(parent)['__call__'] for parent in scanner_mro
                         if '__call__' in vars(parent)), None)
    scanner_effective = scanner.__call__
    # Complete class namespace/MRO identities remain immediate. Function
    # bodies/defaults/cells are immediate for actual property/attribute dispatch
    # and JSON construction/encode/decode; unused Graph method bodies remain
    # under the original full guard at32/end, not a broad object exemption.
    class_records = []
    class_functions = []
    seen_classes = set()
    immediate_classes = (recipe_class, type(runtime), json.JSONDecoder,
                         json.JSONEncoder, json.JSONDecodeError)
    for root in (recipe_class, type(graph), type(runtime), json.JSONDecoder,
                 json.JSONEncoder, json.JSONDecodeError, scanner_type,
                 json.encoder.c_make_encoder):
        for parent in root.__mro__:
            if parent is object or parent in seen_classes:
                continue
            seen_classes.add(parent)
            records = tuple(vars(parent).items())
            class_records.append((parent, type(parent), parent.__mro__, records))
            for name, value in records:
                if isinstance(value, property):
                    for accessor in ('fget', 'fset', 'fdel'):
                        function = getattr(value, accessor)
                        if function is not None:
                            class_functions.append((value, accessor, function, original_state(function)))
                else:
                    function = value.__func__ if isinstance(value, (staticmethod, classmethod)) else value
                    if original_isfunction(function) and (parent in immediate_classes
                            or name in ('__getattribute__', '__getattr__')):
                        class_functions.append((parent, name, function, original_state(function)))
    class_records, class_functions = tuple(class_records), tuple(class_functions)
    # Name resolution is part of the actual delegated executable endpoint.
    # co_names conservatively includes attributes as well as global reads; all
    # nested code constants are included (e.g. iterencode's floatstr). Extra
    # absence checks are custody checks, never mathematical grammar filters.
    resolution_functions = [make_recipe_allocation_guard, full_guard, initializer,
                            original_isfunction]
    resolution_functions.extend(function for _, function, _, _ in helpers)
    resolution_functions.extend(function for _, function, _ in driver_functions)
    resolution_functions.extend(function for _, _, function, _ in json_functions)
    resolution_functions.extend(function for _, _, function, _ in class_functions)
    resolution_functions.extend(function for function, _ in decoder_functions)
    resolution_scopes = {}
    resolution_signatures = []
    for function in resolution_functions:
        namespace = function.__globals__
        original_need(original_type(namespace) is original_dict,
                      'actual Python callable global dictionary, no proxy')
        resolution_signatures.append((function, namespace, original_state(function)))
        scope = resolution_scopes.setdefault(id(namespace), [namespace, set()])
        original_need(scope[0] is namespace, 'unique actual global dictionary identities')
        pending = [function.__code__]
        while pending:
            code = pending.pop()
            scope[1].update(code.co_names)
            pending.extend(child for child in code.co_consts
                           if original_type(child) is original_code_type)
    resolution_records = []
    namespace_records = []
    for namespace, names in resolution_scopes.values():
        builtin_holder = namespace.get('__builtins__')
        builtin_kind = original_type(builtin_holder)
        original_need(builtin_kind in (original_dict, original_module_type),
                      'original standard builtin dictionary/module only')
        builtin_namespace = builtin_holder if builtin_kind is original_dict else original_vars(builtin_holder)
        original_need(original_type(builtin_namespace) is original_dict,
                      'actual native builtin resolution dictionary')
        namespace_records.append((namespace, original_tuple(namespace), builtin_holder,
                                  builtin_kind, builtin_namespace))
        for name in sorted(names):
            global_present = name in namespace
            global_value = original_dict_get(namespace, name)
            builtin_present = name in builtin_namespace
            builtin_value = original_dict_get(builtin_namespace, name)
            resolution_records.append((namespace, name, global_present, global_value,
                                       builtin_namespace, builtin_present, builtin_value))
    resolution_records, namespace_records = original_tuple(resolution_records), original_tuple(namespace_records)
    # Even unused added JSON globals can change future builtin fallback. Name
    # tuples are cheap identity/presence custody, not recursive value snapshots.
    relevant_namespace_records = original_tuple((module, original_vars(module),
                                                original_tuple(original_vars(module)))
        for module in json_modules + (graph_module, driver_module))
    progress = {'index': -1, 'busy': False}

    def allocation_guard(*, index, recipe):
        # These direct rejections precede all potentially mutable validators.
        # The driver independently seals this exact function/defaults/cells at
        # every caller; this function is not its own source of entry authority.
        # Direct native-only resolution gates precede ANY mutable helper,
        # builtin-name lookup or module property used by the existing body.
        if original_type(original_globals()) is not original_dict:
            raise original_ValueError('original caller global dictionary type changed')
        for namespace, keys, holder, holder_kind, builtin_namespace in namespace_records:
            if original_type(namespace) is not original_dict or original_tuple(namespace) != keys:
                raise original_ValueError('reachable callable namespace added/lost names')
            if (original_dict_get(namespace, '__builtins__') is not holder
                    or original_type(holder) is not holder_kind
                    or (holder if holder_kind is original_dict else original_vars(holder)) is not builtin_namespace):
                raise original_ValueError('actual reachable builtin mapping identity/type changed')
        for module, namespace, keys in relevant_namespace_records:
            if (original_type(module) is not original_module_type
                    or original_vars(module) is not namespace or original_tuple(namespace) != keys):
                raise original_ValueError('actual relevant module namespace added/lost names')
        for namespace, name, global_present, global_value, builtin_namespace, builtin_present, builtin_value in resolution_records:
            if ((name in namespace) is not global_present
                    or original_dict_get(namespace, name) is not global_value
                    or (name in builtin_namespace) is not builtin_present
                    or original_dict_get(builtin_namespace, name) is not builtin_value):
                raise original_ValueError('actual reachable global/builtin presence or identity changed')
        if time.perf_counter is not original_clock:
            raise ValueError('original allocation diagnostic clock changed')
        boundary_started = original_clock()
        phase_evidence['boundary_entries'] += 1
        phase_evidence['last_started_recipe_index'] = index
        if any(globals().get(name) is not module for name, module in module_bindings):
            raise ValueError('original actual allocation module binding changed')
        if function_state is not original_state or original_state.__code__ is not state_code:
            raise ValueError('original allocation function-state validator changed')
        if need is not original_need or original_need.__code__ is not need_code:
            raise ValueError('original allocation rejector changed')
        if inspect.isfunction is not original_isfunction or original_isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed')
        if types.FunctionType is not original_function_type or types.ModuleType is not original_module_type:
            raise ValueError('original Python function/module type changed')
        if any(type(module) is not original_module_type for _, module in module_bindings):
            raise ValueError('original allocation module acquired a custom attribute endpoint')
        if any(type(module) is not original_module_type for _, module, _, _, _, _, _, _ in buffers):
            raise ValueError('original project module acquired a custom attribute endpoint')
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF != original_self:
            raise ValueError('original allocation clock/resource binding changed')
        if sys._getframe is not original_getframe or sys.modules is not original_modules:
            raise ValueError('original frame/cache endpoints changed')
        if any(globals().get(name) is not fn or fn.__code__ is not code for name, fn, code, _ in helpers):
            raise ValueError('original allocation helper identity/code changed')
        if original_state(original_isfunction) != isfunction_anchor:
            raise ValueError('original function predicate defaults/cells changed')
        if any(original_state(fn) != anchor for _, fn, _, anchor in helpers):
            raise ValueError('original allocation helper defaults/cells changed')
        if original_state(full_guard) != full_anchor:
            raise ValueError('original complete cold guard authority changed')
        for function, namespace, signature in resolution_signatures:
            if function.__globals__ is not namespace or original_state(function) != signature:
                raise ValueError('original reachable function globals/code/default/cells changed')
        # Original relevant class/dispatch authority precedes field reads.
        # No broad executable_state/value_state/JSON encoding is delegated here.
        for owner, kind, mro, records in class_records:
            if type(owner) is not kind or owner.__mro__ != mro or any(a is not b for a, b in zip(owner.__mro__, mro)):
                raise ValueError('actual allocation class type/MRO changed')
            actual = vars(owner)
            if tuple(actual) != tuple(name for name, _ in records) or any(actual[name] is not value for name, value in records):
                raise ValueError('actual allocation class namespace/descriptor identity changed')
        for owner, name, function, anchor in class_functions:
            actual = getattr(owner, name) if isinstance(owner, property) else vars(owner)[name]
            if isinstance(actual, (staticmethod, classmethod)):
                actual = actual.__func__
            if actual is not function or original_state(function) != anchor:
                raise ValueError('actual allocation accessor/constructor/JSON method code/default/cells changed')
        if any(type(module) is not original_module_type for module in json_modules):
            raise ValueError('actual JSON module gained custom attribute authority')
        if any(vars(owner).get(name) is not value for owner, name, value in json_aliases + json_bindings):
            raise ValueError('actual JSON class/module/native hook binding changed')
        for owner, name, function, anchor in json_functions:
            if vars(owner).get(name) is not function or original_state(function) != anchor:
                raise ValueError('actual JSON Python function code/default/cells changed')
        for owner, name, value, kind, entries in json_constants:
            if vars(owner).get(name) is not value or type(value) is not kind:
                raise ValueError('actual JSON constant binding changed')
            if entries is not None and (tuple(value) != tuple(key for key, _, _ in entries)
                    or any(value[key] is not child or type(child) is not child_type for key, child, child_type in entries)):
                raise ValueError('actual JSON constant table entries changed')
        if runtime.guard is not full_guard:
            raise ValueError('original Runtime guard field changed')
        if (graph_module.Recipe is not recipe_class or graph_module.PointGraph is not type(graph)
                or driver_module.Runtime is not type(runtime)
                or driver_module.FirstSelectedProofObserver is not observer_class
                or observer_class.__init__ is not initializer):
            raise ValueError('original allocation class/initializer binding changed')
        if original_state(initializer) != initializer_anchor:
            raise ValueError('original observer initialization code/default/cells changed')
        if type(index) is not int or not 0 <= index < len(recipe_records):
            raise ValueError('exact complete recipe index required')
        if recipe is not recipe_records[index][0] or graph.recipes is not recipes or type(recipe) is not recipe_class:
            raise ValueError('allocation recipe must be the original indexed graph occurrence')
        if progress['busy'] or index not in (progress['index'], progress['index'] + 1):
            raise ValueError('recursive, skipped or reversed allocation row')
        # Invocation is confined to the real private constructor frame. It
        # cannot be reused as a cheap proof/search/point/checker guard later.
        frame = original_getframe(1)
        active = None
        try:
            for _ in range(4):
                if frame is None:
                    break
                if frame.f_code is initializer_anchor[1]:
                    active = frame
                    break
                frame = frame.f_back
            if (active is None or active.f_locals.get('graph') is not graph
                    or active.f_locals.get('runtime') is not runtime
                    or active.f_locals.get('allocation_guard') is not allocation_guard):
                raise ValueError('localized endpoint guard is initializer-only')
            primitive_records = active.f_locals.get('primitives')
            if type(primitive_records) is not list or len(primitive_records) != index:
                raise ValueError('diagnostics require actual completed comparison-prefix length')
            # Each record appended only after the original complete comparisons.
            # This is observation of that fact, not accepted prefix or fit.
            phase_evidence['completed_recipe_comparisons_observed'] = len(primitive_records)
        finally:
            del frame, active
        if any(getattr(runtime, name) is not value for name, value in runtime_fields):
            raise ValueError('original Runtime fixed fields changed')
        if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
            raise TimeoutError('same allocation20/worker55/500 deadline or memory exhausted')
        progress['busy'] = True
        try:
            for role, module, name, file, raw, path, sha, size in buffers:
                record = source_records[role]
                if (module_anchors[role] is not module or original_modules.get(name) is not module
                        or module.__name__ != name or module.__file__ != file
                        or cached_source_buffers[role] is not raw
                        or (record['path'], record['sha256'], record['bytes']) != (path, sha, size)):
                    raise ValueError('original cached raw Source/module ledger replaced')
            if graph_module.json is not json or driver_module.json is not json:
                raise ValueError('actual delegated JSON module changed')
            if any(getattr(driver_module, name) is not fn or original_state(fn) != anchor
                   for name, fn, anchor in driver_functions):
                raise ValueError('actual canonical/predicate/delegation endpoint changed')
            if set(vars(recipe)) != set(fields):
                raise ValueError('original Recipe namespace gained a shadow')
            for name, value, kind in recipe_records[index][1]:
                if getattr(recipe, name) is not value or type(value) is not kind:
                    raise ValueError('original indexed Recipe wire/port field replaced')
            if json._default_decoder is not decoder or type(decoder) is not json.JSONDecoder or tuple(vars(decoder)) != decoder_names:
                raise ValueError('actual default decoder identity/type/namespace changed')
            if any(getattr(decoder, name) is not value or type(value) is not kind for name, value, kind in decoder_fields):
                raise ValueError('actual default decoder hook/scanner fields changed')
            if any(original_state(fn) != anchor for fn, anchor in decoder_functions):
                raise ValueError('actual decoder Python hook code/defaults/cells changed')
            check_endpoint(decoder, decoder_anchor)
            if decoder.scan_once is not scanner or type(scanner) is not scanner_type or scanner_type.__mro__ != scanner_mro:
                raise ValueError('actual native scanner identity/type/MRO changed')
            if next((vars(parent)['__call__'] for parent in scanner_mro if '__call__' in vars(parent)), None) is not scanner_call:
                raise ValueError('actual native scanner callable descriptor changed')
            effective = scanner.__call__
            if type(effective) is not type(scanner_effective) or getattr(effective, '__self__', None) is not scanner:
                raise ValueError('actual native scanner effective receiver changed')
            # Repeat exact originally captured resolution custody after checks;
            # no changed binding is accepted by re-capture or a helper shim.
            # Direct native-only resolution gates precede ANY mutable helper,
            # builtin-name lookup or module property used by the existing body.
            if original_type(original_globals()) is not original_dict:
                raise original_ValueError('original caller global dictionary type changed')
            for namespace, keys, holder, holder_kind, builtin_namespace in namespace_records:
                if original_type(namespace) is not original_dict or original_tuple(namespace) != keys:
                    raise original_ValueError('reachable callable namespace added/lost names')
                if (original_dict_get(namespace, '__builtins__') is not holder
                        or original_type(holder) is not holder_kind
                        or (holder if holder_kind is original_dict else original_vars(holder)) is not builtin_namespace):
                    raise original_ValueError('actual reachable builtin mapping identity/type changed')
            for module, namespace, keys in relevant_namespace_records:
                if (original_type(module) is not original_module_type
                        or original_vars(module) is not namespace or original_tuple(namespace) != keys):
                    raise original_ValueError('actual relevant module namespace added/lost names')
            for namespace, name, global_present, global_value, builtin_namespace, builtin_present, builtin_value in resolution_records:
                if ((name in namespace) is not global_present
                        or original_dict_get(namespace, name) is not global_value
                        or (name in builtin_namespace) is not builtin_present
                        or original_dict_get(builtin_namespace, name) is not builtin_value):
                    raise original_ValueError('actual reachable global/builtin presence or identity changed')
            # Direct post-delegation helper/callback/clock checks precede trust
            # in any completed allocation boundary. No authority is re-sealed.
            if any(globals().get(name) is not module for name, module in module_bindings):
                raise ValueError('original allocation module changed during checks')
            if function_state is not original_state or original_state.__code__ is not state_code or need is not original_need or original_need.__code__ is not need_code:
                raise ValueError('original allocation predicates changed during delegated validators')
            if any(globals().get(name) is not fn or fn.__code__ is not code for name, fn, code, _ in helpers):
                raise ValueError('original allocation helper changed during checks')
            if any(original_state(fn) != anchor for _, fn, _, anchor in helpers) or original_state(full_guard) != full_anchor:
                raise ValueError('original allocation captured authority changed during checks')
            if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF != original_self:
                raise ValueError('original allocation clock changed during checks')
            if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
                raise TimeoutError('allocation boundary completed after unchanged limits')
            progress['index'] = index
        finally:
            progress['busy'] = False
        # Counter metadata itself is charged. No failed boundary is counted as
        # a successful return; incomplete-boundary costs remain outside this
        # sum and the whole caller/owner clocks remain authoritative.
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage:
            raise ValueError('original diagnostic completion clocks changed')
        phase_evidence['completed_boundary_inclusive_seconds'] += original_clock() - boundary_started
        phase_evidence['boundary_returns'] += 1
        phase_evidence['last_returned_boundary_recipe_index'] = index
        if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
            phase_evidence['boundary_returns'] -= 1
            raise TimeoutError('allocation metadata completed after unchanged limits')

    # Full guarded caller runs immediately after return and alone marks the
    # factory_returned latch. Diagnostic data never authorizes construction.
    if time.perf_counter is not original_clock or resource.getrusage is not original_usage:
        raise ValueError('original factory diagnostic clocks changed')
    phase_evidence['factory_capture_seconds'] = original_clock() - phase_started
    if original_clock() >= original_deadline or original_clock() - original_began >= 55 or original_usage(original_self).ru_maxrss >= 524288000:
        raise TimeoutError('allocation-slice capture metadata exceeds unchanged limits')
    return allocation_guard


def main():
    original_clock=time.perf_counter; original_usage=resource.getrusage
    began=original_clock(); deadline=began+20
    original_self=resource.RUSAGE_SELF
    own=sys.modules[__name__]
    helper_functions={name:fn for name,fn in vars(own).items() if inspect.isfunction(fn) and fn.__module__==__name__}
    helper_codes={name:fn.__code__ for name,fn in helper_functions.items()}
    original_state=function_state; state_code=function_state.__code__
    original_isfunction=inspect.isfunction; isfunction_code=inspect.isfunction.__code__
    helper_anchors={name:original_state(fn) for name,fn in helper_functions.items()}
    own_snapshot=executable_state(own,class_roots=(Path,)); own_functions=exact_function_anchors(own_snapshot)
    parser_snapshots=tuple(executable_state(module) for module in (json,json.decoder,json.scanner,json.encoder))
    parser_functions=tuple(anchor for state in parser_snapshots for anchor in exact_function_anchors(state))
    # The cached default decoder is actually used by unchanged Recipe getters
    # and calibration json.loads without hooks; module/class seals alone miss
    # its ordinary instance shadows. Capture once before any project load.
    cached_decoder=json._default_decoder
    need(type(cached_decoder) is json.JSONDecoder,'exact runtime default decoder type')
    cached_decoder_anchor=endpoint_anchor(cached_decoder)
    cached_decoder_fields=tuple((name,value,type(value)) for name,value in vars(cached_decoder).items())
    cached_decoder_names=tuple(vars(cached_decoder))
    cached_decoder_functions=tuple((value,function_state(value)) for _,value,_ in cached_decoder_fields
                                   if inspect.isfunction(value))
    cached_scanner=cached_decoder.scan_once
    cached_scanner_type=type(cached_scanner); cached_scanner_mro=cached_scanner_type.__mro__
    need(cached_scanner_type is json.scanner.c_make_scanner and cached_scanner_type.__module__=='_json',
         'exact frozen native scanner callable, no Python substitute')
    cached_scanner_call=next((vars(parent)['__call__'] for parent in cached_scanner_mro if '__call__' in vars(parent)),None)
    cached_scanner_effective=cached_scanner.__call__
    need(cached_scanner_call is not None and getattr(cached_scanner_effective,'__self__',None) is cached_scanner,
         'actual native scanner receiver bound')
    cached_parser_snapshot=executable_state(json,class_roots=(type(cached_decoder),cached_scanner_type))
    cached_parser_functions=exact_function_anchors(cached_parser_snapshot)
    # Stable handle identities: construction adds endpoints once; later data may
    # change only inside original graph/outcome/counter/ledger transactions.
    handles={'modules':{},'module_anchors':{},'snapshots':[],'functions':[],
             'objects':{},'object_anchors':{},'fixed_fields':{},'mutable_fields':{},
             'plan':None,'sources':None,'source_buffers':{},'call_tape':[], 'sealed':False,
             'nested_callbacks':()}
    def direct():
        if (time.perf_counter is not original_clock or resource.getrusage is not original_usage
                or resource.RUSAGE_SELF!=original_self):
            raise ValueError('original clock/resource endpoints changed')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original function-state validator changed')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name]
               for name,fn in helper_functions.items()):
            raise ValueError('original own loading/rejection/serialization validator identity/code changed')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('original own validator defaults/closure changed')
        if json._default_decoder is not cached_decoder or type(cached_decoder) is not json.JSONDecoder:
            raise ValueError('original actual cached decoder identity/type changed')
        if tuple(vars(cached_decoder))!=cached_decoder_names:
            raise ValueError('actual decoder instance acquired a method/field shadow')
        if any(getattr(cached_decoder,name) is not value or type(value) is not kind
               for name,value,kind in cached_decoder_fields):
            raise ValueError('actual decoder hook/scanner/memo binding changed')
        if any(original_state(fn)!=anchor for fn,anchor in cached_decoder_functions):
            raise ValueError('cached decoder Python hook code/default/cells changed')
        if (cached_decoder.scan_once is not cached_scanner or type(cached_scanner) is not cached_scanner_type
                or cached_scanner_type.__mro__!=cached_scanner_mro
                or any(a is not b for a,b in zip(cached_scanner_type.__mro__,cached_scanner_mro))):
            raise ValueError('actual native scanner identity/type/MRO changed')
        if next((vars(parent)['__call__'] for parent in cached_scanner_mro if '__call__' in vars(parent)),None) is not cached_scanner_call:
            raise ValueError('native scanner callable descriptor changed')
        effective_scanner=cached_scanner.__call__
        if type(effective_scanner) is not type(cached_scanner_effective) or getattr(effective_scanner,'__self__',None) is not cached_scanner:
            raise ValueError('actual native scanner effective receiver changed')
        check_endpoint(cached_decoder,cached_decoder_anchor)
        check_exact_functions(cached_parser_functions)
        unchanged_executable(cached_parser_snapshot)
    direct_fn=direct; direct_anchor=original_state(direct_fn)
    def guarded_direct():
        # This rejection does not call the potentially changed validator first.
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('own state helper changed before direct guard')
        if globals().get('need') is not helper_functions['need'] or helper_functions['need'].__code__ is not helper_codes['need']:
            raise ValueError('own rejector changed before direct guard')
        if direct_fn is not direct or direct_fn.__code__ is not direct_anchor[1]:
            raise ValueError('direct guard shim changed')
        if original_state(direct_fn)!=direct_anchor:
            raise ValueError('direct guard default/closure changed')
        direct_fn()
    gd_fn=guarded_direct; gd_anchor=original_state(gd_fn)
    def tick(*, inner):
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('own state helper changed before clock')
        if gd_fn is not guarded_direct or gd_fn.__code__ is not gd_anchor[1]:
            raise ValueError('clock delegation shim changed')
        if original_state(gd_fn)!=gd_anchor:
            raise ValueError('clock shim default/closure changed')
        gd_fn()
        if original_clock()-began>=55 or original_usage(original_self).ru_maxrss>=524288000:
            raise TimeoutError('whole55/500 worker reserve exhausted')
        if inner and original_clock()>=deadline:
            raise TimeoutError('all successful work/output exceeded original shared20')
    tick_fn=tick; tick_anchor=original_state(tick_fn)
    def checked_tick(*, inner):
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original validator changed before tick delegation')
        if tick_fn is not tick or tick_fn.__code__ is not tick_anchor[1]:
            raise ValueError('tick code/identity changed')
        if original_state(tick_fn)!=tick_anchor:
            raise ValueError('tick defaults/captured authority changed')
        tick_fn(inner=inner)
        if tick_fn is not tick or tick_fn.__code__ is not tick_anchor[1] or original_state(tick_fn)!=tick_anchor:
            raise ValueError('tick changed during delegation')
    ct_fn=checked_tick; ct_anchor=original_state(ct_fn)
    def source_guard():
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('own validator changed before source guard')
        # Check each original local executable, not only the module globals.
        if any(fn.__code__ is not anchor[1] for fn,anchor in handles['nested_callbacks']):
            raise ValueError('local clock/guard/writer code changed before delegated authority')
        if any(original_state(fn)!=anchor for fn,anchor in handles['nested_callbacks']):
            raise ValueError('local callback defaults/cell authority changed before delegation')
        if ct_fn is not checked_tick or ct_fn.__code__ is not ct_anchor[1] or original_state(ct_fn)!=ct_anchor:
            raise ValueError('source guard clock shim changed')
        ct_fn(inner=False)  # Driver Runtime/checker Boundary own the inner20.
        check_exact_functions(own_functions); check_exact_functions(parser_functions)
        unchanged_executable(own_snapshot)
        for state in parser_snapshots:
            unchanged_executable(state)
        for state in handles['snapshots']:
            unchanged_executable(state)
        for anchors in handles['functions']:
            check_exact_functions(anchors)
        for name,obj in handles['objects'].items():
            check_endpoint(obj,handles['object_anchors'][name])
            for field,value in handles['fixed_fields'].get(name,()):
                need(getattr(obj,field) is value,'fixed constructed binding/handle replaced')
            for field,value,kind in handles['mutable_fields'].get(name,()):
                need(getattr(obj,field) is value and type(value) is kind,'declared mutable data container replaced')
        if 'graph' in handles['objects']:
            actual_graph=handles['objects']['graph']; graph_module=handles['modules']['point_graph']
            # Dynamic keys are constructed later by the unchanged engine. Their
            # effective data method must be the already sealed class endpoint;
            # never adopt a per-instance callable while taking a state snapshot.
            dynamic_keys=list(actual_graph.order)
            dynamic_keys.extend(key for excluded in actual_graph.excluded for key in excluded)
            dynamic_keys.extend(entry[1] for entry in actual_graph.trail)
            for key in dynamic_keys:
                need(type(key) is graph_module.Key and set(vars(key))=={'recipe','row','refs'},
                     'actual dynamic key type/fields, no instance shadow')
                effective=key.data
                need(getattr(effective,'__self__',None) is key
                     and getattr(effective,'__func__',None) is graph_module.Key.data,
                     'dynamic key effective data endpoint changed')
        if handles['sources'] is not None:
            source_cache_guard(handles['sources'],handles['modules'],handles['module_anchors'])
        # Direct post-delegation rejection comes before relying on own helpers.
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('own validator changed during guard')
        if gd_fn is not guarded_direct or gd_fn.__code__ is not gd_anchor[1] or original_state(gd_fn)!=gd_anchor:
            raise ValueError('direct guard changed during delegation')
        gd_fn()
        check_exact_functions(own_functions); check_exact_functions(parser_functions)
        for anchors in handles['functions']:
            check_exact_functions(anchors)
        ct_fn(inner=False)
    guard_fn=source_guard; guard_anchor=original_state(guard_fn)
    def invoke_guard():
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original validator changed before guard delegation')
        if guard_fn is not source_guard or guard_fn.__code__ is not guard_anchor[1]:
            raise ValueError('source callback identity/code changed')
        if original_state(guard_fn)!=guard_anchor:
            raise ValueError('source callback defaults/cell authority changed')
        guard_fn()
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original validator changed during guard callback')
        if guard_fn is not source_guard or guard_fn.__code__ is not guard_anchor[1] or original_state(guard_fn)!=guard_anchor:
            raise ValueError('source callback changed while delegated')
        gd_fn()
    invoke_fn=invoke_guard; invoke_anchor=original_state(invoke_fn)
    def boundary(*, inner):
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('validator changed before boundary')
        if invoke_fn is not invoke_guard or invoke_fn.__code__ is not invoke_anchor[1] or original_state(invoke_fn)!=invoke_anchor:
            raise ValueError('original guard invoking shim changed')
        invoke_fn(); checked_tick(inner=inner)
        if invoke_fn is not invoke_guard or invoke_fn.__code__ is not invoke_anchor[1] or original_state(invoke_fn)!=invoke_anchor:
            raise ValueError('guard invoking shim changed after boundary')
    boundary_fn=boundary; boundary_anchor=original_state(boundary_fn)
    def checked_boundary(*, inner):
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('validator changed before final boundary delegation')
        if boundary_fn is not boundary or boundary_fn.__code__ is not boundary_anchor[1] or original_state(boundary_fn)!=boundary_anchor:
            raise ValueError('final boundary callback authority changed')
        boundary_fn(inner=inner)
        if boundary_fn is not boundary or boundary_fn.__code__ is not boundary_anchor[1] or original_state(boundary_fn)!=boundary_anchor:
            raise ValueError('final boundary changed while invoked')
    cb_fn=checked_boundary; cb_anchor=original_state(cb_fn)
    def call(function,*args,**kwargs):
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('validator changed before guarded function')
        if cb_fn is not checked_boundary or cb_fn.__code__ is not cb_anchor[1] or original_state(cb_fn)!=cb_anchor:
            raise ValueError('current boundary authority changed before call')
        cb_fn(inner=True)
        anchor=original_state(function)
        result=function(*args,**kwargs)
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('validator changed during function')
        if original_state(function)!=anchor:
            raise ValueError('actual called code/default/closure changed')
        cb_fn(inner=True)
        return result
    call_fn=call; call_anchor=original_state(call_fn)
    def save(path,value,*,inner):
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('own validator changed before writer')
        if cb_fn is not checked_boundary or cb_fn.__code__ is not cb_anchor[1] or original_state(cb_fn)!=cb_anchor:
            raise ValueError('writer boundary changed')
        cb_fn(inner=inner)
        h=hashlib.sha256(); count=maximum=since=0
        with path.open('xb') as stream:
            for chunk in json_chunks(value):
                raw=chunk.encode('utf8'); need(len(raw)<=4*1048576,'bounded complete canonical output chunk')
                need(stream.write(raw)==len(raw),'complete output write')
                h.update(raw); count+=len(raw); maximum=max(maximum,len(raw)); since+=len(raw)
                if since>=65536:
                    cb_fn(inner=inner); since=0
        cb_fn(inner=inner)
        record=pin(path); need(record['bytes']==count and record['sha256']==h.hexdigest(),'whole output byte/SHA/EOF')
        cb_fn(inner=inner)
        return record
    save_fn=save; save_anchor=original_state(save_fn)
    # Own nested callbacks retain stable handles; no code/cell anchor resealing.
    nested={'direct':(direct_fn,direct_anchor),'guarded_direct':(gd_fn,gd_anchor),
            'tick':(tick_fn,tick_anchor),'checked_tick':(ct_fn,ct_anchor),
            'source_guard':(guard_fn,guard_anchor),'invoke_guard':(invoke_fn,invoke_anchor),
            'boundary':(boundary_fn,boundary_anchor),'checked_boundary':(cb_fn,cb_anchor),
            'call':(call_fn,call_anchor),'save':(save_fn,save_anchor)}
    # The dictionary is captured in no earlier callable closure; verify directly
    # at every outer post-return and output delegation boundary too.
    def outer():
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('own validator changed before outer delegation')
        if any(fn.__code__ is not anchor[1] for fn,anchor in nested.values()):
            raise ValueError('own nested callback code changed')
        if any(original_state(fn)!=anchor for fn,anchor in nested.values()):
            raise ValueError('own nested callback defaults/cell authority changed')
        cb_fn(inner=True)
        if any(original_state(fn)!=anchor for fn,anchor in nested.values()):
            raise ValueError('own nested callback changed during outer boundary')
    outer_fn=outer; outer_anchor=original_state(outer_fn)
    handles['nested_callbacks']=tuple(nested.values())+((outer_fn,outer_anchor),)
    plan=owner=output=graph=events=result=None; output_files={}; error=None; returned=False
    allocation_phase={'schema':'Q-private-allocation-phase-evidence-v1',
        'factory_started':False,'factory_returned':False,'factory_capture_seconds':None,
        'boundary_entries':0,'boundary_returns':0,'last_started_recipe_index':None,
        'last_returned_boundary_recipe_index':None,'completed_recipe_comparisons_observed':0,
        'completed_boundary_inclusive_seconds':0.0,'constructor_returned':False,
        'constructor_recipe_interfaces':None}
    stage_completed=False
    try:
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        need(len(sys.argv)==4 and sys.argv[1]==COMMAND,'one literal cold first-proof invocation')
        plan_path,owner_path=(Path(value) for value in sys.argv[2:])
        need(all(path.is_absolute() and path==path.resolve() for path in (plan_path,owner_path)),'canonical flat leaf/owner paths')
        plan,owner,output,plan_pin,owner_pin,closure,owner_closure=call_fn(preflight,plan_path,owner_path)
        handles['plan']=plan; handles['sources']=plan['sources']
        documents={name:call_fn(read,record) for name,record in plan['inputs'].items()
                   if name not in ('producer_preparation','initial_state','initial_oracle_domains')}
        for document in documents.values():
            call_fn(authenticate_named,document,closure)
        call_fn(validate_producer,documents,closure)
        certificate=call_fn(validate_admitted,documents,closure)
        preparation=call_fn(read_lossless_preparation,FROZEN_INPUTS['producer_preparation'])
        declaration=documents['declaration']; catalogue=preparation['catalogue']
        need(catalogue['declaration']==declaration and catalogue['authority']['source_bindings']==PRODUCER_SOURCES,
             'same complete original declaration and raw producer7 model')
        immutable_inputs={'plan':plan,'owner':owner,'documents':documents,'preparation':preparation,
                          'original_producer_sources':PRODUCER_SOURCES}
        input_seal=call_fn(value_digest,immutable_inputs,lambda: cb_fn(inner=True))
        output.mkdir()
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        for role in ('point_graph','independent_checker','driver','calibration'):
            source_raw=call_fn(checked_buffer,plan['sources'][role],2*1048576)
            handles['source_buffers'][role]=source_raw
            module=call_fn(load_cached,plan['sources'][role], '_ROOT_cold_Q_'+role,source_raw,
                           role=role,registration=handles)
            need(handles['modules'][role] is module and handles['module_anchors'][role] is module,
                 'loader completed exact owned registration before postguard')
            # V5 immediate original caller guard BEFORE outer delegation
            if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
                raise ValueError('original clock/resource changed before outer caller trust')
            if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
                raise ValueError('original function-type predicate changed before outer caller trust')
            if function_state is not original_state or function_state.__code__ is not state_code:
                raise ValueError('original state predicate changed before outer caller trust')
            if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
                raise ValueError('own helper/rejector changed before outer caller delegation')
            if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
                raise ValueError('own helper defaults/cells changed before outer caller delegation')
            if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
                raise ValueError('original outer identity/code/default/cells changed at direct caller')
            outer_fn()
            # V5 immediate original caller guard AFTER outer delegation
            if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
                raise ValueError('original clock/resource changed before outer caller trust')
            if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
                raise ValueError('original function-type predicate changed before outer caller trust')
            if function_state is not original_state or function_state.__code__ is not state_code:
                raise ValueError('original state predicate changed before outer caller trust')
            if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
                raise ValueError('own helper/rejector changed before outer caller delegation')
            if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
                raise ValueError('own helper defaults/cells changed before outer caller delegation')
            if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
                raise ValueError('original outer identity/code/default/cells changed at direct caller')
        module=handles['modules']['point_graph']; checker=handles['modules']['independent_checker']; driver=handles['modules']['driver']
        calibration=handles['modules']['calibration']
        need(driver.VERSION=='Q-baseline-first-actual-selected-proof-Source-v3'
             and driver.CURRENT['model_epoch']==CURRENT['model_epoch'],'exact current API/context')
        boundary_data=catalogue['boundary']
        graph=call_fn(construct_owned,'graph',registration=handles,guarded_call=call_fn,keywords=dict(
            height=catalogue['height'],formulas=catalogue['formula_codes'],recipe_data=catalogue['recipes'],
            context=catalogue['context'],authority=catalogue['authority'],fixed_marks=boundary_data['fixed_marks'],
            roots=boundary_data['roots'],seed_keys=(),fixture=False,source_bindings=PRODUCER_SOURCES))
        need(graph.model_epoch==CURRENT['model_epoch'] and graph.authority_epoch==CURRENT['primitive_authority_epoch']
             and graph.registry_sha==CURRENT['formula_registry_sha256'],'original model/authority/registry, no new source epoch model')
        runtime=call_fn(construct_owned,'runtime',registration=handles,guarded_call=call_fn,
            keywords=dict(began=began,deadline=deadline,source_guard=invoke_fn))
        binding={'schema':'Q-first-selected-proof-original-context-binding-v1',
            'finite_admission':FROZEN_INPUTS['finite_ROOT_admission'],
            'finite_certificate':FROZEN_INPUTS['finite_audit_certificate'],
            'word_controls':FROZEN_INPUTS['actual_word_controls_ROOT'],
            'declaration':FROZEN_INPUTS['declaration'],'preparation':FROZEN_INPUTS['producer_preparation'],
            'initial_state_witness':FROZEN_INPUTS['initial_state'],
            'initial_oracle_witness':FROZEN_INPUTS['initial_oracle_domains'],
            'model_epoch':graph.model_epoch,'primitive_authority_epoch':graph.authority_epoch,
            'formula_registry_sha256':graph.registry_sha}
        allocation_guard=call_fn(make_recipe_allocation_guard,graph_module=module,driver_module=driver,
            graph=graph,runtime=runtime,source_records=plan['sources'],
            cached_source_buffers=handles['source_buffers'],module_anchors=handles['module_anchors'],
            full_guard=invoke_fn,phase_evidence=allocation_phase)
        allocation_phase['factory_returned']=True
        allocation_anchor=original_state(allocation_guard)
        # Original Source-copy factory code is already in the sealed own module.
        # Register this newly returned callback ONCE before constructor use;
        # its private row counter may evolve, executable authority may not.
        handles['nested_callbacks']=handles['nested_callbacks']+((allocation_guard,allocation_anchor),)
        observer=call_fn(construct_owned,'observer',registration=handles,guarded_call=call_fn,
            keywords=dict(graph=graph,catalogue=catalogue,declaration=declaration,checker_module=checker,
                          runtime=runtime,context_binding=binding,allocation_guard=allocation_guard))
        # Full construction and mandatory caller postguard have returned; this
        # diagnostic is not a target, point certificate or accepted prefix.
        allocation_phase['constructor_returned']=True
        allocation_phase['constructor_recipe_interfaces']=len(observer.primitives)
        # Every actual generated/dataclass class and property/code root is already
        # module-snapshotted. Recipes are immutable field records; compare all of
        # them before and after search, not just output counts.
        fixed_graph={'height':graph.height,'fixture':graph.fixture,'formulas':graph.formulas,
            'context':graph.context,'authority':graph.authority,'source_bindings':graph.source_bindings,
            'recipes':[[r.index,r.identifier,r.witness_text,list(r.premise_texts),r.output,list(r.inputs)] for r in graph.recipes],
            'recipe_index':graph.recipe_index,'roots':list(graph.roots),'initial_marks':[[*p,v] for p,v in sorted(graph.initial_marks.items())],
            'registry_sha':graph.registry_sha,'context_id':graph.context_id,'authority_epoch':graph.authority_epoch,
            'model_epoch':graph.model_epoch,'initial_selected':[key.data() for key in graph.initial_selected]}
        fixed_graph_seal=call_fn(value_digest,fixed_graph,lambda: cb_fn(inner=True))
        state=call_fn(module.PointGraph.semantic_state,graph)
        need(state==preparation['initial_state'],'full initial state relation matches original one-parse preparation')
        initial_state_sha=call_fn(value_digest,state,lambda: cb_fn(inner=True))
        del state
        events=call_fn(construct_owned,'events',registration=handles,guarded_call=call_fn,
            arguments=(output/'events-v1',runtime),keywords={})
        handles['sealed']=True
        entry=graph.checkpoint()
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        # This call is NOT run_first_checked_Q. A declared five-role controls
        # ledger never executes search main/preflight or any future search grant.
        control_fn=calibration.run_Q_first_proof_controls
        control_anchor=original_state(control_fn)
        start_event={'ordinal':0,'event':'started','operation':'run_Q_first_proof_controls','source':CALIBRATION,
            'worker_elapsed_seconds':original_clock()-began,'context_binding':binding,
            'scientific_worker_subject_raw_only':SCIENTIFIC_SUBJECT,'target_searches':0}
        handles['call_tape'].append(start_event)
        output_files['call_started']=save_fn(output/'Q-controls-call-started-v1.json',start_event,inner=True)
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        try:
            result=control_fn(driver_module=driver,point_module=module,checker_module=checker,
                graph=graph,observer=observer,runtime=runtime,events=events,context_binding=binding,
                catalogue=catalogue,declaration=declaration,initial_state_record=FROZEN_INPUTS['initial_state'],
                initial_oracle_record=FROZEN_INPUTS['initial_oracle_domains'],
                fixture_document=documents['calibration_fixtures'],source_guard=invoke_fn)
            returned=True
            handles['call_tape'].append({'ordinal':1,'event':'returned','operation':'run_Q_first_proof_controls',
                'source':CALIBRATION,'worker_elapsed_seconds':original_clock()-began,'target_searches':0})
        except BaseException as failure:
            handles['call_tape'].append({'ordinal':1,'event':'raised','operation':'run_Q_first_proof_controls',
                'source':CALIBRATION,'worker_elapsed_seconds':original_clock()-began,'target_searches':0,
                'error':{'type':type(failure).__name__,'message':str(failure)[:2048]}})
            raise
        late=original_clock()>=deadline
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original own validator changed after controls return')
        if save_fn is not save or save_fn.__code__ is not save_anchor[1] or original_state(save_fn)!=save_anchor:
            raise ValueError('original controls return writer changed')
        output_files['returned_result']=save_fn(output/'Q-proof-neutral-controls-return-provisional-v1.json',result,inner=not late)
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        need(calibration.run_Q_first_proof_controls is control_fn and original_state(control_fn)==control_anchor,
             'actual calibration entry identity/code/default/closure unchanged')
        coverage=documents['calibration_coverage']
        need(type(result) is dict and result['schema']==coverage['result_schema'], 'exact whole control result API')
        for name,value in coverage['required_success_booleans'].items():
            need(value is True and result[name] is True,'literal completed implemented controls only')
        for name,value in coverage['required_false_booleans'].items():
            need(value is False and result[name] is False,'no strong flags or future search admission from controls')
        for name in coverage['required_zero_counters']:
            need(type(result[name]) is int and result[name]==0,'literal zero search/target counter, boolean invalid')
        rows=result['results']
        expected_ids=coverage['current_dynamic_control_ids']+coverage['whole_literal_control_ids']
        need(type(rows) is list and [row['id'] for row in rows]==expected_ids
             and type(result['implemented_control_count']) is int
             and result['implemented_control_count']==len(rows)
             and all(row['completed'] is True and row['all_checks_passed'] is True for row in rows),
             'every actually declared dynamic and literal control complete in order; no accepted prefix')
        # The one independent initial scan is owned by the first control itself.
        initial=rows[0]['evidence']['full_initial_point_check']
        need(initial['exact_saved_point_union_accepted'] is True
             and initial['domain_sha256_by_row']==certificate['initial_point_domains']['domain_sha256_by_row']
             and initial['domain_counts']==certificate['initial_point_domains']['domain_counts']
             and initial['complete_candidate_count']==certificate['initial_point_domains']['complete_candidate_count'],
             'actual all24 byte/EOF/oracle relation matches original finite audit, without duplicate wrapper scan')
        need(graph.checkpoint()==entry,'complete control rollback checkpoint')
        restored=call_fn(module.PointGraph.semantic_state,graph)
        need(call_fn(value_digest,restored,lambda: cb_fn(inner=True))==initial_state_sha,'whole actual state restored')
        del restored
        fixed_graph_after={'height':graph.height,'fixture':graph.fixture,'formulas':graph.formulas,
            'context':graph.context,'authority':graph.authority,'source_bindings':graph.source_bindings,
            'recipes':[[r.index,r.identifier,r.witness_text,list(r.premise_texts),r.output,list(r.inputs)] for r in graph.recipes],
            'recipe_index':graph.recipe_index,'roots':list(graph.roots),'initial_marks':[[*p,v] for p,v in sorted(graph.initial_marks.items())],
            'registry_sha':graph.registry_sha,'context_id':graph.context_id,'authority_epoch':graph.authority_epoch,
            'model_epoch':graph.model_epoch,'initial_selected':[key.data() for key in graph.initial_selected]}
        need(call_fn(value_digest,fixed_graph_after,lambda: cb_fn(inner=True))==fixed_graph_seal,'whole fixed original graph unchanged')
        need(call_fn(value_digest,immutable_inputs,lambda: cb_fn(inner=True))==input_seal,'all decoded inputs/fixture values unchanged')
        for record in closure.values():
            call_fn(verify,record)
        for raw_record in owner['closure']:
            call_fn(verify,normalize(raw_record))
        event_inventory=[]
        for path in sorted((output/'events-v1').iterdir()):
            need(path.is_file() and not path.is_symlink(),'only literal owned calibration/snapshot files')
            event_inventory.append(call_fn(pin,path))
        for record in result['complete_event_and_serializer_files']:
            need(record in event_inventory,'complete every event/serializer raw output retained'); call_fn(verify,record)
        ledger=call_fn(source_cache_guard,plan['sources'],handles['modules'],handles['module_anchors'])
        need(len(ledger)==len(EXECUTED_ROLES) and {record['path'] for record in ledger}==
             {plan['sources'][role]['path'] for role in EXECUTED_ROLES},'complete actual five-role controls execution ledger')
        evidence={'schema':'Q-proof-neutral-cold-controls-evidence-v1','allocation_initialization_phase_evidence':dict(allocation_phase),'worker_plan':plan_pin,'owner_plan':owner_pin,
            'sources':plan['sources'],'inputs':plan['inputs'],'original_producer_sources':PRODUCER_SOURCES,
            'scientific_worker_subject_raw_only':SCIENTIFIC_SUBJECT,'source_execution_ledger':ledger,
            'context_binding':binding,'initial_point_check_from_single_suite_scan':initial,
            'initial_state_sha256':initial_state_sha,'immutable_input_seal_before':input_seal,
            'immutable_input_seal_after':input_seal,'fixed_model_seal_before':fixed_graph_seal,
            'fixed_model_seal_after':fixed_graph_seal,'call_tape':handles['call_tape'],
            'actual_started_control_calls':1,'actual_returned_control_calls':1,'actual_raised_control_calls':0,
            'target_searches':0,'production_driver_search_calls':0,'target_proof_discovered':False,
            'returned_result':output_files['returned_result'],'all_event_and_serializer_outputs':event_inventory,
            'coverage':coverage['coverage'],'implemented_results':rows,'deferred':result['deferred'],
            'all11_prerequisites_qualified':False,'native_accepted':False,'full24_accepted':False,
            'full_trajectory_accepted':False,'full_PA_accepted':False,'induction_accepted':False,'RL_used':False,
            'inner_scope':'One parse/graph/setup/suite/single initial point scan/all outputs and final guards in original20',
            'inner_seconds_before_evidence_write':original_clock()-began,'peak_self_bytes':original_usage(original_self).ru_maxrss}
        output_files['evidence']=save_fn(output/'Q-proof-neutral-controls-evidence-v1.json',evidence,inner=True)
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        receipt={'schema':'Q-proof-neutral-cold-controls-receipt-v1','allocation_initialization_phase_evidence':dict(allocation_phase),'stage':'replay',
            'scientific_stage':'proof-neutral-original-Q-and-authored-calibration-controls-only','stage_completed':True,
            'worker_plan':plan_pin,'owner_plan':owner_pin,'sources':plan['sources'],'inputs':plan['inputs'],
            'evidence':output_files['evidence'],'returned_result':output_files['returned_result'],
            'call_started':output_files['call_started'],'actual_started_control_calls':1,'actual_returned_control_calls':1,
            'actual_raised_control_calls':0,'target_searches':0,'production_driver_search_calls':0,
            'target_proof_discovered':False,'native_queries':0,'native_replays':0,
            'implemented_control_count':result['implemented_control_count'],'production_selected_point_moves':result['production_selected_point_moves'],
            'coverage':coverage['coverage'],'deferred':result['deferred'],'all11_prerequisites_qualified':False,
            'selected_target_proof_accepted':False,'full24_accepted':False,'full_trajectory_accepted':False,
            'full_PA_accepted':False,'induction_accepted':False,'library_used':False,'rank_used':False,'RL_used':False,
            'ROOT_resource_accepted':False,'ROOT_search_activation_issued':False,
            'all_direct_children_terminal_and_reaped':True,'direct_children_peak_sum_bytes':0,
            'requires_ROOT_group_cleanup':False,
            'scope':'Finite actual init/passivity/canonical point move+rollback and labelled calibration only; no search/target/full11/FOUND/fullboard authority',
            'inner_seconds_before_receipt_write':original_clock()-began,'peak_self_bytes':original_usage(original_self).ru_maxrss}
        receipt_pin=save_fn(output/RECEIPT,receipt,inner=True)
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        post={'schema':'Q-proof-neutral-controls-worker-postwrite-v1','receipt':receipt_pin,
            'whole_worker_seconds':original_clock()-began,'inner_completed_inside_original20':True,
            'peak_self_bytes':original_usage(original_self).ru_maxrss,'all_direct_children_terminal_and_reaped':True,
            'ROOT_resource_accepted':False}
        save_fn(output/'Q-proof-neutral-controls-postwrite-v1.json',post,inner=True)
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        line=canonical({'schema':'Q-proof-neutral-controls-console-v1','stage':'replay','stage_completed':True,
            'receipt':receipt_pin,'target_searches':0,'implemented_control_count':result['implemented_control_count'],
            'all11_prerequisites_qualified':False,'worker_seconds':original_clock()-began})
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        print(line,flush=True)
        # V5 immediate original caller guard BEFORE outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        outer_fn()
        # V5 immediate original caller guard AFTER outer delegation
        if time.perf_counter is not original_clock or resource.getrusage is not original_usage or resource.RUSAGE_SELF!=original_self:
            raise ValueError('original clock/resource changed before outer caller trust')
        if inspect.isfunction is not original_isfunction or inspect.isfunction.__code__ is not isfunction_code:
            raise ValueError('original function-type predicate changed before outer caller trust')
        if function_state is not original_state or function_state.__code__ is not state_code:
            raise ValueError('original state predicate changed before outer caller trust')
        if any(globals().get(name) is not fn or fn.__code__ is not helper_codes[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper/rejector changed before outer caller delegation')
        if any(original_state(fn)!=helper_anchors[name] for name,fn in helper_functions.items()):
            raise ValueError('own helper defaults/cells changed before outer caller delegation')
        if outer_fn is not outer or outer_fn.__code__ is not outer_anchor[1] or original_state(outer_fn)!=outer_anchor:
            raise ValueError('original outer identity/code/default/cells changed at direct caller')
        stage_completed=True
    except BaseException as failure:
        error={'type':type(failure).__name__,'message':str(failure)[:2048]}
        # No successful latch survives any guard/timeout/writer/final failure.
        # Existing full returned tape is provisional evidence, never amended.
        # Failure-only metadata cannot call a graph/checker/search again.
        if output is not None and output.exists():
            try:
                if function_state is not original_state or function_state.__code__ is not state_code:
                    raise ValueError('cannot delegate failure writer through changed validator')
                if save_fn is not save or save_fn.__code__ is not save_anchor[1] or original_state(save_fn)!=save_anchor:
                    raise ValueError('cannot delegate failure writer through changed callback')
                record={'schema':'Q-proof-neutral-cold-controls-failure-v1','status':'UNKNOWN','stage_completed':False,
                    'allocation_initialization_phase_evidence':dict(allocation_phase),
                    'error':error,'call_tape':handles['call_tape'],'actual_started_control_calls':
                    sum(item['event']=='started' for item in handles['call_tape']),
                    'actual_returned_control_calls':sum(item['event']=='returned' for item in handles['call_tape']),
                    'actual_raised_control_calls':sum(item['event']=='raised' for item in handles['call_tape']),
                    'returned_value_available':returned,'output_files':output_files,
                    'selected_target_proof_accepted':False,'full24_accepted':False,'full_trajectory_accepted':False,
                    'native_accepted':False,'RL_used':False,'ROOT_resource_accepted':False,
                    'failure_only_worker_seconds':original_clock()-began}
                save_fn(output/'Q-proof-neutral-controls-failure-v1.json',record,inner=False)
            except BaseException:
                # Raw existing partial outputs plus owner stderr/termination are
                # retained. Do not bypass a broken guard to create acceptance.
                pass
        raise
    finally:
        # Any failure after writing a prospective receipt still exits nonzero;
        # generic owner/ROOT final gates cannot use a stale stage-complete file.
        if not stage_completed:
            pass


if __name__=='__main__':
    main()
