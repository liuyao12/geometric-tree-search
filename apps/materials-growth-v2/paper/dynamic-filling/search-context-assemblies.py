"""Finite context-choice compatibility diagnostic, NOT the GCTS filling engine.

Domains: original-pose contexts that pass the saved displacement prior, with
all bounded injective port assignments, plus saved optimized local witnesses.
Binary tests demand reciprocal proposed ports, anchor/value agreement and
displacement compatibility. These are explicit geometric diagnostic priors.
"""
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
import numpy as np


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def assignments(domains, limit=10000):
    order = sorted(range(len(domains)), key=lambda k: len(domains[k]))
    chosen, used, answers = [None]*len(domains), set(), []
    nodes, truncated = 0, False
    def visit(depth):
        nonlocal nodes, truncated
        if nodes >= limit:
            truncated = True
            return
        nodes += 1
        if depth == len(order):
            answers.append(chosen.copy())
            return
        k = order[depth]
        for j in domains[k]:
            if j in used:
                continue
            chosen[k] = j
            used.add(j)
            visit(depth+1)
            used.remove(j)
            if truncated:
                return
    visit(0)
    return answers, dict(nodes=nodes, truncated=truncated)


def solve(domains, compatible, limit=100000):
    """Fixed-order forward checking; finite diagnostic CSP, not base search."""
    nodes, stopped = 0, False
    def visit(remaining, chosen):
        nonlocal nodes, stopped
        if nodes >= limit:
            stopped = True
            return None
        nodes += 1
        if any(not d for d in remaining):
            return None
        if not remaining:
            return chosen
        k = len(chosen)
        for value in remaining[0]:
            if not compatible(k, value, k, value):
                continue
            filtered = [[b for b in d if compatible(k, value, k+offset+1, b)]
                        for offset, d in enumerate(remaining[1:])]
            found = visit(filtered, chosen+[value])
            if found is not None:
                return found
            if stopped:
                return None
        return None
    answer = visit(domains, [])
    return answer, dict(nodes=nodes, status='witness' if answer is not None else 'unknown-budget' if stopped else 'exhausted-finite-pool')


