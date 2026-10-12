"""SOURCE ONLY: ROOT's whole native-input preparation and byte audit.

No native process, inference checker, search or learner is invoked here. Future
ROOT execution uses the unchanged syntax serializers and independent constructor
decoder, under a separately owned sixty-second / 768-MiB preparation phase.
The source author has not imported or invoked any project module/function.
"""
import copy
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CONTRACT = HERE / 'preparation-input-contract-v1.json'
OUTPUT_ROOT = ROOT / '.gcts-active/guard-native-bridge-progress-20261012'
PROJECT = ROOT / 'research/gcts-rl-renewal'
MAXIMUM_JSON_BYTES = 10000000
MAXIMUM_MICRO_JSON_BYTES = 268435456
HEAP_BAND_CELLS = 1048576
PINNED_PROGRAM = '877c47879b027b08f02d3923d1e6dd9ccaf9a12e354567109f1aaa640a8fb673'
PINNED_MICRO = '2f9e430b0b7034ed615d81c3e9b3978dc47ba4136686227a9b86df5779b203ac'
PINNED_TABLE = 'fd1621b29a7d497859c850a116b295956db99b3d7c4c076e3b78bed680d682dd'


def need(value, label):
    if not value:
        raise ValueError(label)


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('ascii')


def sha_value(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def resolve(path):
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def pin(path, declared=None):
    p = resolve(path)
    before = p.stat()
    h = hashlib.sha256()
    size = 0
    with p.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block)
            size += len(block)
    after = p.stat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    need(identity(before) == identity(after) and size == after.st_size,
         'whole immutable pinned source/input')
    if declared is None:
        try:
            declared = str(p.relative_to(ROOT))
        except ValueError:
            declared = str(p)
    return dict(path=declared, sha256=h.hexdigest(), bytes=size)


def verify(record):
    need(type(record) is dict and set(record) == {'path', 'sha256', 'bytes'},
         'exact declared whole pin')
    need(pin(record['path'], record['path']) == record, 'exact frozen source/input bytes')
    return resolve(record['path'])


def pairs(items):
    value = {}
    for key, item in items:
        need(key not in value, 'duplicate JSON field')
        value[key] = item
    return value


def decode(raw, maximum=MAXIMUM_JSON_BYTES):
    need(type(raw) is bytes and len(raw) <= maximum, 'whole bounded JSON input')
    def invalid(_):
        raise ValueError('nonfinite JSON')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_constant=invalid)


def read_json(record):
    p = verify(record)
    need(record['bytes'] <= MAXIMUM_JSON_BYTES, 'bounded exact metadata input')
    raw = p.read_bytes()
    need(len(raw) == record['bytes'] and hashlib.sha256(raw).hexdigest() == record['sha256'],
         'same raw buffer decoded')
    return decode(raw)


def read_gzip_json(record):
    p = verify(record)
    with gzip.open(p, 'rb') as stream:
        raw = stream.read(MAXIMUM_MICRO_JSON_BYTES + 1)
    verify(record)
    return decode(raw, MAXIMUM_MICRO_JSON_BYTES)


def require_translation(request, receipt, certificate):
    """Mechanical correspondence, without evaluating any inference rule."""
    need(set(request) == {'protocol', 'theory', 'target', 'blocks', 'proof'} and
         request['protocol'] == 'gcts-fol-1' and request['blocks'] == [],
         'exact unchanged native request fields')
    expected_theory = copy.deepcopy(certificate['theory'])
    gamma = certificate['ordered_local_premises']
    need(len(gamma) == 3 and len(certificate['proof']) == 24, 'whole accepted source extent')
    for index, formula in enumerate(gamma):
        name = 'hypothesis-' + str(index)
        need(name not in expected_theory['axioms'], 'no original theory overwrite')
        expected_theory['axioms'][name] = copy.deepcopy(formula)
    expected_commands = []
    for row, source in enumerate(certificate['proof']):
        if source['rule'] == 'assumption':
            index = source['index']
            need(type(index) is int and 0 <= index < len(gamma) and
                 source['formula'] == gamma[index], 'same indexed occurrence')
            command = dict(rule='axiom', formula=copy.deepcopy(source['formula']),
                           name='hypothesis-' + str(index))
        else:
            command = copy.deepcopy(source)
        expected_commands.append(command)
    need(request['theory'] == expected_theory and
         request['target'] == certificate['target'] and
         request['proof'] == expected_commands, 'all original rows/target/theory/context copied')
    original = dict(protocol='gcts-ground-sequent-bridge-1', theory=certificate['theory'],
                    ordered_local_premises=gamma, target=certificate['target'])
    need(receipt['schema'] == 'guard-native-contextual-translation-receipt-v1' and
         receipt['original_problem'] == original and
         receipt['original_problem_sha256'] == sha_value(original) and
         receipt['native_problem_sha256'] == sha_value({k: request[k] for k in ('protocol', 'theory', 'target')})
         and receipt['native_request_sha256'] == sha_value(request), 'whole translation receipt binding')
    need(receipt['original_rows'] == receipt['native_rows'] == 24 and
         receipt['original_proof_sha256'] == sha_value(certificate['proof']) and
         receipt['native_proof_sha256'] == sha_value(request['proof']) and
         receipt['original_formula_stream_sha256'] == receipt['native_formula_stream_sha256'] ==
         sha_value([command['formula'] for command in certificate['proof']]),
         'no compacting, alternative proof word or row elision')
    need(receipt['native_accepted'] is None and receipt['target_searches'] ==
         receipt['native_queries'] == 0, 'translation is not native acceptance')


