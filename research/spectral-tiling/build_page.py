#!/usr/bin/env python3
"""Update data-backed parts of the living HTML notes; never generate a PDF."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
PAGE = ROOT.parents[1]/'docs/projects/spectral-tiling-study.html'


def math(value):
    return r'\('+str(value)+r'\)'


def replace_body(source, identifier, body, tag='tbody'):
    pattern = r'(<'+tag+' id="'+identifier+r'">).*?(</'+tag+'>)'
    source, count = re.subn(pattern, lambda m: m[1]+body+m[2], source, flags=re.S)
    assert count == 1, identifier
    return source


def main():
    data = json.loads((ROOT/'arithmetic-spectra.json').read_text())
    original = json.loads((ROOT/'results.json').read_text())
    source = PAGE.read_text()
    control = data['L_triomino']
    anchors = {a['q']: a for a in control['anchors']}
    gaps = []
    for g in control['gaps']:
        g = dict(g)
        a, b = g['left_q'], g['right_q']
        projections = [anchors[q]['clusters']['4']['minimum_selected_projection'] for q in (a, b)]
        margins = [min(x-a, b-x) for x in g['fine_interior_normalized_estimates']]
        g['endpoint_margin_exceeds_last_refinement_change'] = all(
            margin > change for margin, change in zip(margins, g['last_refinement_absolute_changes']))
        g['status'] = ('refinement-stable estimate' if
                       g['anchor_ranks_stable_on_two_finest_meshes'] and
                       g['all_fine_interior_estimates_strictly_between'] and
                       g['endpoint_margin_exceeds_last_refinement_change'] and min(projections) > .95
                       else 'pending endpoint resolution')
        g['left_constructed_multiplicity'] = anchors[a]['constructed_multiplicity']
        g['right_constructed_multiplicity'] = anchors[b]['constructed_multiplicity']
        gaps.append(g)
    rows = []
    for g in gaps:
        ready = g['status'] == 'refinement-stable estimate'
        count = math(g['counts_by_refinement']['4']) if ready else 'Pending'
        counts = math(r',\;'.join(str(g['counts_by_refinement'][str(level)]) for level in control['levels']))
        rows.append('<tr><td>'+math(f"({g['left_q']},{g['right_q']})")+'</td><td>'+count+'</td><td>'+counts+'</td><td'+
                    ('' if ready else ' class="pending"')+'>'+g['status']+'</td></tr>')
    source = replace_body(source, 'gap-table', ''.join(rows))
    fine, previous = control['meshes']['4'], control['meshes']['3']
    minimum_projection = min(a['clusters']['4']['minimum_selected_projection'] for a in control['anchors'])
    note = ('The finest gap-count mesh has '+math(fine['nodes'])+' nodes and '+math(fine['triangles'])+
            ' triangles. Each mesh supplies '+math(control['modes_per_mesh'])+' modes, including multiplicities. '+
            'The smallest selected analytic-subspace projection score on the finest mesh is '+math(f'{minimum_projection:.4f}')+
            '; a score of '+math(1)+' would mean complete agreement with the interpolated explicit subspace. '+
            'The four counts in each row run from the coarsest to the finest mesh. '+
            '<a href="../../research/spectral-tiling/arithmetic-spectra.json">All estimates, ranks, projection scores and refinement movements</a> are retained.')
    source = replace_body(source, 'gap-validation', note, 'p')
    hat = min(original['cases'], key=lambda c: abs(c['r']-3**.5))
    equilateral = min(original['cases'], key=lambda c: abs(c['r']-1))
    turtle = data['Turtle_low_modes']
    atlas = []
    for name, values, prior in [
        ('L-triomino', [3*x for x in fine['eigenvalues']], [3*x for x in previous['eigenvalues']]),
        ('Hat', hat['meshes']['3']['area_eigenvalues'], hat['meshes']['2']['area_eigenvalues']),
        ('Turtle', turtle['meshes']['3']['area_eigenvalues'], turtle['meshes']['2']['area_eigenvalues']),
        ('Equilateral polygon', equilateral['meshes']['3']['area_eigenvalues'], equilateral['meshes']['2']['area_eigenvalues'])]:
        change = max(abs(a/b-1) for a, b in zip(prior[:12], values[:12]))*100
        atlas.append('<tr><td>'+name+'</td><td>'+math(r',\;'.join(f'{v:.5f}' for v in values[:4]))+
                     '</td><td>'+math(f'{change:.3f}'+r'\%')+'</td></tr>')
    source = replace_body(source, 'atlas-table', ''.join(atlas))
    payload = {'normalization': 'lambda/pi^2', 'gaps': gaps}
    encoded = json.dumps(payload, separators=(',', ':')).replace('<', r'\u003c')
    source = replace_body(source, 'gap-data', encoded, 'script') if '<script id="gap-data">' in source else re.sub(
        r'(<script id="gap-data" type="application/json">).*?(</script>)', lambda m: m[1]+encoded+m[2], source, flags=re.S)
    modes = json.loads((ROOT/'mode-data.json').read_text())
    encoded_modes = json.dumps(modes, separators=(',', ':')).replace('<', r'\u003c')
    source, count = re.subn(r'(<script id="mode-data" type="application/json">).*?(</script>)',
                            lambda m: m[1]+encoded_modes+m[2], source, flags=re.S)
    assert count == 1
    PAGE.write_text(source)
    print(json.dumps({'gap_rows': len(gaps), 'refinement_stable_rows': sum(g['status'] == 'refinement-stable estimate' for g in gaps),
                      'pending_rows': sum(g['status'] != 'refinement-stable estimate' for g in gaps),
                      'atlas_domains': len(atlas)}, indent=2))


if __name__ == '__main__':
    main()
