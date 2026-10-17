"""Raw/AST/compile/real-patch metadata only; reviewed Source never evaluated."""
import ast
import copy
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

P=Path('/private/tmp/gcts-first-admission-journal-engine-source-20261017')
parent=Path('/private/tmp/gcts-head-gated-family-engine-source-20261017/receptor_family_search_engine_v7.py')
current=P/'receptor_family_search_engine_v8.py'
checks=[]
def pin(path):
    path=Path(path);raw=path.read_bytes()
    return dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    path=P/name
    assert not path.exists()
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    return pin(path)
def check(name,condition,**details):
    assert condition,name
    checks.append(dict(check=name,passed=True,**details))
old,parent_raw=parent.read_text(),parent.read_bytes()
new,current_raw=current.read_text(),current.read_bytes()
check('parent and current immutable raw pins',pin(parent)['sha256']=='b53dbb82f8f06f6b844eaeaedbe2ec646b77e88c40473016d16adf894c8ead9e' and pin(current)['sha256']=='9fd543e42db1e8f657a36cd081c7f9bd4621bb22b97e4daabe5a8856e944eb7f')
oldtree,newtree=ast.parse(old),ast.parse(new)
compile(current_raw,str(current),'exec')
check('AST and compile without evaluation',True)
oldlines,newlines=old.splitlines(keepends=True),new.splitlines(keepends=True)
edits=[]
for op,a,b,c,d in difflib.SequenceMatcher(None,oldlines,newlines,autojunk=False).get_opcodes():
    if op!='equal':edits.append(dict(operation=op,old_start=a,old_end=b,new_start=c,new_end=d,old=''.join(oldlines[a:b]),new=''.join(newlines[c:d])))
forward=oldlines[:]
for e in reversed(edits):forward[e['old_start']:e['old_end']]=e['new'].splitlines(keepends=True)
inverse=newlines[:]
for e in reversed(edits):inverse[e['new_start']:e['new_end']]=e['old'].splitlines(keepends=True)
check('whole raw forward and inverse',''.join(forward)==new and ''.join(inverse)==old,regions=len(edits))
check('whole AST forward and inverse',ast.dump(ast.parse(''.join(forward)),include_attributes=False)==ast.dump(newtree,include_attributes=False) and ast.dump(ast.parse(''.join(inverse)),include_attributes=False)==ast.dump(oldtree,include_attributes=False))
patches=[]
for direction,start,finish in [('forward',oldlines,newlines),('inverse',newlines,oldlines)]:
    raw=''.join(difflib.unified_diff(start,finish,fromfile=parent.name if direction=='forward' else current.name,tofile=current.name if direction=='forward' else parent.name,n=3)).encode()
    path=P/('engine-v8.'+direction+'.patch');assert not path.exists();path.write_bytes(raw)
    target=P/('actual-patch-'+direction+'.py');target.write_text(''.join(start))
    done=subprocess.run(['patch','-s','-F0',str(target),str(path)],capture_output=True)
    check('actual '+direction+' text patch application and cmp',done.returncode==0 and target.read_text()==''.join(finish),returncode=done.returncode,stdout=done.stdout.decode(),stderr=done.stderr.decode())
    patches.append(pin(path))

def regions(raw):
    lines=raw.splitlines(keepends=True);out={}
    def walk(n,prefix=''):
        for child in ast.iter_child_nodes(n):
            if isinstance(child,(ast.FunctionDef,ast.ClassDef)):
                key=prefix+child.name
                out[key]=(''.join(lines[child.lineno-1:child.end_lineno]),ast.dump(child,include_attributes=False))
                walk(child,key+'.')
            else:walk(child,prefix)
    walk(ast.parse(raw));return out
