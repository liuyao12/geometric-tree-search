"""Raw/AST-only once-plan preparation. No project imports or scientific calls."""
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent


def read(path):
    return json.loads(Path(path).read_bytes())


def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def checked(ref):
    path = Path(ref['path'])
    assert path.is_absolute() and path == path.resolve() and pin(path) == ref
    return path


def save(name, value):
    path = HERE / name
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
    return pin(path)


def main(argv):
    assert len(argv) == 4
    handoff_path, handoff_sha, peer_path, peer_sha = argv
    hpath, ppath = Path(handoff_path), Path(peer_path)
    assert pin(hpath)['sha256'] == handoff_sha and pin(ppath)['sha256'] == peer_sha
    handoff = read(hpath)
    sources, inputs = handoff['sources'], handoff['inputs']
    contract_ref = handoff['source_contract']
    contract = read(checked(contract_ref))
    assert len(sources) == 7 and len(inputs) == 8
    assert contract['sources'] == sources and contract['inputs'] == inputs
    for ref in [*sources.values(), *inputs.values(), *contract['original_model_sources'].values()]:
        checked(ref)
    for ref in sources.values():
        compile(ast.parse(Path(ref['path']).read_bytes()), ref['path'], 'exec')
    limits = {'aggregate_owned_bytes': 536870912, 'caller_finish_reserve_seconds': 1,
              'caller_seconds': 90, 'failure_only_seconds': 55, 'joint_seconds': 20, 'owned_seconds': 60}
    assert contract['limits'] == handoff['limits'] == limits
    peer = read(ppath)
    assert peer['source'] == sources['intake'] and peer['sources'] == sources
    assert peer['source_contract'] == contract_ref and peer['scope'] == contract['scope']
    assert peer['author_identity'] == '/root/arithmetic_induction'
    assert peer['reviewer_identity'] not in ('/root', '/root/arithmetic_induction')
    assert peer['source_only'] is True and peer['source_review_passed'] is True
    assert peer['scientific_calls'] == 0 and peer['scientific_acceptance'] is False
    root_review = dict(contract['Review_ABI'])
    root_review.update(source_contract=contract_ref, reviewer_identity='/root', source_review_passed=True,
        source_only=True, scientific_calls=0, scientific_acceptance=False, concrete_blockers=[],
        authorship_disclosure='Root reviewed new caller authored by arithmetic_induction and new projection module authored by hilbert_advice_controls. Root owns plan/execution only; distinct diagnosis reviews whole caller and projection. No project imports/functions/model or scientific execution during Source review.',
        checks=[
            'All new extraction/main/requirezero paths read; inherited top-level helpers checked by raw/AST inverse. Source7 executable custody is separately authenticated from exact original Source17 semantic map. Every originalSource raw buffer and both oldplan/grant/review/input2 bindings verified; old intake/engine/search never loaded.',
            'Deterministic first saved DEAD0 selects one preceding root TRY/PLACE and no exclusions/restores. Saved evidence/status arrays and late returned_metadata are unused. Complete original root/selected point state is reconstructed via pinned c354 membership/support/marking logic and compared with old root/state hashes; no epoch/key rewrite.',
            'Fresh c960 proposal and fresh-language independently authored c354 fullcontext cover must complete ZERO with exact state/binding/row, empty candidates, no singleton, false higher flags. Native/membership/guard exceptions propagate; incomplete UNKNOWN is never zero. Local conclusion is conditional, not validation of old trajectory.',
            'Fresh row0 projection module generation and same-implementation fresh verification use private original raw authority/literal. Full six-rule AX/Gamma census and row0 necessary-boundary argument separately Source-reviewed. It gives input-scoped reusable exclusion, not a second theorem implementation,1717/99b3 acceptance or arbitrary-row generalization.',
            'Twelve explicit new controls preserve copied-old-receipt, state/epoch/prefix, forgedcensus and UNKNOWN rejection; original AX yields NOT_CERTIFIED. Projection literal/binding/census forgery checks compare full certificate. No original17/23/43 meaning changed or rerun; no targetsearch/proofword/donor/route/markactivation/RL/gain.',
            'Same early native20/500MiB internal reserve,512MiB aggregate, inherited once/meter2/CodeSeal/immediateguard/transport/response2LF/nativeexit/postprobe closure. Single owned process/no children. All cold setup/imports/proposals/checking/controls/output charged; strict postterminal20 plus caller90/owned60 gates required.',
            'Trusted synchronous pinned Source scope only, no hostile concurrent OS claim. Unit-row specialization and complete reference-conformance gaps remain. All broad research objectives stay active.'
        ])
    root_ref = save('ROOT-caller-Source-review-v1.json', root_review)
    projection_root = pin(HERE / 'ROOT-projection-Source-review-v1.json')
    projection_peer = pin(BASE / 'unit-row-row-zero-projection-independent-source-20261016/typed-Source-review-v1.json')
    for ref in (projection_root, projection_peer):
        r = read(checked(ref))
        assert r['source'] == sources['row0_projection'] and r['source_review_passed'] is True
        assert r['scientific_calls'] == 0 and r['scientific_acceptance'] is False
    runtime = pin(Path('/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/bin/python3.9'))
    assert (runtime['sha256'], runtime['bytes']) == ('bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e', 102352)
    owned, external = HERE / 'certification-owned-v1', HERE / 'certification-external-v1'
    assert not owned.exists() and not external.exists()
    protocol = save('ROOT-certification-protocol-choice-v1.json', {
        'schema': 'ROOT-row0-local-certification-protocol-choice-v1',
        'previous_goal_turn': 'progress', 'current_goal_turn': 'progress',
        'sources': sources, 'inputs': inputs, 'limits': limits,
        'original_model_sources': contract['original_model_sources'],
        'original_model_inputs': contract['original_model_inputs'],
        'original_model_binding': contract['original_model_binding'],
        'sample_selection': 'First DEAD0 root-child context from each old arm in fixed canonical/advised order; saved receipt never accepted.',
        'expected_samples': 2, 'expected_controls': 12,
        'scientific_execution': False, 'target_search': False, 'marking_activation': False,
        'scope': 'Fresh conditional local ZERO and input-scoped row0 structural projection only; no fulltrajectory/targetproof/gain/RL.',
        'costs': 'All cold authentication/imports/reconstruction/proposal/check/census/negative controls/output/nativeexit/postprobe charged.'
    })
    common = {'invocation_id': 'row0-first-DEAD0-certification-20261016-v1',
              'purpose': 'unit-row-first-DEAD0-certification', 'output_directory': str(owned),
              'sources': sources, 'inputs': inputs, 'source_contract': contract_ref,
              'reviews': {'ROOT': root_ref, 'peer': pin(ppath)}, 'runtime': runtime,
              'limits': limits, 'resource_rule': 'single-owned-process-native-terminal-v1'}
    grant = save('ROOT-certification-authorization-v1.json', dict(common,
        schema='ROOT-first-DEAD0-certification-authorization-v1', author_identity='/root',
        actual_execution_authorized=True, maximum_actual_invocations=1, protocol_choice=protocol,
        dependency_reviews={'projection_ROOT': projection_root, 'projection_peer': projection_peer}))
    plan = save('ROOT-certification-plan-v1.json', dict(common,
        schema='ROOT-first-DEAD0-certification-plan-v1', ROOT_authorization=grant))
    save('ROOT-certification-preflight-v1.json', {
        'schema': 'ROOT-row0-local-certification-preflight-v1', 'plan': plan,
        'handoff': pin(hpath), 'scientific_calls': 0,
        'current_Source7_input8_original_Source17_verified': True,
        'fresh_owned_and_external_outputs': True})
    print(json.dumps({'plan': plan, 'external_directory': str(external)}))


if __name__ == '__main__':
    main(sys.argv[1:])
