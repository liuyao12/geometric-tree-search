"""Render the frozen relay-curriculum comparison for the research notebook."""

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import shutil


def cells(values):
    return ''.join(f'<td>{escape(str(value))}</td>' for value in values)


def table(headers, rows):
    columns = ''.join(f'<th scope="col">{escape(str(label))}</th>' for label in headers)
    body = ''.join(f'<tr><th scope="row">{escape(str(name))}</th>{cells(values)}</tr>'
                   for name, values in rows)
    return f'<div class="scroll"><table><thead><tr>{columns}</tr></thead><tbody>{body}</tbody></table></div>'


def render(results, output):
    summary = json.loads((results/'summary.json').read_text())
    verification = json.loads((results/'verification.json').read_text())
    output.mkdir(parents=True, exist_ok=True)
    for name in ('summary.json', 'policies.json', 'verification.json', 'example.json'):
        source = results/name
        if source.is_file():
            shutil.copyfile(source, output/name)
        else:
            (output/name).unlink(missing_ok=True)
    cover = summary['evaluation']['test']
    inputs = json.loads((results/'traces.json').read_text())['caseInputs']
    family_sizes = Counter(c['family'] for c in inputs
                           if c['split'] == 'test' and c['expected'] == 'provable')
    staged, shuffled = summary['selectedRL'], summary['selectedShuffled']
    labels = {
        'size': 'Size-first', 'goal': 'Fixed goal-directed',
        staged: 'Easy-to-hard RL', shuffled: 'Shuffled RL',
    }
    times = [f'{round(t*1000)} ms' for t in summary['timeMarks']]
    count = cover['positives']
    totals = table(('Scheduler', *times, 'Total seconds'), (
        (title, (*(f'{n} of {count}' for n in cover['summary'][lane]['proofs']),
                 f'{cover["summary"][lane]["seconds"]:.3f}'))
        for lane, title in labels.items()))
    per_family = table(('Held-out family', *labels.values()), (
        (name, [f'{lanes_by_family[lane]["proofs"][-1]} of {family_sizes[name]}'
                for lane in labels])
        for name, lanes_by_family in cover['byFamily'].items()))
    levels = []
    first = next(iter(summary['schedules'].values()))
    for idx, row in enumerate(first):
        values = [row['depth'], row['max_decoys']]
        for mode in ('staged', 'shuffled'):
            selected = [tiers[idx] for lane, tiers in summary['schedules'].items()
                        if lane.startswith(mode+'-')]
            values.append(f'{sum(x["checked"] for x in selected)} of {sum(x["episodes"] for x in selected)}')
        levels.append((f'Tier {row["level"]}', values))
    training = table(('Tier', 'Relay depth', 'Max. decoys per node', 'Easy-to-hard', 'Shuffled'), levels)
    proof = ('<p><a href="example.json">Example clauses and checked proof certificate</a>.</p>'
             if (output/'example.json').is_file() else '')
    pair = cover['paired']
    saw = cover['summary'][staged]['proofs'][-1]
    fixed = cover['summary']['size']['proofs'][-1]
    control = cover['summary'][shuffled]['proofs'][-1]
    replayed = verification['counts']['checked serialized proofs']
    models = verification['counts']['checked finite models']
    doc = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Relay curriculum and proof-search transfer · GCTS research</title>
<link rel="stylesheet" href="../report.css?v=20261009-r33.1">
<style>
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;white-space:nowrap}}
td,th{{text-align:right;padding:.5rem .7rem;border-bottom:1px solid #cbd5dc}}th:first-child{{text-align:left}}
</style></head>
<body><header class="masthead"><a href="../fol-proof-discovery/index.html">First-order proof discovery</a><a href="#test">Results</a></header>
<main><section class="intro">
<h1>Does easier-to-harder relay training transfer?</h1>
<p>At {times[-1]}, the frozen curriculum policy proved {saw} of {count} new conjectures.
Size-first proved {fixed}, and the frozen shuffled-training control proved {control}.</p>
</section>
<section class="panel" id="test"><h2>New proof families</h2>{totals}
<p>Every deadline includes clause ordering, exact lifted search and independent proof replay.
A result counts if a majority of {summary['repeats']} interleaved repetitions finish by the deadline.
All runs share the {summary['evalSteps']}-activation cap and the same proof rules.</p>
{per_family}
<p>Against size-first at the largest deadline, the easy-to-hard scheduler alone solved
{len(pair['learnedOnly'])} cases and size-first alone solved {len(pair['fixedOnly'])} cases.
They both solved {pair['both']} cases. On those shared successes, the sum of median
proof times was {1_000*pair['commonSeconds'][staged]:.1f} ms for easy-to-hard RL and
{1_000*pair['commonSeconds']['size']:.1f} ms for size-first.</p>
</section>
<section class="panel"><h2>Training order control</h2>{training}
<p>The table pools training episodes across three seeds per schedule. Both schedules used the same
{summary['counts']['train']} relay cases, two visits per case and the same per-episode exploration seeds.
The staged schedule finishes each tier before starting the next. The shuffled schedule mixes all six tiers.
A distinct {summary['counts']['calibration']}-case witness-join family selected one seed from each schedule
before the three held-out families were generated. The selected policies were {escape(staged)} and
{escape(shuffled)}. Calibrated proof coverage is recorded in the study data.</p>
</section>
<section class="panel"><h2>Evidence</h2>
<p>The saved-data audit replayed {replayed} serialized proof certificates and checked {models} explicit
finite countermodels for the negative controls. All search and scoring uses symbolic and numeric code.</p>
{proof}
<p><a href="summary.json">Case counts and timings</a> · <a href="policies.json">Frozen policies</a>
· <a href="verification.json">Replay audit</a> ·
<a href="https://github.com/liuyao12/geometric-tree-search/tree/main/research/fol-proof-discovery">Source and reproduction</a></p>
</section></main></body></html>
"""
    (output/'index.html').write_text(doc)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    render(args.results, args.output)
