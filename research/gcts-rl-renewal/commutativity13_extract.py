"""Read-only exact projection of every prior fixed policy event for conformance."""
import argparse
import gzip
import hashlib
import json
import resource
import time
from pathlib import Path
from commutativity_cluster_intern_v3 import load
from commutativity13_json import save, encoded

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/commutativity13-20261011'
OLD = ROOT / '.gcts-active/commutativity-cluster-search-20261011'


def main():
    began = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument('name', choices=('fixed-r1', 'fixed-r2'))
    args = parser.parse_args()
    plan = json.loads((OUT / 'preflight-plan.json').read_text())
    for path, h in {**plan['source_sha256'], **plan['input_sha256']}.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != h:
            raise ValueError('frozen projection input/source ' + path)
    raw = load(OLD / (args.name + '-search.json.gz'))
    value = dict(case=raw['case'], observation=raw['observation'], events=raw['search']['events'],
                 original_trace_sha256=hashlib.sha256((OLD / (args.name + '-search.json.gz')).read_bytes()).hexdigest(),
                 native_target_queries=0, target_searches=0,
                 scope='All prior fixed-event contexts/pools/features/scores/work, read only for exact implementation correspondence. No prior ordinary word or witnesses are read. Not policy training.')
    h = hashlib.sha256(encoded(value['events'])).hexdigest()
    save(OUT / (args.name + '-events.json.gz'), value)
    replay = json.loads(gzip.decompress((OUT / (args.name + '-events.json.gz')).read_bytes()))
    if hashlib.sha256(encoded(replay['events'])).hexdigest() != h:
        raise ValueError('complete event projection serialization')
    receipt = dict(status='complete_exact_event_projection_pending_independent_audit', id=args.name,
                   events=len(value['events']), events_sha256=h, original_trace_sha256=value['original_trace_sha256'],
                   seconds=time.perf_counter() - began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if receipt['seconds'] > 180 or receipt['peak_rss_bytes'] > 536870912:
        receipt['status'] = 'unknown_projection_resource_budget'
    (OUT / (args.name + '-events-receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
