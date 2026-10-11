"""Freeze decoder-only compact reader repair after V1 parsing memory cutoff."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DONOR = ROOT / '.gcts-active/hilbert-aggregate-independent-audit-20261011/independent_aggregate_full_v2.py'
AUDIT = ROOT / '.gcts-active/hilbert-aggregate-independent-audit-20261011/audit-full-v2.json'
AUDIT_LIFETIME = ROOT / '.gcts-active/hilbert-aggregate-independent-audit-20261011/audit-lifetime-v2.json'


def pin(p):
    data = p.read_bytes()
    return {'path': str(p.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def write(p, s):
    assert not p.exists(), 'immutable reader repair file exists'
    p.write_text(s)


def main():
    old_plan = json.loads((HERE / 'reader-extraction-plan-v1.json').read_text())
    failed = json.loads((HERE / 'reader-extraction-lifetime-v1.json').read_text())
    assert failed['status'] == 'unknown_or_failed' and failed['child_wait_reaped']
    audit = json.loads(AUDIT.read_text())
    # The observer filename is pinned below from the exact auditor directory.
    lifetime = json.loads(AUDIT_LIFETIME.read_text())
    old_source = (HERE / 'hilbert_aggregate_reader_data_v1.py').read_text()
    donor_text = DONOR.read_text()
    pairs = donor_text[donor_text.index('def object_pairs(pairs):'):donor_text.index('\ndef load(path):', donor_text.index('def object_pairs(pairs):'))]
    parser = donor_text[donor_text.index('class StreamingObject:'):donor_text.index('\ndef shared_example(', donor_text.index('class StreamingObject:'))]
    decoder = '''"""Read-only copied JSON decoder; no audit/producer code imported.

