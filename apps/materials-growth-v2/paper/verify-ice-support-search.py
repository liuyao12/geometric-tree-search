"""Verify supported ice search states against the original registered model.

This independently checks final t/m values, inventory and connectivity. Prior
pruning/graph certificates are hash-bound dependencies, not re-proved here.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys

def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

original_path, pruned_path, graph_path, pruning_check_path, graph_check_path, cover_path, search_path, kernel_path, output = sys.argv[1:]
original, pruned, data = map(read, (original_path, pruned_path, graph_path))
assert original['sourceHashes']['cover'] == sha(cover_path)
pc, gc = map(read, (pruning_check_path, graph_check_path))
assert pc['inputModelHash'] == sha(original_path)
assert pc['outputModelHash'] == sha(pruned_path) == gc['inputModelHash']
assert gc['outputModelHash'] == sha(graph_path)
assert gc['pruningCheckHash'] == sha(pruning_check_path)
assert original['clouds'] == pruned['clouds'] == data['clouds']
assert len(original['models']) == len(pruned['models']) == len(data['models'])
spec = importlib.util.spec_from_file_location('cloud', Path(__file__).with_name('portable-cloud-markings.py'))
cloud = importlib.util.module_from_spec(spec); spec.loader.exec_module(cloud)
covers = {r['id']: r for r in read(cover_path)['results']}
summary = read(Path(search_path) / 'summary.json')
assert summary['modelHash'] == sha(graph_path) and summary['kernelHash'] == sha(kernel_path)
for name, digest in summary['sourceHashes'].items():
    assert sha(Path(__file__).with_name(name)) == digest
models = {}; candidates_checked = 0
for source, reduced, entry in zip(original['models'], pruned['models'], data['models']):
    assert source['file'] == reduced['file'] == entry['file']
    assert source['fold'] == reduced['fold'] == entry['fold']
    assert source['trainingLifts'] == reduced['trainingLifts'] == entry['trainingLifts']
    before = source['model']; model = entry['model']
    assert reduced['model'] == {k: v for k, v in model.items() if k not in ('supportGroups', 'complementSupport')}
    assert {k: v for k, v in before.items() if k != 'candidates'} == {k: v for k, v in reduced['model'].items() if k != 'candidates'}
    pool = {c['id']: c for c in before['candidates']}
    assert len(pool) == len(before['candidates'])
    by_id = {c['id']: c for c in model['candidates']}
    assert len(by_id) == len(model['candidates'])
    for cid, c in by_id.items(): assert c == pool[cid]
    candidates_checked += len(by_id)
    models[entry['fold']] = (entry, by_id)

def check(entry, pool, selected, witnesses):
    assert len(selected) == len(set(selected))
    chosen = [pool[i] for i in selected]
    assert len({c['base'] for c in chosen}) == len(chosen)
    model = entry['model']; totals = dict.fromkeys(model['required'], 0)
    fields = defaultdict(list)
    for c in chosen:
        assert c['m'] == []
        for t in c['t']: totals[t['point']] += t['value']
        for m in c['cloudM']: fields[(m['point'], 'portable')].append(data['clouds'][m['cloud']])
    assert all(0 <= value <= model['capacity'] for value in totals.values())
    if witnesses is None:
        values = {}
        for key, assignments in fields.items():
            result = cloud.propose_common_witness(assignments, model['cloudRadius'])
            assert result['status'] == 'verified-witness'
            values[key] = result['witness']
    else:
        values = {tuple(json.loads(w['point'])): w['witness'] for w in witnesses}
        assert len(values) == len(witnesses) and set(values) == set(fields)
    for key, assignments in fields.items():
        for a in assignments: assert cloud.contains(a, values[key], model['cloudRadius']) is not None
    complete = all(value == model['capacity'] for value in totals.values())
    cover = covers[entry['file']]; adj = [set() for _ in cover['components']]
    for c in chosen:
        a, b = cover['componentPairs'][int(c['base'])]; adj[a].add(b); adj[b].add(a)
    remaining = {i for i, neighbors in enumerate(adj) if neighbors}; components = 0
    while remaining:
        todo = [remaining.pop()]; components += 1
        while todo:
            for i in adj[todo.pop()] & remaining: remaining.remove(i); todo.append(i)
    return complete, components, len(values)

lifts = 0
for entry, pool in models.values():
    for lift in entry['trainingLifts']:
        assert check(entry, pool, lift['selected'], None)[0]; lifts += 1
files = sorted(Path(search_path).glob('[0-9]*-true.json'))
assert len(files) == len(summary['results']) and files
rows = []; keys = set()
for path in files:
    raw = read(path); r = raw['result']; key = (r['fold'], r['enabled'])
    assert key not in keys; keys.add(key)
    assert r['enabled'] and r['rootRollback'] and r['markingStatus'] == 'verified-common-values'
    for field in ('modelHash', 'kernelHash', 'sourceHashes'): assert raw[field] == summary[field]
    assert dict(r, selected=len(r['selected'])) in summary['results']
    entry, pool = models[r['fold']]
    assert r['file'] == entry['file']
    complete, components, count = check(entry, pool, r['selected'], raw['commonWitnesses'])
    assert complete == r['scalarComplete'] and count == r['commonValues']
    if r['status'] == 'verified finite registered filling': assert complete
    rows.append(dict(file=entry['file'], status=r['status'], complete=complete,
                     selected=len(r['selected']), positiveSupportComponents=components,
                     verifiedCommonValues=count, seconds=r['seconds'], steps=r['steps']))
result = dict(scope=__doc__, modelHash=sha(graph_path), summaryHash=sha(Path(search_path)/'summary.json'),
              pruningCheckHash=sha(pruning_check_path), graphCheckHash=sha(graph_check_path),
              verifierHash=sha(__file__), coverHash=sha(cover_path),
              retainedCandidatesChecked=candidates_checked, trainingLiftsChecked=lifts, results=rows,
              limits='Final states independently checked; runtime rollback and scheduling rely on separate harness audits. No proof of continuous-pose completeness, blind growth, or transfer.')
with Path(output).open('x') as f: json.dump(result, f, indent=2)
print(json.dumps(result), flush=True)
