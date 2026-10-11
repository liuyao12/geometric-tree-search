"""Prospective independent tiny artifact audit; owner/plan activation required.

Imports only our independent oracle/records/replay sources. It does not import
the producer, geometry graph, engine or native checker. Descriptor bodies and
fixture symbols/palettes/boundaries are independently authored from pinned
literal source; self-hashed descriptors are never treated as admission.
"""
import argparse
import copy
import hashlib
import itertools
import json
import signal
import time
from pathlib import Path
from independent_lifecycle_records_v1 import expected_descriptor, need, json_equal
from independent_lifecycle_replay_v2 import (
    SnapshotController, check_record, graph_data, current_hint, replay_dfs, key_data,
)
from lifecycle_oracle_v2 import key, integer, sha, canonical, parent_after_child

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
D=ROOT/'.gcts-active/hilbert-cluster-lifecycle-20261011'
P=['pred','P',[]];Q=['pred','Q',[]];R=['pred','R',[]];IMP=['imp',P,Q]
FORMULAS=[P,Q,IMP,R]


def pin(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    return dict(path=str(p.relative_to(ROOT)),sha256=h.hexdigest(),bytes=p.stat().st_size)


def recipe(name,formula,premises=(),rule='fixture_zero'):
    return dict(id='synthetic-'+name,primitive_witness=dict(rule=rule,formula=formula,fixture_name=name),
                ordered_premise_formulas=list(premises))


PALETTE=[recipe('p-first',P),recipe('q',Q),recipe('imp',IMP),recipe('p-second',P),
    recipe('literal-mp',Q,[P,IMP],'mp'),recipe('equal-ordered-port-fixture',Q,[P,P],'opaque_pair')]
DFS_PALETTE=[recipe('irrelevant-r-first',R),recipe('p',P),recipe('imp',IMP),recipe('mp',Q,[P,IMP],'mp')]


def fixture_binding(record):
    height=len(record['state']['graph']['roots']);name=record['name']
    need(height in (3,4),'declared toy boundary')
    need(json_equal(record['formulas'],FORMULAS),'exact source symbols and registry')
    need(json_equal(record['recipes'],DFS_PALETTE if height==4 else PALETTE),'full exact authored primitive palette')
    need(json_equal(record['state']['graph']['roots'],[0,0,0,5] if height==4 else [0,0,0]),'exact generation roots')
    marks={(1,r):-1 for r in range(1-height,0)}
    if height==4:marks[1,3]=1
    elif name=='assigned-zero-remote-offset':marks[2,2]=0
    elif name.startswith('exhaustive-formula-state-'):
        index=int(name.rsplit('-',1)[1]);need(0<=index<64,'all 64 formula states')
        values=list(itertools.product((None,0,1,2),repeat=3))[index]
        marks.update(((1,row),v) for row,v in enumerate(values) if v is not None)
    need(json_equal(record['initial_marks'],[[*p,v] for p,v in sorted(marks.items())]),'exact source initial marks including zero')


def terminal_bindings(plan):
    receipt=json.loads((D/'attempt-03/fixtures-lifetime-v1.json').read_bytes())
    supervision=json.loads((D/'attempt-03/fixtures-supervision-v1.json').read_bytes())
    need(receipt['status']=='passed_authored_tiny_lifecycle_full_lifetime','producer complete resource qualification')
    need(supervision['status']=='passed_bounded_authored_tiny_lifecycle','producer complete terminal fixture gate')
    need(receipt['plan_sha256']==pin(D/'plan-attempt-03.json')['sha256'],'exact producer plan binding')
    need(receipt['supervision_sha256']==pin(D/'attempt-03/fixtures-supervision-v1.json')['sha256'],'exact terminal metadata')
    need(receipt['process_return_code']==0 and receipt['supervisor_wait_reaped'] is True,'terminal supervisor reaped')
    need(supervision['exit_code']==0 and supervision['owned_child_terminal_wait_reaped'] is True,'terminal producer child reaped')
    need(receipt['conservative_host_peak_bytes']<=536870912 and receipt['cumulative_tiny_seconds']<=60,'unchanged cumulative producer resources')
    need(abs(receipt['prior_failed_attempt_seconds']-.595534332)<1e-9,'both prior failed stages retained and charged')
    return receipt,supervision


def operations_check(outcome,records):
    compared=0
    byepoch={r['state']['authority_epoch']:r for r in records}
    seen={sha(r['state']):r['state'] for r in records}
    # Exact captured pre/post states can be joined by checkpoint semantic hash,
    # even when inspection has resynchronized revision between transactions.
    seen.update({sha(x['before']):x['before'] for x in outcome['controlled_operations']})
    for x in outcome['controlled_operations']:
        before,after=x['before'],x['after'];r=byepoch[before['authority_epoch']]
        c=SnapshotController(r,outcome['authorities'],initial=before)
        kind=x['kind'];payload=x['payload']
        if kind in ('scheduler-step','scheduler-forced-step','scheduler-shared-step'):
            c.apply(payload)
        elif kind=='catalog-controlled-step-and-resync':c.apply(payload,scheduler=False)
        elif kind=='fixture-controlled-exclusion-not-proof':c.exclude(payload,resync=False)
        elif kind=='whole-resync':c.resync()
        elif kind=='paired-rollback':
            need(len(payload)==5 and payload[-1] in seen,'known exact paired rollback destination')
            expected=seen[payload[-1]]
            need(json_equal(expected,after),'restored checkpoint state rather than newly recomputed revival')
            need(payload[3]==sha(after['descriptor_ids']) and payload[2]==after['hint_revision'],'fixed registry/revision')
            need(payload[0]==len(after['graph']['order'])+sum(map(len,after['graph']['excluded'])),'unit graph trail checkpoint')
            need(payload[1]==(len(after['hint_states'])+1)*(after['hint_revision']-1),'whole hint trail checkpoint')
            # Independent raw state/body/hint reconstruction at restored point.
            SnapshotController(r,outcome['authorities'],initial=after)
            compared+=1;continue
        else:raise ValueError('unsupported controlled transaction '+kind)
        need(json_equal(c.semantic(),after),'independent full graph and branch-absorbing hint transaction')
        compared+=1
    return compared


def dfs_check(outcome,records):
    need(len(outcome['synthetic_dfs_traces'])==1,'one complete declared DFS series')
    events=outcome['synthetic_dfs_traces'][0]['events']
    starts=[i for i,e in enumerate(events) if e['kind']=='solve_begin']
    need(len(starts)==3,'unknown0/unknown1/complete bounded series')
    r=next(r for r in records if r['name']=='zero-budget-no-exclusion')
    censuses=[]
    for a,b,budget in zip(starts,starts[1:]+[len(events)],[0,1,100]):
        begin=events[a];need(begin['max_attempts']==budget,'exact declared attempt limit')
        need(begin['seconds']==(2 if budget==100 else 1),'same declared toy wall bounds')
        c=SnapshotController(r,outcome['authorities'],initial=begin['state'])
        independent=replay_dfs(c,budget)
        expected=events[a+1:b]
        need(json_equal(independent['events'],expected),'complete independently reconstructed DFS state/decisions/unknown/exhaustion/rollback')
        need(independent['status']==('finite_exact_point_tiling' if budget==100 else 'unknown_budget'),'logical series outcome')
        if budget<100:
            need(json_equal(c.semantic(),begin['state']),'unknown leaves exact parent exclusions/hints unchanged')
            need(not any(e['kind']=='parent_local_exhausted_child_exclusion' for e in expected),'unknown did not authorize exclusion')
        else:
            need(independent['backtracks']==1,'one justified dead child, then complete tiny solution')
            g,s,d=c.graph();need(d[0]=='complete','every required point exactly filled')
            # This is a finite fixture proof-row tiling, not a Hilbert theorem.
            need(all(v==1 for v in s['total'].values()),'exact point occupancy and mark agreement')
        censuses.append(dict(max_attempts=budget,result=independent['status'],events=len(expected),
            attempts=independent['attempts'],independently_exhausted_children=independent['backtracks']))
    return censuses


def mutations_check(outcome,records):
    rejected=[];positives=[]
    r=next(r for r in records if r['name']=='invalid-and-duplicate-root-descriptors')
    c=SnapshotController(r,outcome['authorities'],initial=r['state'])
    good=r['descriptors'][0];authority=outcome['authorities'][good['body_authority_epoch']]
    def descriptor_check(d):return expected_descriptor(d,authority,c.oracle,c.palette,c.placements)
    def reject(name,call):
        try:call()
        except (ValueError,KeyError,IndexError,TypeError):rejected.append(name);return
        raise AssertionError('corruption accepted '+name)
    def rehash(d):d['descriptor_id']='whole-cluster-'+sha({k:v for k,v in d.items() if k!='descriptor_id'});return d
    bykey={key(p['key']):p for p in c.placements}
    for field in ('model_epoch','context_id','formula_registry_sha256','authority_epoch',
                  'primitive_palette_sha256','boundary_sha256','source_bindings_sha256'):
        bad=copy.deepcopy(good);bad['graph_binding'][field]='stale';rehash(bad)
        reject('stale-'+field,lambda bad=bad:descriptor_check(bad))
    for field in ('source_body_sha256','mapped_body_sha256','body_sha256','body_authority_epoch'):
        bad=copy.deepcopy(good);bad[field]='0'*64;rehash(bad)
        reject('altered-'+field,lambda bad=bad:descriptor_check(bad))
    for name,k in [('valid-altered-recipe',(3,1,())),('valid-altered-row',(0,2,()))]:
        bad=copy.deepcopy(good);p=bykey[k];bad['members']=[key_data(k)];bad['full_member_ids']=[p['id']]
        bad['full_identity_preimages']=[p['identity']];bad['aggregate_t']=p['t'];bad['aggregate_m']=p['m'];rehash(bad)
        reject(name+'-fresh-full-identity',lambda bad=bad:descriptor_check(bad))
    for name,modify in [
        ('altered-command',lambda d:d['full_identity_preimages'][0]['primitive_command'].update(template=['pred','forged',[]])),
        ('overcount-t',lambda d:d['aggregate_t'][0].__setitem__(2,2)),
        ('bool-assigned-zero',lambda d:d['aggregate_m'][0].__setitem__(2,False)),
        ('hidden-mark-conflict',lambda d:d['aggregate_m'].append([1,1,1])),
        ('missing-body',lambda d:d.update(body_name='missing')),
        ('missing-dependency',lambda d:d.update(dependency_bindings=[dict(name='missing',body_sha256='0'*64)])),
    ]:
        bad=copy.deepcopy(good);modify(bad);rehash(bad);reject(name,lambda bad=bad:descriptor_check(bad))
    rp=next(r for r in records if r['name']=='ordered-noninjective-receptor-ports')
    q=SnapshotController(rp,outcome['authorities'],initial=rp['state']);d=copy.deepcopy(rp['descriptors'][0])
    need(d['ordered_input_rows']==[0,0] and len(d['ordered_receptor_ports'])==2,'equal receptor multiplicity retained')
    positives.append('noninjective-two-ordered-ports-retained')
    p={key(p['key']):p for p in q.placements}[(5,2,(1,0))]
    d.update(members=[[5,2,[1,0]]],full_member_ids=[p['id']],full_identity_preimages=[p['identity']],aggregate_t=p['t'],aggregate_m=p['m']);rehash(d)
    reject('altered-valid-ordered-refs-with-fresh-identities',lambda:expected_descriptor(d,outcome['authorities'][d['body_authority_epoch']],q.oracle,q.palette,q.placements))
    rr=copy.deepcopy(next(r for r in records if r['name']=='waiting-root'))
    rr['recipes'][4]['ordered_premise_formulas'][1]=['imp',Q,Q]
    # Formula marking geometry alone could be internally consistent, but literal
    # MP and the exact fixture-source palette both independently reject it.
    reject('point-consistent-invalid-literal-mp',lambda:SnapshotController(rr,outcome['authorities'],initial=rr['state']))
    wrong=copy.deepcopy(r);wrong['state']['graph']['marks'][0][-1]=False
    reject('boolean-mark-reference-count',lambda:check_record(wrong,outcome['authorities']))
    wrong=copy.deepcopy(r);wrong['state']['graph']['totals'][0]=False
    reject('boolean-occupancy',lambda:check_record(wrong,outcome['authorities']))
    wrong=copy.deepcopy(r);wrong['complete_domains'][0].pop()
    reject('dropped-complete-fallback-candidate',lambda:check_record(wrong,outcome['authorities']))
    # Branch retirement remains absorbing even when a caller recomputes a legal
    # view after changing selected data without an explicit checkpoint rollback.
    waiting=next(r for r in records if r['name']=='waiting-root');z=SnapshotController(waiting,outcome['authorities'],initial=waiting['state'])
    _,s,d=z.graph();old=dict(status='retired',reason='pending_member_illegal',eligible=[],decision=d,revision=z.revision)
    absorbed=current_hint(z.compiled[0],s,d,z.revision+1,old)
    need(absorbed['status']=='retired' and not absorbed['eligible'],'whole retirement absorbing')
    fresh=current_hint(z.compiled[0],s,d,z.revision+1)
    need(fresh['status']=='waiting','fresh root/paired restored state can become waiting')
    positives.extend(['branch-retirement-absorbing','paired-rollback-fresh-state-distinguished'])
    # Unknown statuses preserve every parent-local exclusion; only actual DFS
    # exhaustion above authorizes an excluded child in a trace.
    _,parent,_=z.graph();attempted=parent['domains'][0,0][0]
    for status in ('unknown_budget','unknown_resource','unknown_cancelled'):
        preserved=parent_after_child(z.oracle,parent,key_data(attempted),status)
        need(preserved['excluded']==parent['excluded'] and preserved['selected']==parent['selected'],'unknown must not prune')
    positives.append('all-unknown-kinds-preserve-parent')
    need(len(rejected)==24,'declared 24 actual corruptions')
    return dict(actual_corruptions_rejected=rejected,positive_semantic_controls=positives,
        scope='Independent adapters exercised on mutated in-memory tiny records. These are separate checks, not reruns of producer fixture tests or production search.')


def main():
    p=argparse.ArgumentParser();p.add_argument('--plan',required=True);args=p.parse_args()
    planpath=Path(args.plan).resolve();plan=json.loads(planpath.read_bytes())
    need(planpath==HERE/'actual-audit-plan-v1.json','only frozen prospective plan')
    need((HERE/'root-activation-v1.json').exists(),'root actual dispatch authorization required')
    activation=json.loads((HERE/'root-activation-v1.json').read_bytes())
    need(activation['plan_sha256']==pin(planpath)['sha256'] and activation['status']=='authorized_by_root_after_independent_source_review','root activation binds plan')
    started=time.perf_counter();signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(TimeoutError('independent tiny audit alarm')));signal.alarm(50)
    for entry in plan['sources']+plan['inputs']:
        need(pin(ROOT/entry['path'])=={k:entry[k] for k in ('path','sha256','bytes')},'exact audit source/input')
    producer_life,_=terminal_bindings(plan)
    outcome=json.loads((D/'attempt-03/fixtures-outcome-v1.json').read_bytes())
    need(outcome['status']=='passed_authored_synthetic_whole_cluster_lifecycle_pending_independent_gate','complete tiny outcome')
    need(outcome['actual_geometry_model_execution'] is False and outcome['geometry_target_searches']==outcome['native_queries']==0 and outcome['new_RL_training'] is False,'same scoped synthetic authority')
    expectedpins=[pin(D/'plan-v1.json'),pin(D/'hilbert_cluster_fixtures_attempt03_v1.py')]
    for epoch,authority in outcome['authorities'].items():
        need(epoch==authority['epoch'],'authority lookup exact')
        need(authority['source_bindings']==expectedpins,'exact complete toy source closure')
    records=outcome['states'];need(len(records)==81,'all 81 controlled state records')
    comparisons=0
    for r in records:
        fixture_binding(r);c=check_record(r,outcome['authorities']);_,s,d=c.graph()
        if r['name']=='invalid-and-duplicate-root-descriptors':
            good=r['descriptors'][0];bad=copy.deepcopy(good)
            bad['dependency_bindings']=[dict(name='missing',body_sha256='0'*64)]
            root=r['state']['root_rejected']
            need(len(root)==2 and [x['registration'] for x in root]==[0,2],'exact invalid/duplicate root registrations')
            need(root[0]['payload_sha256']==sha(bad) and root[1]['payload_sha256']==sha(good),'source-authored root rejection payloads')
            need(root[0]['reason']=='ValueError: whole descriptor differs from frozen body/identity/authority'
                 and root[1]['reason']=='ValueError: duplicate root descriptor identity','exact separately reconstructed root errors')
        else:need(r['state']['root_rejected']==[],'no hidden root descriptor rejection')
        comparisons+=sum(map(len,s['domains'].values()))
        if d[0] in ('forced','branch'):
            ordered=c.ordered()
            need(set(ordered)==set(s['domains'][0,d[1]]) and len(ordered)==len(s['domains'][0,d[1]]),'full fallback census')
    need(comparisons==outcome['complete_raw_candidate_comparisons'],'full candidate comparison count')
    transactions=operations_check(outcome,records);dfs=dfs_check(outcome,records)
    mutations=mutations_check(outcome,records)
    audit=dict(status='passed_independent_tiny_whole_lifecycle_point_body_and_finite_dfs_audit',
        plan_sha256=pin(planpath)['sha256'],outcome_pin=pin(D/'attempt-03/fixtures-outcome-v1.json'),
        complete_states=len(records),complete_candidate_comparisons=comparisons,authority_registries=len(outcome['authorities']),
        exact_source_bindings=expectedpins,controlled_transactions=transactions,complete_dfs_series=dfs,
        actual_corruptions=mutations,producer_total_cumulative_seconds=producer_life['cumulative_tiny_seconds'],
        audit_seconds_before_receipt_write=time.perf_counter()-started,
        scope=['All recorded tiny point domains/body transports/ordered ports/full identities/assigned-zero/generations/graph-hint paired rollback reconstructed independently.',
            'Finite DFS event replay independently establishes every actual excluded child exhaustion; unknown restores parent without exclusion. Retirement is branch-absorbing until explicit paired rollback.',
            'Source registries are authored toy infrastructure. Synthetic zero and opaque-pair rules are nonlogical; this is no searched mathematical theorem or Hilbert/native/Wang/compiler acceptance.',
            'The producer nonfinite-budget and untracked-metadata negative groups have pass records only; source review plus our explicit binding/byte/type corruptions, not independent replay of those unsaved failing calls, is the scope.',
            'No actual geometry model load, target DFS, learned policy/training or native query. Full-language lifecycle remains future gated work.'],
        searches=0,native_queries=0,actual_geometry_models=0,training_episodes=0)
    with (HERE/'actual-audit-result-v1.json').open('x') as f:json.dump(audit,f,indent=2);f.write('\n')


if __name__=='__main__':main()
