"""Draw the checked proof board and show the clause carried by a tile."""

import json
from pathlib import Path
from string import Template

from prime_tiling import assemble, check_patch, final_context
from proof_view import WITNESS_ALIASES, formula, math, variable_tex


def bracket(tex):
    return r'\bigl('+tex+r'\bigr)'


def clause_sentence(clause):
    if not clause:
        return r'\bot'
    free = set()

    def term(node):
        if isinstance(node,str):
            if node.startswith('?'):
                free.add(node)
                return variable_tex(node)
            if node in WITNESS_ALIASES:
                return WITNESS_ALIASES[node]
            return {'zero':'0','one':'1'}[node]
        name,*args = node
        if name in ('plus','mul'):
            left,right = [bracket(term(a)) if isinstance(a,(tuple,list)) and
                          a[0] in ('plus','mul') else term(a) for a in args]
            symbol = '+' if name=='plus' else r'\cdot'
            return f'{left} {symbol} {right}'
        return WITNESS_ALIASES[name]+bracket(','.join(map(term,args)))

    literals = []
    for sign,name,args in clause:
        if name=='prime':
            literal = r'\operatorname{Prime}'+bracket(term(args[0]))
        else:
            relation = {'lt':'<','le':r'\le','divides':r'\mid','eq':'='}[name]
            literal = f'{term(args[0])} {relation} {term(args[1])}'
        literals.append(literal if sign else r'\neg '+bracket(literal))
    body = r' \lor '.join(literals)
    if not free:
        return body
    variables = ','.join(map(variable_tex,sorted(free)))
    return r'\forall\, '+variables+r'\;'+bracket(body)


def tile(row, col, marks, role):
    north, _, south, _ = marks
    top = north[2] if north[0]=='register' else None
    bottom = south[2] if south[0]=='register' else None
    visible = f'C{bottom+1}' if bottom is not None else ''
    label = f'Row {row+1}, column {col+1}, {role} {visible}'.rstrip()
    return (f'<button class="tile tile-{role}" type="button" aria-label="{label}" tabindex="-1" '
            f'aria-pressed="false" data-row="{row}" data-col="{col}" data-role="{role}" '
            f'data-north="{top if top is not None else ""}" data-south="{bottom if bottom is not None else ""}" '
            f'>{visible}</button>')


def render(results, output):
    saved = results/'proof-tiling.json'
    patch = json.loads(saved.read_text()) if saved.is_file() else assemble(results)
    sources, _, _ = final_context(results)
    roles = check_patch(patch,sources)
    rows = '\n'.join(f'<div class="tile-row" role="group" aria-label="Row {i+1}">'+
                     ''.join(tile(i,j,marks,roles[i][j]) for j,marks in enumerate(row))+
                     '</div>' for i,row in enumerate(patch['squares']))
    clauses = '\n'.join(f'<template id="clause-{i}" data-empty="{str(not clause).lower()}">'+
                        math(clause_sentence(clause))+'</template>'
                        for i,clause in enumerate(patch['clauses']))
    library = json.loads((results/'certificate.json').read_text())['library']
    conclusion = math(formula(library['unbounded-primes']['formula']))
    steps = []
    for row, move in zip(patch['squares'],patch['moves']):
        written = row[move['write']+1][2][2]
        steps.append({'parents':move['claims'],'written':written})
    template = Template(Path(__file__).with_name('tiling-template.html').read_text())
    (output/'tiling.html').write_text(template.substitute(
        nrows=len(roles), ncolumns=len(roles[0]), rows=rows,
        clauses=clauses, conclusion=conclusion, steps=json.dumps(steps,separators=(',',':')),
    ))
