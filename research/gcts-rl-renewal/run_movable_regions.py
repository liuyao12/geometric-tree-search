"""Cold movable regions, certified failed-pair marks, warm and classical lanes."""
import copy
import hashlib
import resource
import time
from pathlib import Path

import movable_proof_regions as M
import check_movable_regions as A
import quantified_receptors as Q
from quantified_receptor_cases import registry
from audit_serialized_kernel import replay
from serialized_kernel import canonical

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]/'docs/research/gcts-rl-renewal'


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def specs():
    base, bindings = registry()
    rows = []
    for c in base:
        c = copy.deepcopy(c)
        c['bound'] = c.pop('length')
        rows.append(c)
    supplied = copy.deepcopy(rows[0])
    supplied['id'] = 'supplied-target'
    supplied['target'] = supplied['hypotheses'][-1]
    rows.append(supplied)
    return rows, bindings


def row_keys(m, rows):
    known = {j: a for j, a in enumerate(m.hypotheses, -len(m.hypotheses))}
    out = []
    for j, row in enumerate(rows):
        refs = tuple(row['refs'])
        matches = [rid for rid, r in enumerate(m.catalog['rules'])
                   if Q.row(r, refs) == row and tuple(known[i] for i in refs) == r['inputs']]
        if not matches:
            raise ValueError("control row has no inventory instance")
        out.append((j, matches[0], refs))
        known[j] = row['formula']
    return out


def decorate(m, spec, r):
    if r['proof'] is None:
        return
    start = time.perf_counter()
    if 'placements' not in r:
        n = len(r['proof'])
        r['placements'] = row_keys(m, r['proof'])+[(n, M.END, ())]+[(j, M.PAD, ()) for j in range(n+1, m.length)]
        s = m.initial()
        for key in r['placements']:
            s.place(m.placement(key))
        r['tile_generations'] = s.tile_generations
        r['endpoint'] = n
    r['tiles'] = [dict(key=k, occupancy=m.placement(k).occupancy, marks=m.placement(k).marks)
                  for k in r['placements']]
    r['closing_cluster'] = M.closing_cluster(m, r['endpoint'])
    r['point_certificate'] = A.certificate(m.catalog['rules'], spec, r, r['tiles'], m.marking)
    A.cluster(m.catalog['rules'], spec, r, m.marking)
    erasure = [dict(t, marks=tuple((p, v) for p, v in t['marks'] if p[0] != -2000)) for t in r['tiles']]
    r['erased_certificate'] = A.certificate(m.catalog['rules'], spec, r, erasure)
    if 'search_tree' in r:
        state = m.initial()
        graph = M.Graph(m, state)
        frames = []
        for key in r['placements']:
            kind, point, keys = graph.decision(state)
            if key not in keys:
                raise ValueError("actual placement path")
            frames.append(dict(kind=kind, point=point, key=key,
                               domains=[dict(point=p, blocks=d.base.blocks,
                                             structural=d.structural, excluded=sorted(d.excluded),
                                             count=len(d)) for p, d in sorted(graph.domains.items())]))
            graph.update(m, state, state.place(m.placement(key)))
        r['frames'] = frames
    r['point_assembly_and_check_seconds'] = time.perf_counter()-start
    start = time.perf_counter()
    r['compiled'] = M.compile_region(r['proof'], spec['target'], spec['hypotheses'], spec['theory'])
    if replay(canonical(r['compiled']['request']))['status'] != 'accepted':
        raise ValueError("independent kernel")
    if spec['hypotheses']:
        r['deduced'] = M.compile_region(r['proof'], spec['target'], spec['hypotheses'], spec['theory'], True)
        if replay(canonical(r['deduced']['request']))['status'] != 'accepted':
            raise ValueError("independent discharged proof")
    r['compile_and_host_check_seconds'] = time.perf_counter()-start


