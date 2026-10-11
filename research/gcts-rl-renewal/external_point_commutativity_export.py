"""Standalone immutable exact-point solver reader; no shared index mutation."""
import gzip,hashlib,html,json,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'.gcts-active/external-point-commutativity-20261011';DOC=ROOT/'docs/research/gcts-rl-renewal'
def load(p):
    b=p.read_bytes();return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def packed(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def item(p):b=p.read_bytes();return dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def term(t):
    if t[0]=='var':return t[1]
    if t[1]=='zero':return '0'
    if t[1]=='succ':return 'S('+term(t[2][0])+')'
    if t[1]=='add':return '('+term(t[2][0])+'+'+term(t[2][1])+')'
    return r'\operatorname{'+t[1]+'}('+','.join(map(term,t[2]))+')'
def formula(f):
    if f[0]=='eq':return term(f[1])+'='+term(f[2])
    if f[0]=='all':return r'\forall '+f[1]+r'\;('+formula(f[2])+')'
    if f[0]=='imp':return '('+formula(f[1])+r'\Rightarrow '+formula(f[2])+')'
    if f[0]=='not':return r'\neg('+formula(f[1])+')'
    if f[0] in ['and','or']:return '('+('\\land ' if f[0]=='and' else '\\lor ').join(map(formula,f[1:]))+')'
    raise ValueError('unsupported displayed formula '+str(f[0]))
def english(line):
    c=line['command'];refs=line['source_rows'];r=c['rule']
    if r=='block':return 'Apply the already admitted lemma interface to '+('no premises' if not refs else 'the formulas on '+', '.join('row \\('+str(i+1)+'\\)' for i in refs))+'. Its exact definition and expansion are retained in the evidence.'
    if r=='generalize':return 'Universally quantify '+r'\('+c['variable']+r'\)'+' in the formula on row '+r'\('+str(refs[0]+1)+r'\)'+'.'
    return {'axiom':'Use the declared arithmetic axiom.','refl':'Every term equals itself.','induction':'Use this explicitly declared instance of natural-number induction.','tautology':'Use a propositional tautology.'}.get(r,'Use the exact primitive rule '+r+'.')
def main():
    began=time.perf_counter();plan=load(OUT/'plan.json');audit=load(OUT/'audit.json');production=load(OUT/'production.json');costs=load(OUT/'stage-costs.json');freeze=load(OUT/'encoding-freeze.json')
    need=audit['status']=='passed_complete_independent_encoding_and_available_SAT_checks'
    if not need:raise ValueError('export must disclose incomplete audit through separate unknown report')
    panels=[]
    for n in plan['lengths']:
        path=OUT/('result-'+str(n)+'.json.gz');r=load(path) if path.exists() else dict(solver_result='unknown_no_complete_result',solver_setup_seconds=0,solver_seconds=0)
        a=next(x for x in audit['models'] if x['length']==n);panel=dict(length=n,result=r['solver_result'],status=a['status'],solver_setup_seconds=r['solver_setup_seconds'],solver_seconds=r['solver_seconds'],census=a,rows=[])
        if (OUT/('checked-'+str(n)+'.json.gz')).exists():
            checked=load(OUT/('checked-'+str(n)+'.json.gz'))
            panel['rows']=[dict(x,latex=formula(x['formula']),english=english(x)) for x in checked['rows']]
        panels.append(panel)
    summary=dict(title='Commutativity: exact finite point-model solver control',panels=panels,audit=audit,plan=plan,costs=costs,production=production,encoding_freeze=freeze,
        authority='SAT assignments independently checked against every original point marking and decoded logical word. UNSAT is an unchecked solver assertion. No native Wang target query; no GCTS or RL discovery attribution.')
    filename='external_point_commutativity_control'
    summary_path=DOC/(filename+'.json');summary_path.write_bytes(packed(summary))
    page=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Exact point-model solver control</title>
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},chtml:{scale:1},options:{skipHtmlTags:['script','noscript','style','textarea','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
<style>body{font:17px/1.55 system-ui;margin:2rem auto;padding:0 1rem;max-width:1100px;color:#15283b;background:#f7fafc}h1{line-height:1.2}section{background:white;padding:1.2rem;margin:1rem 0;border:1px solid #d6e1e8;border-radius:12px}table{border-collapse:collapse;width:100%}td,th{padding:.5rem;border-bottom:1px solid #dee6ec;text-align:left}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.math{overflow-x:auto;max-width:100%;padding:.5rem 0}.row{border-top:1px solid #dbe4ed;padding:1rem 0}.tiles{display:flex;flex-wrap:wrap;gap:.5rem}.tile{width:72px;height:62px;border:3px solid #477cba;background:#e6f0fb;display:grid;place-content:center;font-size:12px;overflow:hidden}.tile.guard{border-color:#a358ba;background:#f5e8fa}.tile.input{border-color:#e0a239;background:#fff3d8}.warn{border-left:5px solid #ce9140;padding:1rem;background:#fff5df}a{color:#165f9e}button,select{font:inherit;padding:.4rem}summary{cursor:pointer}.badge{font-weight:600}code{font-size:14px;overflow-wrap:anywhere}</style></head><body>
<h1>Commutativity: solver control on the exact finite point model</h1><p>Original target: \(\forall x\,\forall y\;(x+y=y+x)\). The solver receives every placement in the same finite scalar marking model, with \(12\) and \(13\) proof rows, the original \(153\) inference interfaces and all \(94\) natively admitted definitions.</p>
<p class="warn">A SAT assignment is checked against all original occupancy and distant marking constraints and its decoded logical word. An UNSAT answer remains a solver assertion with an unchecked refutation string. It does not establish finite exhaustion or mathematical nonprovability. There is no native Wang target acceptance claim and no RL attribution.</p>
<section id="comparison"><h2>Actual outcomes and costs</h2><div id="costs"></div><p>Z3 solves a Boolean constraint language. GCTS uses its reference point scheduler and placement ordering. The region and legal placement set agree, while algorithms, caps and machine conditions differ. No speed ratio is inferred. This control never reads the ordinary target proof word or uses a solution seed.</p><p>Previous \(12\)-row GCTS runs remain search-budget unknowns. The independent \(13\)-row GCTS track is linked separately when published; a solver result is not attributed to that track.</p></section>
<section id="encoding"><h2>Exact reduction and cross-track binding</h2><p>One Boolean selects each complete placement. Every required point has exactly one selected incident placement, each contributing capacity \(12\). Every selected placement implies each of its assigned marking values; different values at one marking point are mutually exclusive. Mark-only points participate even outside the occupied roots. Missing marks remain unconstrained, and assigned zero remains a value.</p><p>Sequential auxiliary variables encode at-most-one constraints. Any legal point selection extends to a satisfying valuation by setting the appropriate marking variables and prefix variables. Conversely, a satisfying valuation forces exact occupancy and agreement of all selected markings, including the initial target. This is an authored reduction argument, independently checked on the full data and exhaustive tiny fixtures.</p><div id="hashes"></div><details><summary>Frozen encoding and audit plan</summary><pre id="plan"></pre></details></section>
<section id="reader"><h2>Returned rows</h2><label>Boundary <select id="selector"></select></label><div id="proof"></div><p>Blue command, purple guard and amber input tiles are the actual four selected point placements per row. Their distant supports are retained in the exact JSON. These are scalar point tiles with fixed orientations, rather than a primitive Wang occupancy compilation.</p></section>
<section id="evidence"><h2>Evidence and reproducibility</h2><p><a href="external_point_commutativity_control_evidence.zip">Complete sources, inputs, constraints, solver outputs and checked words</a> · <a href="external_point_commutativity_control.json">Reader data and exact pins</a> · <a href="external_point_commutativity_control_audit.json">Independent audit</a> · <a href="commutativity_cluster_results.html#reader">Prior GCTS and ordinary-control report</a></p><p>Runtime, source and input bytes are pinned. The producer has a cumulative \(180\)-second gate including preparation and serialization; the independent audit has a separate \(180\)-second gate, each with a measured \(512\,\mathrm{MiB}\) peak admission limit. Native soft OS memory limits are not relied upon. Process receipts include startup, final serialization, timeout cleanup and reaping. Human development and waiting are outside the measured gates.</p><p>Z3's Boolean interface and solver behavior are described in the <a href="https://microsoft.github.io/z3guide/docs/logic/propositional-logic/">official propositional logic guide</a> and <a href="https://microsoft.github.io/z3guide/programming/Z3%20Python/Introduction/">Python guide</a>. A produced proof object needs its own checker; see the <a href="https://microsoft.github.io/z3guide/programming/Proof%20Logs/">official proof log documentation</a>.</p></section>
<script>
fetch('external_point_commutativity_control.json').then(r=>r.json()).then(async d=>{
 const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const math=s=>'\\('+s+'\\)';
 document.querySelector('#costs').innerHTML='<table><tr><th>Rows</th><th>Solver</th><th>Setup / solve seconds</th><th>Independent result</th></tr>'+d.panels.map(p=>'<tr><td>'+math(p.length)+'</td><td>'+esc(p.result)+'</td><td>'+math(p.solver_setup_seconds.toFixed(3))+' / '+math(p.solver_seconds.toFixed(3))+'</td><td>'+esc(p.status.replaceAll('_',' '))+'</td></tr>').join('')+'</table><p>Cumulative producer process: '+math(d.costs.producer_seconds.toFixed(3))+ ' seconds; independent audit process: '+math(d.costs.audit_seconds.toFixed(3))+ ' seconds. Source/runtime freeze: '+math(d.plan.freeze_seconds_before_final_plan_write.toFixed(3))+' seconds. Producer peak: '+math((d.production.peak_rss_bytes/1048576).toFixed(2))+' MiB; audit peak: '+math((d.audit.peak_rss_bytes/1048576).toFixed(2))+' MiB.</p><details><summary>All process and preparation receipts</summary><pre>'+esc(JSON.stringify({costs:d.costs,encoding:d.encoding_freeze,production:d.production},null,2))+'</pre></details>';
 document.querySelector('#hashes').innerHTML=d.encoding_freeze.models.map(x=>'<p>'+math(x.length)+' rows: '+math(x.placements)+' candidates, '+math(x.roots)+' required points, '+math(x.variables)+' Boolean variables and '+math(x.clauses)+' clauses. Complete semantic hash: <code>'+esc(x.semantic_sha256)+'</code></p>').join('');
 document.querySelector('#plan').textContent=JSON.stringify(d.plan,null,2);
 const sel=document.querySelector('#selector');d.panels.forEach((p,i)=>sel.add(new Option(p.length+' rows: '+p.result,i)));
 async function show(){const p=d.panels[Number(sel.value)];document.querySelector('#proof').innerHTML=p.rows.length?p.rows.map(x=>'<div class="row"><p class="badge">Row '+math(x.row+1)+'</p><div class="tiles">'+x.placements.map((k,i)=>'<div class="tile '+(i===1?'guard':i>1?'input':'')+'"><span>'+['command','guard','input 1','input 2'][i]+'</span><code>'+esc(JSON.stringify(k))+'</code></div>').join('')+'</div><div class="math">'+math(x.latex)+'</div><p>'+esc(x.english)+'</p><details><summary>Exact formula and row command</summary><pre>'+esc(JSON.stringify({formula:x.formula,command:x.command,source_rows:x.source_rows},null,2))+'</pre></details></div>').join(''):'<p>'+esc(p.status.replaceAll('_',' '))+'. No returned satisfying placement word is displayed.</p>';await MathJax.startup.promise;await MathJax.typesetPromise();}
 sel.addEventListener('change',show);await show();});</script></body></html>'''
    html_path=DOC/(filename+'.html');html_path.write_text(page)
    audit_path=DOC/(filename+'_audit.json');audit_path.write_bytes((OUT/'audit.json').read_bytes())
    evidence=DOC/(filename+'_evidence.zip')
    with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(OUT/'frozen-inputs.zip','frozen-inputs.zip')
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p.name not in ['frozen-inputs.zip','integration.json']:z.write(p,'private/'+p.name)
    exports=[html_path,summary_path,audit_path,evidence]+[Path(__file__).with_name('external_point_commutativity_'+s+'.py') for s in ['produce','audit','runner','export']]
    manifest=dict(status='frozen_independently_audited_exact_point_control',reader='external_point_commutativity_control.html?v=20261011-epc1#reader',files={str(p.relative_to(ROOT)):item(p) for p in exports},source_input_archive=str(evidence.relative_to(ROOT)),private_data=list(sorted(p.name for p in OUT.iterdir() if p.is_file())),export_seconds_before_manifest=time.perf_counter()-began,
        audit_status=audit['status'],source_pins=plan['sources'],input_pins=plan['inputs'],runtime_pins=plan['runtime'])
    (OUT/'integration.json').write_bytes(packed(manifest));print(json.dumps(dict(integration=item(OUT/'integration.json'),files=len(exports),reader=manifest['reader'])))
if __name__=='__main__':main()
