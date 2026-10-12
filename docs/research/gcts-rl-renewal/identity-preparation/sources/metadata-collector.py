"""Read saved scalar diagnostics/resource metadata only; never catalog records."""
import gzip
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUT = HERE / 'train-pa-right-zero-preparation-v1'
PUBLIC = ROOT / 'docs/research/gcts-rl-renewal/identity-preparation'


def read(path):
    return json.loads(Path(path).read_bytes())


def pin(path):
    path = Path(path)
    h = hashlib.sha256(); length = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); length += len(block)
    return dict(path=str(path.relative_to(ROOT)), sha256=h.hexdigest(), bytes=length)


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


def label(value, length, alphabet):
    return type(value) is str and 1 <= len(value) <= length and all(c in alphabet for c in value)


def main():
    decision = read(HERE / 'preparation-ROOT-final-decision-v1.json')
    owner = read(HERE / 'preparation-owner-v1/provisional-terminal-v1.json')
    post = read(HERE / 'preparation-owner-v1/post-write-observation-v1.json')
    accepted = decision['ROOT_final_accepted'] is True
    assert owner['owned_leftovers'] == []
    assert owner['all_direct_children_terminal_and_reaped'] is True
    assert owner['cleanup_errors'] == [] and owner['cancelled'] is False
    receipt_path = OUTPUT / 'preparation-result-v3.json'
    receipt = read(receipt_path) if receipt_path.exists() else None
    if accepted:
        assert all(decision['predicates'].values())
        assert owner['worker_returncode'] == 0
        assert receipt and receipt['stage_completed'] is True
    else:
        assert not all(decision['predicates'].values())
    completed_trace = bool(receipt and receipt.get('stage_completed') is True)
    trace = OUTPUT / 'producer-diagnostics-v1.jsonl'
    raw = trace.read_bytes(); assert len(raw) <= 1048576
    complete_raw = raw[:raw.rfind(b'\n') + 1]
    tail = raw[len(complete_raw):]
    lines = complete_raw.splitlines(keepends=True); assert len(lines) <= 1024
    events = []; elapsed = 0.0; emitter = None
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/'
    for index, line in enumerate(lines):
        assert len(line) <= 4096 and line.endswith(b'\n')
        item = json.loads(line)
        assert set(item) == {'schema','index','emitter_pid','worker_elapsed_seconds','event'}
        assert item['schema'] == 'compact-preparation-producer-diagnostic-record-v1'
        assert type(item['index']) is int and item['index'] == index
        assert type(item['emitter_pid']) is int and item['emitter_pid'] > 0
        emitter = item['emitter_pid'] if emitter is None else emitter
        assert item['emitter_pid'] == emitter
        stamp = item['worker_elapsed_seconds']
        assert type(stamp) in (int,float) and math.isfinite(stamp) and stamp >= elapsed
        elapsed = stamp; event = item['event']
        assert set(event) == {'phase','milestone','counters'}
        assert label(event['phase'],80,alphabet) and label(event['milestone'],80,alphabet)
        assert type(event['counters']) is dict and len(event['counters']) <= 12
        for name,value in event['counters'].items():
            assert label(name,64,alphabet.replace('/',''))
            assert type(value) is int and 0 <= value < 1 << 64
        events.append(dict(index=index,worker_elapsed_seconds=stamp,event=event))
    assert events and (not completed_trace or not tail)
    if completed_trace:
        assert events[-1]['event']['milestone'] == 'receipt_serialization_begin'
    rows = [x['event']['counters']['row'] for x in events if x['event']['milestone']=='factor_row_closed']
    assert rows == list(range(len(rows))) and len(rows) <= 24
    if accepted: assert rows == list(range(24))
    with gzip.open(HERE / 'preparation-owner-v1/owned-ownership-ledger-v1.json.gz','rt') as stream:
        ledger = json.load(stream)
    assert len(ledger['samples']) == owner['sampled_observations']
    assert ledger['leftovers'] == {}
    assert {str(emitter)} <= {str(pid) for pid in ledger['final_retained_births']}
    samples = [{k:s[k] for k in ['seconds','owned_rss_bytes','combined_bytes','ROOT_peak_bytes','observer_peak_bytes']} for s in ledger['samples']]
    def event(phase,milestone):
        found = [x for x in events if x['event']['phase']==phase and x['event']['milestone']==milestone]
        assert len(found) == 1
        return found[0]
    spans = []
    for title,start,end in [
        ('Equality scheme generation',('equality_product','begin'),('equality_product','complete')),
        ('Formula ordering and registry',('formula_registry','begin'),('formula_registry','complete')),
        ('Recipe sorting and identity generation',('recipe_identity','begin'),('recipe_identity','complete')),
        ('Syntax-node serialization',('nodes','begin'),('nodes','complete')),
        ('Catalog decoder setup',('worker','decoder_begin'),('worker','decoder_ready')),
        ('Initial point-graph setup',('worker','graph_begin'),('worker','graph_ready'))]:
        first,last = event(*start),event(*end)
        spans.append(dict(title=title,start_index=first['index'],end_index=last['index'],
            start_seconds=first['worker_elapsed_seconds'],end_seconds=last['worker_elapsed_seconds'],
            seconds=last['worker_elapsed_seconds']-first['worker_elapsed_seconds'],
            scope='Same emitter-local wall time between markers, including diagnostics; not isolated CPU cost.'))
    artifacts = [pin(p) for p in sorted(OUTPUT.rglob('*')) if p.is_file()]
    names = {Path(p['path']).name for p in artifacts}
    assert {'producer-diagnostics-v1.jsonl','catalog-v1.json','nodes-v1.jsonl.gz','formulas-v1.u64le.bin','recipes-v1.bin'} <= names
    if accepted: assert 'preparation-result-v3.json' in names and 'full-preparation-evidence-v1.json.gz' in names
    private = dict(schema='ROOT-identity-saved-metadata-v1',status='accepted_complete_preparation_pending_independent_catalog_audit' if accepted else 'UNKNOWN_whole_preparation_no_dependent_activation',
        original_trace=pin(trace),complete_JSON_lines=len(lines),incomplete_tail_bytes=len(tail),
        incomplete_tail_sha256=hashlib.sha256(tail).hexdigest(),captured_after_worker_reap=True,
        producer_trace_completed_receipt=completed_trace,complete_preparation=accepted,
        raw_catalog_artifacts_present=True,independent_catalog_qualified=False,
        event_projection=events,observed_factor_rows=rows,spans=spans,
        owner_provisional=pin(HERE/'preparation-owner-v1/provisional-terminal-v1.json'),
        ROOT_resource_decision=pin(HERE/'preparation-ROOT-final-decision-v1.json'),
        artifacts=artifacts,artifact_total_bytes=sum(x['bytes'] for x in artifacts),
        compiler_attempts=1,independent_scientific_audits=0,target_searches=0,new_proofs=0,new_RL_training=False,
        native_queries=0,all_five_qualification=False,scientific_calls_by_collector=0)
    save(HERE / 'ROOT-saved-telemetry-metadata-v1.json',private)
    PUBLIC.mkdir()
    public = dict(schema='public-identity-progress-privacy-view-v1',
        status=private['status'],projection_of=pin(HERE/'ROOT-saved-telemetry-metadata-v1.json'),
        original_trace=pin(trace),projection_notes='Every complete scalar event and numeric ownership sample retained. Emitter process ID, ownership birth identities and absolute host paths omitted. Trace completion and ROOT preparation acceptance are explicit below; producer counters are diagnostic observations, not independently licensed counts.',
        events=events,spans=spans,observed_factor_rows=rows,raw_trace_complete_lines=len(lines),
        raw_trace_incomplete_tail_bytes=len(tail),producer_trace_completed_receipt=completed_trace,
        raw_catalog_artifacts_present=True,independent_catalog_qualified=False,
        samples=samples,owner_observation={k:owner[k] for k in ['peak_bytes','ROOT_peak_bytes','worker_kernel_peak_bytes','observer_peak_bytes','direct_children_peak_sum_bytes','worker_returncode','sampled_observations','max_sampled_owned_rss_bytes','elapsed_before_write_seconds','error','cleanup_errors','cancelled','owned_leftovers','resource_gate_accepted','all_direct_children_terminal_and_reaped']},
        owner_post_write={k:post[k] for k in ['resource_gate_accepted','elapsed_seconds','peak_bytes','limits']},
        caller_elapsed_seconds=decision['caller_elapsed_seconds'],resource_predicates=decision['predicates'],
        ROOT_final_accepted=accepted,limits=decision['limits'],artifacts=artifacts,
        compiler_attempts=1,independent_scientific_audits=0,target_searches=0,new_proofs=0,new_RL_training=False,
        native_queries=0,all_five_qualification=False,goal_active=True)
    save(PUBLIC/'saved-progress-view-v1.json',public)
    print(json.dumps(dict(metadata=pin(HERE/'ROOT-saved-telemetry-metadata-v1.json'),
        public_view=pin(PUBLIC/'saved-progress-view-v1.json'),events=len(events),samples=len(samples),
        peak_MiB=owner['peak_bytes']/(1<<20),spans=spans,artifact_files=len(artifacts),
        artifact_bytes=private['artifact_total_bytes'],scientific_calls=0)))


if __name__ == '__main__':
    main()
