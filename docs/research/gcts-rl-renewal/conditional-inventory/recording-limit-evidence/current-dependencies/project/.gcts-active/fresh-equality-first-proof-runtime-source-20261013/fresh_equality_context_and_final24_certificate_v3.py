"""SOURCE ONLY fresh donor/evaluation final primitive certificate helper, no dispatcher.

The future ROOT-owned caller supplies the exact unchanged GroundChecker class
and one ROOT-issued qualified context record. This helper imports no project
module, constructs no graph and searches for nothing. It checks final witness
and physical identities; it does NOT replay the search, qualify its resources,
or accept RNG/reward/update/performance claims. All file reading, selected AST
expansion and returned reader-data construction belong to that caller's phase.
"""
import gzip
import hashlib
import io
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'independent-compact24-primitive-advice-pair-final-certificate-v1'
QUALIFICATION = 'ROOT-qualified-compact-proof-context-v1'
DFS = 'compact24-first-checked-proof-scientific-DFS-v11-source'
MARKING = 'injective-formula-ordered-mp-offset-v1'
DECLARATION = 'fresh-ground-cohort-context-declaration-v1'
RULES = ('axiom', 'instantiate', 'eq_subst', 'mp', 'assumption')
ROW = struct.Struct('<11Q32s32s')
WORD = struct.Struct('<Q')
SENTINEL = (1 << 64) - 1
MAX_JSON_BYTES = 64 * 1024 * 1024
KERNEL_SHA = 'a9c960735f0f132933dd8e6c3aa44fa9c1b36efd44ecdcb24279929690dc773e'
DFS_SHA = 'a2cf1bb6d3ede1695d08f7c0d6f709bd5e9a6bc493ff06f1febe2fd4650269e4'
ADVICE_SOURCE = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-incidence-priority-source-20261013/incidence_priority_witness_advice_v2.py', 'sha256': '3a86adba8982c406ae4a2ad3349b8ae962e52498dee38ee3ee26719b22468053', 'bytes': 27264}
COHORT_INPUTS = {
    'fixture': {'path': str(ROOT / '.gcts-active/ground-cohort-prospective-source-20261012/cohort-statements-v1.json'),
        'sha256': 'd51db816d4711812d1b0d41356b131b4d5154cb3d16683b31a5ec3e0dc6cbb56', 'bytes': 7902},
    'syntax_seeds': {'path': str(ROOT / '.gcts-active/ground-cohort-prospective-source-20261012/syntax-seeds-v1.json'),
        'sha256': '977820ba0a678c646fd90db45279cdfcc567131344db0727466718c5f966a7f4', 'bytes': 1282}}
PRODUCER_SHAS = {
    'compiler': 'f8afce27207eb86d638bb8924ef1479945761cbd9266bf69d749b309eb4ce568',
    'decoder': '5b7ce634334ac85208db578170360c42dfea702cb9c07cdad91ba67431e4492f',
    'compact_engine': 'd638f7152ec7fa8293adbd8915b79de60f95d0756952bdc6bf0e40b15f549ca0',
    'worker': '4593a611d4fbe485e995b2901634efd6c7f99f1b46408ccc9e7aa6f8d9a000fb',
    'point_core': 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd',
    'master': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}
AUDIT_SHAS = {
    'grammar': '10c77aa23284c5d2587a26c8f239604a444f9d94ef848eb19e1196f30b8d5b35',
    'catalog_audit': '1087243d2377375b5997c0880646de33db234073af8682ec9ca4a55f1b5a2986',
    'domains': '1b9d6b94c78f363ba20f48234dc1eb48ac9dcfa548e8f0fa1a7350699b059b34',
    'worker': '80111c971bb170072a95a2a5fc8c72140d401d1dc7527894ac6fc7931df04a08',
    'logical_oracle': KERNEL_SHA, 'master': PRODUCER_SHAS['master']}
ORIGINAL_INPUTS = {'fixture': {'path': str(ROOT / '.gcts-active/cluster-transfer-theorem-source-20261012/fixtures-v2.json'),
    'sha256': 'b17ba2cea0dd5d595e39c7c38f3d7cefce2d2c040ba1f3fd4a4aa10418bd99f8', 'bytes': 24474}}
ORIGINAL_PRODUCER_SHAS = dict(PRODUCER_SHAS,
    compiler='be5d6fdf80a28effaefb1e0fa69bfce32dd262d05db8a7a0eed377d51e72481c',
    decoder='46e3b26a688d64665303238d7d8f3f9b54345cc98e17d903403ca1b62b9b0293',
    worker='db4f65b1ac6a21410707eb6c31f20de4c96672327b1aa7a6dcc40085bd932236')
ORIGINAL_AUDIT_SHAS = dict(AUDIT_SHAS,
    grammar='86b8c916344c34629450bc12a0251b8ec9a0c29ce1542d1e039966879fb3278e',
    catalog_audit='db4dc3b904715be3123ed1a9b22eb1ce9144c35aa00c610da94f13263e4334e8',
    worker='2256ca596ff4f432e12479e7006c04f0cc21f85999680d0c5b8844931515ae81')
PROFILES = {
    'original-nine': {'inputs': ORIGINAL_INPUTS, 'producer': ORIGINAL_PRODUCER_SHAS,
        'audit': ORIGINAL_AUDIT_SHAS, 'declaration': 'fresh-ground-cluster-context-declaration-v1',
        'producer_plan': 'ROOT-fresh-ground-compact-identity-preparation-plan-v3',
        'producer_receipt': 'fresh-ground-compact-preparation-worker-receipt-v3',
        'producer_evidence': 'fresh-ground-compact-preparation-evidence-v3',
        'audit_plan': 'ROOT-fresh-ground-compact-identity-independent-audit-plan-v3',
        'audit_receipt': 'independent-complete-compact-catalog-static-worker-receipt-v3',
        'audit_evidence': 'independent-complete-compact-catalog-static-evidence-v3'},
    'cohort-four': {'inputs': COHORT_INPUTS, 'producer': PRODUCER_SHAS,
        'audit': AUDIT_SHAS, 'declaration': DECLARATION,
        'producer_plan': 'ROOT-fresh-ground-cohort-compact-preparation-plan-v1',
        'producer_receipt': 'fresh-ground-cohort-compact-preparation-worker-receipt-v1',
        'producer_evidence': 'fresh-ground-cohort-compact-preparation-evidence-v1',
        'audit_plan': 'ROOT-fresh-ground-cohort-compact-independent-audit-plan-v1',
        'audit_receipt': 'independent-complete-cohort-compact-catalog-static-worker-receipt-v1',
        'audit_evidence': 'independent-complete-cohort-compact-catalog-static-evidence-v1'}}

