"""SOURCE ONLY: exact contextual certificate transport, never proof search.

ROOT may execute this syntax/binding adapter after source review. It copies an
already accepted certificate to the unchanged gcts-fol-1 request schema. Closed
ordered hypotheses become separately named native axioms because the existing
native top-level proof has no local-assumption argument. All rows are retained.
The adapter imports no project module and invokes no native or proof checker.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
INPUTS = HERE / 'frozen-inputs-v1.json'
OUTPUT_ROOT = ROOT / '.gcts-active/guard-native-bridge-progress-20261012'
MAXIMUM_BYTES = 10000000
NATIVE_PROTOCOL = 'gcts-fol-1'
SEQUENT_PROTOCOL = 'gcts-ground-sequent-bridge-1'
RULE_FIELDS = {
    'assumption': ('rule', 'formula', 'index'),
    'axiom': ('rule', 'formula', 'name'),
    'tautology': ('rule', 'formula'),
    'refl': ('rule', 'formula'),
    'instantiate': ('rule', 'formula', 'universal', 'term'),
    'distribute': ('rule', 'formula', 'variable', 'antecedent', 'consequent'),
    'eq_subst': ('rule', 'formula', 'variable', 'template', 'left', 'right'),
    'mp': ('rule', 'formula', 'antecedent', 'implication'),
    'generalize': ('rule', 'formula', 'variable', 'source'),
    'induction': ('rule', 'formula', 'variable', 'template'),
}


def need(value, label):
    if not value:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')


def value_sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def resolve(declared):
    p = Path(declared)
    return p if p.is_absolute() else ROOT / p


def pin(path, declared=None):
    p = resolve(path)
    before = p.stat()
    digest = hashlib.sha256()
    size = 0
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
            size += len(block)
    after = p.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    need(identity(before) == identity(after) and size == after.st_size,
         'immutable whole input/source bytes')
    if declared is None:
        try:
            declared = str(p.relative_to(ROOT))
        except ValueError:
            declared = str(p)
    return dict(path=declared, sha256=digest.hexdigest(), bytes=size)


def verify(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'},
         'exact declared pin record')
    need(pin(record['path'], record['path']) == record, 'exact pinned raw bytes')
    return resolve(record['path'])


def pairs(items):
    value = {}
    for key, item in items:
        need(key not in value, 'duplicate JSON field')
        value[key] = item
    return value


def decode(raw):
    need(type(raw) is bytes and len(raw) <= MAXIMUM_BYTES, 'bounded JSON bytes')
    def invalid(_):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=invalid)


def read_json(record):
    p = verify(record)
    need(record['bytes'] <= MAXIMUM_BYTES, 'bounded decoded metadata/certificate')
    raw = p.read_bytes()
    need(len(raw) == record['bytes'] and
         hashlib.sha256(raw).hexdigest() == record['sha256'], 'same decoded raw buffer')
    return decode(raw)


def free_names(formula):
    """Syntactic closure check only, not an inference or validity checker."""
    todo = [('formula', formula, frozenset())]
    free = set()
    while todo:
        kind, value, bound = todo.pop()
        need(type(value) is list and value and type(value[0]) is str, 'AST shape')
        tag = value[0]
        if kind == 'term':
            if tag == 'var':
                need(len(value) == 2 and type(value[1]) is str, 'variable AST')
                if value[1] not in bound:
                    free.add(value[1])
            else:
                need(tag == 'fun' and len(value) == 3 and type(value[1]) is str
                     and type(value[2]) is list, 'function AST')
                todo.extend(('term', child, bound) for child in value[2])
        elif tag == 'bot':
            need(len(value) == 1, 'bottom AST')
        elif tag == 'pred':
            need(len(value) == 3 and type(value[1]) is str and type(value[2]) is list,
                 'predicate AST')
            todo.extend(('term', child, bound) for child in value[2])
        elif tag == 'eq':
            need(len(value) == 3, 'equality AST')
            todo.extend(('term', child, bound) for child in value[1:])
        elif tag in ('imp', 'and', 'or'):
            need(len(value) == 3, 'binary formula AST')
            todo.extend(('formula', child, bound) for child in value[1:])
        elif tag == 'not':
            need(len(value) == 2, 'negation AST')
            todo.append(('formula', value[1], bound))
        else:
            need(tag == 'all' and len(value) == 3 and type(value[1]) is str,
                 'supported universal AST')
            todo.append(('formula', value[2], bound | {value[1]}))
    return free


def translate(certificate):
    """Request-independent copy/relabel operation; no target-specific route."""
    need(type(certificate) is dict and
         set(certificate) == {'theory', 'ordered_local_premises', 'proof', 'target'},
         'exact accepted certificate schema')
    theory = certificate['theory']
    need(type(theory) is dict and
         set(theory) == {'functions', 'predicates', 'axioms', 'schemas'} and
         type(theory['axioms']) is dict, 'unchanged original theory fields')
    gamma = certificate['ordered_local_premises']
    proof = certificate['proof']
    need(type(gamma) is list and type(proof) is list and proof, 'ordered arrays')
    need(all(not free_names(a) for a in gamma), 'closed hypotheses only')
    names = ['hypothesis-' + str(i) for i in range(len(gamma))]
    need(not set(names) & set(theory['axioms']), 'no original axiom-name collision')
    native_theory = copy.deepcopy(theory)
    for name, formula in zip(names, gamma):
        native_theory['axioms'][name] = copy.deepcopy(formula)
    commands = []
    mapping = []
    for row, command in enumerate(proof):
        need(type(command) is dict and command.get('rule') in RULE_FIELDS,
             'supported flat native command, never a block/macro')
        rule = command['rule']
        need(set(command) == set(RULE_FIELDS[rule]), 'strict native command fields')
        for field in (('antecedent', 'implication') if rule == 'mp' else
                      ('source',) if rule == 'generalize' else ()):
            need(type(command[field]) is int and 0 <= command[field] < row,
                 'strict-prior row references retained')
        if rule == 'assumption':
            index = command['index']
            need(type(index) is int and 0 <= index < len(gamma), 'occurrence index')
            need(command['formula'] == gamma[index], 'exact licensed occurrence formula')
            out = dict(rule='axiom', formula=copy.deepcopy(command['formula']),
                       name=names[index])
        else:
            out = copy.deepcopy(command)
        need(out['formula'] == command['formula'], 'no formula changed')
        commands.append(out)
        mapping.append(dict(row=row, original_rule=rule, native_rule=out['rule'],
                            original_command_sha256=value_sha256(command),
                            native_command_sha256=value_sha256(out),
                            occurrence_index=command['index'] if rule == 'assumption' else None,
                            native_axiom=out['name'] if rule == 'assumption' else None))
    need(commands[-1]['formula'] == certificate['target'], 'unchanged final target')
    request = dict(protocol=NATIVE_PROTOCOL, theory=native_theory,
                   target=copy.deepcopy(certificate['target']), blocks=[], proof=commands)
    original_problem = dict(protocol=SEQUENT_PROTOCOL, theory=copy.deepcopy(theory),
                            ordered_local_premises=copy.deepcopy(gamma),
                            target=copy.deepcopy(certificate['target']))
    native_problem = {k: request[k] for k in ('protocol', 'theory', 'target')}
    receipt = dict(
        schema='guard-native-contextual-translation-receipt-v1',
        status='syntax_translation_only_pending_independent_encoding_and_native_checks',
        original_problem=original_problem,
        original_problem_sha256=value_sha256(original_problem),
        native_problem_sha256=value_sha256(native_problem),
        native_request_sha256=value_sha256(request),
        original_proof_sha256=value_sha256(proof),
        native_proof_sha256=value_sha256(commands),
        original_formula_stream_sha256=value_sha256([r['formula'] for r in proof]),
        native_formula_stream_sha256=value_sha256([r['formula'] for r in commands]),
        original_rows=len(proof), native_rows=len(commands),
        ordered_occurrences=[dict(index=i, native_axiom=names[i], formula=copy.deepcopy(a))
                             for i, a in enumerate(gamma)],
        row_mapping=mapping, blocks=[],
        original_theory_preserved_except_explicit_closed_hypothesis_additions=True,
        reduction_scope='Original ordered sequent encoded as original theory plus exactly '
                        'one named closed axiom per hypothesis occurrence. No native '
                        'top-level assumption field exists. Repeated occurrences have '
                        'distinct names; no row is inserted, deleted, reordered or compacted.',
        native_accepted=None, independent_native_replay_accepted=None,
        finite_Wang_rectangle_accepted=None, universal_compiler_theorem=False,
        target_searches=0, native_queries=0, new_RL_training=False,
        all_five_qualification=False)
    return request, receipt


def bind_accepted_rows(certificate, point, reader, decision, required_rows):
    """Compare saved authoritative rows, without rerunning a proof/point checker."""
    need(decision['schema'] == 'ROOT-one-context-proof-control-final-decision-v1' and
         decision['selector'] == 'donor-repeated-guard' and
         decision['mode'] == 'fixed-whole-family-pool' and
         decision['status'] == 'accepted_ground_point_and_symbolic_certificate' and
         decision['ROOT_final_accepted'] is True and decision['point_symbolic_accepted'] is True
         and decision['trace_accepted'] is True, 'actual original ROOT acceptance')
    need(reader['selector'] == decision['selector'], 'same accepted context')
    lane = reader['lanes'][decision['mode']]
    need(lane['proof']['ROOT_final_accepted'] is True and
         lane['proof']['point_symbolic_accepted'] is True and
         lane['producer']['job_resource_accepted'] is True and
         lane['replay']['job_resource_accepted'] is True and
         lane['replay']['trace_accepted'] is True, 'original complete saved admission')
    rows = lane['rows']
    placements = point['placements']
    proof = certificate['proof']
    need(len(rows) == len(placements) == len(proof) == required_rows,
         'all actual rows retained, including repeated valid commands')
    for index, (row, placement, command) in enumerate(zip(rows, placements, proof)):
        need(row['row_index'] == index and placement['t'] == [[0, index, 1]],
             'exact original row order/placement support')
        need(row['command'] == placement['command'] ==
             placement['identity_preimage']['primitive_command'] == command,
             'exact accepted tile command correspondence')
        need(row['formula_ast'] == command['formula'] and
             row['placement_id'] == placement['id'] and
             row['t'] == placement['t'] and row['m'] == placement['m'],
             'full original point/formula provenance retained')


def write_new(path, value):
    raw = canonical(value) + b'\n'
    need(len(raw) <= MAXIMUM_BYTES, 'bounded complete output')
    with Path(path).open('xb') as stream:
        stream.write(raw)
    return pin(path)


def main():
    need(len(sys.argv) == 4 and sys.argv[1] == 'ROOT-translate-only',
         'ROOT-only frozen inputs and new output directory; no native dispatch')
    need(Path.cwd().resolve() == ROOT and Path(sys.argv[2]).resolve() == INPUTS.resolve(),
         'exact reviewed ROOT input contract')
    manifest = decode(INPUTS.read_bytes())
    need(manifest['schema'] == 'guard-native-bridge-frozen-input-contract-v1' and
         manifest['source_only'] is True and manifest['actual_execution_authorized'] is False,
         'frozen source/input interface does not authorize native execution')
    for record in manifest['closure']:
        verify(record)
    roles = manifest['input_roles']
    values = {role: read_json(record) for role, record in roles.items()}
    certificate = values['symbolic_certificate']
    decision = values['ROOT_final_decision']
    need(decision['certificate_pin'] == roles['point_certificate'] and
         decision['symbolic_certificate_pin'] == roles['symbolic_certificate'],
         'exact ROOT accepted public certificate pins')
    bind_accepted_rows(certificate, values['point_certificate'], values['reader_data'],
                       decision, manifest['required_rows'])
    need(len(certificate['ordered_local_premises']) == manifest['required_occurrences'],
         'entire ordered hypothesis inventory')
    request, receipt = translate(certificate)
    receipt.update(input_contract=pin(INPUTS), bridge_source=pin(__file__),
                   accepted_input_roles=copy.deepcopy(roles),
                   original_point_certificate_sha256=roles['point_certificate']['sha256'])
    output = Path(sys.argv[3]).resolve()
    need(output.parent == OUTPUT_ROOT.resolve() and not output.exists(),
         'fresh ROOT-owned translation directory, no overwrite/retry')
    need(OUTPUT_ROOT.is_dir(), 'ROOT creates and owns progress parent')
    output.mkdir()
    request_pin = write_new(output / 'native-request-v1.json', request)
    receipt['native_request_file'] = request_pin
    receipt_pin = write_new(output / 'translation-receipt-v1.json', receipt)
    print(json.dumps(dict(request=request_pin, receipt=receipt_pin, rows=len(request['proof']),
                          target_searches=0, native_queries=0, native_accepted=None)))


if __name__ == '__main__':
    main()
