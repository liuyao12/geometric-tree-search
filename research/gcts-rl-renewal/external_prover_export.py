"""Publishable standalone report from the saved external control, without search."""
import gzip,html,json,pathlib,statistics
from external_prover_check import records,leaves,native_formula
from external_prover_inputs import sha

ROOT=pathlib.Path(__file__).resolve().parents[2]
PRIVATE=ROOT/'.gcts-active/external-prover-20261011'
PUBLIC=ROOT/'docs/research/gcts-rl-renewal'

def esc(s):return html.escape(str(s))
def name(s):return r'\mathrm{'+s.replace('_',r'\_')+'}'
def tex(f,m):
    h=f[0]
    if h=='var':return 'x_{'+f[1][1:]+'}' if f[1].startswith('X') else name(f[1])
    if h=='fun':
        n={v:k for k,v in m['functions'].items()}[f[1]]
        return (r'\operatorname{'+n.replace('_',r'\_')+'}('+','.join(tex(t,m) for t in f[2])+')') if f[2] else name(n)
    if h=='pred':
        n={v:k for k,v in m['predicates'].items()}[f[1]]
        return r'\operatorname{'+n.replace('_',r'\_')+'}'+('('+','.join(tex(t,m) for t in f[2])+')' if f[2] else '')
    if h=='eq':return tex(f[1],m)+'='+tex(f[2],m)
    if h=='bot':return r'\bot'
    if h=='top':return r'\top'
    if h=='not':return r'\neg\bigl('+tex(f[1],m)+r'\bigr)'
    if h in ('and','or','imp'):return r'\bigl('+tex(f[1],m)+{'and':r'\land ','or':r'\lor ','imp':r'\Rightarrow '}[h]+tex(f[2],m)+r'\bigr)'
    if h in ('forall','exists'):
        return (r'\forall ' if h=='forall' else r'\exists ')+tex(('var',f[1]),m)+r'\;\bigl('+tex(f[2],m)+r'\bigr)'
    raise ValueError(h)

def proof_panel(obs,m,text,check,index):
    p=['<article class="proof-panel" id="proof-'+str(index)+'"'+(' hidden' if index else '')+'>']
    p.append('<p><strong>'+esc(obs['case'])+'</strong> · '+esc(obs['lane'])+' · repetition '+str(obs['repetition'])+'</p>')
    if obs['certificate_status']!='checked_complete_derivation':
        p.append('<p>E returned <code>'+esc(obs['szs_status'])+'</code>. This is not a proof of the conjecture. The separate audit interpretation below confirms that the disconnected conclusion is false in a model of the hypotheses and the entire admitted library.</p>')
        cm=check.get('countermodel')
        if cm and cm['status']=='independently_checked_countermodel':
            domain='D='+r'\{'+','.join(str(v) for v in cm['domain'])+r'\}'
            constants=',\;'.join(name(n)+'='+str(v) for n,v in cm['constants'].items())
            predicates=[]
            for n,tuples in cm['predicate'].items():
                values=[str(t[0]) if len(t)==1 else '('+','.join(str(v) for v in t)+')' for t in tuples]
                predicates.append(r'\operatorname{'+n+'}='+r'\{'+','.join(values)+r'\}')
            target=next(e['formula'] for e in m['entries'] if e['role']=='conjecture')
            target_formula=tex(native_formula(target,m),m)+'='+r'\bot'
            entries=[('Domain',domain),('Constant assignments',constants),('Predicate extension',r',\;'.join(predicates)),('Target value',target_formula)]
            p.append('<table><thead><tr><th>Exact interpretation</th><th>Audited value</th></tr></thead><tbody>')
            for label,value in entries:p.append('<tr><td>'+label+'</td><td>\\('+esc(value)+'\\)</td></tr>')
            p.append('</tbody></table><p class="small">All '+str(len(cm['axioms']))+' hypotheses and all '+str(len(cm['lemmas']))+' supplied lemma interfaces evaluate true; the target evaluates false. The finite interpretation is separate audit evidence, not E’s returned model and not a search input.</p>')
            p.append('<details><summary>Actual independent countermodel check</summary><pre>'+esc(json.dumps(cm,indent=2))+'</pre></details>')
    else:
        rs=records(text);numbers={r['name']:i+1 for i,r in enumerate(rs)}
        p.append('<p class="small">'+str(len(rs))+' returned lines. All file-backed inputs and every inference are checked, including preprocessing. A displayed quantified variable is local to its formula; renaming is immaterial. The original symbol names are restored.</p>')
        for i,r in enumerate(rs):
            s=r['source'];ch=check['checks'][i];p.append('<div class="proof-line"><span class="line-number">'+str(i+1)+'</span><div>')
            p.append('<div class="formula">\\('+esc(tex(r['formula'],m))+'\\)</div>')
            if s['head']=='file':
                meaning='Statement to prove. It is not an assumed premise.' if r['role']=='conjecture' else 'Input hypothesis '+ch['original_name']+'.'
            elif s['args'][0]=='assume_negation':meaning='Assume the negation of line '+str(numbers[ch['parents'][0]])+' and seek a contradiction.'
            else:
                ps=', '.join(str(numbers[n]) for n in ch['parents']);rule=s['args'][0]
                meaning={'fof_simplification':'Simplify the formula','fof_nnf':'Put the formula into negation normal form','split_conjunct':'Extract the universally closed clause','cn':'Obtain the contradiction after the recorded rewrites/inferences'}.get(rule,'Derive the formula')+' from line(s) '+ps+'.'
            p.append('<p>'+esc(meaning)+'</p><p class="small"><code>'+esc(r['name'])+'</code> · '+esc(ch['status'])+(' · '+str(ch['ground_clauses'])+' ground clauses / '+str(ch['refutation']['nodes'])+' certificate-tree nodes' if 'refutation' in ch else '')+'</p>')
            p.append('<details><summary>Actual TSTP source and independent check</summary><pre>'+esc(json.dumps(dict(source=s,check=ch),indent=2))+'</pre></details></div></div>')
    p.append('<details><summary>Complete returned TSTP output</summary><pre>'+esc(text)+'</pre></details></article>');return ''.join(p)