# SOURCE-only exact third profile; no actual acceptance or proof is supplied.
HILBERT_PROFILE = 'hilbert-first-checked-equality-cohort-static-v1'
HILBERT_RECIPIENT_IDS = ('fresh-inc-point-chain-w', 'fresh-inc-reversed-line-chain')
HILBERT_INPUTS = {'fixture': {'bytes': 43532, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/fresh-equality-fixtures-v1.json', 'sha256': 'b60869d015f5f60caa726864595a6293a4566ffdf04403c2499ade76987ef831'}}
HILBERT_SOURCES = {'producer': {'compact_engine': {'bytes': 20787, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/cluster-transfer-compact-engine-source-20261012/compact_point_graph_v1.py', 'sha256': 'd638f7152ec7fa8293adbd8915b79de60f95d0756952bdc6bf0e40b15f549ca0'}, 'compiler': {'bytes': 46112, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/hilbert_fresh_equality_compiler_v1.py', 'sha256': '57653bb27eaf3c4dd1e050c70ac360133f78e1f636cd1276a39a20fd64610a56'}, 'decoder': {'bytes': 14720, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/cluster-transfer-compact-compiler-source-20261012/compact_catalog_decoder_v1.py', 'sha256': '46e3b26a688d64665303238d7d8f3f9b54345cc98e17d903403ca1b62b9b0293'}, 'master': {'bytes': 21657, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md', 'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}, 'point_core': {'bytes': 31300, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py', 'sha256': 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'}, 'worker': {'bytes': 31893, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/hilbert_fresh_equality_prepare_worker_v1.py', 'sha256': 'cc1f05b4b18e4f570b25745a0cf3d3f7c816e4146872f36f8d7a939894acb7e3'}}, 'audit': {'catalog_audit': {'bytes': 15171, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/cluster-transfer-compact-independent-source-20261012/independent_compact_catalog_audit_v1.py', 'sha256': 'db4dc3b904715be3123ed1a9b22eb1ce9144c35aa00c610da94f13263e4334e8'}, 'domains': {'bytes': 7441, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/cluster-transfer-compact-independent-source-20261012/independent_compact_domains_v1.py', 'sha256': '1b9d6b94c78f363ba20f48234dc1eb48ac9dcfa548e8f0fa1a7350699b059b34'}, 'grammar': {'bytes': 14799, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/hilbert_fresh_equality_grammar_v1.py', 'sha256': '34322db5dc25cd3e0cc1dfa43f379f9f45107442c4f035d955b39f1e21b31db1'}, 'logical_oracle': {'bytes': 24588, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-independent-oracles-source-20261013/hilbert_fresh_catalog_oracle_v2.py', 'sha256': '3b6aee8d9b0c1668f2ccf4e0d3b5e7e87dc9e0dd6579e55308e74c3992d6b3cc'}, 'master': {'bytes': 21657, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/docs/basic-tiling-algorithm.md', 'sha256': 'c1327e5ed6e9c6bcb29768d11e21e178bfe2a231464c086cad0c6af7352a1cf9'}, 'worker': {'bytes': 47959, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/hilbert_fresh_equality_audit_worker_v1.py', 'sha256': '7b25d902b69398d5d71c450ee9e63021df6d3b4e967b4c47b7d6e6b563d55fe6'}}}
HILBERT_REVIEWS = {}
HILBERT_UPSTREAM_REVIEWS = {'compiler_person_review': {'bytes': 51269, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-literal-compiler-independent-source-20261013/source-review-v2.json', 'sha256': '0e782dd6207746fa95b5109f32beaf45036b9edfd6be226fa182c1d581598cf8'}, 'oracle_person_review': {'bytes': 33603, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-next-independent-oracles-person-review-20261013/source-review-v1.json', 'sha256': '86091bf909f486ff160fad27606ffd7f8d1945737d63218d3c68ea4986a1f7ee'}}
HILBERT_STATIC_PROFILE_PIN = {'bytes': 5565, 'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/hilbert-fresh-equality-static-source-20261013/static-profile-plan-v1.json', 'sha256': '91ed32762629eb127319d3710b9f7fab8d05a87226b203497d346bb6104cfbc7'}
HILBERT_KERNEL_SHA = '3b6aee8d9b0c1668f2ccf4e0d3b5e7e87dc9e0dd6579e55308e74c3992d6b3cc'
PROFILES[HILBERT_PROFILE] = {
    'inputs': HILBERT_INPUTS,
    'producer': {role: pin['sha256'] for role, pin in HILBERT_SOURCES['producer'].items()},
    'audit': {role: pin['sha256'] for role, pin in HILBERT_SOURCES['audit'].items()},
    'declaration': 'fresh-ground-cluster-context-declaration-v1',
    'producer_plan': 'ROOT-Hilbert-next-compact-preparation-plan-v1',
    'producer_receipt': 'Hilbert-next-compact-preparation-worker-receipt-v1',
    'producer_evidence': 'Hilbert-next-compact-preparation-evidence-v1',
    'audit_plan': 'ROOT-Hilbert-next-compact-independent-audit-plan-v1',
    'audit_receipt': 'Hilbert-next-complete-compact-catalog-static-worker-receipt-v1',
    'audit_evidence': 'Hilbert-next-complete-compact-catalog-static-evidence-v1'}

RESOURCE_PREDICATES = frozenset(('actual_tool_terminal', 'caller_clock_bound',
    'owner_terminal_link_present', 'owner_gate', 'post_write_gate',
    'cancelled_at_final_print_false', 'final_print_gate', 'stage_identity',
    'worker_complete', 'all_worker_direct_children_closed',
    'all_owner_direct_children_closed', 'no_owned_leftovers',
    'complete_post_closure_unchanged', 'post_write_exact_terminal'))


def need(value, label):
    if not value:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def same(a, b, label):
    need(canonical(a) == canonical(b), label)


def exact_int(value, lower=0, upper=None):
    need(type(value) is int and value >= lower and (upper is None or value < upper),
         'literal integer outside exact finite certificate grammar')
    return value


def unique(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, 'duplicate JSON field')
        value[key] = item
    return value


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda token: (_ for _ in ()).throw(ValueError('nonfinite JSON ' + token)))


class ClosedInputs:
    """Raw pin checking only; no imported project's verification authority."""
    def __init__(self):
        self.pins = {}

    def verify(self, pin):
        need(type(pin) is dict and set(pin) == {'path', 'sha256', 'bytes'}
             and type(pin['path']) is str and type(pin['sha256']) is str
             and len(pin['sha256']) == 64 and all(c in '0123456789abcdef' for c in pin['sha256']),
             'exact typed raw input pin')
        exact_int(pin['bytes'])
        declared = Path(pin['path'])
        need(str(declared) == pin['path'] and '..' not in declared.parts,
             'exact safe lexical raw pin spelling')
        # Preserve original REL evidence pins and lexical external runtime pins
        # in ROOT closures. Declared identities are not silently normalized.
        path = declared if declared.is_absolute() else ROOT / declared
        if pin['path'] in self.pins:
            same(pin, self.pins[pin['path']], 'inconsistent repeated raw pin')
        h = hashlib.sha256(); count = 0
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(65536), b''):
                h.update(block); count += len(block)
        need(count == pin['bytes'] and h.hexdigest() == pin['sha256'], 'closed whole raw bytes changed')
        self.pins[pin['path']] = dict(pin)
        return path

    def equivalent(self, a, b, label):
        pa, pb = self.verify(a), self.verify(b)
        need(pa.resolve() == pb.resolve() and a['sha256'] == b['sha256'] and a['bytes'] == b['bytes'], label)

    def absolute(self, pin):
        path = self.verify(pin)
        return dict(pin, path=str(path.resolve()))

    def json(self, pin):
        path = self.verify(pin)
        # Full result read is bounded transport admission, never a prefix or
        # catalog trim. A larger tape requires a future reader, otherwise UNKNOWN.
        with path.open('rb') as stream:
            raw = stream.read(MAX_JSON_BYTES + 1)
            need(len(raw) <= MAX_JSON_BYTES and stream.read(1) == b'', 'whole bounded raw JSON transport')
        need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],
             'parse exactly the same authenticated raw JSON bytes')
        if path.name.endswith('.gz'):
            with gzip.GzipFile(fileobj=io.BytesIO(raw), mode='rb') as stream:
                raw = stream.read(MAX_JSON_BYTES + 1)
                need(len(raw) <= MAX_JSON_BYTES and stream.read(1) == b'', 'whole bounded decoded JSON, no prefix acceptance')
        # Rehash after parsing closes races detectable by the owned file model.
        value = parse(raw); self.verify(pin)
        return value

    def source_map(self, records, expected):
        need(type(records) is dict and set(records) == set(expected), 'exact complete source roles')
        for role, sha in expected.items():
            self.verify(records[role]); need(records[role]['sha256'] == sha, 'exact unchanged source role ' + role)

    def close(self):
        for pin in tuple(self.pins.values()):
            self.verify(pin)



