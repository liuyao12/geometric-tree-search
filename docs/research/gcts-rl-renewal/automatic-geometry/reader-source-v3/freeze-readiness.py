"""Source/display-only final checks; never imports scientific data or engines."""
import difflib
import hashlib
import json
import subprocess
import time
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'.gcts-active/automatic-geometry-reader-source-v3-20261011';OLD=ROOT/'.gcts-active/automatic-geometry-reader-source-v2-20261011'
NODE='/Users/liuyao/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
def pin(p):return {'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def save(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,ensure_ascii=True);f.write('\n')
started=time.perf_counter()
syntax=subprocess.run([NODE,'--check',str(OUT/'viewer.js')],capture_output=True,text=True,timeout=10)
controls=subprocess.run([NODE,str(OUT/'reader-source-controls.js')],capture_output=True,text=True,timeout=10)
(OUT/'source-syntax-stderr.txt').write_text(syntax.stderr)
(OUT/'source-controls-stdout.txt').write_text(controls.stdout)
(OUT/'source-controls-stderr.txt').write_text(controls.stderr)
seconds=time.perf_counter()-started
if syntax.returncode or controls.returncode:raise RuntimeError('Source/display controls failed; streams preserved')
control=json.loads(controls.stdout)
save('source-controls.json',{'status':control['status'],'node_check_exit':syntax.returncode,'controls_exit':controls.returncode,'source_check_seconds':seconds,'controls':control,'scope':'Synthetic native-DOM-shaped controls only; no actual browser/MathJax/result/scientific verification.'})
(OUT/'viewer-v2-to-v3.diff').write_text(''.join(difflib.unified_diff((OLD/'viewer.js').read_text().splitlines(True),(OUT/'viewer.js').read_text().splitlines(True),fromfile='frozen-v2/viewer.js',tofile='new-v3/viewer.js')))
schema=json.loads((OLD/'source-schema-clarified.json').read_text());schema['schema']='automatic-geometry-browser-reader-source-v3'
schema['snapshot']['exterior_blue']={'condition':'Only x=1, row<0, value=-1 is an exterior boundary exclusion sentinel. It is an explicitly assigned literal mark, never a formula code. All other blue formula marks are nonnegative registered codes on nonnegative rows.','display':'Retain every saved exterior assignment and show its exact LaTeX point value and reference count, labelled Exterior boundary exclusion sentinel; never access formula_codes[-1] or translate it as formula English. Sentinels remain visible when formula/reference layers are toggled.','checks':'Reject exterior blue values zero, other negative values, and any interior blue sentinel.'}
schema['source_correction'] += ' V3 additionally handles the actual declared exterior negative-row blue sentinel -1; V2 rejected it as an invalid formula code. Frozen V2 is preserved. Author still loads no actual result or model.'
save('source-schema.json',schema)
preserved=[pin(OLD/name) for name in ['viewer.js','source-schema-clarified.json','readiness-receipt.json','integration.json']]
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['readiness-receipt.json','integration.json']]
save('readiness-receipt.json',{'schema':'automatic-geometry-reader-v3-source-readiness','status':'frozen_source_only_synthetic_controls_passed','files':files,'preserved_v2':preserved,'verification':{'bundled_node':NODE,'node_check_exit':syntax.returncode,'controls_exit':controls.returncode,'source_check_seconds':seconds,'controls':control},'minimal_change':'Two display branches distinguish literal exterior exclusion sentinels from registered formula codes, and reference counts now use explicit LaTeX. Exact diff supplied. All snapshot/certificate/policy/scientific conditions otherwise preserved.','authoring_cost':{'source_authoring_seconds':None,'reason':'Source authoring/debug elapsed/CPU not instrumented; earlier successful manual Node checks retained as source-only preparation, not scientific replay cost.'},'actual_data_or_browser_qa':'Unexecuted by author; root integrates original data, independence flags and actual MathJax/browser checks. Current root-reported null certificates leave actual certificate DOM unexercised.','science':{'actual_results_loaded':0,'models_loaded':0,'scientific_imports':0,'searches':0,'training':0,'native_queries':0,'scientific_replays':0},'immutable_after_readiness':True})
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='integration.json']
save('integration.json',{'schema':'task-only-reader-v3-frozen-manifest','scope':'Source/UI only; preserves every earlier reader file. Root owns actual-data integration/browser QA/publication.','entry':'viewer.js','source_schema':'source-schema.json','files':files})
print(json.dumps({'status':'frozen_source_only_v3_ready','viewer':pin(OUT/'viewer.js'),'schema':pin(OUT/'source-schema.json'),'receipt':pin(OUT/'readiness-receipt.json'),'manifest':pin(OUT/'integration.json'),'checks_seconds':seconds,'file_count':len(files)}))
