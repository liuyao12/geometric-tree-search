"""SOURCE ONLY: immutable input/receipt binding for a future proof control.

No dispatch, scientific import, model construction or execution on import.
ROOT must freeze the missing process-local-clock chain and actual per-phase
input/activation contracts separately. These functions have not been called.
Hash/JSON checks here never decide mathematical legality or resource sufficiency.
"""
import copy
import gzip
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


VERSION = 'one-context-two-lane-proof-control-v1'
FUTURE_SELECTORS = ('donor-repeated-guard', 'donor-repeated-equality',
                    'heldout-mixed-guard-equality')
MODES = ('base', 'fixed-whole-family-pool')
LIMITS = {'attempts': 128, 'seconds': 20, 'event_ceiling': 2000}
OWNED_LIMITS = {'whole_seconds': 180, 'supervisor_seconds': 175,
                'child_seconds': 170, 'peak_bytes': 536870912}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False)


def same(actual, expected, message):
    need(canonical(actual) == canonical(expected), message)


def pin_bytes(path, raw):
    need(type(path) is str and bool(path) and type(raw) is bytes,
         'exact declared path and immutable raw byte buffer')
    return {'path': path, 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw)}


def fields(pairs):
    value = {}
    for key, item in pairs:
        need(key not in value, 'duplicate JSON field')
        value[key] = item
    return value


def reject_constant(token):
    raise ValueError('nonfinite JSON token: ' + token)


@dataclass(frozen=True)
class BoundArtifact:
    """Caller-owned raw bytes, with decoding bound to that same buffer.

    ROOT's future owner must charge reading/decoding and retain the original
    files. This value is not a producer-asserted acceptance token.
    """
    declared_path: str
    raw: bytes
    sha256: str
    size: int
    compressed_json: bool = False

    def pin(self):
        need(type(self.size) is int and type(self.compressed_json) is bool,
             'strict size/encoding types')
        value = pin_bytes(self.declared_path, self.raw)
        same(value, {'path': self.declared_path, 'sha256': self.sha256,
                     'bytes': self.size}, 'exact immutable decoded-byte authority')
        return value

    def json(self):
        self.pin()
        raw = gzip.decompress(self.raw) if self.compressed_json else self.raw
        return json.loads(raw.decode('utf8'), object_pairs_hook=fields,
                          parse_constant=reject_constant)


def documents(bundle, roles):
    need(type(bundle) is dict and set(bundle) == set(roles),
         'complete exact role bundle, no hidden authority fields')
    need(all(isinstance(bundle[r], BoundArtifact) for r in roles),
         'every decoded input has immutable bound bytes')
    return {r: bundle[r].json() for r in roles}


CONTEXT_ROLES = (
    'compiled_context', 'preparation_evidence', 'fresh_static_result',
    'fresh_static_plan', 'fresh_static_resource', 'trusted_static_tool_terminal',
    'frozen_reference', 'frozen_split', 'frozen_RL_protocol',
    'frozen_selection_binding', 'family_projection',
)


def pin_closure(document, closure):
    """Retain and bind every exact nested pin without inventing observations."""
    need(type(closure) is dict and all(isinstance(v, BoundArtifact) for v in closure.values()),
         'complete caller-owned raw receipt/source closure')
    required = {}
    def visit(value):
        if type(value) is dict:
            if set(value) == {'path', 'sha256', 'bytes'}:
                path = value['path']
                old = required.setdefault(path, value)
                same(old, value, 'consistent nested raw pin')
            else:
                for item in value.values():
                    visit(item)
        elif type(value) is list:
            for item in value:
                visit(item)
    visit(document)
    for path, record in required.items():
        need(path in closure, 'missing closed raw artifact/source: ' + path)
        same(closure[path].pin(), record, 'entire nested raw pin closure')
    return required


