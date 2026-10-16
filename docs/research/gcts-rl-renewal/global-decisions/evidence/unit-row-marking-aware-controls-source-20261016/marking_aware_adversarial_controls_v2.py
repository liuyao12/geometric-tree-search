"""SOURCE ONLY adversarial controls; original-language fixtures and labeled seams.

No project imports, saved word/donor/library, native clock, runner or grant.
Root supplies authenticated callable endpoints and the original language.
"""
import copy
import hashlib
import json

VERSION = 'unit-row-marking-aware-adversarial-controls-v2'

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


class InterruptedCursor:
  """Control-only interruption of a REAL cursor; never synthesizes EOF/data."""
  def __init__(self, real, limit, log):
    self.real,self.limit,self.log,self.seen=real,limit,log,0
  def context(self):
    return self.real.context()
  def advance(self):
    if self.seen>=self.limit:
      self.real.abort();self.log.append({'kind':'CONTROL_INTERRUPT','after_candidates':self.seen})
      raise CallbackExhausted('declared real-cursor transport interruption')
    event=self.real.advance();self.log.append(copy.deepcopy(event))
    if event['kind']=='CANDIDATE':self.seen+=1
    return event
  def abort(self):
    return self.real.abort()


def _run_original_controls(*,language,engine_factory,degree_proposer,fallback,certify_fallback,scheduler,tick):
  """No automatic target search; one explicitly incomplete bounded search seam."""
  cases=[];outside=language.OutsideLanguage
  local='Original-language unit placements/pending obligations; no logical proof.'
  seam='CONTROL-ONLY incomplete real-cursor/proposal transport; no completeness evidence.'
  def passed(name,observed,scope=local):
    tick();cases.append({'case':name,'status':'PASSED','observed':copy.deepcopy(observed),'scope':scope})
  def skipped(name,reason):
    cases.append({'case':name,'status':'SKIPPED','observed':{'reason':reason},'scope':'Unavailable fixture; gap retained.'})
  def prepared(fn,*args):
    try:return fn(*args)
    except outside as error:
      if type(error) is not outside:raise
      raise Unavailable('Original fixture membership exclusion: '+str(error))
  def make(s,dp=None,fb=None,cert='CURRENT'):
    return engine_factory(initial_state=copy.deepcopy(s),degree_proposer=degree_proposer if dp is None else dp,
      fallback=fallback if fb is None else fb,certify_fallback=certify_fallback if cert=='CURRENT' else cert,tick=tick)
  def snapshot(e):
    value=e.state_snapshot()
    need(value['state']['generation']==[[[0,r],0] for r in range(24)],'all original root generations zero')
    return value
  def unchanged(e,before,name):
    after=snapshot(e);need(canonical(after)==canonical(before),name+' exact full logical rollback')
    return after
  def drain(e,row,limit=4):
    values=[]
    for _ in range(limit):
      tick();event=e.next_alternative(row)
      if event['kind']=='EOF':return values,event['completion']
      need(event['kind']=='CANDIDATE','literal cursor event');values.append(event['candidate'])
    raise AssertionError('fixture cursor did not reach real EOF within declared tiny bound')
  def expected_value_error(name,call,contains=None):
    reason=None
    try:call()
    except ValueError as error:
      if type(error) is not ValueError:raise
      reason=str(error)
    need(reason is not None,name+' genuine ValueError rejection')
    if contains is not None:need(contains in reason,name+' expected rejection edge')
    return {'exception_type':'ValueError','reason':reason}
  def unknown_hint(**kwargs):
    # Suppression only: preserve complete current binding/state/false flags.
    p=copy.deepcopy(degree_proposer(**kwargs));p['kind']='UNKNOWN';p['candidates']=[]
    p['coverage']=None;p['rejections']=[];p['complete_cover_proposed']=False
    if p['fibre_cover'] is not None:p['fibre_cover']['completed']=False
    return p
  def interrupted(limit,log,only_child=False):
    def open_cursor(**kwargs):
      real=fallback(**kwargs)
      if only_child and not kwargs['state']['selected']:return real
      return InterruptedCursor(real,limit,log)
    return open_cursor

  initial=state(language,[],tick)
  names=sorted(language.theory['axioms']);variables=[v for v in language.parameters if v not in language.forbidden]
  roots=list(language.theory['axioms'].values())+list(language.gamma)
  bot=['bot'];bottom_absent=not any(f==bot for f in roots)
  if not variables or not names:
    for name in ('late-global-ZERO-before-earlier-singleton','global-forced-before-branch',
      'real-EOF-singleton-without-independent-cover-UNKNOWN','real-EOF-singleton-current-cover-FORCED',
      'interrupted-zero-prefix-not-ZERO','interrupted-one-prefix-not-SINGLETON'):
      skipped(name,'No original named AX or Gamma-eligible parameter.')
  else:
    v=variables[0];a=copy.deepcopy(language.theory['axioms'][names[0]])
    root_count=sum(f==a for f in roots)
    try:
      single_s=state(language,[prepared(ug,language,a,v,0,1,tick)],tick)
      if root_count!=1:raise Unavailable('Chosen original formula has multiple AX/Gamma occurrences.')
      if not bottom_absent:raise Unavailable('Original bottom root blocks late ZERO fixture.')
      late_s=state(language,[prepared(ug,language,a,v,0,1,tick),prepared(ug,language,bot,v,2,4,tick)],tick)
      e=make(late_s);before=snapshot(e);d=e.decision();after=snapshot(e)
      certs=dict(after['certificates'])
      need(d=={'kind':'DEAD','row':2} and certs[0]['status']=='SINGLETON'
        and certs[2]['status']=='ZERO','global later zero beats earlier singleton')
      need(canonical(before['state'])==canonical(after['state']),'decision does not place singleton')
      passed('late-global-ZERO-before-earlier-singleton',{'decision':d,'before':before,'after':after})
      e=make(single_s);before=snapshot(e);d=e.decision();after=snapshot(e)
      need(d['kind']=='FORCED' and d['row']==0,'global forced move before any branch')
      need(canonical(before['state'])==canonical(after['state']),'decision only classifies')
      passed('global-forced-before-branch',{'decision':d,'before':before,'after':after})

      # Exact real EOF is still not its own 0/1 authority.
      e=make(single_s,dp=unknown_hint,cert=None);d=e.decision();after=snapshot(e)
      slot=dict(after['cursors'])[0]
      need(d['kind']=='UNKNOWN' and len(slot['keys'])==1 and slot['completion'] is not None,
        'real singleton EOF without independent cover remains UNKNOWN')
      passed('real-EOF-singleton-without-independent-cover-UNKNOWN',{'decision':d,'snapshot':after},seam)
      e=make(single_s,dp=unknown_hint);d=e.decision();after=snapshot(e)
      need(d['kind']=='FORCED' and d['row']==0 and dict(after['certificates'])[0]['complete_cover_checked'] is True,
        'fresh completed independent cover permits singleton after real EOF')
      passed('real-EOF-singleton-current-cover-FORCED',{'decision':d,'snapshot':after},seam)
      for cap,label in ((0,'interrupted-zero-prefix-not-ZERO'),(1,'interrupted-one-prefix-not-SINGLETON')):
        log=[];e=make(single_s,dp=unknown_hint,fb=interrupted(cap,log));reason=None
        try:e.decision()
        except CallbackExhausted as error:
          if type(error) is not CallbackExhausted:raise
          reason=str(error)
        need(reason is not None and not any(x['kind']=='EOF' for x in log),'interruption cannot synthesize EOF')
        need(sum(x['kind']=='CANDIDATE' for x in log)==cap,'exact declared interruption prefix')
        passed(label,{'exception_type':'CallbackExhausted','reason':reason,'actual_cursor_events':log,
          'snapshot':snapshot(e)},seam)
    except Unavailable as error:
      for name in ('late-global-ZERO-before-earlier-singleton','global-forced-before-branch',
        'real-EOF-singleton-without-independent-cover-UNKNOWN','real-EOF-singleton-current-cover-FORCED',
        'interrupted-zero-prefix-not-ZERO','interrupted-one-prefix-not-SINGLETON'):
        if not any(c['case']==name for c in cases):skipped(name,type(error).__name__+': '+str(error))

  if not variables or not bottom_absent:
    for name in ('unseen-remote-key-invalidated','remote-singleton-stream-cover-key-agreement',
      'rollback-revives-unseen-key-and-cursor-position','exact-ordered-child-alternatives-and-restoration',
      'omitted-stream-survivor-rejected','assumed-exclusions-change-context-not-universe'):
      skipped(name,'Need eligible original parameter and no original bottom root.')
  else:
    v=variables[0];c=bot
    for _ in range(41):c=['not',c]
    try:
      # Fixed original bounds imply antecedent maximum1 here; no bounded model is replaced.
      need(prepared(language.formula,copy.deepcopy(c))==42,'deep fixture exact formula nodes42')
      if any(f==c for f in roots):raise Unavailable('Deep fixture coincides with original AX/Gamma root.')
      if language.theory.get('predicates'):raise Unavailable('Tiny two-MP reference requires no original predicates.')
      deep_s=state(language,[prepared(ug,language,c,v,2,3,tick)],tick)
      mp=[]
      for i,j in ((0,1),(1,0)):
        witness={'rule':'mp','formula':copy.deepcopy(c)}
        mp.append(obligations(prepared(tile,language,witness,[bot,['imp',bot,copy.deepcopy(c)]],[i,j],2,tick),deep_s))
      e=make(deep_s);first=e.next_alternative(2)
      need(first['kind']=='CANDIDATE' and canonical(first['candidate'])==canonical(mp[0]),'first exact ordered MP key')
      before=snapshot(e);token=e.checkpoint()
      need(len(before['exposed_candidates'])==1 and len(dict(before['cursors'])[2]['keys'])==1,'reverse key is genuinely unseen')
      remote=obligations(prepared(ug,language,bot,v,0,4,tick),deep_s)
      e.place(remote);changed=snapshot(e)
      need(changed['revision']==before['revision']+1 and all(b==a+1 for a,b in zip(before['row_versions'],changed['row_versions'])),
        'remote change invalidates every implicit context version')
      need(changed['cursors']==[] and changed['certificates']==[] and changed['exposed_candidates']==[],
        'unseen alternatives cannot survive stale cached context')
      rejection=expected_value_error('remote old reverse key',lambda:e.place(mp[1]),'whole original point legality')
      passed('unseen-remote-key-invalidated',{'first_checked':first,'before':before,'remote':remote,
        'after':changed,'stale_reverse_rejection':rejection})
      survivors,completion=drain(e,2)
      need(len(survivors)==1 and canonical(survivors[0]['placement_key'])==canonical(mp[0]['placement_key']),
        'remote bottom mark removes exactly reversed read placement')
      current=snapshot(e)['state']
      receipt=certify_fallback(language=language,state=copy.deepcopy(current),row=2,
        completion=copy.deepcopy(completion),checked_candidates=copy.deepcopy(survivors),tick=tick)
      need(receipt is not None and receipt['status']=='SINGLETON' and receipt['complete_cover_checked'] is True,
        'real EOF one survives only with fresh independent completed cover')
      passed('remote-singleton-stream-cover-key-agreement',{'state':current,'checked_candidates':survivors,
        'completion':completion,'independent_receipt':receipt})
      rejection=expected_value_error('omitted stream survivor',lambda:certify_fallback(language=language,
        state=copy.deepcopy(current),row=2,completion=copy.deepcopy(completion),checked_candidates=[],tick=tick),
        'complete cover agrees')
      passed('omitted-stream-survivor-rejected',rejection)
      e.rollback(token);after=unchanged(e,before,'remote child')
      second=e.next_alternative(2)
      need(second['kind']=='CANDIDATE' and canonical(second['candidate'])==canonical(mp[1]),'rollback replays saved prefix then unseen reverse')
      final=e.next_alternative(2);need(final['kind']=='EOF','actual two-key stream EOF')
      passed('rollback-revives-unseen-key-and-cursor-position',{'restored':after,'second':second,'EOF':final,
        'cursor_replays_observed':e.counts['cursor_replays']},'Original membership/transaction mechanics; EOF alone not exact-degree authority.')

      e=make(deep_s);children=[]
      for expected in mp:
        event=e.next_alternative(2);need(event['kind']=='CANDIDATE' and canonical(event['candidate'])==canonical(expected),
          'canonical ordered parent alternatives')
        before=snapshot(e);token=e.checkpoint();e.place(event['candidate']);d=e.decision()
        need(d['kind']=='DEAD','each bottom-obligation child has a fresh certified global dead row')
        child=snapshot(e);e.rollback(token);after=unchanged(e,before,'ordered child')
        children.append({'alternative':event,'decision':d,'child':child,'before':before,'restored':after})
      need(e.next_alternative(2)['kind']=='EOF','two real ordered alternatives then EOF')
      passed('exact-ordered-child-alternatives-and-restoration',{'children':children},
        'Policy-independent public place/rollback mechanics; not a reference-scheduled branch trace.')
      excluded=copy.deepcopy(deep_s);excluded['excluded']=[copy.deepcopy(mp[1]['placement_key'])]
      e=make(excluded);items,comp=drain(e,2)
      need(len(items)==1 and canonical(items[0]['placement_key'])==canonical(mp[0]['placement_key']),
        'exact full-key branch exclusion only')
      need(comp['state_sha256']==digest(excluded) and comp['state_sha256']!=digest(deep_s),'exclusion binds new full context')
      passed('assumed-exclusions-change-context-not-universe',{'state':excluded,'stream':items,'completion':comp},
        'Assumed branch-local exclusion control; justification is not asserted.')
    except Unavailable as error:
      for name in ('unseen-remote-key-invalidated','remote-singleton-stream-cover-key-agreement',
        'rollback-revives-unseen-key-and-cursor-position','exact-ordered-child-alternatives-and-restoration',
        'omitted-stream-survivor-rejected','assumed-exclusions-change-context-not-universe'):
        if not any(x['case']==name for x in cases):skipped(name,type(error).__name__+': '+str(error))

  # This is the only search() call: a declared incomplete child-transport seam.
  if len(names)<2:skipped('UNKNOWN-child-never-excluded','Need two original named AX witnesses.')
  else:
    log=[]
    def child_unknown(**kwargs):
      return unknown_hint(**kwargs) if kwargs['state']['selected'] else degree_proposer(**kwargs)
    e=make(initial,dp=child_unknown,fb=interrupted(0,log,only_child=True))
    before=snapshot(e);result=e.search();after=unchanged(e,before,'UNKNOWN search child')
    need(result['schema']=='unit-row-lazy-global-search-result-v1' and result['status']=='UNKNOWN'
      and result['found'] is None and result['root_restored'] is True,'incomplete child returns UNKNOWN, not exhaustion')
    need(result['counts']['branches']>=1 and any(x['kind']=='TRY' for x in result['events'])
      and any(x['kind']=='CONTROL_INTERRUPT' for x in log),'a real original child was attempted before interruption')
    need(not any(x['kind']=='EXCLUDE' for x in result['events']) and after['state']['excluded']==[],
      'UNKNOWN child never becomes proved parent exclusion')
    passed('UNKNOWN-child-never-excluded',{'before':before,'restored':after,'actual_cursor_events':log,
      'bounded_search_result':result},seam+' One intentionally interrupted engine search; not target discovery.')

  # Original cursor lifetime mechanics, without replacing native tick or EOF.
  gate={'armed':False}
  def injected_tick():
    tick()
    if gate['armed']:raise CallbackExhausted('declared cursor callback exhaustion')
  real=fallback(language=language,state=copy.deepcopy(initial),row=0,tick=injected_tick)
  context=real.context();gate['armed']=True;first_reason=None
  try:real.advance()
  except CallbackExhausted as error:
    if type(error) is not CallbackExhausted:raise
    first_reason=str(error)
  gate['armed']=False;second_reason=None
  try:real.advance()
  except RuntimeError as error:
    if type(error) is not RuntimeError:raise
    second_reason=str(error)
  need(first_reason is not None and second_reason is not None,'failed cursor cannot later produce EOF')
  passed('callback-exhaustion-poisons-real-cursor',{'context':context,'first':first_reason,'later':second_reason},seam)
  real=fallback(language=language,state=copy.deepcopy(initial),row=0,tick=tick);context=real.context();real.abort();reason=None
  try:real.advance()
  except RuntimeError as error:
    if type(error) is not RuntimeError:raise
    reason=str(error)
  need(reason is not None,'aborted cursor cannot later produce EOF')
  passed('abort-poisons-real-cursor',{'context':context,'reason':reason},seam)

  # Isolated scheduler inputs are NOT altered production generations or fake certificates.
  evidence={0:{'status':'MANY','degree_exact':10},1:{'status':'MANY','degree_exact':2}}
  d=scheduler(evidence=copy.deepcopy(evidence),generations={0:0,1:1},tick=tick)
  need(d=={'kind':'BRANCH','row':0},'earliest generation outranks later smaller degree')
  tied=scheduler(evidence=copy.deepcopy(evidence),generations={0:0,1:0},tick=tick)
  need(tied=={'kind':'BRANCH','row':0},'named ROW-TIE, not historical min-count tie')
  passed('synthetic-varied-generation-and-ROW-TIE',{'abstract_evidence':evidence,'generations':[[0,0],[1,1]],
    'decision':d,'same_generation_decision':tied},'NONLOGICAL pure scheduler kernel; no original-model varied generations.')
  d=scheduler(evidence={0:{'status':'SINGLETON'},1:{'status':'ZERO'}},generations={0:0,1:9},tick=tick)
  need(d=={'kind':'DEAD','row':1},'synthetic global dead before forced')
  u=scheduler(evidence={0:{'status':'SINGLETON'},1:{'status':'UNKNOWN'}},generations={0:0,1:9},tick=tick)
  need(u['kind']=='UNKNOWN','unresolved frontier prevents forced decision')
  passed('synthetic-global-priority-with-UNKNOWN',{'dead_decision':d,'unresolved_decision':u},
    'NONLOGICAL scheduler status mechanics, separate from genuine original-language fixtures.')
  need(len({x['case'] for x in cases})==len(cases),'unique declared case names')
  tick()
  return {'schema':'unit-row-lazy-global-controls-v1','version':VERSION,'cases':cases,
    'all_declared_cases_completed':True,'original_height':24,'original_root_generations':0,
    'variant':'GLOBAL-DEAD-FORCED-EARLIEST-GENERATION-ROW-TIE',
    'scope':'Genuine original-language transactions plus explicitly labeled adversarial seams; no target search result.',
    'complete_candidate_graph_accepted':False,'scheduler_or_rollback_accepted':False,
    'logical_proof_accepted':False,'exact_point_board_accepted':False,'GCTS_advantage_accepted':False,
    'trajectory_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}


def run_controls(*,language,engine_factory,degree_proposer,fallback,certify_fallback,scheduler,tick):
  """Original seventeen ROW controls plus six separately counted policy controls.

  No target discovery call is added. All original-language decisions retain the
  complete current degree/fallback/independent-checker path. Pure kernel inputs
  below are explicitly NONLOGICAL, not substituted live certificates.
  """
  result=_run_original_controls(language=language,engine_factory=engine_factory,
    degree_proposer=degree_proposer,fallback=fallback,certify_fallback=certify_fallback,
    scheduler=scheduler,tick=tick)
  cases=result['cases'];need(len(cases)==17,'all original seventeen cases retained')
  original_names=[c['case'] for c in cases]
  policy='ASSIGNED-OUTPUT-THEN-ROW'
  new_names=('mark-tie-synthetic-generation-and-row',
    'mark-tie-synthetic-global-priority',
    'mark-tie-original-ROW-versus-assigned-output-BRANCH',
    'mark-tie-original-readonly-decision-and-checkpoint',
    'mark-tie-original-occupied-output-retie-and-rollback',
    'mark-tie-original-global-DEAD-and-FORCED')
  local='Original AX/UG unit placements and pending formula constraints; no logical proof or target trajectory.'
  abstract='NONLOGICAL pure scheduler inputs; no production generations/certificates are replaced.'
  def passed(name,observed,scope=local):
    tick();cases.append({'case':name,'status':'PASSED','observed':copy.deepcopy(observed),'scope':scope})
  def skipped(name,reason):
    tick();cases.append({'case':name,'status':'SKIPPED','observed':{'reason':reason},
      'scope':'Definite original fixture ineligibility; new policy coverage gap retained.'})
  def make(s,branch_tie):
    return engine_factory(initial_state=copy.deepcopy(s),degree_proposer=degree_proposer,
      fallback=fallback,certify_fallback=certify_fallback,tick=tick,branch_tie=branch_tie)
  def snap(e):
    value=e.state_snapshot()
    need(value['state']['generation']==[[[0,r],0] for r in range(24)],'original roots remain generation zero')
    return value
  def same(a,b,reason):
    need(canonical(a)==canonical(b),reason)
  def logical_same(before,after):
    same(before['state'],after['state'],'decision is logically read-only, not a placement')
  def schedule(evidence,generations,assigned):
    return scheduler(evidence=copy.deepcopy(evidence),generations=copy.deepcopy(generations),
      branch_tie=policy,assigned_output_rows=copy.deepcopy(assigned),tick=tick)

  evidence={0:{'status':'MANY','degree_exact':10},1:{'status':'MANY','degree_exact':2},
    2:{'status':'TWO_OR_MORE','degree_exact':None}}
  early=schedule(evidence,{0:0,1:1,2:1},[1,2])
  marked=schedule(evidence,{0:0,1:0,2:0},[2])
  tied=schedule(evidence,{0:0,1:0,2:0},[1,2])
  absent=schedule(evidence,{0:0,1:0,2:0},[])
  need(early=={'kind':'BRANCH','row':0},'assigned later generation cannot outrank earliest absent')
  need(marked=={'kind':'BRANCH','row':2},'assigned output wins only within earliest generation')
  need(tied=={'kind':'BRANCH','row':1} and absent=={'kind':'BRANCH','row':0},
    'literal row resolves assigned/absent class ties, not minimum degree')
  passed(new_names[0],{'abstract_evidence':evidence,'earlier_generation':early,
    'assigned_same_generation':marked,'two_assigned':tied,'all_absent':absent},abstract)
  dead=schedule({0:{'status':'SINGLETON'},1:{'status':'ZERO'}},{0:0,1:9},[0])
  forced=schedule({0:{'status':'MANY'},1:{'status':'SINGLETON'}},{0:0,1:9},[0])
  unresolved=schedule({0:{'status':'SINGLETON'},1:{'status':'UNKNOWN'}},{0:0,1:9},[0])
  need(dead=={'kind':'DEAD','row':1},'global dead before marked forced')
  need(forced=={'kind':'FORCED','row':1},'global forced before earlier marked branch')
  need(unresolved=={'kind':'UNKNOWN','row':None,'unresolved_rows':[1]},'unknown does not become forced')
  passed(new_names[1],{'dead':dead,'forced':forced,'unresolved':unresolved},abstract)

  outside=language.OutsideLanguage
  def prepared(fn,*args):
    try:return fn(*args)
    except outside as error:
      if type(error) is not outside:raise
      raise Unavailable('Original fixture membership exclusion: '+str(error))
  names=sorted(language.theory['axioms'])
  variables=[v for v in language.parameters if v not in language.forbidden]
  try:
    if len(names)<2 or not variables:
      raise Unavailable('Need two original named AX witnesses and an eligible original parameter.')
    v=variables[0];a=copy.deepcopy(language.theory['axioms'][names[0]])
    d=['all',v,copy.deepcopy(a)]
    # Rows 0 and 5 stay absent. Distinct original AX occurrences at 1 and 2
    # give actual UG alternatives for the pending outputs at rows 3 and 6.
    seed=[prepared(tile,language,{'rule':'axiom','name':names[0],'formula':copy.deepcopy(a)},[],[],r,tick)
      for r in (1,2)]
    seed.extend([prepared(ug,language,d,v,3,4,tick),prepared(ug,language,d,v,6,7,tick)])
    initial=state(language,seed,tick)
    row_engine=make(initial,'ROW');row_before=snap(row_engine)
    row_decision=row_engine.decision();row_after=snap(row_engine)
    logical_same(row_before,row_after)
    need(row_decision=={'kind':'BRANCH','row':0},'actual original ROW baseline selects unmarked row zero')
    e=make(initial,policy);cold=snap(e);outer=e.checkpoint()
    try:
      mark_decision=e.decision();warm=snap(e)
      logical_same(cold,warm)
      need(mark_decision=={'kind':'BRANCH','row':3},'actual current global MARK branch selects first assigned output')
      marks={tuple(p):value for p,value in warm['state']['m']}
      need((1,0) not in marks and marks[(1,3)]==['formula',canonical(d)]
        and marks[(1,6)]==['formula',canonical(d)],'genuine absent-versus-assigned formula distinction')
      certificates=dict(warm['certificates'])
      need(certificates[0]['status'] in ('MANY','TWO_OR_MORE')
        and certificates[3]['status'] in ('MANY','TWO_OR_MORE')
        and certificates[6]['status'] in ('MANY','TWO_OR_MORE'),
        'real independently checked local lower bounds, no fabricated degree')
      passed(new_names[2],{'seed':seed,'initial_state':initial,'ROW_decision':row_decision,
        'ROW_snapshot':row_after,'MARK_decision':mark_decision,'MARK_snapshot':warm})
      inner=e.checkpoint()
      try:
        again=e.decision();again_snapshot=snap(e)
        need(again==mark_decision,'same current decision on repeated read')
        same(again_snapshot,warm,'warm full logical/cache snapshot unchanged by repeated classification')
      finally:
        e.rollback(inner)
      same(snap(e),warm,'owned warm checkpoint exact cache/context/receipt restoration')
      passed(new_names[3],{'cold':cold,'warm':warm,'repeated_decision':again,
        'repeated_snapshot':again_snapshot,'restored_warm':snap(e)},
        local+' Decision may populate caches/counters/events; the logical state is read-only and public snapshot excludes cumulative diagnostics.')
      token=e.checkpoint()
      fill=obligations(prepared(ug,language,a,v,1,3,tick),warm['state'])
      try:
        e.place(fill);changed=snap(e);next_decision=e.decision();classified=snap(e)
        need(next_decision=={'kind':'BRANCH','row':6},'occupied assigned row removed, next assigned output selected')
        logical_same(changed,classified)
      finally:
        e.rollback(token)
      restored=snap(e);same(restored,warm,'whole warm snapshot restored after legal fill')
      final_decision=e.decision();same(snap(e),warm,'rollback continuation keeps exact current classification cache')
      need(final_decision==mark_decision,'restored assigned output wins again')
      passed(new_names[4],{'fill':fill,'changed':changed,'next_decision':next_decision,
        'classified':classified,'restored':restored,'restored_decision':final_decision},
        local+' Policy-independent public place transaction, not a claimed scheduled search trajectory.')
    finally:
      e.rollback(outer)
    same(snap(e),cold,'owned cold checkpoint restores whole initial snapshot after all decision work')
  except Unavailable as error:
    for name in new_names[2:5]:
      if not any(c['case']==name for c in cases):skipped(name,str(error))

  try:
    if not names or not variables:raise Unavailable('Need original AX and eligible original parameter.')
    v=variables[0];a=copy.deepcopy(language.theory['axioms'][names[0]])
    roots=list(language.theory['axioms'].values())+list(language.gamma)
    if sum(f==a for f in roots)!=1 or any(f==['bot'] for f in roots):
      raise Unavailable('Need one exact original AX/Gamma occurrence and no bottom root.')
    forced_state=state(language,[prepared(ug,language,a,v,0,1,tick)],tick)
    dead_state=state(language,[prepared(ug,language,a,v,0,1,tick),prepared(ug,language,['bot'],v,2,4,tick)],tick)
    observed=[]
    for s,kind,row in ((dead_state,'DEAD',2),(forced_state,'FORCED',0)):
      e=make(s,policy);before=snap(e);token=e.checkpoint()
      try:
        decision=e.decision();after=snap(e)
        need(decision['kind']==kind and decision['row']==row,'actual MARK global dead/forced priority')
        logical_same(before,after)
        observed.append({'before':before,'decision':decision,'after':after})
      finally:
        e.rollback(token)
      same(snap(e),before,'priority decision owned checkpoint restores full snapshot')
    passed(new_names[5],{'decisions':observed})
  except Unavailable as error:
    skipped(new_names[5],str(error))
  need([c['case'] for c in cases[:17]]==original_names,'original case meanings/order retained')
  need(len(cases)==23 and {c['case'] for c in cases[17:]}==set(new_names),'separate six controls, no relabeled pass')
  need(len({c['case'] for c in cases})==23,'unique prospective case names')
  result.update(version=VERSION,variant='ROW-BASELINE-AND-ASSIGNED-OUTPUT-BRANCH-TIE-CONTROLS',
    original_case_count=17,new_policy_case_count=6,prospective_case_count=23,
    scope='Seventeen unchanged ROW controls plus six separately counted marking-aware policy controls; no target result.')
  tick()
  return result
