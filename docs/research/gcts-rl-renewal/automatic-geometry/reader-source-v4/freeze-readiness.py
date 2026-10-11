"""Final native display-source checks and immutable freeze; no science/data imports."""
import difflib
import hashlib
import json
import subprocess
import time
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'.gcts-active/automatic-geometry-reader-source-v4-20261011';OLD=ROOT/'.gcts-active/automatic-geometry-reader-source-v3-20261011'
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
if syntax.returncode or controls.returncode:raise RuntimeError('Final display source check failed; streams preserved')
control=json.loads(controls.stdout)
save('source-controls.json',{'status':control['status'],'node_check_exit':syntax.returncode,'controls_exit':controls.returncode,'source_check_seconds':seconds,'controls':control,'scope':'Synthetic native-DOM-shaped checks only, no original actual data/MathJax/browser/scientific verification.'})
(OUT/'viewer-v3-to-v4.diff').write_text(''.join(difflib.unified_diff((OLD/'viewer.js').read_text().splitlines(True),(OUT/'viewer.js').read_text().splitlines(True),fromfile='frozen-v3/viewer.js',tofile='new-v4/viewer.js')))
schema=json.loads((OLD/'source-schema.json').read_text());schema['schema']='automatic-geometry-browser-reader-source-v4'
schema['english_notation']={'variable_and_binder':'Inline LaTeX mathit with existing escapeTex inside returned English strings.','function_and_predicate_names':'Inline LaTeX operatorname with existing escapeTex inside returned English strings.','rule_names':'Axiom, recipe and unknown rule names use escaped inline text; generalization variable uses escaped inline mathit. UI row numbers and selector/recipe metadata labels remain metadata.','dom':'All English is assigned by textContent, then included in existing full proof/trace MathJax typeset target. No innerHTML or new scientific interpretation.','checks':'Nine source-synthetic English controls cover variables, constants, functions, predicates, binders, escaped backslash/braces/underscore/dollar names, axiom/recipe/rule IDs and generalization variable.'}
schema['math_renderer'] += ' V4 also supplies inline LaTeX for mathematical identifiers in English explanations; the same existing DOM typesetting path handles these textContent strings.'
save('source-schema.json',schema)
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name not in ['readiness-receipt.json','integration.json']]
save('readiness-receipt.json',{'schema':'automatic-geometry-reader-v4-source-readiness','status':'frozen_source_only_synthetic_controls_passed','files':files,'preserved_v3':[pin(OLD/name) for name in ['viewer.js','source-schema.json','readiness-receipt.json','integration.json']], 'verification':{'bundled_node':NODE,'node_check_exit':syntax.returncode,'controls_exit':controls.returncode,'source_check_seconds':seconds,'controls':control},'minimal_change':'English identifier notation only: escaped inline LaTeX added through one helper; exact inference, snapshot, certificate, key, mark, sentinel, metadata and selection semantics otherwise unchanged. Exact source diff supplied.', 'authoring_cost':{'source_authoring_seconds':None,'reason':'Not instrumented; source-only local escaping syntax failure was corrected before final source checks. Earlier successful manual checks are preparation only, not scientific replay cost.'},'actual_data_or_browser_qa':'Author did not load actual results/models or execute a browser/MathJax check. Root owns actual-data integration, acceptance flags and end-to-end live QA; actual certificate DOM remains unexercised.','science':{'actual_results_loaded':0,'models_loaded':0,'scientific_imports':0,'searches':0,'training':0,'native_queries':0,'scientific_replays':0},'immutable_after_readiness':True})
files=[pin(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='integration.json']
save('integration.json',{'schema':'task-only-reader-v4-frozen-manifest','scope':'Native display-source only. Earlier v1/v2/v3 unchanged. Root owns actual-data integration/browser QA/publication.','entry':'viewer.js','source_schema':'source-schema.json','files':files})
print(json.dumps({'status':'frozen_source_only_v4_ready','viewer':pin(OUT/'viewer.js'),'schema':pin(OUT/'source-schema.json'),'receipt':pin(OUT/'readiness-receipt.json'),'manifest':pin(OUT/'integration.json'),'checks_seconds':seconds,'file_count':len(files)}))
