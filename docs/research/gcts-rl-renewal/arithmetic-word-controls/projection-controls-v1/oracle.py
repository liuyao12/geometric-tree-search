"""Independent numerical subcomponent; no clocks, project imports or proof claim.

Only the explicitly authorized isolated control worker may execute this Source.
Float ratios are decoded from IEEE754 bits, not float.as_integer_ratio. Synthetic
edge cases are oracle controls, not observations of a production helper/clock.
"""
import struct

VERSION = 'Q-isolated-projection-binary64-oracle-Source-v1'
SIGN = 1 << 63
MASK = (1 << 64) - 1
FRACTION = (1 << 52) - 1
LOW_ORDER = 0x0010000000000000
HIGH_ORDER = 0xffefffffffffffff
CAPTURE_NAMES = (
    'global_deadline_ns', 'producer_pair', 'local_before', 'global_after',
    'remaining_ns', 'local_lower', 'numerator', 'denominator',
    'bound_numerator', 'bound_denominator', 'local_deadline', 'local_began',
    'deadline_numerator', 'deadline_denominator', 'final_global')


def require(condition, message):
    if condition is not True:
        raise ValueError(message)


def reduced(numerator, denominator):
    require(type(numerator) is int and type(denominator) is int
            and denominator > 0, 'exact integer rational')
    a, b = abs(numerator), denominator
    while b:
        a, b = b, a % b
    return numerator // a, denominator // a


def bits_ratio(bits):
    require(type(bits) is int and 0 <= bits <= MASK, 'binary64 bits')
    exponent = (bits >> 52) & 2047
    fraction = bits & FRACTION
    require(exponent != 2047, 'finite binary64 only')
    significand = fraction if exponent == 0 else (1 << 52) + fraction
    power = -1074 if exponent == 0 else exponent - 1075
    numerator = -significand if bits & SIGN else significand
    if power >= 0:
        return reduced(numerator << power, 1)
    return reduced(numerator, 1 << -power)


def float_bits(value):
    require(type(value) is float, 'literal float')
    return int.from_bytes(struct.pack('>d', value), 'big')


def bits_float(bits):
    bits_ratio(bits)
    return struct.unpack('>d', bits.to_bytes(8, 'big'))[0]


def order_bits(order):
    require(type(order) is int and LOW_ORDER <= order <= HIGH_ORDER,
            'finite ordered binary64 key')
    return (order ^ SIGN) if order & SIGN else ((~order) & MASK)


def predecessor_bits(bits):
    bits_ratio(bits)
    if bits & (SIGN - 1) == 0:
        result = SIGN + 1
    elif bits & SIGN:
        result = bits + 1
    else:
        result = bits - 1
    bits_ratio(result)
    return result


def compare_ratios(left, right):
    difference = left[0] * right[1] - right[0] * left[1]
    return (difference > 0) - (difference < 0)


def floor_bits(numerator, denominator):
    """Independent integer binary search over the entire finite binary64 order."""
    target = reduced(numerator, denominator)
    require(compare_ratios(bits_ratio(order_bits(LOW_ORDER)), target) <= 0,
            'rational below finite binary64 range')
    lo, hi = LOW_ORDER, HIGH_ORDER
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if compare_ratios(bits_ratio(order_bits(mid)), target) <= 0:
            lo = mid
        else:
            hi = mid - 1
    return order_bits(lo)


def nearest_bits(numerator, denominator):
    """Round an exact rational to nearest binary64, ties to even; finite only."""
    target = reduced(numerator, denominator)
    lower_bits = floor_bits(*target)
    lower = bits_ratio(lower_bits)
    if compare_ratios(lower, target) == 0:
        return lower_bits
    lower_order = ((~lower_bits) & MASK) if lower_bits & SIGN else lower_bits ^ SIGN
    if lower_order == HIGH_ORDER:
        # The overflow threshold lies half a last-binade ULP above max finite.
        threshold = reduced(lower[0] * 1 + (1 << 970), 1)
        require(compare_ratios(target, threshold) < 0, 'rounding would overflow')
        return lower_bits
    upper_bits = order_bits(lower_order + 1)
    upper = bits_ratio(upper_bits)
    midpoint = reduced(lower[0] * upper[1] + upper[0] * lower[1],
                       2 * lower[1] * upper[1])
    comparison = compare_ratios(target, midpoint)
    if comparison < 0:
        return lower_bits
    if comparison > 0:
        return upper_bits
    return lower_bits if lower_bits & 1 == 0 else upper_bits


def scalar(record, kind):
    require(type(record) is dict and record.get('kind') == kind, 'wire scalar kind')
    if kind == 'none':
        require(set(record) == {'kind'}, 'exact None wire')
        return None
    if kind in ('int', 'bool'):
        expected_type = int if kind == 'int' else bool
        require(set(record) == {'kind', 'value'} and type(record['value']) is expected_type,
                'literal typed wire value')
        return record['value']
    require(kind == 'float' and set(record) == {'kind', 'hex', 'ratio'},
            'exact float wire')
    require(type(record['hex']) is str and len(record['hex']) <= 32,
            'bounded canonical float hex')
    value = float.fromhex(record['hex'])
    require(value.hex() == record['hex'], 'canonical roundtrip float hex')
    bits = float_bits(value)
    ratio = bits_ratio(bits)
    require(type(record['ratio']) is list and len(record['ratio']) == 2
            and all(type(v) is int for v in record['ratio'])
            and record['ratio'] == list(ratio), 'independently decoded ratio matches wire')
    return value, bits, ratio


