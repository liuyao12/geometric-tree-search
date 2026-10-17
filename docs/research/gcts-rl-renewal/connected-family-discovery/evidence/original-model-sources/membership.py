"""SOURCE ONLY: literal, scoped membership in the separately named B12/N44 profile.

This module supplies membership, not a syntax enumeration/count certificate or a
GCTS model. The injected original kernel checks every MEMBER. A resource callback
is guidance inside this delegate; callers own Source seals and final native gates.
"""
import copy
import hashlib
import json

VERSION = 'shared-bounded-six-rule-language-v2'
PROFILE_NAME = 'shared-bounded-six-rule-B12-N44-v2'
PROFILE_SHA256 = '227b3d4c1e8f5491365b5da580f59367300840d43d388d94e0657cf1b5f89c02'
KERNEL_SHA256 = '43bcd76ab1c672c5241f792cf898059a9f0157ace8f15b9684c7e48663db55a9'
KERNEL_BYTES = 10323
FIELDS = {'axiom': {'name'}, 'assumption': {'index'},
          'instantiate': {'universal', 'term'},
          'eq_subst': {'variable', 'template', 'left', 'right'},
          'mp': set(), 'generalize': {'variable'}}
ARITY = {'axiom': 0, 'assumption': 0, 'instantiate': 0,
         'eq_subst': 0, 'mp': 2, 'generalize': 1}
STRONG_FLAGS = ('Root_resource_accepted', 'proof_accepted', 'point_model_accepted',
                'complete_ground_counts_accepted', 'legacy_embedding_accepted',
                'GCTS_advantage_accepted', 'RL_accepted')


class OutsideLanguage(ValueError):
    """A completed, definite syntax/rule exclusion, never a budget conclusion."""
    def __init__(self, reason, evidence=None):
        super().__init__(reason)
        self.reason = reason
        self.evidence = evidence


class MembershipUnknown(TimeoutError):
    pass


def need(ok, label):
    if not ok:
        raise OutsideLanguage(label)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def _no_number(value):
    raise OutsideLanguage('no JSON float/nonfinite value')


def _decode(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 1048576, 'bounded complete raw input')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_float=_no_number, parse_constant=_no_number)
    except RecursionError as error:
        raise MembershipUnknown('JSON depth computation unfinished') from error


def _name(value):
    need(type(value) is str and value and len(value.encode('utf-8')) <= 64,
         'bounded literal symbol/name')
    return value


def _flags():
    return {key: False for key in STRONG_FLAGS}