def context_receipt_gate(bundle, selector, resource_closure):
    """Bind a future accepted static result and its scoped resource receipt.

    Requires genuine accepted disposition from the separately reviewed future
    clock/finalizer chain. It does not recompute that ledger, infer acceptance
    from raw semantics, or permit either already executed selector.
    """
    need(type(selector) is str and selector in FUTURE_SELECTORS,
         'only one previously unexecuted frozen selector; no equality/guard retry')
    data = documents(bundle, CONTEXT_ROLES)
    compiled, evidence = data['compiled_context'], data['preparation_evidence']
    static, resource = data['fresh_static_result'], data['fresh_static_resource']
    need(compiled['schema'] == 'closed-frozen-curriculum-context-v1',
         'exact existing curriculum model, not a new proof grammar')
    same(static['status'], 'passed_independent_frozen_curriculum_context_family_pool_audit',
         'actual fresh independent semantic gate')
    for key, value in {'static_context_pool_accepted': True, 'trace_accepted': False,
            'certificate_accepted': False, 'RL_episode_or_training_accepted': False,
            'full_DFS_or_RNG_replay_accepted': False, 'whole_target_logical_checks': 0,
            'native_queries': 0, 'native_accepted': False, 'searches': 0, 'training': 0,
            'primitive_license_count': 229, 'non_assumption_witness_count': 226,
            'source_body_count': 171, 'single_types': 171, 'pair_types': 29241,
            'RL_full_pool_capacity': 64, 'RL_full_pool_capacity_satisfied': True}.items():
        same(static[key], value, 'exact complete static field: ' + key)
    same(static['selector'], selector, 'same exact independently audited selector')
    same(static['plan'], bundle['fresh_static_plan'].pin(), 'bound actual static plan')
    same(static['compiled_context_pin'], bundle['compiled_context'].pin(), 'bound model')
    same(static['preparation_evidence_pin'], bundle['preparation_evidence'].pin(), 'bound full pool')
    for key in ('model_epoch', 'group_authority_epoch', 'original_body_authority_epoch'):
        same(static[key], evidence[key], 'same static/evidence authority: ' + key)
    same(static['context_id'], compiled['context_id'], 'compiled context identity')
    same(static['model_epoch'], evidence['graph_binding']['model_epoch'], 'bound graph epoch')
    groups = evidence['groups']
    need(type(groups) is list and len(groups) <= 64,
         'complete full pool within frozen capacity; never trim')
    same(len(groups), len(static['groups_checked']), 'all independently checked groups')
    same(resource['schema'], 'ROOT-compact-static-external-resource-disposition-v1',
         'future exact scoped static resource schema')
    same(resource['status'], 'accepted_conditional_known_topology_static_resource_envelope',
         'accepted scope required; UNKNOWN is not admission')
    for key, value in {'resource_accepted': True, 'static_context_pool_resource_qualified': True,
            'semantic_static_candidate': True, 'RL_full_pool_capacity': 64,
            'RL_full_pool_capacity_satisfied': True, 'all_five_qualification': False,
            'target_proof_accepted': False, 'trace_accepted': False, 'new_training': False,
            'external_wait4_claim': False, 'OS_hard_cap_claim': False,
            'whole_host_cap_claim': False}.items():
        same(resource[key], value, 'exact scoped resource field: ' + key)
    same(resource['selector'], selector, 'resource selector')
    same(resource['plan'], bundle['fresh_static_plan'].pin(), 'resource plan pin')
    same(resource['closed_artifacts']['owner_result'], bundle['fresh_static_result'].pin(),
         'resource-qualified closed full semantic result')
    same(resource['complete_group_count'], len(groups), 'complete resource-bound group count')
    same(resource['terminal_tool_result'], bundle['trusted_static_tool_terminal'].pin(),
         'trusted actual terminal bytes, not a launch flag')
    tool = data['trusted_static_tool_terminal']
    same(tool['terminal'], True, 'actually terminal static tool')
    same(tool['actual_invocations'], 1, 'once-only future static phase')
    same(tool['terminal_tool_result']['result']['exit_code'], 0, 'successful terminal gate')
    same(resource['resource_ledger']['resource_accepted'], True, 'accepted closed scoped ledger')
    same(resource['resource_ledger']['all_five_qualification'], False, 'no global escalation')
    pin_closure(resource, resource_closure)
    # ROOT's future source contract must independently pin/close raw frames,
    # owner receipt/SELF, observer tables, platform/activation and local clocks.
    # Their presence and complete bytes are required by phase_authority below;
    # this static disposition is not a new resource checker.
    return data


def library_bindings(libraries, expected):
    """Verify the exact source bytes of already ROOT-owned loaded modules.

    No import is performed here. The future reviewed owner must bind transitive
    imports and source manifests before loading any scientific library.
    """
    need(type(libraries) is dict and type(expected) is dict and set(libraries) == set(expected),
         'entire exact source/library role map')
    for role, module in libraries.items():
        record = expected[role]
        path = Path(module.__file__).resolve()
        need(path == Path(record['absolute_path']).resolve(), 'loaded source path: ' + role)
        same(pin_bytes(record['pin']['path'], path.read_bytes()), record['pin'],
             'loaded exact source bytes: ' + role)


