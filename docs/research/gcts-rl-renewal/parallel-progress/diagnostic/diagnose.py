"""Read-only diagnostic of saved policy actions; never constructs/runs an engine.

Parse the original normal JSON traces, dropping only the huge census field.
Existing independently replayed graph/scheduler evidence supplies legality.
All other fields, including every proposed pool/action/review, are retained.
"""
import collections
import gzip
import hashlib
import json
import math
import re
import resource
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / '.gcts-active/commutativity13-20261011'
OUT = Path(__file__).resolve().parent
STRING = re.compile(r'"(?:[^"\\]|\\.)*"')
SPECIAL = re.compile(r'["{}\[\]]')
SCALAR = re.compile(r'[-+0-9.eE]+|true|false|null')


class Reader:
    def __init__(self, stream):
        self.stream, self.buffer, self.pos, self.eof = stream, '', 0, False
        self.skipped_censuses = 0

    def fill(self):
        self.buffer = self.buffer[self.pos:] + self.stream.read(65536)
        self.pos = 0
        if not self.buffer:
            self.eof = True
        return bool(self.buffer)

    def peek(self):
        if self.pos == len(self.buffer) and not self.fill():
            return ''
        return self.buffer[self.pos]

    def ws(self):
        while self.peek() and self.peek().isspace():
            self.pos += 1

    def char(self, expected):
        self.ws()
        if self.peek() != expected:
            raise ValueError(('JSON token', expected, self.buffer[self.pos:self.pos+40]))
        self.pos += 1

    def string(self):
        self.ws()
        if self.peek() != '"':
            raise ValueError('JSON string expected')
        while True:
            match = STRING.match(self.buffer, self.pos)
            if match:
                self.pos = match.end()
                return json.loads(match.group())
            remainder = self.buffer[self.pos:]
            part = self.stream.read(65536)
            if not part:
                raise ValueError('unterminated string')
            self.buffer, self.pos = remainder + part, 0

    def skip_container(self):
        self.ws()
        if self.peek() not in '[{':
            raise ValueError('census must be container')
        depth = 0
        while True:
            match = SPECIAL.search(self.buffer, self.pos)
            if not match:
                self.pos = len(self.buffer)
                if not self.fill():
                    raise ValueError('unterminated census')
                continue
            self.pos = match.start()
            char = self.peek()
            if char == '"':
                self.string()
            else:
                self.pos += 1
                depth += 1 if char in '[{' else -1
                if depth == 0:
                    return

    def value(self):
        self.ws()
        char = self.peek()
        if char == '"':
            return self.string()
        if char == '{':
            self.pos += 1
            obj = {}
            self.ws()
            if self.peek() == '}':
                self.pos += 1
                return obj
            while True:
                key = self.string()
                if key in obj:
                    raise ValueError('duplicate key')
                self.char(':')
                if key == 'census':
                    self.skip_container()
                    self.skipped_censuses += 1
                else:
                    obj[key] = self.value()
                self.ws()
                end = self.peek()
                self.pos += 1
                if end == '}':
                    return obj
                if end != ',':
                    raise ValueError('object delimiter')
        if char == '[':
            self.pos += 1
            arr = []
            self.ws()
            if self.peek() == ']':
                self.pos += 1
                return arr
            while True:
                arr.append(self.value())
                self.ws()
                end = self.peek()
                self.pos += 1
                if end == ']':
                    return arr
                if end != ',':
                    raise ValueError('array delimiter')
        while True:
            match = SCALAR.match(self.buffer, self.pos)
            if match and match.end() < len(self.buffer):
                self.pos = match.end()
                return json.loads(match.group())
            remainder = self.buffer[self.pos:]
            part = self.stream.read(65536)
            if not part:
                if match:
                    self.pos = match.end()
                    return json.loads(match.group())
                raise ValueError('JSON scalar')
            self.buffer, self.pos = remainder + part, 0


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def rows(raw):
    pending = [(raw['search']['tree'], 0)]
    while pending:
        node, depth = pending.pop()
        yield node, depth
        pending.extend((child['tree'], depth+1) for child in reversed(node['children']))


