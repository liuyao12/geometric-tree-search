"""Draw the checked proof board and expand a clause into its symbols."""

import json
from pathlib import Path
from string import Template

from prime_tiling import assemble, check_patch, final_context
from proof_view import WITNESS_ALIASES, formula, math, operator, variable


def bracket(tokens):
    return [('punctuation','('),*tokens,('punctuation',')')]


def symbols(clause):
    if not clause:
        return [('empty',r'\bot')]
    free = set()

    def term(node):
        if isinstance(node,str):
            if node.startswith('?'):
                free.add(node)
                return [('variable',variable(node))]
            if node in WITNESS_ALIASES:
                return [('witness',WITNESS_ALIASES[node])]
            return [('number',{'zero':'0','one':'1'}[node])]
        name,*args = node
        if name in ('plus','mul'):
            left,right = [bracket(term(a)) if isinstance(a,(tuple,list)) and
                          a[0] in ('plus','mul') else term(a) for a in args]
            return [*left,('arithmetic','+' if name=='plus' else r'\cdot'),*right]
        return [('witness',WITNESS_ALIASES[name]),*bracket(join(map(term,args),('punctuation',',')))]

    literals = []
    for sign,name,args in clause:
        if name=='prime':
            literal = [('predicate',r'\operatorname{Prime}'),*bracket(term(args[0]))]
        else:
            relation = {'lt':'<','le':r'\le','divides':r'\mid','eq':'='}[name]
            literal = [*term(args[0]),('predicate',relation),*term(args[1])]
        literals.append(literal if sign else [('negation',operator('not')),*bracket(literal)])
    body = join(literals,('connective',operator('or')))
    if not free:
        return body
    variables = join(([('variable',variable(name))] for name in sorted(free)),('punctuation',','))
    return [('quantifier',operator('all')),*variables,*bracket(body)]


def join(groups,separator):
    result = []
    for group in groups:
        if result:
            result.append(separator)
        result.extend(group)
    return result


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
    clauses = '\n'.join(f'<template id="clause-{i}">'+
                        ''.join(f'<span class="symbol symbol-{kind}" title="{kind}">'+math(tex)+'</span>'
                                for kind,tex in symbols(clause))+'</template>'
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
