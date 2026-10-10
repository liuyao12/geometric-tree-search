"""Bind the compact human reader to independent region and cache audits."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]/'docs/research/gcts-rl-renewal'


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    data = json.loads((DOC/'movable-regions-001.json').read_bytes())
    audit = json.loads((DOC/'movable-regions-audit-001.json').read_bytes())
    cache = json.loads((DOC/'movable-core-cache-001.json').read_bytes())
    if audit['input_sha256'] != digest(DOC/'movable-regions-001.json') or audit['cache_sha256'] != digest(DOC/'movable-core-cache-001.json'):
        raise ValueError("exact audit input")
    if audit['source_sha256'] != digest(HERE/'audit_movable_regions.py'):
        raise ValueError("auditor source")
    for source in (data['sources'], audit['helper_sources']):
        if any(digest(HERE/n) != pin for n, pin in source.items()):
            raise ValueError("frozen source")
    cases = []
    for c in data['cases']:
        runs = {}
        used = set()
        for lane, r in c['runs'].items():
            fields = ('status', 'metrics', 'seconds', 'endpoint', 'point_certificate',
                      'point_assembly_and_check_seconds', 'compile_and_host_check_seconds')
            row = {k: r[k] for k in fields if k in r}
            if lane in ('baseline', 'marked') and r['proof'] is not None:
                for key in r['placements']:
                    if key[1] >= 0:
                        used.add(key[1])
                row.update({k: r[k] for k in ('proof', 'placements', 'tiles', 'tile_generations',
                                              'closing_cluster', 'erased_certificate')})
                row['compiled_request'] = r['compiled']['request']
                if 'deduced' in r:
                    row['deduced_request'] = r['deduced']['request']
                row['frames'] = [dict(kind=f['kind'], point=f['point'], key=f['key'],
                                      domains=[dict(point=d['point'], count=d['count'],
                                                    factors=len(d['blocks']),
                                                    structural=len(d['structural']),
                                                    excluded=len(d['excluded'])) for d in f['domains']])
                                 for f in r['frames']]
            runs[lane] = row
        for item in c['certified']:
            used.update(k[1] for k in item['pair'] if k[1] >= 0)
        fields = ('spec', 'family', 'bindings', 'context_hash', 'build_seconds',
                  'baseline_binding_seconds', 'certification_seconds', 'encoding_seconds',
                  'training_seconds', 'learned_points')
        cases.append(dict({k: c[k] for k in fields}, runs=runs,
                          used_rules={i: c['catalog']['rules'][i] for i in sorted(used)},
                          rules=len(c['catalog']['rules']),
                          certified=[dict(pair=n['pair'], check=n['check'],
                                          subtree_sha256=hashlib.sha256(json.dumps(n['tree'], sort_keys=True, separators=(',', ':')).encode()).hexdigest())
                                     for n in c['certified']]))
    return dict(version='movable-regions-reader-001', family=data['family'], cases=cases,
                seconds=data['seconds'], peak_process_rss_bytes=data['peak_process_rss_bytes'],
                audit=dict(seconds=audit['seconds'], mutations=len(audit['mutations_rejected']),
                           input_sha256=audit['input_sha256']),
                cache=cache)


if __name__ == '__main__':
    (DOC/'movable-regions-reader-001.json').write_text(json.dumps(build(), separators=(',', ':'))+'\n')
