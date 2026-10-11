"""Produce a small static mathematical reader from measured/audited artifacts."""
import copy,gzip,hashlib,html,json,shutil
from pathlib import Path

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/induction-receptors-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def esc(s):return html.escape(str(s),quote=True)
def term(t):
    if t[0]=='var':return r'\mathit{'+t[1]+r'}'
    if t[1]=='zero':return '0'
    if t[1]=='succ':return r'\operatorname{S}\!\left('+term(t[2][0])+r'\right)'
    if t[1]=='add':return r'\left('+term(t[2][0])+'+'+term(t[2][1])+r'\right)'
    return r'\operatorname{'+t[1]+r'}\!\left('+','.join(term(a) for a in t[2])+r'\right)'
def formula(f):
    if f[0]=='eq':return term(f[1])+'='+term(f[2])
    if f[0]=='all':return r'\forall\,'+r'\mathit{'+f[1]+r'}\;\left('+formula(f[2])+r'\right)'
    if f[0]=='bot':return r'\bot'
    if f[0] in ('imp','and','or'):return r'\left('+formula(f[1])+{'imp':r'\Rightarrow ','and':r'\land ','or':r'\lor '}[f[0]]+formula(f[2])+r'\right)'
    if f[0]=='not':return r'\neg\left('+formula(f[1])+r'\right)'
    if f[0]=='pred':return r'\operatorname{'+f[1]+r'}\left('+','.join(term(t) for t in f[2])+r'\right)'
    raise ValueError('formula not displayed')
def math(f):return r'\('+esc(formula(f))+r'\)'
def explanation(row,rules):
    rule=row['rule']
    if rule=='refl':return 'An expression equals itself.'
    if rule=='generalize':return 'The previous result is valid for an arbitrary variable; universally quantify it. Source: line '+str(row['source']+1)+'.'
    if rule=='block':
        r=next(r for r in rules if r['command'].get('name')==row['name']);d=r['description'];op=d['operation']
        labels={'rewrite':'Use one recursive addition equation in one expression context.','conditional-rewrite':'Use one equation in one expression context while keeping the induction hypothesis explicit.','conditional-reflexivity':'Start an equality path under the explicit induction hypothesis.','induction':'Combine the checked base and universally quantified implication step by the natural-number induction schema.'}
        label=labels.get(op,op)
        if op in ('rewrite','conditional-rewrite'):label+=' The chosen edge uses '+('the induction hypothesis' if d['move']['rule']['origin']=='assumption' else 'axiom '+d['move']['rule']['name'])+'.'
        if row.get('inputs'):label+=' Inputs: '+', '.join('line '+str(i+1) for i in row['inputs'])+'.'
        return label
    if rule=='assumption':return 'Local hypothesis '+str(row['index']+1)+' of this reusable inference.'
    if rule=='axiom':return 'Use named theory axiom '+row['name']+'.'
    if rule=='instantiate':return 'Use the capture-avoiding universal instantiation scheme.'
    if rule=='eq_subst':return 'Substitute equals for equals in the stated formula template.'
    if rule=='tautology':return 'Use a propositionally valid implication or conjunction identity.'
    if rule=='mp':return 'Apply modus ponens to local lines '+str(row['antecedent']+1)+' and '+str(row['implication']+1)+'.'
    if rule=='distribute':return 'Move a universal quantifier across an implication; its variable is absent from the antecedent.'
    if rule=='induction':return 'Use the enabled induction schema instance.'
    return rule
