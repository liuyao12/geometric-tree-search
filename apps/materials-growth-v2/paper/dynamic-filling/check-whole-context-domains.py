"""Necessary geometric domains for complete, training-only port contexts.

Uses original atom-valid motif poses and every proposed explicit-image neighbor.
Each saved port must inject into a distinct directed neighbor of the correct
type, within the frozen displacement-target tolerance. This is NOT a GCTS
constraint: missing overlaps remain unconstrained in GCTS. It is a diagnostic
of the current interface representation/proposal prior, not a filling test.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def injective(domains):
    """Complete finite bipartite matching, with a port-to-neighbor witness."""
    owners = {}
    def visit(port, seen):
        for neighbor in domains[port]:
            if neighbor in seen:
                continue
            seen.add(neighbor)
            if neighbor not in owners or visit(owners[neighbor], seen):
                owners[neighbor] = port
                return True
        return False
    for port in sorted(range(len(domains)), key=lambda p: len(domains[p])):
        if not visit(port, set()):
            return None
    assignment = [None] * len(domains)
    for neighbor, port in owners.items():
        assignment[port] = neighbor
    return assignment


def compatible(context, models, rotation, neighbors, tolerance):
    domains = []
    for mi, role in context['ports']:
        model = models[mi]
        opposite = 'B' if role == 'A' else 'A'
        # Both values encode A -> B. A B-role port therefore points backwards.
        vector = np.asarray(model['value' + role]) @ rotation
        if role == 'B':
            vector = -vector
        domains.append([j for j, n in enumerate(neighbors)
                        if n['type'] == model['type' + opposite]
                        and np.linalg.norm(vector - n['d']) <= tolerance + 1e-9])
    return injective(domains)


def run(metap, motifp, interfacep, contextp):
    meta, motifs, interfaces, inventory = [json.loads(p.read_text()) for p in
                                          [metap, motifp, interfacep, contextp]]
    assert inventory['mode'] == 'all-training-ports'
    assert inventory['metadataHash'] == interfaces['metadataHash'] == sha(metap)
    assert inventory['motifHash'] == interfaces['motifHash'] == sha(motifp)
    assert inventory['interfaceHash'] == sha(interfacep)
    mm = {r['id']: r for r in meta['configurations']}
    rr = {r['id']: r for r in motifs['rows']}
    cr = {r['configuration']: r for r in inventory['rows']}
    contexts, models = inventory['contexts'], interfaces['models']
    by_type, usage = defaultdict(list), defaultdict(set)
    for ci, context in enumerate(contexts):
        by_type[context['baseType']].append(ci)
        assert context['ports'], 'An empty decoration is not an observed connection-free motif'
        for mi, role in context['ports']:
            assert role in ['A', 'B'] and models[mi]['type' + role] == context['baseType']
    rows, self_checks = [], 0
    for frame in interfaces['frames']:
        if frame['status'] != 'admitted':
            continue
        cid = frame['configuration']
        clusters = rr[cid]['clusters']
        assert frame['training'] == rr[cid]['training']
        neighbors, source_ports = [[] for _ in clusters], [[] for _ in clusters]
        for oi in frame['observations']:
            o = interfaces['observations'][oi]
            assert o['configuration'] == cid and o['training'] == frame['training']
            a, b, d = o['clusterA'], o['clusterB'], np.asarray(o['d'])
            neighbors[a].append(dict(observation=oi, role='A', type=o['typeB'], d=d))
            neighbors[b].append(dict(observation=oi, role='B', type=o['typeA'], d=-d))
            if frame['training']:
                assert o['interface'] is not None
                source_ports[a].append((o['interface'], 'A'))
                source_ports[b].append((o['interface'], 'B'))
        selected = []
        for k, cluster in enumerate(clusters):
            rotation = np.asarray(cluster['fit']['rotationRow'])
            matches, typed_contexts = [], []
            for ci in by_type[cluster['type']]:
                required_types = Counter(models[mi]['typeB' if role == 'A' else 'typeA']
                                         for mi, role in contexts[ci]['ports'])
                available_types = Counter(n['type'] for n in neighbors[k])
                if all(available_types[t] >= n for t, n in required_types.items()):
                    typed_contexts.append(ci)
                witness = compatible(contexts[ci], models, rotation, neighbors[k],
                                     interfaces['valueTargetTolerance'])
                if witness is not None:
                    matches.append(dict(context=ci, neighbors=witness))
            if frame['training']:
                saved = cr[cid]['motifs'][k]
                ci = saved['context']
                assert saved['cluster'] == k and contexts[ci]['baseType'] == cluster['type']
                assert Counter(map(tuple, contexts[ci]['ports'])) == Counter(source_ports[k])
                assert Counter(map(tuple, saved['ports'])) == Counter(source_ports[k])
                assert any(m['context'] == ci for m in matches), 'Training context must fit its source'
                usage[ci].add(cid)
                self_checks += 1
            selected.append(dict(cluster=k, baseType=cluster['type'], degree=len(neighbors[k]),
                                 typeCountCompatibleContexts=typed_contexts,
                                 compatibleContexts=matches))
        rows.append(dict(configuration=cid, training=frame['training'], motifs=selected))
    for ci, context in enumerate(contexts):
        assert len(usage[ci]) == context['trainingFrames']
        assert context['sourceConfiguration'] in usage[ci]
        source = cr[context['sourceConfiguration']]['motifs'][context['sourceCluster']]
        assert source['context'] == ci
    summary = []
    for phase in sorted({m['phase'] for m in mm.values()}):
        for recurring in [False, True]:
            group = [r for r in rows if not r['training'] and mm[r['configuration']]['phase'] == phase]
            def count(m):
                return sum(not recurring or contexts[v['context']]['trainingFrames'] >= 2
                           for v in m['compatibleContexts'])
            def type_count(m):
                return sum(not recurring or contexts[ci]['trainingFrames'] >= 2
                           for ci in m['typeCountCompatibleContexts'])
            summary.append(dict(phase=phase, recurringContextsOnly=recurring, frames=len(group),
                                motifs=sum(len(r['motifs']) for r in group),
                                motifsWithTypeCountDomain=sum(type_count(m) > 0 for r in group for m in r['motifs']),
                                motifsWithDomain=sum(count(m) > 0 for r in group for m in r['motifs']),
                                framesWithAllDomains=sum(all(count(m) > 0 for m in r['motifs']) for r in group)))
    return dict(scope=__doc__, metadataHash=sha(metap), motifHash=sha(motifp),
                interfaceHash=sha(interfacep), contextHash=sha(contextp), codeHash=sha(Path(__file__)),
                trainingSelfChecks=self_checks, summary=summary, rows=rows,
                limits='Necessary displacement-target filter only. No paired-anchor coincidence, '
                       'opposite-port consistency, cross-interface collision, common m-value, t-sum, '
                       'or global search test. Domains use fixed recorded poses and a finite Voronoi '
                       'proposal set; empty domains do not establish continuous or GCTS impossibility. '
                       'Single-frame contexts are hypotheses, separately reported from recurrent contexts.')


if __name__ == '__main__':
    metap, motifp, interfacep, contextp, out = map(Path, sys.argv[1:])
    report = run(metap, motifp, interfacep, contextp)
    with out.open('x') as f:
        json.dump(report, f, indent=2)
    print(json.dumps({k: report[k] for k in ['trainingSelfChecks', 'summary']}))