def main():
    paths = list(map(Path, sys.argv[1:]))
    coordp, metap, motifp, interfacep, contextp, domainp, posep, out = paths
    coords, meta, motifs, interfaces, inventory, baseline, poses = [json.loads(p.read_text()) for p in paths[:-1]]
    for key, p in [('coordinateHash', coordp), ('metadataHash', metap), ('motifHash', motifp), ('interfaceHash', interfacep), ('contextHash', contextp), ('baselineHash', domainp)]:
        assert poses[key] == sha(p)
    loader = load('poses', 'optimize-whole-context-poses.py')
    audit = load('audit', 'audit-assembled-contexts.py')
    checker = load('check', 'verify-whole-context-poses.py')
    graph_checker = load('graph_check', 'verify-shared-interface-poses.py')
    checker.verify(coords, meta, motifs, interfaces, inventory, baseline, poses)
    cc = {r['id']: r for r in coords['configurations']}
    mm = {r['id']: r for r in meta['configurations']}
    rr = {r['id']: r for r in motifs['rows']}
    ff = {r['configuration']: r for r in interfaces['frames']}
    pp = {(r['configuration'], r['cluster']): r for r in poses['rows']}
    contexts, models = inventory['contexts'], interfaces['models']
    rows = []
    for frame in baseline['rows']:
        if frame['training']:
            continue
        cid = frame['configuration']
        clusters, f = rr[cid]['clusters'], ff[cid]
        cell = np.asarray(cc[cid]['cell'])
        options, entries, enumeration = [], [], []
        for k, entry in enumerate(frame['motifs']):
            assert k == entry['cluster']
            p = clusters[k]['fit']
            R = np.asarray(p['rotationRow'])
            neighbors = loader.neighbors_for(f, interfaces, k)
            choices, seen = [], set()
            def add(w):
                # Only identical full decorated witnesses are deduplicated.
                key = json.dumps(w, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    choices.append(w)
            for saved in entry['compatibleContexts']:
                ci = saved['context']
                vectors, types = loader.port_data(contexts[ci], models)
                domains = [[j for j, n in enumerate(neighbors) if n['type'] == typ and np.linalg.norm(v@R-n['d']) <= .30+1e-9]
                           for v, typ in zip(vectors, types)]
                matches, stats = assignments(domains)
                enumeration.append(dict(cluster=k, context=ci, **stats))
                for assignment in matches:
                    add(dict(context=ci, neighbors=assignment, pose=p))
            for lane in pp[cid, k]['lanes']:
                w = lane['witness']
                if w is not None:
                    add({key: w[key] for key in ['context', 'neighbors', 'pose']})
            options.append(choices)
            ports = []
            for w in choices:
                R, tr = np.asarray(w['pose']['rotationRow']), np.asarray(w['pose']['translation'])
                mapping = {}
                for (mi, role), j in zip(contexts[w['context']]['ports'], w['neighbors']):
                    n = neighbors[j]
                    mapping[n['observation'], n['role']] = dict(anchor=np.asarray(models[mi]['anchor'+role])@R+tr,
                                                               value=np.asarray(models[mi]['value'+role])@R,
                                                               sign=1 if role == 'A' else -1)
                ports.append((tr, mapping))
            entries.append(ports)
        cache = {}
        def compatible(k, a, l, b):
            key = (k,a,l,b)
            if key in cache:
                return cache[key]
            ta, pa = entries[k][a]
            tb, pb = entries[l][b]
            answer = True
            for oi in f['observations']:
                o = interfaces['observations'][oi]
                i,j = o['clusterA'],o['clusterB']
                if sorted((i,j)) != sorted((k,l)):
                    continue
                A, B = (pa.get((oi,'A')), pb.get((oi,'B'))) if i == k else (pb.get((oi,'A')), pa.get((oi,'B')))
                if (A is None) != (B is None):
                    answer = False
                    break
                if A is None:
                    continue
                shift = np.asarray(o['imageShift'])@cell
                d = (tb-ta if i == k else ta-tb)+shift
                errors = [np.linalg.norm(A['anchor']-B['anchor']-shift), np.linalg.norm(A['value']-B['value']),
                          np.linalg.norm(A['value']*A['sign']-d), np.linalg.norm(B['value']*B['sign']+d)]
                if max(errors) > .30+1e-9:
                    answer = False
                    break
            cache[key] = answer
            return answer
        for recurring in [False, True]:
            domains = [[j for j,w in enumerate(opts) if not recurring or contexts[w['context']]['trainingFrames'] >= 2] for opts in options]
            answer, stats = solve(domains, compatible)
            truncated = any(s['truncated'] for s in enumeration)
            if answer is None and truncated:
                stats['status'] = 'unknown-enumeration-budget'
            witness = [options[k][j] for k,j in enumerate(answer)] if answer is not None else None
            if witness is not None:
                replay = audit.audit(cell, clusters, f, interfaces, contexts, witness)
                assert replay['displacementPass'] and replay['reciprocalPairPass']
                edges = []
                for pair in replay['reciprocalPairs']:
                    o = interfaces['observations'][pair['observation']]
                    edges.append((o['clusterA'],o['clusterB'],o['imageShift']))
                try:
                    connectivity = dict(status='constructive-periodic-paths', paths=graph_checker.periodic_paths(len(clusters), edges))
                except AssertionError:
                    connectivity = dict(status='unknown-no-path-in-bounded-box')
            else:
                connectivity = None
            rows.append(dict(configuration=cid, recurringOnly=recurring, domainSizes=list(map(len,domains)),
                             enumerationTruncated=truncated, search=stats, witness=witness, connectivity=connectivity))
    summary = []
    for phase in sorted({r['phase'] for r in mm.values()}):
        for recurring in [False, True]:
            group = [r for r in rows if mm[r['configuration']]['phase'] == phase and r['recurringOnly'] == recurring]
            summary.append(dict(phase=phase, recurringOnly=recurring, frames=len(group),
                                statuses=dict(Counter(r['search']['status'] for r in group)),
                                periodicPathWitnesses=sum(r['connectivity'] is not None and r['connectivity']['status']=='constructive-periodic-paths' for r in group),
                                maximumOptions=max((max(r['domainSizes']) for r in group), default=0)))
    result = dict(scope=__doc__, poseHash=sha(posep), baselineHash=sha(domainp), codeHash=sha(Path(__file__)),
                  rows=rows, summary=summary,
                  limits='Finite saved-pose/context diagnostic, not continuous completeness or GCTS point filling. '
                         'Assignment enumeration is bounded at 10000 nodes per context; search at 100000 nodes per frame/lane. '
                         'Reciprocal proposed-edge constraints are an extra geometric prior, not the marking rule itself. '
                         'No t-values or cross-edge/multiway geometric-point agreement. Exhaustion refers only to this finite pool.')
    with out.open('x') as f:
        json.dump(result,f,indent=2)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