def hilbert_full_pin(closed, pin):
    """Canonicalize safe literal provenance only, retaining full raw identity."""
    path = closed.verify(pin); declared = Path(pin['path'])
    parts = pin['path'].split('/')
    need(not any(part in ('', '.', '..') for part in (parts[1:] if declared.is_absolute() else parts)),
         'safe full provenance pin spelling')
    need(path.resolve() == path and (declared.is_absolute() or ROOT in path.parents),
         'canonical ABS or safe literal ROOT-relative provenance')
    return dict(pin, path=str(path.resolve()))


def hilbert_tree_pins(value):
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is dict:
            if set(item) == {'path', 'sha256', 'bytes'}:
                yield item
            else:
                pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)


def hilbert_closure(closed, plan_pin, plan, binding, roots):
    """Reconcile exact named SOURCE-owned reader roots, never arbitrary ancestors."""
    need(type(binding) is dict and set(binding) == {'schema', 'closure', 'reader_roots',
         'worker_plan_self_exclusion', 'full_path_hash_length_membership',
         'arbitrary_ancestor_JSON_decoding', 'scientific_acceptance'}
         and binding['schema'] == 'complete-Hilbert-next-worker-raw-closure-check-v1'
         and binding['full_path_hash_length_membership'] is True
         and binding['arbitrary_ancestor_JSON_decoding'] is False
         and binding['scientific_acceptance'] is False, 'whole Hilbert raw closure evidence grammar')
    same(binding['closure'], plan['closure'], 'same complete admitted leaf closure')
    closed.equivalent(binding['worker_plan_self_exclusion'], plan_pin, 'one exact worker-plan self exclusion')
    same(binding['reader_roots'], [{'role': role, 'pin': pin} for role, pin, _ in roots],
         'all exact SOURCE-owned named reader roots')
    by_path = {}
    need(type(plan['closure']) is list and plan['closure'], 'nonempty full raw closure')
    for pin in plan['closure']:
        normalized = hilbert_full_pin(closed, pin)
        need(pin == normalized and pin['path'] not in by_path and pin['path'] != plan_pin['path'],
             'canonical ABS unique closure with exact plan self exclusion')
        by_path[pin['path']] = pin
    for role, raw_pin, value in [('worker_plan', plan_pin, plan), *roots]:
        normalized = hilbert_full_pin(closed, raw_pin)
        if role != 'worker_plan':
            same(by_path.get(normalized['path']), normalized, 'entire named raw reader root in closure')
        for pin in hilbert_tree_pins(value):
            normalized = hilbert_full_pin(closed, pin)
            same(by_path.get(normalized['path']), normalized, 'entire named decoded reader-tree pin in closure')


def hilbert_static_metadata(closed, q, pp, ap, pr, ar, pe, ae, header):
    """New profile metadata only; whole existing proof/point checks remain below."""
    need(type(q['instance_id']) is str and q['instance_id'] in HILBERT_RECIPIENT_IDS,
         'exact three fresh Hilbert recipients only')
    same(q['sources'], HILBERT_SOURCES, 'full exact Hilbert producer and independent source records')
    profile = closed.json(HILBERT_STATIC_PROFILE_PIN)
    need(profile['profile_id'] == HILBERT_PROFILE
         and tuple(c['id'] for c in profile['selected_cases']) == HILBERT_RECIPIENT_IDS,
         'exact fresh donor/evaluation static profile')
    reviews = {}
    for which, plan, evidence in (('producer', pp, pe), ('audit', ap, ae)):
        # SOURCE review is a named actual-phase read, anchored by ROOT's q,
        # exact complete admitted phase plan and its full raw closure. No
        # arbitrary ancestor metadata is decoded or standalone review admitted.
        review = closed.json(plan['source_review']); reviews[which] = review
        phase = 'preparation' if which == 'producer' else 'audit'
        need(review['schema'] == 'independent-Hilbert-next-'+phase+'-worker-source-review-v1'
             and review['scope'] == 'Hilbert-next-'+phase+'-worker'
             and review['reviewer_identity'] == '/root'
             and review['author_identity'] == '/root/hilbert_ordering_diagnosis'
             and review['source_review_passed'] is True,
             'current genuine ROOT SOURCE review of exact fresh phase')
        need(review['static_profile_id'] == HILBERT_PROFILE
             and review['static_profile_plan'] == HILBERT_STATIC_PROFILE_PIN
             and evidence['static_profile_id'] == HILBERT_PROFILE
             and evidence['static_profile_plan'] == HILBERT_STATIC_PROFILE_PIN,
             'current actual phase and source review bind the fresh static profile')
        same(review['sources'], HILBERT_SOURCES[which], 'review exact full phase source map')
        same(review['inputs'], HILBERT_INPUTS, 'review exact whole literal fixture')
        same(review['upstream_reviews'], HILBERT_UPSTREAM_REVIEWS, 'exact compiler/oracle SOURCE reviews')
        need(review['author_identity'] != review['reviewer_identity'] and review['source_only'] is True
             and review['source_ready'] is True and review['scientific_calls'] == 0
             and review['scientific_acceptance'] is False, 'SOURCE-only different-person review is no scientific authority')
        closed.equivalent(evidence['source_review'], plan['source_review'], 'evidence same phase SOURCE review')
    dimensions = header['dimensions']
    need(set(dimensions) == {'logical_rows', 'formula_count', 'primitive_license_count',
         'non_assumption_witness_count', 'source_body_count'}
         and all(type(v) is int for v in dimensions.values())
         and dimensions['logical_rows'] == 24 and dimensions['formula_count'] > 0
         and dimensions['primitive_license_count'] >= 3
         and dimensions['non_assumption_witness_count'] == dimensions['primitive_license_count'] - 3
         and dimensions['source_body_count'] == 0, 'complete actual primitive census and empty bootstrap inventory')
    for value in (pr, ar, pe, ae):
        same(value['dimensions'], dimensions, 'every actual full phase census matches')
    need(header['bodies'] == [] and header['complete_cluster_inventory'] == []
         and pe['bodies'] == [] and pe['groups'] == [] and pe['complete_pool_count'] == 0
         and pe['pool_capacity'] == 64 and pe['pool_over_capacity'] == 'reject without trimming'
         and pr['source_body_count'] == ae['source_body_count'] == 0,
         'authenticated complete EMPTY inventory, no donor/library/checkpoint prerequisite')
    same(pe['model_epoch'], pr['model_epoch'], 'same complete static model')
    same(ae['initial_graph_small_state']['model_epoch'], pe['model_epoch'], 'independent complete static model')
    source = HILBERT_SOURCES['audit']['logical_oracle']
    expected_checker = dict(source=source, class_name='GroundChecker',
        module_name='Hilbert_next_independent_five_rule_logical_oracle_v2',
        methods=['__init__', 'term', 'formula', 'command', 'proof'],
        same_authenticated_raw_source_buffer=True,
        five_commands_only=list(RULES), native_accepted=False, proof_accepted=False)
    same(ae['injected_checker_provenance'], expected_checker, 'exact pinned unchanged generic injected checker origin')
    same(ar['injected_checker_provenance'], expected_checker, 'receipt exact same checker provenance')
    upstream = {role: closed.json(pin) for role, pin in HILBERT_UPSTREAM_REVIEWS.items()}
    fixture = closed.json(HILBERT_INPUTS['fixture'])
    prod_roots = [('fixture', HILBERT_INPUTS['fixture'], fixture),
        ('worker_source_review', pp['source_review'], reviews['producer']),
        ('static_profile_plan', HILBERT_STATIC_PROFILE_PIN, profile),
        *[(role, pin, upstream[role]) for role, pin in HILBERT_UPSTREAM_REVIEWS.items()]]
    hilbert_closure(closed, q['producer']['plan'], pp, pe['raw_closure_binding'], prod_roots)
    same(pr['raw_closure_binding'], pe['raw_closure_binding'], 'producer receipt whole same closure')
    decision_pin = q['producer']['ROOT_decision']; decision = closed.json(decision_pin)
    owner_plan = closed.json(decision['plan']); owner = closed.json(decision['owner'])
    ledger_pin = owner['ownership_ledger']; ledger = closed.json(ledger_pin)
    audit_roots = [('worker_source_review', ap['source_review'], reviews['audit']),
        ('static_profile_plan', HILBERT_STATIC_PROFILE_PIN, profile),
        *[(role, pin, upstream[role]) for role, pin in HILBERT_UPSTREAM_REVIEWS.items()],
        ('fixture', HILBERT_INPUTS['fixture'], fixture),
        ('producer_plan', q['producer']['plan'], pp),
        ('producer_source_review', pp['source_review'], reviews['producer']),
        ('producer_receipt', q['producer']['receipt'], pr),
        ('preparation_ROOT_decision', decision_pin, decision),
        ('producer_owner_plan', decision['plan'], owner_plan),
        ('preparation_evidence', q['producer']['evidence'], pe),
        ('catalog_header', q['catalog'], header),
        ('producer_owner_terminal', decision['owner'], owner),
        ('producer_ownership_ledger', ledger_pin, ledger),
        ('producer_diagnostic_raw', pr['producer_diagnostics']['trace'], None)]
    hilbert_closure(closed, q['independent']['plan'], ap, ae['raw_closure_binding'], audit_roots)
    same(ar['raw_closure_binding'], ae['raw_closure_binding'], 'audit receipt whole same closure')


