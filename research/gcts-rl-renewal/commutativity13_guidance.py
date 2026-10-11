"""Exact indexed implementation of the frozen cluster proposal language.

Static incidence/ranking caches change cost, never pools, work counters or order.
No found commutativity word, ordinary witnesses or learned restriction is read.
"""
import collections
import hashlib
import itertools
from certificate_boundary_search import canonical
from commutativity_catalog import motif_families
from native_inference_inventory import aggregate
from commutativity_cluster_guidance import FEATURES, FIXED


def requirements(model, roles, row):
    if set(roles) != {0, 1, 2, 3}:
        return None
    c, g = model.metadata[roles[0]], model.metadata[roles[1]]
    if c['inference'] != g['inference'] or c['command'] != g['command']:
        return None
    inference = c['inference']
    r = model.rules[inference]
    out = []
    for i in range(2):
        m = model.metadata[roles[i + 2]]
        if m['mode'] != model.rule_modes[inference]:
            return None
        if i < len(r['premises']):
            if m['source'] is None or not 0 <= m['source'] < row:
                return None
            out.append((m['source'], r['premises'][i]))
        elif m['source'] is not None:
            return None
    return out


def vectors(items, model, state, graph):
    selected = collections.defaultdict(dict)
    for key in state.selected:
        selected[key[0]][key[1]] = key
    known, facts = set(), set()
    for row in range(model.spec['length']):
        refs = requirements(model, selected[row], row)
        if refs is not None and all(source in known for source, formula in refs):
            known.add(row)
            facts.add(canonical(model.metadata[selected[row][1]]['command']['formula']))
    out = []
    for item in items:
        if item is None:
            out.append([0.] * 8 + [1.])
            continue
        slots = {k[0] for k in item['members']}
        guards = [model.metadata[k] for k in item['members'] if k[1] == 1]
        members = collections.defaultdict(dict)
        for key in item['members']:
            members[key[0]][key[1]] = key
        refs = []
        for row in slots:
            combined = dict(selected[row])
            combined.update(members[row])
            refs.extend(requirements(model, combined, row) or [])
        if not refs:
            refs = [pair for key in item['members'] for pair in model.metadata[key]['requirements']]
        complete = sum(requirements(model, members[row], row) is not None for row in slots)
        out.append([float(any(g['inference'] in model.promoted_rules for g in guards)),
                    item['new_occupancy'] / 48,
                    float(any(canonical(g['command']['formula']) not in facts for g in guards)),
                    sum(source in known for source, formula in refs) / max(1, len(refs)),
                    float(any(g['command']['formula'] == model.spec['target'] for g in guards)),
                    item['new_marks'] / 1000, len(slots) / (max(slots) - min(slots) + 1),
                    complete / max(1, len(slots)), 0.])
    return out


