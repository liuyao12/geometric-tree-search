"""Independent whole-hint state and deep-snapshot transaction reconstruction.

No production graph, hint controller or scheduler is imported. This is not a
search executor. Its methods only check the predeclared controlled operations.
"""
import copy
import hashlib
from full_point_oracle_v1 import canonical, digest, integer, need, points
from full_family_registry_v1 import equal, key, key_data


def graph_decision(state):
    graph = state.semantic()
    frontier = [r for r in range(state.height) if state.totals[r] < 1]
    if not frontier:
        return ['complete', None, 0, None]
    dead = [r for r in frontier if graph['domains'][r]['count'] == 0]
    forced = [r for r in frontier if graph['domains'][r]['count'] == 1]
    if dead or forced:
        row = min(dead or forced); kind = 'dead' if dead else 'forced'
    else:
        row = min(frontier, key=lambda r: (min([state.roots[r]] +
            [v for k, v in state.selected.items() if k[1] == r]), graph['domains'][r]['count'], r))
        kind = 'branch'
    generation = min([state.roots[row]] + [v for k, v in state.selected.items() if k[1] == row])
    return [kind, row, graph['domains'][row]['count'], generation]


def legal(state, value):
    try:
        i, row, refs = value
        integer(i); integer(row)
        if not 0 <= i < len(state.recipes) or not 0 <= row < state.height:
            return False
        if value in state.selected or value in state.excluded[row] or state.totals[row] >= 1:
            return False
        _, marks = points(state.recipes[i], row, refs, state.height)
        return state.compatible(marks)
    except (ValueError, IndexError, KeyError, TypeError):
        return False


def hint_view(descriptor, state, decision, revision, old=None):
    if old is not None and old['status'] == 'retired':
        return dict(status='retired', reason=old['reason'], eligible=[], decision=decision, revision=revision)
    members = [key(k) for k in descriptor['members']]
    pending = [k for k in members if k not in state.selected]
    reason = None
    if any(not legal(state, k) for k in pending):
        reason = 'pending_member_illegal'
    else:
        additions = {}
        for k in pending:
            additions[k[1]] = additions.get(k[1], 0) + 1
            if state.totals[k[1]] + additions[k[1]] > 1:
                reason = 'pending_aggregate_overcapacity'; break
        if reason is None and any((x, y) in state.marks and state.marks[x, y] != v
                                  for x, y, v in descriptor['aggregate_m']):
            reason = 'aggregate_remote_mark_conflict'
    eligible = [key_data(k) for k in pending if decision[0] == 'branch' and k[1] == decision[1]] if reason is None else []
    status = 'retired' if reason else ('consumed' if not pending else ('ready' if eligible else 'waiting'))
    return dict(status=status, reason=reason, eligible=eligible, decision=decision, revision=revision)


class SnapshotController:
    def __init__(self, state, descriptors, authority_epoch):
        self.state = copy.deepcopy(state)
        self.descriptors = copy.deepcopy(descriptors)
        self.authority_epoch = authority_epoch
        self.revision = 0
        self.hints = [dict(status='waiting', reason=None, eligible=[], decision=['unresolved', None, 0, None], revision=0)
                      for _ in descriptors]
        self.graph_changes = 0
        self.hint_changes = []
        self.checkpoints = {}
        self.resync()
        self.hint_changes.clear()

    def semantic(self):
        return dict(graph=self.state.semantic(), hint_states=copy.deepcopy(self.hints), hint_revision=self.revision,
            descriptor_ids=[d['descriptor_id'] for d in self.descriptors], root_rejected=[], authority_epoch=self.authority_epoch)

    def resync(self):
        decision = graph_decision(self.state)
        self.hint_changes.append(('revision', self.revision)); self.revision += 1
        for i, d in enumerate(self.descriptors):
            new = hint_view(d, self.state, decision, self.revision, self.hints[i])
            if new != self.hints[i]:
                self.hint_changes.append(('state', i, copy.deepcopy(self.hints[i]))); self.hints[i] = new
        return decision

    def ordering(self):
        decision = self.resync()
        need(decision[0] in ('branch', 'forced'), 'ordering only a current scheduler decision')
        preferred = []
        if decision[0] == 'branch':
            for h in self.hints:
                if h['status'] == 'ready':
                    for value in h['eligible']:
                        k = key(value)
                        if k not in preferred:
                            need(legal(self.state, k) and k[1] == decision[1], 'ready exact branch member')
                            preferred.append(k)
        # Stream complete fallback; there is no top-k shortlist or cluster degree.
        seen = set(preferred)
        for k in preferred:
            yield k
        for k, _, _ in self.state.raw_candidates(decision[1]):
            if k not in seen:
                yield k

    def checkpoint(self):
        cp = [self.graph_changes, len(self.hint_changes), self.revision,
              digest([d['descriptor_id'] for d in self.descriptors]), digest(self.semantic())]
        self.checkpoints[tuple(cp)] = (copy.deepcopy(self.state), self.graph_changes,
            copy.deepcopy(self.hint_changes), self.revision, copy.deepcopy(self.hints))
        return cp

    def rollback(self, value):
        need(tuple(value) in self.checkpoints, 'known exact paired parent checkpoint')
        self.state, self.graph_changes, self.hint_changes, self.revision, self.hints = copy.deepcopy(self.checkpoints[tuple(value)])
        need(digest(self.semantic()) == value[-1], 'exact independently saved parent restoration')

    def apply(self, value, scheduler=True):
        value = key(value) if type(value) is list else value
        need(legal(self.state, value), 'whole-model legal candidate')
        if scheduler:
            d = graph_decision(self.state)
            need(d[0] in ('branch', 'forced') and value[1] == d[1], 'global dead/forced/generation scheduler')
            if d[0] == 'forced':
                domain = list(self.state.raw_candidates(d[1]))
                need(len(domain) == 1 and domain[0][0] == value, 'independently exhausted forced singleton')
        self.state.apply(value); self.graph_changes += 1; self.resync()


def complete_census(state, label):
    """Independently enumerate every raw prototype translation in this state."""
    rows = []
    for row in range(state.height):
        count, recipes, h = 0, [0]*len(state.recipes), hashlib.sha256()
        for k, t, m in state.raw_candidates(row):
            h.update((canonical([key_data(k), t, m])+'\n').encode())
            count += 1; recipes[k[0]] += 1
        rows.append(dict(row=row, frontier=state.totals[row] < 1, degree=count,
            per_recipe_degree=recipes, complete_key_t_m_stream_sha256=h.hexdigest()))
    graph = state.semantic()
    need(all(r['degree'] == graph['domains'][r['row']]['count'] for r in rows), 'raw full exhaustion equals all factor counts')
    return dict(label=label, rows=rows, candidate_nodes=sum(r['degree'] for r in rows),
        incidence_edges=sum(r['degree'] for r in rows), frontier_points=sum(r['frontier'] for r in rows),
        candidate_node_incidence_reason='each primitive placement has exactly one unit positive-support edge')


def check_snapshot(controller, recorded, comparison):
    label = recorded['label']
    expected = complete_census(controller.state, label)
    equal({k: comparison[k] for k in expected}, expected, 'complete raw every-key/t/m stream/census')
    d = graph_decision(controller.state)
    if d[0] in ('branch', 'forced'):
        order = [key_data(k) for k in controller.ordering()]
        equal(comparison['decision_ordering'], order, 'complete preferred plus fallback permutation')
        need(len(order) == expected['rows'][d[1]]['degree'], 'no duplicate preference or omitted base key')
    equal(recorded['state'], controller.semantic(), 'whole recorded graph/hint semantic state')
    return expected
