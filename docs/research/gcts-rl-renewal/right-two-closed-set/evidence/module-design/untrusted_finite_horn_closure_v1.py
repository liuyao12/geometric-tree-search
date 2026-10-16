"""SOURCE ONLY UNTRUSTED full finite-Horn least-closure bitset proposal.

Only the checker-owned deeply immutable view is accepted. No mutable catalogue,
declaration, authority object, expected target answer, proof route or checker
function is supplied/imported. A separate checker must accept every certificate.
"""
import hashlib
import json

VERSION = 'untrusted-finite-Horn-least-closure-Source-v1'
VIEW = 'audited-finite-horn-view-v1'
BIT_ORDER = 'lsb0-formula-code'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def wire(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),
                      ensure_ascii=False,allow_nan=False)


def propose_least_closure(*, view, tick):
    """Complete forward saturation, then emit bits; no proof or admission.

    Every sweep scans every recipe. A fixed point is reached at all-zero change,
    without target-shortcut or word-length ceiling. Timeout/cancel propagates;
    it cannot emit a partial prefix as a certificate. Producer is untrusted even
    when it labels its own fixed point complete.
    """
    tick()
    require(type(view) is tuple and len(view) == 7 and view[0] == VIEW,
            'original checker-owned immutable-view ABI')
    _, binding, declaration_value_sha, formulas, rules, target, relation_sha = view
    require(type(formulas) is tuple and type(rules) is tuple and formulas
            and type(target) is int and 0 <= target < len(formulas),
            'whole finite view, no Boolean target')
    flags = [False for _ in formulas]
    sweeps = visits = known = 0
    while True:
        tick()
        changed = False
        for identifier, output, premises in rules:
            tick()
            visits += 1
            if not flags[output] and all(flags[code] for code in premises):
                flags[output] = True
                known += 1
                changed = True
        sweeps += 1
        tick()
        if not changed:
            break
    bits = bytearray((len(flags)+7)//8)
    for code, present in enumerate(flags):
        tick()
        if present:
            bits[code//8] |= 1 << (code%8)
    # Independent producer-side transcript hash is a claim, not checker authority.
    h = hashlib.sha256()
    for index, (identifier, output, inputs) in enumerate(rules):
        tick()
        h.update((wire([index,identifier,output,list(inputs)])+'\n').encode('utf8'))
    require(h.hexdigest() == relation_sha, 'immutable whole relation unchanged')
    candidate = {'schema':'finite-horn-closed-set-candidate-v1','binding':dict(binding),
        'formula_count':len(formulas),'recipe_count':len(rules),'target_code':target,
        'bit_order':BIT_ORDER,'bits_hex':bytes(bits).hex(),'relation_sha256':relation_sha}
    result = {'schema':'untrusted-finite-horn-least-closure-result-v1','version':VERSION,
        'closed_set_candidate':candidate,'target_in_set_claimed':bool(flags[target]),
        'least_fixed_point_claimed':True,'known_count_claimed':known,
        'complete_sweeps_claimed':sweeps,'recipe_visits_claimed':visits,
        'declaration_value_sha256':declaration_value_sha,
        'finite_horn_unreachable_accepted':False,'proof_accepted':False,
        'arithmetic_nonprovability_accepted':False,'point_state_accepted':False,
        'trajectory_accepted':False,'full24_accepted':False,'native_accepted':False,
        'ROOT_resource_accepted':False,'RL_accepted':False}
    wire(result)
    tick()
    return result
