"""Metadata-only ROOT display assembly; no research imports or execution."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent.parent.parent
HERE=Path(__file__).resolve().parent
PUBLIC=ROOT/'docs/research/gcts-rl-renewal/curriculum-platform'
RAW=HERE/'outputs/calibration-result-v1.json'


def read(path):return json.loads(Path(path).read_text())


def pin(path):
    path=Path(path);sha=hashlib.sha256();n=0
    with path.open('rb') as f:
        for block in iter(lambda:f.read(65536),b''):sha.update(block);n+=len(block)
    return dict(path=str(path.relative_to(ROOT)),sha256=sha.hexdigest(),bytes=n)


def write(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')


def main():
    if PUBLIC.exists():raise ValueError('new one-shot reporting namespace')
    result=read(RAW);outer=read(HERE/'outer-reap-v1.json')
    if result['scientific_calls']!=0 or not outer['child_reaped']:raise ValueError('actual finite calibration only')
    PUBLIC.mkdir()
    origins=[];links={}
    groups=[('calibration',HERE),
        ('calibration-review',ROOT/'.gcts-active/curriculum-platform-calibration-independent-review-20261012'),
        ('platform-docs',ROOT/'.gcts-active/curriculum-platform-semantics-source-review-20261012'),
        ('compact-source',ROOT/'.gcts-active/curriculum-compact-wrapper-source-20261012'),
        ('reader-source',ROOT/'.gcts-active/curriculum-platform-reader-source-20261012')]
    for label,base in groups:
        for source in sorted(base.rglob('*')):
            if not source.is_file():continue
            relative=source.relative_to(base);destination=PUBLIC/'evidence'/label/relative
            destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
            if source.read_bytes()!=destination.read_bytes():raise ValueError('exact origin copy')
            origins.append(dict(source=pin(source),public=pin(destination)))
            links[str(source)]=str(destination.relative_to(PUBLIC))
    def href(path):return links[str(Path(path))]
    for name in ('reader.html','reader.js'):
        source=groups[-1][1]/name;destination=PUBLIC/name;shutil.copyfile(source,destination)
        origins.append(dict(source=pin(source),public=pin(destination)))
    # First UNKNOWN and all previous public evidence remain immutable; bind
    # the existing live checkpoint instead of republishing its large raw audit.
    previous=ROOT/'.gcts-active/curriculum-gates-progress-20261012/first-static-resource-unknown-disposition-v1.json'
    dest=PUBLIC/'evidence/original-resource-UNKNOWN.json';shutil.copyfile(previous,dest)
    origins.append(dict(source=pin(previous),public=pin(dest)))
    cases=[];memory=[];actors=[]
    coordinator_pid=result['cases'][0]['pid']
    # Actual coordinator identity is the exact closed frame saved by external.
    external=read(HERE/'external-receipt-v1.json');coordinator_pid=external['coordinator_pid']
    actors.append(dict(label='Calibration external supervisor',role='launcher',pid=outer['child_pid'],
        parent_pid=None,scope_note='Direct child of ROOT entry; parent PID was not saved.',evidence_href=href(HERE/'outer-reap-v1.json')))
    actors.append(dict(label='Calibration coordinator',role='owner',pid=coordinator_pid,parent_pid=outer['child_pid'],
        scope_note='Source-owned direct child of the recorded external supervisor; all actual case handles reaped.',evidence_href=href(HERE/'external-receipt-v1.json')))
    labels=['Smaller single leaf','Larger single leaf','Smaller parent with larger child',
            'Larger parent with smaller child','Smaller parent with two sequential larger children']
    for index,case in enumerate(result['cases']):
        children=(case['parent_receipt'] or {}).get('children',[])
        observers=[o for o in result['observers'] if o['case']==case['name']]
        own=case['actor_frame']['SELF_ru_maxrss_raw'];rolled=case['wait4_raw']['ru_maxrss']
        sampled=max(sum(row['RSS_1024_byte_units']*1024 for row in o['rows']) for o in observers)
        bars=[dict(label='Actor SELF peak after receipt close',value_bytes=own,kind='self'),
              dict(label='Actor terminal wait4 peak (may include descendants)',value_bytes=rolled,kind='rolled'),
              dict(label='Saved simultaneous actor/child RSS sample sum',value_bytes=sampled,kind='sample')]
        for bar in bars:bar['display_fraction']=bar['value_bytes']/134217728
        note=('No nested child: the leaf SELF and direct wait4 peaks agree.' if not children else
              'Terminal wait4 is the maximum of the parent SELF and reaped child peaks; it does not sum simultaneous process RSS.')
        if len(children)>1:note+=' The cumulative child peak remains the larger of the two sequential leaf peaks.'
        cases.append(dict(id=case['name'],label=labels[index],bars=bars,note=note,
            checks_note='Observed success frames, direct terminal reaping and declared PS ancestry agree. Finite evidence only; failure paths and arbitrary concurrency are not empirically proved.',
            evidence_href=href(RAW)))
        actors.append(dict(label=labels[index],role='calibration_worker',pid=case['pid'],parent_pid=coordinator_pid,
            scope_note='Non-scientific actor; exact terminal handle reaped.',evidence_href=href(RAW)))
        for child in children:
            actors.append(dict(label='Nested calibration leaf in '+case['name'],role='calibration_worker',pid=child['pid'],
                parent_pid=case['pid'],scope_note='Direct child recorded and reaped by this actor.',evidence_href=href(RAW)))
        for label,value,method,scope in [('SELF',own,'getrusage SELF','Actor only, after artifact close'),
            ('terminal',rolled,'direct wait4','Descendant-inclusive maximum for parent actors'),
            ('sample',sampled,'ps RSS sum','Unique actual actor/child PIDs; finite sample may miss peaks')]:
            memory.append(dict(label=case['name']+' '+label,method=method,value_bytes=value,original_value=value,
                original_unit='bytes; PS rows converted using their documented 1024-byte unit',scope_note=scope,evidence_href=href(RAW)))
    for observation in result['observers']:
        actors.append(dict(label='Observer for '+observation['case'],role='leaf_observer',pid=observation['pid'],
            parent_pid=coordinator_pid,scope_note='Separate owned pinned PS command, closed streams and terminal wait4.',evidence_href=href(RAW)))
    memory.append(dict(label='Saved retrospective calibration envelope',method='Distinct role maxima plus declared reserve',
        value_bytes=outer['complete_distinct_role_estimate_bytes'],original_value=outer['complete_distinct_role_estimate_bytes'],
        original_unit='bytes',scope_note='Source-computed saved total; runner SELF summand was not individually saved. Independent complete resource recomputation remains unavailable; no hard OS cap.',
        evidence_href=href(HERE/'outer-reap-v1.json')))
    view=dict(schema='ROOT-assembled-curriculum-platform-reader-v1',
        status_note='Five fresh non-scientific cases and six owned observers completed. Finite unit/max-rollup observations pass; independently complete resource qualification remains unknown. No new proof, search, RNG or learning.',
        actors=actors,memory_observations=memory,calibration_cases=cases,
        phases=[dict(label='Original first donor static audit',version='Original frozen curriculum; donor-two-guards',
            semantic_status='pass',resource_status='unknown',root_full_owned_seconds=14.004124667,
            disposition_note='Raw semantic pass; original full resource failure preserved. No rerun or discount.',evidence_href='evidence/original-resource-UNKNOWN.json'),
            dict(label='Fresh non-scientific calibration',version='Calibration V4, outer runner V2, fixed five cases',
            semantic_status='pass',resource_status='unknown',root_full_owned_seconds=outer['full_external_process_seconds'],
            disposition_note='Clock covers external creation through reap. Saved retrospective estimate passes its source check; missing raw runner SELF prevents independently complete resource recomputation. Entry-runner final receipt/exit clock remains additional.',
            evidence_href=href(HERE/'outer-reap-v1.json'))],
        milestone=dict(calibration=dict(status='pass',note='Actual saved unit and descendant-max observations; finite scope only.',evidence_href=href(RAW)),
            next_donor=dict(status='not_run',note='All four original remaining contexts are still unexecuted. Compact wrappers are source only; platform adapter, outer binding and review remain required.'),
            ROOT_qualified=True,claim_basis='actual_calibration',
            note='Milestone is actual finite calibration evidence. It is not complete resource qualification, a mathematical theorem, policy training or benchmark superiority.'),
        preserved_original=dict(first_donor_resource='UNKNOWN',first_static_conservative_bytes=1023344640,
            frozen_memory_cap_bytes=536870912,remaining_contexts_executed=0,all_five_qualified=False),
        costs=dict(external_creation_to_reap_seconds=outer['full_external_process_seconds'],
            entry_runner_seconds_before_receipt=outer['runner_seconds_before_receipt'],
            entry_runner_final_receipt_exit_clock=None,report_review_and_publication_cost=None,
            saved_retrospective_envelope_bytes=outer['complete_distinct_role_estimate_bytes'],
            complete_resource_recomputation_qualified=False),
        evidence=[dict(label='Exact public origins',href='origins.json'),
            dict(label='Raw finite calibration result',href=href(RAW)),
            dict(label='Full external lifetime and postclose frame',href=href(HERE/'outer-reap-v1.json')),
            dict(label='Independent calibration source review',href=href(groups[1][1]/'review-v4-source-pass-v1.json')),
            dict(label='Independent actual saved-record review',href=href(groups[1][1]/'actual-review-v1.json')),
            dict(label='Platform primary-source findings',href=href(groups[2][1]/'conclusions-v1.json')),
            dict(label='Compact wrappers source-only handoff',href=href(groups[3][1]/'integration-v2.json'))])
    write(PUBLIC/'view.json',view);write(PUBLIC/'origins.json',dict(schema='exact-platform-report-origins-v1',copies=origins))
    # This source is a projection only. Independently reconciled raw records
    # retain authority; no display field creates a scientific qualification.
    write(HERE/'reader-assembly-v2.json',dict(status='metadata_only_reader_assembled',actual_calibration_rerun=False,
        scientific_calls=0,exact_origin_copies=len(origins),view=pin(PUBLIC/'view.json'),origins=pin(PUBLIC/'origins.json'),
        files=[pin(p) for p in sorted(PUBLIC.rglob('*')) if p.is_file()]))
    print(json.dumps(dict(cases=len(cases),actors=len(actors),memory_rows=len(memory),exact_copies=len(origins))))


if __name__=='__main__':main()
