"""Measured full-universe/proposer correspondence before matched13 searches."""
import copy
import gc
import gzip
import hashlib
import json
import random
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from turtle import Graph
from certificate_boundary_search import canonical
from native_inventory_policy import choose
from commutativity_cluster_points import Model
from commutativity_cluster_guidance import Join as Old, vector, FIXED
from commutativity_cluster_search import search as old_search
from commutativity13_guidance import Join as Fast, vectors
from commutativity13_json import save, encoded
from commutativity13_search import search as fast_search

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/commutativity13-20261011'
PARENT = ROOT / '.gcts-active/commutativity-receptors-20261011'


def load(path):
    with gzip.open(path, 'rt') as stream:
        return json.load(stream)


def need(value, message):
    if not value:
        raise ValueError(message)


def model(spec, catalog):
    path = PARENT / 'native-complete/registry.json.gz'
    return Model(spec, catalog, load(path), json.loads((PARENT / 'native-complete/registry-audit.json').read_text()), path.read_bytes())


def binding(record, domains, length):
    roots = sorted(record['roots'])
    return dict(schema='exact-scalar-point-model-v1', length=length,
                required_points=[dict(point=p, generation=0) for p in roots],
                initial=dict(roots=[[p, 0] for p in roots], generations=[[p, 0] for p in roots],
                             marks=sorted(record['initial_marks']), totals=[], allowed_points=roots),
                placements=sorted(record['placements'], key=lambda p: p['key']),
                injective_catalog=record['catalog'], inference_rules=record['inference_rules'],
                rule_modes=[i + 1 if r['premises'] else 0 for i, r in enumerate(record['inference_rules'])],
                row_domains=domains, arity=2, capacity=12, registry_sha256=record['registry_sha256'])


def static_index(join):
    return dict(families=join.families, bindings=join.bindings,
                incidence=[[k, v] for k, v in sorted(join.incidence.items())],
                ports=[[k, v] for k, v in sorted(join.ports.items())],
                universe=join.universe, key_bytes=[[k, v.decode()] for k, v in sorted(join.key_bytes.items())],
                rank_cache_limit=join.rank_cache_limit)


def comparable(result):
    value = copy.deepcopy(result)
    for key in ('seconds', 'peak_rss_bytes', 'graph_metrics', 'scope'):
        value.pop(key, None)
    value['metrics'].pop('proposal_seconds', None)
    return value


