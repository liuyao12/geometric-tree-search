"""Compare easy-to-hard relay training with a matched shuffled control."""

import argparse
from collections import Counter
import json
from pathlib import Path
from random import Random
from time import perf_counter

from audit import audit
from curriculum_cases import LEVELS, calibration_cases, cases, heldout_cases, training_cases
from policy import NumericPolicy, checked_reward
from run import (EVAL_STEPS, TIME_MARKS, TRAIN_SECONDS, TRAIN_STEPS, compare, fingerprint,
                 median_case, metrics, one, paired_summary, proof_example, work)


TRAIN_SEEDS = (5101, 6127, 7343)
PASSES = 2
CALIBRATION_REPEATS = 3


def train(problems):
    snapshots, logs = {}, {}
    for seed in TRAIN_SEEDS:
        random = Random(seed)
        events = [(case, repeat, random.randrange(2**32)) for case in problems
                  for repeat in range(PASSES)]
        random.shuffle(events)
        ordered = sorted(events, key=lambda event: event[0]['level'])
        for label, schedule in (('staged', ordered), ('shuffled', events)):
            started = perf_counter()
            model = NumericPolicy(seed=seed)
            episodes = []
            for case, repeat, episode_seed in schedule:
                selector = model.selector(train=True, seed=episode_seed)
                result = one(case, selector, TRAIN_STEPS, TRAIN_SECONDS)
                proved = result['status'] == 'proved'
                reward = checked_reward(proved, work(result))
                model.update(selector, reward)
                episodes.append(dict(id=case['id'], level=case['level'], repeat=repeat,
                                     seed=episode_seed, checked=proved, reward=reward,
                                     seconds=result['seconds'], work=work(result)))
            name = f'{label}-{seed}'
            logs[name] = dict(episodes=episodes, seconds=perf_counter()-started)
            snapshots[name] = model.snapshot()
            print(name, sum(e['checked'] for e in episodes), 'checked proofs in',
                  len(episodes), 'training episodes', flush=True)
        # Match cases, visit counts, exploration seeds and initial weights.
        keys = Counter((c['id'], r, s) for c, r, s in events)
        for name in (f'staged-{seed}', f'shuffled-{seed}'):
            assert keys == Counter((e['id'], e['repeat'], e['seed']) for e in logs[name]['episodes'])
    return snapshots, logs


def select(rows, lanes):
    def rank(lane):
        coverage = tuple(sum(median_case(r['runs'][lane], cap) for r in rows)
                         for cap in (TIME_MARKS[-1], *TIME_MARKS[:-1]))
        spent = sum(work(result) for row in rows for result in row['runs'][lane])
        return (*coverage, -spent)
    return max(lanes, key=rank)


def family_metrics(rows, names):
    families = sorted({case['family'] for case in rows})
    return {
        family: metrics([case for case in rows if case['family'] == family], names, TIME_MARKS)
        for family in families
    }


def levels_summary(training):
    result = {}
    for lane, run in training.items():
        stats = []
        for index, (depth, width) in enumerate(LEVELS, 1):
            subset = [e for e in run['episodes'] if e['level'] == index]
            stats.append(dict(level=index, depth=depth, max_decoys=width, episodes=len(subset),
                              checked=sum(e['checked'] for e in subset)))
        result[lane] = stats
    return result


def run(output, repeats):
    output.mkdir(parents=True, exist_ok=True)
    training_set, calibration_set = list(training_cases()), list(calibration_cases())
    snapshots, training = train(training_set)
    calibration_names = ('size', 'goal', *snapshots)
    calibration = compare(calibration_set, calibration_names, snapshots,
                          CALIBRATION_REPEATS, TIME_MARKS)
    staged = select(calibration, [lane for lane in snapshots if lane.startswith('staged-')])
    shuffled = select(calibration, [lane for lane in snapshots if lane.startswith('shuffled-')])
    frozen = dict(selectedFixed='size', selectedRL=staged, selectedShuffled=shuffled, policies=snapshots)
    frozen_sha = fingerprint(frozen)
    (output/'policies.json').write_text(json.dumps(frozen, indent=2)+'\n')
    print(f'Frozen {staged} and {shuffled} on calibration; opening held-out families', flush=True)

    test = list(heldout_cases())
    families = [{case['family'] for case in split} for split in (training_set, calibration_set, test)]
    assert all(not a & b for i, a in enumerate(families) for b in families[i+1:])
    names = ('size', 'goal', staged, shuffled)
    evaluated = compare(test, names, snapshots, repeats, TIME_MARKS)
    assert fingerprint(json.loads((output/'policies.json').read_text())) == frozen_sha
    assert fingerprint(frozen) == frozen_sha
    inputs = [*training_set, *calibration_set, *test]
    assert len({case['id'] for case in inputs}) == len(inputs)
    sheet = dict(summary=metrics(evaluated, names, TIME_MARKS),
                 byFamily=family_metrics(evaluated, names),
                 paired=paired_summary(evaluated, 'size', staged, TIME_MARKS[-1]),
                 versusShuffled=paired_summary(evaluated, shuffled, staged, TIME_MARKS[-1]),
                 positives=sum(case['expected']=='provable' for case in test))
    summary = dict(schema='relay-curriculum-v1', caseDigest=fingerprint(inputs), policyDigest=frozen_sha,
                   selectedFixed='size', selectedRL=staged, selectedShuffled=shuffled,
                   counts=dict(train=len(training_set), calibration=len(calibration_set), test=len(test)),
                   schedules=levels_summary(training),
                   trainingSeconds={lane:r['seconds'] for lane,r in training.items()},
                   calibration=metrics(calibration, calibration_names, TIME_MARKS),
                   timeMarks=TIME_MARKS, evalSteps=EVAL_STEPS, trainSteps=TRAIN_STEPS,
                   trainSeconds=TRAIN_SECONDS, repeats=repeats, evaluation={'test':sheet})
    example = proof_example(evaluated, test, staged)
    if example is None:
        (output/'example.json').unlink(missing_ok=True)
    else:
        (output/'example.json').write_text(json.dumps(example, indent=2)+'\n')
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'traces.json').write_text(json.dumps(dict(caseInputs=inputs, calibration=calibration,
        training=training, evaluation={'test':dict(sheet, rows=evaluated)}),
        separators=(',', ':'))+'\n')
    audit(output, case_source=cases)
    for lane, result in sheet['summary'].items():
        print(lane, result['proofs'], round(result['seconds'], 3), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1 or args.repeats % 2 == 0:
        parser.error('use an odd positive number of repetitions')
    run(args.output, args.repeats)
