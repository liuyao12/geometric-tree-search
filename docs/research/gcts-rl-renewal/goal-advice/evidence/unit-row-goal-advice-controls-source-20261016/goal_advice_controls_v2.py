"""SOURCE ONLY genuine goal-advice/consumer component controls.

No project imports, saved proof/library, native clocks or activation. All
scientific endpoints are caller-authenticated delegates; malformed packets and
interruptions below are explicit control seams, never candidate/EOF oracles.
"""
import copy
import hashlib
import json

VERSION = 'unit-row-goal-advice-adversarial-controls-v2-preserved-advice-diagnostics'
STRONG_FLAGS = ('logical_proof_accepted', 'exact_point_board_accepted',
    'degree_or_EOF_accepted', 'scheduler_accepted', 'complete_GCTS_model_accepted',
    'trajectory_accepted', 'learned_marking_accepted', 'RL_accepted', 'ROOT_resource_accepted')

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


def run_controls(*,language,engine_factory,adviser,validate_advice,degree_proposer,
                 fallback,certify_fallback,tick):
  """Actual original-language components; no target proof search benchmark.

  Endpoint kwargs follow the contract. The factory injects original semantics
  and permits only the declared callback overrides. No private engine attribute,
  fabricated degree/candidate universe, EOF or pending family is used here.
  """
  cases=[];artifacts={};coverage_gaps=[];outside=language.OutsideLanguage
  local='Original-language advisory component; no proof, complete graph, trajectory, benefit or RL authority.'
  seam='CONTROL-ONLY malformed data, hint suppression or native-first interruption; original universe unchanged.'
  def passed(name,value,scope=local):
    tick();cases.append({'case':name,'status':'PASSED','observed':copy.deepcopy(value),'scope':scope})
  def skip(name,reason):
    cases.append({'case':name,'status':'SKIPPED','observed':{'reason':str(reason)},
      'scope':'Eligibility gap retained; this consumer gate is not qualified.'})
  def prepared(fn,*args):
    try:return fn(*args)
    except outside as error:
      if type(error) is not outside:raise
      raise Unavailable('Original fixture outside current profile: '+str(error))
  def reject(call):
    tick();reason=None
    try:call()
    except ValueError as error:
      if type(error) is not ValueError:raise
      reason=str(error)
    tick();need(reason is not None,'declared malformed control genuinely rejected')
    return {'exception_type':'ValueError','reason':reason}
  def snap(e):
    value=e.state_snapshot()
    need(value['state']['generation']==[[[0,r],0] for r in range(24)],'original all24 root generations')
    return value
  def restored(e,before):
    after=snap(e);need(canonical(after)==canonical(before),'exact entire public snapshot restoration')
    return {'before_sha256':digest(before),'after_sha256':digest(after)}
  def make(s,dp=None,adv=None,validator=None):
    return engine_factory(initial_state=copy.deepcopy(s),degree_proposer=degree_proposer if dp is None else dp,
      fallback=fallback,certify_fallback=certify_fallback,branch_adviser=adv,
      validate_advice=validate_advice if validator is None and adv is not None else validator,tick=tick)
  def current_advice(**kwargs):
    return adviser(**kwargs,maximum_terms=1,maximum_demands=16,maximum_rounds=4,maximum_proposals=8)
  def check(s,d,b,step=tick):
    return validate_advice(state=copy.deepcopy(s),decision=copy.deepcopy(d),batch=copy.deepcopy(b),tick=step)
  def receipt_flags(receipt):
    need(all(receipt[k] is False for k in STRONG_FLAGS),'all independent receipt authority flags remain false')
    return receipt
  def first_key(s,row):
    cursor=fallback(language=language,state=copy.deepcopy(s),row=row,tick=tick)
    try:
      context=cursor.context();event=cursor.advance()
      need(event['kind']=='CANDIDATE' and event['ordinal']==0,'genuine canonical first candidate, not EOF')
      return {'context':context,'event':event}
    finally:cursor.abort()
  def unknown_result(e,before,result):
    need(result['status']=='UNKNOWN' and result['root_restored'] is True and result['stack_restored'] is True,
      'declared interruption is UNKNOWN with root and stack restored')
    need(result['found'] is None and not any(x['kind']=='EXCLUDE' for x in result['events']),
      'UNKNOWN never produces proof or child exclusion')
    restored(e,before)
  def first_try(result):
    return next(x for x in result['events'] if x['kind']=='TRY')
  def empty_advice(**kwargs):
    # Explicit suppression of hints only, after a real current READY proposal.
    value=current_advice(**kwargs)
    need(value['status']=='READY','hint-suppression seam requires genuine completed READY batch')
    value=copy.deepcopy(value);value['proposals']=[]
    return value
  def quota_advice(**kwargs):
    value=adviser(**kwargs,maximum_work=1,maximum_terms=1,maximum_demands=1,maximum_rounds=1,maximum_proposals=1)
    need(value['status']=='UNKNOWN','genuine finite advisory quota returns UNKNOWN')
    return value
  def stop_after_placement(s,adv,validator=None):
    holder={'engine':None,'child_snapshot':None}
    def observed_degree(**kwargs):
      tick()
      if len(kwargs['state']['selected'])>len(s['selected']):
        holder['child_snapshot']=snap(holder['engine'])
        raise CallbackExhausted('declared stop after one actual original placement')
      return degree_proposer(**kwargs)
    e=make(s,observed_degree,adv,validator);holder['engine']=e
    before=snap(e);value=e.search();unknown_result(e,before,value)
    need(holder['child_snapshot'] is not None,'actual placed child observed before interruption')
    return value,holder['child_snapshot']

  initial=state(language,[],tick)
  names=sorted(language.theory['axioms']);variables=[v for v in sorted(language.parameters) if v not in language.forbidden]
  roots=[language.theory['axioms'][n] for n in names]+list(language.gamma)
  fixture_error=None
  try:
    if not variables:raise Unavailable('No Gamma-eligible declared parameter for generic UG fixture.')
    v=variables[0]
    universals=[(n,language.theory['axioms'][n]) for n in names if language.theory['axioms'][n][0]=='all']
    if not universals:raise Unavailable('No original universal AX for generic UI/MP/UG preference fixture.')
    name,u=universals[0];u=copy.deepcopy(u)
    body=prepared(language.substitute,u[2],u[1],['var',v])
    demand=['all',v,copy.deepcopy(body)]
    future=prepared(ug,language,demand,v,8,9,tick)
    s=state(language,[future],tick)
    e=make(s);decision=e.decision()
    if decision!={'kind':'BRANCH','row':0}:raise Unavailable('Original scheduler did not choose row0 BRANCH: '+canonical(decision))
    before=canonical(s);batch=current_advice(state=copy.deepcopy(s),decision=decision,tick=tick)
    # Preserve the WHOLE actual return before eligibility can skip controls.
    # UNKNOWN partial proposals/counters are diagnostic only, never executable.
    artifacts['fixture_advice_attempt']={'schema':'unit-row-fixture-advice-attempt-v1',
      'state':copy.deepcopy(s),'decision':copy.deepcopy(decision),
      'actual_adviser_return':copy.deepcopy(batch),'diagnostic_only':True,
      'authority_accepted':False,
      'pre_advice_state_sha256':hashlib.sha256(before.encode()).hexdigest(),
      'derived_from':{'AX_name':name,'eligible_parameter':v,'UI_instance':copy.deepcopy(body),
        'selected_future_UG':copy.deepcopy(future)}}
    if batch['status']!='READY' or not batch['proposals']:
      raise Unavailable('Actual bounded adviser returned no current READY proposal: '+str(batch['status']))
    receipt=receipt_flags(check(s,decision,batch))
    need(canonical(s)==before,'adviser and independent validator do not alter fixture state')
    need(receipt['selection'] is not None,'genuine READY first anchor validated')
    artifacts['fixture']={'state':s,'decision':decision,'batch':batch,'receipt':receipt,
      'derived_from':{'AX_name':name,'eligible_parameter':v,'UI_instance':body,'selected_future_UG':future}}
  except Unavailable as error:fixture_error=str(error)

  common_names=('genuine-READY-whole-independent-validation','pending-obligations-never-facts',
    'malformed-batch-controls','later-ranked-malformed-proposal-rejected','genuine-quota-UNKNOWN-diagnostic-only',
    'UNKNOWN-rejected-by-executable-validator','empty-hints-preserve-canonical-choice',
    'quota-UNKNOWN-preserves-canonical-choice','adviser-Timeout-UNKNOWN-no-exclusion',
    'adviser-ValueError-propagates','validator-ValueError-propagates',
    'actual-anchor-only-no-future-preinstallation','first-search-exact-root-restoration',
    'public-rollback-restores-genuine-nonempty-pending','pending-key-real-current-row-selection',
    'pending-search-exact-inner-root-restoration','remote-mark-invalidates-pending-key',
    'rejected-pending-hint-preserves-canonical-choice','pending-request-malformed-controls',
    'global-forced-fill-retires-family-before-fresh-advice')
  if fixture_error is not None:
    for label in common_names:skip(label,fixture_error)
  else:
    passed(common_names[0],{'artifact':'fixture','validated_proposals':len(batch['proposals'])})
    obligations_seen=[o for p in batch['proposals'] for o in p['ordered_PENDING_obligations']]
    need(all(o['status']=='PENDING' and o['fact_accepted'] is False for o in obligations_seen),'every external obligation remains unproved')
    need(all(p['installed'] is False and p['logical_proof_accepted'] is False for p in batch['proposals']),
      'no future member or proposed family installed as fact')
    if obligations_seen:
      passed(common_names[1],{'artifact':'fixture','obligation_occurrences':len(obligations_seen),
        'meaning':'Repeated observations, not distinct facts or causal reuse.'})
    else:skip(common_names[1],'Actual returned proposals have no external PENDING obligation to exercise.')

    mutations=[]
    def bad(label,edit):
      b=copy.deepcopy(batch);edit(b);mutations.append({'mutation':label,'result':reject(lambda:check(s,decision,b))})
    bad('stale-whole-binding',lambda b:b['binding'].__setitem__('language_epoch','0'*64))
    bad('stale-whole-state-hash',lambda b:b.__setitem__('state_sha256','0'*64))
    bad('wrong-scheduler-row',lambda b:b['decision'].__setitem__('row',1))
    bad('forged-anchor-key',lambda b:b['proposals'][0]['anchor_full_key'].__setitem__('tile_type_id','forged'))
    bad('forged-member-mark',lambda b:b['proposals'][0]['members'][0]['candidate']['global_m_values'][0].__setitem__(1,['formula','forged']))
    bad('duplicate-full-member-identity',lambda b:b['proposals'][0]['members'].append(copy.deepcopy(b['proposals'][0]['members'][0])))
    bad('forged-installed-family',lambda b:b['proposals'][0].__setitem__('installed',True))
    bad('forged-proof-authority',lambda b:b.__setitem__('logical_proof_accepted',True))
    port_locations=[(p,i) for p in range(len(batch['proposals'])) for i,m in enumerate(batch['proposals'][p]['members']) if m['ordered_ports']]
    if port_locations:
      p,i=port_locations[0]
      bad('circular-ordered-port',lambda b:b['proposals'][p]['members'][i]['ordered_ports'][0].update(
        kind='member',index=i,row=b['proposals'][p]['members'][i]['candidate']['placement_key']['translation'][1]))
      bad('future-ordered-port',lambda b:b['proposals'][p]['members'][i]['ordered_ports'][0].__setitem__('row',23))
      pairs=[(p,i) for p in range(len(batch['proposals'])) for i,m in enumerate(batch['proposals'][p]['members']) if len(m['ordered_ports'])>=2]
      if pairs:
        p,i=pairs[0]
        bad('swapped-ordered-ports',lambda b:b['proposals'][p]['members'][i]['ordered_ports'].reverse())
      else:
        mutations.append({'mutation':'swapped-ordered-ports','status':'SKIPPED','reason':'No actual two-port proposal.'})
        coverage_gaps.append('swapped-ordered-ports')
    else:
      mutations.append({'mutation':'ordered-port-mutations','status':'SKIPPED','reason':'No actual returned member has a read port.'})
      coverage_gaps.append('ordered-port-mutations')
    passed(common_names[2],{'mutations':mutations},seam)
    if len(batch['proposals'])>=2:
      b=copy.deepcopy(batch);b['proposals'][-1]['members'][0]['candidate']['membership']={}
      passed(common_names[3],reject(lambda:check(s,decision,b)),seam)
    else:skip(common_names[3],'Only one actual ranked proposal; no later proposal to corrupt.')

    q=quota_advice(state=copy.deepcopy(s),decision=decision,tick=tick)
    artifacts['quota_UNKNOWN']=q
    passed(common_names[4],{'artifact':'quota_UNKNOWN','status':q['status'],'no_executable_prefix':True})
    # A quota may interrupt before binding capture, so use a literal clone with
    # current joins ONLY to test the validator's UNKNOWN-status rejection edge.
    qjoin=copy.deepcopy(q);qjoin.update(binding=copy.deepcopy(batch['binding']),state_sha256=batch['state_sha256'],decision=copy.deepcopy(decision))
    passed(common_names[5],reject(lambda:check(s,decision,qjoin)),seam)
    canonical_first=first_key(s,0);artifacts['canonical_first']=canonical_first
    empty_result,empty_child=stop_after_placement(s,empty_advice)
    need(canonical(first_try(empty_result)['key'])==canonical(canonical_first['event']['candidate']['placement_key']),
      'empty actual hint list keeps first original canonical alternative')
    artifacts['empty_search']=empty_result
    passed(common_names[6],{'search':'empty_search','canonical':'canonical_first','child_state':empty_child['state']},seam)
    unknown_result_value,unknown_child=stop_after_placement(s,quota_advice)
    need(canonical(first_try(unknown_result_value)['key'])==canonical(canonical_first['event']['candidate']['placement_key'])
      and unknown_result_value['counts']['advice_unknown']>=1,'UNKNOWN advisory prefix never executed')
    artifacts['quota_search']=unknown_result_value
    passed(common_names[7],{'search':'quota_search','canonical':'canonical_first','child_state':unknown_child['state']})
    def timeout_advice(**kwargs):
      tick();raise CallbackExhausted('declared adviser callback Timeout, not definite exclusion')
    e=make(s,adv=timeout_advice);before=snap(e);r=e.search();unknown_result(e,before,r)
    need(not any(x['kind']=='TRY' for x in r['events']),'no attempted partial advisory member')
    artifacts['callback_timeout_search']=r
    passed(common_names[8],{'search':'callback_timeout_search'},seam)
    def value_error(**kwargs):
      tick();raise ValueError('declared callback ValueError must propagate')
    for label,adv,validator in ((common_names[9],value_error,None),(common_names[10],current_advice,value_error)):
      e=make(s,adv=adv,validator=validator);before=snap(e)
      observed=reject(e.search);need(observed['reason']=='declared callback ValueError must propagate','exact callback failure not classified as hint rejection')
      observed.update(restored(e,before));passed(label,observed,seam)

    selection=receipt['selection']
    if not selection['future_keys']:
      for label in common_names[11:]:skip(label,'Actual first selected family has no future keys; consumer gate remains unqualified.')
    else:
      holder={'engine':None,'inner_token':None,'inner_snapshot':None,'phase':'capture','receipts':[]}
      def watched_validator(**kwargs):
        tick();value=validate_advice(**kwargs)
        if value['mode']=='PENDING_KEYS':holder['receipts'].append(copy.deepcopy(value))
        return value
      def capture_degree(**kwargs):
        tick();current=snap(holder['engine'])
        if holder['phase']=='capture' and current['pending_preferences'] is not None:
          holder['inner_token']=holder['engine'].checkpoint();holder['inner_snapshot']=current
          raise CallbackExhausted('declared stable child checkpoint capture after real anchor placement')
        if holder['phase']=='continue' and any(x['selection'] is not None for x in holder['receipts']):
          holder['after']=current;raise CallbackExhausted('declared stop after actual pending-key placement')
        if holder['phase']=='remote' and any(x['rejections'] for x in holder['receipts']):
          holder['after']=current;raise CallbackExhausted('declared stop after rejected hint and actual fallback placement')
        if holder['phase']=='forced-retirement' and holder['retirement_calls']:
          holder['after']=current;raise CallbackExhausted('declared stop after forced-fill retirement and later canonical branch')
        return degree_proposer(**kwargs)
      def watched_adviser(**kwargs):
        tick()
        if holder['phase']=='forced-retirement':
          holder['retirement_calls'].append({'state':copy.deepcopy(kwargs['state']),
            'decision':copy.deepcopy(kwargs['decision'])})
          return quota_advice(**kwargs)
        return current_advice(**kwargs) if holder['phase']=='capture' else empty_advice(**kwargs)
      e=make(s,capture_degree,watched_adviser,watched_validator);holder['engine']=e
      outer=e.checkpoint();before=snap(e);r=e.search();unknown_result(e,before,r)
      inner=holder['inner_snapshot'];token=holder['inner_token']
      need(inner is not None and token is not None,'genuine normal-search child has nonempty family')
      need(len(inner['state']['selected'])==len(s['selected'])+1,'one anchor placed, no future members')
      anchor_key=selection['anchor']['placement_key']
      need(any(canonical(x)==canonical(dict(copy.deepcopy(anchor_key),generation=1)) for x in inner['state']['selected']),
        'actual first independently selected anchor installed')
      need(all(not any(canonical(k)==canonical({f:r[f] for f in ('tile_type_id','type_preimage','translation')}) for r in inner['state']['selected'])
        for k in selection['future_keys']),'no pending future key preinstalled')
      expected=state(language,[future,selection['anchor']],tick)
      need(canonical(inner['state'])==canonical(expected),'whole point state equals fixed fixture plus anchor only')
      artifacts['adoption_search']=r;artifacts['genuine_inner_snapshot']=inner
      passed(common_names[11],{'search':'adoption_search','inner':'genuine_inner_snapshot','no_future_marks_installed':True})
      passed(common_names[12],restored(e,before))
      e.rollback(token);need(canonical(snap(e))==canonical(inner),'public owned child token restores nonempty pending whole snapshot')
      passed(common_names[13],{'snapshot':'genuine_inner_snapshot','actual_pending_keys':inner['pending_preferences']['pending_keys']})

      # Same genuine engine and once-bound callbacks. Only explicit control
      # phase changes in a stable holder; no engine callback reseal/mutation.
      h=holder;e2=e;outer2=outer;before2=before;inner2=copy.deepcopy(inner)
      h['phase']='continue';h['receipts']=[];continuation=e2.search();unknown_result(e2,inner2,continuation)
      selected_pending=[x for x in h['receipts'] if x['selection'] is not None]
      if selected_pending:
        need(continuation['counts']['pending_selected']>=1,'actual pending selection counter')
        artifacts['pending_selection_receipts']=h['receipts'];artifacts['pending_continuation_search']=continuation
        passed(common_names[14],{'search':'pending_continuation_search','receipts':'pending_selection_receipts'})
        passed(common_names[15],restored(e2,inner2))
      else:
        skip(common_names[14],'Actual selected family did not reach a legal pending BRANCH before an independent UNKNOWN.')
        passed(common_names[15],restored(e2,inner2))

      # Derive one remote conflict from an actual pending key, not from a
      # supplied target route. It must leave that pending output row unfilled.
      e2.rollback(token);remote_error=None
      try:
        family=inner2['pending_preferences'];remote=None;bad_key=None
        occupied={r['translation'][1] for r in inner2['state']['selected']}
        marks={tuple(p):v for p,v in inner2['state']['m']}
        for k in family['pending_keys']:
          pre=k['type_preimage'];row=k['translation'][1]
          for formula,offset in zip(pre['ordered_premise_formulas'],pre['ordered_offsets']):
            read=row+offset
            if read in occupied or (1,read) in marks:continue
            for ax_name in names:
              other=language.theory['axioms'][ax_name]
              if canonical(other)==canonical(formula):continue
              for out in range(23,read,-1):
                if out in occupied or out==row:continue
                try:
                  candidate=prepared(ug,language,other,v,read,out,tick)
                  proposed=state(language,[future,selection['anchor'],candidate],tick)
                except Unavailable:continue
                remote=candidate;bad_key=k;break
              if remote is not None:break
            if remote is not None:break
          if remote is not None:break
        if remote is None:raise Unavailable('No legal original remote UG conflict for an actual absent pending read.')
        e2.place(obligations(remote,inner2['state']));remote_before=snap(e2)
        h['phase']='remote';h['receipts']=[];remote_search=e2.search();unknown_result(e2,remote_before,remote_search)
        rejected=[x for x in h['receipts'] if x['rejections']]
        if not rejected:raise Unavailable('Actual scheduler did not reach conflicting pending row before independent UNKNOWN.')
        need(any(canonical(k['key'])==canonical(bad_key) and k['reason']=='whole_remote_or_metadata_mark_conflict'
          for x in rejected for k in x['rejections']),'actual full pending key rejected by whole remote mark')
        artifacts['remote_search']=remote_search;artifacts['remote_receipts']=h['receipts']
        artifacts['remote_fixture']={'remote':remote,'before':remote_before,'invalidated_pending_key':bad_key}
        passed(common_names[16],{'search':'remote_search','receipts':'remote_receipts','fixture':'remote_fixture'})
        advice_events=[x for x in remote_search['events'] if x['kind']=='ADVICE' and x.get('rejected_keys')]
        need(advice_events and advice_events[-1]['mode']=='CANONICAL_FALLBACK','rejected key not executed and fallback retained')
        passed(common_names[17],{'actual_fallback_event':advice_events[-1], 'search':'remote_search'})
      except Unavailable as error:remote_error=str(error)
      finally:e2.rollback(outer2);restored(e2,before2)
      if remote_error is not None:
        skip(common_names[16],remote_error);skip(common_names[17],remote_error)

      # Current-row-only pending requests and repeated full identity checks.
      key=copy.deepcopy(selection['future_keys'][0]);row=key['translation'][1]
      request={'schema':'unit-row-pending-preference-request-v1','binding':copy.deepcopy(language.binding),
        'state_sha256':digest(inner['state']),'decision':{'kind':'BRANCH','row':row},
        'family_id':inner['pending_preferences']['family_id'],'keys':[key]}
      component_decision=request['decision']
      checks=[]
      for label,edit in (
          ('duplicate-pending-key',lambda b:b['keys'].append(copy.deepcopy(b['keys'][0]))),
          ('pending-wrong-incident-row',lambda b:b['keys'][0]['translation'].__setitem__(1,0)),
          ('pending-forged-full-key',lambda b:b['keys'][0].__setitem__('tile_type_id','forged'))):
        p=copy.deepcopy(request);edit(p)
        checks.append({'mutation':label,'result':reject(lambda:check(inner['state'],component_decision,p))})
      passed(common_names[18],{'checks':checks,
        'authority':'Component intake only: this BRANCH-shaped request does not establish the global scheduler decision.'},seam)

      # Use actual point constraints to force the remaining family rows. Every
      # predecessor except one pending output is filled with the original AX;
      # a selected later UG imposes the remaining output formula. No pending
      # member is directly installed, and no custom scheduler/degree is used.
      try:
        e2.rollback(token);family=inner['pending_preferences']
        pending=family['pending_keys'];pending_rows=sorted(k['translation'][1] for k in pending)
        if len(pending_rows)!=2 or pending_rows[-1]>=22:
          raise Unavailable('Forced-fill fixture needs actual two-key family below the last two rows.')
        low,high=pending_rows
        low_key=next(k for k in pending if k['translation'][1]==low)
        low_formula=copy.deepcopy(low_key['type_preimage']['primitive_witness']['formula'])
        filler=[]
        for row in range(high):
          current=snap(e2)['state'];occupied={r['translation'][1] for r in current['selected']}
          if row in occupied or row in pending_rows:continue
          candidate=prepared(tile,language,{'rule':'axiom','name':name,'formula':u},[],[],row,tick)
          # Literal independent fixture recomposition detects incompatible
          # premises before public place; absence never means occupied/fact.
          selected_tiles=[tile(language,r['type_preimage']['primitive_witness'],
              r['type_preimage']['ordered_premise_formulas'],
              [r['translation'][1]+d for d in r['type_preimage']['ordered_offsets']],r['translation'][1],tick)
              for r in current['selected']]
          state(language,selected_tiles+[candidate],tick)
          e2.place(obligations(candidate,current));filler.append(candidate)
        current=snap(e2)['state'];occupied={r['translation'][1] for r in current['selected']}
        later=next((r for r in range(high+1,23) if r not in occupied),None)
        if later is None:raise Unavailable('No unused later row for a genuine UG pending-output constraint.')
        constrain=prepared(ug,language,low_formula,v,low,later,tick)
        e2.place(obligations(constrain,current));forced_before=snap(e2)
        need(all(dict((tuple(p),n) for p,n in forced_before['state']['t'])[(0,r)]==0 for r in pending_rows),
          'both future family rows genuinely unoccupied before global forced propagation')
        h['phase']='forced-retirement';h['retirement_calls']=[];h['receipts']=[]
        forced_retirement=e2.search();unknown_result(e2,forced_before,forced_retirement)
        if not h['retirement_calls']:
          raise Unavailable('Actual global state did not reach later BRANCH after forced filling before independent UNKNOWN.')
        observed=h['retirement_calls'][0];totals={tuple(p):n for p,n in observed['state']['t']}
        need(all(totals[(0,r)]==1 for r in pending_rows),'fresh advice called only after all old preference rows filled')
        events=[x for x in forced_retirement['events'] if x['kind']=='ADVICE' and x['retired_keys']]
        need(events and {canonical(k) for k in events[-1]['retired_keys']}=={canonical(k) for k in pending}
          and events[-1]['pending_preferences'] is None,'actual branch retires exactly occupied hints, fresh UNKNOWN then canonical fallback')
        forced_rows={x['row'] for x in forced_retirement['events'] if x['kind']=='TRY' and x['mode']=='FORCED'}
        need(set(pending_rows)<=forced_rows,'original global forced moves filled both pending rows, not adviser macro')
        artifacts['forced_retirement']={'search':forced_retirement,'before':forced_before,
          'new_adviser_calls':h['retirement_calls'],'filler_AX':filler,'selected_UG_constraint':constrain}
        passed(common_names[19],{'artifact':'forced_retirement','retired_keys':events[-1]['retired_keys']})
      except Unavailable as error:skip(common_names[19],error)
      finally:e2.rollback(outer2);restored(e2,before2)

  # Same actual global scheduler, original AX/UG states. Forbidden adviser
  # asserts it cannot run on DEAD or before a forced placement.
  scheduler_names=('global-DEAD-overrides-advice','global-FORCED-overrides-advice')
  try:
    if not names or not variables:raise Unavailable('Need original AX and Gamma-eligible parameter.')
    a=copy.deepcopy(language.theory['axioms'][names[0]]);v=variables[0]
    if sum(f==a for f in roots)!=1 or ['bot'] in roots:
      raise Unavailable('Scheduler fixture requires one AX occurrence and no original bottom root.')
    single=state(language,[prepared(ug,language,a,v,0,1,tick)],tick)
    late=state(language,[prepared(ug,language,a,v,0,1,tick),prepared(ug,language,['bot'],v,2,4,tick)],tick)
    calls=[]
    def forbidden_advice(**kwargs):
      tick();calls.append(copy.deepcopy(kwargs['decision']))
      raise AssertionError('advice bypassed mandatory global DEAD/FORCED precedence')
    e=make(late,adv=forbidden_advice);before=snap(e);dead=e.search();restored(e,before)
    need(dead['status']=='EXHAUSTED' and calls==[] and dead['counts']['placements']==0,'real later ZERO kills before earlier forced/advice')
    artifacts['dead_search']=dead;passed(scheduler_names[0],{'search':'dead_search','adviser_calls':calls})
    forced,child=stop_after_placement(single,forbidden_advice)
    need(forced['counts']['forced']==1 and not any(x['kind']=='ADVICE' for x in forced['events']),
      'one actual forced move before any advice')
    artifacts['forced_search']=forced;passed(scheduler_names[1],{'search':'forced_search','child_state':child['state'],'adviser_calls':calls},seam)
  except Unavailable as error:
    for label in scheduler_names:skip(label,error)
  expected_names=set(common_names+scheduler_names)
  need(len(cases)==len(expected_names) and {c['case'] for c in cases}==expected_names,'every declared case exactly once')
  missing=[c['case'] for c in cases if c['status']=='SKIPPED']
  result={'schema':'unit-row-goal-advice-controls-v1','version':VERSION,'cases':cases,'artifacts':artifacts,
    'declared_cases':len(expected_names),'passed':sum(c['status']=='PASSED' for c in cases),
    'skipped':len(missing),'all_declared_cases_completed':True,'all_advice_consumer_gates_qualified':not missing and not coverage_gaps,
    'unqualified_consumer_gates':missing,'additional_coverage_gaps':coverage_gaps,'scope':local,
    'seams':'Declared malformed/suppressed-hint/native-first Timeout/ValueError only; no fake universe, candidate, EOF, degree or family.',
    'counts_are_observations_not_distinct_or_causal_reuse':True}
  result.update({k:False for k in STRONG_FLAGS})
  tick();return result

