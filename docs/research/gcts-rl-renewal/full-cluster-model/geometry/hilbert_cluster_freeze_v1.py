"""Static-only source/input/preservation freeze. Does not import any engine."""
import ast
import hashlib
import json
import sys
import time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PRIOR=ROOT/'.gcts-active/hilbert-primitive-executor-20261011'


def pin(path):
    path=Path(path); sha=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):sha.update(block)
    return {'path':str(path.relative_to(ROOT)),'sha256':sha.hexdigest(),'bytes':path.stat().st_size}


def main():
    start=time.perf_counter(); target=HERE/'plan-v1.json'
    if target.exists():raise ValueError('immutable prospective tiny plan exists')
    prior=json.loads((PRIOR/'full-model-plan-v1.json').read_text())
    previous=prior['sources']+prior['inputs']+prior['preserved_files']
    previous += [pin(p) for p in sorted(PRIOR.iterdir()) if p.is_file()]
    preserved={}
    for p in previous:
        current=pin(ROOT/p['path']); expected={k:p[k] for k in ('path','sha256','bytes')}
        if current!=expected:raise ValueError('prior frozen byte changed: '+p['path'])
        if p['path'] in preserved and preserved[p['path']]!=current:raise ValueError('ambiguous prior pin')
        preserved[p['path']]=current
    sources=sorted(HERE.glob('hilbert_cluster*_v1.py'))
    for p in sources:ast.parse(p.read_text(),filename=str(p))
    inputs=list(prior['inputs'])
    extra=[('frozen_primitive_core',PRIOR/'hilbert_primitive_graph_v2.py'),
           ('prior_full_model_plan',PRIOR/'full-model-plan-v1.json'),
           ('prior_whole_cluster_continuation_plan',PRIOR/'cluster-continuation-plan-v1.json'),
           ('prior_full_model_outcome',PRIOR/'full-model-outcome-v1.json'),
           ('prior_full_model_lifetime',PRIOR/'full-model-lifetime-v1.json'),
           ('prior_full_model_independent_result',ROOT/'.gcts-active/stochastic-replay-review-20261011/geometry-full-independent-result-v1.json'),
           ('prior_full_model_independent_lifetime',ROOT/'.gcts-active/stochastic-replay-review-20261011/geometry-full-independent-lifetime-v1.json'),
           ('prior_full_model_independent_integration',ROOT/'.gcts-active/stochastic-replay-review-20261011/geometry-full-independent-integration-v1.json'),
           ('source_constant_transport_certificate',ROOT/'.gcts-active/hilbert-constant-certificates-20261011/certificate-v3.json.gz'),
           ('source_constant_transport_audit',ROOT/'.gcts-active/hilbert-constant-certificates-20261011/audit-v3.json'),
           ('exact_three_source_schemas',ROOT/'.gcts-active/hilbert-chain-composition-plan-20261011/source-schemas-v1.json'),
           ('source_searched_native_receipt',ROOT/'docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_source_native.json.gz'),
           ('source_searched_native_independent_audit',ROOT/'docs/research/gcts-rl-renewal/hilbert_promotion_family_v3_source_audit.json'),
           ('source_general_transport_argument',ROOT/'docs/research/gcts-rl-renewal/constant-transport-argument.html'),
           ('source_general_transport_ledger',ROOT/'docs/research/gcts-rl-renewal/constant-transport-ledger.json'),
           ('source_general_transport_review',ROOT/'docs/research/gcts-rl-renewal/constant-transport-review.json'),
           ('full_exact_source_expansions',ROOT/'.gcts-active/hilbert-aggregate-expansion-20261011/expansions-v2.json.gz'),
           ('source_authoring_start',HERE/'authoring-start-v1.json')]
    inputs += [{'role':role,**pin(path)} for role,path in extra]
    authoring=json.loads((HERE/'authoring-start-v1.json').read_text())
    fixturetree=ast.parse((HERE/'hilbert_cluster_fixtures_v1.py').read_text())
    names=[n.args[0].value for n in ast.walk(fixturetree) if isinstance(n,ast.Call)
           and isinstance(n.func,ast.Name) and n.func.id=='passed' and n.args and isinstance(n.args[0],ast.Constant)]
    plan={'version':'hilbert-whole-cluster-lifecycle-tiny-gate-v1',
          'status':'frozen_source_ready_root_review_and_explicit_dispatch_required',
          'sources':[pin(p) for p in sources],'inputs':inputs,
          'preserved_files':[preserved[k] for k in sorted(preserved)],
          'producer_limits':{'full_outer_wall_seconds':60,'child_alarm_seconds':50,'supervisor_seconds':55,
                             'host_bytes':536870912,'execution_authorized_by_this_freeze':False},
          'gate_scope':'Synthetic adversarial transactions and bounded tiny DFS only; zero actual geometry models, no native/compiler activation or actual target search.',
          'projection_counts':{'fixture_groups_planned':len(names),'fixture_group_names':names,
                               'exhaustive_formula_states_planned':64,'counts_are_predictions_until_actual_terminal_receipt':True},
          'model_preservation':{'future_actual_height':24,'future_actual_recipes':229,'future_actual_formula_values':217,
                                'primitive_kernel':'exact frozen v2, imported with SHA check; no old source edits',
                                'fixed_global_seeds':'same three recipient assumptions, generation zero',
                                'translation_only':True,'orientation':'identity','new_point_defining_markings':False},
          'authority_boundary':{
              'registration':'Root-fixed frozen source/body registry; a caller descriptor is reconstructed against the registered body, not admitted by its self-hash.',
              'primitive_proposals':'arbitrary root-authored primitive placement bodies, explicitly not closed lemmas',
              'family_proposals':'exact all-171 body projection and complete source/native/static audit closure; flat primitive expansion replaces nested calls without erasing their provenance',
              'body_dependencies':'Registered explicit nested dependencies must be strict-prior and full-body bound; flat expanded family bodies have no remaining nested calls, while complete recursive source evidence remains pinned.',
              'whole_identity':'actual global recipient context plus literal recipe witness, all ordered refs, exact t/m, registry and authority; same formula is never a sharing identity',
              'metadata_mutation':'Advertised descriptor and actual context/formula/authority/palette/boundary/source metadata hashes are checked. Untracked mutation retires hints; changing the underlying graph version remains unsupported and requires a new accepted-prefix protocol.',
              'authority_label':'host finite source relation / ordering advice, not native_accepted',
              'no_authored_word':'The authored24 field is discarded by the family loader. No authored24 word supplies hints, seeds, training or generic continuation.'},
          'intended_gap_closure':{
              'historical_gap':'v2 checked an immutable preference set once, then skipped illegal constituents individually; it did not retire whole clusters, retain waiting hints or trail hint lifecycle.',
              'new_intention':['immutable body-bound descriptors','waiting/ready/consumed/retired whole status',
                  'forced-first resynchronization','all-ready exact preferred keys plus complete fallback',
                  'paired graph/hint checkpoint and semantic snapshot hash restoration',
                  'full exhausted-child return alone creates exact parent-local exclusion; budget unknown does not'],
              'currently_verified':'static syntax, exact hashes and source freeze only; not scientific fixture success'},
          'complete_graph_invariant':'Hints never alter graph recipe inventory, point domains, incidence counts, dead/forced/earliest selection, point generations or exclusions. Only the complete graph plus fully exhausted child evidence can create exclusions.',
          'fixed_policy':'root registrations and fixed integer priority/member order; no learned policy or new RL training',
          'output_evidence':['immutable source/body registries and descriptors','full controlled graph/hint snapshots',
                             'ordered repeated receptor ports and full member identities','explicit operation before/after records',
                             'synthetic DFS global decisions, unknown returns, exhausted exclusions and paired rollback trace',
                             'independent direct raw complete tiny domain/preference permutation comparisons'],
          'resource_enforcement':'task-owned external sampled own-child RSS/time watchdog; fail-closed kill/wait/reap; child SIGALRM; final conservative kernel-peak rejection. No OS soft-limit claim.',
          'cost_accounting':{'source_authoring_elapsed_since_instrumented_start_seconds':time.monotonic()-authoring['monotonic_seconds'],
              'initial_contract_read_cost':'before instrumented source start, not measured; not claimed zero',
              'freeze_preparation_seconds_before_plan_write':time.perf_counter()-start,
              'all_prior_native_preparation_and_unknowns':'Retained through exact source receipt, static export and preserved old evidence. No fresh native query.',
              'new_descriptor_compile_node_scan_ordering_rollback':'measured as separate cumulative metrics in fixtures; no rewinding work costs',
              'independent_audit':'separate owned source/freeze/resource phase; not supplied by producer'},
          'next_actual_gate':'Source-only separately frozen 229/217/24 controlled transactions after tiny producer+independent passes and root source review; no actual DFS or authored word proposals.',
          'native_compiler_correspondence':'open','native_queries':0,'actual_model_executions':0,
          'actual_geometry_target_searches':0,'new_RL_training':False,
          'runtime_observation':{'python_executable':sys.executable,'python_version':sys.version}}
    target.write_text(json.dumps(plan,indent=2)+'\n')
    receipt={'status':'lifecycle_sources_inputs_limits_frozen_without_execution','plan':pin(target),
             'source_count':len(sources),'input_count':len(inputs),'preserved_count':len(preserved),
             'source_syntax':'ast.parse only, no engine imports or scientific fixture execution',
             'fixture_executions':0,'actual_model_executions':0,'native_queries':0,
             'freeze_seconds_before_receipt_write':time.perf_counter()-start}
    (HERE/'freeze-receipt-v1.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt),flush=True)

if __name__=='__main__':main()