def audit_observation(record):
    require(type(record) is dict and set(record) == {
        'case_id', 'global_deadline_ns', 'producer_pair', 'captured', 'returned'},
        'exact observed-sample record')
    require(type(record['case_id']) is str and 0 < len(record['case_id']) <= 128,
            'bounded case identity')
    deadline = record['global_deadline_ns']
    producer = record['producer_pair']
    require(type(deadline) is int and 0 <= deadline < (1 << 63)
            and type(producer) is bool, 'expected deadline/mode')
    captured = record['captured']
    require(type(captured) is dict and set(captured) == set(CAPTURE_NAMES),
            'complete successful helper scalar capture')
    require(scalar(captured['global_deadline_ns'], 'int') == deadline
            and scalar(captured['producer_pair'], 'bool') is producer,
            'actual argument linkage')
    ints = {name: scalar(captured[name], 'int') for name in (
        'global_after', 'remaining_ns', 'numerator', 'denominator',
        'bound_numerator', 'bound_denominator', 'deadline_numerator',
        'deadline_denominator', 'final_global')}
    before, before_bits, before_ratio = scalar(captured['local_before'], 'float')
    lower, lower_bits, lower_ratio = scalar(captured['local_lower'], 'float')
    local_deadline, deadline_bits, deadline_ratio = scalar(captured['local_deadline'], 'float')
    require(lower_bits == predecessor_bits(before_bits), 'genuine finite predecessor sample')
    require(compare_ratios(lower_ratio, before_ratio) < 0, 'strict downward sample')
    global_after, final_global = ints['global_after'], ints['final_global']
    remaining = deadline - global_after
    require(0 <= global_after <= final_global < deadline < (1 << 63)
            and 0 < remaining <= 20000000000, 'same-domain timely exact remainder')
    require(ints['remaining_ns'] == remaining, 'captured remainder')
    require((ints['numerator'], ints['denominator']) == lower_ratio,
            'captured lower ratio independently decoded')
    bound = (lower_ratio[0] * 1000000000 + remaining * lower_ratio[1],
             lower_ratio[1] * 1000000000)
    original_bound = (before_ratio[0] * 1000000000 + remaining * before_ratio[1],
                      before_ratio[1] * 1000000000)
    require((ints['bound_numerator'], ints['bound_denominator']) == bound,
            'captured bound independently reconstructed')
    require((ints['deadline_numerator'], ints['deadline_denominator']) == deadline_ratio,
            'captured final deadline ratio independently decoded')
    require(compare_ratios(before_ratio, deadline_ratio) < 0
            and compare_ratios(deadline_ratio, bound) <= 0
            and compare_ratios(deadline_ratio, original_bound) <= 0,
            'strict future and both exact conservative upper bounds')
    returned = record['returned']
    require(type(returned) is list and len(returned) == 2, 'actual return pair wire')
    require(scalar(returned[1], 'float')[1] == deadline_bits,
            'actual returned deadline equals captured bits')
    if producer:
        began, began_bits, began_ratio = scalar(captured['local_began'], 'float')
        require(scalar(returned[0], 'float')[1] == began_bits,
                'actual returned producer origin equals captured bits')
        require(local_deadline == began + 20.0, 'unchanged producer float expression')
        require(nearest_bits(began_ratio[0] + 20 * began_ratio[1], began_ratio[1])
                == deadline_bits, 'independently rounded exact producer addition')
    else:
        scalar(captured['local_began'], 'none')
        scalar(returned[0], 'none')
    return {'schema': 'Q-independent-observed-projection-certificate-v1',
            'case_id': record['case_id'], 'passed': True,
            'remaining_ns': remaining, 'local_before_bits': '%016x' % before_bits,
            'local_lower_bits': '%016x' % lower_bits,
            'local_deadline_bits': '%016x' % deadline_bits,
            'independent_bound_ratio': list(reduced(*bound)),
            'proof_accepted': False, 'full52_qualified': False,
            'resource_fit_accepted': False}


