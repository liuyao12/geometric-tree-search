"""Root saved-byte reconciliation only. Never imports or runs scientific Source."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
checks = []


def check(value, label):
    if not value:
        raise ValueError(label)
    checks.append(label)


def canon(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(Path(path).read_bytes())


def pin(ref):
    raw = Path(ref['path']).read_bytes()
    check((len(raw), sha(raw)) == (ref['bytes'], ref['sha256']), 'pin:' + ref['path'])
    return raw


def wire(path):
    raw = Path(path).read_bytes()
    check(raw.endswith(b'\n') and raw.count(b'\n') == 2, 'whole two-LF:' + str(path))
    a, b = raw.splitlines()
    body, completion = json.loads(a), json.loads(b)
    check(completion['body_sha256'] == sha(a+b'\n') and completion['body_bytes'] == len(a)+1,
          'completion whole body:' + str(path))
    check(a == canon(body) and b == canon(completion), 'canonical whole response:' + str(path))
    return body


def record(path):
    p = Path(path)
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'sha256': sha(raw), 'bytes': len(raw)}


def main():
    plan_path = ROOT/'ROOT-plan-v1.json'
    raw = plan_path.read_bytes()
    check((sha(raw), len(raw)) ==
          ('91768edb503601d093fb9e0d0470d2036e35e2617887995aa65cb5c200ef6b13', 6932), 'frozen actual plan')
    plan = json.loads(raw)
    for group in ('sources', 'inputs', 'reviews'):
        for ref in plan[group].values():
            pin(ref)
    for name in ('runtime', 'source_contract', 'family_contract', 'family_peer', 'protocol_choice', 'ROOT_authorization'):
        pin(plan[name])
    owned, external = ROOT/'training-owned-v1', ROOT/'training-external-v1'
    body = wire(owned/'response.jsonl')
    obs, native = load(external/'observation.json'), load(external/'native-terminal.json')
    once, bracket = load(external/'ONCE.json'), load(ROOT/'ROOT-tool-bracket-v1.json')
    receipt = load(external/'meter-stdout.txt')
    for item in (body, obs, once, receipt):
        check(item['invocation_id'] == plan['invocation_id'], 'actual invocation binding')
    check(body['plan'] == {'sha256': sha(raw), 'bytes': len(raw)}, 'body plan binding')
    for item in (obs, once):
        check(item['plan_sha256'] == sha(raw) and item['plan_bytes'] == len(raw), 'external plan binding')
    for name in ('sources', 'inputs', 'limits', 'purpose', 'resource_rule'):
        check(body[name] == plan[name], 'same actual ' + name)
    check(body['status'] == 'COMPLETE_TRAINING_PENDING_EXTERNAL', 'complete training wire')
    check(native['all_reaped'] and native['error'] is None and
          not native['interrupted'] and not native['cancellation_forwarded'], 'true terminal without interruption')
    check(native['wait4_status'] == native['caller_returncode'] == obs['meter_returncode'] ==
          obs['probe_returncode'] == bracket['exit_code'] == 0, 'all actual terminal exits zero')
    check(native['wait4_pid'] == native['caller_pid'], 'native wait4 exact worker')
    peak = native['caller_kernel_peak_bytes']
    check(peak == native['wait4_usage'][2] and 0 < peak <= plan['limits']['aggregate_owned_bytes'],
          'single owned native terminal peak fits unchanged512MiB')
    launch, terminal, probe = (native['caller_launch_began_ns'], native['caller_terminal_observed_ns'],
                                obs['postterminal_native_probe_ns'])
    check(launch <= body['joint_began_ns'] < terminal <= probe and
          body['joint_deadline_ns'] - body['joint_began_ns'] == 20000000000,
          'one inherited native20s deadline and actual terminal ordering')
    check(0 < probe-launch < 20000000000, 'strict native launch-to-postprobe20s')
    check(native['caller_kernel_elapsed_ns'] == terminal-launch, 'native terminal elapsed exact')
    check('session_id' not in bracket and 0 <= bracket['end_ms']-bracket['start_ms'] < 60000 and
          bracket['wall_time_seconds'] < 60 and bracket['end_ms']-bracket['start_ms'] + 1000 < 90000,
          'complete actual tool Date bracket and original60/90+1 gates')
    check((external/'meter-stderr.txt').read_bytes() == (external/'postterminal-probe-stderr.txt').read_bytes() == b'',
          'whole stderr empty')
    check(int((external/'postterminal-probe-stdout.txt').read_bytes()) == probe, 'actual native probe bytes')
    check(receipt['pending_external'] is True and receipt['response'] ==
          {k: record(owned/'response.jsonl')[k] for k in ('sha256','bytes')}, 'whole final response receipt')
    expected = []
    for item in receipt['output_inventory']:
        ref = record(owned/item['path'])
        check({**ref, 'path': item['path']} == item, 'whole owned file:' + item['path'])
        expected.append(item['path'])
    check(sorted(expected) == sorted(p.name for p in owned.iterdir()) and len(expected) == 5, 'complete five-file inventory')
    check(body['output_inventory'] == receipt['output_inventory'][:-1], 'response four-file inventory')
    donor, library, controls, intake = [load(owned/n) for n in
        ('donor.json','mined-library.json','controls.json','intake-record.json')]
    check(intake['sources'] == plan['sources'] and intake['inputs'] == plan['inputs'] and
          intake['plan_sha256'] == sha(raw) and not intake['large_Q_files_read'] and
          intake['recipient_instances'] == 0, 'narrow donor intake scope')
    candidate = json.loads(pin(plan['inputs']['checked_candidate']))
    authority = json.loads(pin(plan['inputs']['original_authority']))
    producer = wire(plan['inputs']['searched_producer_response']['path'])
    previous = wire(plan['inputs']['checked_verifier_response']['path'])
    check(donor['commands'] == candidate['commands'], 'same actually searched primitive command word')
    check(donor['origin']['binding'] == candidate['binding'] == authority['binding'], 'same original logical authority')
    check(donor['origin']['producer_origin'] == candidate['origin'], 'same admitted searched origin')
    decl = authority['declaration']
    check(donor['context'] == {n: decl[n] for n in ('ordered_Gamma','parameters','target','theory')}, 'same original sequent context')
    commands = donor['commands']
    command_hash = sha(canon(commands))
    check(controls == body['controls'] and [c['id'] for c in controls] == ['corrupt-origin','corrupted-command'] and
          [c['error'] for c in controls] == ['admitted searched origin linkage','exact named original axiom'] and
          all(c['rejected'] is True for c in controls), 'actual two specific negative rejections')
    check(controls[0]['unchanged_commands_sha256'] == controls[1]['original_commands_sha256'] == command_hash and
          controls[1]['original_target_unchanged'] is True, 'controls retain original word and target scope')
    check(library['donor_intake_sha256'] == sha(canon([donor])), 'complete donor intake binding')
    dc = library['donor_checks']
    check(len(dc) == 1 and dc[0]['donor_id'] == donor['id'], 'one admitted actual training donor')
    fresh = dc[0]['independent_word_check']
    cert = fresh['underlying_receipt']
    check(fresh['completed'] and fresh['logical_accepted'] and fresh['original_target_primary_accepted'] and
          cert['completed'] and cert['original_Gamma_target_sequent_accepted'], 'fresh original closed-target word check')
    old_cert = previous['validation']['certificate']
    for key in cert:
        if key != 'elapsed_seconds_before_final_guard':
            check(cert[key] == old_cert[key], 'fresh saved certificate same:' + key)
    check(cert['commands_sha256'] == command_hash and cert['target'] == donor['context']['target'] and
          cert['original_ordered_Gamma'] == [] and cert['parameters'] == donor['context']['parameters'], 'fresh full original context')
    check(cert['essential_rows'] == list(range(len(commands))) and len(cert['rows']) == len(commands), 'all primitive proof rows essential')
    for i, (row, command) in enumerate(zip(cert['rows'],commands)):
        refs = ([command['antecedent'],command['implication']] if command['rule'] == 'mp' else
                [command['source']] if command['rule'] == 'generalize' else [])
        check(row['row'] == i and row['rule'] == command['rule'] and row['formula_sha256'] == sha(canon(command['formula'])) and
              row['ordered_prior_rows'] == refs and all(r < i for r in refs), 'saved primitive row/reference:' + str(i))
    census, families = library['donor_census'], library['families']
    check([r['root'] for r in census] == list(range(len(commands))) and all(r['donor_id'] == donor['id'] for r in census),
          'complete frozen donor-root census')
    eligible = [r for r in census if r['reason'] == 'eligible']
    check(len(eligible) == body['eligible_root_count'] and len(census) == body['root_count'] and
          len(families) == body['selected_family_count'] <= 1 and bool(families) == bool(eligible), 'derived census and first-eligible selection count')
    for family in families:
        shape = family['shape']
        shape_hash = sha(canon(shape))
        check(family['family_id'] == 'atomic-context-family-' + shape_hash and
              eligible[0]['shape_sha256'] == shape_hash, 'selected first eligible family identity')
        roles = family['donor_role_terms']
        def ground(value):
            if isinstance(value, list):
                if len(value) == 2 and value[0] == 'family-term':
                    return roles[value[1]]
                if value == ['family-hole']:
                    return ['var', family['donor_hole']]
                if value == ['family-hole-name']:
                    return family['donor_hole']
                return [ground(v) for v in value]
            if isinstance(value, dict):
                return {k:ground(v) for k,v in value.items()}
            return value
        external_rows, member_rows = family['ordered_external_command_indices'], family['body_command_indices']
        check(member_rows[-1] == eligible[0]['root'] and family['donor_commands_sha256'] == command_hash,
              'selected donor cluster row binding')
        check([ground(v) for v in shape['input_receptors']] == [commands[r]['formula'] for r in external_rows] and
              ground(shape['output']) == commands[member_rows[-1]]['formula'], 'literal family receptor/output grounding')
        ports = {'input:equality':external_rows[0], 'input:formula':external_rows[1]}
        for j, (member, row_index) in enumerate(zip(shape['members'], member_rows)):
            command = commands[row_index]
            witness = {k:v for k,v in command.items() if k not in ('antecedent','implication')}
            check(ground(member['witness']) == witness, 'literal abstract member grounding:' + str(j))
            refs = [command['antecedent'],command['implication']] if command['rule'] == 'mp' else []
            check([ports[p] for p in member['ordered_ports']] == refs, 'literal ordered family ports:' + str(j))
            ports['member:' + str(j)] = row_index
    for key in ('ROOT_library_admitted','ROOT_resource_accepted','recipient_accepted','new_theorem_claimed',
                'point_state_accepted','trajectory_accepted','native_accepted','full24_accepted','RL_accepted','advantage_claimed'):
        check(body[key] is False, 'no unearned claim:' + key)
    refs = [record(p) for p in sorted(owned.iterdir())] + [record(p) for p in sorted(external.iterdir())]
    result = {'schema':'ROOT-atomic-family-donor-disposition-v1','invocation_id':plan['invocation_id'],
        'scope':'Fresh closed-target donor recheck, two negative controls and complete training root census with literal donor-grounded family extraction',
        'donor_stage_accepted':True,'resource_accepted':True,'library_admitted':False,'recipient_accepted':False,
        'new_theorem_claimed':False,'RL_accepted':False,'GCTS_advantage_claimed':False,'goal_complete':False,
        'native_launch_to_postprobe_ns':probe-launch,'native_caller_elapsed_ns':native['caller_kernel_elapsed_ns'],
        'native_single_worker_peak_bytes':peak,'tool_date_elapsed_ms':bracket['end_ms']-bracket['start_ms'],
        'prior_training_ns':body['prior_training_launch_to_postprobe_ns'],
        'first_use_training_plus_mining_ns':body['prior_training_launch_to_postprobe_ns']+probe-launch,
        'cost_scope':'Sum of two separately budgeted actuals; not one20s experiment and not transfer/speed evidence',
        'roots':len(census),'eligible_roots':[r['root'] for r in eligible], 'selected_families':len(families),
        'selected_family_body_rows':[f['body_command_indices'] for f in families],
        'reconciliation':'Saved bytes and literal term/port reconstitution; no Source functions or independent semantic/trajectory replay',
        'limitations':['Human-chosen three-rule mining grammar after donor observation','No universal family theorem or current-state recipient check',
                       'Fixed Source with no descendants, scoped native ABI; no hostile OS/VM guarantee'],
        'checks':checks,'evidence':refs}
    with (ROOT/'ROOT-training-disposition-v1.json').open('xb') as stream:
        stream.write(json.dumps(result,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('checks','evidence')},sort_keys=True))


if __name__ == '__main__':
    main()