oldr,newr=regions(old),regions(new)
changed=[k for k in oldr if oldr[k]!=newr.get(k)]
exact=[k for k in oldr if oldr[k]==newr.get(k)]
check('existing named regions only constructor/search/walk/class change',set(oldr)==set(newr) and set(changed)=={'LazyUnitRowEngine','LazyUnitRowEngine.__init__','LazyUnitRowEngine.search','LazyUnitRowEngine.search.walk'},unchanged=exact,changed=changed)
diag_names={'milestone_observer','first_root_family_journal','child_milestone_pending','journal_this_root'}
class Erase(ast.NodeTransformer):
    def visit_If(self,n):
        if any(isinstance(x,ast.Name) and x.id in {'first_root_family_journal','child_milestone_pending','journal_this_root'} for x in ast.walk(n.test)):
            return None
        return self.generic_visit(n)
    def visit_Assign(self,n):
        if any(isinstance(t,ast.Name) and t.id in diag_names for t in n.targets):return None
        if any(isinstance(t,ast.Attribute) and t.attr in {'_milestone_observer','_milestone_observer_anchor'} for t in n.targets):return None
        if any(isinstance(t,ast.Name) and t.id=='VERSION' for t in n.targets):
            n.value=copy.deepcopy(next(x.value for x in oldtree.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VERSION' for t in x.targets)))
        return self.generic_visit(n)
    def visit_Expr(self,n):
        if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='need' and any(isinstance(x,ast.Name) and x.id=='milestone_observer' for x in ast.walk(n.value)):
            return None
        return self.generic_visit(n)
    def visit_Nonlocal(self,n):
        n.names=[x for x in n.names if x not in diag_names];return n
    def visit_arguments(self,n):
        pairs=[(arg,default) for arg,default in zip(n.kwonlyargs,n.kw_defaults) if arg.arg!='milestone_observer']
        n.kwonlyargs=[x for x,y in pairs];n.kw_defaults=[y for x,y in pairs]
        return self.generic_visit(n)
erased=Erase().visit(copy.deepcopy(newtree));ast.fix_missing_locations(erased)
check('whole diagnostic erasure restores exact complete parent AST',ast.dump(erased,include_attributes=False)==ast.dump(oldtree,include_attributes=False))

stages=['FIRST_ROOT_FAMILY_PLAN_READY','FIRST_ROOT_FAMILY_EVENT_READY','FIRST_ROOT_PRIMITIVE_PLACED','FIRST_CHILD_DECISION_READY']
common=['schema','stage','engine_version','depth','diagnostic_only','scientific_acceptance']
extra={stages[0]:['pre_state','decision','decision_event','plan','prototype_census'],stages[1]:['state','pending_preferences','event'],stages[2]:['state','transition','invalidation_event','place_event'],stages[3]:['state','decision','decision_event','prototype_census']}
calls=[x for x in ast.walk(newtree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='milestone_observer']
check('exactly four direct literal observer call sites',len(calls)==4 and {x.args[0].value for x in calls}==set(stages))
for call in calls:
    stage=call.args[0].value;payload=call.args[1]
    keys=[k.value for k in payload.keys]
    check('exact builtin payload '+stage,isinstance(payload,ast.Dict) and set(keys)==set(common+extra[stage]) and not any(isinstance(x,(ast.Call,ast.ListComp,ast.DictComp,ast.Set,ast.Tuple,ast.GeneratorExp)) for x in ast.walk(payload)),line=call.lineno,fields=keys)
check('no imports added',[(type(x).__name__,ast.dump(x)) for x in newtree.body if isinstance(x,(ast.Import,ast.ImportFrom))]==[(type(x).__name__,ast.dump(x)) for x in oldtree.body if isinstance(x,(ast.Import,ast.ImportFrom))])
check('all degree/candidate/point/transition/census/cursor/scheduler/rollback bodies exact',all(oldr[k]==newr[k] for k in oldr if k not in changed))
delta=save('Source-delta-v8.json',dict(schema='first-admission-journal-engine-raw-delta-v1',parent=pin(parent),source=pin(current),coordinate_system='zero-based lines/end exclusive',edits=edits,forward_patch=patches[0],inverse_patch=patches[1],whole_raw_and_AST_inverse=True,diagnostic_AST_erasure_exact=True,source_only=True,scientific_calls=0))
static=save('static-Source-audit-v8.json',dict(schema='first-admission-journal-engine-static-audit-v1',source=pin(current),parent=pin(parent),checks=checks,source_evaluated=False,scientific_calls=0,scientific_acceptance=False,unchanged_named_regions=exact,changed_named_regions=changed,observer_call_sites=[dict(stage=x.args[0].value,line=x.lineno) for x in calls],raw_references=[pin(parent),pin(current),*patches,delta]))
api=save('API-wire-v8.json',dict(schema='first-admission-journal-engine-API-v1',source=pin(current),parent=pin(parent),VERSION='lazy-unit-row-global-engine-v13-receptor-family-preferences-v8-first-admission-journal',unchanged_provider_version='receptor-family-observed-receptor-transfer-provider-v8-head-gated',constructor='LazyUnitRowEngine(*,language,degree_proposer,semantics,fallback,certify_fallback,transition_checker,tick,milestone_observer,initial_state=None,maximum_nodes=128,maximum_events=2000,branch_adviser=None,validate_advice=None,branch_tie=ROW,family_proposer=None,family_consumer=None,initial_prototype_census=None)',required_observer='Authenticated synchronous read-only milestone_observer(stage,payload), positional. Return ignored; native/Source/other errors are not masked.',stages=stages,payload_schema='unit-row-first-family-engine-milestone-v1',common_fields=common,stage_fields=extra,phase_labels=dict(zip(stages,['M1_PLAN_READY','M2_EVENT_READY','M3_PLACE_RETURN','M4_CHILD_DECISION'])),record_semantics={stages[0]:'Only first completed depth0 family selection; actual global DECISION event retained before selection delegate, since selection can emit fallback events. plan.mode explicitly distinguishes BATCH/CONTINUATION READY preference from CANONICAL_FALLBACK.',stages[1]:'After unchanged _adopt_family_branch returns; individual full FAMILY_PREFERENCE event. No placement yet.',stages[2]:'After unchanged place returns; exact installed COW state, transition and individual preceding INVALIDATE/PLACE events; no child decision yet.',stages[3]:'After first decision returned at depth1 beneath this root placement, before classifying or acting on the decision. Actual individual DECISION event owns statuses/evidence; no private int-key certificate dictionary.'},lifetime='At most four callbacks per search(), only first root family branch; local diagnostic flags are not semantic state or checkpoint metadata. No callbacks for later root siblings/branches. Child callback only if matching root placement and its original observer post-tick returned.',payload_types='Builtin JSON dict/list/str/int/bool/None; own fields are fresh wrappers, references point only to already-owned literal plans/state/census/individual events. No tuple/frozenset/function/private int-key map/live events list. No deep copy/hash/traversal/model call is introduced by packet construction.',scientific_authority=False,source_only=True,scientific_calls=0,actual_execution_authorized=False))
parent_h=pin('/private/tmp/gcts-head-gated-family-engine-source-20261017/handoff-v7.json')
parent_c=pin('/private/tmp/gcts-head-gated-family-engine-source-20261017/Source-contract-v7.json')
parent_peer=pin('/private/tmp/gcts-head-gated-family-engine-peer-20261017/typed-Source-review-v7.json')
proposal=pin('/private/tmp/gcts-postconsumer-cost-plan-20261017/Source-cost-plan-v1.json')
source=pin(current);sources={'family_engine':source}
abi={'schema':'receptor-family-first-admission-journal-engine-typed-Source-review-v8','scope':'receptor-family-first-admission-journal-engine-Source','author_identity':'/root/hilbert_ordering_diagnosis','source':source,'sources':sources,'source_only':True,'scientific_calls':0,'scientific_acceptance':False,'required':['Whole current Source/API/contract and unchanged operative engine7 ancestry; all raw edits/whole AST erasure/actual forward+inverse patches.','Exactly four first-root observer calls, native pre/post ticks and retained callback identity; no later science gating from return values.','Full literal plans/provider reports/consumer receipts/native state/census and existing events; original COW/nonmutation lifetime and no live list/private int-key map exposure.','All original scheduler/global DEAD/FORCED/earliest-generation/one-primitive/fallback/census/retention/owned rollback logic erasure exact.','Original17/input2 epoch/model and Root native20/512/once/Source guards remain external immutable prerequisites; no runtime or prior qualification inherited.','Disclose helper/engine/old primitive authorship overlap and no scientific execution; no author self-review.']}
contract=save('Source-contract-v8.json',dict(schema='receptor-family-first-admission-journal-engine-Source-contract-v8',scope=abi['scope'],author_identity=abi['author_identity'],source=source,sources=sources,source_only=True,scientific_calls=0,scientific_acceptance=False,source_evaluated=False,runtime_qualified=False,actual_execution_authorized=False,proof_accepted=False,engine_accepted=False,pruning_accepted=False,RL_accepted=False,API=api,Review_ABI=abi,parent_source=pin(parent),operative_parent_contract=parent_c,parent_handoff=parent_h,preserved_parent_distinct_peer=parent_peer,source_cost_proposal=proposal,source_delta=delta,static_audit=static,patches=patches,implementation_scope='New required diagnostic observer and four bounded first-root milestone calls only, explicit new VERSION. No scientific function/candidate/universe/marking/native-evidence/receipt policy change. No Root actual or new grant in this packet.',model_and_limits='Original17/input2 semantic binding and epoch unchanged and separately authenticated from Root current executable map. Root passes original maximum_nodes2/maximum_events256 and same native20/512, internal500 reserve, failure55/owned60/caller90+1/once. Engine generic defaults and ceilings unchanged. Observer metadata time/memory and any phase writes consume the same original20/512; failure writer is Root-owned separate55 builtin-only path.',unchanged_math='All native receipt validation, independent degree checker, whole original/decorated tile/state/membership checks, collision ledgers, complete candidate universe, selected/excluded domain dependency, fixed marking, generation/tie policy, complete fallback ordering/EOF/current keys, transitions/refresh, `_candidate`, `_observe`, `_install`, place/exclusion, checkpoint/rollback and root/native output behavior remain raw/AST exact except VERSION observations. Exact full diagnostic erasure restores parent entire AST, including original search compound statements/guards/caps/catches/finally.',observer_protocol={'constructor_required':True,'signature':'milestone_observer(stage,payload)','return_ignored':True,'maximum_calls_per_search':4,'call_order':stages,'selection_status':'PLAN_READY is completion of engine branch-plan selection, not an asserted READY family; complete plan.mode/receipt.status remain explicit. A canonical fallback is never relabelled family admission.','charges':'Every call has engine tick and endpoint identity check before and after; callback must use Root original tick/native phase endpoint and complete Source guards. No new clock here. Native/Source/other errors propagate; old TimeoutError catch/restoration remains unchanged.','no_late_calls':'This module contains no failure writer or postdeadline observer path. If a native tick fails, later milestones do not execute. Root writer may serialize bounded retained literals using its separately reviewed captured native55/builtin-only path.','prefix_semantics':'Markers/observer records may be incomplete due a postwrite/postobserver native tick. Even all four records cannot independently certify restoration, complete resource closure, theorem, trajectory, degree/fallback authority, runtime advantage or end-to-end gain. Later original search continues without a forced stop.'},COW_nonmutation_argument=['Stage1 plan owns full engine-copied consumer receipt and copied provider report/census. `_adopt_family_branch` copies family into preferences, `_candidate` copies candidate, and original selection/adoption/place never mutate the retained plan or its owned receipts. Provider/consumer callbacks receive private copies, not this plan.','Current `_state` is replaced on prepared `_install`/exclusion and restored by pointer from owned checkpoint. No engine operation mutates an installed state dictionary or its nested arrays in place; place first makes a deep private copy. Retained pre/post state references remain stable.','`_family_prototype_census` is replaced with a fresh dictionary by `_join_prototype_census`; never updated in place. `_preferences` is copied/replaced, not mutated. Checkpoint tuple retains exact old semantic/cursor/dependency/ledger references; diagnostic flags/references remain outside that tuple.','Every event payload is detached by `_emit` JSON roundtrip before append. No engine operation mutates an existing event; subsequent append never changes the individual event object passed here. Root decision event is captured before selection because fallback can append. Stage2 last event is FAMILY_PREFERENCE; stage3 preceding events are successful INVALIDATE/PLACE; stage4 last event is actual completed DECISION.','All retained payload structures are builtin JSON data by unchanged fresh copy/native point/receipt pipelines or `_emit` JSON reconstruction. No private int-key `_certs` dictionary, live appendable event list, iterator, closure, owner engine or callback object is delegated. Root observer must only retain these objects read-only; later serialization belongs to bounded builtin writer.','These are Source facts under the same synchronous authenticated pinned Sources/nonreentrancy assumption as the parent. No hostile observer/frame mutation, arbitrary nth-tick trace equivalence, asynchronous mutation, or malicious callable guarantee is asserted. The observer can consume budget or fail; such failure remains UNKNOWN/error without pruning authority.'],authorship_overlap='Author owns census-engine4-7 and older checker/point/diagnostic ancestry. This is author Source audit only. Arithmetic authors separately required helper plumbing and performs distinct engine review; Root independently reviews/integrates observer/writer/reader/current Source map. Shared old primitives and schema coordination do not substitute for those peer gates.',future_review_and_actual=['Distinct whole engine Source review before integration.','Fresh Root helper/cold/observer/writer/reader Source composition review with exact current executable/contract pins; preserve original semantic authority and all native once limits.','Actual measured Root diagnostic only after new explicit grant; no outcome/fit/cost improvement predicted and no inheritance from earlier incomplete windows.']))
abi['source_contract']=contract
handoff=save('handoff-v8.json',dict(schema='receptor-family-first-admission-journal-engine-handoff-v8',author_identity='/root/hilbert_ordering_diagnosis',source=source,sources=sources,source_contract=contract,API=api,Review_ABI=abi,parent_source=pin(parent),parent_handoff=parent_h,parent_contract=parent_c,parent_distinct_peer=parent_peer,source_delta=delta,static_audit=static,patches=patches,source_only=True,scientific_calls=0,scientific_acceptance=False,source_evaluated=False,runtime_qualified=False,actual_execution_authorized=False,next_action='Distinct whole Source review, Root current helper/cold observer/writer/reader integration and review; Root alone may later grant one fresh measured actual.'))
print(json.dumps(dict(source=source,contract=contract,handoff=handoff,API=api,delta=delta,static=static,checks=len(checks),regions=len(edits),unchanged=len(exact)),indent=2))
