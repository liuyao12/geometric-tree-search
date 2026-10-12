"""SOURCE ONLY streamed selection overlay; no engine imports or CLI.

The caller supplies the exact pinned Controller/core/features/math modules. This
implements selection of already validated single/pair whole-union proposals,
not new topology construction. Controller descriptors/priorities stay immutable.
ROOT must separately implement/review the owned driver and independent replay
before any scientific invocation of these methods.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

VERSION = 'compact-paired-learned-whole-family-overlay-v3'


CONSUMER_SCHEMA = 'ROOT-whole-streamed-consumer-source-binding-v1'
CONSUMER_ROLES = frozenset(('streamed_overlay', 'streamed_dfs', 'streamed_proposal', 'features31', 'policy_math'))
BORROWED_SHA = {'features31': '644e4cd195f98c1ca3f97c3fcba84dfdbc18765454512435702951cc6169a14b',
                'policy_math': '61b772b45ed4523ba4c14ae4519cd9dae53c21d4dc1b1681689011707831c294'}


def checked_pin(pin):
    # Byte/source binding only; acceptance of both reviews and all dynamic,
    # inventory, catalog and resource gates belongs to ROOT's separate wrapper.
    if (type(pin) is not dict or set(pin) != {'path', 'sha256', 'bytes'}
            or type(pin['path']) is not str or type(pin['sha256']) is not str
            or len(pin['sha256']) != 64 or type(pin['bytes']) is not int or pin['bytes'] < 0):
        raise ValueError('exact whole closed pin required')
    path = Path(pin['path'])
    if not path.is_absolute() or str(path.resolve()) != str(path):
        raise ValueError('consumer bindings use canonical ABS paths')
    h = hashlib.sha256(); count = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); count += len(block)
    if h.hexdigest() != pin['sha256'] or count != pin['bytes']:
        raise ValueError('closed consumer/source/review bytes changed')
    return pin


def check_consumer_binding(binding, graph, core, features, policy_math, *, dfs_function=None):
    required = {'schema', 'graph_binding_sha256', 'source_records',
                'ROOT_source_review_pin', 'independent_source_review_pin'}
    if type(binding) is not dict or set(binding) != required or binding['schema'] != CONSUMER_SCHEMA:
        raise ValueError('exact whole consumer-source binding required')
    if binding['graph_binding_sha256'] != core.digest(graph.compact_graph_binding()):
        raise ValueError('consumer closure belongs to a different complete catalog/runtime')
    records = binding['source_records']
    if type(records) is not list:
        raise ValueError('complete consumer source records required')
    by_role = {}
    for record in records:
        if type(record) is not dict or set(record) != {'role', 'path', 'sha256', 'bytes'}:
            raise ValueError('exact role pin required')
        role = record['role']
        if role not in CONSUMER_ROLES or role in by_role:
            raise ValueError('missing, duplicate or unknown consumer role')
        pin = {key: record[key] for key in ('path', 'sha256', 'bytes')}
        checked_pin(pin)
        if role in BORROWED_SHA and pin['sha256'] != BORROWED_SHA[role]:
            raise ValueError('exact unchanged31-feature and policy-math sources required')
        by_role[role] = pin
    if set(by_role) != CONSUMER_ROLES:
        raise ValueError('all whole consumer roles required')
    origins = {'streamed_overlay': LearnedFamilyOverlay.__init__.__code__.co_filename,
               'features31': features.menu_features.__code__.co_filename,
               'policy_math': policy_math.distribution.__code__.co_filename}
    if dfs_function is not None:
        origins['streamed_dfs'] = dfs_function.__code__.co_filename
    if any(str(Path(origin).resolve()) != by_role[role]['path'] for role, origin in origins.items()):
        raise ValueError('provided consumer function does not originate in exact bound source')
    checked_pin(binding['ROOT_source_review_pin']); checked_pin(binding['independent_source_review_pin'])
    return core.canonical(binding)


class LearnedFamilyOverlay:
    def __init__(self, controller, core, features, policy_math, weights, *,
                 epsilon=0.1, temperature=1.0, maximum_descriptors=64, consumer_binding):
        self.control = controller
        self.graph = controller.graph
        self.core, self.features, self.math = core, features, policy_math
        self.consumer_binding_text = check_consumer_binding(consumer_binding, self.graph, core, features, policy_math)
        self.consumer_binding_sha256 = core.digest(json.loads(self.consumer_binding_text))
        core.integer(maximum_descriptors)
        if maximum_descriptors < 1 or len(controller.descriptors) > maximum_descriptors:
            raise ValueError('whole pool exceeds predeclared RL capacity; do not trim it')
        self.records = tuple(json.loads(d.text) for d in controller.descriptors)
        self.record_texts = tuple(core.canonical(record) for record in self.records)
        self.recipes, self.formula_heads = self.graph.feature_views()
        self._feature_views = (self.recipes, self.formula_heads)
        self.recipe_binding_text = core.canonical(self.graph.compact_graph_binding())
        self.registry_text = core.canonical([[d.identifier, d.priority, d.text]
                                              for d in controller.descriptors])
        self.pool_epoch = core.digest(dict(authority_epoch=controller.authority.epoch,
                                          registry=json.loads(self.registry_text)))
        self.weights = policy_math.vector(weights, 'frozen episode weights')
        if set(self.weights) != set(features.FEATURE_NAMES):
            raise ValueError('all exact feature coefficients retained, including zero')
        self.weight_sha256 = core.digest(self.weights)
        self.epsilon = policy_math.finite_number(epsilon, 'epsilon')
        self.temperature = policy_math.finite_number(temperature, 'temperature')
        if not 0.0 <= self.epsilon <= 1.0 or self.temperature <= 0.0:
            raise ValueError('declared mixture hyperparameters required')
        self.active_id = None
        self.revision = 0
        self.trail = []
        self.history = []  # Cumulative observation/learning log, never rollback authority.

    def _check_registry(self):
        actual = self.core.canonical([[d.identifier, d.priority, d.text]
                                      for d in self.control.descriptors])
        if (actual != self.registry_text or self.core.digest(self.weights) != self.weight_sha256
                or tuple(self.core.canonical(record) for record in self.records) != self.record_texts
                or self.core.canonical(self.graph.compact_graph_binding()) != self.recipe_binding_text
                or self.recipes is not self._feature_views[0] or self.formula_heads is not self._feature_views[1]
                or any(view.catalog is not self.graph.catalog for view in self._feature_views)
                or self.core.digest(json.loads(self.consumer_binding_text)) != self.consumer_binding_sha256):
            raise ValueError('registry or episode weights changed without a new source gate')

    def _set_active(self, identifier):
        if identifier is not None and identifier not in {d.identifier for d in self.control.descriptors}:
            raise ValueError('only a whole source-authorized descriptor may be activated')
        self.trail.append((self.active_id, self.revision))
        self.active_id = identifier
        self.revision += 1

    def _current_hint(self):
        if self.active_id is None:
            return None
        for descriptor, hint in zip(self.control.descriptors, self.control.states):
            if descriptor.identifier == self.active_id:
                return hint
        raise ValueError('active descriptor must remain in immutable whole registry')

    def after_resync(self):
        """Call after every primitive/forced step or justified child exclusion.

        Waiting is retained. Retirement/consumption ends the overlay preference,
        never changes graph legality or seeds a hypothesis. Forced moves always
        interrupt advice; the unchanged Controller has already revalidated all
        whole descriptors and all distant assigned marks.
        """
        self._check_registry()
        hint = self._current_hint()
        if hint is not None and hint.status in ('retired', 'consumed'):
            self._set_active(None)

    def _feature_graph(self):
        # Every assigned mark is read; no viewport/adjacency cutoff. Complete
        # domains/legality remain exclusively in the unchanged graph scheduler.
        return dict(height=self.graph.height, totals=list(self.graph.totals),
                    marks=[[*p, v, self.graph.mark_refs[p]] for p, v in sorted(self.graph.marks.items())],
                    selected_keys=[k.data() for k in self.graph.order],
                    initial_selected_keys=[k.data() for k in self.graph.initial_selected])

    def fact_potential(self):
        """Call after every actual primitive step, including forced interruptions."""
        available = self.features.available_rows(self._feature_graph(), self.recipes)
        return len(available['distinct_nonroot_codes'])

    def prepare(self, decision):
        """Exactly one resync and one complete domain, before optional draw.

        Every source-authorized hint remains registered, including waiting and
        retired descriptors. The menu contains NULL plus all waiting/ready hints.
        A previously selected waiting hint persists with base-only continuation;
        it is not a proved premise and does not trigger resampling.
        """
        self._check_registry()
        if decision != self.graph.decision() or decision.kind not in ('branch', 'forced'):
            raise ValueError('fresh mandatory global graph decision required')
        self.control.resync(decision)
        self.after_resync()
        base = self.graph.ordered_domain(decision)
        if len(base) != decision.count:
            raise ValueError('complete graph domain, never proposal shortlist')
        d = [decision.kind, decision.row, decision.count, decision.generation]
        menu = None
        if decision.kind == 'branch' and self.active_id is None:
            menu = self.features.menu_features(self._feature_graph(), self.recipes, self.formula_heads,
                self.records, [hint.data() for hint in self.control.states], d)
        if decision.kind == 'forced' and len(base) != 1:
            raise ValueError('mandatory forced singleton bypass')
        return dict(decision=d, base_domain_descriptor=base.descriptor(), menu=menu, needs_one_draw=menu is not None,
                    prepared_state_sha256=self.core.digest(self.semantic_state()),
                    pool_epoch=self.pool_epoch, weight_sha256=self.weight_sha256)

    def choose_prepared(self, prepared, draw=None):
        """Validate exact state, optionally select one whole proposal, full fallback.

        Caller owns one chronological saved RNG draw per new policy selection;
        no draw for forced propagation or waiting/ready continuation. RNG and
        cumulative policy logs are not rolled back. They cannot prune candidates.
        NULL suppresses EVERY fixed-priority preference for this operation.
        """
        self._check_registry()
        if (type(prepared) is not dict or set(prepared) != {'decision', 'base_domain_descriptor', 'menu',
                'needs_one_draw', 'prepared_state_sha256', 'pool_epoch', 'weight_sha256'}):
            raise ValueError('exact compact prepared transport; producer fields are not authority')
        if (prepared['pool_epoch'] != self.pool_epoch or prepared['weight_sha256'] != self.weight_sha256
                or prepared['prepared_state_sha256'] != self.core.digest(self.semantic_state())):
            raise ValueError('stale or changed prepared family menu')
        current = self.graph.decision()
        if prepared['decision'] != [current.kind, current.row, current.count, current.generation]:
            raise ValueError('prepared selection must follow current global scheduler')
        base = self.graph.ordered_domain(current)
        if self.core.canonical(prepared['base_domain_descriptor']) != self.core.canonical(base.descriptor()):
            raise ValueError('exact complete current primitive relation and canonical fallback required')
        # The prepared object is a caller-owned transport value, not authority.
        # Rebuild the complete canonical menu from the SAME verified state and
        # immutable inputs; neither a supplied hash nor a draw flag can make
        # altered features/action IDs authoritative. No resync occurs here,
        # because that would change the exact state being checked.
        expected_needs_one_draw = current.kind == 'branch' and self.active_id is None
        expected_menu = (self.features.menu_features(
            self._feature_graph(), self.recipes, self.formula_heads,
            self.records, [hint.data() for hint in self.control.states],
            [current.kind, current.row, current.count, current.generation])
            if expected_needs_one_draw else None)
        if (prepared['needs_one_draw'] is not expected_needs_one_draw
                or self.core.canonical(prepared['menu']) != self.core.canonical(expected_menu)):
            raise ValueError('prepared complete menu or draw requirement differs from verified state')
        policy = None
        if expected_needs_one_draw:
            if draw is None:
                raise ValueError('exact caller-supplied saved draw required')
            menu = expected_menu
            distribution = self.math.distribution(menu['action_ids'], menu['feature_vectors'], self.weights,
                epsilon=self.epsilon, temperature=self.temperature)
            choice = self.math.choose(distribution, draw)
            gradient = self.math.score_gradient(distribution, choice['chosen_index'])
            self._set_active(None if choice['chosen_id'] == 'NULL' else choice['chosen_id'])
            policy = dict(distribution=distribution, choice=choice, score_gradient=gradient,
                          menu=copy.deepcopy(menu))
        elif draw is not None:
            raise ValueError('forced or waiting continuation must consume no draw')
        preferred = ()
        hint = self._current_hint()
        if current.kind == 'branch' and hint is not None and hint.status == 'ready':
            preferred = hint.eligible
        if any(k.row != current.row or not self.graph.legal(k) for k in preferred):
            raise ValueError('whole preference remains within complete chosen-row domain')
        ordered = self.graph.ordered_domain(current, tuple(preferred))
        if len(ordered) != len(base):
            raise ValueError('full fallback relation retains every primitive candidate')
        if current.kind == 'forced' and preferred:
            raise ValueError('forced step cannot be policy-modified')
        base_first = base.first(); ordered_first = ordered.first()
        record = dict(version=VERSION, decision=prepared['decision'], pool_epoch=self.pool_epoch,
            weight_sha256=self.weight_sha256, policy=policy, active_descriptor_id=self.active_id,
            complete_base_count=len(base), base_domain_descriptor=base.descriptor(),
            preferred_keys=[k.data() for k in preferred], ordered_domain_descriptor=ordered.descriptor(),
            actual_first_key=ordered_first.data(), changed_first=ordered_first != base_first,
            literal_full_stream_hashes_measured=False,
            continuation='new-selection' if policy is not None else 'existing-whole-hint-or-forced-base',
            pending_scope='Structural obligations only; pending/empty marks never become hypotheses')
        self.history.append(copy.deepcopy(record))
        return ordered, record

    def semantic_state(self):
        return dict(controller=self.control.semantic_state(), active_descriptor_id=self.active_id,
                    overlay_revision=self.revision, pool_epoch=self.pool_epoch,
                    weight_sha256=self.weight_sha256, consumer_binding_sha256=self.consumer_binding_sha256)

    def checkpoint(self):
        self._check_registry()
        return dict(controller=self.control.checkpoint(), overlay_trail=len(self.trail),
                    active_descriptor_id=self.active_id, overlay_revision=self.revision,
                    pool_epoch=self.pool_epoch, semantic_sha256=self.core.digest(self.semantic_state()))

    def rollback(self, checkpoint):
        """Restore graph, whole hints AND selection overlay; keep cumulative costs."""
        self._check_registry()
        if checkpoint['pool_epoch'] != self.pool_epoch:
            raise ValueError('paired checkpoint retains exact source-body/pool authority')
        depth = self.core.integer(checkpoint['overlay_trail'])
        if not 0 <= depth <= len(self.trail):
            raise ValueError('valid overlay trail depth')
        self.control.rollback(checkpoint['controller'])
        while len(self.trail) > depth:
            self.active_id, self.revision = self.trail.pop()
        if (self.active_id != checkpoint['active_descriptor_id']
                or self.revision != checkpoint['overlay_revision']
                or self.core.digest(self.semantic_state()) != checkpoint['semantic_sha256']):
            raise ValueError('exact paired graph/hint/overlay rollback required')
