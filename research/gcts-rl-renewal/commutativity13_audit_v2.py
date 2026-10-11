"""Independent old-semantics correspondence and complete13 point reconstruction.

No accelerated guidance/search/serializer is imported. Original reference
proposals and literal full-universe graph enumeration supply the audit.
"""
import argparse
import collections
import gc
import gzip
import hashlib
import json
import math
import resource
import subprocess
import sys
import time
from pathlib import Path
from commutativity_cluster_intern_v3 import load as stream_load
from commutativity_cluster_audit import load, need, packed, initial, families, row, proposals, features, tree
from induction_receptors_audit import model_binding
from audit_semantic_inventory import LiteralDomains, advance, legal

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.gcts-active/commutativity13-20261011'
OLD = ROOT / '.gcts-active/commutativity-cluster-search-20261011'
PARENT = ROOT / '.gcts-active/commutativity-receptors-20261011'


def verify(plan):
    for p, h in {**plan['source_sha256'], **plan['input_sha256']}.items():
        need(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, 'exact auditor source/input ' + p)


def semantic(record, domains, length):
    roots = sorted(record['roots'])
    return dict(schema='exact-scalar-point-model-v1', length=length,
                required_points=[dict(point=p, generation=0) for p in roots],
                initial=dict(roots=[[p, 0] for p in roots], generations=[[p, 0] for p in roots],
                             marks=sorted(record['initial_marks']), totals=[], allowed_points=roots),
                placements=sorted(record['placements'], key=lambda p: p['key']),
                injective_catalog=record['catalog'], inference_rules=record['inference_rules'],
                rule_modes=[i + 1 if r['premises'] else 0 for i, r in enumerate(record['inference_rules'])],
                row_domains=domains, arity=2, capacity=12, registry_sha256=record['registry_sha256'])


