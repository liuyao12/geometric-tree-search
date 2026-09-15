"""Independently reconstruct saved finite covers, including marking-only sites."""
import hashlib
import json
import sys
from pathlib import Path

compiled_path, folder, kernel, alternatives, destination = map(Path, sys.argv[1:])
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
compiled = json.loads(compiled_path.read_text())

def check(model, selected):
    candidates = {c['id']: c for c in model['candidates']}
    assert len(selected) == len(set(selected))
    totals = dict.fromkeys(model['required'], 0)
    marks, owners, adjacency = {}, {}, {i: set() for i in selected}
    for i in selected:
        c = candidates[i]
        for site in c['t']:
            p, value = site['point'], site['value']
            assert value > 0
            totals[p] += value
            assert totals[p] <= model['capacity']
            if p in owners:
                j = owners[p]
                adjacency[i].add(j)
                adjacency[j].add(i)
            owners[p] = i
        for site in c['m']:
            key = (site['point'], site['channel'])
            assert site['lo'] == site['hi']
            assert key not in marks or marks[key] == site['lo']
            marks[key] = site['lo']
    unseen, components = set(selected), 0
    while unseen:
        todo = [unseen.pop()]
        components += 1
        while todo:
            new = adjacency[todo.pop()] & unseen
            unseen -= new
            todo.extend(new)
    return {'complete': all(t == model['capacity'] for t in totals.values()),
            'positiveSupportComponents': components, 'selected': len(selected)}

checks = []
for source in compiled['models']:
    for halo in (False, True):
        run = json.loads((folder / f"{source['fold']}-{str(halo).lower()}.json").read_text())
        assert run['compiledHash'] == digest(compiled_path)
        assert run['kernelHash'] == digest(kernel)
        for name, value in run['sourceHashes'].items():
            assert digest(Path(__file__).with_name(name)) == value
        model = {k: source[k] for k in ('capacity', 'required')}
        model['candidates'] = [dict(c, m=[s for s in c['m'] if halo or s['channel'] == '0']) for c in source['candidates']]
        assert run['model'] == model
        assert check(model, source['trainingSelected'])['complete']
        result = check(model, run['result']['selected'])
        assert result['complete'] == (run['result']['status'] == 'exact finite point-cover witness')
        checks.append(dict(file=source['file'], halo=halo, **result))
alternative_checks = []
alternative_data = json.loads(alternatives.read_text())
assert alternative_data['inputHash'] == compiled['inputHash']
assert alternative_data['learningHash'] == compiled['learningHash']
for run in alternative_data['runs']:
    model = compiled['models'][run['fold']]
    result = check(model, [f'{i:06d}' for i in run['selected']])
    assert result['complete'] and result['positiveSupportComponents'] == 1
    alternative_checks.append(dict(file=run['file'], seed=run['seed'], **result))
destination.write_text(json.dumps({'compiledHash': digest(compiled_path),
    'searchSummaryHash': digest(folder / 'summary.json'),
    'alternativeHash': digest(alternatives), 'checks': checks,
    'alternativeChecks': alternative_checks}, indent=2) + '\n')
print(json.dumps({'searchesVerified': len(checks), 'alternativeCoversVerified': len(alternative_checks)}))
