"""SOURCE ONLY genuine original-language retained-domain adversarial controls.

No proof word/donor/library, project imports, clocks, runner or activation.
Transition/refresh are caller-authenticated callables with fresh authority.
"""
import copy
import hashlib
import json

VERSION = 'unit-row-retained-domain-controls-v1'

class Unavailable(Exception):
  pass

class CallbackExhausted(TimeoutError):
  pass

def need(ok, reason):
  if not ok:
    raise AssertionError(reason)

def canonical(value):
  return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)

def digest(value):
  return hashlib.sha256(canonical(value).encode()).hexdigest()

def tile(language,witness,premises,reads,row,tick):
  tick()
  member=language.primitive(copy.deepcopy(witness),copy.deepcopy(premises))
  need(type(row) is int and 0<=row<24 and all(type(k) is int and 0<=k<row for k in reads),'fixture strict-prior rows')
  need(len(reads)==len(premises),'fixture ordered port occurrences')
  offsets=[k-row for k in reads]
  pre={'input_epoch':language.binding['language_epoch'],'primitive_witness':copy.deepcopy(witness),
    'ordered_premise_formulas':copy.deepcopy(premises),'ordered_offsets':offsets}
  key={'tile_type_id':'bounded-point-tile-'+digest(pre),'type_preimage':pre,'translation':[0,row]}
  local=[[[1,0],['formula',canonical(witness['formula'])]]]
  marks=[[[1,row],['formula',canonical(witness['formula'])]]]
  for port,(formula,offset,k) in enumerate(zip(premises,offsets,reads)):
    tick();value=['formula',canonical(formula)]
    local.extend([[[1,offset],copy.deepcopy(value)],[[2+port,0],['offset',offset]]])
    marks.extend([[[1,k],copy.deepcopy(value)],[[2+port,row],['offset',offset]]])
  return {'placement_key':key,'selection_record':dict(copy.deepcopy(key),generation=1),
    'local_t_values':[[[0,0],1]],'local_m_values':local,'global_t_values':[[[0,row],1]],
    'global_m_values':marks,'membership':member}

def state(language,tiles,tick,excluded=()):
  epoch=language.binding['language_epoch'];totals={r:0 for r in range(24)}
  marks={(1,r):['outside',epoch] for r in range(-23,0)}
  marks[(1,23)]=['formula',canonical(language.target)]
  selected=[];seen=set()
  for item in tiles:
    tick();key=canonical(item['placement_key'])
    if key in seen:raise Unavailable('fixture duplicates a selected placement')
    seen.add(key);selected.append(copy.deepcopy(item['selection_record']))
    for point,value in item['global_t_values']:
      if point[0]!=0 or point[1] not in totals or type(value) is not int:raise Unavailable('fixture support outside target')
      totals[point[1]]+=value
      if totals[point[1]]>1:raise Unavailable('fixture support overfill')
    for point,value in item['global_m_values']:
      p=tuple(point)
      if p in marks and canonical(marks[p])!=canonical(value):raise Unavailable('fixture marking conflict')
      marks[p]=copy.deepcopy(value)
  return {'schema':'unit-row-implicit-private-state-v1','input_epoch':epoch,'height':24,
    't':[[[0,r],totals[r]] for r in range(24)],'m':[[list(p),v] for p,v in sorted(marks.items())],
    'selected':selected,'excluded':copy.deepcopy(list(excluded)),
    'generation':[[[0,r],0] for r in range(24)]}

def ug(language,body,variable,source,row,tick):
  return tile(language,{'rule':'generalize','variable':variable,'formula':['all',variable,copy.deepcopy(body)]},
        [body],[source],row,tick)

def obligations(item, s):
  value=copy.deepcopy(item);row=value['placement_key']['translation'][1]
  pre=value['placement_key']['type_preimage'];totals={tuple(p):v for p,v in s['t']}
  value['read_obligations']=[{'row':row+d,'formula':copy.deepcopy(f),
    'occupied':totals[(0,row+d)]==1,'fact_accepted':False}
    for d,f in zip(pre['ordered_offsets'],pre['ordered_premise_formulas'])]
  return value