def project_modules(records):
    """Future ROOT imports only the exact frozen serializer/decoder closure."""
    expected = {Path(r['path']).stem: r for r in records}
    need(set(expected) == {'proof_boundary', 'tree_machine', 'tape_tree_machine',
                           'tape_binary', 'audit_proof_boundary', 'audit_tree_kernel',
                           'audit_tape_kernel'}, 'exact complete reachable project module union')
    need(all(name not in sys.modules for name in expected), 'fresh serializer/decoder module cache')
    for record in records:
        p = verify(record)
        need(p.parent.resolve() == PROJECT.resolve() and p.suffix == '.py',
             'frozen existing project source namespace')
    sys.path.insert(0, str(PROJECT))
    try:
        producer = importlib.import_module('proof_boundary')
        binary = importlib.import_module('tape_binary')
        independent = importlib.import_module('audit_proof_boundary')
        for name, record in expected.items():
            need(name in sys.modules and Path(sys.modules[name].__file__).resolve() ==
                 verify(record).resolve(), 'actual loaded module source identity')
        return producer, binary, independent
    finally:
        sys.path.pop(0)


def write_json_gzip(path, value):
    raw = canonical(value) + b'\n'
    with Path(path).open('xb') as out:
        with gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as stream:
            stream.write(raw)
    return dict(file=pin(path), raw_sha256=hashlib.sha256(raw).hexdigest(), raw_bytes=len(raw))


def compress_raw(source, target):
    source = Path(source)
    before = pin(source)
    with source.open('rb') as src, Path(target).open('xb') as out:
        with gzip.GzipFile(fileobj=out, mode='wb', mtime=0) as stream:
            for block in iter(lambda: src.read(65536), b''):
                stream.write(block)
    need(pin(source) == before, 'closed raw binary during complete compression')
    return dict(file=pin(target), raw_sha256=before['sha256'], raw_bytes=before['bytes'])