def execute(spec, family=None, bindings=()):
    start = time.perf_counter()
    catalog = Q.inventory(spec['theory'], spec['hypotheses'], spec['terms'], spec['variables'],
                          spec['rounds'], family, bindings, spec['generalization_rounds'])
    build = time.perf_counter()-start
    rules, forms = A.A.inventory(spec, family, bindings)
    if rules != catalog['rules'] or forms != catalog['formulas']:
        raise ValueError("independent inventory")
    start = time.perf_counter()
    base_model = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'])
    base_binding = time.perf_counter()-start
    base = M.search(base_model, node_limit=40000, seconds=12, collect_pairs=True)
    start = time.perf_counter()
    certified = []
    seen = set()
    for item in base['negatives']:
        key = frozenset(item['pair'])
        if key in seen:
            continue
        checked = A.tree(rules, spec, seeds=item['pair'], node=item['tree'])
        if checked['outcome']:
            raise ValueError("positive is not a negative training label")
        certified.append(dict(item, check=checked))
        seen.add(key)
    certification = time.perf_counter()-start
    start = time.perf_counter()
    pairs = [c['pair'] for c in certified]
    marked_model = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'], pairs)
    encoding = time.perf_counter()-start
    if base_model.context_hash() != marked_model.context_hash():
        raise ValueError("exact frozen context")
    warm = M.search(marked_model, node_limit=40000, seconds=12)
    runs = {'baseline': base, 'marked': warm}
    models = {'baseline': base_model, 'marked': marked_model}
    for lane, marking in (('chronological', ()), ('chronological_marked', pairs), ('saturation', ())):
        m = M.Model(catalog, spec['target'], spec['bound'], spec['hypotheses'], marking)
        if lane == 'saturation':
            r = Q.saturation(m)
            fits = r['proof'] is not None and len(r['proof']) <= spec['bound']
            r['fits_region_bound'] = fits
            if r['proof'] is not None and not fits:
                r['status'] = 'found_outside_region_bound'
                r['outside_proof'] = r['proof']
                r['proof'] = None
        else:
            r = M.chronological(m, node_limit=40000, seconds=12)
        runs[lane] = r
        models[lane] = m
    for lane, r in runs.items():
        decorate(models[lane], spec, r)
    return dict(spec=spec, family=family, bindings=bindings, catalog=catalog,
                context_hash=base_model.context_hash(), build_seconds=build,
                baseline_binding_seconds=base_binding, certification_seconds=certification,
                encoding_seconds=encoding, certified=certified,
                learned_points=[dict(point=M.learning_point(n), assignments=[
                    dict(key=a, value=0), dict(key=b, value=1)])
                    for n, (a, b) in enumerate(pairs)],
                training_seconds=base_binding+base['seconds']+certification+encoding,
                runs=runs)


def main():
    began = time.perf_counter()
    names = ('run_movable_regions.py', 'movable_proof_regions.py', 'check_movable_regions.py',
             'test_movable_regions.py', 'quantified_receptors.py', 'quantified_receptor_cases.py',
             'check_quantified_receptors.py', 'logic.py', 'serialized_kernel.py',
             'audit_serialized_kernel.py', 'turtle.py')
    pins = {n: digest(HERE/n) for n in names}
    rows, bindings = specs()
    source = execute(rows[0])
    proof = source['runs']['baseline']['proof']
    if not proof or any(r['kind'] == 'family' for r in proof):
        raise ValueError("fresh primitive donor")
    family = dict(name='universal-mp', proof=proof, premises=rows[0]['hypotheses'],
                  conclusion=rows[0]['target'], guards=tuple(sorted({
                      r['parameters']['variable'] for r in proof if r['kind'] == 'generalize'})),
                  source='universal-mp')
    cases = [source]
    for spec in rows[1:]:
        cases.append(execute(spec))
    for name, binding in (('arithmetic', 'arithmetic'), ('geometry-family', 'geometry')):
        spec = copy.deepcopy(next(c for c in rows if c['id'] == name))
        spec['id'] += '-family'
        cases.append(execute(spec, family, [bindings[binding]]))
    for c in cases:
        print(c['spec']['id'], {k: (r['status'], r.get('endpoint'), r.get('metrics', {}).get('nodes'))
                               for k, r in c['runs'].items()}, 'pairs', len(c['certified']), flush=True)
    out = dict(version='movable-regions-001', sources=pins, family=family, cases=cases,
               seconds=time.perf_counter()-began, peak_process_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               scope='Finite positional movable boundary with exact flow; candidate-pair exclusions certified by complete whole-region exhaustion, encoded as actual sparse point values and frozen per exact context. No full corona catalog, no transfer theorem, no RL lane, no minimum-length claim.')
    if any(digest(HERE/n) != p for n, p in pins.items()):
        raise ValueError("measured source changed")
    (DOC/'movable-regions-001.json').write_bytes(canonical(out)+b'\n')
    print('complete', out['seconds'], flush=True)


if __name__ == '__main__':
    main()