def main():
    began = time.perf_counter()
    plan = json.loads((OUT / 'preflight-plan.json').read_text())
    for path, h in {**plan['source_sha256'], **plan['input_sha256']}.items():
        need(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == h, 'preflight exact freeze ' + path)
    result = dict(status='running_exact_proposer_and_serialization_correspondence', native_target_queries=0, new_measured_target_searches=0, observations=[])
    for name in ('fixed-r1', 'fixed-r2'):
        need(time.perf_counter() - began < 300, 'unknown_preflight_producer_time_budget')
        subprocess.run([sys.executable, str(Path(__file__).with_name('commutativity13_extract.py')), name], check=True)
        receipt = json.loads((OUT / (name + '-events-receipt.json')).read_text())
        need(receipt['status'] == 'complete_exact_event_projection_pending_independent_audit', 'full old-event projection resource gate')
    catalog = load(PARENT / 'attempt-02/two-lemmas-retained-core.json.gz')
    timings = dict(old_join_seconds=0., fast_join_seconds=0., old_features_seconds=0., fast_features_seconds=0.)
    initial12 = copy.deepcopy(plan['case']); initial12.update(id='old-event-correspondence', length=12)
    exact = model(initial12, catalog)
    stage = time.perf_counter(); old = Old(exact); old_init = time.perf_counter() - stage
    stage = time.perf_counter(); fast = Fast(exact); fast_init = time.perf_counter() - stage
    states, graphs, prior = [exact.initial()], [Graph(exact, exact.initial())], []
    events = 0
    correspondence = []
    for name in ('fixed-r1', 'fixed-r2'):
        projection = load(OUT / (name + '-events.json.gz'))
        for event in projection['events']:
            keys = [tuple(k) for k in event['chosen']]
            common = 0
            while common < min(len(prior), len(keys)) and prior[common] == keys[common]:
                common += 1
            states, graphs = states[:common + 1], graphs[:common + 1]
            for key in keys[common:]:
                child, graph = states[-1].copy(), graphs[-1].copy()
                need(child.legal(exact.placement(key)), 'recorded full prefix legality')
                graph.update(exact, child, child.place(exact.placement(key)))
                states.append(child); graphs.append(graph)
            prior = keys
            state, graph, point = states[-1], graphs[-1], tuple(event['point'])
            need(graph.decision(state)[:2] == ('branch', point), 'global recorded branch context')
            stage = time.perf_counter(); a, wa = old(state, graph, point); timings['old_join_seconds'] += time.perf_counter() - stage
            stage = time.perf_counter(); b, wb = fast(state, graph, point); timings['fast_join_seconds'] += time.perf_counter() - stage
            need(canonical(a) == canonical(b) and wa == wb == event['work'] and canonical(a) == canonical(event['items']), 'complete canonical pools/work/old events')
            stage = time.perf_counter(); av = [vector(item, exact, state, graph) for item in a]; timings['old_features_seconds'] += time.perf_counter() - stage
            stage = time.perf_counter(); bv = vectors(b, exact, state, graph); timings['fast_features_seconds'] += time.perf_counter() - stage
            need(av == bv == event['features'], 'every old/new vector')
            _, choice = choose(b, bv, list(FIXED), random.Random(0), False)
            need(all(choice[key] == event[key] for key in ('scores', 'probabilities', 'uniform', 'index')), 'fixed scores/ties/distribution')
            correspondence.append(dict(id=name, index=events, chosen=event['chosen'], point=event['point'],
                                       items=b, work=wb, features=bv, choice=choice))
            events += 1
            if events % 25 == 0:
                (OUT / 'preflight-checkpoint.json').write_text(json.dumps(dict(phase='correspondence', events=events, timings=timings, seconds=time.perf_counter() - began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss), indent=2) + '\n')
            need(time.perf_counter() - began <= 300 and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 536870912, 'unknown_preflight_correspondence_resource_budget')
        del projection
    save(OUT / 'correspondence.json.gz', correspondence)
    del correspondence
    result.update(old_recorded_events=events, old_proposer_initialization_seconds=old_init,
                  fast_proposer_initialization_seconds=fast_init, correspondence_timings=timings,
                  rank_cache_bound=16, cold_warm_disclosure='One initial static12-rowcache charged; its bounded exact ranking cache warms across all589old-eventcorrespondence contexts. Actual13-rowobservations use freshprocesses/models/coldcaches, never these contexts or cachedvalues.')
    del exact, old, fast, states, graphs
    gc.collect()
    spec = copy.deepcopy(plan['case']); spec.update(id='13-row-complete-preflight', length=13)
    exact = model(spec, catalog); record = exact.record(); bound = binding(record, exact.domains, 13)
    save(OUT / 'model13.json.gz', dict(case=spec, model=record, row_domains=exact.domains))
    save(OUT / 'binding13.json.gz', bound)
    result.update(placements=len(record['placements']), roots=len(record['roots']),
                  complete_model_sha256=hashlib.sha256(canonical(bound)).hexdigest(),
                  component_sha256={k: hashlib.sha256(canonical(v)).hexdigest() for k, v in bound.items()})
    stage = time.perf_counter(); fast = Fast(exact)
    result['static13_initialization_seconds'] = time.perf_counter() - stage
    result['complete_family_bindings'] = len(fast.bindings)
    save(OUT / 'static13.json.gz', static_index(fast))
    del fast, exact, record, bound
    gc.collect()
    fixture_results = []
    for mode in ('base', 'fixed'):
        a_model = model(spec, catalog); a = old_search(a_model, mode=mode, seed=1, attempts=40, seconds=30)
        b_model = model(spec, catalog); b = fast_search(b_model, mode=mode, seed=1, attempts=40, seconds=30)
        need(canonical(comparable(a)) == canonical(comparable(b)), 'complete old/new13rowfixturetree/events/fallback/rootrollback')
        item = dict(case=spec, observation=dict(id='fixture-' + mode, mode=mode, rep=1), search=b, native_target_queries=0)
        file = OUT / ('fixture-' + mode + '.json.gz'); save(file, item)
        need(canonical(load(file)) == canonical(item), 'complete fast node-aware serialization values')
        fixture_results.append(dict(mode=mode, old=a, fast=b))
        del a_model, b_model, a, b
        gc.collect()
    save(OUT / 'fixtures.json.gz', fixture_results)
    result.update(status='complete_exact589event_and13row_fixture_correspondence_pending_independent_audit',
                  fixture_nodes=[r['fast']['metrics']['nodes'] for r in fixture_results],
                  diagnostic13_fixture_searches=4, ordinary_word_or_witnesses_used=False,
                  actual_matched13_searches=0, seconds=time.perf_counter() - began,
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if result['seconds'] > 300 or result['peak_rss_bytes'] > 536870912:
        result['status'] = 'unknown_preflight_producer_resource_budget'
    (OUT / 'preflight-summary.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        result = dict(status='unknown_or_failed_preflight', error=repr(error),
                      peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                      checkpoint=json.loads((OUT / 'preflight-checkpoint.json').read_text()) if (OUT / 'preflight-checkpoint.json').exists() else None,
                      native_target_queries=0, actual_matched13_searches=0)
        (OUT / 'preflight-summary.json').write_text(json.dumps(result, indent=2) + '\n')
        raise
