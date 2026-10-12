"""SOURCE ONLY independent fixture body, descriptor and Controller reconstruction.

All t/m data and primitive identities come from an independent literal graph.
No production BodyAuthority, descriptor compiler, Controller, overlay or expected
trace import. Synthetic authored proposals are not certified mathematical lemmas.
"""
import copy

CORE_SHA = 'e415664386b93cf9bbfeba92d6c35f40ca4cb25eb239de093134133b22c8adbd'
VERSION = 'whole-cluster-lifecycle-v1'


def graph_binding(graph, point):
    return dict(model_epoch=graph.epoch, context_id=graph.context_id,
        formula_registry_sha256=graph.registry_sha, authority_epoch=graph.authority_epoch,
        primitive_palette_sha256=point.digest(graph.recipes),
        boundary_sha256=point.digest(dict(height=graph.height, roots=graph.roots,
            fixed_marks=[[x, y, v] for (x, y), v in sorted(graph.fixed.items())],
            initial_selected=[point.key_data(k) for k in graph.initial_selected])),
        source_bindings_sha256=point.digest(graph.source_bindings),
        marking_version=point.MARKING, orientation='identity', core_sha256=CORE_SHA,
        native_accepted=False, engine_authority_activated=False)


def union(graph, keys, point):
    total, marking = {}, {}
    for key in keys:
        t, m = graph.points(key)
        for x, y, value in t:
            total[x, y] = total.get((x, y), 0) + value
            point.need(total[x, y] <= 1, 'whole distinct union capacity')
        for x, y, value in m:
            point.need((x, y) not in marking or marking[x, y] == value, 'whole internal marking agreement')
            marking[x, y] = value
    return ([[x, y, v] for (x, y), v in sorted(total.items())],
            [[x, y, v] for (x, y), v in sorted(marking.items())])


def body(graph, name, raw_keys, point):
    keys = [point.key(k) for k in raw_keys]
    point.need(keys and len(set(keys)) == len(keys) and
               all(a[1] < b[1] for a, b in zip(keys, keys[1:])), 'strict distinct authored body members')
    union(graph, keys, point)
    internal = {k[1] for k in keys}
    external = sorted({r for k in keys for r in k[2] if r not in internal})
    values, members = {}, []
    for i, row, sources in keys:
        recipe = graph.recipes[i]
        for source, code in zip(sources, recipe['inputs']):
            if source in external:
                point.need(source not in values or values[source] == code, 'one receptor formula per point')
                values[source] = code
        members.append(dict(row=row, recipe_id=recipe['id'], formula_code=recipe['output'],
                            ordered_inputs=list(sources)))
    ports = []
    for index, row in enumerate(external):
        readers = [dict(reader_row=k[1], primitive_input_port=port, formula_code=values[row])
                   for k in keys for port, source in enumerate(k[2]) if source == row]
        ports.append(dict(high_level_port=index, input_row=row, formula_code=values[row],
                          new_occupancy=0, readers=readers))
    result = dict(kind='authored_primitive_proposal_not_closed_lemma', name=name,
        canonical_input_rows=external, premise_codes=[values[r] for r in external], primitive_members=members,
        dependency_bindings=[], native_accepted=False, ordered_receptor_ports=ports)
    result['source_body_sha256'] = point.digest(result)
    result['mapped_body_sha256'] = result['source_body_sha256']
    return result


def registry(graph, corpus, names, source_bindings, point):
    bodies = [body(graph, name, corpus['proposal_specs'][name]['members'], point) for name in names]
    specs = [dict(name=b['name'], input_rows=b['canonical_input_rows'],
                  member_rows=[m['row'] for m in b['primitive_members']],
                  priority=corpus['proposal_specs'][b['name']]['priority']) for b in bodies]
    binding = graph_binding(graph, point)
    original_epoch = point.digest(dict(graph=binding, sources=source_bindings,
        bodies=[[b['name'], point.digest(b)] for b in bodies], version=VERSION))
    original = dict(graph_text=point.canonical(binding), source_text=point.canonical(source_bindings),
                    bodies=[[b['name'], point.canonical(b)] for b in bodies], epoch=original_epoch)
    wrapper_epoch = point.digest(dict(schema='fixture-only-whole-record-wrapper-v1',
        original_epoch=original_epoch, specs=specs, graph=binding))
    records = []
    recipe_ids = {recipe['id']: i for i, recipe in enumerate(graph.recipes)}
    for pool_index, (b, spec) in enumerate(zip(bodies, specs)):
        mapping = dict(zip(b['canonical_input_rows'], spec['input_rows']))
        mapping.update((m['row'], r) for m, r in zip(b['primitive_members'], spec['member_rows']))
        keys = [(recipe_ids[m['recipe_id']], row, tuple(mapping[r] for r in m['ordered_inputs']))
                for m, row in zip(b['primitive_members'], spec['member_rows'])]
        total, marks = union(graph, keys, point)
        marking = {(x, y): v for x, y, v in marks}
        for row, code in zip(spec['input_rows'], b['premise_codes']):
            point.need((1, row) not in marking or marking[1, row] == code, 'receptor alias marking union')
            marking[1, row] = code
        ports = [dict(high_level_port=port['high_level_port'], input_row=row, formula_code=code,
            new_occupancy=0, readers=[dict(reader_row=mapping[r['reader_row']],
                primitive_input_port=r['primitive_input_port'], formula_code=code,
                offset_value=row - mapping[r['reader_row']]) for r in port['readers']])
            for port, row, code in zip(b['ordered_receptor_ports'], spec['input_rows'], b['premise_codes'])]
        decorated = [graph.decorate(k) for k in keys]
        base = dict(version=VERSION, relation=b['kind'], graph_binding=binding, source_bindings=source_bindings,
            body_authority_epoch=original_epoch, body_name=b['name'], body_sha256=point.digest(b),
            source_body_sha256=b['source_body_sha256'], mapped_body_sha256=b['mapped_body_sha256'],
            dependency_bindings=[], ordered_input_rows=spec['input_rows'], ordered_member_rows=spec['member_rows'],
            ordered_receptor_ports=ports, fixed_priority=spec['priority'], members=[point.key_data(k) for k in keys],
            full_member_ids=[v['id'] for v in decorated], full_identity_preimages=[v['identity_preimage'] for v in decorated],
            aggregate_t=total, aggregate_m=[[x, y, v] for (x, y), v in sorted(marking.items())],
            native_accepted=False, native_authority_activated=False)
        base['descriptor_id'] = 'whole-cluster-' + point.digest(base)
        wrapped = copy.deepcopy(base)
        wrapped.update(body_authority_epoch=wrapper_epoch, original_body_authority_epoch=original_epoch,
            fixture_wrapper_schema='fixture-only-whole-record-wrapper-v1', fixture_pool_index=pool_index,
            fixture_original_record=copy.deepcopy(base),
            components=[dict(name=b['name'], ordered_receptor_ports=copy.deepcopy(ports),
                ordered_input_bindings=[dict(kind='fixture_receptor', index=i) for i in range(len(spec['input_rows']))],
                conclusion_code=b['primitive_members'][-1]['formula_code'], conclusion_row=spec['member_rows'][-1])],
            component_member_occurrences=len(keys), distinct_member_count=len(keys), shared_member_count=0)
        del wrapped['descriptor_id']
        wrapped['descriptor_id'] = 'fixture-whole-family-' + point.digest(wrapped)
        records.append(wrapped)
    return bodies, specs, original, wrapper_epoch, records