def reader(raw,c):
    proof=raw['search']['proof'];defs={d['name']:d for d in c['definitions']};record=raw['model'];tiles={tuple(t['key']):t for t in record['placements']};by={(k[0],k[1]):tiles[tuple(k)] for k in raw['search']['placements']};roles=['C','G','I1','I2'];colors=['#7e57c2','#d29a23','#258a63','#d16640'];height=78*len(proof)+40;svg=[];lines=[]
    for j,row in enumerate(proof):
        y=35+78*j;svg.append(f'<text x="10" y="{y+26}" fill="#334">Line {j+1}</text>')
        for r,label in enumerate(roles):
            tile=by[j,r];x=100+135*r;src=tile.get('source');value=next((v for p,v in tile['marks'] if p==[4*j+2,100+r-2]),None) if r>=2 else next(v for p,v in tile['marks'] if p==[4*j+2,1 if r==0 else 0]);unused=r>=2 and src is None
            fill='#f1f2f3' if unused else colors[r];text_fill='#334' if unused else 'white';dash='stroke-dasharray="5 4"' if unused else ''
            label_value='unused (-1)' if unused else 'source '+str(src+1) if r>=2 else 'catalog '+str(value)
            svg.append(f'<g><title>{esc(json.dumps(dict(point=[4*j,r],marks=tile["marks"],key=tile["key"])) )}</title><rect x="{x}" y="{y}" width="110" height="54" rx="6" fill="{fill}" stroke="#25334a" {dash}/><text x="{x+8}" y="{y+20}" fill="{text_fill}">{label}</text><text x="{x+8}" y="{y+40}" fill="{text_fill}">{label_value}</text></g>')
            if r>=2 and src is not None:
                yy=35+78*src+27;edge=665+22*(r-2);svg.append(f'<path d="M {x+110} {y+27} H {edge} V {yy} H 655" fill="none" stroke="{colors[r]}" stroke-width="2"/>')
        line=f'<li id="proof-{j+1}"><div class="proof-formula">{math(row["formula"])}</div><p>{esc(explanation(row,c["rules"]))}</p>'
        if row['rule']=='block':
            d=defs[row['name']];line+='<details><summary>Expand the native-checked local derivation ('+str(len(d['proof']))+' commands)</summary><ol>'
            for local in d['proof']:line+='<li>'+math(local['formula'])+'<p>'+esc(explanation(local,c['rules']))+'</p></li>'
            line+='</ol></details>'
        line+='<details><summary>Exact discovered command and point values</summary><pre>'+esc(json.dumps(dict(command=row,tiles=[by[j,r] for r in range(4)]),indent=2))+'</pre></details></li>';lines.append(line)
    return '<div class="tile-figure"><svg viewBox="0 0 740 '+str(height)+'" role="img" aria-label="Actual colored command guard and source receptor tiles">'+''.join(svg)+'</svg></div><ol class="proof-lines">'+''.join(lines)+'</ol>'