def owned_result_gate(receipt_artifact, result_artifact, closure, *, phase, selector, mode):
    """ABSTRACT FUTURE INTERFACE: exact closed result + owned resource receipt.

    A new reviewed producer/replay process owner must implement this distinct
    proof-control resource disposition. The existing static-only clock chain
    does not emit it. No instance exists in this source package. This function
    binds its claimed accepted scope and raw closure, not a memory theorem.
    """
    need(isinstance(receipt_artifact, BoundArtifact) and isinstance(result_artifact, BoundArtifact),
         'future immutable owned receipt/result bytes')
    receipt = receipt_artifact.json()
    same(receipt['schema'], 'ROOT-one-context-proof-control-owned-resource-disposition-v1',
         'distinct future search/replay owner contract; not static credit')
    same(receipt['status'], 'accepted_conditional_known_topology_proof_control_resource_envelope',
         'future complete owned lifecycle accepted, never UNKNOWN')
    same(receipt['phase'], phase, 'owned producer/replay phase')
    same(receipt['selector'], selector, 'owned context')
    same(receipt['mode'], mode, 'owned lane')
    same(receipt['result'], result_artifact.pin(), 'resource-qualified exact returned bytes')
    same(receipt['owned_limits'], OWNED_LIMITS, 'inclusive immutable phase ceilings')
    same(receipt['resource_accepted'], True, 'actual accepted retrospective resource scope')
    same(receipt['all_five_qualification'], False, 'no globally qualified learner')
    same(receipt['new_training'], False, 'no training credit')
    same(receipt['OS_hard_cap_claim'], False, 'no hard-cap theorem')
    same(receipt['whole_host_cap_claim'], False, 'known owned scope only')
    same(receipt['external_wait4_claim'], False, 'trusted tool terminal provenance')
    same(receipt['resource_clock_rule'], 'process_local_no_cross_process_absolute_comparison',
         'no cross-emitter absolute clocks')
    same(receipt['postlude_reserve_bytes'], 33554432, 'frozen conditional reserve')
    for field, maximum in [('whole_tool_bound_seconds', 180), ('owner_complete_seconds', 175),
                           ('worker_complete_seconds', 170), ('scoped_estimate_bytes', 536870912)]:
        value = receipt[field]
        need(type(value) in (int, float) and 0 <= value <= maximum,
             'actual owned phase ceiling: ' + field)
    pin_closure(receipt, closure)
    for field in ('trusted_tool_terminal', 'ROOT_SELF', 'ROOT_raw_frame', 'owner_raw_frame',
                  'worker_raw_frame', 'owner_lifetime', 'observer_tables', 'closed_artifacts',
                  'source_review', 'platform_evidence'):
        need(field in receipt, 'complete future raw resource term: ' + field)
    tool_pin = receipt['trusted_tool_terminal']
    tool = closure[tool_pin['path']].json()
    same(tool['terminal'], True, 'actual trusted phase tool terminal')
    same(tool['actual_invocations'], 1, 'once-only future job, no retry')
    same(tool['terminal_tool_result']['result']['exit_code'], 0, 'successful owned terminal')
    return receipt


def phase_authority(activation, source_contract, phase, selector, mode, input_pins):
    """Future caller supplies exact ROOT-issued activation and reviewed contract.

    No such record is created or supplied in this source-only package. The
    process-local owner/entry/finalizer chain is an explicit unresolved input.
    """
    need(phase in ('producer', 'independent') and selector in FUTURE_SELECTORS and mode in MODES,
         'exact future deterministic phase/context/lane')
    need(isinstance(activation, BoundArtifact) and isinstance(source_contract, BoundArtifact),
         'future raw ROOT source/activation receipt authority')
    contract, gate = source_contract.json(), activation.json()
    same(contract['schema'], 'ROOT-reviewed-one-context-proof-control-source-contract-v1',
         'separately reviewed future source contract')
    same(contract['status'], 'reviewed_source_contract_no_execution_claim', 'source scope')
    same(contract['phase'], phase, 'source phase')
    same(contract['version'], VERSION, 'source version')
    same(contract['selectors'], list(FUTURE_SELECTORS), 'excluded prior failures remain excluded')
    same(contract['modes'], list(MODES), 'exact two deterministic controls')
    same(contract['search_limits'], LIMITS, 'unchanged search limits')
    same(contract['owned_limits'], OWNED_LIMITS, 'prospective complete owned lifecycle limits')
    same(contract['resource_clock_rule'], 'process_local_no_cross_process_absolute_comparison',
         'each emitter uses its own local origin')
    same(contract['required_raw_resource_terms'], ['trusted_tool_terminal', 'ROOT_SELF',
         'ROOT_raw_frame', 'owner_raw_frame', 'worker_raw_frame', 'owner_lifetime',
         'observer_tables', 'closed_artifacts', 'source_review', 'platform_evidence'],
         'complete future owned resource closure is mandatory')
    same(gate['schema'], 'ROOT-one-context-proof-control-phase-activation-v1', 'separate activation')
    same(gate['authorized'], True, 'explicit future ROOT owner authorization')
    same(gate['source_contract'], source_contract.pin(), 'exact reviewed source contract')
    same(gate['phase'], phase, 'activation phase')
    same(gate['selector'], selector, 'activation context')
    same(gate['mode'], mode, 'activation lane')
    same(gate['input_pins'], input_pins, 'complete immutable future inputs')
    same(gate['new_training'], False, 'no learner activation')
    same(gate['all_five_qualification'], False, 'no global RL credit')
    return copy.deepcopy(contract)
