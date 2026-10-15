"""UNEXECUTED Source: separate exact Q1717 and Hilbert3b6 checking profiles.

The caller chooses authenticated modules and a conservative same-process local
deadline from the unchanged global budget. No imports, loaders, clocks or plans
here. Source/effective-method custody remains a future cold-caller obligation.
"""
VERSION = 'equality-operand-separate-checker-adapters-Source-v1'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def check_word(*, profile, context, commands, conclusion, primary,
               q_module, hilbert_checker_class, source_guard, local_deadline, tick):
    """No profile interchangeability and no open intermediate primary claim."""
    tick()
    need(type(primary) is bool and type(commands) is list and commands,
         'explicit scope and complete nonempty word')
    if primary:
        need(conclusion == context['target'], 'exact original closed target for donor acceptance')
    if profile == 'Q-six-rule-open-parameter':
        if primary:
            receipt = q_module.check_primitive_word(theory=context['theory'],
                parameters=context['parameters'], original_Gamma=context['ordered_Gamma'],
                commands=commands, target=conclusion, source_guard=source_guard,
                deadline=local_deadline)
            need(receipt['completed'] is True
                 and receipt['original_Gamma_target_sequent_accepted'] is True,
                 'unchanged Q public closed-target word checker')
            scope = 'original-closed-target-word'
        else:
            # NEW, explicitly narrow adapter scope: the unchanged six-rule
            # command relation allows parameter-scoped intermediate formulas.
            # It does not relax or replace the public CLOSED-target endpoint.
            boundary = q_module.Boundary(source_guard, local_deadline, 5000000)
            semantics = q_module.Semantics(context['theory'], context['parameters'],
                                           context['ordered_Gamma'], boundary)
            need(len(commands) <= 20000, 'unchanged complete word ceiling')
            goal, prior = semantics.formula(conclusion), []
            need(semantics.free(goal) <= set(context['parameters']),
                 'intermediate consequence has only original open parameters')
            for command in commands:
                tick()
                prior.append(semantics.command(command, prior))
            need(prior[-1] == goal, 'exact parameter-scoped intermediate conclusion')
            boundary.check()
            receipt = {'completed': True, 'parameter_scoped_consequence_accepted': True,
                       'rows': len(commands), 'original_Gamma_target_sequent_accepted': False}
            scope = 'parameter-scoped-intermediate-consequence'
    elif profile == 'Hilbert-five-rule-ground':
        need(context['parameters'] == [], 'Hilbert profile does not acquire Q open parameters')
        source_guard()
        receipt = hilbert_checker_class(context['theory']).proof(
            commands, context['ordered_Gamma'], conclusion)
        source_guard()
        need(receipt['original_ground_sequent_accepted'] is True
             and receipt['native_accepted'] is False, 'unchanged closed Hilbert proof checker')
        scope = 'original-closed-target-word' if primary else 'closed-intermediate-consequence'
    else:
        raise ValueError('no checker profile fallback or cross-ABI transplant')
    tick()
    return {'schema': 'equality-family-independent-word-adapter-result-v1',
        'completed': True, 'logical_accepted': True, 'profile': profile, 'scope': scope,
        'underlying_receipt': receipt, 'original_target_primary_accepted': bool(primary),
        'native_accepted': False, 'full_board_accepted': False, 'trajectory_accepted': False,
        'ROOT_library_admitted': False, 'ROOT_resource_accepted': False}