def analyze(name):
    start = time.perf_counter()
    with gzip.open(INPUT / (name+'-search.json.gz'), 'rt', encoding='utf-8') as stream:
        reader = Reader(stream)
        raw = reader.value()
        reader.ws()
        assert not reader.peek()
    search = raw['search']
    assert raw['case']['length'] == 13
    events = search['events']
    hints = search['hints']
    stats = collections.Counter()
    phases = collections.Counter()
    event_rows = []
    node_rows = []
    digest = hashlib.sha256()
    event_kinds = collections.Counter()
    selected_kinds = collections.Counter()
    per_kind_features = collections.defaultdict(set)
    for node, depth in rows(raw):
        stats['nodes'] += 1
        stats['node_'+node['kind']] += 1
        structural = [node['kind'], node['point'], node['state_sha256'], node.get('alternatives'), [c['key'] for c in node['children']]]
        digest.update(packed(structural)+b'\n')
        phase = node['review']['phase']
        phases[node['kind']+'/'+phase] += 1
        if node['hint_in'] is not None:
            stats['hint_'+phase] += 1
        alternatives = node.get('alternatives', [])
        baseline = sorted(alternatives)
        assert alternatives == baseline, 'actual trace reordered domain'
        if 'alternatives' in node:
            stats['decision_points'] += 1
        active_review = node.get('start_review', node['review'])
        eligible = active_review['eligible']
        preferred = [k for k in baseline if k in eligible]
        reordered = preferred + [k for k in baseline if k not in eligible]
        if node['kind'] == 'branch':
            assert reordered == alternatives
            if node['hint_in'] is not None and phase == 'waiting':
                stats['branch_suppressed_by_waiting_hint'] += 1
            if preferred:
                stats['branch_with_preference'] += 1
                stats['branch_preference_base_prefix'] += int(preferred == baseline[:len(preferred)])
        if node['kind'] == 'forced' and eligible:
            stats['forced_eligible_no_choice'] += 1
        if node['kind'] == 'dead' and node['hint_in'] is not None:
            stats['dead_before_hint_action'] += 1
        for child in node['children']:
            stats['visited_children_'+child['role']] += 1
        node_rows.append(dict(preorder=stats['nodes']-1, depth=depth, kind=node['kind'], point=node['point'], state_sha256=node['state_sha256'],
                              hint_in=node['hint_in'], review=phase, start_review=node.get('start_review'), policy_event=node.get('policy_event'),
                              domain_size=len(baseline), preferred=preferred, child_roles=[c['role'] for c in node['children']]))
        if 'policy_event' not in node:
            continue
        e = events[node['policy_event']]
        assert e['point'] == node['point']
        assert node['start_review']['phase'] == 'eligible'
        assert hints[node['hint_start']]['item'] == e['items'][e['index']]
        scores = [sum(w*v for w, v in zip(e['weights'], f)) for f in e['features']]
        assert scores == e['scores']
        assert e['index'] == max(range(len(scores)), key=lambda i: (scores[i], -i))
        assert e['uniform'] is None
        top = max(scores)
        exponentials = [math.exp(score-top) for score in scores]
        probabilities = [p/sum(exponentials) for p in exponentials]
        assert probabilities == e['probabilities']
        details = []
        by_features = collections.defaultdict(list)
        for index, (item, feature, score) in enumerate(zip(e['items'], e['features'], e['scores'])):
            if item is None:
                keys = []
                order = baseline
                kind = 'defer'
            else:
                keys = [k for k in baseline if k in item['pending']]
                assert keys, 'off-point item in actual pool'
                order = keys + [k for k in baseline if k not in keys]
                kind = item['kind']
            change = order != baseline
            first_change = bool(order and order[0] != baseline[0])
            details.append(dict(index=index, kind=kind, score=score, probability=probabilities[index], features=feature, eligible=keys,
                                changes_order=change, changes_first=first_change, maximum=score == top,
                                members=item['members'] if item else []))
            event_kinds[kind] += 1
            per_kind_features[kind].add(tuple(feature))
            by_features[tuple(feature)].append(details[-1])
        winner = details[e['index']]
        selected_kinds[winner['kind']] += 1
        stats['events'] += 1
        stats['event_selected_index_zero'] += int(e['index'] == 0)
        stats['event_maximum_tie'] += int(sum(d['maximum'] for d in details) > 1)
        stats['event_changing_order_available'] += int(any(d['changes_order'] for d in details))
        stats['event_changing_first_available'] += int(any(d['changes_first'] for d in details))
        stats['event_maximum_changing_order_available'] += int(any(d['maximum'] and d['changes_order'] for d in details))
        stats['event_maximum_changing_first_available'] += int(any(d['maximum'] and d['changes_first'] for d in details))
        stats['event_feature_identical_changing_action_to_winner'] += int(any(d['features'] == winner['features'] and d['changes_order'] for d in details))
        stats['event_feature_identical_changing_first_to_winner'] += int(any(d['features'] == winner['features'] and d['changes_first'] for d in details))
        stats['event_selected_changes_order'] += int(winner['changes_order'])
        stats['event_selected_changes_first'] += int(winner['changes_first'])
        stats['pool_changing_order'] += sum(d['changes_order'] for d in details)
        stats['pool_changing_first'] += sum(d['changes_first'] for d in details)
        stats['pool_maximum_tie_items'] += sum(d['maximum'] for d in details)
        stats['pool_items_including_defer'] += len(details)
        stats['pool_null_items'] += sum(d['kind'] == 'defer' for d in details)
        assert not winner['changes_order']
        event_rows.append(dict(id=e['id'], preorder=stats['nodes']-1, point=e['point'], chosen=e['chosen'],
                               domain=baseline, selected=e['index'], maximum=top, maximum_tie=sum(d['maximum'] for d in details),
                               features_ambiguous_across_first_actions=sum(len({tuple(d['eligible'][0]) if d['eligible'] else None for d in ds}) > 1 for ds in by_features.values()),
                               stochastic_same_pool_probability_of_changing_first=sum(d['probability'] for d in details if d['changes_first']),
                               work=e['work'], actions=details))
    summary = json.loads((INPUT/(name+'-summary.json')).read_text())
    for key in ('nodes', 'events', 'hint_eligible', 'hint_waiting', 'hint_invalid', 'hint_completed'):
        expected = len(events) if key == 'events' else summary['metrics'].get(key, 0)
        assert stats[key] == expected, (key, stats[key], expected)
    assert reader.skipped_censuses == stats['nodes']
    expected_sha = '12b0cb0cfd13a90e0a6830293b507dd2d7cc4e97ec7586f5df1831b8fdbddb13'
    assert digest.hexdigest() == expected_sha
    assert sha(INPUT/(name+'-structure.jsonl')) == expected_sha
    cost = dict(seconds=time.perf_counter()-start, peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    result = dict(id=name, status='passed_read_only_saved_action_diagnostic', case_length=13, structural_sha256=digest.hexdigest(),
                  dropped_field='census only; all saved scheduler/pool/action/hint fields retained. Full legality authority is separately pinned prior independent replay.',
                  counters=dict(stats), phases_by_kind=dict(sorted(phases.items())), pool_kinds=dict(event_kinds), selected_kinds=dict(selected_kinds),
                  distinct_feature_vectors_by_kind={k:len(v) for k,v in per_kind_features.items()}, recorded_costs=summary, diagnostic_cost=cost,
                  events=event_rows, nodes=node_rows)
    (OUT/(name+'-diagnostic.json')).write_text(json.dumps(result, indent=2)+'\n')
    return {k:v for k,v in result.items() if k not in ('events','nodes')}


def main():
    began = time.perf_counter()
    sources = ['research/gcts-rl-renewal/'+f for f in ('commutativity13_guidance.py', 'commutativity13_executor_search.py',
               'commutativity_cluster_guidance.py', 'native_inventory_policy.py', 'commutativity13_structure.py', 'commutativity13_json.py', 'turtle.py')]
    inputs = [str((INPUT/f).relative_to(ROOT)) for f in ('execution-freeze.json', 'tree-audit-plan-stream.json', 'tree-audit-stream.json', 'integration-v2.json',
              'binding13.json.gz', 'base-r1-structure.jsonl', 'base-r2-structure.jsonl', 'fixed-r1-structure.jsonl', 'fixed-r2-structure.jsonl',
              'fixed-r1-search.json.gz', 'fixed-r2-search.json.gz', 'fixed-r1-summary.json', 'fixed-r2-summary.json')]
    pins = {p:sha(ROOT/p) for p in sources+inputs}
    freeze = json.loads((INPUT/'execution-freeze.json').read_text())
    audit_freeze = json.loads((INPUT/'tree-audit-plan-stream.json').read_text())
    for p in sources:
        declared = freeze['source_sha256'].get(p, audit_freeze['source_sha256'][p])
        assert pins[p] == declared, ('source changed', p)
    gate = json.loads((INPUT/'tree-audit-stream.json').read_text())
    assert gate['status'] == 'passed_complete_four13row_graph_and_proposal_traces'
    result = dict(status='diagnosing_read_only_saved_actions', source_input_sha256=pins,
                  parser_sha256=sha(Path(__file__)), no_engine_execution=True, no_model_training=True,
                  no_search_or_solver_or_native_queries=True, observations=[])
    for name in ('fixed-r1','fixed-r2'):
        result['observations'].append(analyze(name))
        print(json.dumps(result['observations'][-1]), flush=True)
    result.update(status='passed_read_only_saved_action_diagnostic', seconds=time.perf_counter()-began,
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (OUT/'diagnostic.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
