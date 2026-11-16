"""Draw the actual checked Wang-style proof patch with syntax marks."""

from html import escape
import json
from pathlib import Path
from string import Template

from prime_tiling import assemble, check_patch, final_context
from proof_view import clause_tokens, formula, math
from tile_syntax import CATEGORIES, clause_mask


def bands(mask):
    colors = [color for bit, (_, _, color) in enumerate(CATEGORIES) if mask & (1 << bit)]
    if not colors:
        return 'var(--vacant)'
    stops = []
    for i,color in enumerate(colors):
        stops.append(f'{color} {100*i/len(colors):.2f}% {100*(i+1)/len(colors):.2f}%')
    return 'linear-gradient(90deg,'+','.join(stops)+')'


def tile(row, col, marks, role, masks):
    north, _, south, _ = marks
    top = north[2] if north[0]=='register' else None
    bottom = south[2] if south[0]=='register' else None
    label = f'Row {row+1}, column {col+1}, {role}'
    styles = f'--north:{bands(masks[top] if top is not None else 0)}; ' \
             f'--south:{bands(masks[bottom] if bottom is not None else 0)}'
    return (f'<button class="tile tile-{role}" type="button" aria-label="{label}" tabindex="-1" '
            f'aria-pressed="false" data-row="{row}" data-col="{col}" data-role="{role}" '
            f'data-north="{top if top is not None else ""}" data-south="{bottom if bottom is not None else ""}" '
            f'style="{styles}"><i></i><i></i></button>')


def render(results, output):
    saved = results/'proof-tiling.json'
    patch = json.loads(saved.read_text()) if saved.is_file() else assemble(results)
    sources, _, _ = final_context(results)
    roles = check_patch(patch,sources)
    masks = list(map(clause_mask,patch['clauses']))
    rows = '\n'.join(f'<div class="tile-row" role="group" aria-label="Row {i+1}">'+
                     ''.join(tile(i,j,marks,roles[i][j],masks) for j,marks in enumerate(row))+
                     '</div>' for i,row in enumerate(patch['squares']))
    legend = '\n'.join(f'<span><i style="background:{color}"></i>{escape(label)}</span>'
                       for _,label,color in CATEGORIES)
    clauses = '\n'.join(f'<template id="clause-{i}">{clause_tokens(clause)}</template>'
                        for i,clause in enumerate(patch['clauses']))
    library = json.loads((results/'certificate.json').read_text())['library']
    exemplar = math(formula(library['prime-divisor']['formula']))
    template = Template(Path(__file__).with_name('tiling-template.html').read_text())
    (output/'tiling.html').write_text(template.substitute(
        nrows=len(roles), ncolumns=len(roles[0]), legend=legend, rows=rows,
        clauses=clauses, exemplar=exemplar,
    ))