def main():
    s=json.loads((PRIVATE/'summary.json').read_text());a=json.loads((PRIVATE/'audit.json').read_text());prep=json.loads((PRIVATE/'preparation.json').read_text());plan=json.loads((PRIVATE/'plan.json').read_text())
    if s['status']!='complete' or a['status']!='passed':raise ValueError('unvalidated control')
    observations=s['observations'];options=[];panels=[];bundle={};titles={c['case']:c for c in s['gcts_reference']}
    for i,o in enumerate(observations):
        stem=o['case']+'-'+('library' if o['lane']!='theory-only' else 'theory');base=stem+'-r'+str(o['repetition'])
        m=json.loads((PRIVATE/(stem+'.mapping.json')).read_text());text=(PRIVATE/(base+'.tstp')).read_text();check=json.loads((PRIVATE/(base+'.check.json')).read_text())
        options.append('<option value="'+str(i)+'">'+esc(o['case']+' · '+('with library' if o['lane']!='theory-only' else 'theory only')+' · run '+str(o['repetition']))+'</option>')
        panels.append(proof_panel(o,m,text,check,i));bundle[base]=dict(mapping=m,output=text,check=check,observation=o)
    rows=[]
    for case,ref in titles.items():
        theory=[o for o in observations if o['case']==case and o['lane']=='theory-only'];library=[o for o in observations if o['case']==case and o['lane']!='theory-only'];gcts=[o for o in ref['observations'] if o['lane']=='family-base']
        def span(v):return f'{min(v):.3f}–{max(v):.3f}'
        verdict='checked' if theory[0]['certificate_status']=='checked_complete_derivation' else 'countermodel audited'
        gstatus='proof' if gcts[0]['status']=='finite_marked_proof_region' else 'unknown'
        rows.append('<tr><td>'+esc(case)+'</td><td>'+verdict+'</td><td>'+span([1000*o['wall_seconds'] for o in theory])+'</td><td>'+span([1000*o['wall_seconds'] for o in library])+'</td><td>'+gstatus+' · '+span([o['seconds'] for o in gcts])+'</td></tr>')
    data=dict(version='external-prover-evidence-1',summary=s,audit=a,preparation=prep,plan=plan,traces=bundle,
              calibration_files={p.name:p.read_text() for p in PRIVATE.glob('calibration*') if p.is_file()})
    packed=(json.dumps(data,separators=(',',':'))+'\n').encode();gz=gzip.compress(packed,mtime=0);data_path=PUBLIC/'external_prover_control_data.json.gz';data_path.write_bytes(gz)
    PUBLIC.joinpath('external_prover_control_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    PUBLIC.joinpath('external_prover_control_audit.json').write_text(json.dumps(a,indent=2)+'\n')
    PUBLIC.joinpath('external_prover_control_summary.json').write_text(json.dumps({k:v for k,v in s.items() if k not in ('setup','gcts_reference')},indent=2)+'\n')
    page=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>External automated prover control · GCTS research</title>
<link rel="stylesheet" href="report.css?v=20261011-ep1"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>.intro{margin-top:42px}h1{font-size:clamp(40px,5vw,64px)}.small{font-size:12px;line-height:1.7}.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:30px 0}.flow>div{padding:18px;border-top:4px solid #377fa0;background:#f3f5ee}.flow>div:last-child{border-color:#337a59}.flow strong{display:block;margin-bottom:12px}.scroll-table{overflow:auto}table{border-collapse:collapse;width:100%;font-size:12px}th,td{text-align:left;padding:11px;border-bottom:1px solid var(--line)}.proof-line{display:grid;grid-template-columns:40px minmax(0,1fr);gap:14px;padding:18px 0;border-bottom:1px solid var(--line)}.line-number{font-size:12px;color:var(--muted)}.formula{font-size:19px;overflow:auto;max-width:100%}pre{white-space:pre;overflow:auto;max-height:400px;font-size:11px}select{max-width:100%}[hidden]{display:none!important}@media(max-width:650px){.flow{grid-template-columns:repeat(2,1fr)}.proof-line{grid-template-columns:25px minmax(0,1fr);gap:8px}}</style></head><body>
<header class="masthead"><a href="./#first-order-families">GCTS + RL · Research notebook</a><span>EXTERNAL CONTROL · E FIRST-ORDER SEARCH</span></header><main>
<section class="intro"><p class="eyebrow">IDENTICAL ASSERTIONS · TWO LIBRARIES · COMPLETE LOGICAL CHECKING</p><h1>A real external<br>proof-search control.</h1><p class="deck">E solves these same small assertions far more cheaply. Their success does not establish a competitive advantage for GCTS or its learned ordering.</p>
<p>The official E implementation automatically discovers a refutation from each original theory and negated target. The two lanes supply either the theory alone or that theory plus every previously admitted ground lemma interface. No target derivation is supplied. The returned proof lines are independently checked, including formula preprocessing.</p><p>Across \(28\) fresh prover runs, \(24\) full derivations pass the separate checker. They cover the six valid assertions in both lanes and both repetitions. Four runs return <code>CounterSatisfiable</code> for the disconnected premise. A separate exact interpretation confirms that this target is false while all hypotheses and all supplied lemmas hold. No returned proof references a learned lemma.</p>
<div class="flow"><div><strong>Exact assertions</strong>Injective symbol mapping. Same axioms, target, and optional admitted lemma interfaces.</div><div><strong>Automatic search</strong>E’s first-order saturation calculus. No fixed proof-row boundary.</div><div><strong>Returned derivation</strong>File-backed inputs, negated goal, preprocessing, clauses, and contradiction.</div><div><strong>Independent checking</strong>Every local consequence has a certified Herbrand/EUF refutation. Unknown checks cannot pass.</div></div></section>
<section class="panel" id="comparison"><h2>Measured result and its practical meaning.</h2><div class="scroll-table"><table><thead><tr><th>Frozen assertion</th><th>E evidence</th><th>E theory-only ms</th><th>E with library ms</th><th>Earlier GCTS family-base seconds</th></tr></thead><tbody>__ROWS__</tbody></table></div>
<p class="small">Ranges show two repetitions, with lane order reversed in the second. The E columns measure binary execution including parsing, preprocessing, search and printed proof/statistics output. The GCTS column reuses Notebook 68 search times, which include graph construction and proposals but exclude its separately charged setup and final native checking.</p>
<p>E’s broader calculus permits unrestricted term/quantifier instantiation and has no five-, seven-, or nine-row boundary. The GCTS primitive and family command catalogs are finite, and adding families changes their certificate language. Equal hypotheses and lemma interfaces therefore do not make the candidate grammars equal. Different certificate checkers, budgets and concurrent host workloads also prevent a formal speed-ratio claim.</p><p>These easy equality-transport and Horn-style assertions are useful correctness tests, but poor evidence of a learned-search advantage. More substantial arithmetic induction, Hilbert incidence, and standard TPTP problems remain separate experiments. The checker can be extended for those inputs; no result is extrapolated to them here.</p>
<p>There is no external point-tiling conformance claim. E is a specialized first-order control; the existing GCTS runs retain their own complete point/candidate graph, scheduler and rollback semantics. This external derivation has not been translated into the native Wang checker.</p></section>
<section class="panel" id="reader"><h2>Read what E actually discovered.</h2><p>Choose a saved run. Formula rows restore the original symbol names; English describes the actual role of each line. A compact E inference may nest several rewrites or superpositions in its source annotation. The independent checker proves the displayed child from all actual leaf parents, rather than trusting an inference label.</p><div class="controls"><label for="external-proof-control">Actual external run</label><select id="external-proof-control">__OPTIONS__</select></div>__PANELS__</section>
<section class="panel" id="checking"><h2>Why finite grounding is sound here.</h2><p>For each inference, the checker conjoins its universally closed parents with the negation of its universally closed child. Polarity-correct negation normal form flips quantifiers. Bound variables receive fresh identities, and each existential receives a fresh Skolem symbol depending on the universal variables in its lexical scope. Distributing conjunction/disjunction yields implicit universal clauses. A finite collection of their ground instances is sufficient only when it has an actual refutation.</p><p>This is not a finite-domain approximation. Satisfiable ground instances produce <em>unknown</em>, not a validity claim. Negative universal formulas create properly scoped fresh witnesses before grounding. Tests specifically reject \(P(a)\Rightarrow\forall x\,P(x)\) and \((\exists x\,P(x))\Rightarrow P(a)\), and do not refute the satisfiable assertion \(\forall x\,\exists y\,(x\ne y)\).</p><p>A binary propositional certificate covers both truth values at every split. Each leaf identifies a falsified clause or an equality/congruence conflict. Proof-tree replay recomputes equality closure with a separate relation algorithm. Predicate values must agree on congruent arguments. Every file-backed hypothesis is compared directly with the original AST, independent of the TPTP printer, allowing only bound-variable renaming.</p><p>The checker rejects unsupported E-introduced symbols, arity changes, missing parents and opaque sources. It does not treat arbitrary Skolemization or definitional preprocessing in E as logical entailment. All actual recipient preprocessing passed without such a gap. Future unsupported preprocessing will remain unknown until a sound certificate rule is added.</p><p><a href="https://github.com/eprover/eprover/blob/3b7afc70fe77d3118bb95144c4735ca45f5f31cf/README.md">E’s official README</a> explains proof-object output and warns that its bundled <code>checkproof</code> skips non-clausal first-order steps. That checker was not used to establish these results. The syntax and conjecture/lemma roles follow the <a href="https://tptp.org/UserDocs/TPTPLanguage/TPTPLanguage.shtml">official TPTP language documentation</a>.</p></section>
<section class="panel" id="costs"><h2>Preparation and verification are charged separately.</h2>__COSTS__
<p>The library already exists and its ground-native admission is disclosed reuse from Notebook 68. The external experiment additionally checks all \(232\) recipient ground lemma interfaces as logical consequences without hypotheses, and binds each interface to its actual previously accepted native query. It does not rerun those native computations. The countermodel is audit-only and never enters search.</p><p>The measured cold rebuild uses already downloaded/configured official source. Original source acquisition, configuration and training-case calibration were not instrumented and are excluded; the reported rebuild is not a total cold acquisition cost. The recorded E build is a <code>DEBUG</code> configuration. Repeated searches use fresh processes but a warm filesystem cache. These limits must accompany any cost comparison.</p></section>
<section class="panel" id="evidence"><h2>Saved evidence and reproduction.</h2><p>Independent replay checks all \(24\) derivations and their \(328\) displayed proof lines. It rejects \(72\) corrupted recipient traces and \(204\) corrupted local refutation trees. Seven test groups cover quantifier scope, equality/function congruence, source mapping, and calibration trace corruption. The trusted checker includes its parser, AST conversion, negation/Skolem/clause transformations, ground-instance producer and certificate replay; this implementation has not itself been formally verified.</p>
<p><a href="external_prover_control_data.json.gz">Complete evidence bundle</a> · <a href="external_prover_control_summary.json">Measured summary</a> · <a href="external_prover_control_plan.json">Frozen plan</a> · <a href="external_prover_control_audit.json">Audit and corruptions</a></p>
<p><a href="../../../research/gcts-rl-renewal/external_prover_inputs.py">Input exporter</a> · <a href="../../../research/gcts-rl-renewal/external_prover_check.py">Independent checker</a> · <a href="../../../research/gcts-rl-renewal/external_prover_run.py">Measurement runner</a> · <a href="../../../research/gcts-rl-renewal/external_prover_audit.py">Replay audit</a> · <a href="../../../research/gcts-rl-renewal/external_prover_tests.py">Soundness fixtures</a></p>
<details><summary>Reproduce the external search from the repository root</summary><pre>git clone https://github.com/eprover/eprover.git /private/tmp/gcts-e-reproduce
git -C /private/tmp/gcts-e-reproduce checkout 3b7afc70fe77d3118bb95144c4735ca45f5f31cf
# In that directory: ./configure, then make. See E's official README.
mkdir -p .gcts-active/external-prover-reproduce
cp docs/research/gcts-rl-renewal/external_prover_control_plan.json .gcts-active/external-prover-reproduce/plan.json
PYTHONPYCACHEPREFIX=/private/tmp/gcts-native-wang-pycache python3 research/gcts-rl-renewal/external_prover_run.py --reader docs/research/gcts-rl-renewal/first-order-families-reader-001.json --e /private/tmp/gcts-e-reproduce/PROVER/eprover --output .gcts-active/external-prover-reproduce
PYTHONPYCACHEPREFIX=/private/tmp/gcts-native-wang-pycache python3 research/gcts-rl-renewal/external_prover_audit.py --output .gcts-active/external-prover-reproduce</pre></details><p class="small">The audit rechecks file and formula identities using the actual reproduction paths. Existing tests also use the training-case calibration outputs saved in the evidence bundle; restore those under <code>.gcts-active/external-prover-20261011</code> to run all test groups. A future runtime or E revision is a new experiment, not a replacement for these frozen observations.</p></section></main><footer>External first-order control · independently checked returned derivations · research program active</footer>
<script>document.getElementById('external-proof-control').addEventListener('change',async function(){for(const p of document.querySelectorAll('.proof-panel'))p.hidden=p.id!=='proof-'+this.value;if(window.MathJax?.typesetPromise)await MathJax.typesetPromise([document.getElementById('proof-'+this.value)]);});</script></body></html>'''
    costs='<ul><li>E binary execution across all runs: '+f'{s["external_search_seconds"]:.6f}'+' seconds.</li><li>Independent returned-proof checks: '+f'{s["verification_seconds"]:.6f}'+' seconds.</li><li>Input export and independent library checks: '+f'{s["input_and_library_seconds"]:.6f}'+' seconds.</li><li>Full orchestration including fresh measurement workers and serialization: '+f'{s["total_seconds"]:.6f}'+' seconds.</li><li>Peak E resident memory: '+f'{max(o["peak_rss_bytes"] for o in observations)/1048576:.3f}'+' MiB, measured through macOS per-child resource accounting.</li><li>Measured cold rebuild: '+f'{prep["wall_seconds"]:.3f}'+' seconds; peak '+f'{prep["peak_rss_bytes"]/1048576:.3f}'+' MiB.</li><li>Saved-trace replay and corruption audit: '+f'{a["seconds"]:.6f}'+' seconds.</li></ul><p class="small">Pinned source commit: <code>3b7afc70fe77d3118bb95144c4735ca45f5f31cf</code>. Binary-reported version: <code>'+esc(s['prover_version'])+'</code>. The embedded version commit differs from the checked-out source commit and is recorded verbatim. Binary SHA-256: <code>'+s['prover_binary_sha256']+'</code>. E’s own resource line labels its macOS resident count “pages”; the measured byte count above uses independent platform-aware resource accounting.</p>'
    page=page.replace('__ROWS__',''.join(rows)).replace('__OPTIONS__',''.join(options)).replace('__PANELS__',''.join(panels)).replace('__COSTS__',costs)
    PUBLIC.joinpath('external_prover_control.html').write_text(page)
    paths=[p for p in PUBLIC.glob('external_prover_*') if p.is_file()]+[p for p in (ROOT/'research/gcts-rl-renewal').glob('external_prover_*') if p.is_file()]
    manifest=dict(status='exported-awaiting-root-publication',files=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(paths)],
                  proposed_url='https://liuyao12.github.io/geometric-tree-search/docs/research/gcts-rl-renewal/external_prover_control.html?v=20261011-ep1#reader',
                  evidence_bundle_sha256=sha(gz),full_evidence_uncompressed_bytes=len(packed))
    (PRIVATE/'export.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