def admitted_context(closed, qualification):
    """Conditional ROOT admission, not a new independent resource decision.

    A future ROOT-owned worker must freeze this strict record AFTER accepted
    complete producer+independent static/resource phases. The exact original
    nine-case profile and new four-case cohort have distinct source/schema
    gates. No record is supplied or fabricated by this source packet. ROOT resource
    statements are authenticated and bound; this helper cannot attest the OS.
    """
    fields = {'schema', 'status', 'declaration_profile', 'instance_id', 'declaration_inputs', 'catalog',
              'producer', 'independent', 'sources', 'expected_consumer_source_binding',
              'all_complete_catalog_licenses_and_initial24domains_accepted'}
    need(type(qualification) is dict and set(qualification) == fields
         and qualification['schema'] == QUALIFICATION
         and qualification['status'] == 'accepted_complete_catalog_and_initial_point_model'
         and qualification['all_complete_catalog_licenses_and_initial24domains_accepted'] is True,
         'trusted ROOT whole exact declared-context qualification required')
    need(qualification['declaration_profile'] in PROFILES, 'only two exact predeclared source profiles')
    profile = PROFILES[qualification['declaration_profile']]; inputs = profile['inputs']
    hilbert = qualification['declaration_profile'] == HILBERT_PROFILE
    if hilbert:
        need(type(qualification['instance_id']) is str and qualification['instance_id'] in HILBERT_RECIPIENT_IDS,
             'only the exact three literal Hilbert recipients')
    same(qualification['declaration_inputs'], inputs, 'exact whole original declaration, not arbitrary theory')
    fixture = closed.json(inputs['fixture'])
    seeds = closed.json(inputs['syntax_seeds']) if 'syntax_seeds' in inputs else None
    need(set(qualification['sources']) == {'producer', 'audit'}, 'both exact source closures')
    closed.source_map(qualification['sources']['producer'], profile['producer'])
    closed.source_map(qualification['sources']['audit'], profile['audit'])
    producer, independent = qualification['producer'], qualification['independent']
    need(type(producer) is dict and set(producer) == {'plan', 'receipt', 'evidence', 'ROOT_decision'}
         and type(independent) is dict and set(independent) == {'plan', 'receipt', 'evidence', 'licenses', 'ROOT_decision'},
         'complete producer and independent artifact roles')
    pp, pr, pe = [closed.json(producer[k]) for k in ('plan', 'receipt', 'evidence')]
    ap, ar, ae = [closed.json(independent[k]) for k in ('plan', 'receipt', 'evidence')]
    header = closed.json(qualification['catalog'])
    for record, stage, receipt_pin in ((producer, 'preparation', producer['receipt']),
                                       (independent, 'replay', independent['receipt'])):
        decision = closed.json(record['ROOT_decision'])
        need(decision['schema'] == 'ROOT-fresh-catalog-stage-final-decision-v1'
             and decision['stage'] == stage and decision['ROOT_final_accepted'] is True
             and decision['status'] == 'accepted_complete_owned_stage'
             and type(decision['predicates']) is dict and set(decision['predicates']) == RESOURCE_PREDICATES
             and all(v is True for v in decision['predicates'].values())
             and decision['mismatches'] == [] and decision['native_accepted'] is False
             and decision['all_five_qualification'] is False, 'complete trusted ROOT14 static resource prerequisite')
        closed.equivalent(decision['worker'], receipt_pin, 'ROOT decision exact completed worker')
        same(decision['limits'], {'whole_seconds': 60, 'peak_bytes': 536870912, 'caller_seconds': 90},
             'unchanged declared static/resource/caller envelope')
        for field in ('plan', 'actual_tool', 'owner', 'post_write'):
            closed.verify(decision[field])
        owner_plan = closed.json(decision['plan'])
        declared_receipt = Path(owner_plan['worker_receipt'])
        owner_receipt_path = declared_receipt if declared_receipt.is_absolute() else ROOT / declared_receipt
        need(owner_plan['stage'] == stage and owner_receipt_path.resolve() == closed.verify(receipt_pin).resolve(),
             'ROOT admitted exact owner worker scope')
        for pin in owner_plan['closure']:
            closed.verify(pin)
    instance = qualification['instance_id']
    plan_fields = {'schema', 'selector', 'output_directory', 'inputs', 'sources', 'source_review', 'limits', 'ROOT_owned_once_only'}
    if hilbert:
        plan_fields = plan_fields | {'closure'}
    need(type(pp) is dict and set(pp) == plan_fields and type(ap) is dict and set(ap) == plan_fields
         and pp['schema'] == profile['producer_plan']
         and ap['schema'] == profile['audit_plan']
         and pp['selector'] == ap['selector'] == instance
         and pp['ROOT_owned_once_only'] is True and ap['ROOT_owned_once_only'] is True,
         'fresh strict cohort source plans, no old static receipt reuse')
    for plan in (pp, ap):
        same(plan['limits'], {'whole_seconds': 60, 'peak_bytes': 536870912}, 'exact original worker envelope')
    same(pp['inputs'], inputs, 'producer exact raw declaration inputs')
    same(pp['sources'], qualification['sources']['producer'], 'producer exact source map')
    same(ap['sources'], qualification['sources']['audit'], 'independent exact source map')
    for plan, which in ((pp, 'producer'), (ap, 'audit')):
        review = closed.json(plan['source_review'])
        need(review['source_only'] is True and review['source_ready'] is True
             and review['scientific_acceptance'] is False, 'separately reviewed source readiness prerequisite')
        same(review['sources'], qualification['sources'][which], 'exact reviewed source closure')
        same(review['inputs'], inputs, 'exact reviewed raw declarations')
    expected_inputs = dict(inputs, producer_plan=producer['plan'], producer_receipt=producer['receipt'],
        preparation_evidence=producer['evidence'], catalog=qualification['catalog'],
        preparation_ROOT_decision=producer['ROOT_decision'], producer_diagnostics=pr['producer_diagnostics']['trace'])
    need(set(ap['inputs']) == set(expected_inputs), 'audit all exact accepted producer input roles')
    for name, pin in expected_inputs.items():
        closed.equivalent(ap['inputs'][name], pin, 'audit exact accepted producer input ' + name)
    for pin in expected_inputs.values():
        closed.verify(pin)
    need(pr['schema'] == profile['producer_receipt']
         and pr['stage_completed'] is True and pr['stage'] == 'preparation'
         and pr['status'] == 'complete_pending_independent_and_ROOT_resource_gates'
         and ar['schema'] == profile['audit_receipt']
         and ar['stage_completed'] is True and ar['stage'] == 'replay'
         and ar['status'] == 'complete_catalog_static_semantic_audit_pending_ROOT_resources'
         and ar['logical_accepted'] is True and ar['initial_static_point_accepted'] is True,
         'complete cohort producer and independently accepted whole static audit')
    for receipt, record in ((pr, producer), (ar, independent)):
        closed.equivalent(receipt['plan'], record['plan'], 'receipt exact phase plan')
        closed.equivalent(receipt['full_result'], record['evidence'], 'receipt exact whole evidence')
        need(receipt['selector'] == instance and receipt['direct_children_peak_sum_bytes'] == 0
             and receipt['all_direct_children_terminal_and_reaped'] is True, 'complete exact child stage')
    need(pe['schema'] == profile['producer_evidence']
         and pe['status'] == 'complete_compact_catalog_and_initial_graph_pending_independent_gate'
         and ae['schema'] == profile['audit_evidence']
         and ae['status'] == 'accepted_complete_semantics_pending_ROOT_resources'
         and ae['logical_accepted'] is True and ae['initial_static_point_accepted'] is True
         and all(ae[k] is True for k in ('all_formulas_checked', 'all_licenses_checked', 'all_DAG_nodes_checked',
                  'original_canonical_order_and_preimages_checked', 'all_three_ordered_seed_identities_checked')),
         'full independent licensing/registry/boundary authority, not selected-only census')
    for evidence, plan, record in ((pe, pp, producer), (ae, ap, independent)):
        closed.equivalent(evidence['plan'], record['plan'], 'evidence exact plan')
        same(evidence['sources'], plan['sources'], 'evidence exact complete sources')
        same(evidence['inputs'], plan['inputs'], 'evidence exact complete raw inputs')
        closed.equivalent(evidence['catalog'], qualification['catalog'], 'evidence exact catalog header')
        same(evidence['catalog_streams'], header['streams'], 'evidence exact full binary streams')
        same(evidence['dimensions'], header['dimensions'], 'complete admitted census')
        need(evidence['instance_id'] == instance and evidence['target_searches'] == 0
             and evidence['point_certificates'] == 0 and evidence['RNG_draws'] == 0
             and evidence['new_RL_training'] is False, 'static qualification cannot claim a discovered proof')
    same(pe['catalog_header'], header, 'raw whole header versus producer evidence')
    closed.equivalent(ae['complete_licenses'], independent['licenses'], 'exact whole independent license stream')
    closed.equivalent(ar['complete_licenses'], independent['licenses'], 'receipt entire license stream')
    same(ar['primitive_license_checks'], header['dimensions']['primitive_license_count'], 'all primitive licenses checked')
    same(ae['primitive_license_checks'], ar['primitive_license_checks'], 'complete license count')
    need(ae['point_audit']['rows'] == 24 and ae['point_audit']['all_required_rows_checked'] is True
         and len(ae['point_audit']['complete_point_factor_streams']) == 24,
         'whole independently admitted initial24-point streams')
    if hilbert:
        hilbert_static_metadata(closed, qualification, pp, ap, pr, ar, pe, ae, header)
    cases = [c for c in fixture['cases'] if c['id'] == instance]
    need(len(cases) == 1, 'one exact original statement')
    case = cases[0]; theory = fixture['theories'][case['theory']]
    gamma = [fixture['literal_formulas'][name] for name in case['hypotheses']]
    target = fixture['literal_formulas'][case['target']]
    need(case['rows'] == 24 and len(gamma) == 3, 'full24 rows and three ordered hypothesis occurrences')
    selected = dict(instance_id=instance, split=case['split'], theory_key=case['theory'],
        theory=theory, ordered_hypotheses=gamma, target=target, rows=24, structural_tag=case['structural_tag'])
    grammar = fixture['finite_grammars'][case['theory']]
    need(grammar['instantiation_rounds'] == 4 and grammar['equality_layers'] == 1,
         'entire original fixed four-round and one-equality-layer declaration')
    declaration_binding = dict(fixture_sha256=digest(fixture), selected_sha256=digest(selected),
        grammar_sha256=digest(grammar), theory_key=case['theory'])
    same(header['context'], {'theory': theory, 'ordered_local_premises': gamma}, 'unchanged theory and exact Gamma')
    same(header['target'], target, 'unchanged theorem conclusion')
    need(header['schema'] == 'fresh-ground-compact-catalog-v1' and header['declaration_schema'] == profile['declaration']
         and header['height'] == 24 and header['instance_id'] == instance and header['orientation'] == 'identity'
         and header['marking_version'] == MARKING, 'strict cohort translation-only point model')
    bindings = [closed.absolute(producer['plan']), *pp['inputs'].values(), *pp['sources'].values(), pp['source_review']]
    same(header['source_bindings'], bindings, 'full actual producer closure, no audit-source epoch substitution')
    authority = header['authority']
    if seeds is not None:
        syntax_binding = {'schema': 'theory-scoped-ground-cohort-syntax-binding-v1', 'inputs': inputs,
            'fixture_semantic_sha256': digest(fixture), 'syntax_seed_metadata_semantic_sha256': digest(seeds),
            'extra_closed_terms_by_theory': {'pa-ground': [], 'hilbert-incidence': [['fun', 'D', []]]},
            'theory_sha256_by_key': {k: digest(v) for k, v in fixture['theories'].items()}}
        same(authority['syntax_seed_binding'], syntax_binding, 'exact authenticated nonlogical syntax authority')
        declaration_binding['syntax_seed_binding_sha256'] = digest(syntax_binding)
    else:
        need('syntax_seed_binding' not in authority, 'original nine source authority cannot inherit cohort seeds')
    need(authority['activated'] is False and authority['native_accepted'] is False
         and authority['declaration_schema'] == profile['declaration']
         and authority['recipient_theory_sha256'] == digest(theory)
         and authority['finite_grammar_sha256'] == digest(grammar)
         and authority['epoch'] == digest({k: v for k, v in authority.items() if k != 'epoch'}),
         'exact original inactive theory authority epoch')
    need(header['context_id'] == digest(header['context']), 'exact original sequent context identity')
    same(authority['source_bindings'], bindings, 'same complete producer epoch inputs')
    same(header['declaration_binding'], declaration_binding, 'full exact original declaration binding')
    same(ae['declaration_binding'], declaration_binding, 'full independent declaration binding')
    same(ae['context_id'], header['context_id'], 'independent exact context')
    same(ae['authority_epoch'], authority['epoch'], 'independent exact authority')
    same(ae['formula_registry_sha256'], header['formula_registry_sha256'], 'independent exact registry')
    for pin in header['streams'].values():
        closed.verify(pin)
    closed.verify(independent['licenses'])
    return header, gamma, target, theory, independent['licenses'], ae


