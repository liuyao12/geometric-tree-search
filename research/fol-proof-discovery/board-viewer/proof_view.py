"""Render the checked resolution certificate as a color-coded proof."""

from html import escape
import json
from pathlib import Path
import re
from string import Template

from prime_tiling import final_context


COLORS = {
    'quantifier': '704598',
    'variable': '1B508D',
    'predicate': '166353',
    'negation': 'A03733',
    'implication': '825015',
    'connective': '715489',
    'witness': '884361',
}
OPERATORS = {
    'all': ('quantifier', r'\forall'),
    'some': ('quantifier', r'\exists'),
    'not': ('negation', r'\neg'),
    'and': ('connective', r'\land'),
    'or': ('connective', r'\lor'),
    'implies': ('implication', r'\Rightarrow'),
}
WITNESS_ALIASES = {'_sk19_1': r'd_\star', '_sk20_1': r'm_\star', '_skgoal_0': 'b'}
LIBRARY = {'prime-divisor': 'Prime divisor', 'bounded-positive-le-divides': 'Common multiple'}


def paint(kind, tex):
    color = COLORS[kind]
    channels = ','.join(str(int(color[i:i+2], 16)) for i in (0,2,4))
    return r'\textcolor[RGB]{' + channels + '}{' + tex + '}'


def operator(kind):
    category, tex = OPERATORS[kind]
    return paint(category, tex)


def variable(name):
    if name.startswith('@') and re.fullmatch('[a-z]', name[1:]):
        return paint('variable', name[1:])
    match = re.fullmatch(r'\?v([0-9]+)', name)
    if match:
        return paint('variable', 'v_{'+match[1]+'}')
    raise ValueError('Unsupported proof variable '+name)


def term(value):
    if isinstance(value, str):
        if value.startswith(('?', '@')):
            return variable(value)
        if value in WITNESS_ALIASES:
            return paint('witness', WITNESS_ALIASES[value])
        return {'zero': '0', 'one': '1'}[value]
    name, *args = value
    if name in ('plus', 'mul'):
        symbol = '+' if name=='plus' else r'\cdot'
        parts = [r'\bigl('+term(a)+r'\bigr)' if isinstance(a, (list, tuple)) and
                 a[0] in ('plus','mul') else term(a) for a in args]
        return (' '+symbol+' ').join(parts)
    return paint('witness', WITNESS_ALIASES[name]) + r'\bigl(' + ','.join(map(term,args)) + r'\bigr)'


def atom(name, args):
    if name=='prime':
        return paint('predicate', r'\operatorname{Prime}') + r'\bigl(' + term(args[0]) + r'\bigr)'
    glyph = {'lt': '<', 'le': r'\le', 'divides': r'\mid', 'eq': '='}[name]
    return term(args[0]) + paint('predicate', glyph) + ' ' + term(args[1])


def formula(node):
    tag, *args = node
    if tag=='atom':
        return atom(*args)
    if tag in ('all','some'):
        name, body = args
        return operator(tag)+variable(name)+r'\;\bigl('+formula(body)+r'\bigr)'
    if tag=='not':
        return operator('not')+r'\bigl('+formula(args[0])+r'\bigr)'
    if tag=='or' and len(args)==2 and args[0][0]=='not':
        return formula(args[0][1])+' '+operator('implies')+' '+formula(args[1])
    if tag in ('and','or'):
        return r'\bigl(' + (' '+operator(tag)+' ').join(map(formula,args)) + r'\bigr)'
    raise ValueError('Unsupported formula syntax '+tag)


def math(tex):
    return r'\(' + escape(tex) + r'\)'


def clause_tokens(clause):
    if not clause:
        return '<span class="literal" aria-label="Empty clause">'+math(r'\bot')+'</span>'
    literals = []
    variables = set()

    def observe(value):
        if isinstance(value, str):
            if value.startswith('?'):
                variables.add(value)
        else:
            for arg in value[1:]:
                observe(arg)

    for sign,name,args in clause:
        for arg in args:
            observe(arg)
        literal = atom(name,args)
        if not sign:
            literal = operator('not') + r'\bigl(' + literal + r'\bigr)'
        literals.append('<span class="literal">'+math(literal)+'</span>')
    content = ('<span class="join">'+math(operator('or'))+'</span>').join(literals)
    if not variables:
        return content
    closure = operator('all')+r'\,'+','.join(map(variable,sorted(variables)))+r'\;\bigl('
    return '<span class="scope">'+math(closure)+'</span>'+content+math(r'\bigr)')


def source_label(name):
    if name in LIBRARY:
        return f'<a href="#{name}">{LIBRARY[name]} theorem</a>'
    if name=='goal-denial':
        return 'Negated goal'
    return escape(name.replace('-',' ').capitalize())


def line_table(steps,names):
    entries = []
    for index, step in enumerate(steps,1):
        rule = step['rule']
        if rule=='input':
            reason = source_label(names[step['source']])
        else:
            parents = ' and '.join(f'<a href="#line-{p+1}">line {p+1}</a>' for p in step['parents'])
            reason = {'resolve':'Resolve','factor':'Factor'}[rule]+' '+parents
        if not step['clause']:
            reason += ' · empty clause'
        entries.append(
            f'<li id="line-{index}" value="{index}">'
            f'<span class="line-number" aria-hidden="true">{index:02}</span>'
            f'<div class="clause">{clause_tokens(step["clause"])}</div>'
            f'<span class="reason">{reason}</span></li>'
        )
    return '\n'.join(entries)


def render(results, output):
    # Reuse the checker and its exact source numbering before generating HTML.
    _, names, steps = final_context(results)
    library = json.loads((results/'certificate.json').read_text())['library']
    samples = [
        ('Quantifiers', operator('all')+r',\;'+operator('some')),
        ('Variables', variable('@n')+r',\;'+variable('@p')),
        ('Predicates', paint('predicate',r'\operatorname{Prime}')+r',\;'+paint('predicate',r'<,\mid')),
        ('Negation', operator('not')),
        ('Implication', operator('implies')),
        ('And / or', operator('and')+r',\;'+operator('or')),
        ('Witness symbols', paint('witness',r'd_\star,\;m_\star,\;b')),
    ]
    legend = '\n'.join(f'<span>{math(tex)} <span>{label}</span></span>' for label,tex in samples)
    lemmas = '\n'.join(f'<div class="lemma" id="{key}"><h3>{title}</h3>'
                       f'<p class="formula">{math(formula(library[key]["formula"]))}</p></div>'
                       for key,title in LIBRARY.items())
    bindings = math(term('_skgoal_0'))+' names the bound assumed in the negated goal. '+math(
        paint('witness', WITNESS_ALIASES['_sk19_1']))+' and '+math(
        paint('witness', WITNESS_ALIASES['_sk20_1']))+' name witnesses supplied by the two library theorems.'
    template = Template(Path(__file__).with_name('proof-template.html').read_text())
    (output/'proof.html').write_text(template.substitute(
        legend=legend, lemmas=lemmas, bindings=bindings, lines=line_table(steps,names),
        conclusion=math(formula(library['unbounded-primes']['formula'])),
        input_count=sum(step['rule']=='input' for step in steps), last_line=len(steps),
    ))