class Join:
    def __init__(self, model, enable_lemmas=True):
        self.model = model
        self.families = motif_families(model.compiled) if enable_lemmas else []
        self.guards = {(k[0], m['inference']): k for k, m in model.metadata.items() if k[1] == 1}
        self.by_row = collections.defaultdict(list)
        for item in sorted(self.guards.items()):
            self.by_row[item[0][0]].append(item)
        self.bindings, self.incidence = [], collections.defaultdict(list)
        for family in self.families:
            for row in range(model.spec['length']):
                if (row, family['rewrite_rule']) not in self.guards:
                    continue
                for root in range(row):
                    for source in range(row):
                        if source == root:
                            continue
                        members = self.row(root, family['root_rule'], []) + self.row(row, family['rewrite_rule'], [source, root])
                        index = len(self.bindings)
                        self.bindings.append(members)
                        for key in members:
                            self.incidence[key].append(index)
        self.ports = collections.defaultdict(list)
        for point, keys in model.align_cache.items():
            for key in keys:
                if key[1] in (2, 3):
                    self.ports[(key[0], key[1], model.metadata[key]['mode'])].append(key)
        self.universe = sorted(model.metadata)
        self.key_bytes = {key: ('[' + ','.join(map(str, key)) + ']').encode() for key in self.universe}
        self.ranks = collections.OrderedDict()
        self.rank_cache_limit = 16

    def row(self, slot, rule, sources):
        guard = self.guards[slot, rule]
        mode = self.model.rule_modes[rule]
        return [(slot, 0, guard[2], 0), guard] + [(slot, 2 + i, mode, sources[i] + 1 if i < len(sources) else 0) for i in range(2)]

    def ranking(self, anchor, legal):
        if anchor not in self.ranks:
            prefix = b'[' + self.key_bytes[anchor] + b','
            self.ranks[anchor] = sorted(self.universe, key=lambda key: (hashlib.sha256(prefix + self.key_bytes[key] + b']').digest(), key))
            if len(self.ranks) > self.rank_cache_limit:
                self.ranks.popitem(last=False)
        self.ranks.move_to_end(anchor)
        return [key for key in self.ranks[anchor] if key in legal]

    def __call__(self, state, graph, point, limit=24, checks=2048):
        model, pool, seen, work = self.model, [], set(), collections.Counter()
        anchors = sorted(graph.domains[point])
        anchor_set = set(anchors)

        def save(kind, members):
            if work['validation_checks'] >= checks or len(pool) >= limit:
                return
            work['validation_checks'] += 1
            item = aggregate(model, members, state)
            if item is None or not any(key in anchor_set for key in item['pending']):
                return
            key = tuple(item['members'])
            if key in seen:
                return
            seen.add(key)
            item.update(kind=kind, level=0)
            pool.append(item)

        eligible = sorted({index for anchor in anchors for index in self.incidence.get(anchor, ())})
        for index in eligible:
            save('promoted-family', self.bindings[index])
            if work['validation_checks'] >= checks or len(pool) >= max(1, limit // 2):
                break
        work['family_pool'] = len(pool)
        occupied = {model.cache[key].occupancy[0][0]: key for key in state.selected}
        legality = {}

        def legal_key(key):
            if key not in legality:
                legality[key] = key in state.selected or state.legal(model.cache[key])
            return legality[key]

        for anchor in anchors[:4]:
            row = anchor[0]
            for (_, rule), guard in self.by_row[row]:
                pair = [(row, 0, guard[2], 0), guard]
                if anchor[1] < 2 and anchor not in pair:
                    continue
                if any(not legal_key(key) for key in pair):
                    continue
                mode = model.rule_modes[rule]
                fields = []
                for role in (2, 3):
                    point_at = (4 * row, role)
                    keys = [occupied[point_at]] if point_at in occupied else self.ports[(row, role, mode)]
                    fields.append([key for key in keys if model.metadata[key]['mode'] == mode and legal_key(key) and (anchor[1] != role or key == anchor)])
                for first, second in itertools.product(*fields):
                    save('complete-row', pair + [first, second])
                    if work['validation_checks'] >= checks or len(pool) >= max(1, limit - 4):
                        break
                if work['validation_checks'] >= checks or len(pool) >= max(1, limit - 4):
                    break
            if work['validation_checks'] >= checks or len(pool) >= max(1, limit - 4):
                break
        work['row_pool'] = len(pool) - work['family_pool']
        legal = {key for keys in graph.domains.values() for key in keys}
        for anchor in anchors[:4]:
            save('open-shape', [anchor])
            members = [anchor]
            for key in self.ranking(anchor, legal):
                if key in members:
                    continue
                if work['sample_pair_tests'] >= 64:
                    break
                work['sample_pair_tests'] += 1
                if aggregate(model, members + [key], state, record=False):
                    members.append(key)
                if len(members) == 3:
                    break
            if len(members) > 1:
                save('open-shape', members)
            if work['validation_checks'] >= checks or len(pool) >= limit:
                break
        work['items'] = len(pool)
        return pool + [None], dict(work)