class SelectedWire:
    """Independent selected-record reader, never calls producer decoder APIs.

    Whole stream byte/hash/census semantics come from the bound complete static
    audit. All selected record fields, preimages and logical commands are checked
    afresh here. Memory holds the compact DAG and only selected expanded ASTs.
    """
    def __init__(self, header):
        self.header = header; self.nodes = []; self.expanded = {}
        codec = header['codec']; self.names = codec['names']
        need(codec['recipe_row_bytes'] == ROW.size and codec['formula_word_bytes'] == WORD.size
             and codec['byte_order'] == 'little' and codec['sentinel'] == SENTINEL
             and codec['rules'] == list(RULES), 'exact reversible wire codec')
        with gzip.open(header['streams']['nodes']['path'], 'rb') as stream:
            for line in stream:
                value = parse(line)
                need(type(value) is list and len(value) >= 2 and type(value[0]) is int
                     and value[0] == len(self.nodes), 'contiguous full DAG node stream')
                same(line.decode('utf8'), canonical(value) + '\n', 'canonical complete DAG line')
                self.nodes.append(value[1:])
        need(len(self.nodes) == codec['node_count'], 'complete admitted DAG census')
        dims = header['dimensions']; self.count = exact_int(dims['primitive_license_count'], 3)
        self.formula_count = exact_int(dims['formula_count'], 1)
        need(header['streams']['recipes']['bytes'] == self.count * ROW.size
             and header['streams']['formulas']['bytes'] == self.formula_count * WORD.size,
             'whole fixed-length stream, no unread tail')

    def expand(self, node):
        exact_int(node, 0, len(self.nodes))
        if node in self.expanded:
            return self.expanded[node]
        rec = self.nodes[node]; tag = rec[0]
        def child(index):
            exact_int(index, 0, node)
            return self.expand(index)
        if tag == 'bot' and len(rec) == 1:
            value = ['bot']
        elif tag == 'var' and len(rec) == 2 and type(rec[1]) is str:
            value = list(rec)
        elif tag in ('fun', 'pred') and len(rec) == 3 and type(rec[1]) is str and type(rec[2]) is list:
            value = [tag, rec[1], [child(x) for x in rec[2]]]
        elif tag == 'all' and len(rec) == 3 and type(rec[1]) is str:
            value = [tag, rec[1], child(rec[2])]
        elif (tag in ('eq', 'imp', 'and', 'or') and len(rec) == 3) or (tag == 'not' and len(rec) == 2):
            value = [tag, *[child(x) for x in rec[1:]]]
        else:
            raise ValueError('selected AST constructor outside original codec')
        self.expanded[node] = value
        return value

    def formula_node(self, code):
        exact_int(code, 0, self.formula_count)
        with open(self.header['streams']['formulas']['path'], 'rb') as stream:
            stream.seek(code * WORD.size); raw = stream.read(WORD.size)
        need(len(raw) == WORD.size, 'complete selected formula word')
        return WORD.unpack(raw)[0]

    def formula(self, code):
        return self.expand(self.formula_node(code))

    def recipe(self, index):
        exact_int(index, 0, self.count)
        with open(self.header['streams']['recipes']['path'], 'rb') as stream:
            stream.seek(index * ROW.size); raw = stream.read(ROW.size)
        need(len(raw) == ROW.size, 'complete selected recipe row')
        r = ROW.unpack(raw); tag, node, code, i0, i1, p0, p1, p2, p3, n, occurrence = r[:11]
        exact_int(tag, 0, len(RULES)); rule = RULES[tag]
        need(self.formula_node(code) == node, 'selected output formula-node relation')
        witness = {'rule': rule, 'formula': self.expand(node)}
        ports = [i0, i1] if rule == 'mp' else []
        if rule == 'mp':
            need(all(x == SENTINEL for x in (p0, p1, p2, p3, n, occurrence)), 'exact MP selected row grammar')
        else:
            need(i0 == i1 == SENTINEL, 'zero-port rule has no hidden premise')
            if rule == 'axiom':
                exact_int(n, 0, len(self.names)); witness['name'] = self.names[n]
                need(all(x == SENTINEL for x in (p0, p1, p2, p3, occurrence)), 'exact axiom selected row grammar')
            elif rule == 'instantiate':
                witness.update(universal=self.expand(p0), term=self.expand(p1))
                need(all(x == SENTINEL for x in (p2, p3, n, occurrence)), 'exact instantiation row grammar')
            elif rule == 'eq_subst':
                exact_int(n, 0, len(self.names))
                witness.update(variable=self.names[n], template=self.expand(p0), left=self.expand(p1), right=self.expand(p2))
                need(p3 == occurrence == SENTINEL, 'exact equality substitution row grammar')
            else:
                exact_int(occurrence, 0, 3); witness['index'] = occurrence
                need(all(x == SENTINEL for x in (p0, p1, p2, p3, n)), 'exact occurrence-specific assumption row grammar')
        premises = [self.formula(x) for x in ports]
        if ports:
            same(premises[1], ['imp', premises[0], witness['formula']], 'exact ordered licensed MP interface')
        authority = self.header['authority']
        preimage = {'recipe': {'primitive_witness': witness, 'ordered_premise_formulas': premises},
            'primitive_authority_epoch': authority['epoch'], 'recipient_theory_sha256': authority['recipient_theory_sha256'],
            'marking_version': MARKING, 'formula_registry_sha256': self.header['formula_registry_sha256']}
        if rule == 'assumption':
            preimage['local_context_id'] = self.header['context_id']
        identifier = 'primitive-recipe-' + digest(preimage)
        need(bytes.fromhex(identifier[len('primitive-recipe-'):]) == r[11], 'selected recipe ID full canonical preimage')
        record = {'id': identifier, 'primitive_witness': witness, 'ordered_premise_formulas': premises, 'identity_preimage': preimage}
        need(bytes.fromhex(digest(record)) == r[12], 'selected complete legacy record digest')
        return {'index': index, 'id': identifier, 'witness': witness, 'premises': premises,
                'output': code, 'inputs': ports, 'record_sha256': r[12].hex(), 'rule': rule}

    def model_epoch(self):
        h = self.header; fixed = h['boundary']['fixed_exterior_m'] + h['boundary']['fixed_target_m']
        payload = {'height': 24, 'context': h['context'], 'registry': h['formula_registry_sha256'],
            'authority': h['authority']['epoch'], 'recipes': None, 'fixed_marks': sorted(fixed),
            'roots': [0] * 24, 'seed_keys': [[i, row, []] for row, i in enumerate(h['assumption_recipe_indices'])],
            'marking_version': MARKING, 'fixture': False, 'source_bindings': h['source_bindings']}
        hasher = hashlib.sha256(); hasher.update(b'{')
        for j, name in enumerate(sorted(payload)):
            if j:
                hasher.update(b',')
            hasher.update(canonical(name).encode()); hasher.update(b':')
            if name == 'recipes':
                hasher.update(b'[')
                with open(h['streams']['recipes']['path'], 'rb') as stream:
                    for i in range(self.count):
                        raw = stream.read(ROW.size); need(len(raw) == ROW.size, 'whole model recipe-ID stream')
                        if i:
                            hasher.update(b',')
                        identifier = 'primitive-recipe-' + ROW.unpack(raw)[11].hex()
                        hasher.update(canonical(identifier).encode())
                    need(stream.read(1) == b'', 'model hash no unread recipe tail')
                hasher.update(b']')
            else:
                hasher.update(canonical(payload[name]).encode())
        hasher.update(b'}'); return hasher.hexdigest()


