"""Prospective executable selection overlay; no engine imports or CLI.

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

VERSION = 'paired-learned-whole-family-overlay-v1'


class LearnedFamilyOverlay:
    def __init__(self, controller, core, features, policy_math, weights, *,
                 epsilon=0.1, temperature=1.0, maximum_descriptors=64):
        self.control = controller
        self.graph = controller.graph
        self.core, self.features, self.math = core, features, policy_math
        core.integer(maximum_descriptors)
        if maximum_descriptors < 1 or len(controller.descriptors) > maximum_descriptors:
            raise ValueError('whole pool exceeds predeclared RL capacity; do not trim it')
        self.records = tuple(json.loads(d.text) for d in controller.descriptors)
        self.record_texts = tuple(core.canonical(record) for record in self.records)
        self.recipes = tuple(dict(output=r.output, inputs=tuple(r.inputs), rule=r.witness['rule'])
                             for r in self.graph.recipes)
        self.recipe_text = core.canonical(self.recipes)
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
                or self.core.canonical(self.recipes) != self.recipe_text):
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
        base = tuple(self.graph.candidates(decision.row))
        if len(base) != decision.count or len(set(base)) != len(base):
            raise ValueError('complete graph domain, never proposal shortlist')
        d = [decision.kind, decision.row, decision.count, decision.generation]
        menu = None
        if decision.kind == 'branch' and self.active_id is None:
            menu = self.features.menu_features(self._feature_graph(), self.recipes, self.graph.formulas,
                self.records, [hint.data() for hint in self.control.states], d)
        if decision.kind == 'forced' and len(base) != 1:
            raise ValueError('mandatory forced singleton bypass')
        return dict(decision=d, base=base, menu=menu, needs_one_draw=menu is not None,
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
        if (prepared['pool_epoch'] != self.pool_epoch or prepared['weight_sha256'] != self.weight_sha256
                or prepared['prepared_state_sha256'] != self.core.digest(self.semantic_state())):
            raise ValueError('stale or changed prepared family menu')
        current = self.graph.decision()
        if prepared['decision'] != [current.kind, current.row, current.count, current.generation]:
            raise ValueError('prepared selection must follow current global scheduler')
        base = prepared['base']
        if base != tuple(self.graph.candidates(current.row)):
            raise ValueError('every current primitive alternative retained in original order')
        policy = None
        if prepared['needs_one_draw']:
            if draw is None:
                raise ValueError('exact caller-supplied saved draw required')
            menu = prepared['menu']
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
        if any(k not in base for k in preferred):
            raise ValueError('whole preference remains within complete chosen-row domain')
        seen = set()
        ordered = []
        for k in tuple(preferred) + base:
            if k not in seen:
                seen.add(k); ordered.append(k)
        if len(ordered) != len(base) or set(ordered) != set(base):
            raise ValueError('full fallback permutation required')
        if current.kind == 'forced' and tuple(ordered) != base:
            raise ValueError('forced step cannot be policy-modified')
        stream = lambda keys: hashlib.sha256(('\n'.join(self.core.canonical(k.data()) for k in keys)
                                               + '\n').encode()).hexdigest()
        record = dict(version=VERSION, decision=prepared['decision'], pool_epoch=self.pool_epoch,
            weight_sha256=self.weight_sha256, policy=policy, active_descriptor_id=self.active_id,
            complete_base_count=len(base), base_keys_sha256=stream(base),
            preferred_keys=[k.data() for k in preferred], ordered_keys_sha256=stream(ordered),
            actual_first_key=ordered[0].data(),
            changed_first=bool(ordered and ordered[0] != base[0]),
            continuation='new-selection' if policy is not None else 'existing-whole-hint-or-forced-base',
            pending_scope='Structural obligations only; pending/empty marks never become hypotheses')
        self.history.append(copy.deepcopy(record))
        return tuple(ordered), record

    def semantic_state(self):
        return dict(controller=self.control.semantic_state(), active_descriptor_id=self.active_id,
                    overlay_revision=self.revision, pool_epoch=self.pool_epoch,
                    weight_sha256=self.weight_sha256)

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
