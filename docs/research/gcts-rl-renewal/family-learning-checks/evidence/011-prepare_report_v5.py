"""Package only this checkpoint's exact evidence and code-native HTML visual."""
import hashlib
import html
import json
from pathlib import Path
import shutil

ROOT=Path.cwd()
PRIVATE=ROOT/'.gcts-active/family-numeric-actual-progress-20261012'
PUBLIC=ROOT/'docs/research/gcts-rl-renewal/family-learning-checks'
NUMERIC=Path('.gcts-active/family-proposal-learning-numeric-source-20261012')

def pin(path):
    data=path.read_bytes()
    return {'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def save(path,data):
    with path.open('x') as stream:json.dump(data,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')

def main():
    PUBLIC.mkdir(parents=True,exist_ok=False)
    (PUBLIC/'evidence').mkdir()
    beginnings=[NUMERIC/'numeric-output-v2/result.json',NUMERIC/'owned-output-v1/owned-lifetime.json',
        Path('.gcts-active/family-numeric-actual-progress-20261012/outer-terminal-v1.json'),
        Path('.gcts-active/family-numeric-actual-progress-20261012/actual-numeric-disposition-v1.json'),
        Path('.gcts-active/family-numeric-actual-progress-20261012/source-review-v1.json'),
        Path('.gcts-active/family-numeric-source-review-20261012/source-review-v1.json'),
        NUMERIC/'owner-plan-v1.json',NUMERIC/'owner-activation-v1.json',
        Path('.gcts-active/family-numeric-actual-progress-20261012/review_and_activate.py'),
        Path('.gcts-active/family-numeric-actual-progress-20261012/run_owned_once.py'),
        Path('.gcts-active/family-numeric-actual-progress-20261012/inspect_actual_result.py'),
        Path(__file__).resolve().relative_to(ROOT)]
    queue=[pin(ROOT/p) for p in beginnings];seen={};external=[];bindings=[];excluded=[];historical=[]
    def collect(value):
        if isinstance(value,dict):
            if set(('path','sha256','bytes')).issubset(value):
                rec={k:value[k] for k in ('path','sha256','bytes')}
                if isinstance(rec['path'],str) and len(rec['sha256'])==64:queue.append(rec)
            for v in value.values():collect(v)
        elif isinstance(value,list):
            for v in value:collect(v)
    while queue:
        record=queue.pop(0);name=record['path']
        if name in seen:
            assert seen[name]['origin']==record,(name,'inconsistent exact pins')
            continue
        path=Path(name)
        if path.is_absolute():
            assert name.startswith('/Library/Developer/CommandLineTools/') or name=='/bin/ps',name
            data=path.read_bytes();assert hashlib.sha256(data).hexdigest()==record['sha256'] and len(data)==record['bytes']
            external.append(record);seen[name]={'origin':record,'public':None};continue
        assert not path.is_absolute() and '..' not in path.parts and (ROOT/path).resolve().is_relative_to(ROOT),name
        assert pin(ROOT/path)==record,(name,'mismatch')
        allowed=any(name.startswith('.gcts-active/'+prefix) for prefix in ('family-proposal-learning-','family-proposal-learning-numeric-source-','family-numeric-actual-progress-','family-numeric-source-review-')) or name in ('docs/basic-tiling-algorithm.md','AGENTS.md')
        if not allowed:
            routes=json.loads((ROOT/'docs/research/gcts-rl-renewal/fixed-family-search/source-input-bindings.json').read_text())
            matches=[x for x in routes if all(x.get(k)==v for k,v in record.items())]
            assert len(matches)<=1, ('Ambiguous historical route',name)
            route=matches[0] if matches else {'origin':record,'scope':'Related prospective research provenance; not a functional numeric fixture dependency; not newly published.'}
            historical.append(route);seen[name]={'origin':record,'public':None,'historical':route};continue
        if name.endswith('.bin'):
            excluded.append(record);seen[name]={'origin':record,'public':None};continue
        dest=PUBLIC/'evidence'/('%03d-%s'%(len(seen),path.name))
        shutil.copyfile(ROOT/path,dest)
        public=str(dest.relative_to(PUBLIC))
        seen[name]={'origin':record,'public':public,'published':pin(dest)}
        if path.suffix=='.json':
            content=json.loads(path.read_text());collect(content)
        bindings.append(seen[name])
    save(PUBLIC/'origins.json',{'status':'exact_task_owned_evidence_copies','files':bindings,'external_runtime_binaries_not_published':external,'excluded_private_streams':excluded,'existing_historical_prerequisite_routes':historical})
    r=json.loads((ROOT/beginnings[0]).read_text());outer=json.loads((ROOT/beginnings[2]).read_text())
    assert r['status']=='passed_numeric_and_abstract_API_controls_only'
    assert outer['status']=='passed_complete_numeric_fixture_lifecycle'
    link=lambda p:seen[str(p)]['public']
    cards=[]
    names={'epsilon0_temp05':'No exploration mixture','epsilon01_temp1':'Exploration mixture',
           'epsilon035_temp2':'Warmer exploration mixture','epsilon1_uniform':'Uniform exploration',
           'zero_weights':'Zero weights','duplicate_vectors':'Repeated feature vectors'}
    for control in r['controls']:
        if not control['id'].startswith('mixture_case:'):continue
        key=control['id'].split(':',1)[1];d=control['detail']['distribution']
        bars=''.join('<div class="prob-row"><span class="action">'+html.escape(a)+'</span><div class="bar-track"><div class="bar '+a.lower()+'" style="width:'+str(100*p)+'%"></div></div><span class="prob">\\('+format(p,'.5f')+'\\)</span></div>' for a,p in zip(d['action_ids'],d['probabilities']))
        cards.append('<article class="distribution"><h3>'+names[key]+'</h3><p>\\(\\varepsilon='+str(d['epsilon'])+',\\ T='+str(d['temperature'])+'\\)</p>'+bars+'</article>')
    rows=''.join('<tr><td><code>'+html.escape(c['id'])+'</code></td><td class="ok">Passed</td></tr>' for c in r['controls'])
    report=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Checking the learning policy · GCTS research</title><link rel="stylesheet" href="../report.css"><script>window.MathJax={tex:{inlineMath:[['\\(','\\)']],displayMath:[['\\[','\\]']]},options:{skipHtmlTags:['script','style','pre','code']}};</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>main{max-width:1200px}.passed{border-left:5px solid #32735e;padding:20px;background:#eef7f1}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.distribution,.track{padding:20px;background:#f5f6f0;border:1px solid #d4dccf;border-radius:6px}.distribution h3{font-size:18px;margin:0}.prob-row{display:grid;grid-template-columns:45px minmax(0,1fr) 65px;gap:8px;align-items:center;margin:12px 0}.bar-track{height:18px;background:#dfe5df;border-radius:3px;overflow:hidden}.bar{height:100%}.a{background:#4476ad}.b{background:#9170b3}.null{background:#669672}.prob{font-size:13px}.ok{color:#266443}code{overflow-wrap:anywhere}.equation{overflow:auto;padding:12px;background:#f5f6f0}.control-table{font-size:14px}details{margin:20px 0}@media(max-width:800px){.grid{grid-template-columns:1fr}.equation{font-size:14px}}</style></head><body><header class="masthead"><a href="../#family-learning-checks">Research report</a><span>NOTEBOOK 111</span><a href="#checks">Actual controls</a></header><main><section class="intro"><p class="eyebrow">ACTUAL NUMERIC GATE · PARALLEL SOURCE DEVELOPMENT</p><h1>Check the policy before asking it to search.</h1><p class="deck">The learning mathematics passes its bounded numerical controls. The changed-hypothesis compiler, independent checker, and restricted learning policy are being prepared in parallel.</p><p><a href="#probabilities">Saved probabilities</a> · <a href="#checks">Control records</a> · <a href="#parallel">Parallel work</a> · <a href="#evidence">Sources and evidence</a></p></section><section class="panel" id="result"><h2>A measured foundation for the next learning experiment.</h2><p class="passed">All \(26\) ordered controls passed. ROOT independently recomputed the saved \(6\) mixture distributions and \(36\) analytic gradient components. The complete numeric fixture lifecycle took \(@@SECONDS@@\) seconds.</p><p>The worker also compared \(36\) gradient components with finite differences and tested \(24\) supplied deterministic draws. It rejected a plain-softmax gradient where the exploration mixture requires a different derivative. Its clipping, baseline-update order, malformed-probability rejection, and Python compatibility checks passed.</p><p>This is a numeric fixture using artificial feature vectors, plus an abstract selection-overlay test double. It runs no production graph or Controller, generates no random draws, and performs no policy training or theorem search. The earlier <a href="../fixed-family-search/reader.html#reader">independently checked incidence proof and its actual colored tile rows</a> remain the latest proof-search result.</p></section><section class="panel" id="probabilities"><h2>Read the saved action probabilities.</h2><p>Blue and purple identify the artificial actions <code>A</code> and <code>B</code>; green identifies the explicit <code>NULL</code> action. These are numeric examples, not proof tiles or actual available clusters. Each card reports its saved temperature and exploration weight; several parameters differ between cards.</p><div class="grid">@@CARDS@@</div><div class="equation">\[q_i=\frac{\exp(w\cdot f_i/T)}{\sum_j\exp(w\cdot f_j/T)},\qquad p_i=(1-\varepsilon)q_i+\frac{\varepsilon}{N}.\]</div><p>The gradient belongs to the mixture probability. Its feature expectation is taken under the softmax distribution:</p><div class="equation">\[\nabla_w\log p_i=\frac{(1-\varepsilon)q_i}{p_iT}\left(f_i-\sum_jq_jf_j\right).\]</div><p>The update averages the saved score gradients over an executed episode, multiplies by the return minus the old baseline, clips that direction, changes the weights, then updates the baseline. This episode-averaged, clipped update is a heuristic; it is not claimed to be an unbiased expected-return gradient.</p></section><section class="panel" id="checks"><h2>Inspect every actual control.</h2><p>The saved result contains exactly the following ordered controls. The overlay control demonstrates the intended API contract on a test double: choosing <code>NULL</code> removes hint preference, complete fallback remains available, and the active view is restored with its checkpoint. Actual graph, hint retirement, distant markings and rollback still require their own engine gate.</p><details><summary>Show all \(26\) control records</summary><div class="table-scroll"><table class="control-table"><thead><tr><th>Saved control identity</th><th>Outcome</th></tr></thead><tbody>@@ROWS@@</tbody></table></div></details><p><a href="@@NUMERIC@@">Full actual numeric result</a> · <a href="@@DISPOSITION@@">Independent saved-result inspection</a> · <a href="@@REVIEW@@">Prior independent source review</a></p></section><section class="panel" id="parallel"><h2>Three agents, separate responsibilities.</h2><div class="grid"><article class="track"><h3>Context and search</h3><p>Rebuild the ordered hypothesis licenses and all placement identities for a changed receptor pattern. Prepare the complete primitive, fixed forward and whole-pool control lanes.</p></article><article class="track"><h3>Independent geometry checking</h3><p>Reconstruct the fresh primitive licenses, full source-body inventory, complete cluster census, point domains and eventual returned proofs independently.</p></article><article class="track"><h3>Learning policy</h3><p>Freeze generic receptor features and a donor/held-out-context protocol before examining the new search outcomes. Preserve an explicit NULL action and complete primitive fallback.</p></article></div><p>ROOT reviews and activates measured runs, owns their process handles, integrates checked evidence and publishes. Source authoring is concurrent; acceptance remains separate from proposal generation.</p><p>The prospective recipient changes the second hypothesis to an equality:</p><div class="equation">\[H(P,Q,l,m),\quad m=n,\quad\operatorname{Incident}(R,l)\quad\vdash\quad\operatorname{Incident}(R,n).\]</div><p>Here \(H\) is the explicit guarded conjunction stating that the distinct points \(P,Q\) lie on both stated lines. It is expanded into symbols in the source specification. The declared experiment retains all \(171\) existing conditional families, the \(24\)-row boundary and the global scheduler. Rebuilding the new licenses and independently checking the complete pool are prerequisites. There is no new transfer-search observation in this checkpoint.</p><p>The proposed learning control chooses among validated existing single or paired cluster proposals. It remains a restricted within-library context test; learning arbitrary new cluster topology and proving a general first-order encoding remain separate research tasks.</p></section><section class="panel" id="cost"><h2>Charge the complete fixture lifecycle.</h2><div class="table-scroll"><table><thead><tr><th>Measured quantity</th><th>Actual value</th></tr></thead><tbody><tr><td>Full outer lifecycle, including owner final serialization and reaping</td><td>\(@@SECONDS@@\) seconds</td></tr><tr><td>Conservative combined kernel peak</td><td>\(@@MEMORY@@\) bytes</td></tr><tr><td>Whole phase time gate</td><td>\(30\) seconds</td></tr><tr><td>Memory acceptance gate</td><td>\(536870912\) bytes</td></tr><tr><td>Production engine / training / theorem-search runs</td><td>\(0\,/\,0\,/\,0\)</td></tr></tbody></table></div><p>The owned worker and accounting children terminated and were reaped normally. The memory figure sums the outer and owner kernel peaks, plus the functional worker and maximum accounting-observer peak. It is a conservative retrospective gate, not a hard operating-system memory cap. Source authoring, metadata review, reporting, publication and earlier research costs are additional, not zero.</p></section><section class="panel" id="evidence"><h2>Reproduce or inspect the exact evidence.</h2><p><a href="@@PLAN@@">Frozen owner plan</a> · <a href="@@OWNER@@">Owned lifetime receipt</a> · <a href="@@OUTER@@">Full outer terminal receipt</a> · <a href="@@POLICY@@">Policy mathematics source</a> · <a href="origins.json">Exact published origins and runtime pins</a></p><p>Every published source and receipt is copied byte for byte, with its original path, SHA and byte count. Runtime binaries and raw process-table snapshots are excluded. This reader displays saved data and does not execute a scientific checker. The broad research goal remains active.</p></section></main></body></html>'''
    substitutions={'CARDS':''.join(cards),'ROWS':rows,'SECONDS':str(outer['full_seconds_including_owner_final_serialization_and_reaping']),
       'MEMORY':str(outer['conservative_combined_peak_bytes']),'NUMERIC':link(beginnings[0]),'DISPOSITION':link(beginnings[3]),
       'REVIEW':link(beginnings[5]),'PLAN':link(NUMERIC/'owner-plan-v1.json'),'OWNER':link(beginnings[1]),'OUTER':link(beginnings[2]),
       'POLICY':link(Path('.gcts-active/family-proposal-learning-20261012/family_policy_math_v2.py'))}
    for k,v in substitutions.items():report=report.replace('@@'+k+'@@',v)
    assert '@@' not in report
    (PUBLIC/'reader.html').write_text(report)
    paths=sorted(p for p in PUBLIC.rglob('*') if p.is_file())
    save(PRIVATE/'task-files.json',{'files':[pin(p) for p in paths],'total_files':len(paths),'total_bytes':sum(p.stat().st_size for p in paths),
        'main_index_update':'Counter110 to111 and additive family-learning-checks panel only; preserve all other bytes.'})
    print(json.dumps({'total_files':len(paths),'total_bytes':sum(p.stat().st_size for p in paths),'origins':len(bindings)}))

if __name__=='__main__':main()