def projection(name):
    began = time.perf_counter()
    verify(json.loads((OUT / 'preflight-audit-plan-v2.json').read_text()))
    raw = stream_load(OLD / (name + '-search.json.gz'))
    projected = load(OUT / (name + '-events.json.gz'))
    need(packed(projected['events']) == packed(raw['search']['events']), 'complete actual old event projection')
    need(projected['case'] == raw['case'] and projected['observation'] == raw['observation'], 'old exact case/observation')
    need(projected['original_trace_sha256'] == hashlib.sha256((OLD / (name + '-search.json.gz')).read_bytes()).hexdigest(), 'exact original trace binding')
    result = dict(status='passed_complete_original_event_projection', id=name, events=len(projected['events']),
                  seconds=time.perf_counter() - began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    need(result['seconds'] <= 180 and result['peak_rss_bytes'] <= 536870912, 'unknown_independent_projection_resource_budget')
    (OUT / (name + '-projection-audit-v2.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


def main():
    began = time.perf_counter()
    plan = json.loads((OUT / 'preflight-audit-plan-v2.json').read_text()); verify(plan)
    allowance = 300 - plan['prior_audit_seconds']
    for name in ('fixed-r1', 'fixed-r2'):
        subprocess.run([sys.executable, __file__, '--projection', name], check=True)
    catalog = load(PARENT / 'attempt-02/two-lemmas-retained-core.json.gz')
    oldraw = load(OLD / 'preflight-model.json.gz')
    model_binding(oldraw['case'], catalog, oldraw['model'])
    inventory = {tuple(p['key']): p for p in oldraw['model']['placements']}
    declared = families(catalog); domains_at = LiteralDomains(inventory)
    correspondence = load(OUT / 'correspondence.json.gz')
    index = 0; states = [initial(oldraw['model'])]; prior = []
    for name in ('fixed-r1', 'fixed-r2'):
        original = load(OUT / (name + '-events.json.gz'))
        for event in original['events']:
            keys = [tuple(k) for k in event['chosen']]; common = 0
            while common < min(len(prior), len(keys)) and prior[common] == keys[common]: common += 1
            states = states[:common + 1]
            for key in keys[common:]:
                need(legal(inventory[key], states[-1]), 'literal actual prefix legality')
                states.append(advance(inventory[key], states[-1]))
            prior = keys; state = states[-1]; domains = domains_at(state); point = tuple(event['point'])
            need(all(domains.values()) and all(len(v) > 1 for v in domains.values()), 'policy only after global dead/forced')
            need(point == min(domains, key=lambda p: (state['generations'][p], len(domains[p]), p)), 'literal earliest generation')
            items, work = proposals(inventory, catalog['rules'], declared, state, domains, point, 24, 2048)
            vals = [features(item, inventory, catalog['rules'], oldraw['case'], state) for item in items]
            got = correspondence[index]
            need(got['id'] == name and got['index'] == index and packed(got['chosen']) == packed(keys) and packed(got['point']) == packed(point), 'every saved accelerated context')
            need(packed(items) == packed(got['items']) == packed(event['items']) and work == got['work'] == event['work'], 'independent full exact pools order/counters')
            need(vals == got['features'] == event['features'], 'all exact features')
            scores = [sum(w*x for w,x in zip([.7,.3,1.,.8,.2,-.1,.2,.2,0.], v)) for v in vals]
            ex = [math.exp(s - max(scores)) for s in scores]; prob = [s / sum(ex) for s in ex]
            choice = got['choice']
            need(choice['scores'] == scores and choice['probabilities'] == prob and choice['uniform'] is None and choice['index'] == max(range(len(scores)), key=lambda i: (scores[i],-i)), 'exact fixed scoring/ties/SHA ordered open pool')
            index += 1
            if index % 25 == 0:
                (OUT / 'preflight-audit-checkpoint-v2.json').write_text(json.dumps(dict(events=index, seconds=time.perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
            need(time.perf_counter()-began <= allowance and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 536870912, 'unknown_full_correspondence_audit_resource_budget')
        del original
    need(index == len(correspondence) == 589, 'no omitted actual old event')
    del correspondence, inventory, states, domains_at, oldraw
    gc.collect()
    raw = load(OUT / 'model13.json.gz'); placements = model_binding(raw['case'], catalog, raw['model'])
    inventory = {tuple(p['key']): p for p in placements}; guards = {(k[0], p['inference']):k for k,p in inventory.items() if k[1] == 1}
    static = load(OUT / 'static13.json.gz'); binds = []; incidence = collections.defaultdict(list)
    for family in declared:
        for j in range(13):
            if (j,family['rewrite_rule']) not in guards: continue
            for root in range(j):
                for source in range(j):
                    if source == root: continue
                    keys = row(inventory,catalog['rules'],guards,root,family['root_rule'],[]) + row(inventory,catalog['rules'],guards,j,family['rewrite_rule'],[source,root])
                    n = len(binds); binds.append(keys)
                    for k in keys: incidence[k].append(n)
    ports = collections.defaultdict(list)
    for k,p in sorted(inventory.items()):
        if k[1] in (2,3): ports[(k[0],k[1],p['mode'])].append(k)
    expected = dict(families=declared, bindings=binds, incidence=[[k,v] for k,v in sorted(incidence.items())], ports=[[k,v] for k,v in sorted(ports.items())], universe=sorted(inventory), key_bytes=[[k,packed(k).decode()] for k in sorted(inventory)], rank_cache_limit=16)
    need(packed(expected) == packed(static) and len(binds) == 18480 and len(inventory) == 19848, 'complete static incidence/port order/all key canonical words/full family binding universe')
    bound = semantic(raw['model'],raw['row_domains'],13)
    need(packed(bound) == packed(load(OUT / 'binding13.json.gz')), 'external exact semantic hash schema')
    h = hashlib.sha256(packed(bound)).hexdigest()
    components = {k:hashlib.sha256(packed(v)).hexdigest() for k,v in bound.items()}
    placement_count, binding_count = len(inventory), len(binds)
    del bound, expected, static, binds, incidence, ports, placements, inventory
    gc.collect()
    (OUT / 'preflight-audit-lifetime-v2.json').write_text(json.dumps(dict(phase='complete_static_witnesses_released_before_full_fixtures', seconds=time.perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
    fixtures = load(OUT / 'fixtures.json.gz'); outcomes = []
    for fixture in fixtures:
        item = load(OUT / ('fixture-' + fixture['mode'] + '.json.gz'))
        need(packed(item['search']) == packed(fixture['fast']), 'all streamed actual fixture values')
        outcomes.append(dict(mode=fixture['mode'], old=tree(raw['case'],raw['model'],fixture['old'],declared), fast=tree(raw['case'],raw['model'],fixture['fast'],declared)))
    result = dict(status='passed_complete_exact_proposer_serialization_and13model_preflight', events=index,
                  placements=placement_count, roots=len(raw['model']['roots']), families=len(declared), family_bindings=binding_count,
                  complete_model_sha256=h, component_sha256=components,
                  fixture_trees=outcomes, seconds=time.perf_counter()-began, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  ordinary_word_or_witnesses_used=False, actual_matched13_searches=0, native_target_queries=0,
                  scope='Every589old actual event; complete13point model/static bindings; all four diagnostic fixture trees. Future target traces require separate complete graph replay.')
    result['prior_failed_audit_seconds'] = plan['prior_audit_seconds']
    result['cumulative_audit_seconds'] = result['seconds'] + plan['prior_audit_seconds']
    if result['cumulative_audit_seconds'] > 300 or result['peak_rss_bytes'] > 536870912: result['status']='unknown_complete_preflight_audit_resource_budget'
    (OUT / 'preflight-audit-v2.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--projection'); args=parser.parse_args()
    if args.projection: projection(args.projection)
    else:
        try: main()
        except Exception as error:
            (OUT/'preflight-audit-v2.json').write_text(json.dumps(dict(status='unknown_or_failed_independent_preflight',error=repr(error),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2)+'\n')
            raise
