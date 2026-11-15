"""Render the proof search experiment for the existing research notebook."""

import argparse
from html import escape
import json
from pathlib import Path
import shutil


def render(results, output):
    doc = json.loads((results/'summary.json').read_text())
    output.mkdir(parents=True, exist_ok=True)
    for name in ('summary.json', 'policies.json', 'example.json', 'verification.json'):
        path = results/name
        if path.is_file():
            shutil.copyfile(path, output/name)
        elif name in ('example.json', 'verification.json'):
            (output/name).unlink(missing_ok=True)
    fixed, learned = doc['selectedFixed'], doc['selectedRL']
    labels = [round(t*1000) for t in doc['timeMarks']]
    thresholds = ''.join(f'<th>{t} ms</th>' for t in labels)
    datasets, reports = [], []
    for split, sheet in doc['evaluation'].items():
        n = sheet['positives']
        rows = []
        pair = sheet['paired']
        for name, metrics in sheet['summary'].items():
            caps = ''.join(f'<td>{count} of {n}</td>' for count in metrics['proofs'])
            rows.append(f'<tr><th scope="row">{escape(name)}</th>{caps}'
                        f'<td>{metrics["seconds"]:.3f}</td><td>{metrics["work"]:,.0f}</td></tr>')
        title = 'Generated held-out families' if split == 'test' else 'External TPTP problems'
        families = ', '.join(doc['splitFamilies'][split])
        datasets.append(f'<section class="panel"><h2>{title}</h2><p>{doc["counts"][split]} cases. '
                        f'{escape(families)}.</p><div class="scroll"><table><thead><tr><th>Scheduler</th>'
                        f'{thresholds}<th>Total seconds</th><th>Counted work</th></tr></thead>'
                        f'<tbody>{"".join(rows)}</tbody></table></div>'
                        f'<p>At the largest time budget, both selected schedules proved {pair["both"]}; '
                        f'{len(pair["learnedOnly"])} were proved only by the learned schedule and '
                        f'{len(pair["fixedOnly"])} only by the selected fixed schedule.</p></section>')
        reports.append(f'{sheet["summary"][learned]["proofs"][-1]} versus '
                       f'{sheet["summary"][fixed]["proofs"][-1]} of {n} '
                       f'on the {"generated" if split == "test" else "external"} set')
    example = ''
    if (output/'example.json').is_file():
        sample = json.loads((output/'example.json').read_text())
        preview = json.dumps(sample['proof'], indent=2)
        example = ('<section class="panel"><h2>Checked proof certificate</h2>'
                   f'<p>{escape(sample["id"])} · {escape(sample["family"])}. '
                   '<a href="example.json">Download the input clauses and certificate</a>.</p>'
                   f'<details><summary>Read the machine certificate</summary><pre>{escape(preview)}</pre>'
                   '</details></section>')
    verification = ''
    audit_path = output/'verification.json'
    if audit_path.is_file():
        audit = json.loads(audit_path.read_text())
        counts = audit['counts']
        train = audit['trainingByFamily']
        relay = sum(r['guarded-relay']['verified'] for r in train.values())
        n = sum(r['guarded-relay']['episodes'] for r in train.values())
        verification = (f'<p>The saved-data audit replayed {counts["checked serialized proofs"]} proofs and checked '
                        f'{counts["checked finite models"]} finite countermodels. It found '
                        f'{relay} checked proof among the {n} guarded-relay training episodes. '
                        '<a href="verification.json">Verification and training by family</a>.</p>')
    contents = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>First-order proof discovery · GCTS + RL</title>
<link rel="stylesheet" href="../report.css?v=20261009-r33.1">
<style>
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;white-space:nowrap}}
td,th{{padding:.5rem .65rem;border-bottom:1px solid #cbd5dc;text-align:right}}
th:first-child{{text-align:left}}pre{{overflow:auto;max-height:30rem;background:#edf2f4;padding:1rem}}
</style>
</head><body><header class="masthead"><a href="../index.html">GCTS research notebook</a><a href="#method">Method</a></header>
<main><section class="intro">
<h1>Can a numeric policy speed up first-order proof discovery?</h1>
<p>The selected learned scheduler and the selected fixed scheduler found {' and '.join(reports)} within {labels[-1]} ms per problem. The selected schedules were {escape(learned)} and {escape(fixed)}.</p>
<p>GCTS searches directly over symbolic clauses. The runtime uses exact lifted inference, a numeric policy and an independent certificate checker.</p>
</section>
{''.join(datasets)}{example}
<section class="panel" id="method"><h2>Method and controls</h2>
<p>The calculus uses lifted resolution and factoring on equality-free clauses. A signed predicate/arity index offers complementary literals, and exact unification determines which pairs can resolve. A clause can be promoted by a score on a bounded shortlist. Regular FIFO slots keep the rest of the queue moving. The checker replays the recorded parent indices, substitutions and clauses through the empty clause.</p>
<p>The policy started from zero weights on {doc['counts']['train']} training cases. A separate {doc['counts']['calibration']}-case split chose the fixed control and learned seed before evaluation. Input families in the synthetic splits are distinct. The study used {doc['repeats']} interleaved repetitions and a cap of {doc['evalSteps']} clause activations in each evaluation run. A case counts at a deadline when a majority of repetitions return a verified proof within it.</p>
<p>Time includes search, scoring and verification from parsed clauses. The total sums per-case medians, including unsuccessful runs. Counted work sums clause activations, candidate pairs inspected and unification equations processed. The time and work include bounded misses. A bounded miss leaves the conjecture open.</p>
{verification}
<p>The six external clause sets come from the TPTP v10.0.0 Problem Library. <a href="https://tptp.tptp.org/">TPTP Problem Library</a>.</p>
<p><a href="summary.json">Metrics and protocol</a> · <a href="policies.json">Frozen policies</a> · <a href="https://github.com/liuyao12/geometric-tree-search/tree/main/research/fol-proof-discovery">Source and reproduction instructions</a></p>
</section></main></body></html>
"""
    (output/'index.html').write_text(contents)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('results', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    render(args.results, args.output)