class BoundedLanguage:
    OutsideLanguage = OutsideLanguage

    def __init__(self, *, declaration_raw, expected_declaration_sha256, profile_raw,
                 source_bindings, kernel_module, local_deadline, tick):
        need(callable(tick), 'resource callback')
        self.tick = tick
        tick()
        need(type(expected_declaration_sha256) is str and
             hashlib.sha256(declaration_raw).hexdigest() == expected_declaration_sha256,
             'exact caller-bound declaration bytes')
        need(type(profile_raw) is bytes and hashlib.sha256(profile_raw).hexdigest() == PROFILE_SHA256,
             'selected complete raw policy V2')
        profile = _decode(profile_raw)
        need(profile.get('profile_name') == PROFILE_NAME and
             profile.get('schema') == 'ROOT-shared-bounded-six-rule-language-policy-v2',
             'selected policy schema/name')
        self.policy = profile
        self.declaration = _decode(declaration_raw)
        need(type(self.declaration) is dict and
             {'theory', 'ordered_Gamma', 'parameters', 'target', 'height'} <= set(self.declaration),
             'whole logical input fields')
        need(type(self.declaration['height']) is int and self.declaration['height'] == 24,
             'original fixed primitive word height24')
        need(type(source_bindings) is dict and source_bindings, 'caller-authenticated Source map')
        for role, capsule in source_bindings.items():
            _name(role)
            need(type(capsule) is dict and {'sha256', 'bytes'} <= set(capsule), 'Source raw capsule')
            need(type(capsule['sha256']) is str and len(capsule['sha256']) == 64 and
                 all(c in '0123456789abcdef' for c in capsule['sha256']) and
                 type(capsule['bytes']) is int and capsule['bytes'] > 0, 'exact Source hash/length types')
        need('kernel' in source_bindings and source_bindings['kernel']['sha256'] == KERNEL_SHA256 and
             source_bindings['kernel']['bytes'] == KERNEL_BYTES and
             kernel_module.VERSION == 'arithmetic-open-parameter-six-rule-Q-v1',
             'original43b kernel authority supplied by authenticated caller')
        self.source_bindings = copy.deepcopy(source_bindings)
        self.kernel_module = kernel_module
        self.theory = copy.deepcopy(self.declaration['theory'])
        self.parameters = copy.deepcopy(self.declaration['parameters'])
        self.gamma = copy.deepcopy(self.declaration['ordered_Gamma'])
        self.target = copy.deepcopy(self.declaration['target'])
        need(type(self.theory) is dict and set(self.theory) == {'functions', 'predicates', 'axioms', 'schemas'}
             and self.theory['schemas'] == [], 'exact theory and no added schema')
        for kind in ('functions', 'predicates'):
            need(type(self.theory[kind]) is dict, 'whole signature table')
            for symbol, arity in self.theory[kind].items():
                _name(symbol)
                need(type(arity) is int and 0 <= arity <= 4, 'literal signature arity')
        need(type(self.theory['axioms']) is dict and type(self.parameters) is list and
             len(self.parameters) <= 4 and len(set(self.parameters)) == len(self.parameters),
             'named axioms/distinct parameters')
        for parameter in self.parameters:
            _name(parameter)
        need(type(self.gamma) is list, 'whole occurrence-ordered Gamma')
        self.parameter_set = frozenset(self.parameters)
        names = set(self.parameters)
        for formula in list(self.theory['axioms'].values()) + self.gamma + [self.target]:
            names.update(self._literal_names(formula))
        self.input_names = frozenset(names)
        self.binder_names = frozenset(names | {'fresh' + str(i) for i in range(32)})
        suffix = 0
        while 'hole' + str(suffix) in names:
            tick()
            suffix += 1
        self.hole = 'hole' + str(suffix)
        for axiom_name, formula in self.theory['axioms'].items():
            _name(axiom_name)
            self.formula(formula)
            need(not self.free(formula), 'every original named axiom closed')
        for formula in self.gamma:
            self.formula(formula)
        self.formula(self.target)
        need(not self.free(self.target), 'original exact closed target')
        self.forbidden = frozenset().union(*(self.free(f) for f in self.gamma))
        logical_input = {'theory': self.theory, 'parameters': self.parameters,
                         'ordered_Gamma': self.gamma, 'target': self.target, 'height': 24}
        binding = {'profile_name': PROFILE_NAME, 'profile_sha256': PROFILE_SHA256,
                   'declaration_sha256': expected_declaration_sha256,
                   'logical_input_sha256': digest(logical_input),
                   'source_bindings_sha256': digest(self.source_bindings)}
        binding['language_epoch'] = digest(binding)
        self.binding = binding
        self.kernel = kernel_module.QChecker(self.theory, self.parameters, self.gamma,
                                              deadline=local_deadline, maximum_visits=5000000,
                                              maximum_depth=64, maximum_fresh=32)
        tick()

    def _literal_names(self, formula):
        # Complete literal AST walk; depth/resource failure is not exclusion evidence.
        names, pending = set(), [(formula, 0)]
        while pending:
            self.tick()
            value, depth = pending.pop()
            if depth > 64:
                raise MembershipUnknown('input name census depth unfinished')
            need(type(value) is list and value, 'literal input AST for complete name census')
            if value[0] == 'var':
                need(len(value) == 2, 'variable fields')
                names.add(_name(value[1]))
            elif value[0] == 'all':
                need(len(value) == 3, 'universal fields')
                names.add(_name(value[1]))
                pending.append((value[2], depth + 1))
            elif value[0] in ('fun', 'pred'):
                need(len(value) == 3 and type(value[2]) is list, 'symbol AST fields')
                pending.extend((x, depth + 1) for x in value[2])
            elif value[0] == 'bot':
                need(len(value) == 1, 'bottom fields')
            else:
                need(value[0] in ('eq', 'not', 'imp', 'and', 'or'), 'known literal AST constructor')
                pending.extend((x, depth + 1) for x in value[1:])
        return names

    def _step(self, depth):
        self.tick()
        if depth > 64:
            raise MembershipUnknown('scoped syntax depth computation unfinished')

    def _term(self, value, scope, depth):
        self._step(depth)
        need(type(value) is list and value, 'literal term')
        if value[0] == 'var':
            need(len(value) == 2 and _name(value[1]) in scope, 'term lexical scope')
            return 1
        need(len(value) == 3 and value[0] == 'fun' and type(value[2]) is list,
             'function fields')
        need(type(value[1]) is str and value[1] in self.theory['functions'] and
             len(value[2]) == self.theory['functions'][value[1]], 'function signature/arity')
        count = 1 + sum(self._term(child, scope, depth + 1) for child in value[2])
        need(count <= 12, 'OUT_OF_PROFILE_TERM_NODES')
        return count

    def term(self, value):
        return self._term(value, self.parameter_set, 0)

    def _formula(self, value, scope, depth):
        self._step(depth)
        need(type(value) is list and value, 'literal formula')
        tag = value[0]
        if tag == 'bot':
            need(len(value) == 1, 'bottom fields')
            count = 1
        elif tag == 'eq':
            need(len(value) == 3, 'equality fields')
            count = 1 + self._term(value[1], scope, depth + 1) + self._term(value[2], scope, depth + 1)
        elif tag == 'pred':
            need(len(value) == 3 and type(value[2]) is list and type(value[1]) is str and
                 value[1] in self.theory['predicates'] and
                 len(value[2]) == self.theory['predicates'][value[1]], 'predicate signature/arity')
            count = 1 + sum(self._term(t, scope, depth + 1) for t in value[2])
        elif tag == 'all':
            need(len(value) == 3 and _name(value[1]) in self.binder_names, 'finite literal binder namespace')
            count = 1 + self._formula(value[2], scope | {value[1]}, depth + 1)
        else:
            need((tag == 'not' and len(value) == 2) or
                 (tag in ('imp', 'and', 'or') and len(value) == 3), 'known connective/arity')
            count = 1 + sum(self._formula(f, scope, depth + 1) for f in value[1:])
        need(count <= 44, 'OUT_OF_PROFILE_FORMULA_NODES')
        return count

    def formula(self, value):
        return self._formula(value, self.parameter_set, 0)

    def contextual_formula(self, value, binder_environment):
        need(type(binder_environment) in (list, tuple) and
             all(type(v) is str and v in self.binder_names for v in binder_environment),
             'explicit literal binder environment')
        return self._formula(value, self.parameter_set | frozenset(binder_environment), 0)

    def template(self, value):
        need(type(value) is list and value and value[0] in ('eq', 'pred'), 'atomic transport template only')
        return self._formula(value, self.parameter_set | {self.hole}, 0)

    def term_names(self, value):
        self.tick()
        return {value[1]} if value[0] == 'var' else set().union(*(self.term_names(t) for t in value[2]))

    def free(self, value, all_names=False):
        self.tick()
        tag = value[0]
        if tag == 'all':
            result = self.free(value[2], all_names)
            return result | {value[1]} if all_names else result - {value[1]}
        if tag == 'eq':
            return self.term_names(value[1]) | self.term_names(value[2])
        if tag == 'pred':
            return set().union(*(self.term_names(t) for t in value[2]))
        if tag == 'bot':
            return set()
        return set().union(*(self.free(f, all_names) for f in value[1:]))

    def _substitute_term(self, value, variable, replacement):
        self.tick()
        if value[0] == 'var':
            return copy.deepcopy(replacement if value[1] == variable else value)
        return ['fun', value[1], [self._substitute_term(t, variable, replacement) for t in value[2]]]

    def substitute(self, value, variable, replacement):
        # Same literal capture algorithm as43b; only completed fresh exhaustion differs.
        self.tick()
        tag = value[0]
        if tag == 'all':
            binder, body = value[1:]
            if binder == variable or variable not in self.free(body):
                return copy.deepcopy(value)
            if binder in self.term_names(replacement):
                used = self.free(body, True) | self.term_names(replacement) | {variable, binder}
                suffix = 0
                while 'fresh' + str(suffix) in used:
                    self.tick()
                    suffix += 1
                if suffix >= 32:
                    raise OutsideLanguage('OUT_OF_PROFILE_FRESH_NAMESPACE',
                                          {'complete_used_names': sorted(used),
                                           'all32_names_present': True, 'first_free_suffix': suffix})
                new = 'fresh' + str(suffix)
                body = self.substitute(body, binder, ['var', new])
                binder = new
            return ['all', binder, self.substitute(body, variable, replacement)]
        if tag == 'eq':
            return ['eq', self._substitute_term(value[1], variable, replacement),
                    self._substitute_term(value[2], variable, replacement)]
        if tag == 'pred':
            return ['pred', value[1], [self._substitute_term(t, variable, replacement) for t in value[2]]]
        if tag == 'bot':
            return ['bot']
        return [tag] + [self.substitute(f, variable, replacement) for f in value[1:]]

    def primitive(self, witness, ordered_premises):
        self.tick()
        need(type(witness) is dict and type(witness.get('rule')) is str and
             witness['rule'] in FIELDS and
             set(witness) == {'rule', 'formula'} | FIELDS[witness['rule']], 'exact primitive witness fields')
        rule = witness['rule']
        need(type(ordered_premises) is list and len(ordered_premises) == ARITY[rule],
             'complete ordered/repeated premise list')
        self.formula(witness['formula'])
        for premise in ordered_premises:
            self.formula(premise)
        command = copy.deepcopy(witness)
        if rule == 'instantiate':
            universal, term = witness['universal'], witness['term']
            self.formula(universal)
            self.term(term)
            need(universal[0] == 'all', 'UI universal witness')
            expected = ['imp', universal, self.substitute(universal[2], universal[1], term)]
            need(witness['formula'] == expected, 'literal capture-safe UI result')
        elif rule == 'eq_subst':
            need(witness['variable'] == self.hole, 'selected distinguished template hole')
            self.template(witness['template'])
            self.term(witness['left'])
            self.term(witness['right'])
            expected = ['imp', ['eq', witness['left'], witness['right']], ['imp',
                        self.substitute(witness['template'], self.hole, witness['left']),
                        self.substitute(witness['template'], self.hole, witness['right'])]]
            need(witness['formula'] == expected, 'literal atomic transport result')
        elif rule == 'mp':
            command.update(antecedent=0, implication=1)
        elif rule == 'generalize':
            command['source'] = 0
        try:
            output = self.kernel.command(command, ordered_premises)
        except TimeoutError as error:
            raise MembershipUnknown('original kernel membership unfinished') from error
        except ValueError as error:
            raise OutsideLanguage('OUT_OF_PROFILE_PRIMITIVE: ' + str(error)) from error
        need(output == witness['formula'], 'original primitive output equality')
        preimage = {'binding': copy.deepcopy(self.binding),
                    'primitive_witness': copy.deepcopy(witness),
                    'ordered_premise_formulas': copy.deepcopy(ordered_premises)}
        self.tick()
        return {'schema': 'shared-bounded-primitive-member-v1', 'status': 'MEMBER',
                'binding': copy.deepcopy(self.binding), 'identity_preimage': preimage,
                'primitive_id': digest(preimage),
                'output_formula_id': digest(witness['formula']),
                'ordered_input_formula_ids': [digest(f) for f in ordered_premises],
                'logical_acceptance': False}


