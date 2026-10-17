"""SOURCE ONLY: bounded source-free host-name candidate environments.

This policy never calls an expander, native language, checker, provider or engine.
Every binding is an untrusted syntax proposal. A separate observed-port inference
attempt must validate it jointly against all current receptor constraints.
"""
import re

VERSION = 'receptor-family-residual-host-binding-prefix-v1'
SCHEMA = 'receptor-family-residual-host-binding-prefix-v1'
DEFAULT_LIMITS = {'work': 100000, 'depth': 64, 'bindings': 64}
FLAGS = {'proposal_only': True, 'source_environment_used': False,
         'descriptor_fully_validated': False, 'ground_environment_checked': False,
         'proof_accepted': False, 'host_membership_accepted': False,
         'point_union_accepted': False, 'engine_activated': False,
         'pruning_accepted': False, 'runtime_qualified': False}


class BindingPrefixDataError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__('residual binding prefix ' + code + ': ' + detail)


class _Unfinished(Exception):
    pass


class _CallbackFailure(BaseException):
    def __init__(self, error):
        self.error = error


def require(ok, code, detail):
    if not ok:
        raise BindingPrefixDataError(code, detail)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names), 'FIELDS', 'exact object fields')


def identifier(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value) is not None,
            'ID', 'declared template identifier')
    return value


class _Work:
    def __init__(self, tick, limits):
        require(callable(tick), 'TICK', 'caller-owned cumulative tick')
        self.tick = tick
        self.steps = 0
        self.limits = dict(DEFAULT_LIMITS)
        if limits is not None:
            require(type(limits) is dict and set(limits) <= set(self.limits), 'LIMITS', 'known fields only')
            for key, value in limits.items():
                require(type(value) is int and 0 < value <= DEFAULT_LIMITS[key], 'LIMITS', 'bounded positive literal int')
                self.limits[key] = value

    def step(self, depth=0):
        if self.steps >= self.limits['work'] or depth > self.limits['depth']:
            raise _Unfinished('OWN_WORK_OR_DEPTH_PREFIX')
        try:
            self.tick()
        except BaseException as error:
            raise _CallbackFailure(error) from error
        self.steps += 1

    def copy(self, value, depth=0):
        self.step(depth)
        if value is None or type(value) in (str, int, bool):
            return value
        if type(value) is list:
            return [self.copy(v, depth+1) for v in value]
        require(type(value) is dict and all(type(k) is str for k in value), 'JSON', 'strict builtin JSON only')
        return {k: self.copy(v, depth+1) for k, v in value.items()}


def _theory_variable_names(value, allowed, found, work, depth=0):
    """Read literal var/all names from axiom AST data, without native admission."""
    work.step(depth)
    if type(value) is list:
        if (len(value) == 2 and value[0] == 'var' or len(value) == 3 and value[0] == 'all'):
            if type(value[1]) is str and value[1] in allowed:
                found.add(value[1])
        for child in value:
            _theory_variable_names(child, allowed, found, work, depth+1)
    elif type(value) is dict:
        for key in sorted(value):
            _theory_variable_names(value[key], allowed, found, work, depth+1)