def main():
    need(len(sys.argv) == 5 and sys.argv[1] == 'ROOT-prepare-only',
         'ROOT actual translated request/receipt and fresh preparation directory')
    need(Path.cwd().resolve() == ROOT, 'exact ROOT cwd')
    contract_pin = pin(CONTRACT)
    contract = read_json(contract_pin)
    need(contract['schema'] == 'guard-native-whole-input-preparation-source-contract-v1' and
         contract['source_only'] is True and contract['actual_execution_authorized'] is False,
         'source interface only, no native execution authority')
    need(contract['heap_band_cells'] == HEAP_BAND_CELLS and
         contract['preparation_limits'] == dict(seconds=60, peak_bytes=805306368),
         'prospective fixed preparation contract')
    for record in contract['closure']:
        verify(record)
    input_contract = read_json(contract['adapter_input_contract'])
    certificate = read_json(input_contract['input_roles']['symbolic_certificate'])
    request_pin, receipt_pin = pin(sys.argv[2]), pin(sys.argv[3])
    need(request_pin == contract['translated_request'] and
         receipt_pin == contract['translation_receipt'], 'exact once-only ROOT converted outputs')
    request, receipt = read_json(request_pin), read_json(receipt_pin)
    need(receipt['input_contract'] == contract['adapter_input_contract'] and
         receipt['bridge_source'] == contract['adapter_source'] and
         receipt['native_request_file'] == request_pin, 'actual translated output/source identity')
    require_translation(request, receipt, certificate)
    boundary = read_json(contract['boundary_metadata'])
    micro = read_gzip_json(contract['microcode_json'])
    need(boundary['program_sha256'] == sha_value(boundary['program']) == PINNED_PROGRAM and
         boundary['machine']['micro_sha256'] == sha_value(micro) == PINNED_MICRO and
         micro['program_sha256'] == PINNED_PROGRAM and
         boundary['machine']['literal_binary_sha256'] == PINNED_TABLE,
         'unchanged complete parser/program/micro/literal authority')
    need(micro['tapes'] == boundary['machine']['tapes'] == 43, 'unchanged band inventory')
    output = Path(sys.argv[4]).resolve()
    need(output.parent == OUTPUT_ROOT.resolve() and not output.exists() and OUTPUT_ROOT.is_dir(),
         'fresh ROOT-owned preparation directory; no overwrite/retry')
    producer, binary, independent = project_modules(contract['project_source_closure'])
    fixed, free = producer.boundary_words(request)
    template = copy.deepcopy(boundary['cases'][0]['initial'])
    initial = copy.deepcopy(template)
    problem = micro['boundary']['problem']
    certificate_band = micro['boundary']['certificate']
    heap = micro['heap']
    need(len({problem, certificate_band, heap}) == 3, 'distinct unchanged bands')
    for band, word in ((problem, fixed), (certificate_band, free)):
        initial['words'][band] = word + ':'
        initial['capacities'][band] = len(word) + 3
        initial['heads'][band] = 1
    need(template['capacities'][heap] <= HEAP_BAND_CELLS and
         len(template['words'][heap]) + 1 < HEAP_BAND_CELLS, 'blank-only heap band extension')
    initial['capacities'][heap] = HEAP_BAND_CELLS
    for band in range(43):
        if band not in (problem, certificate_band):
            need(initial['words'][band] == template['words'][band] and
                 initial['heads'][band] == template['heads'][band], 'immutable bootstrap word/head')
        if band not in (problem, certificate_band, heap):
            need(initial['capacities'][band] == template['capacities'][band], 'immutable other capacities')
    # This parses the whole fixed three plus free two values and validates the
    # exact canonical constructor heap/root. It does not run the micro machine.
    nodes, root = independent.expected_constructor(micro, initial, request)
    independent_input = independent.input_bytes(initial)
    independent_code = independent.code_bytes(micro)
    output.mkdir()
    raw_input = output / 'input.bin'
    raw_code = output / 'microcode.bin'
    binary.write_micro_input(initial, raw_input)
    binary.write_micro(micro, raw_code)
    need(raw_input.read_bytes() == independent_input, 'every whole input byte, independent serializer')
    need(raw_code.read_bytes() == independent_code, 'every micro table byte, independent serializer')
    frame = dict(schema='guard-native-whole-request-frame-v1', request=request,
                 request_sha256=sha_value(request), proposed_initial=initial,
                 original_template_sha256=sha_value(template),
                 original_heap_band_cells=template['capacities'][heap],
                 heap_band_cells=HEAP_BAND_CELLS, heap_band=heap,
                 input_sha256=pin(raw_input)['sha256'], input_bytes=pin(raw_input)['bytes'],
                 microcode_sha256=pin(raw_code)['sha256'], microcode_bytes=pin(raw_code)['bytes'],
                 constructor_nodes=len(nodes), constructor_root=root,
                 full_constructor_request_decode_checked=True,
                 complete_input_bytes_independently_equal=True,
                 program_sha256=PINNED_PROGRAM, micro_sha256=PINNED_MICRO,
                 literal_binary_sha256=PINNED_TABLE,
                 native_accepted=None, target_searches=0, native_queries=0, new_RL_training=False)
    artifacts = dict(frame=write_json_gzip(output / 'request-frame-v1.json.gz', frame),
                     input=compress_raw(raw_input, output / 'input.bin.gz'),
                     microcode=compress_raw(raw_code, output / 'microcode.bin.gz'))
    for record in contract['closure']:
        verify(record)
    need(pin(CONTRACT) == contract_pin and pin(sys.argv[2]) == request_pin and
         pin(sys.argv[3]) == receipt_pin, 'closed preparation input/source authority')
    result = dict(schema='guard-native-whole-input-preparation-result-v1',
                  status='complete_whole_serializer_constructor_byte_checks_pending_own_resources_and_native_execution',
                  stage='preparation', stage_completed=True,
                  direct_children_peak_sum_bytes=0,
                  all_direct_children_terminal_and_reaped=True,
                  contract=contract_pin, source=pin(__file__), request=request_pin,
                  translation_receipt=receipt_pin, artifacts=artifacts,
                  raw_input=pin(raw_input), raw_microcode=pin(raw_code),
                  rows=len(request['proof']), ordered_hypothesis_occurrences=3,
                  fixed_field_count=3, free_field_count=2, bands=43,
                  heap_band_cells=HEAP_BAND_CELLS, constructor_nodes=len(nodes),
                  constructor_root=root, all_input_and_microcode_bytes_equal=True,
                  original_nonpayload_bootstrap_unchanged=True,
                  native_accepted=None, independent_native_replay_accepted=None,
                  finite_Wang_rectangle_accepted=None, universal_compiler_theorem=False,
                  target_searches=0, native_queries=0, new_RL_training=False,
                  own_resource_accepted=False,
                  scope='Whole syntax/constructor and byte preparation only. Native semantics '
                        'have not run. Blank heap band capacity is symbol cells, not cons-node '
                        'capacity or a proof of sufficient working space. ROOT owns separate '
                        'complete resource/terminal and once-only native/replay gates.')
    result_path = output / 'preparation-result-v1.json'
    with result_path.open('xb') as stream:
        stream.write(canonical(result) + b'\n')
    print(json.dumps(dict(result=pin(result_path), artifacts=artifacts,
                          native_queries=0, target_searches=0, own_resource_accepted=False)))


if __name__ == '__main__':
    main()