def licenses(closed, pin, wire, selected):
    """Authenticate every saved license line; recheck selected wire records.

    No license is regenerated here and no subset is called a complete catalog.
    The bound independent whole static auditor is the full licensing authority.
    """
    closed.verify(pin); matched = set(); count = 0
    with gzip.open(pin['path'], 'rb') as stream:
        for line in stream:
            value = parse(line)
            need(type(value) is dict and set(value) == {'recipe_index', 'recipe_id', 'rule', 'record_sha256',
                'logical_accepted', 'native_accepted', 'status'} and value['recipe_index'] == count
                and type(value['recipe_index']) is int and value['rule'] in RULES
                and value['logical_accepted'] is True and value['native_accepted'] is False
                and value['status'] == 'accepted_independent_exact_primitive_license', 'every complete admitted license line')
            same(line.decode(), canonical(value) + '\n', 'canonical entire license line')
            if count in selected:
                recipe = selected[count]
                same([value['recipe_id'], value['rule'], value['record_sha256']],
                     [recipe['id'], recipe['rule'], recipe['record_sha256']], 'selected record matches whole independent license')
                matched.add(count)
            count += 1
    need(count == wire.count and matched == set(selected), 'whole license count and every selected record licensed')


def placement(recipe, row, refs, header):
    need(type(refs) is list and len(refs) == len(recipe['inputs']), 'exact ordered input arity')
    for ref in refs:
        exact_int(ref, 0, row)
    marks = {(1, row): recipe['output']}
    for port, (ref, code) in enumerate(zip(refs, recipe['inputs'])):
        point = (1, ref)
        need(point not in marks or marks[point] == code, 'aliased ordered refs have compatible formula codes')
        marks[point] = code; marks[(2 + port, row)] = ref - row
    t = [[0, row, 1]]; m = [[x, y, v] for (x, y), v in sorted(marks.items())]
    command = dict(recipe['witness'])
    if recipe['rule'] == 'mp':
        command.update(antecedent=refs[0], implication=refs[1])
    prototype = {'recipe_id': recipe['id'], 'primitive_witness': recipe['witness'],
        'ordered_premise_formulas': recipe['premises'], 'relative_ordered_input_offsets': [ref - row for ref in refs],
        'orientation': 'identity', 't': [[0, 0, 1]], 'm': [[x, y - row, v] for x, y, v in m],
        'marking_version': MARKING, 'formula_registry_sha256': header['formula_registry_sha256'],
        'authority_epoch': header['authority']['epoch']}
    preimage = {'prototype_id': 'primitive-prototype-' + digest(prototype), 'prototype_preimage': prototype,
        'transform': [0, row], 'context_id': header['context_id'], 'ordered_input_rows': refs,
        'primitive_command': command, 't': t, 'm': m, 'authority_epoch': header['authority']['epoch'],
        'formula_registry_sha256': header['formula_registry_sha256']}
    return {'id': 'aggregate-primitive-' + digest(preimage), 'identity_preimage': preimage,
            'key': [recipe['index'], row, refs], 'command': command, 't': t, 'm': m}


