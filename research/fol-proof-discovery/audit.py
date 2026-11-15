"""Replay the serialized proof and countermodel evidence from a saved study."""

import argparse
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path

import benchmark
from checker import InvalidProof, verify
from run import fingerprint


def audit(directory):
    traces = json.loads((directory/'traces.json').read_text())
    summary = json.loads((directory/'summary.json').read_text())
    policies = json.loads((directory/'policies.json').read_text())
    cases = {c['id']: c for c in benchmark.cases()}
    if (fingerprint(list(cases.values())) != summary['caseDigest']
            or fingerprint(traces['caseInputs']) != summary['caseDigest']
            or fingerprint(policies) != summary['policyDigest']):
        raise ValueError('saved inputs or frozen policy digest changed')
    counts = Counter()
    for case in cases.values():
        if case['expected'] == 'satisfiable':
            if not benchmark.verify_countermodel(case['clauses'], case['model']):
                raise ValueError(f'{case["id"]}: countermodel rejected')
            counts['checked finite models'] += 1
    cohorts = (traces['calibration'], *(v['rows'] for v in traces['evaluation'].values()))
    for cohort in cohorts:
        for row in cohort:
            case = cases[row['id']]
            for samples in row['runs'].values():
                for result in samples:
                    if (result['proof'] is not None) != (result['status'] == 'proved'):
                        raise ValueError(f'{case["id"]}: mismatched proof status')
                    if result['proof'] is not None:
                        if case['expected'] != 'provable' or not verify(case['clauses'], result['proof']):
                            raise ValueError(f'{case["id"]}: invalid proof verdict')
                        counts['checked serialized proofs'] += 1
                    if (result['counters'].get('selector_errors', 0)
                            or result['counters'].get('age_slots', 0) != result['steps']//4):
                        raise ValueError(f'{case["id"]}: scheduler audit failed')
                    counts['audited search runs'] += 1
    example_path = directory/'example.json'
    example_id = None
    if example_path.is_file():
        example = json.loads(example_path.read_text())
        example_id = example['id']
        if fingerprint(example['clauses']) != fingerprint(cases[example_id]['clauses']):
            raise ValueError('example input changed')
        if not verify(example['clauses'], example['proof']):
            raise ValueError('example proof rejected')
        mutated = deepcopy(example['proof'])
        mutated['root'] = len(mutated['steps'])
        try:
            verify(example['clauses'], mutated)
        except InvalidProof:
            counts['corrupted example rejected'] += 1
        else:
            raise ValueError('inconsistent certificate root accepted')
    training = {}
    for mode, archive in traces['training'].items():
        by_family = {}
        for episode in archive['episodes']:
            family = cases[episode['id']]['family']
            counts['training runs checked during run'] += episode['checked']
            item = by_family.setdefault(family, dict(episodes=0, verified=0))
            item['episodes'] += 1
            item['verified'] += episode['checked']
        training[mode] = by_family
    result = dict(counts=counts, trainingByFamily=training, example=example_id)
    serialized = json.dumps(result, indent=2)
    (directory/'verification.json').write_text(serialized+'\n')
    print(serialized)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    audit(parser.parse_args().directory)