def run_numerical_controls():
    """Fixed synthetic oracle cases, independent of any native sampled clocks."""
    rows = []
    literals = (
        ('positive-zero', 0, (0, 1)),
        ('negative-zero', SIGN, (0, 1)),
        ('positive-min-subnormal', 1, (1, 1 << 1074)),
        ('negative-min-subnormal', SIGN + 1, (-1, 1 << 1074)),
        ('smallest-normal', 1 << 52, (1, 1 << 1022)),
        ('one', 0x3ff0000000000000, (1, 1)),
        ('predecessor-one', 0x3fefffffffffffff, ((1 << 53) - 1, 1 << 53)),
        ('twenty', 0x4034000000000000, (20, 1)))
    for case_id, bits, expected in literals:
        require(bits_ratio(bits) == expected and float_bits(bits_float(bits)) == bits,
                'literal bit/ratio and signed-zero roundtrip')
        rows.append({'case_id': 'numeric-decode-' + case_id, 'passed': True,
                     'bits': '%016x' % bits, 'ratio': list(expected)})
    bounds = (
        ('zero-one-ns', 0, 1, True),
        ('negative-zero-one-ns', SIGN, 1, True),
        ('subnormal-one-ns', 1, 1, True),
        ('smallest-normal-one-ns', 1 << 52, 1, True),
        ('one-one-ns', 0x3ff0000000000000, 1, True),
        ('power-boundary-joint20', 0x3ff0000000000000, 20000000000, True),
        ('large-ulp-one-ns', 0x43b0000000000000, 1, False),
        ('large-ulp-joint20', 0x43b0000000000000, 20000000000, False))
    for case_id, bits, remaining, expected_future in bounds:
        lo = bits_ratio(predecessor_bits(bits))
        bound = (lo[0] * 1000000000 + remaining * lo[1], lo[1] * 1000000000)
        result_bits = floor_bits(*bound)
        ratio = bits_ratio(result_bits)
        require(compare_ratios(ratio, bound) <= 0, 'synthetic conservative bound')
        future = compare_ratios(bits_ratio(bits), ratio) < 0
        require(future is expected_future, 'frozen representability expectation')
        rows.append({'case_id': 'numeric-bound-' + case_id, 'passed': True,
                     'future_available': future, 'result_bits': '%016x' % result_bits,
                     'scope': 'synthetic exact-rational floor; not production-helper execution'})
    # Independent exact halfway/cancellation tests of the addition oracle.
    addition = (
        ('cancel-to-zero', -20, 1, 0),
        ('halfway-at-one-even', (1 << 53) + 1 - 20 * (1 << 53), 1 << 53,
         0x3ff0000000000000),
        ('halfway-at-one-odd', (1 << 53) + 3 - 20 * (1 << 53), 1 << 53,
         0x3ff0000000000002))
    for case_id, numerator, denominator, expected_bits in addition:
        result_bits = nearest_bits(numerator + 20 * denominator, denominator)
        require(result_bits == expected_bits, 'frozen exact addition rounding expectation')
        rows.append({'case_id': 'numeric-add-' + case_id, 'passed': True,
                     'result_bits': '%016x' % result_bits,
                     'scope': 'synthetic exact rational addition; not helper/native clock'})
    for case_id, deadline_bits, expected_began, expected_recovered in (
            ('subnormal-cancels', 1, 0xc034000000000000, 0),
            ('unit-retained', 0x3ff0000000000000,
             0xc033000000000000, 0x3ff0000000000000)):
        deadline_ratio = bits_ratio(deadline_bits)
        began_bits = nearest_bits(deadline_ratio[0] - 20 * deadline_ratio[1],
                                  deadline_ratio[1])
        began_ratio = bits_ratio(began_bits)
        recovered_bits = nearest_bits(began_ratio[0] + 20 * began_ratio[1],
                                      began_ratio[1])
        require(began_bits == expected_began and recovered_bits == expected_recovered,
                'frozen producer subtraction/addition cancellation expectation')
        require(float_bits(bits_float(began_bits) + 20.0) == recovered_bits,
                'actual synthetic binary64 addition agrees with exact oracle')
        rows.append({'case_id': 'numeric-producer-' + case_id, 'passed': True,
                     'began_bits': '%016x' % began_bits,
                     'recovered_bits': '%016x' % recovered_bits,
                     'roundtrip_retained': recovered_bits == deadline_bits,
                     'scope': 'synthetic local pair; not helper/native clock'})
    for case_id, bits in (('infinity', 0x7ff0000000000000),
                          ('negative-infinity', 0xfff0000000000000),
                          ('nan', 0x7ff8000000000001)):
        rejected = False
        try:
            bits_ratio(bits)
        except ValueError:
            rejected = True
        require(rejected, 'nonfinite ratio rejected')
        rows.append({'case_id': 'numeric-reject-' + case_id, 'passed': True,
                     'outcome': 'explicit_nonfinite_rejection'})
    for case_id, remaining in (('zero-remainder', 0), ('foreign-remainder', 20000000001)):
        require(not 0 < remaining <= 20000000000, 'unavailable remainder domain')
        rows.append({'case_id': 'numeric-reject-' + case_id, 'passed': True,
                     'outcome': 'explicit_outside_original_joint20_domain'})
    return {'schema': 'Q-independent-synthetic-numeric-controls-v1',
            'scope': 'pure numeric oracle controls only; no production helper or native sampling',
            'rows': rows, 'case_count': len(rows), 'passed': True,
            'proof_accepted': False, 'full52_qualified': False,
            'resource_fit_accepted': False}