def escaped(name):
    table = {'\\': r'\backslash{}', '{': r'\{', '}': r'\}', '_': r'\_', '%': r'\%',
             '&': r'\&', '#': r'\#', '$': r'\$', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}'}
    return ''.join(table.get(c, c) for c in name)


def latex(value):
    """Display only, no logical authority and no invented abbreviations."""
    tag = value[0]
    if tag == 'var':
        return r'\mathit{' + escaped(value[1]) + '}'
    if tag == 'bot':
        return r'\bot'
    if tag in ('fun', 'pred'):
        name, args = value[1], value[2]
        if tag == 'fun' and name == 'zero' and not args:
            return '0'
        if tag == 'fun' and name == 'succ' and len(args) == 1:
            return 'S(' + latex(args[0]) + ')'
        if tag == 'fun' and name == 'add' and len(args) == 2:
            return '(' + latex(args[0]) + '+' + latex(args[1]) + ')'
        if tag == 'fun' and name == 'mul' and len(args) == 2:
            return '(' + latex(args[0]) + r'\cdot ' + latex(args[1]) + ')'
        head = (r'\mathrm{' if tag == 'fun' else r'\operatorname{') + escaped(name) + '}'
        return head + ('(' + ','.join(latex(a) for a in args) + ')' if args else '')
    if tag == 'all':
        return r'\forall ' + latex(['var', value[1]]) + r'\,(' + latex(value[2]) + ')'
    if tag == 'not':
        return r'\neg(' + latex(value[1]) + ')'
    operators = {'eq': '=', 'imp': r'\to ', 'and': r'\land ', 'or': r'\lor '}
    return '(' + latex(value[1]) + operators[tag] + latex(value[2]) + ')'


def english(value):
    """Literal compositional paraphrase; Point/Line facts are never inferred."""
    tag = value[0]
    if tag == 'eq':
        return '\\(' + latex(value[1]) + '\\) equals \\(' + latex(value[2]) + '\\)'
    if tag == 'pred':
        name, args = value[1], value[2]
        if name == 'Incident' and len(args) == 2:
            return '\\(' + latex(args[0]) + '\\) is incident with \\(' + latex(args[1]) + '\\)'
        if name in ('Point', 'Line') and len(args) == 1:
            return '\\(' + latex(args[0]) + '\\) is a ' + name.lower()
        return 'the predicate \\(' + latex(value) + '\\) holds'
    if tag == 'bot':
        return 'a contradiction holds'
    if tag == 'all':
        return 'for every \\(' + latex(['var', value[1]]) + '\\), (' + english(value[2]) + ')'
    if tag == 'not':
        return 'it is not the case that (' + english(value[1]) + ')'
    if tag == 'imp':
        return 'if (' + english(value[1]) + '), then (' + english(value[2]) + ')'
    return '(' + english(value[1]) + ') ' + {'and': 'and', 'or': 'or'}[tag] + ' (' + english(value[2]) + ')'


def reason(command):
    rule = command['rule']
    if rule == 'assumption':
        return 'This is hypothesis occurrence \\(' + str(command['index'] + 1) + '\\).'
    if rule == 'axiom':
        return 'This is the named axiom \\(\\mathrm{' + escaped(command['name']) + '}\\).'
    if rule == 'instantiate':
        return 'Universal instantiation supplies this implication, using the closed term \\(' + latex(command['term']) + '\\).'
    if rule == 'eq_subst':
        return 'Equality substitution supplies this implication for the displayed atomic template.'
    return 'Apply modus ponens to row \\(' + str(command['antecedent'] + 1) + '\\) and the implication in row \\(' + str(command['implication'] + 1) + '\\).'