def make_language(*, declaration_raw, expected_declaration_sha256, profile_raw,
                  source_bindings, kernel_module, local_deadline, tick):
    return BoundedLanguage(declaration_raw=declaration_raw,
                           expected_declaration_sha256=expected_declaration_sha256,
                           profile_raw=profile_raw, source_bindings=source_bindings,
                           kernel_module=kernel_module, local_deadline=local_deadline, tick=tick)


def check_primitive_record(*, language, primitive_witness, ordered_premise_formulas, tick):
    tick()
    result = language.primitive(primitive_witness, ordered_premise_formulas)
    tick()
    return result


def check_word(*, language, commands, tick):
    need(type(commands) is list and 0 < len(commands) <= 24, 'complete word length1..24')
    prior, rows = [], []
    for command_index, command in enumerate(commands):
        tick()
        need(type(command) is dict and type(command.get('rule')) is str and command['rule'] in FIELDS,
             'primitive command rule')
        rule = command['rule']
        refs = []
        witness = copy.deepcopy(command)
        if rule == 'mp':
            need(set(command) == {'rule', 'formula', 'antecedent', 'implication'}, 'exact MP command')
            refs = [witness.pop('antecedent'), witness.pop('implication')]
        elif rule == 'generalize':
            need(set(command) == {'rule', 'formula', 'variable', 'source'}, 'exact UG command')
            refs = [witness.pop('source')]
        for index in refs:
            need(type(index) is int and 0 <= index < command_index, 'strict prior literal ordered ref')
        row = language.primitive(witness, [prior[index] for index in refs])
        row.update(command_index=command_index, ordered_refs=refs)
        rows.append(row)
        prior.append(copy.deepcopy(command['formula']))
    need(prior[-1] == language.target, 'exact original closed target at final row')
    need(not language.free(prior[-1]), 'closed final word')
    tick()
    return dict({'schema': 'shared-bounded-six-rule-word-membership-v1',
                 'completed': True, 'all_commands_in_language': True,
                 'rows': rows, 'command_count': len(commands),
                 'commands_sha256': digest(commands), 'binding': copy.deepcopy(language.binding),
                 'original_Gamma_preserved': True, 'exact_target': True,
                 'logical_acceptance': False}, **_flags())
