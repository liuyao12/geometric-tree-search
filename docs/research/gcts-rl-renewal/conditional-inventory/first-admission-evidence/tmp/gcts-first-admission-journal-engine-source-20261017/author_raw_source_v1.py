"""Source transformation only; never imports/evaluates the engine."""
from pathlib import Path
import hashlib

HERE=Path('/private/tmp/gcts-first-admission-journal-engine-source-20261017')
PARENT=Path('/private/tmp/gcts-head-gated-family-engine-source-20261017/receptor_family_search_engine_v7.py')
raw=PARENT.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b53dbb82f8f06f6b844eaeaedbe2ec646b77e88c40473016d16adf894c8ead9e'
source=raw.decode()

def replace(old,new):
    global source
    assert source.count(old)==1
    source=source.replace(old,new)

replace("VERSION = 'lazy-unit-row-global-engine-v13-receptor-family-preferences-v7-full-exposure-census-provider8-head-gated'",
        "VERSION = 'lazy-unit-row-global-engine-v13-receptor-family-preferences-v8-first-admission-journal'")
replace('                 certify_fallback, transition_checker, tick, initial_state=None,',
        '                 certify_fallback, transition_checker, tick, milestone_observer, initial_state=None,')
replace('        self._family_callbacks = (family_proposer, family_consumer)\n',
'''        self._family_callbacks = (family_proposer, family_consumer)
        need(callable(milestone_observer), 'required raw milestone observer')
        self._milestone_observer = milestone_observer
        self._milestone_observer_anchor = milestone_observer
''')
replace('        found, reason, last_state = None, None, None\n\n        def walk(depth):\n            nonlocal found, last_state\n            while True:\n',
'''        found, reason, last_state = None, None, None
        # Diagnostic lifetime is local to this search, outside semantic rollback.
        # Current pinned Root observer only retains these owned builtin values.
        # States/ledgers are COW; plan receipts are not subsequently mutated;
        # _emit creates independent event objects and only appends to its list.
        # Never pass that live list, an iterator, private cert map or callback.
        milestone_observer = self._milestone_observer_anchor
        first_root_family_journal = False
        child_milestone_pending = False

        def walk(depth):
            nonlocal found, last_state, first_root_family_journal, child_milestone_pending
            while True:
                journal_this_root = False
''')

def call(stage,fields,indent):
    # Fixed literal Source emission; does not inspect any scientific data.
    pad=' '*indent
    lines=[
        'self.tick()',
        "need(self._milestone_observer is milestone_observer",
        "     and self._milestone_observer_anchor is milestone_observer,",
        "     'fixed original milestone observer endpoint')",
        "milestone_observer('"+stage+"', {",
        "    'schema': 'unit-row-first-family-engine-milestone-v1',",
        "    'stage': '"+stage+"', 'engine_version': VERSION,",
        "    'depth': "+('1' if stage=='FIRST_CHILD_DECISION_READY' else '0')+",",
        "    'diagnostic_only': True, 'scientific_acceptance': False,",
        *['    '+line for line in fields],
        '})',
        "need(self._milestone_observer is milestone_observer",
        "     and self._milestone_observer_anchor is milestone_observer,",
        "     'original milestone observer endpoint unchanged on return')",
        'self.tick()',
    ]
    return ''.join(pad+line+'\n' for line in lines)

replace('                decision = self.decision()\n                kind = decision[\'kind\']\n',
'''                decision = self.decision()
                if depth == 1 and child_milestone_pending:
                    child_milestone_pending = False
'''+call('FIRST_CHILD_DECISION_READY',[
"'state': self._state, 'decision': decision,",
"'decision_event': self.events[-1],",
"'prototype_census': self._family_prototype_census,"],20)+'''                kind = decision['kind']
''')
replace('''                    if self.family_proposer is not None:
                        branch_plan = self._select_family_branch(decision)
                        candidate = branch_plan['candidate']
''',
'''                    if self.family_proposer is not None:
                        # Selection may append fallback events; retain the actual
                        # completed global DECISION event before that delegate.
                        if depth == 0 and not first_root_family_journal:
                            root_decision_event = self.events[-1]
                        branch_plan = self._select_family_branch(decision)
                        candidate = branch_plan['candidate']
                        if depth == 0 and not first_root_family_journal:
                            first_root_family_journal = True
                            journal_this_root = True
'''+call('FIRST_ROOT_FAMILY_PLAN_READY',[
"'pre_state': self._state, 'decision': decision,",
"'decision_event': root_decision_event, 'plan': branch_plan,",
"'prototype_census': self._family_prototype_census,"],28))
replace('''                            self._adopt_family_branch(branch_plan)
                        else:
''',
'''                            self._adopt_family_branch(branch_plan)
                            if journal_this_root:
'''+call('FIRST_ROOT_FAMILY_EVENT_READY',[
"'state': self._state, 'pending_preferences': self._preferences,",
"'event': self.events[-1],"],32)+'''                        else:
''')
replace('''                    self.place(candidate)
                    child = walk(depth+1)
''',
'''                    self.place(candidate)
                    if journal_this_root:
'''+call('FIRST_ROOT_PRIMITIVE_PLACED',[
"'state': self._state, 'transition': self._last_transition,",
"'invalidation_event': self.events[-2], 'place_event': self.events[-1],"],24)+'''                        child_milestone_pending = True
                    child = walk(depth+1)
''')
out=HERE/'receptor_family_search_engine_v8.py'
assert not out.exists()
out.write_bytes(source.encode())
print(out,hashlib.sha256(source.encode()).hexdigest(),len(source.encode()))