def main():
    plan=json.loads((OUT/'plan.json').read_text());summary=json.loads((OUT/'summary.json').read_text());audit=json.loads((OUT/'audit.json').read_text());c=load(OUT/'catalog.json.gz');admission=load(OUT/'admission.json.gz')
    if summary['status']!='complete' or audit['status']!='passed':raise ValueError('publish only finished audited measurements')
    raws=[load(OUT/(o['id']+'.json.gz')) for o in plan['observations']];proofs=[r for r in raws if r['search']['proof'] is not None]
    rows=''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in (o['id'],o['length'],o['status'],o['attempts'],round(o['search_seconds'],3),o['native_query']))+'</tr>' for o in summary['observations'])
    body=''.join('<section id="'+esc(raw['case']['id'])+'"><h2>'+esc(raw['case']['id'])+'</h2><p>Search selected these '+str(len(raw['search']['proof']))+' commands from the complete declared inference inventory. The whole certificate, including every used local definition, was accepted by the unchanged native checker from its actual parser start.</p>'+reader(raw,c)+'</section>' for raw in proofs)
    if not proofs:body='<p>No proof was discovered within the declared budget. The unfinished search trees remain available for inspection; this does not establish that the theorem is unprovable.</p>'
    document='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arithmetic induction receptors — automatic search</title><link rel="stylesheet" href="report.css"><script>window.MathJax={tex:{inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script><style>main{max-width:1120px;margin:auto;padding:24px}.tile-figure svg{width:100%;max-width:820px}.proof-lines>li{padding:16px 10px;border-bottom:1px solid #ccd}.proof-formula{font-size:1.1em;overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{margin:10px 0}table{border-collapse:collapse}td,th{border:1px solid #ccd;padding:8px}section{margin:36px 0}.status{padding:16px;background:#e9f4ee;border-left:4px solid #258a63}</style></head><body><main><p><a href="index.html#goals">Research program</a> · <a href="first-order-families.html#reader">First-order families</a></p><h1>Arithmetic induction receptors</h1>'''
    document+='<p class="status">'+str(len(proofs))+' automatically selected proof observations; '+str(len(c['definitions']))+' independently native-admitted local definitions. Every recorded point-search node and native computation passed independent replay.</p><h2>External theorem and theory</h2><p>'+math(plan['case']['target'])+'</p><p>The theory contains the recursive addition equations '+math(plan['case']['theory']['axioms']['AZ'])+' and '+math(plan['case']['theory']['axioms']['AS'])+', together with the native natural-number induction schema. These are sufficient for this theorem. This is an arithmetic fragment; it is not a claim to have implemented every Peano axiom or unrestricted arithmetic search.</p>'
    document+='<h2>What was authored, and what was found</h2><p>Authored infrastructure enumerates every term with at most four nodes, every recursive equation direction and expression occurrence, and every permitted substitution. It creates generic one-edge equality deductions, a Hilbert deduction transformation, safe quantifier distribution/generalization, and an induction interface for each quantified target variable. No sequence of target-proof moves is supplied. GCTS selects the actual local inferences and their source lines.</p><p>The finite contextual equational adaptation contains '+str(len(c['terms']))+' terms, '+str(len(c['basis']))+' formulas and '+str(len(c['rules']))+' inference templates. The separate '+str(len(c['primitive_schemes']))+' primitive-scheme syntax catalog has only '+str(len(admission['primitive']))+' native diagnostic checks in this pilot; its compilation remains <code>unknown_compile_budget</code>. It is not the searched grammar.</p>'
    document+='<h2>Measured searches</h2><table><thead><tr><th>Run</th><th>Rows</th><th>Outcome</th><th>Attempts</th><th>Search seconds</th><th>Whole native query</th></tr></thead><tbody>'+rows+'</tbody></table><p>Catalog construction: '+str(round(summary['catalog_seconds'],3))+' s. Fresh shared definition admission and primitive diagnostics: '+str(round(summary['admission_seconds'],3))+' s. Producer total: '+str(round(summary['total_seconds'],3))+' s. Independent audit: '+str(round(audit['seconds'],3))+' s, '+str(audit['queries'])+' complete native computations and '+str(audit['native_micro_steps'])+' micro steps. Both searches use fresh models and graphs, with shared disclosed native admission. These observations are not an RL comparison or a speed claim against existing theorem provers.</p><h2>Colored point markings</h2><p>The actual selected roles are <code>C</code> (command, purple), <code>G</code> (admitted interface, gold), <code>I1</code> (green) and <code>I2</code> (orange). Matching exact catalog values bind complete canonical formula/command words. Extended markings connect each input to its actual earlier source. Dashed gray tiles assign an explicit unused value. Occupancy is one unit per root, all roots start at generation zero, and orientations are fixed. This is a high-level point adaptation; no primitive-square occupancy embedding is claimed.</p>'+body
    document+='<h2>Independent evidence</h2><p>The auditor reconstructs the full finite term and rewrite catalog by exhaustive substitution, independently reconstructs every scalar point tile, scans complete candidate domains at every tree node, and verifies global dead/forced/earliest-generation decisions, fallback and rollback. Each native computation is rerun from parser state <code>88986</code>, with the entire input/output bands and execution fingerprint matched. Separate native probes accept safe generalization/deduction and reject variable capture through an open premise, invalid quantifier distribution, and induction without authorization.</p><p><a href="induction_receptors_plan.json">Predeclared plan</a> · <a href="induction_receptors_audit.json">Independent audit</a> · <a href="induction_receptors_summary.json">Measured costs</a> · <a href="induction_receptors_catalog.json.gz">Complete finite catalog</a> · <a href="induction_receptors_native.json.gz">All native requests and results</a></p></main></body></html>'
    (DOC/'induction_receptors.html').write_text(document)
    files=[]
    for source,target in [('plan.json','induction_receptors_plan.json'),('audit.json','induction_receptors_audit.json'),('summary.json','induction_receptors_summary.json'),('catalog.json.gz','induction_receptors_catalog.json.gz'),('admission.json.gz','induction_receptors_admission.json.gz'),('native-records.json.gz','induction_receptors_native.json.gz')]:shutil.copyfile(OUT/source,DOC/target);files.append(str((DOC/target).relative_to(ROOT)))
    for p in plan['observations']:
        target='induction_receptors_'+p['id']+'.json.gz';shutil.copyfile(OUT/(p['id']+'.json.gz'),DOC/target);files.append(str((DOC/target).relative_to(ROOT)))
    files+=['docs/research/gcts-rl-renewal/induction_receptors.html']+[str(p.relative_to(ROOT)) for p in sorted(HERE.glob('induction_receptors_*.py'))]
    manifest=dict(files=[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in files],status='prepared-for-root-integration',published=False)
    (OUT/'integration.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(files=len(files),proof_observations=len(proofs),html_bytes=len(document.encode()))))

if __name__=='__main__':main()
