"""Source/read-only metadata inspection and prospective bridge; never imports code.

No checker, compiler, model constructor, inference, target search or native run.
JSON/GZip files are inspected as static source artifacts only.
"""
import ast
import gzip
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
R = ROOT / 'research/gcts-rl-renewal'
D = ROOT / 'docs/research/gcts-rl-renewal'
L = ROOT / '.gcts-active/hilbert-cluster-lifecycle-20261011'


def pin(path):
    path = Path(path); h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(65536), b''):
            h.update(data)
    return {'path': str(path.relative_to(ROOT)), 'sha256': h.hexdigest(),
            'bytes': path.stat().st_size}


def read(path):
    path = Path(path)
    with (gzip.open(path, 'rt') if path.suffix == '.gz' else path.open()) as stream:
        return json.load(stream)


def save(name, value):
    with (HERE / name).open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def main():
    started = time.perf_counter()
    names = ['shared_wang_inventory.py', 'native_wang_search.py', 'native_wang_cases.py',
             'native_wang_domains.cpp', 'kernel_machine.py', 'uniform_stack_machine.py',
             'binary_stack_machine.py', 'stack_program.py', 'serialized_kernel.py',
             'tree_kernel.py', 'tree_machine.py', 'tree_native.py', 'fol_checker.tree',
             'boundary_syntax.tree', 'proof_boundary.py', 'tape_tree_machine.py',
             'tape_binary.py', 'audit_proof_boundary.py', 'certificate_boundary_search.py',
             'micro_cert.py', 'micro_cert_builder.cpp', 'micro_response_check.cpp']
    sources = [pin(R / name) for name in names]
    sources += [pin(HERE / 'freeze_source_inspection_v1.py'),
                pin(L / 'hilbert_cluster_lifecycle_v1.py'),
                pin(ROOT / '.gcts-active/hilbert-primitive-executor-20261011/hilbert_primitive_graph_v2.py')]
    for source in sources:
        if source['path'].endswith('.py'):
            ast.parse((ROOT / source['path']).read_text(), filename=source['path'])
    paths = [ROOT / 'AGENTS.md', ROOT / 'docs/basic-tiling-algorithm.md',
             D / 'shared-wang-reader-001.json', D / 'native-wang-search-001.json',
             D / 'proof-boundary-001.json', D / 'proof-boundary-microcode-001.json.gz',
             D / 'proof-boundary-machine-001.bin.gz', D / 'kernel-machine-001.json',
             D / 'uniform-machine-001.json', D / 'binary-machine-001.json',
             ROOT / '.gcts-active/hilbert-aggregate-expansion-20261011/model-v2.json.gz',
             ROOT / '.gcts-active/hilbert-aggregate-expansion-20261011/reader-data-v2.json',
             ROOT / '.gcts-active/hilbert-aggregate-independent-audit-20261011/audit-full-v2.json',
             ROOT / '.gcts-active/hilbert-primitive-executor-20261011/full-model-plan-v1.json',
             ROOT / '.gcts-active/stochastic-replay-review-20261011/geometry-full-independent-result-v1.json',
             L / 'full-language-plan-v3.json', L / 'full-language-freeze-v3.json',
             L / 'full-language-outcome-v3.json', L / 'full-language-lifetime-v3.json',
             L / 'full-language-supervision-v3.json']
    inputs = [pin(p) for p in paths]
    reader = read(D / 'shared-wang-reader-001.json')
    boundary = read(D / 'proof-boundary-001.json')
    native = read(D / 'native-wang-search-001.json')
    model = read(ROOT / '.gcts-active/hilbert-aggregate-expansion-20261011/model-v2.json.gz')
    actual = next(m for m in model['models'] if m['height'] == 24)
    formula_codes = model['formula_codes']
    palette = reader['inventory']
    target_code = actual['boundary']['fixed_target_m'][0][2]
    inventory_census = {}
    for recipe in model['recipes']:
        name = recipe['primitive_witness']['rule']
        inventory_census[name] = inventory_census.get(name, 0) + 1
    tiny_and_full = read(L / 'full-language-plan-v3.json')
    # Historical preservation is verified, never modified. All 116 MB expansion
    # bytes are hashed in streaming fashion; their source bodies are not loaded.
    preserved = {}
    for item in tiny_and_full['sources'] + tiny_and_full['inputs'] + tiny_and_full['preserved_files']:
        actual_pin = pin(ROOT / item['path'])
        if actual_pin != {k: item[k] for k in ('path', 'sha256', 'bytes')}:
            raise ValueError('old frozen evidence differs: ' + item['path'])
        preserved[actual_pin['path']] = actual_pin
    fixed_source_table = [
        {'component': 'geometry point grammar', 'object': '217 exact formula AST colors; 229 primitive recipe witnesses; ordered prior-row input offsets',
         'request_independent': False, 'search_role': 'Full finite recipient-specific primitive point catalog and reference scheduler.'},
        {'component': 'kernel_machine.Catalog / KernelMachine', 'object': 'External finite syntax catalog is compiled into fact slots and instruction alphabet r:i',
         'request_independent': False, 'search_role': 'Earlier finite-catalog proof-machine route; rebuilding it for geometry would not implement the requested single shared palette.'},
        {'component': 'UniformMachine', 'object': 'Fixed two-binary-stack interpreter with unary program addresses on tape',
         'request_independent': True, 'search_role': 'Generic computation component; published controls explicitly exclude a complete serialized FOL checker port.'},
        {'component': 'BinaryMachine', 'object': 'Fixed compact/relative-address two-stack interpreter',
         'request_independent': True, 'search_role': 'Generic computation component; cannot substitute short-bit equality controls for geometry inference checking.'},
        {'component': 'shared_wang_inventory.Inventory', 'object': 'Fixed radius-one local reduction of the pinned full parser/FOL checker physical machine',
         'request_independent': True, 'search_role': 'The actual common mathematical proof-validation palette. Theory, formula ASTs and certificate are boundary data.'},
    ]
    static = {
        'status': 'source_and_static_metadata_inspected_no_scientific_execution',
        'saved_utc': datetime.now(timezone.utc).isoformat(), 'sources': sources, 'inputs': inputs,
        'preserved_files': [preserved[k] for k in sorted(preserved)],
        'current_geometry_census': {'formulas': len(formula_codes), 'recipes': len(model['recipes']),
            'rules': inventory_census, 'rows': actual['height'], 'source_family_definitions': 171,
            'context': actual['context'], 'boundary': actual['boundary'], 'target_formula_code': target_code,
            'target_ast': formula_codes[target_code], 'formula_registry_sha256': model['formula_registry_sha256'],
            'authority_epoch': model['authority']['epoch'],
            'authority_label': model['authority']['label'], 'native_accepted': False},
        'fixed_shared_palette_metadata': {'inventory': palette,
            'literal_table_sha256': boundary['machine']['literal_binary_sha256'],
            'literal_bytes': boundary['machine']['literal_bytes'],
            'program_sha256': boundary['program_sha256'], 'micro_sha256': boundary['machine']['micro_sha256'],
            'micro_states': boundary['machine']['micro_states'], 'tapes': boundary['machine']['tapes'],
            'problem_band': boundary['boundary']['problem'], 'certificate_band': boundary['boundary']['certificate'],
            'wire': boundary['boundary']['wire'],
            'native_search_published_scope': native['scope']},
        'routes': fixed_source_table,
        'existing_dense_cost_control': [{k: c['native'][k] for k in ('physical_steps', 'micro_steps', 'status')}
            | {'name': c['name']} for c in boundary['cases'] if c['name'] in ('reflexivity', 'addition-induction')],
        'source_current_vs_compiled_binding': 'Exact compiled artifacts and current source files are separately pinned; source inspection alone is not a fresh compiler equivalence theorem.',
        'inspection_seconds_before_write': time.perf_counter() - started,
        'authoring_time': 'Unmeasured; reading/hashing metadata is preparation, not a native or search result.',
        'scientific_model_constructions': 0, 'native_queries': 0, 'target_searches': 0,
        'compiler_activations': 0, 'training': False}
    save('static-source-inspection-v1.json', static)

    design = {
        'status': 'prospective_exact_certificate_bridge_no_implementation_or_activation',
        'static_inspection': pin(HERE / 'static-source-inspection-v1.json'),
        'problem_latex': r'\Gamma=\{H(P,Q,l,m),H(P,Q,m,n),\operatorname{Incident}(R,l)\},\qquad I.2,\Gamma\vdash\operatorname{Incident}(R,n)',
        'guard_latex': r'H(A,B,u,v)=\operatorname{Point}(A)\land\operatorname{Point}(B)\land\operatorname{Line}(u)\land\operatorname{Line}(v)\land\neg(A=B)\land\operatorname{Incident}(A,u)\land\operatorname{Incident}(B,u)\land\operatorname{Incident}(A,v)\land\operatorname{Incident}(B,v)',
        'logical_scope': 'Closed-constant ground sequent in one-sorted symbolic guarded incidence fragment; Point/Line/Incident are arbitrary predicates. No coordinates, existential line construction, full Hilbert Euclidean theory or universal closure is claimed.',
        'gap': 'The finite recipe tiles are proof-command placements, not the common machine Wang squares. There is no one-square-to-one-square isomorphism: a primitive inference needs serialized ASTs, interpreter workspace and many physical transition rows.',
        'forward_map': [
            {'step': 1, 'object': 'Exact point certificate', 'obligation': 'One selected primitive key per row; reconstruct all t/m from recipe witness and ordered reference offsets; exact target/color, absent versus assigned zero, roots and seeds, full IDs/epochs. Placement execution order is not logical line order.'},
            {'step': 2, 'object': 'Canonical 24-line local symbolic certificate', 'obligation': 'Sort by row, retain every row including padding/repeated premises. Copy zero-port witnesses literally. For MP, set antecedent/ref[0] and implication/ref[1] to exact row numbers; independently check both precede the row and source formulas match exact implication shape.'},
            {'step': 3, 'object': 'Flat gcts-fol-1 request', 'obligation': 'Top-level proof has no local assumptions. Retain I.2 and add three explicitly named closed ground axioms hypothesis-0/1/2 equal to Gamma. Translate every assumption(index=i) command to axiom(name=hypothesis-i), retaining formula/row/references. blocks=[]; schemas=[]; target exact code54 AST. This is the same ground sequent relative to Gamma, not a theorem without Gamma.'},
            {'step': 4, 'object': 'Independently checked symbolic/request certificate', 'obligation': 'Independent checker revalidates all selected axiom/instantiate/eq_subst/ordered-MP instances, capture conditions, field types and signature; never infers validity from matching colors. Validate the local certificate under Gamma and the flat request under I.2+Gamma separately.'},
            {'step': 5, 'object': 'Fixed and free postfix boundary words', 'obligation': 'Fixed word serializes protocol,theory,target in that order. Free word serializes empty blocks then all 24 proof commands. Tagged byte trees use nine little-endian bits per atom0..256 and one cons bit. All object ordering is frozen and retained; do not change nested order or drop commands while claiming exact wire-byte identity.'},
            {'step': 6, 'object': 'Shared machine input', 'obligation': 'Use exact boot nodes, current fixed microtable and literal table, true parser start, exact43-band framing/heads. Independently reconstruct full boundary/input bytes and problem hash. Only separately declared blank resources may change; no target-specific transition compilation.'},
            {'step': 7, 'object': 'Native response / symbolic Wang computation certificate', 'obligation': 'A later explicitly authorized fresh native request and full independent replay establish acceptance or resource unknown. Compact response hierarchy may encode the physical transition computation, but a cropped/local diagram is not a complete accepting rectangle.'},
        ],
        'inverse_scope': 'Any independently valid 24-row certificate maps to one request-boundary payload in the fixed shared encoding. The converse only holds for payloads obeying the explicit finite geometry recipe/row grammar; arbitrary shared-palette accepted proofs can use formulas/rules outside this envelope. No bijection or shared-palette GCTS-search equivalence claim.',
        'assumption_map': {'source': actual['context']['ordered_local_premises'],
            'recipient_names': ['hypothesis-0', 'hypothesis-1', 'hypothesis-2'],
            'preserve_order_and_duplicate_multiplicity': True,
            'closed_signature': actual['context']['theory']['functions'],
            'no_implicit_discharge': 'A universally quantified conditional theorem requires a separate deduction/eigenvariable closure and resource gate, previously unknown; it is not produced by adding ground hypothesis axioms.'},
        'full_palette_cost_obstacle': 'The published reflexivity control uses229147579770 literal physical transitions. A dense rectangle has one row per literal transition and full input width per row, far beyond a bounded host search. Do not promise free-boundary proof search over the complete physical rectangle in this pilot.',
        'recommended_role': 'Use the exact complete finite primitive graph for search and the unchanged common checker palette for eventual certificate validation. The first bridge gate tests this concrete specialization; it does not prove the specialization universal or beneficial.'}
    save('bridge-design-v1.json', design)

    gate = {
        'status': 'prospective_bounded_automatic_primitive_geometry_search_root_review_required',
        'bridge_design': pin(HERE / 'bridge-design-v1.json'),
        'static_inspection': pin(HERE / 'static-source-inspection-v1.json'),
        'before_execution': 'Freeze exact new worker/ordering/decoder/independent auditor/owned resource sources and all prerequisites; root source review and explicit dispatch remain required. This proposal authorizes nothing.',
        'prerequisites': ['Accepted prior all171 static logical expansion audit and complete primitive graph audit',
            'Accepted tiny whole-cluster producer+independent audit',
            'Accepted full-language whole-cluster producer+separately owned independent audit; producer alone is insufficient',
            'Independent source review of new fixed ordering, certificate decoder, trace replay and resource owner'],
        'model': {'load_exact_prior_point_plan': '.gcts-active/hilbert-primitive-executor-20261011/full-model-plan-v1.json',
            'model_epoch': '06bc80d38463caa934136e428e66a05bafd6715c715f1fa3892b0dcf20c3c46c',
            'formulas': 217, 'recipes': 229, 'rows': 24, 'target_code': target_code,
            'recipe_ids': [r['id'] for r in model['recipes']],
            'rule_census': inventory_census, 'boundary_changed': False,
            'all_family_bodies_validated': 171, 'active_cluster_descriptors': 0,
            'reason_no_cluster_hints': 'The accepted lifecycle is root-fixed. A target-independent dynamic family proposer/registry-extension protocol is not yet audited. No authored24 word or precomposed target cluster is supplied.'},
        'observations': [{'id': 'base-complete-primitives', 'order': 'Existing complete base candidate order, empty descriptors', 'repetitions': 1},
                         {'id': 'fixed-forward-novelty', 'order': 'Separately authored generic local readiness/novelty ordering, empty descriptors', 'repetitions': 1}],
        'fixed_forward_order_spec': {
            'all_keys': 'At the exact current global branch point, order every legal key; retain every alternative. Forced action always uses its sole base key.',
            'proved_outputs': 'Exact output formula codes of already selected primitive row placements, not formulas merely marked on unoccupied rows.',
            'tiers': ['Novel MP output with both ordered referenced rows selected',
                'Novel instantiate output whose exact universal AST is already a selected output',
                'Novel eq_subst output whose exact equality antecedent and inner implication antecedent are already selected outputs',
                'Novel named axiom output',
                'Novel eq_subst output whose equality antecedent is already selected',
                'Other novel legal outputs', 'Repeated legal output'],
            'ties': 'Exact output AST node count, canonical primitive witness JSON, recipe index, ordered reference tuple. No geometry-specific constants/variable substitutions/target proof path in code.',
            'scope': 'Author-designed ordering control, not RL training, a pruning rule or a host logical oracle. Full point legality and proof validity still come from complete graph and independent checker.'},
        'limits': {'owner_total_seconds': 180, 'supervisor_seconds': 175, 'child_alarm_seconds': 170,
            'host_bytes': 536870912, 'each_search_seconds': 20, 'each_search_attempts': 128,
            'each_search_event_ceiling': 2000, 'maximum_searches': 2,
            'independent_audit': 'Separate frozen <=180s/512MiB owner; every reported trace branch/exclusion and certificate must pass or remain unaudited unknown.'},
        'exactness': ['All24 roots active generation0 and only three exact hypothesis seed placements generation0',
            'Global dead before forced before earliest generation; minimum degree only a generation tie-break',
            'All229 recipe domains with all ordered prior references and remote marking agreement; absent and0 distinguished',
            'Base fallback is the whole domain, not the fixed ranking shortlist; complete permutation checked by independent oracle',
            'Branch-local exclusion only for independently reconstructed complete child failure/exhaustion; timeout/attempt/trace/memory unknown creates no exclusion',
            'All graph/hint metadata paired rollback restored; immutable full identity sharing and body authority retained',
            'A full point region must be independently reconstructed and every primitive inference checked before mathematical result'],
        'independent_search_trace_plan': 'Independently reconstruct full legal recipe/reference sets or exact integer factor counts at every visited decision and selected key; compare degrees, singleton/dead, action, placement m/t, strict-prior refs and all deltas. Stream entire successful certificates. Replay every returned exhausted child from its complete recorded finite subtree and alternative coverage; zero/one resource controls must restore exact parent without exclusion.',
        'successful_output': 'Every24 placement/fullID/recipe/witness/reference; complete immutable tree/events/costs; local Gamma-relative proof and flat request bytes/problem hash. Preserve all24 commands and their ordinary candidate provenance, including padding. Do not splice an authored proof on timeout.',
        'outcome_labels': ['finite_exact_point_tiling_pending_independent_symbolic_and_trace_audit',
            'accepted_ground_symbolic_theorem_after_full_audit', 'unknown_search_budget',
            'exhausted_complete_24_row_marked_language_only', 'unknown_audit_resource_or_correspondence'],
        'costs': 'Charge all source/family preparation, old native admissions and retained unknowns as dependencies; new cold model/registry setup, ordering feature/sort cost, complete domain refresh, DFS/exclusions/rollback, decoder/serialization and independent audit separately. No new training bill. One observation per lane supports no significance or general speed claim.',
        'later_native_gate': {'not_authorized_here': True, 'maximum_requests': 1,
            'eligibility': 'Only the first independently accepted newly discovered certificate in predeclared base-then-fixed observation order; if none, preserve search unknowns and issue no native query.',
            'fixed_table': boundary['machine']['literal_binary_sha256'],
            'micro_limit': 20000000000, 'heap_band_cells': 262144,
            'resource_scope': 'Predeclare all native band capacities and exact encoded bytes after independent deterministic capacity estimate. The larger blank heap is an external resource boundary, not palette change. If estimate exceeds262144 or native run is unknown, stop; no automatic resize, shortened certificate or changed theory.',
            'owner_seconds': 180, 'host_bytes': 536870912,
            'independent_full_replay': 'Separate predeclared owner180s/512MiB, exact fixed/free/input/output bytes and native-step/lowering fingerprints.',
            'claim': 'Fresh shared-checker native acceptance of this certificate, not direct mathematical proof search on264143617200-square palette.'},
        'next_sources_before_actual_gate': ['shared_symbolic_geometry_search_v1.py', 'shared_symbolic_forward_order_v1.py',
            'shared_symbolic_bridge_decode_v1.py', 'independent_shared_symbolic_geometry_audit_v1.py',
            'owned_fail_closed_resource_supervisor_v1.py'],
        'native_queries_so_far': 0, 'target_searches_so_far': 0, 'model_constructions_so_far': 0,
        'new_training': False, 'compiler_changes': 0, 'publication': False}
    save('prospective-search-gate-v1.json', gate)
    manifest = {'status': 'frozen_private_source_inspection_design_and_prospective_gate_only',
        'files': [pin(HERE / name) for name in ('freeze_source_inspection_v1.py',
                  'static-source-inspection-v1.json', 'bridge-design-v1.json', 'prospective-search-gate-v1.json')],
        'source_count': len(sources), 'input_count': len(inputs),
        'verified_preserved_unique_paths': len(preserved),
        'preparation_seconds_before_manifest_write': time.perf_counter() - started,
        'owner_scientific_dispatches': 0, 'native_queries': 0, 'training': False,
        'unchanged_old_files': True, 'publication_owner': 'root'}
    save('manifest-v1.json', manifest)
    print(json.dumps(manifest), flush=True)


if __name__ == '__main__':
    main()