def build_residual_binding_prefix(*, descriptor, host, residual_parameters,
                                  tick, limits=None):
    """Return {} then a fair bounded name-only prefix; never source bindings.

    The caller may first run observed inference on [{}], use its untrusted
    missing-parameter IDs here, then consume bindings[1:] with the remaining
    attempt allowance. Formula/term parameters are deliberately left absent:
    later observed equations may infer them once formal names become ground.
    """
    work = _Work(tick, limits)
    request = None
    bindings, entries, domains, deferred = [], [], [], []
    preferred, variable_order = [], []
    parameter_syntax_checked = False
    named_exhausted = None
    reason = 'OWN_PREFIX_UNFINISHED'
    try:
        request = work.copy({'descriptor': descriptor, 'host': host,
                             'residual_parameters': residual_parameters})
        d, h, residual = request['descriptor'], request['host'], request['residual_parameters']
        fields(d, ('schema','family_id','origin','provenance','required_host_features',
                   'parameters','hypotheses','inputs','outputs','body','side_conditions','dependencies'))
        require(d['schema'] == 'receptor-lemma-family-v2' and type(d['family_id']) is str
                and bool(d['family_id']), 'DESCRIPTOR', 'full named descriptor proposal')
        fields(h, ('schema','host_id','dialect','binding','authority','functions','predicates',
                   'variable_names','features','rules','ordered_Gamma'))
        require(h['schema'] == 'receptor-family-host-v1' and type(h['authority']) is dict,
                'HOST', 'complete syntax-host data, not proof authority')
        names = h['variable_names']
        require(type(names) is list and all(type(n) is str and n for n in names)
                and len(names) == len(set(names)), 'HOST', 'distinct declared variable names')
        require(type(h['predicates']) is dict, 'HOST', 'predicate signature table')
        for name, arity in h['predicates'].items():
            work.step()
            require(type(name) is str and bool(name) and type(arity) is int and arity >= 0,
                    'HOST', 'literal predicate name and arity')
        require(type(d['parameters']) is list, 'PARAMETER', 'ordered parameter declarations')
        parameters = {}
        for p in d['parameters']:
            work.step()
            require(type(p) is dict, 'PARAMETER', 'literal parameter object')
            kind = p.get('kind')
            if kind == 'VARIABLE':
                fields(p, ('id','kind','role','distinct_from','allowed_names_policy'))
                require(p['role'] in ('FREE_PARAMETER','BOUND','EIGEN','EQUALITY_HOLE')
                        and p['allowed_names_policy'] == 'HOST_DECLARED_SCOPE', 'PARAMETER', 'variable role/scope')
                refs = p['distinct_from']
            elif kind == 'PREDICATE_SYMBOL':
                fields(p, ('id','kind','arity'))
                require(type(p['arity']) is int and p['arity'] >= 0, 'PARAMETER', 'predicate arity')
                refs = []
            else:
                fields(p, ('id','kind','formal_variables','allowed_external_free_variables'))
                require(kind in ('FORMULA','TERM'), 'PARAMETER', 'known typed parameter')
                require(type(p['formal_variables']) is list and type(p['allowed_external_free_variables']) is list,
                        'PARAMETER', 'explicit formal/free VARIABLE IDs')
                for values in (p['formal_variables'], p['allowed_external_free_variables']):
                    require(all(type(v) is str for v in values) and len(values) == len(set(values)),
                            'PARAMETER', 'distinct formal/free IDs')
                refs = p['formal_variables'] + p['allowed_external_free_variables']
            pid = identifier(p['id'])
            require(pid not in parameters and pid not in ('GAMMA','INPUTS','OUTPUTS','ROOT_INPUTS'),
                    'PARAMETER', 'distinct nonreserved parameter ID')
            require(type(refs) is list and all(type(v) is str for v in refs)
                    and (kind != 'VARIABLE' or len(refs) == len(set(refs))),
                    'PARAMETER', 'typed VARIABLE references; distinct_from is unique')
            parameters[pid] = p
        for p in parameters.values():
            work.step()
            for ref in p.get('formal_variables', []) + p.get('allowed_external_free_variables', []) + p.get('distinct_from', []):
                work.step(); identifier(ref)
                require(ref in parameters and parameters[ref]['kind'] == 'VARIABLE',
                        'PARAMETER', 'declared VARIABLE reference')
        require(type(residual) is list and all(type(v) is str for v in residual)
                and len(residual) == len(set(residual)) and set(residual) <= set(parameters),
                'RESIDUAL', 'unique declared residual IDs, not a verification receipt')
        theory = h['authority'].get('theory', {})
        require(type(theory) is dict, 'HOST', 'optional theory object')
        axioms = theory.get('axioms', {})
        require(type(axioms) is dict, 'HOST', 'optional named axiom AST table')
        found, allowed = set(), set(names)
        for name in sorted(axioms):
            work.step()
            _theory_variable_names(axioms[name], allowed, found, work)
        preferred = sorted(found)
        variable_order = preferred + sorted(allowed-found)
        requested = set(residual)
        for pid, p in parameters.items():
            work.step()
            if pid not in requested:
                continue
            if p['kind'] == 'VARIABLE':
                values = variable_order
            elif p['kind'] == 'PREDICATE_SYMBOL':
                values = sorted(name for name, arity in h['predicates'].items() if arity == p['arity'])
            else:
                deferred.append({'parameter_id': pid, 'kind': p['kind'],
                    'policy': 'NOT_ENUMERATED_OBSERVED_INFERENCE_OR_UNKNOWN'})
                continue
            domains.append({'parameter_id': pid, 'kind': p['kind'],
                            'role': p.get('role'), 'values': work.copy(values)})
        parameter_syntax_checked = True
        named_exhausted = False
        work.step()
        bindings.append({}); entries.append({'binding_index': 0, 'channel': 'EMPTY', 'domain_indices': []})
        if not domains or any(not d['values'] for d in domains):
            named_exhausted = True
            reason = 'NO_RESIDUAL_NAME_PARAMETERS' if not domains else 'EMPTY_ARITY_COMPATIBLE_NAME_DOMAIN'
        else:
            lengths = [len(d['values']) for d in domains]
            diagonal, diagonal_end = 0, max(lengths)
            cartesian, cartesian_done = [0] * len(domains), False
            channel, seen = 'DIAGONAL', set()
            while len(bindings) < work.limits['bindings'] and not cartesian_done:
                work.step()
                if channel == 'DIAGONAL' and diagonal < diagonal_end:
                    indices = tuple(diagonal % size for size in lengths)
                    diagonal += 1
                    used_channel = 'DIAGONAL'
                else:
                    indices = tuple(cartesian)
                    used_channel = 'CARTESIAN'
                    i = len(cartesian)-1
                    while i >= 0:
                        work.step(); cartesian[i] += 1
                        if cartesian[i] < lengths[i]:
                            break
                        cartesian[i] = 0; i -= 1
                    if i < 0:
                        cartesian_done = True
                channel = 'CARTESIAN' if used_channel == 'DIAGONAL' else 'DIAGONAL'
                if indices in seen:
                    continue
                binding = {}
                for domain, index in zip(domains, indices):
                    work.step(); binding[domain['parameter_id']] = domain['values'][index]
                binding = work.copy(binding)
                seen.add(indices)
                bindings.append(binding)
                entries.append({'binding_index': len(bindings)-1, 'channel': used_channel,
                                'domain_indices': list(indices)})
            named_exhausted = cartesian_done
            reason = 'NAMED_CARTESIAN_DOMAIN_ENDED' if cartesian_done else 'BINDING_CAP_PREFIX_UNKNOWN'
    except _CallbackFailure as error:
        raise error.error
    except _Unfinished as error:
        reason = str(error)
    return {'schema': SCHEMA, 'version': VERSION,
        'status': 'BINDING_PREFIX' if bindings else 'UNKNOWN', 'request': request,
        'bindings': bindings, 'entries': entries, 'domains': domains,
        'unassigned_formula_term_parameters': deferred,
        'preferred_axiom_variable_names': preferred, 'variable_name_order': variable_order,
        'parameter_domain_syntax_checked': parameter_syntax_checked,
        'named_domain_exhausted': named_exhausted,
        'substitution_enumeration_complete': False,
        'work': {'steps': work.steps, 'limits': dict(work.limits), 'emitted_bindings': len(bindings)},
        'reason': reason, 'flags': dict(FLAGS)}