class LoggedCursor:
  """Records REAL events; optional replay interruption never manufactures EOF."""
  def __init__(self,real,record,limit):
    self.real,self.record,self.limit,self.count=real,record,limit,0
  def context(self):
    return self.real.context()
  def advance(self):
    if self.limit is not None and self.count>=self.limit:
      self.real.abort();self.record['interrupted_after_candidates']=self.count
      raise CallbackExhausted('declared retained-prefix replay interruption')
    value=self.real.advance();self.record['events'].append(copy.deepcopy(value))
    if value['kind']=='CANDIDATE':self.count+=1
    return value
  def abort(self):
    return self.real.abort()


def run_controls(*,language,engine_factory,degree_proposer,fallback,certify_fallback,transition,refresh,tick):
  cases=[];outside=language.OutsideLanguage
  scope='Original-language local domain/transaction controls; no theorem, search trajectory or benefit claim.'
  def passed(name,observed,local_scope=scope):
    tick();cases.append({'case':name,'status':'PASSED','observed':copy.deepcopy(observed),'scope':local_scope})
  def skip(name,reason):
    cases.append({'case':name,'status':'SKIPPED','observed':{'reason':reason},'scope':'Unavailable original fixture; gap retained.'})
  def prepared(fn,*args):
    try:return fn(*args)
    except outside as error:
      if type(error) is not outside:raise
      raise Unavailable('Original fixture membership exclusion: '+str(error))
  def make(s,fb=fallback):
    return engine_factory(initial_state=copy.deepcopy(s),degree_proposer=degree_proposer,fallback=fb,
      certify_fallback=certify_fallback,tick=tick)
  def snap(e):
    result=e.state_snapshot()
    need(result['state']['generation']==[[[0,r],0] for r in range(24)],'original root generations0')
    return result
  def restored(e,before):
    after=snap(e);need(canonical(after)==canonical(before),'exact retained-domain/checkpoint/archive rollback')
    return after
  def rowproof(snapshot,row):
    return next(p for p in snapshot['last_transition']['rows'] if p['row']==row)
  def cursor(snapshot,row):
    return dict(snapshot['cursors'])[row]
  def cert(snapshot,row):
    return dict(snapshot['certificates'])[row]
  def rejected(fn,reason_substring):
    reason=None
    try:fn()
    except ValueError as error:
      if type(error) is not ValueError:raise
      reason=str(error)
    need(reason is not None and reason_substring in reason,'exact independent rejection edge')
    tick();return {'exception_type':'ValueError','reason':reason}
  def logged(log,before_sha=None,limit=None):
    def open_cursor(**kwargs):
      real=fallback(**kwargs);context=real.context()
      record={'context':copy.deepcopy(context),'events':[]};log.append(record)
      cap=limit if before_sha is not None and context['state_sha256']!=before_sha else None
      return LoggedCursor(real,record,cap)
    return open_cursor
  def drain(e,row,limit=8):
    candidates=[]
    for _ in range(limit):
      event=e.next_alternative(row)
      if event['kind']=='EOF':return candidates,event['completion']
      need(event['kind']=='CANDIDATE','actual candidate/EOF');candidates.append(event['candidate'])
    raise AssertionError('declared tiny original fixture did not reach real EOF')
  def core_without_occupancy(value):
    result=copy.deepcopy(value)
    for o in result['read_obligations']:o.pop('occupied')
    return result
  def archive_matches(slot,old_slot):
    # Immutable four-field entries retain actual packets from that context.
    entries=slot['context_archive']
    return any(canonical(x['context'])==canonical(old_slot['context'])
      and canonical(x['completion'])==canonical(old_slot['completion'])
      and canonical(x['keys'])==canonical(old_slot['keys'])
      and canonical(x['candidates'])==canonical(old_slot['candidates']) for x in entries)

  names=sorted(language.theory['axioms']);variables=[v for v in language.parameters if v not in language.forbidden]
  group=['retained-domain-refreshes-only-read-occupancy','old-receipt-unchanged-explicit-transfer',
    'fresh-full-prefix-replay-before-current-EOF','multiple-transitions-preserve-literal-context-EOF-archives',
    'refresh-independent-current-packets-input-unchanged','refresh-forged-core-rejected','refresh-duplicate-full-key-rejected',
    'repeated-retention-before-replay-does-not-relabel-archive','fresh-prefix-replay-before-new-candidate',
    'interrupted-retained-replay-never-EOF']
  main=None
  if not names or not variables:
    for name in group:skip(name,'Need original AX and Gamma-eligible parameter.')
  else:
    a=copy.deepcopy(language.theory['axioms'][names[0]]);v=variables[0]
    try:
      if a[0]=='imp':raise Unavailable('Original chosen AX must be non-imp for tiny completed cover.')
      roots=list(language.theory['axioms'].values())+list(language.gamma)
      if sum(f==a for f in roots)!=1:raise Unavailable('Need unique original AX/Gamma occurrence for pending row1.')
      d=['all',v,copy.deepcopy(a)]
      if any(f==d for f in roots):raise Unavailable('Extra original root matches two-UG fixture output.')
      ax=prepared(tile,language,{'rule':'axiom','name':names[0],'formula':a},[],[],0,tick)
      u2=prepared(ug,language,a,v,1,2,tick);u5=prepared(ug,language,d,v,3,5,tick)
      base=state(language,[ax,u2,u5],tick)
      fill1=obligations(prepared(tile,language,{'rule':'axiom','name':names[0],'formula':a},[],[],1,tick),base)
      fill4=obligations(prepared(tile,language,{'rule':'axiom','name':names[0],'formula':a},[],[],4,tick),base)
      fill6=obligations(prepared(tile,language,{'rule':'axiom','name':names[0],'formula':a},[],[],6,tick),base)
      main=(base,fill1,fill4,fill6,ax,u2,a,v)
    except Unavailable as error:
      for name in group:skip(name,str(error))

  if main is not None:
    base,fill1,fill4,fill6,ax,u2,a,v=main;log=[];e=make(base,logged(log));root=snap(e);token=e.checkpoint()
    try:
      decision=e.decision();classified=snap(e);original_receipt=copy.deepcopy(cert(classified,3))
      need(original_receipt['schema']=='unit-row-degree-evidence-check-v2' and original_receipt['status']=='MANY'
        and original_receipt['degree_exact']==2,'two complete original UG occurrence keys')
      items,completion=drain(e,3);before=snap(e);old_slot=copy.deepcopy(cursor(before,3))
      need(len(items)==2 and old_slot['completion'] is not None,'complete old real two-key stream')
      need(sorted(o['occupied'] for c in items for o in c['read_obligations'])==[False,True],
        'one pending versus one occupied original read')
      e.place(fill1);after=snap(e);retained=copy.deepcopy(cursor(after,3))
      proof=rowproof(after,3)
      need(proof['retain'] is True and after['last_transition']['collision_ledger_equal'] is True
        and proof['read_occupancy_changes']==[1],'same full relation/prototype ledger, only read1 occupancy changed')
      need(after['row_versions'][3]==before['row_versions'][3] and after['row_versions'][1]>before['row_versions'][1],
        'retained row version stable, newly occupied row invalidated')
      need(canonical(retained['keys'])==canonical(old_slot['keys']) and canonical(retained['context'])==canonical(old_slot['context'])
        and canonical(retained['completion'])==canonical(old_slot['completion']),'old context/EOF not relabeled at transition')
      need(all(canonical(core_without_occupancy(x))==canonical(core_without_occupancy(y)) for x,y in zip(items,retained['candidates']))
        and all(o['occupied'] is True for c in retained['candidates'] for o in c['read_obligations']),
        'only occupancy refreshes; complete keys/core/ordered obligations preserved')
      passed('retained-domain-refreshes-only-read-occupancy',{'decision':decision,'before':before,'after':after})
      transferred=copy.deepcopy(cert(after,3))
      need(transferred['schema']=='unit-row-transferred-domain-classification-v1'
        and canonical(transferred['original_receipt'])==canonical(original_receipt)
        and transferred['state_sha256']==digest(after['state'])
        and original_receipt['state_sha256']==digest(base)
        and transferred['state_sha256']!=original_receipt['state_sha256'],
        'new explicit proof wrapper keeps exact original checked receipt/state SHA')
      passed('old-receipt-unchanged-explicit-transfer',{'original_receipt':original_receipt,'current_transfer':transferred})
      raw_before=canonical(items)
      fresh=refresh(state=copy.deepcopy(after['state']),candidates=copy.deepcopy(items),tick=tick)
      need(canonical(items)==raw_before and canonical(fresh)==canonical(retained['candidates']),
        'independent refresh agrees exactly and never mutates original packets')
      passed('refresh-independent-current-packets-input-unchanged',{'old':items,'current':fresh},
        'Refresh premise is previously c354-checked engine-owned candidates, not arbitrary old read metadata.')
      bad=copy.deepcopy(items);bad[0]['global_m_values'][0][1]=['CONTROL_FORGED']
      passed('refresh-forged-core-rejected',rejected(lambda:refresh(state=copy.deepcopy(after['state']),candidates=bad,tick=tick),
        'unchanged entire core'))
      passed('refresh-duplicate-full-key-rejected',rejected(lambda:refresh(state=copy.deepcopy(after['state']),
        candidates=[copy.deepcopy(items[0]),copy.deepcopy(items[0])],tick=tick),'unique known full keys'))
      e.place(fill4);before_replay=snap(e);unreplayed=cursor(before_replay,3)
      need(canonical(unreplayed['context'])==canonical(old_slot['context'])
        and canonical(unreplayed['completion'])==canonical(old_slot['completion'])
        and archive_matches(unreplayed,old_slot)
        and sum(canonical(x['context'])==canonical(old_slot['context']) for x in unreplayed['context_archive'])==1,
        'repeated retention without replay preserves single original actual archive entry, not refreshed old-context packets')
      passed('repeated-retention-before-replay-does-not-relabel-archive',{'old_slot':old_slot,'after_two_transitions':before_replay})
      previous_replays=e.counts['cursor_replays'];start=len(log);event=e.next_alternative(3);current=snap(e)
      need(event['kind']=='EOF' and len(log)==start+1,'retained old EOF triggers genuine fresh cursor')
      observed=log[-1];need(observed['context']['state_sha256']==digest(before_replay['state'])
        and [x['kind'] for x in observed['events']]==['CANDIDATE','CANDIDATE','EOF']
        and [x['ordinal'] for x in observed['events'][:-1]]==[0,1]
        and e.counts['cursor_replays']==previous_replays+2,'every actual full prefix precedes fresh EOF')
      current_slot=copy.deepcopy(cursor(current,3))
      need(current_slot['context']['state_sha256']==digest(before_replay['state']) and archive_matches(current_slot,old_slot),
        'exact original full context/EOF/prefix archive survives current context installation')
      passed('fresh-full-prefix-replay-before-current-EOF',{'actual_new_cursor':observed,'new_slot':current_slot,'returned':event})
      before_second=snap(e);second_old=copy.deepcopy(cursor(before_second,3));e.place(fill6);second=snap(e)
      need(rowproof(second,3)['retain'] is True and second['last_transition']['collision_ledger_equal'] is True,
        'second existing AX prototype outside q3 support also retains q3')
      second_event=e.next_alternative(3);second_final=snap(e);second_slot=cursor(second_final,3)
      need(second_event['kind']=='EOF' and archive_matches(second_slot,old_slot) and archive_matches(second_slot,second_old),
        'both full original contexts/completions/prefixes survive multiple transitions and actual replay')
      second_receipt=cert(second_final,3)
      need(canonical(second_receipt['original_receipt'])==canonical(original_receipt)
        and len(second_receipt['transfer_chain'])==3,'multi-hop transfer keeps original receipt, explicit chain')
      passed('multiple-transitions-preserve-literal-context-EOF-archives',{'before_second':before_second,
        'after_second':second_final,'returned':second_event})
    finally:e.rollback(token)
    restored(e,root)

    # A retained one-key prefix must replay before a new candidate too, not only EOF.
    log=[];e=make(base,logged(log));root=snap(e);token=e.checkpoint()
    try:
      e.decision();first=e.next_alternative(3);old=snap(e);e.place(fill1);changed=snap(e)
      need(first['kind']=='CANDIDATE' and len(cursor(old,3)['keys'])==1,'one actual saved prefix key')
      start=len(log);replays=e.counts['cursor_replays'];second=e.next_alternative(3);after=snap(e)
      need(second['kind']=='CANDIDATE' and len(log)==start+1
        and [x['kind'] for x in log[-1]['events']]==['CANDIDATE','CANDIDATE']
        and [x['ordinal'] for x in log[-1]['events']]==[0,1]
        and log[-1]['context']['state_sha256']==digest(changed['state'])
        and e.counts['cursor_replays']==replays+1,'replay entire saved prefix before returning next original candidate')
      need(second['candidate']['placement_key']!=first['candidate']['placement_key']
        and second['candidate']['read_obligations'][0]['occupied'] is True
        and archive_matches(cursor(after,3),cursor(old,3)),'next original ordered key and occupied metadata/current archive')
      passed('fresh-prefix-replay-before-new-candidate',{'first':first,'before':old,'changed':changed,
        'actual_new_cursor':log[-1],'second':second,'after':after})
    finally:e.rollback(token)
    restored(e,root)

    # Real replay interrupted after the first of two required saved keys.
    log=[];e=make(base,logged(log,digest(base),1));root=snap(e);token=e.checkpoint()
    try:
      e.decision();drain(e,3);e.place(fill1);before=snap(e);start=len(log);reason=None
      try:e.next_alternative(3)
      except CallbackExhausted as error:
        if type(error) is not CallbackExhausted:raise
        reason=str(error)
      need(reason is not None and len(log)==start+1 and len(log[-1]['events'])==1
        and log[-1]['events'][0]['kind']=='CANDIDATE' and log[-1]['interrupted_after_candidates']==1,
        'actual prefix interrupted after one, no candidate/EOF return shortcut')
      after=snap(e);need(canonical(after)==canonical(before),'interrupted replay does not replace logical slot/context/archives')
      passed('interrupted-retained-replay-never-EOF',{'before':before,'after':after,'actual_cursor':log[-1],
        'exception_type':'CallbackExhausted','reason':reason},
        'CONTROL-ONLY interruption of real current cursor after one of two mandatory prefix events; no fake EOF/universe.')
    finally:e.rollback(token)
    restored(e,root)

  remote_group=['same-UG-prototype-remote-marks-retain-earlier-invalidate-affected','current-illegal-old-candidate-refresh-rejected',
    'local-exclusion-stable-ledger-invalidates-own-row','new-global-prototype-ledger-invalidates-all-domains']
  remote=None
  if main is not None:
    base,fill1,fill4,fill6,ax,u2,a,v=main
    try:
      small=state(language,[ax,u2],tick)
      remote_tile=obligations(prepared(ug,language,a,v,3,4,tick),small)
      need(canonical(remote_tile['placement_key']['type_preimage'])==canonical(u2['placement_key']['type_preimage']),
        'translated same UG offset/body/epoch prototype')
      remote=(small,remote_tile)
    except Unavailable as error:
      for name in remote_group:skip(name,str(error))
  else:
    for name in remote_group:skip(name,'Primary original AX/UG fixture unavailable.')
  if remote is not None:
    small,remote_tile=remote;e=make(small);root=snap(e);token=e.checkpoint()
    try:
      e.decision();before=snap(e)
      old_bad=[r['candidate'] for _,r in before['exposed_candidates'] if r['row']==3
        and r['candidate']['placement_key']['type_preimage']['primitive_witness']['formula']!=a]
      e.place(remote_tile);after=snap(e)
      need(after['last_transition']['collision_ledger_equal'] is True and rowproof(after,1)['retain'] is True
        and all(rowproof(after,r)['retain'] is False for r in (3,4,5)),
        'existing translated prototype preserves earlier support but remote marks invalidate affected/later supports')
      need(after['row_versions'][1]==before['row_versions'][1]
        and after['row_versions'][3]>before['row_versions'][3],'retained and invalidated row versions')
      need(3 not in dict(after['certificates']) and cert(after,1)['schema']=='unit-row-transferred-domain-classification-v1',
        'affected old receipt removed, earlier checked receipt transferred')
      passed('same-UG-prototype-remote-marks-retain-earlier-invalidate-affected',{'before':before,'placement':remote_tile,'after':after})
      if old_bad:
        passed('current-illegal-old-candidate-refresh-rejected',rejected(lambda:refresh(state=copy.deepcopy(after['state']),
          candidates=[copy.deepcopy(old_bad[0])],tick=tick),'retained candidate whole current legality'))
      else:skip('current-illegal-old-candidate-refresh-rejected','No genuinely exposed alternative with distinct formula at3.')
    finally:e.rollback(token)
    restored(e,root)
    excluded_key=prepared(tile,language,{'rule':'axiom','name':names[0],'formula':a},[],[],1,tick)['placement_key']
    excluded=state(language,[ax,u2],tick,excluded=[excluded_key])
    receipt=transition(before=copy.deepcopy(small),after=copy.deepcopy(excluded),rows=[1,3],tick=tick)
    rows={x['row']:x for x in receipt['rows']}
    need(receipt['collision_ledger_equal'] is True and rows[1]['retain'] is False and rows[3]['retain'] is True,
      'local exact excluded key changes own domain; remote pending facts do not borrow row1 proof')
    passed('local-exclusion-stable-ledger-invalidates-own-row',{'before':small,'after':excluded,'transition':receipt},
      'Exact branch-local exclusion assumed as input, no justification of pruning asserted.')
    other=next((n for n in names if language.theory['axioms'][n]!=a),None)
    if other is None:skip('new-global-prototype-ledger-invalidates-all-domains','No other distinct original AX prototype.')
    else:
      b=copy.deepcopy(language.theory['axioms'][other]);e=make(small);root=snap(e);token=e.checkpoint()
      try:
        new_tile=obligations(prepared(tile,language,{'rule':'axiom','name':other,'formula':b},[],[],4,tick),small)
        e.decision();before=snap(e);e.place(new_tile);after=snap(e)
        need(after['last_transition']['collision_ledger_equal'] is False
          and all(x['retain'] is False for x in after['last_transition']['rows']),
          'new global full-preimage ledger invalidates all rows conservatively')
        need(after['certificates']==after['cursors']==after['exposed_candidates']==[]
          and all(y==x+1 for x,y in zip(before['row_versions'],after['row_versions'])),
          'no stale domain/prefix survives global ledger change')
        passed('new-global-prototype-ledger-invalidates-all-domains',{'before':before,'placement':new_tile,'after':after})
      finally:e.rollback(token)
      restored(e,root)

  initial=state(language,[],tick);bad=copy.deepcopy(initial);bad['input_epoch']='CONTROL_STALE_EPOCH'
  passed('transition-stale-epoch-rejected',rejected(lambda:transition(before=copy.deepcopy(initial),after=bad,rows=[0],tick=tick),
    'private epoch/profile'))
  passed('transition-Boolean-row-rejected',rejected(lambda:transition(before=copy.deepcopy(initial),after=copy.deepcopy(initial),
    rows=[True],tick=tick),'literal sorted distinct queried rows'))
  need(len({c['case'] for c in cases})==len(cases),'unique separately counted control IDs')
  tick()
  return {'schema':'unit-row-retained-domain-controls-v1','version':VERSION,'cases':cases,'all_declared_cases_completed':True,
    'original_height':24,'original_root_generations':0,'no_target_search_call':True,
    'scope':'Source-only controls until Root actual; original mathematical fixtures plus one explicitly interrupted replay seam.',
    'complete_candidate_graph_accepted':False,'scheduler_or_rollback_accepted':False,'logical_proof_accepted':False,
    'exact_point_board_accepted':False,'trajectory_accepted':False,'GCTS_advantage_accepted':False,
    'RL_accepted':False,'ROOT_resource_accepted':False}
