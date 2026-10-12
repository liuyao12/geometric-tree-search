"""Add the concurrent measured preparation and frozen RL source protocol."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path.cwd();OUT=ROOT/'.gcts-active/family-numeric-actual-progress-20261012';PUB=ROOT/'docs/research/gcts-rl-renewal/family-learning-checks'

def pin(p):
    d=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(d).hexdigest(),'bytes':len(d)}

def save(p,data):
    with p.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')

def main():
    transfer=ROOT/'.gcts-active/fixed-family-transfer-source-v1-20261012';rl=ROOT/'.gcts-active/family-proposal-rl-small-source-20261012'
    outcome=json.loads((transfer/'preparation-outcome-v1.json').read_text())
    terminal=ROOT/'.gcts-active/fixed-family-transfer-progress-20261012/preparation-terminal-v1.json'
    r=json.loads(terminal.read_text());assert r['status']=='passed_ROOT_complete_fresh_context_preparation'
    assert outcome['target_searches']==0 and outcome['complete_pool_group_count']==4
    paths=[]
    for folder in (transfer,rl):
        manifest=json.loads((folder/'integration-v1.json').read_text())
        for rec in manifest['files']:
            p=ROOT/rec['path'];assert pin(p)==rec;paths.append(p)
        paths.append(folder/'integration-v1.json')
    paths += [transfer/n for n in ('compiled-context-v1.json.gz','preparation-evidence-v1.json.gz','preparation-outcome-v1.json','preparation-lifetime-v1.json','preparation-supervision-v1.json','root-preparation-activation-v1.json')]
    paths += [terminal,ROOT/'.gcts-active/fixed-family-transfer-progress-20261012/preparation-source-review-v1.json',ROOT/'.gcts-active/fixed-family-transfer-independent-source-20261012/preparation-source-review-v1.json',Path(__file__).resolve()]
    routes=[];lookups={};target=PUB/'parallel-evidence';target.mkdir(exist_ok=False)
    for p in paths:
        q=target/(str(len(routes)).zfill(3)+'-'+p.name);shutil.copyfile(p,q)
        routes.append({'origin':pin(p),'public':str(q.relative_to(PUB)),'published':pin(q)});lookups[str(p)]=str(q.relative_to(PUB))
    save(PUB/'parallel-origins.json',{'status':'exact_new_preparation_and_frozen_policy_sources','files':routes,
        'scope':'One actually executed preparation; all RL scientific execution remains unexecuted. Earlier prerequisite bytes stay in their historical notebooks, not recopied here.'})
    source=PUB/'reader.html';s=source.read_text()
    panel=r'''<section class="panel" id="preparation"><h2>The new receptor pattern produces four proposed clusters.</h2><p>The changed-hypothesis compiler and preparation have now actually run. They retained the \(226\) non-assumption logical witnesses, rebuilt the \(3\) assumption licenses, reconstructed the \(24\)-row point model and retained all \(171\) conditional source bodies. The complete initial-domain census contains \(332510\) candidates. The declared grammar enumerates \(171\) single types and \(29241\) ordered pair types and produces \(4\) compatible whole proposals.</p><p>These are producer preparation observations. Independent reconstruction of the new licenses, complete domains and pool remains pending. The preparation executes no Controller, theorem search, training or native proof query. Its full dispatched lifecycle took \(5.907957208\) seconds; the inherited memory estimate is \(143933440\) bytes and omits simultaneous accounting-observer RSS. It is not a strict aggregate host upper bound.</p><p>The separate learning source now implements \(31\) graph/receptor features and a paired selection overlay with an explicit NULL choice and complete fallback. Its frozen protocol declares \(8\) donor episodes and \(8\) matched held-out evaluations. The changed mixed context is held out from training and tuning. This implementation is still source-only: an actual engine gate, driver and independent replay are required before execution.</p><p><a href="@@PREP@@">Actual preparation outcome</a> · <a href="@@TERMINAL@@">Full preparation lifecycle</a> · <a href="@@RL@@">Frozen prospective RL manifest</a> · <a href="parallel-origins.json">Exact new sources and origins</a></p></section>'''
    panel=panel.replace('@@PREP@@',lookups[str(transfer/'preparation-outcome-v1.json')]).replace('@@TERMINAL@@',lookups[str(terminal)]).replace('@@RL@@',lookups[str(rl/'integration-v1.json')])
    assert s.count('<section class="panel" id="cost">')==1
    source.write_text(s.replace('<section class="panel" id="cost">',panel+'<section class="panel" id="cost">'))
    main=ROOT/'docs/research/gcts-rl-renewal/index.html';parent=main.read_text();assert parent.count('RESEARCH NOTEBOOK · 110')==1 and 'id="family-learning-checks"' not in parent
    main_panel=r'''<section class="panel" id="family-learning-checks"><h2>Checkpoint 111 · Numerical learning controls and fresh receptor preparation</h2><p>All \(26\) numerical controls pass, with a complete \(0.24595837499999998\)-second fixture lifecycle. The changed-hypothesis preparation produces \(4\) whole cluster proposals after the complete declared grammar census; independent new-context validation remains pending. The parallel learning source freezes \(31\) features and donor/held-out-context controls before new transfer-search outcomes. <a href="family-learning-checks/reader.html?v=20261012-flc1#preparation">Inspect saved probabilities, actual preparation and the parallel sources</a>.</p><p>No new theorem search, real Controller learning run or RL advantage is claimed in this checkpoint. The checked proof in Checkpoint 110 remains available line by line.</p></section>
'''
    parent=parent.replace('RESEARCH NOTEBOOK · 110','RESEARCH NOTEBOOK · 111').replace('<section class="panel" id="fixed-family-search">',main_panel+'<section class="panel" id="fixed-family-search">',1)
    main.write_text(parent)
    files=sorted(p for p in PUB.rglob('*') if p.is_file())+[main]
    save(OUT/'task-files-v2.json',{'files':[pin(p) for p in files],'total_files':len(files),'total_bytes':sum(p.stat().st_size for p in files),
      'parent_index_change':'Exactly counter110→111 and one additive family-learning-checks panel; all other bytes preserved.',
      'prior_preliminary_manifest':pin(OUT/'task-files.json')})
    print(json.dumps({'total_files':len(files),'total_bytes':sum(p.stat().st_size for p in files),'new_source_origins':len(routes)}))

if __name__=='__main__':main()
