"""Display immutable actual evidence only; never execute a research engine."""
import copy
import gzip
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from report_evidence import ROOT, PUB, PREFIX, DEST, pin, load, project

HERE=Path(__file__).resolve().parent
BASE='a4adb7b113338e6b8753b880356954b6a26d2086'
MAIN='docs/research/gcts-rl-renewal/index.html'


def math(value):
    return r'\('+html.escape(str(value))+r'\)'


def prose(value):
    return re.sub(r'(?<![\w])([0-9][0-9,]*(?:\.[0-9]+)?)(?![\w])',lambda m:math(m.group(1).replace(',','')),html.escape(value))


def table(headers,rows):
    return '<div class="table-scroll"><table><thead><tr>'+''.join('<th>'+html.escape(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def main():
    selected=load(HERE/'terminal-selection.json')
    assert selected['all_owned_handles_terminal'] is True
    phase=ROOT/selected['producer_folder']
    outcome=load(phase/'search-outcome-v1.json');life=load(phase/'search-lifetime-v1.json')
    assert life['status']=='passed_automatic_primitive_geometry_full_lifetime'
    plan=load(phase/'search-plan-v1.json');acceptance=load(ROOT/selected['independent_result'])
    assert acceptance['status']==selected['independent_result_status']
    assert acceptance['observation_verdicts']==selected['observation_verdicts'],'independent acceptance flags must come from exact actual audit'
    baseline=subprocess.check_output(['git','show',BASE+':'+MAIN],cwd=PUB)
    assert hashlib.sha256(baseline).hexdigest()==selected['main_baseline_sha256']
    assert (HERE/'baseline-index.html').read_bytes()==baseline
    historical={(MAIN,selected['main_baseline_sha256']):HERE/'baseline-index.html'}
    # Scientific history binds older report versions. Preserve each exact byte
    # version separately; a later report cannot overwrite its historical hash.
    priorbase='f41da478a4a16b4c91eabe20aa8255ebdfc30830'
    priorbytes=subprocess.check_output(['git','show',priorbase+':'+MAIN],cwd=PUB)
    historicalfile=HERE/'historical-index-105.html'
    if historicalfile.exists():assert historicalfile.read_bytes()==priorbytes
    else:historicalfile.write_bytes(priorbytes)
    historical[(MAIN,hashlib.sha256(priorbytes).hexdigest())]=historicalfile
    draft=ROOT/'.gcts-active/receptor-matching-geometry-independent-20261011/positive_certificate_oracle_draft_7ed3f345.py'
    historical[('.gcts-active/receptor-matching-geometry-independent-20261011/positive_certificate_oracle_v1.py','7ed3f345f8938bdf465d72033f52972314db5e303f93066fdb20840d4f3f67c7')]=draft
    exclusions={'publication.json','publication-staging.json','task-files.json','turn-result.json','local-validation.json','live-hash-checks.json','browser-validation.json','staged-whitespace-check.json','verify_live_files.py','baseline-index.html','historical-index-105.html','stage_publication.py','root_final_review.json'}
    folders=selected['frozen_folders']+[(str(HERE.relative_to(ROOT)),'coordinator',exclusions)]
    files,origins,bindings=project(folders,historical)
    def save(name,value):
        opts={'separators':(',',':')} if name=='visual-data.json' else {'indent':2}
        p=DEST/name;p.write_text(json.dumps(value,allow_nan=False,**opts)+'\n');files.add(str(p.relative_to(ROOT)))
    def link(origin,label):
        row=next((e for e in origins if e['origin']==origin),None)
        if row:target=row['path']
        else:
            row=next(e for e in bindings if e['path']==origin)
            assert row.get('archive_member') is None
            target=row['published_path']
        return '<a href="'+html.escape(os.path.relpath(target,PREFIX))+'">'+html.escape(label)+'</a>'
    modelpin=next(e for e in plan['inputs'] if e['role']=='primitive_model')
    with gzip.open(ROOT/modelpin['path'],'rt') as s:model=json.load(s)
    contexts=[entry['context'] for entry in model['models'] if entry['height']==24];assert len(contexts)==1
    observations=[]
    for source in outcome['observations']:
        assert pin(ROOT/source['result']['path'])=={k:source['result'][k] for k in ('sha256','bytes')}
        with gzip.open(ROOT/source['result']['path'],'rt') as s:result=json.load(s)
        verdict=selected['observation_verdicts'][source['id']]
        value=copy.deepcopy(result)
        value.update(id=source['id'],independent_certificate_accepted=verdict['certificate_accepted'],independent_trace_accepted=verdict['trace_accepted'],independent_scope=verdict['scope'])
        observations.append(value)
    visual=dict(scope='Actual selected constraints, search traces and any independently checked certificates. Trace correctness, symbolic proof validity and native acceptance are distinct.',formula_codes=model['formula_codes'],recipes=[{k:r[k] for k in ('id','primitive_witness','ordered_premise_formulas')} for r in model['recipes']],hypotheses=contexts[0]['ordered_local_premises'],target=model['formula_codes'][54],observations=observations,producer_result=dict(path=str((phase/'search-outcome-v1.json').relative_to(ROOT)),**pin(phase/'search-outcome-v1.json')))
    save('visual-data.json',visual)
    viewer=ROOT/selected['viewer_source'];target=DEST/'viewer.js';shutil.copyfile(viewer,target);files.add(str(target.relative_to(ROOT)))
    origins.append(dict(origin=str(viewer.relative_to(ROOT)),path=str(target.relative_to(ROOT)),**pin(viewer)))
    bindings.append(dict(path=str(viewer.relative_to(ROOT)),**pin(viewer),published_path=str(target.relative_to(ROOT)),archive_member=None))
    save('origins.json',origins);save('source-input-bindings.json',bindings)
    passed=[o['id'] for o in observations if o['independent_certificate_accepted']]
    results=table(['Control','Actual outcome','Attempts','Forced moves','Search seconds','Ground proof','Trace audit'],[[html.escape(o['id']),html.escape(o['status']),math(o['attempts']),math(o['graph_metrics']['forced']),math(round(o['seconds'],6)),'Accepted' if o['independent_certificate_accepted'] else 'No accepted proof','Passed' if o['independent_trace_accepted'] else html.escape(o['independent_scope'])] for o in observations])
    purelife=load(phase/'pure-ast-lifetime-v1.json');auditlife=load(ROOT/selected['independent_lifetime'])
    purecost=Decimal(str(purelife['full_child_and_owner_seconds_before_final_receipt_write']))
    producercost=Decimal(str(life['full_supervisor_process_seconds_including_receipt_write']))
    auditcost=Decimal(str(selected['independent_owned_seconds']))
    metadata_life=load(ROOT/selected['metadata_lifetime']);failed_audit_life=load(ROOT/selected['failed_audit_lifetime'])
    metadatacost=Decimal(str(metadata_life['full_child_and_owner_seconds_before_final_receipt_write']))
    failedcost=Decimal(str(failed_audit_life['full_owner_and_worker_seconds_before_receipt_write']))
    assert selected['independent_owned_seconds']==auditlife['full_owner_and_worker_seconds_before_receipt_write']
    assert selected['independent_peak_bytes']==auditlife['conservative_combined_peak_bytes']
    ownedtotal=purecost+producercost+auditcost+metadatacost+failedcost
    costs=table(['New owned phase','Seconds','Conservative peak bytes','Scope'],[
        ['Pure AST controls',math(purecost),math(purelife['conservative_host_peak_bytes']),'No actual model or search'],
        ['Two-control producer',math(producercost),math(life['conservative_host_peak_bytes']),'Cold preparation, matching, search, decoding, serialization and reap'],
        ['Preserved audit launch failure',math(failedcost),math(failed_audit_life['conservative_combined_peak_bytes']),'Wrong activation filename; no child or actual audit created'],
        ['Independent actual audit',math(auditcost),math(selected['independent_peak_bytes']),html.escape(selected['independent_gate_scope'])],
        ['Recorded-trace diagnosis',math(metadatacost),math(metadata_life['conservative_host_peak_bytes']),'Metadata only; no model, matcher, checker or replay'],
        ['Additional owned total',math(ownedtotal),'Peaks are not added','Source preparation, reference controls, other metadata, review and publication are additional']])
    metrics=table(['Control','Ordering calls','Complete keys ranked','Score feature seconds','Sort seconds'],[[html.escape(o['id']),math(o['fixed_forward_metrics']['calls']),math(o['fixed_forward_metrics']['complete_keys_ranked']),math(round(o['fixed_forward_metrics']['feature_seconds'],6)),math(round(o['fixed_forward_metrics']['sort_seconds'],6))] for o in observations])
    matchmetrics=next(o['fixed_forward_metrics'] for o in observations if o['mode']=='fixed-forward-receptor')
    matching=table(['Receptor subphase','Measured seconds'],[[label,math(round(matchmetrics[key],6))] for label,key in [('Pattern preparation','pattern_preparation_seconds'),('Selected-constraint collection','selected_constraint_collection_seconds'),('Literal matching','literal_matching_seconds'),('Comparison and score payload hashing','feature_payload_hash_seconds')]])
    bridge=load(ROOT/'.gcts-active/shared-symbolic-native-bridge-20261011/bridge-design-v1.json')
    config={'tex':{'inlineMath':[[r'\(',r'\)']],'displayMath':[[r'\[',r'\]']]},'options':{'skipHtmlTags':['script','style','pre','code']}}
    verdict='<p class="note">'+prose(selected['assessment'])+'</p>'
    if passed:
        proofscope='A supplied complete ground certificate has passed the independent symbolic and point checks indicated above. Its assumptions remain the original three hypotheses and guarded incidence axiom. Flat shared-checker request correspondence and native acceptance have their separately stated scope; no hypothesis discharge or universal closure is inferred.'
    else:
        proofscope='No accepted proof or shared native request was produced. The point constraints and partial occupied rows displayed below are search states, not established derivations. Unknown does not imply that the statement is unprovable or that the finite region is impossible.'
    diagnosis='<section class="panel" id="next"><h2>The recorded bottleneck and next hypothesis.</h2><p>'+prose(selected['diagnosis_summary'])+'</p><p>These are recorded structural constraints and choices, not an accepted partial theorem. The next source-bound options test availability across both ordered ports or whole composed family interfaces. Neither option has been implemented or run, and no larger budget or target-proof sequence was supplied.</p><p>'+link(selected['diagnosis_result'],'Recorded-trace metadata')+' · '+link(selected['next_options'],'Findings and prospective options')+'</p></section>'
    content='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Literal receptor matching · GCTS research</title><link rel="stylesheet" href="../report.css"><script>window.MathJax='''+json.dumps(config)+''';</script><script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script><style>
main{max-width:1240px}.note{padding:18px;border-left:4px solid #a57334;background:#fff4e3}.controls{display:flex;flex-wrap:wrap;gap:16px;margin:18px 0}select{max-width:100%;font:inherit;padding:8px}#reader .gcts-math{display:inline-block;max-width:100%;overflow:auto;vertical-align:middle}#reader .gcts-proof-row>div:last-child{min-width:0;overflow:auto}td{font-size:14px}pre{overflow:auto;max-height:420px}.sequence{display:flex;flex-wrap:wrap;gap:12px;margin:22px 0}.sequence>div{flex:1;min-width:180px;padding:16px;border:2px solid #6d7c6b;background:#fff;border-radius:6px}.sequence .formula-advice{border-color:#4e82c1;background:#edf4ff}.sequence .references{border-color:#7954aa;background:#f3edff}.sequence p{font-size:15px}.sequence small{font-size:12px}h2{scroll-margin-top:20px}
</style></head><body><header class="masthead"><a href="../#receptor-matching">Research report</a><span>NOTEBOOK 107</span><a href="#assessment">Assessment</a></header><main><section class="intro"><p class="eyebrow">GENERIC STRUCTURAL ADVICE · COMPLETE LEGAL FALLBACK</p><h1>Match a receptor before choosing a tile.</h1><p class="deck">Two automatic controls search the same symbolic geometry problem. The new control ranks literal guard matches after the existing readiness tier.</p><p><a href="#results">Actual outcomes</a> · <a href="#method">The matching feature</a> · <a href="#reader">Tile rows and formulas</a> · <a href="#cost">Full costs</a></p></section><section class="panel" id="problem"><h2>The same guarded incidence statement.</h2><div class="formula">'''+math(bridge['problem_latex'])+'''</div><div class="formula">'''+math(bridge['guard_latex'])+'''</div><p>The supplied hypotheses connect two pairs of lines through distinct points and put the indicated point on the first line. Guarded uniqueness identifies the lines; the goal puts the point on the last line. Incidence, points and lines are symbolic predicates and constants. No drawn geometry, distances or angles enter the search.</p><p>'''+html.escape(proofscope)+'''</p></section><section class="panel" id="results"><h2>Actual bounded searches.</h2>'''+results+verdict+'''<p>The controls retain '''+math(229)+' recipes, '+math(217)+' formula values, '+math(24)+' required rows and all '+math(171)+''' checked source bodies. The active descriptor list is empty and no authored target-proof sequence is supplied. The finite grammar was prepared for this ground problem; it is not the full request-independent Wang palette.</p><p>Each control receives '''+math(128)+' attempts, a '+math(20)+'-second checked deadline and '+math(2000)+''' trace events. Deadline overshoot in an in-flight operation remains charged in actual time and cannot justify a strict equal-wall-time comparison. The reference repeats the previous fixed forward order on a fresh model.</p></section><section class="panel" id="method"><h2>What the receptor feature does.</h2><div class="sequence" role="img" aria-label="Global constraint checks precede readiness, literal receptor advice and the complete original fallback"><div><strong>Global point graph</strong><p>Dead ends, forced moves, then earliest generation.</p></div><div class="references"><strong>Existing readiness</strong><p>The declared source ports and selected output constraints retain their original priority.</p></div><div class="formula-advice"><strong>Literal receptor advice</strong><p>Match, neutral, then nonmatch within the same readiness tier.</p></div><div><strong>Complete fallback</strong><p>Original size and canonical ties; every legal candidate remains.</p></div></div><p>An instantiation recipe contributes the immediate implication guard after its remaining leading universal prefix. Only distinctly named prefix variables are slots; completed constants stay rigid. Literal compound constructors recurse, but slot images in this first version must be closed nullary function terms. An MP recipe uses its exact first ordered premise as a rigid guard and checks the literal implication in its second premise.</p><p>Only outputs of physically selected squares are recipients. Some selected outputs still have pending earlier sources. A match is structural advice, not a derived statement, a new premise or a reason to remove a candidate. An assigned mark at an empty row is not a selected recipient. Duplicate formulas on different selected rows keep their distinct identities.</p><p>Repeated slots must agree. Constructor, predicate, arity, polarity and argument order are literal. Quantified or free recipients, nested quantified guards, repeated prefix binders, unsupported connectives and compound slot images are neutral within the stated subset. A definite mismatch elsewhere in an otherwise supported pair takes precedence over an unsupported slot image. No equality symmetry, conjunction rearrangement, theorem-name lookup or logical oracle is used.</p>'''+metrics+matching+'''<p>Full selected identities, pattern records, successful bindings, comparison labels and complete score/order hashes are saved in the raw results. The independent audit reconstructs them independently; source checks and synthetic examples alone cannot establish their behavior on the actual graph.</p></section><section class="panel" id="reader"><h2>Read the actual squares, formulas and English.</h2><p>Blue markings carry formula values; purple markings carry ordered offsets to earlier source rows. Tiles translate without rotation. The selected search trace shows the occupied squares and their exact output constraints. Pending source receptors remain visibly distinguished. A complete accepted certificate, if present, is a separate row-by-row view.</p><div class="controls"><label>Observation <select id="observation"></select></label><label>Trace event <select id="trace-event"></select></label></div><p><label><input id="formula-layer" type="checkbox" checked> Blue formula layer</label> <label><input id="reference-layer" type="checkbox" checked> Purple ordered-reference layer</label></p><div id="proof-view" aria-live="polite"></div><div id="trace-view" aria-live="polite"></div></section><section class="panel" id="cost"><h2>Preparation and checking count too.</h2>'''+costs+'''<p>The producer keeps its '''+math(180)+'-second outer, '+math(175)+'-second supervisor, '+math(170)+'-second child alarm and '+math(512)+''' MiB conservative peak gates. Sampling and kernel peak checks are distinct from a hard operating-system memory cap. The first audit launch stopped before child creation because ROOT used the wrong activation filename. Its exact failure remains saved; the corrected isolated successor uses the same tapes and gates. A source-only checkpoint-variable defect was also caught before any audit ran. Independent audit uses its own declared owner. Component timers overlap: matching, ordering, tracing and rollback clocks must not be added as disjoint costs.</p><p>The previous failed adapter, previous two-control producer and previous independent audit add '''+math('50.405773542')+''' seconds under their separate owners; historical inventory/native preparation and prior unknown runs remain additional. Current source freezing, cross-domain reference controls, metadata, reviews, report generation and publication are also additional. Source-authoring CPU time is unmeasured. The original accepted body-authority plan retains '''+math(56)+''' unique inputs; all previous wider phase prerequisites remain checked.</p></section><section class="panel" id="assessment"><h2>Contribution and limits.</h2>'''+verdict+'''<p>GCTS contributes exact occupancy, distant marking compatibility, complete candidate bookkeeping, forced propagation and rollback in this finite scalar-point adaptation. The new feature is authored deterministic ordering. It neither trains RL nor learns failure markings. Proof validity is checked independently of the ranking.</p><p>One bounded observation per control does not establish statistical superiority, general arithmetic transfer, unrestricted first-order completeness or a native Wang-machine proof. Practical comparison still needs held-out theorem families, matched budgets and full preparation/checking costs.</p><p>The parallel cross-domain work checks '''+math(41)+' literal AST cases and '+math(10)+''' availability/completion examples using an independent synthetic reference. The producer matcher separately passes '''+math(64)+''' pure controls. Arithmetic requires agreement among its command, guard and ordered input roles; its current searched grammar lacks primitive instantiation actions. These examples do not activate arithmetic quantifier guidance or discover arithmetic proofs.</p><p>Receptor-adapted reusable clusters remain the next hierarchy step: runtime interface matching across the whole checked family registry, checked constituent expansion, complete primitive fallback and exact retirement/rollback. This experiment has no active cluster proposal. The full research program remains active, including learning, multiscale and movable-boundary tiling, turtle and Penrose.</p></section>'''+diagnosis+'''<section class="panel" id="evidence"><h2>Inspect the exact evidence.</h2><p>'''+link(str((phase/'search-outcome-v1.json').relative_to(ROOT)),'Actual producer outcome')+' · '+link(str((phase/'search-lifetime-v1.json').relative_to(ROOT)),'Producer lifetime')+' · '+link(selected['independent_result'],'Independent actual audit')+' · '+link(selected['independent_lifetime'],'Independent owned lifetime')+'''</p><p>'''+link(str((phase/'matcher-contract-v1.json').relative_to(ROOT)),'Matcher contract')+' · '+link('.gcts-active/receptor-matching-cross-domain-source-20261011/compatibility-assessment-v1.json','Arithmetic transfer assessment')+'''</p><p><a href="visual-data.json">Viewer projection</a> · <a href="result-summary.json">Result summary</a> · <a href="origins.json">Exported origins</a> · <a href="source-input-bindings.json">Exact source/input routes</a> · <a href="sources-and-inputs.zip">Bound sources and history</a></p><p>The reader displays saved evidence. It cannot establish proof validity by itself.</p></section></main><script defer src="viewer.js"></script></body></html>'''
    reader=DEST/'reader.html';reader.write_text(content);files.add(str(reader.relative_to(ROOT)))
    save('result-summary.json',dict(goal_status='active',accepted_ground_certificates=passed,assessment=selected['assessment'],controls=[dict(id=o['id'],status=o['status'],attempts=o['attempts'],seconds=o['seconds'],independent_certificate_accepted=o['independent_certificate_accepted'],independent_trace_accepted=o['independent_trace_accepted']) for o in observations],active_cluster_descriptors=0,authored_target_hints=0,new_native_queries=0,new_RL_training=False,additional_owned_seconds=str(ownedtotal),scope='Finite symbolic ground-sequent search; trace, point, symbolic and native acceptance remain distinct.'))
    previous=baseline.decode();assert 'RESEARCH NOTEBOOK · 106' in previous
    panel='<section class="panel" id="receptor-matching"><h2>Checkpoint 107 · Generic literal receptor matching</h2><p>'+prose(selected['main_assessment'])+' <a href="receptor-matching/reader.html?v=20261011-rm1#reader">Read the actual tile rows, formulas and search traces</a>.</p><p>The old readiness tier, complete fallback and primitive graph are unchanged. No target-proof word, active cluster descriptor, new native query or RL training is supplied.</p></section>\n'
    anchor='<section class="panel" id="automatic-geometry">';assert previous.count(anchor)==1
    updated=previous.replace('RESEARCH NOTEBOOK · 106','RESEARCH NOTEBOOK · 107',1).replace(anchor,panel+anchor,1)
    current=ROOT/MAIN
    if current.read_bytes()!=baseline:
        oldmanifest=load(HERE/'task-files.json');record=next(e for e in oldmanifest if e['path']==MAIN)
        assert pin(current)=={k:record[k] for k in ('sha256','bytes')},'unrelated main report edit'
    current.write_text(updated);files.add(MAIN)
    manifest=[dict(path=f,**pin(ROOT/f)) for f in sorted(files)];(HERE/'task-files.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(files=len(manifest),origins=len(origins),bindings=len(bindings),accepted_ground_certificates=passed,science_executed_by_report=False)))


if __name__=='__main__':main()
