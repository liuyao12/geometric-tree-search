"""Build the Pages study and a diagram of two held-out cavity completions."""

import argparse
import json
from html import escape
from math import sqrt
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from geometry import transform
from model import SHAPES


LABELS = {
    'gcts': 'Plain GCTS',
    'primitive_rl': 'Single tiles + RL',
    'pairs_rl': 'Pairs + RL',
    'hierarchy_random': 'Hierarchy, random order',
    'hierarchy_largest': 'Hierarchy, largest first',
    'hierarchy_rl': 'Hierarchy + RL',
}


def choose(data):
    return max(data['rows'], key=lambda r: (
        max((len(keys) for _, keys in r['lanes']['hierarchy_rl']['choices']), default=0),
        sum(bool(index) for index, _ in r['lanes']['hierarchy_rl']['choices']), r['tileCount']))


def diagram(results, output):
    image = Image.new('RGB', (1560, 970), '#f2f5f5')
    draw = ImageDraw.Draw(image)
    font_path = '/System/Library/Fonts/Supplemental/Arial.ttf'
    font = ImageFont.truetype(font_path, 27) if Path(font_path).exists() else ImageFont.load_default(size=27)
    title = ImageFont.truetype(font_path, 34) if Path(font_path).exists() else ImageFont.load_default(size=34)
    colors = ('#e7bd6c', '#91cbc2', '#bac3e9', '#d9a9a2', '#a8c999', '#b6aacf',
              '#dfb28d', '#9fc9d8', '#dab5d0', '#c5c589', '#abd9bb', '#e7a6ae')
    for row, result in enumerate(results):
        case = choose(result)
        name = result['shape']
        choices = case['lanes']['hierarchy_rl']['choices']
        boundary = case['boundary']

        def polygon(key):
            o, x, y = key
            xy = ((x+a, y+b) for a, b in (transform(o, *p[:2]) for p in SHAPES[name]))
            return tuple((u+v/2, -v*sqrt(3)/2) for u, v in xy)

        points = [p for k in boundary for p in polygon(k)]
        points += [p for _, keys in choices for k in keys for p in polygon(k)]
        xs, ys = zip(*points)
        scale = min(617/(max(xs)-min(xs)), 324/(max(ys)-min(ys)))
        cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
        for col, label in enumerate(('Fixed boundary', 'Frozen RL completion')):
            left, top = 22+col*778, 18+row*480
            draw.rounded_rectangle((left, top, left+738, top+452), radius=16, fill='#ffffff', outline='#c7d3d6', width=2)
            draw.text((left+18, top+16), f'{name.capitalize()} · {label}', fill='#16343e', font=title)

            def place(key, color):
                vertices = [(left+369+(x-cx)*scale, top+236+(y-cy)*scale) for x, y in polygon(key)]
                draw.polygon(vertices, fill=color, outline='#314953', width=2)

            for k in boundary:
                place(k, '#dce5e8')
            if col:
                use = 0
                for index, keys in choices:
                    color = colors[use % len(colors)] if index else '#eef3f1'
                    use += bool(index)
                    for key in keys:
                        place(key, color)
            draw.text((left+18, top+414), f'{case["tileCount"]} interior tiles · case {case["id"]}', fill='#38535d', font=font)
    image.save(output, optimize=True)


def metrics_table(results):
    body = []
    for item in results:
        total = len(item['rows'])
        for key, label in LABELS.items():
            m = item['summary'][key]
            row = (f'<tr><td>{item["shape"].capitalize()}</td><th scope="row">{escape(label)}</th>'
                   f'<td>{m["solved"]}/{total}</td><td>{m["states"]:,}</td>'
                   f'<td>{m["seconds"]*1000/total:.2f}</td><td>{m["endToEnd"]*1000/total:.2f}</td></tr>')
            body.append(row)
    return ('<div class="scroll"><table><thead><tr><th>Tile</th><th>Policy</th><th>Solved</th>'
            '<th>States</th><th>Search ms/cavity</th><th>Total ms/cavity</th></tr></thead><tbody>'
            + ''.join(body) + '</tbody></table></div>')