class WholeController:
    """Independent deep-snapshot transaction oracle, including full validation cost."""
    def __init__(self, graph, descriptors, epoch, point):
        self.graph, self.point, self.epoch = graph, point, epoch
        self.records = sorted(copy.deepcopy(descriptors), key=lambda d: (d['fixed_priority'], d['fixture_pool_index']))
        self.hints = [dict(status='waiting', reason=None, eligible=[],
                           decision=['unresolved', None, 0, None], revision=0) for _ in self.records]
        self.revision, self.trail = 0, []
        self.members_checked = self.mark_checks = self.whole_scans = self.resyncs = self.status_updates = self.retirements = 0
        self.sync()
        self.trail = []

    def full(self):
        return dict(graph=self.graph.semantic(), hint_states=copy.deepcopy(self.hints), hint_revision=self.revision,
            descriptor_ids=[d['descriptor_id'] for d in self.records], root_rejected=[], authority_epoch=self.epoch)

    def view(self, record, old, decision):
        p, g = self.point, self.graph
        if old['status'] == 'retired':
            return dict(status='retired', reason=old['reason'], eligible=[], decision=decision, revision=self.revision)
        self.whole_scans += 1
        pending, additional, reason = [], {}, None
        for raw, identity in zip(record['members'], record['full_member_ids']):
            k = p.key(raw); self.members_checked += 1
            if k in g.selected:
                g.metrics['lazy_id_constructions'] += 1
                if g.decorate(k)['id'] != identity:
                    reason = 'selected_identity_mismatch'; break
                continue
            if not g.legal(k):
                reason = 'pending_member_illegal'; break
            pending.append(k)
            for x, y, value in g.points(k)[0]:
                additional[x, y] = additional.get((x, y), 0) + value
                if g.totals[y] + additional[x, y] > 1:
                    reason = 'pending_aggregate_overcapacity'; break
            if reason:
                break
        if reason is None:
            for x, y, value in record['aggregate_m']:
                self.mark_checks += 1
                if (x, y) in g.marks and g.marks[x, y] != value:
                    reason = 'aggregate_remote_mark_conflict'; break
        eligible = [p.key_data(k) for k in pending if decision[0] == 'branch' and k[1] == decision[1]] if not reason else []
        status = 'retired' if reason else ('consumed' if not pending else ('ready' if eligible else 'waiting'))
        return dict(status=status, reason=reason, eligible=eligible, decision=decision, revision=self.revision)

    def sync(self):
        decision = self.graph.decision()
        self.trail.append(copy.deepcopy((self.hints, self.revision)))
        self.revision += 1
        for i, record in enumerate(self.records):
            old = self.hints[i]; new = self.view(record, old, decision)
            if old != new:
                # Source Controller stores one revision delta plus one changed
                # hint delta, so retain that exact checkpoint depth independently.
                self.trail.append(None)
                self.status_updates += 1
                self.retirements += int(old['status'] != 'retired' and new['status'] == 'retired')
                self.hints[i] = new
        self.resyncs += 1
        return decision

    def checkpoint(self):
        return [len(self.graph.trail), len(self.trail), self.revision,
                self.point.digest([d['descriptor_id'] for d in self.records]), self.point.digest(self.full())]

    def rollback(self, checkpoint):
        graph_depth, hint_depth, revision, registry_hash, snapshot_hash = checkpoint
        self.point.need(registry_hash == self.point.digest([d['descriptor_id'] for d in self.records]),
                        'paired immutable full registry')
        self.point.need(type(hint_depth) is int and 0 <= hint_depth <= len(self.trail), 'hint checkpoint depth')
        self.graph.rollback(graph_depth)
        while len(self.trail) > hint_depth:
            saved = self.trail.pop()
            if saved is not None:
                self.hints, self.revision = copy.deepcopy(saved)
        self.point.need(self.revision == revision and self.point.digest(self.full()) == snapshot_hash,
                        'exact complete graph/hint paired rollback')