The delimiter loops accept a trailing comma. This is not a generic strict JSON
validator; inputs are exact pinned known standard JSON produced by json.dumps.
Only decoding is reused, not scientific checking or authority.
"""
import json


def require(condition, message):
    if not condition:
        raise ValueError(message)


''' + pairs.replace('base.require', 'require') + '\n\n' + parser.replace('base.require', 'require')
    decoder += '''

def expansion_records(path, fields):
    import gzip
    with gzip.open(path, 'rt') as handle:
        for kind, key, value in StreamingObject(handle).entries():
            if kind == 'field':
                fields[key] = value
            elif kind == 'record':
                yield value
            else:
                require(kind == 'record_count' and key == 'records' and value == 171,
                        'unexpected compact reader record census')
'''
    new_source = old_source.replace('import gzip\n', 'import gzip\nimport itertools\nfrom hilbert_aggregate_reader_decoder_v2 import expansion_records\n')
    new_source = new_source.replace('reader-extraction-plan-v1.json', 'reader-extraction-plan-v2.json')
    before = "    expanded = load(paths['expansions'])\n    registry = expanded['formula_codes']"
    after = "    expanded = {}\n    streamed = iter(expansion_records(paths['expansions'], expanded))\n    first = next(streamed)\n    registry = expanded['formula_codes']"
    assert new_source.count(before) == 1
    new_source = new_source.replace(before, after).replace("for source in expanded['records']:", 'for source in itertools.chain([first], streamed):')
    new_source = new_source.replace('read_only_extraction_independent_finite_audit_pending_at_extraction', 'read_only_projection_with_bound_passed_independent_finite_audit')
    new_source = new_source.replace("'extraction_plan_pin': pin(plan_path)", "'independent_audit_pin': pin(paths['independent_audit']), 'extraction_plan_pin': pin(plan_path)")
    new_source = new_source.replace('reader-data-v1.json', 'reader-data-v2.json').replace('reader-extraction-receipt-v1.json', 'reader-extraction-receipt-v2.json')
    new_source = new_source.replace('compact_read_only_extraction_complete_pending_independent_audit', 'compact_read_only_extraction_complete_independent_audit_bound')
    old_runner = (HERE / 'hilbert_aggregate_reader_run_v1.py').read_text()
    runner = old_runner
    for old, new in [('reader-extraction-lifetime-v1.json', 'reader-extraction-lifetime-v2.json'),
                     ('reader-extraction-plan-v1.json', 'reader-extraction-plan-v2.json'),
                     ('hilbert_aggregate_reader_data_v1.py', 'hilbert_aggregate_reader_data_v2.py'),
                     ('reader-stdout-v1.txt', 'reader-stdout-v2.txt'), ('reader-stderr-v1.txt', 'reader-stderr-v2.txt'),
                     ('reader-extraction-receipt-v1.json', 'reader-extraction-receipt-v2.json')]:
        runner = runner.replace(old, new)
    prior = failed['full_seconds_including_child_receipt_serialization']
    remaining = 180 - prior
    runner = runner.replace('elapsed > 180', 'elapsed > ' + repr(remaining))
    runner = runner.replace("'wall_ceiling_seconds': 180", f"'wall_ceiling_seconds': {remaining!r}, 'prior_failed_preparation_seconds': {prior!r}, 'cumulative_reader_preparation_seconds': elapsed + {prior!r}")
    diff = []
    for name, before, after in [('hilbert_aggregate_reader_data', old_source, new_source),
                                ('hilbert_aggregate_reader_run', old_runner, runner)]:
        ast.parse(after)
        write(HERE / (name + '_v2.py'), after)
        diff.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=name + '_v1.py', tofile=name + '_v2.py'))
    ast.parse(decoder)
    write(HERE / 'hilbert_aggregate_reader_decoder_v2.py', decoder)
    write(HERE / 'reader-repair-diff-v2.txt', ''.join(diff))
    inputs = old_plan['inputs'] + [{'role': 'independent_audit', **pin(AUDIT)},
                                 {'role': 'independent_audit_lifetime', **pin(AUDIT_LIFETIME)},
                                 {'role': 'decoder_source', **pin(DONOR)}]
    names = ['hilbert_aggregate_reader_data_v2.py', 'hilbert_aggregate_reader_run_v2.py',
             'hilbert_aggregate_reader_decoder_v2.py', 'hilbert_aggregate_reader_freeze_v2.py']
    plan = {'version': 'hilbert-aggregate-reader-streaming-repair-v2', 'status': 'frozen_before_one_read_only_repair',
            'inputs': inputs, 'sources': [pin(HERE / n) for n in names],
            'prior_plan_pin': pin(HERE / 'reader-extraction-plan-v1.json'),
            'prior_failure_pin': pin(HERE / 'reader-extraction-lifetime-v1.json'), 'source_diff_pin': pin(HERE / 'reader-repair-diff-v2.txt'),
            'scope': 'Same requested formula/member/row/port/point/digest projection. Parse one source record at a time; scientific data unchanged. Metadata binds separately passed finite audit; extraction itself grants no logical authority.',
            'parser_provenance': {'source_pin': pin(DONOR), 'class': 'StreamingObject', 'max_buffer_characters': 16777216,
                                  'copied_scope': 'duplicate-key helper and decoder class only, with require rebound locally; no scientific auditor code imported',
                                  'caveat': 'delimiter loops accept trailing comma; only exact pinned known-standard-JSON scientific inputs are accepted'},
            'failed_v1_unknown': {'seconds': prior, 'terminal_exit_code': failed['terminal_exit_code'], 'host_kernel_peak_sum_bytes': failed['host_kernel_peak_sum_bytes']},
            'remaining_seconds': remaining, 'cumulative_reader_preparation_ceiling_seconds': 180,
            'host_ceiling_bytes': 512 * 1024 * 1024,
            'native_queries': 0, 'target_searches': 0, 'scientific_data_changed': False,
            'engine_or_authority_activation': False, 'HTML_publication': False}
    write(HERE / 'reader-extraction-plan-v2.json', json.dumps(plan, indent=2) + '\n')
    print(json.dumps({'plan_pin': pin(HERE / 'reader-extraction-plan-v2.json'), 'remaining_seconds': remaining,
                      'execution_started': False, 'sources': plan['sources']}))


if __name__ == '__main__':
    main()