def build(results, followup, output, dataset_seconds):
    output.mkdir(parents=True, exist_ok=True)
    diagram(results, output/'cavities.png')
    summaries = []
    for item in results:
        summary = {k: v for k, v in item.items() if k not in ('rows', 'training')}
        summary['caseMetrics'] = [
            {k: row[k] for k in ('id','source','tileCount','columns','candidates','compileSeconds')} |
            {'lanes': {lane: {k: r[k] for k in ('solved','seconds','endToEnd','stats')}
                       for lane, r in row['lanes'].items()}} for row in item['rows']]
        sample = choose(item)
        summary['example'] = dict(id=sample['id'], boundary=sample['boundary'],
                                  moves=sample['lanes']['hierarchy_rl']['choices'])
        summary['trainingEpisodes'] = len(item['training'])
        summaries.append(summary)
    guarded = []
    for study in followup:
        guarded.append({k: v for k, v in study.items() if k != 'rows'} |
                       {'cases': [{k: row[k] for k in ('id','source','tiles')} |
                                  {'lanes': {lane: {k: r[k] for k in ('solved','seconds','endToEnd','stats')}
                                             for lane, r in row['lanes'].items()}} for row in study['rows']]})
    (output/'results.json').write_text(json.dumps(dict(datasetWallSeconds=dataset_seconds,
                                                 shapes=summaries, forcedFollowup=guarded),
                                                 separators=(',', ':')))
    total_train = sum(i['trainingCases'] for i in results)
    total_eval = sum(len(i['rows']) for i in results)
    ratios = []
    for item in results:
        base = item['summary']['gcts']
        rl = item['summary']['hierarchy_rl']
        paired = [row for row in item['rows'] if all(row['lanes'][k]['solved'] for k in ('gcts', 'hierarchy_rl'))]
        ratio_solved = (sum(r['lanes']['hierarchy_rl']['seconds'] for r in paired) /
                        sum(r['lanes']['gcts']['seconds'] for r in paired))
        lo, hi = rl['endToEndRatio95']
        ratios.append(
            f'<li><strong>{item["shape"].capitalize()}</strong> · '
            rf'\({rl["seconds"]/base["seconds"]:.2f}\times\) the baseline search time, '
            rf'\({rl["endToEnd"]/base["endToEnd"]:.3f}\times\) the compile-plus-search time '
            rf'(source-bootstrap interval \({lo:.3f}\) to \({hi:.3f}\)). '
            f'{rl["states"]:,} versus {base["states"]:,} visited states. '
            rf'Across the {len(paired)} cavities both solved, search time was \({ratio_solved:.2f}\times\) the baseline.</li>')
    macro_counts = []
    for item in results:
        s = item['summary']['hierarchy_rl']
        macro_counts.append(f'<li><strong>{item["shape"].capitalize()}</strong> · '
                            + ', '.join(f'{s["winningMacros"].get(str(n), 0)} {n}-tile moves'
                                        for n in (2,4,8)) + ' on successful paths.</li>')
    forced_rows = []
    for study in followup:
        n = len(study['rows'])
        for lane, label in (('gcts', 'Plain GCTS'), ('guarded_largest', 'Certified, largest first'), ('guarded_rl', 'Certified + frozen RL')):
            s = study['summary'][lane]
            forced_rows.append(f'<tr><td>{study["shape"].capitalize()}</td><th scope="row">{label}</th>'
                               f'<td>{s["solved"]}/{n}</td><td>{s["states"]:,}</td>'
                               f'<td>{s["seconds"]*1000/n:.2f}</td><td>{s["endToEnd"]*1000/n:.2f}</td></tr>')
    (output/'index.html').write_text(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fixed-boundary hat and turtle experiments · GCTS + RL</title>
<link rel="stylesheet" href="../report.css?v=20261009-r33.1">
<script>window.MathJax={{tex:{{inlineMath:[['\\\\(','\\\\)']]}}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;white-space:nowrap}}
td,th{{padding:.46rem .65rem;border-bottom:1px solid #cbd5dc;text-align:right}}
td:first-child,th:first-child,th:nth-child(2){{text-align:left}}figure{{margin:1.1rem 0}}
figure img{{display:block;width:100%;height:auto}}figcaption{{margin-top:.5rem}}
</style></head><body>
<header class="masthead"><a href="../index.html">GCTS research notebook</a><a href="#results">Results</a></header>
<main><section class="intro">
<h1>Can GCTS + RL fill a fixed boundary faster?</h1>
<p class="deck">An unmarked hat and turtle experiment using {total_train} training cavities and {total_eval} held-out cavities from separate growth runs.</p>
<ul>{''.join(ratios)}</ul>
</section>
<section class="panel" id="results"><h2>Held-out reconstruction</h2>{metrics_table(results)}
<p>Timing uses three interleaved runs per cavity and policy. The table averages the per-cavity medians. Total includes building the exact cavity incidence graph and searching it, including cluster matching. These averages include cases that reached the state cap. Offline training and independent replay are outside the matched timing.</p>
<figure><img src="cavities.png" width="1560" height="970" alt="Two sample fixed-boundary cavities and the corresponding held-out hat and turtle reconstructions.">
<figcaption>Gray tiles are the fixed collar. Each colored group is one cluster move selected by the frozen policy. Pale interior tiles were placed individually.</figcaption></figure>
<ul>{''.join(macro_counts)}</ul></section>
<section class="panel"><h2>Follow-up with forced cluster moves</h2>
<p>The first experiment lets each fitted cluster create a speculative branch. The follow-up commits a cluster only after finding a singleton obligation for each of its tiles in sequence. When certification fails, normal single-tile GCTS continues. The bank and policy are unchanged. This diagnostic uses different cavities from the same held-out growth lineages.</p>
<div class="scroll"><table><thead><tr><th>Tile</th><th>Policy</th><th>Solved</th><th>States</th><th>Search ms/cavity</th><th>Total ms/cavity</th></tr></thead>
<tbody>{''.join(forced_rows)}</tbody></table></div></section>
<section class="panel"><h2>How the boundaries and clusters were made</h2>
<p>Unmarked GCTS grew fresh patches from the polygon outlines using integer translations and twelve lattice symmetries. Each cavity removes a connected interior whose entire edge boundary was already surrounded. The solver gets the empty region. The original completion stays out of the search inputs.</p>
<p>Each target is an exact union of triangular atoms. GCTS checks all open obligations for dead points and singletons, then branches on the smallest domain. Every atom is initially required, so all cavity obligations begin at generation zero. Every primitive branch remains available when cluster moves are added.</p>
<p>The learner starts with zero policy weights. Its candidate clusters come from recurring touching pairs in solved training cavities. Disjoint touching child clusters can form four-tile and eight-tile parents. The episodic reward trades off incidence work and measured solve time, with a penalty for incomplete fills. Evaluation reuses the frozen cluster bank and policy. Cavities equivalent under symmetry or translation are removed before evaluation.</p>
<p>Independent polygon rerasterization checked every returned fill against its cavity and fixed collar. The experiment uses boundaries from previously generated finite patches. It tests cavity reconstruction and finite cluster reuse under the lattice model.</p></section>
<section class="panel"><h2>Reproduce the run</h2>
<p>Patch generation took {dataset_seconds:.1f} seconds. The per-shape training, case timings, and frozen-policy hashes are in the data.</p>
<p><a href="results.json">Case-level results</a> · <a href="hat-policy.json">Frozen hat policy</a> · <a href="turtle-policy.json">Frozen turtle policy</a> · <a href="https://github.com/liuyao12/geometric-tree-search/tree/main/research/hat-turtle-speed-rl">Source and reproduction instructions</a></p>
</section></main></body></html>
""")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('hat', type=Path)
    parser.add_argument('turtle', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--dataset-seconds', type=float, required=True)
    parser.add_argument('--forced', type=Path, nargs=2, required=True)
    args = parser.parse_args()
    build([json.loads(path.read_text()) for path in (args.hat, args.turtle)],
          [json.loads(path.read_text()) for path in args.forced], args.output, args.dataset_seconds)
