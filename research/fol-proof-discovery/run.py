"""Train and compare clause schedulers under a common exact proof kernel."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from random import Random
from statistics import median
from time import perf_counter

import benchmark
from checker import verify
from kernel import search
from policy import NumericPolicy, checked_reward, fixed_selector


FIXED = ('fifo', 'size', 'goal', 'random')
SEEDS = (41, 229, 613)
TIME_MARKS = (0.015, 0.050, 0.120)
TRAIN_STEPS = 90
TRAIN_SECONDS = 0.075
EVAL_STEPS = 180


def fingerprint(value):
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def one(case, selector, steps, seconds):
    """Measure request through verified proof, including selector evaluation."""
    started = perf_counter()
    result = search(case['clauses'], select=selector, max_steps=steps, seconds=seconds)
    status = result['status']
    if status == 'proved':
        if verify(case['clauses'], result['proof']) is not True:
            raise ValueError(f'{case["id"]}: rejected proof')
        if case['expected'] != 'provable':
            raise ValueError(f'{case["id"]}: proof conflicts with a countermodel')
    elapsed = perf_counter() - started
    return dict(status=status, steps=result['steps'], counters=result['counters'],
                seconds=elapsed, limit=result.get('limit'), proof=result.get('proof'))


def work(record):
    counts = record['counters']
    return record['steps'] + counts.get('offers', 0) + counts.get('solved_equations', 0)


def curriculum(cases, epochs):
    logs, policies = {}, {}
    for seed in SEEDS:
        started = perf_counter()
        model = NumericPolicy(seed=seed)
        rng = Random(seed)
        episodes = []
        schedule = list(cases)
        for epoch in range(1, epochs + 1):
            rng.shuffle(schedule)
            for case in schedule:
                controller = model.selector(train=True, seed=rng.randrange(2**32))
                result = one(case, controller, TRAIN_STEPS, TRAIN_SECONDS)
                verdict = result['status'] == 'proved'
                reward = checked_reward(verdict, work(result))
                model.update(controller, reward)
                episodes.append(dict(id=case['id'], epoch=epoch, checked=verdict,
                                     work=work(result), reward=reward, seconds=result['seconds']))
        label = f'rl-{seed}'
        logs[label] = dict(episodes=episodes, seconds=perf_counter()-started)
        policies[label] = model.snapshot()
        print(f'{label} trained on {len(episodes)} episodes', flush=True)
    return policies, logs


def make_selector(lane, seed, policies):
    if lane == 'fifo':
        return None
    if lane in FIXED:
        return fixed_selector(lane, seed=seed)
    return NumericPolicy.from_snapshot(policies[lane]).selector(train=False, seed=seed)


def compare(cases, lanes, policies, repeats, time_marks):
    out = []
    for index, case in enumerate(cases):
        records = defaultdict(list)
        shuffle = Random(7221 + index)
        for repeat in range(repeats):
            order = list(lanes)
            shuffle.shuffle(order)
            for lane in order:
                # A seeded random controller is evaluated over multiple orders.
                selector = make_selector(lane, 4209 + index*37 + repeat, policies)
                result = one(case, selector, EVAL_STEPS, time_marks[-1])
                records[lane].append(result)
        out.append(dict(id=case['id'], family=case['family'], split=case['split'],
                        expected=case['expected'], runs=dict(records)))
    return out


def median_case(samples, cap):
    count = sum(r['status'] == 'proved' and r['seconds'] <= cap for r in samples)
    return count > len(samples)//2


def metrics(rows, lanes, time_marks):
    totals = {}
    positives = [r for r in rows if r['expected'] == 'provable']
    for lane in lanes:
        summaries = list(zip(*(r['runs'][lane] for r in rows)))
        totals[lane] = dict(
            proofs=[sum(median_case(r['runs'][lane], cap) for r in positives) for cap in time_marks],
            countsByRepeat=[dict(Counter(v['status'] for v in repeat)) for repeat in summaries],
            seconds=sum(median(x['seconds'] for x in r['runs'][lane]) for r in rows),
            work=sum(median(work(x) for x in r['runs'][lane]) for r in rows),
            proofWork=sum(median(work(x) for x in r['runs'][lane] if x['status']=='proved')
                          for r in positives if any(x['status']=='proved' for x in r['runs'][lane])),
        )
    return totals


def choose(rows, lanes):
    """Calibrate by checked coverage, then bounded work. Keep test data sealed."""
    def rank(lane):
        proved = [r for row in rows if row['expected'] == 'provable'
                  for r in row['runs'][lane]
                  if r['status'] == 'proved' and r['seconds'] <= TIME_MARKS[-1]]
        return (len(proved), sum(work(r) <= 150 for r in proved),
                -sum(work(r) for row in rows for r in row['runs'][lane]))
    return max(lanes, key=rank)


def proof_example(rows, problems, learned):
    by_id = {r['id']: r for r in problems}
    for row in rows:
        learned_proof = next((x['proof'] for x in row['runs'][learned] if x['proof'] is not None), None)
        if learned_proof is not None:
            return dict(id=row['id'], family=row['family'], clauses=by_id[row['id']]['clauses'],
                        proof=learned_proof)
    return None


def paired_summary(rows, fixed, learned, cap):
    fixed_only, learned_only, common = [], [], []
    for row in rows:
        a = median_case(row['runs'][fixed], cap)
        b = median_case(row['runs'][learned], cap)
        if a and b:
            common.append(row)
        elif a:
            fixed_only.append(row['id'])
        elif b:
            learned_only.append(row['id'])
    return dict(fixedOnly=fixed_only, learnedOnly=learned_only, both=len(common),
                commonSeconds={lane:sum(median(x['seconds'] for x in row['runs'][lane])
                                         for row in common) for lane in (fixed, learned)})


def run(output, epochs, repeats):
    output.mkdir(parents=True, exist_ok=True)
    loaded = list(benchmark.cases())
    for case in loaded:
        if case['expected'] == 'satisfiable':
            if not benchmark.verify_countermodel(case['clauses'], case['model']):
                raise ValueError(f'{case["id"]}: rejected countermodel')
    ids = [case['id'] for case in loaded]
    assert len(ids) == len(set(ids))
    grouped = {split: [c for c in loaded if c['split'] == split]
               for split in ('train','calibration','test','external')}
    assert all(grouped[s] for s in ('train', 'calibration', 'test'))
    synthetic = ('train','calibration','test')
    for i, split in enumerate(synthetic):
        families = {c['family'] for c in grouped[split]}
        for other in synthetic[i+1:]:
            assert families.isdisjoint(c['family'] for c in grouped[other]), (split, other)
    policies, training = curriculum(grouped['train'], epochs)
    calibration = compare(grouped['calibration'], (*FIXED, *policies), policies, 1, TIME_MARKS)
    best_fixed = choose(calibration, FIXED)
    best_rl = choose(calibration, tuple(policies))
    frozen = dict(selectedFixed=best_fixed, selectedRL=best_rl, policies=policies)
    policy_digest = fingerprint(frozen)
    (output/'policies.json').write_text(json.dumps(frozen, indent=2)+'\n')
    print(f'Calibration selected {best_fixed} and {best_rl}; policies frozen', flush=True)
    lanes = (*FIXED, best_rl)
    evaluation = {}
    for split in ('test','external'):
        if grouped[split]:
            rows = compare(grouped[split], lanes, policies, repeats, TIME_MARKS)
            evaluation[split] = dict(rows=rows, summary=metrics(rows, lanes, TIME_MARKS),
                                     paired=paired_summary(rows, best_fixed, best_rl, TIME_MARKS[-1]),
                                     positives=sum(r['expected']=='provable' for r in rows))
            print(f'{split}: {len(rows)} cases', flush=True)
    assert fingerprint(frozen)==policy_digest
    summary = dict(schema='gcts-fol-proof-discovery-v1', counts={k:len(v) for k,v in grouped.items()},
                   splitFamilies={k:sorted({c['family'] for c in v}) for k,v in grouped.items()},
                   caseDigest=fingerprint(loaded), policyDigest=policy_digest,
                   selectedFixed=best_fixed, selectedRL=best_rl, repeats=repeats, epochs=epochs,
                   evalSteps=EVAL_STEPS, timeMarks=TIME_MARKS,
                   trainingSeconds={k:v['seconds'] for k,v in training.items()},
                   evaluation={s:{k:v for k,v in item.items() if k != 'rows'} for s,item in evaluation.items()})
    example = proof_example(evaluation['test']['rows'], grouped['test'], best_rl)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'traces.json').write_text(json.dumps(dict(caseInputs=loaded, calibration=calibration,
         training=training, evaluation=evaluation), separators=(',', ':'))+'\n')
    if example is not None:
        (output/'example.json').write_text(json.dumps(example, indent=2)+'\n')
    else:
        (output/'example.json').unlink(missing_ok=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--epochs', type=int, default=4)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.epochs < 1 or args.repeats < 1 or args.repeats % 2 == 0:
        parser.error('use at least one epoch and an odd positive number of repetitions')
    run(args.output, args.epochs, args.repeats)