def verify_saved_certificate(*, result_pin, qualification_pin, checker_class, expected_mode):
    """Future ROOT-only conditional API. No file or acceptance record is written.

    The ROOT-owned worker must first independently review/qualify its exact
    runtime+source objects and full input/output/resource scope. It injects the
    unchanged pinned GroundChecker; only this future invocation calls that
    logical kernel. This packet author never imports or invokes it.
    """
    closed = ClosedInputs(); qualification = closed.json(qualification_pin)
    header, gamma, target, theory, license_pin, static = admitted_context(closed, qualification)
    kernel_pin = qualification['sources']['audit']['logical_oracle']
    expected_kernel = HILBERT_KERNEL_SHA if qualification['declaration_profile'] == HILBERT_PROFILE else KERNEL_SHA
    need(kernel_pin['sha256'] == expected_kernel and isinstance(checker_class, type)
         and checker_class.__name__ == 'GroundChecker', 'unchanged generic logical kernel required')
    for method in ('__init__', 'command', 'proof', 'formula', 'term'):
        need(str(Path(getattr(checker_class, method).__code__.co_filename).resolve()) == kernel_pin['path'],
             'injected logical object must originate in exact pinned source')
    need(qualification['declaration_profile'] == HILBERT_PROFILE
         and expected_mode in ('base','seed_forward'), 'only the declared primitive advice pair')
    result = closed.json(result_pin)
    need(result['mode'] == expected_mode and result['seed'] is None
         and result['rng_draws'] == [] and result['policy_choices'] == []
         and result['commits'] == [] and result['training_updates'] == 0
         and result['all_source_body_count'] == 0
         and result['registered_whole_descriptor_count'] == 0,
         'actual expected deterministic lane, empty inventory and no RNG/learning')
    advice = result['candidate_advice']
    if expected_mode == 'seed_forward':
        same(advice['source_binding'], ADVICE_SOURCE, 'exact reviewed generic advice source')
        closed.verify(ADVICE_SOURCE)
        need(advice['mode'] == expected_mode and advice['construction']['completed'] is True
             and all(record['completed'] is True for record in advice['observations']),
             'no partial candidate advice construction/selection accepted')
    else:
        need(advice['mode'] is None and advice['source_binding'] is None
             and advice['construction'] is None and advice['observations'] == [],
             'canonical pair lane has no advice')
    need(result['schema'] == DFS and result['status'] == 'finite_exact_point_tiling'
         and result['trace_complete'] is True and type(result['point_certificate']) is dict,
         'complete positive compact result, no UNKNOWN/prefix salvage')
    consumer = result['consumer_source_binding']
    same(consumer, qualification['expected_consumer_source_binding'], 'ROOT expected exact search consumer sources')
    need(result['consumer_source_binding_sha256'] == digest(consumer), 'complete consumer binding identity')
    source_records = consumer['source_records']
    seen = set()
    for record in source_records:
        need(type(record) is dict and set(record) == {'role', 'path', 'sha256', 'bytes'}
             and record['role'] not in seen, 'exact unique consumer role pin')
        seen.add(record['role']); pin = {k: record[k] for k in ('path', 'sha256', 'bytes')}
        closed.verify(pin)
        if record['role'] == 'streamed_dfs':
            need(pin['sha256'] == DFS_SHA, 'exact separately bound pair DFS result wire authority')
    need('streamed_dfs' in seen, 'exact DFS source record')
    for field in ('ROOT_source_review_pin', 'independent_source_review_pin'):
        closed.verify(consumer[field])
    certificate = result['point_certificate']
    need(set(certificate) == {'status', 'model_epoch', 'source_bindings', 'placements',
             'native_accepted', 'native_authority_activated', 'compiler_correspondence'}
         and certificate['status'] == 'finite_exact_point_tiling_pending_independent_logical_certificate'
         and certificate['native_accepted'] is False and certificate['native_authority_activated'] is False
         and certificate['compiler_correspondence'] == 'open', 'exact pending primitive certificate grammar')
    same(certificate['source_bindings'], header['source_bindings'], 'certificate complete original producer source epoch')
    wire = SelectedWire(header); epoch = wire.model_epoch()
    need(certificate['model_epoch'] == result['model_epoch'] == static['initial_graph_small_state']['model_epoch'] == epoch,
         'full catalog/boundary/context/model epoch, not selected-only identity')
    boundary = header['boundary']
    same(boundary['required'], [[0, r] for r in range(24)], 'all24 unit occupancy obligations')
    same(boundary['root_generations'], [[0, r, 0] for r in range(24)], 'original24 root generations')
    need(boundary['all_root_obligations_generation_zero'] is True, 'all24 explicit root0 obligations')
    same(boundary['fixed_exterior_m'], [[1, r, -1] for r in range(-23, 0)], 'entire exterior marking support')
    same(boundary['fixed_target_m'], [[1, 23, header['target_code']]], 'unchanged target formula mark')
    same(wire.formula(header['target_code']), target, 'target exact injective formula code')
    same([wire.formula(c) for c in header['hypothesis_codes']], gamma, 'three original hypothesis codes')
    need(type(header['assumption_recipe_indices']) is list and len(header['assumption_recipe_indices']) == 3,
         'three distinct occurrence-specific assumption licenses')
    same(boundary['fixed_initial_local_seeds'], [{'recipe_id': wire.recipe(index)['id'], 'row': row, 'generation': 0}
         for row, index in enumerate(header['assumption_recipe_indices'])], 'whole exact fixed physical seed identities')
    items = certificate['placements']
    need(type(items) is list and len(items) == 24, 'exactly one distinct primitive per24 rows')
    recipes = {}; commands = []; expected_placements = []; totals = {}; marks = {}; refs_count = {}
    def assign(x, y, value):
        point = (x, y)
        need(point not in marks or marks[point] == value, 'whole remote marking union conflicts')
        marks[point] = value; refs_count[point] = refs_count.get(point, 0) + 1
    for x, y, value in boundary['fixed_exterior_m'] + boundary['fixed_target_m']:
        assign(x, y, value)
    for row, supplied in enumerate(items):
        key = supplied['key']
        need(type(key) is list and len(key) == 3 and type(key[1]) is int and key[1] == row,
             'canonical complete row ordering and exact key grammar')
        recipe = wire.recipe(key[0]); recipes[key[0]] = recipe
        expected = placement(recipe, row, key[2], header)
        same(supplied, expected, 'full independently reconstructed primitive/prototype/placement identity')
        if row < 3:
            need(key == [header['assumption_recipe_indices'][row], row, []]
                 and recipe['rule'] == 'assumption' and recipe['witness']['index'] == row,
                 'fixed separately indexed original Gamma occurrence seed')
        command = expected['command']; commands.append(command); expected_placements.append(expected)
        for x, y, value in expected['t']:
            totals[(x, y)] = totals.get((x, y), 0) + value
        for x, y, value in expected['m']:
            assign(x, y, value)
    need(totals == {(0, r): 1 for r in range(24)}, 'whole t=1 positive support and no extra support')
    need(len({p['id'] for p in expected_placements}) == 24, 'distinct physical placement identities')
    licenses(closed, license_pin, wire, recipes)
    checker = checker_class(theory)
    logical = checker.proof(commands, gamma, target)
    need(logical['original_ground_sequent_accepted'] is True and logical['rows'] == 24
         and logical['native_accepted'] is False, 'all original five primitive rules and final target accepted')
    terminal = result['terminal_state']; graph_sha = terminal['overlay']['controller']['graph_state_sha256']
    graph = result['graph_states'][graph_sha]
    need(digest(graph) == graph_sha and graph['schema'] == 'compact-complete-dynamic-point-state-v2'
         and graph['model_epoch'] == epoch, 'exact terminal graph-state content identity')
    same(graph['totals'], [1] * 24, 'terminal entire required occupancy')
    same(graph['marks'], [[x, y, value, refs_count[(x, y)]] for (x, y), value in sorted(marks.items())],
         'terminal whole remote mark union including exact fixed and placement reference counts')
    keys = [p['key'] for p in expected_placements]
    need(type(graph['order']) is list and len(graph['order']) == 24
         and len({canonical(k) for k in graph['order']}) == 24
         and {canonical(k) for k in graph['order']} == {canonical(k) for k in keys}, 'terminal selected set exactly certificate')
    same(graph['order'][:3], keys[:3], 'fixed seed initialization order')
    same(graph['roots'], [0] * 24, 'all original explicit root generations')
    same(graph['selected_generations'], sorted([[k, 0 if k[1] < 3 else 1] for k in keys]),
         'terminal generation values for this all-root0 unit-support specialization')
    rows = [{'row': row, 'display_row': row + 1, 'placement_id': p['id'], 'recipe_id': recipes[p['key'][0]]['id'],
             'key': p['key'], 'command': p['command'], 'formula': p['command']['formula'],
             'formula_latex': latex(p['command']['formula']), 'formula_english': english(p['command']['formula']),
             'derivation_english': reason(p['command']), 'ordered_prior_rows': p['key'][2],
             't': p['t'], 'm': p['m'], 'marking_version': MARKING,
             'display_is_acceptance_authority': False}
            for row, p in enumerate(expected_placements)]
    closed.close()
    return {'schema': VERSION, 'status': 'accepted_independent_final_primitive_certificate',
        'qualification_pin': qualification_pin, 'result_pin': result_pin, 'instance_id': header['instance_id'],
        'expected_mode': expected_mode, 'actual_mode': result['mode'], 'DFS_source_sha256': DFS_SHA,
        'context_id': header['context_id'], 'model_epoch': epoch, 'authority_epoch': header['authority']['epoch'],
        'formula_registry_sha256': header['formula_registry_sha256'], 'point_certificate_sha256': digest(certificate),
        'commands_sha256': digest(commands), 'ordered_hypotheses': gamma, 'target': target, 'rows': rows,
        'complete_required_rows': 24, 'selected_primitive_placements': 24, 'original_ground_sequent_accepted': True,
        'whole_t_and_remote_m_accepted': True, 'all_selected_placement_identities_checked': True,
        'all_selected_recipes_independently_symbolically_checked': True, 'native_accepted': False,
        'search_trajectory_accepted': False, 'RNG_credit_update_accepted': False,
        'resource_acceptance_issued': False, 'same_inventory_performance_claim': False, 'RL_advantage_claim': False,
        'raw_closed_input_pins': list(closed.pins.values()),
        'scope': 'Final24-row ground sequent and exact translated point tiling only. Complete static catalog/license '
            'and trusted ROOT resource prerequisites are bound, not re-issued. No new proof discovery is performed. '
            'Full scheduler/rollback/exclusion/order/RNG/commit/reward/learning trajectory and fair cold controls remain separate.'}
