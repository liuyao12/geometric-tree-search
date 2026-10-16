"""SOURCE ONLY genuine goal-advice/consumer component controls.

No project imports, saved proof/library, native clocks or activation. All
scientific endpoints are caller-authenticated delegates; malformed packets and
interruptions below are explicit control seams, never candidate/EOF oracles.
"""
import copy
import hashlib
import json

VERSION = 'unit-row-observation-reuse-controls-v2'
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
    return adviser(**kwargs,maximum_terms=1,maximum_demands=5,maximum_rounds=3,maximum_proposals=8)
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


# Preserve the ENTIRE reviewed 22-case function above, including all assertions.
# The observing callbacks below are control-only data collection/fault seams.
_run_prior_controls = run_controls


def run_controls(*,language,engine_factory,adviser,validate_advice,degree_proposer,
                 fallback,certify_fallback,tick):
  """Run the unchanged22 then eight prospective whole-family lifecycle checks.

  Reuse actual old remote/continuation work; no duplicate root adoption/search.
  Only three short public searches are added, from a genuinely owned checkpoint
  captured at a completed independent pending-rejection callback. No private
  cache/family mutation, fabricated candidate universe or EOF is used.
  """
  records=[];extra=[];evidence={}
  local='Actual original-language independent pending rejection and public owned transaction; no proof, graph, trajectory or benefit authority.'
  seam='Explicit native-first callback observation/fault/quota control, never candidate/degree/EOF or logical authority.'
  labels=('whole-family-abandoned-with-different-future-key-remaining',
    'one-fresh-batch-at-same-rejected-BRANCH',
    'abandoned-future-members-never-installed-or-excluded',
    'successful-pending-continuity-preserved',
    'rejection-parent-and-owned-inner-rollback-exact',
    'fresh-replacement-ValueError-propagates-without-family-commit',
    'fresh-replacement-Timeout-UNKNOWN-no-exclusion',
    'later-BRANCH-reconsiders-fresh-advice-after-abandonment')
  def passed(name,value,scope=local):
    tick();extra.append({'case':name,'status':'PASSED','observed':copy.deepcopy(value),'scope':scope})
  def skip(name,reason):
    extra.append({'case':name,'status':'SKIPPED','observed':{'reason':str(reason)},
      'scope':'Essential family-retirement coverage not exercised; unqualified.'})
  def observing_factory(*,initial_state=None,degree_proposer=degree_proposer,
                        fallback=fallback,certify_fallback=certify_fallback,
                        branch_adviser=None,validate_advice=None,tick):
    if branch_adviser is None:
      return engine_factory(initial_state=initial_state,degree_proposer=degree_proposer,
        fallback=fallback,certify_fallback=certify_fallback,
        branch_adviser=None,validate_advice=None,tick=tick)
    record={'mode':'PRIOR22','engine':None,'adviser_calls':[], 'validations':[],
      'token':None,'snapshot':None,'checkpoint_call_index':None,'later_calls':[], 'stop_snapshot':None}
    records.append(record)
    prior_degree,prior_adviser,prior_validator=degree_proposer,branch_adviser,validate_advice
    def observed_degree(**kwargs):
      tick()
      if record['mode']=='PRIOR22':return prior_degree(**kwargs)
      if record['mode']=='LATER' and len(record['later_calls'])>=2:
        record['stop_snapshot']=record['engine'].state_snapshot()
        raise CallbackExhausted('declared stop after two real fresh advised/fallback branches')
      # Genuine original degree endpoint after the completed old harness; this
      # bypasses only its now-finished observer, never the candidate language.
      return degree_proposer_endpoint(**kwargs)
    def observed_adviser(**kwargs):
      tick();entry={'mode':record['mode'],'state':copy.deepcopy(kwargs['state']),
        'decision':copy.deepcopy(kwargs['decision'])}
      record['adviser_calls'].append(entry)
      if record['mode']=='VALUE_ERROR':
        raise ValueError('declared replacement adviser ValueError after definite rejection')
      if record['mode']=='TIMEOUT':
        raise CallbackExhausted('declared replacement adviser Timeout after definite rejection')
      if record['mode']=='LATER':
        value=adviser(**kwargs,maximum_work=1,maximum_terms=1,
          maximum_demands=1,maximum_rounds=1,maximum_proposals=1)
        need(value['status']=='UNKNOWN','genuine quota batch diagnostic only')
        record['later_calls'].append(entry)
      else:value=prior_adviser(**kwargs)
      entry['actual_return']=copy.deepcopy(value)
      return value
    def observed_validator(**kwargs):
      tick();value=prior_validator(**kwargs) if record['mode']=='PRIOR22' else validate_advice_endpoint(**kwargs)
      entry={'mode':record['mode'],'state':copy.deepcopy(kwargs['state']),
        'decision':copy.deepcopy(kwargs['decision']),'batch':copy.deepcopy(kwargs['batch']),
        'actual_receipt':copy.deepcopy(value),'adviser_calls_before':len(record['adviser_calls'])}
      record['validations'].append(entry)
      if (record['mode']=='PRIOR22' and value['mode']=='PENDING_KEYS' and value['rejections']
          and record['token'] is None):
        # Read-only public calls at stable pure branch-selection boundary. Do
        # not place/rollback/reenter search while this callback is active.
        record['snapshot']=record['engine'].state_snapshot()
        record['token']=record['engine'].checkpoint()
        record['checkpoint_call_index']=len(record['validations'])-1
      return value
    engine=engine_factory(initial_state=initial_state,degree_proposer=observed_degree,
      fallback=fallback,certify_fallback=certify_fallback,
      branch_adviser=observed_adviser,validate_advice=observed_validator,tick=tick)
    record['engine']=engine
    return engine

  degree_proposer_endpoint=degree_proposer
  validate_advice_endpoint=validate_advice
  result=_run_prior_controls(language=language,engine_factory=observing_factory,adviser=adviser,
    validate_advice=validate_advice,degree_proposer=degree_proposer,fallback=fallback,
    certify_fallback=certify_fallback,tick=tick)
  need(result['declared_cases']==22 and len(result['cases'])==22,'all original22 retained once')
  candidates=[r for r in records if r['token'] is not None]
  reason=None
  if len(candidates)!=1:reason='Need one genuine current pending-rejection checkpoint from original remote case.'
  for name in ('remote_search','remote_receipts','remote_fixture','pending_continuation_search'):
    if name not in result['artifacts']:reason='Original22 did not produce required actual '+name+'; no fabricated family.'
  if reason is not None:
    for label in labels:skip(label,reason)
  else:
    record=candidates[0];engine=record['engine'];outer=engine.checkpoint();outer_snapshot=engine.state_snapshot()
    inner=record['snapshot'];token=record['token']
    rejection=record['validations'][record['checkpoint_call_index']]
    pending=inner['pending_preferences'];request=rejection['batch'];receipt=rejection['actual_receipt']
    family_id=pending['family_id'];rejected={canonical(x['key']) for x in receipt['rejections']}
    remaining=[k for k in pending['pending_keys'] if canonical(k) not in rejected]
    remote=result['artifacts']['remote_search'];continuity=result['artifacts']['pending_continuation_search']
    events=[x for x in remote['events'] if x['kind']=='ADVICE' and x['abandoned_family'] is not None]
    need(events,'actual engine emitted abandonment inside normal child adoption')
    event=events[-1];abandoned=event['abandoned_family']
    need(abandoned['schema']=='unit-row-advisory-family-abandonment-v1'
      and abandoned['family_id']==family_id and abandoned['branch_row']==request['decision']['row']
      and abandoned['reason']=='DEFINITE_CURRENT_PENDING_MEMBER_REJECTION'
      and {canonical(k) for k in abandoned['pending_keys']}=={canonical(k) for k in pending['pending_keys']}
      and {canonical(k) for k in abandoned['rejected_keys']}==rejected and remaining,
      'rejection abandons ALL actual still-pending keys including a different future key')
    # Establish literal current legality of a different future key, without
    # claiming that its row was selected by the global scheduler now.
    later=remaining[0];later_row=later['translation'][1]
    later_request={'schema':'unit-row-pending-preference-request-v1','binding':copy.deepcopy(language.binding),
      'state_sha256':digest(rejection['state']),'decision':{'kind':'BRANCH','row':later_row},
      'family_id':family_id,'keys':[copy.deepcopy(later)]}
    later_receipt=validate_advice(state=copy.deepcopy(rejection['state']),decision=later_request['decision'],
      batch=later_request,tick=tick)
    need(later_receipt['selection'] is not None and later_receipt['rejections']==[],
      'different unfilled future key still whole-point legal; family abandonment is advisory cleanup')
    evidence['actual_rejection']={**rejection,'owned_inner_snapshot':inner,'abandonment_event':event,
      'different_future_key_component_check':{'request':later_request,'receipt':later_receipt,
        'scope':'Component point legality only; not current global scheduling authority.'}}
    passed(labels[0],{'artifact':'family_retirement.actual_rejection','old_family_keys':len(pending['pending_keys']),
      'actually_rejected_keys':len(rejected),'different_legal_key':later})
    calls=record['adviser_calls'][rejection['adviser_calls_before']:]
    matching=[x for x in calls if x['mode']=='PRIOR22' and canonical(x['state'])==canonical(rejection['state'])
      and canonical(x['decision'])==canonical(rejection['decision'])]
    need(len(matching)==1 and 'actual_return' in matching[0],
      'exactly one real fresh advice callback after definite rejection at same selected BRANCH')
    need(event['mode']=='CANONICAL_FALLBACK' and event['pending_preferences'] is None,
      'actual old control suppresses fresh hints, whole abandoned family absent in child plan')
    evidence['same_branch_fresh_batch']=matching[0]
    passed(labels[1],{'artifact':'family_retirement.same_branch_fresh_batch','fresh_calls':len(matching)})
    need(not any(x['kind']=='EXCLUDE' for x in remote['events']), 'no rejection/UNKNOWN child exclusion')
    actual_last=remote['last_observed_state'];rebuilt=[]
    for r in actual_last['selected']:
      p=r['type_preimage'];row=r['translation'][1]
      rebuilt.append(tile(language,p['primitive_witness'],p['ordered_premise_formulas'],
        [row+d for d in p['ordered_offsets']],row,tick))
    need(canonical(state(language,rebuilt,tick,actual_last['excluded']))==canonical(actual_last),
      'actual observed child point state independently recomposes selected placements only')
    need(all(not any(canonical(k)==canonical({f:r[f] for f in ('tile_type_id','type_preimage','translation')})
      for r in actual_last['selected']) for k in remaining),'no other future key silently installed')
    passed(labels[2],{'remote_search_artifact':'remote_search','actual_child_state':actual_last,
      'remaining_keys_never_installed':remaining,'EXCLUDE_events':0})
    successful=[x for x in continuity['events'] if x['kind']=='ADVICE' and x['mode']=='PENDING_KEYS']
    need(successful and all(x['abandoned_family'] is None for x in successful),
      'genuine successful continuation retained, not whole-family abandonment on ordinary progress')
    passed(labels[3],{'continuity_artifact':'pending_continuation_search','actual_successful_events':successful})
    engine.rollback(token);need(canonical(engine.state_snapshot())==canonical(inner),'owned nonempty inner token restores exactly')
    before=engine.state_snapshot()
    need(remote['root_snapshot_sha256']==remote['final_snapshot_sha256'], 'old remote search whole-root rollback')
    passed(labels[4],{'inner_snapshot_sha256':digest(inner),'restored_sha256':digest(before),
      'remote_search_root_sha256':remote['root_snapshot_sha256']})
    try:
      for mode,label in (('VALUE_ERROR',labels[5]),('TIMEOUT',labels[6])):
        engine.rollback(token);before=engine.state_snapshot();start=len(record['adviser_calls']);record['mode']=mode
        if mode=='VALUE_ERROR':
          error=None
          try:engine.search()
          except ValueError as ex:
            if type(ex) is not ValueError:raise
            error=str(ex)
          need(error=='declared replacement adviser ValueError after definite rejection','exact fresh replacement error propagates')
          observed={'exception_type':'ValueError','reason':error}
        else:
          value=engine.search()
          need(value['status']=='UNKNOWN' and value['found'] is None
            and value['root_restored'] is True and value['stack_restored'] is True,
            'replacement callback Timeout remains UNKNOWN and restores')
          need(not any(x['kind']=='EXCLUDE' for x in value['events']),'replacement UNKNOWN never excludes original candidate')
          observed={'actual_result':value}
        new_calls=record['adviser_calls'][start:]
        need(len(new_calls)==1 and canonical(new_calls[0]['decision'])==canonical(rejection['decision'])
          and canonical(new_calls[0]['state'])==canonical(rejection['state']),
          'one fresh replacement callback at same branch, no recursive advice retry')
        after=engine.state_snapshot();need(canonical(after)==canonical(before),'full parent restored despite pre-adoption failure')
        need(canonical(after['pending_preferences'])==canonical(pending), 'failed pure plan cannot leak abandoned family state')
        observed.update(before_sha256=digest(before),after_sha256=digest(after),actual_callback=new_calls[0])
        passed(label,observed,seam)
      engine.rollback(token);before=engine.state_snapshot();record['mode']='LATER';record['later_calls']=[]
      follow=engine.search();after=engine.state_snapshot()
      need(follow['status']=='UNKNOWN' and follow['found'] is None and canonical(after)==canonical(before)
        and not any(x['kind']=='EXCLUDE' for x in follow['events']), 'later real branch continuation exact rollback without exclusion')
      calls=record['later_calls'];need(len(calls)==2 and calls[0]['decision']==rejection['decision']
        and calls[1]['decision']['kind']=='BRANCH' and calls[1]['decision']['row']>calls[0]['decision']['row'],
        'fresh batch reconsidered at rejected branch then a genuinely later global branch')
      need(record['stop_snapshot'] is not None and record['stop_snapshot']['pending_preferences'] is None,
        'real quota UNKNOWN does not execute partial family or leave stale preferences')
      evidence['follow_on_search']={'actual_result':follow,'actual_adviser_calls':calls,
        'actual_child_snapshot':record['stop_snapshot'],'before_sha256':digest(before),'after_sha256':digest(after)}
      passed(labels[7],{'artifact':'family_retirement.follow_on_search'},seam)
    finally:
      record['mode']='PRIOR22';engine.rollback(outer)
      need(canonical(engine.state_snapshot())==canonical(outer_snapshot),'restore actual finished old-harness outer state')
  need(len(extra)==8 and {x['case'] for x in extra}==set(labels),'all eight new gates retained')
  result['cases'].extend(extra);result['artifacts']['family_retirement']=evidence
  need(len(result['cases'])==30 and len({x['case'] for x in result['cases']})==30,'all thirty distinct declared gates exactly once')
  result['version']=VERSION;result['declared_cases']=30
  result['passed']=sum(x['status']=='PASSED' for x in result['cases'])
  result['skipped']=sum(x['status']=='SKIPPED' for x in result['cases'])
  result['unqualified_consumer_gates']=[x['case'] for x in result['cases'] if x['status']=='SKIPPED']
  result['all_advice_consumer_gates_qualified']=not result['unqualified_consumer_gates'] and not result['additional_coverage_gaps']
  result['family_retirement_control_scope']=local
  tick();return result


# Keep both previous control functions and all thirty original cases unchanged.
_run_prior30_controls = run_controls


def run_controls(*,language,engine_factory,adviser,validate_advice,degree_proposer,
                 fallback,certify_fallback,tick):
  """Preserved40 checks plus three current source-fibre component controls.

  Observe genuine current returns only. A missing returned descriptor is not
  evidence of nongeneration; absent reopening/replacement coverage stays a gap.
  No fair-index calibration, route, fake family, candidate universe or EOF.
  """
  labels=('real-returned-interface-features-score-and-order',
    'forged-interface-feature-and-score-rejections',
    'Boolean-versus-integer-feature-and-score-rejections',
    'obsolete-adviser-version-rejected',
    'later-ranked-quality-defect-and-order-rejected',
    'real-returned-root-reopening-remains-legal-and-demoted',
    'real-returned-universal-diversity-with-declared-term-horizon',
    'nonempty-READY-replacement-adopted-after-definite-rejection',
    'replacement-installs-anchor-only-not-future-obligations',
    'replacement-owned-nonempty-inner-and-parent-rollback-exact')
  records=[];extra=[];evidence={};returned={}
  # In-invocation control REPORT reuse only. The always-fresh delegate below is
  # still used by every engine, mutation, injected callback and replacement.
  # Canonical bytes are immutable and distinguish bool/int and absence/zero.
  report_receipts={};reuse_log=[]
  reuse_counts={'fresh_calls':0,'recorded_unique_receipts':0,'report_hits':0,'report_misses':0}
  consumer_version='unit-row-independent-advice-consumer-validator-v3-compatible-fibres-versions'
  def authority_bytes():
    tick()
    return canonical({'binding':language.binding,'source_bindings':language.source_bindings,
      'declaration':language.declaration,'policy':language.policy,'theory':language.theory,
      'parameters':language.parameters,'Gamma':language.gamma,'target':language.target,
      'forbidden':sorted(language.forbidden),'parameter_set':sorted(language.parameter_set),
      'input_names':sorted(language.input_names),'binder_names':sorted(language.binder_names),
      'hole':language.hole,'validator_version':consumer_version}).encode('utf8')
  def request_bytes(s,d,b):
    tick();value=(authority_bytes(),canonical(s).encode('utf8'),
      canonical(d).encode('utf8'),canonical(b).encode('utf8'))
    tick();return value
  def fresh_validate(**kwargs):
    before=request_bytes(kwargs['state'],kwargs['decision'],kwargs['batch'])
    reuse_counts['fresh_calls']+=1
    receipt=validate_advice(**kwargs)  # ALWAYS actual fresh guarded Root endpoint.
    tick();after=request_bytes(kwargs['state'],kwargs['decision'],kwargs['batch'])
    need(before==after,'full authority/request canonical bytes stable across actual independent delegation')
    if (kwargs['batch'].get('schema')=='unit-row-goal-branch-advice-batch-v1'
        and kwargs['batch'].get('status')=='READY' and receipt['mode']=='ADVICE_BATCH'):
      need(receipt['version']==consumer_version
        and canonical(receipt['binding']).encode('utf8')==canonical(language.binding).encode('utf8')
        and canonical(receipt['decision']).encode('utf8')==before[2]
        and receipt['state_sha256']==digest(kwargs['state'])
        and receipt['input_sha256']==digest(kwargs['batch'])
        and all(receipt[k] is False for k in STRONG_FLAGS),'completed current full receipt exact request/authority join')
      raw=canonical(receipt).encode('utf8');tick()
      if before in report_receipts:
        need(report_receipts[before]['receipt']==raw,'same whole request has same complete independent receipt')
      else:
        report_receipts[before]={'receipt':raw,'origin_fresh_call':reuse_counts['fresh_calls']}
        reuse_counts['recorded_unique_receipts']+=1
    tick();return receipt
  def report_receipt(s,d,b,site):
    before=request_bytes(s,d,b);entry=report_receipts.get(before)
    if entry is None:
      reuse_counts['report_misses']+=1
      # Misses remain actual validation, not READY from remember(raw return).
      value=fresh_validate(state=copy.deepcopy(s),decision=copy.deepcopy(d),batch=copy.deepcopy(b),tick=tick)
      entry=report_receipts.get(before)
      need(entry is not None,'report requires one completed full current independent receipt')
      hit=False
    else:
      reuse_counts['report_hits']+=1
      value=json.loads(entry['receipt'].decode('utf8'));hit=True
    tick();need(before==request_bytes(s,d,b),'full report request/authority bytes unchanged during reuse')
    reuse_log.append({'site':site,'reused':hit,'origin_fresh_call':entry['origin_fresh_call'],
      'state_sha256':digest(s),'decision_sha256':digest(d),'batch_sha256':digest(b),'receipt_sha256':digest(value)})
    tick();return value
  local='Genuine current original-language returned-batch and owned-search controls; no degree, proof, speed, learned marking or RL authority.'
  seam='CONTROL ONLY: malformed literal packets or order-preserving suppression after whole real-batch validation; never used by target search.'
  def passed(name,value,scope=local):
    tick();extra.append({'case':name,'status':'PASSED','observed':copy.deepcopy(value),'scope':scope})
  def skip(name,reason):
    extra.append({'case':name,'status':'SKIPPED','observed':{'reason':str(reason)},
      'scope':'Unexercised interface/replacement coverage remains an explicit unqualified gate.'})
  def remember(s,d,b):
    tick()
    if b.get('status')=='READY' and b.get('proposals'):
      key=digest(b)
      captured=request_bytes(s,d,b)
      if key in returned:
        prior=returned[key]
        need(prior['request_bytes']==captured,'digest bucket deduplicates only exact whole request/authority bytes')
      else:
        returned[key]={'state':copy.deepcopy(s),'decision':copy.deepcopy(d),'batch':copy.deepcopy(b),
          'request_bytes':captured}
  def actual_adviser(**kwargs):
    tick();b=adviser(**kwargs)
    remember(kwargs['state'],kwargs['decision'],b)
    return b
  def observing_factory(*,initial_state=None,degree_proposer=degree_proposer,
                        fallback=fallback,certify_fallback=certify_fallback,
                        branch_adviser=None,validate_advice=None,tick):
    if branch_adviser is None:
      return engine_factory(initial_state=initial_state,degree_proposer=degree_proposer,
        fallback=fallback,certify_fallback=certify_fallback,
        branch_adviser=None,validate_advice=None,tick=tick)
    record={'mode':'PRIOR30','engine':None,'token':None,'snapshot':None,
      'rejection':None,'replacement':None,'replacement_attempt':None,'child_token':None,'child_snapshot':None,
      'fresh_calls':0,'accepted_context':None}
    records.append(record)
    prior_degree,prior_adviser,prior_validator=degree_proposer,branch_adviser,validate_advice
    def observed_degree(**kwargs):
      tick()
      if record['mode']=='PRIOR30':return prior_degree(**kwargs)
      if record['replacement'] is not None:
        current=record['engine'].state_snapshot()
        if current['pending_preferences'] is not None:
          record['child_snapshot']=current
          record['child_token']=record['engine'].checkpoint()
          raise CallbackExhausted('declared stable stop after genuine READY replacement anchor adoption and placement')
      return degree_endpoint(**kwargs)
    def observed_adviser(**kwargs):
      tick()
      if record['mode']=='PRIOR30':return prior_adviser(**kwargs)
      record['fresh_calls']+=1
      need(record['fresh_calls']==1,'at most one fresh batch at the same actual rejected BRANCH')
      b=adviser(**kwargs,maximum_work=50000,maximum_terms=1,
        maximum_demands=5,maximum_rounds=3,maximum_proposals=8)
      remember(kwargs['state'],kwargs['decision'],b)
      record['replacement_attempt']={'state':copy.deepcopy(kwargs['state']),
        'decision':copy.deepcopy(kwargs['decision']),'whole_actual_batch':copy.deepcopy(b),
        'diagnostic_only':True,'authority_accepted':False}
      if b['status']!='READY':
        raise Unavailable('Actual replacement batch is '+str(b['status'])+'; partial proposals are diagnostic only.')
      full_receipt=validator_endpoint(state=copy.deepcopy(kwargs['state']),
        decision=copy.deepcopy(kwargs['decision']),batch=copy.deepcopy(b),tick=tick)
      # Validate EVERY genuine ranked proposal before optional suppression.
      positions=[i for i,p in enumerate(b['proposals']) if len(p['members'])>1]
      if not positions:
        raise Unavailable('Actual validated READY replacement has no genuine future-bearing family.')
      index=positions[0];restricted=copy.deepcopy(b)
      restricted['proposals']=[copy.deepcopy(b['proposals'][index])]
      receipt=validator_endpoint(state=copy.deepcopy(kwargs['state']),
        decision=copy.deepcopy(kwargs['decision']),batch=copy.deepcopy(restricted),tick=tick)
      need(receipt['selection'] is not None and receipt['selection']['future_keys'],
        'order-preserving real subselection has nonempty independently checked future preferences')
      record['replacement']={'state':copy.deepcopy(kwargs['state']),
        'decision':copy.deepcopy(kwargs['decision']),'whole_actual_batch':copy.deepcopy(b),
        'whole_actual_receipt':copy.deepcopy(full_receipt),
        'control_only_selected_index':index,'executed_batch':restricted,
        'executed_receipt':copy.deepcopy(receipt),
        'suppression_scope':'CONTROL ONLY whole real batch validated first; one actual proposal retained in original order; never target policy.'}
      return restricted
    def observed_validator(**kwargs):
      tick();receipt=prior_validator(**kwargs) if record['mode']=='PRIOR30' else validator_endpoint(**kwargs)
      if (record['mode']=='PRIOR30' and record['token'] is None
          and receipt['mode']=='PENDING_KEYS' and receipt['rejections']):
        record['snapshot']=record['engine'].state_snapshot()
        record['token']=record['engine'].checkpoint()
        record['rejection']={'state':copy.deepcopy(kwargs['state']),
          'decision':copy.deepcopy(kwargs['decision']),'request':copy.deepcopy(kwargs['batch']),
          'receipt':copy.deepcopy(receipt)}
      if (record['mode']=='PRIOR30' and record['accepted_context'] is None
          and receipt['mode']=='PENDING_KEYS' and receipt['selection'] is not None
          and receipt['rejections']==[]):
        current=record['engine'].state_snapshot()
        need(canonical(current['state'])==canonical(kwargs['state'])
          and kwargs['decision'].get('kind')=='BRANCH'
          and canonical(receipt['decision'])==canonical(kwargs['decision'])
          and receipt['state_sha256']==digest(kwargs['state'])
          and receipt['input_sha256']==digest(kwargs['batch'])
          and canonical(receipt['binding'])==canonical(language.binding),
          'actual engine pending callback exact selected global BRANCH/request/whole snapshot')
        # This registered engine callback runs after its global decision and
        # before child adoption/place. Only read-only public capture occurs.
        record['accepted_context']={'snapshot':current,'token':record['engine'].checkpoint(),
          'state':copy.deepcopy(kwargs['state']),'decision':copy.deepcopy(kwargs['decision']),
          'request':copy.deepcopy(kwargs['batch']),'receipt':copy.deepcopy(receipt),
          'authority':authority_bytes()}
      return receipt
    e=engine_factory(initial_state=initial_state,degree_proposer=observed_degree,
      fallback=fallback,certify_fallback=certify_fallback,
      branch_adviser=observed_adviser,validate_advice=observed_validator,tick=tick)
    record['engine']=e
    return e
  degree_endpoint=degree_proposer;validator_endpoint=fresh_validate
  result=_run_prior30_controls(language=language,engine_factory=observing_factory,adviser=actual_adviser,
    validate_advice=fresh_validate,degree_proposer=degree_proposer,fallback=fallback,
    certify_fallback=certify_fallback,tick=tick)
  need(result['declared_cases']==30 and len(result['cases'])==30,'all prior30 run exactly once unchanged')

  # Two explicitly declared component calibrations only. They are never inputs
  # to the original-root theorem search. The real engine chooses the BRANCH;
  # absent/UNKNOWN batches remain diagnostic and never manufacture coverage.
  fibre_labels=('compatible-occupied-UI-source-fibre-returned-and-validated',
    'incompatible-marked-UI-source-not-returned-as-legal-or-executed',
    'missing-UI-source-remains-PENDING-not-a-fact')
  component_attempts={}
  def component(s,label):
    tick();e=engine_factory(initial_state=copy.deepcopy(s),degree_proposer=degree_proposer,
      fallback=fallback,certify_fallback=certify_fallback,
      branch_adviser=None,validate_advice=None,tick=tick)
    outer=e.checkpoint();before=e.state_snapshot()
    attempt={'state':copy.deepcopy(s),'before':copy.deepcopy(before),'scope':
      'Declared open original-language component only; no claim of reachability from target-root search or proof trajectory.',
      'authority_accepted':False}
    component_attempts[label]=attempt
    try:
      d=e.decision();after=e.state_snapshot()
      need(canonical(after['state'])==canonical(before['state']),
        'real global decision changes no selected point/mark state')
      attempt.update(actual_decision=copy.deepcopy(d),after_decision=copy.deepcopy(after))
      if d.get('kind')!='BRANCH':
        attempt['eligibility_gap']='Actual original global decision is '+str(d.get('kind'))+'; no BRANCH fabricated.'
        return attempt
      b=adviser(state=copy.deepcopy(after['state']),decision=copy.deepcopy(d),tick=tick,
        maximum_work=50000,maximum_terms=1,maximum_demands=5,maximum_rounds=3,maximum_proposals=8)
      attempt['whole_actual_batch']=copy.deepcopy(b)
      remember(after['state'],d,b)
      if b['status']!='READY':
        attempt['eligibility_gap']='Actual bounded component adviser is '+str(b['status'])+'; partial data diagnostic only.'
        return attempt
      receipt=fresh_validate(state=copy.deepcopy(after['state']),decision=copy.deepcopy(d),
        batch=copy.deepcopy(b),tick=tick)
      need(all(receipt[k] is False for k in STRONG_FLAGS),'whole component independent false authority flags')
      attempt['whole_actual_receipt']=copy.deepcopy(receipt)
      need(canonical(e.state_snapshot())==canonical(after),'advice and validation install no member in real component engine')
      return attempt
    finally:
      e.rollback(outer)
      need(canonical(e.state_snapshot())==canonical(before),'exact owned component rollback, no hidden family or member')
      attempt['restored_sha256']=digest(e.state_snapshot())
  component_reason=None
  try:
    eligible=[v for v in sorted(language.parameters) if v not in language.forbidden]
    if not eligible:raise Unavailable('No original Gamma-eligible declared parameter for reopening component.')
    v=eligible[0];f=['eq',['var',v],['var',v]]
    selected=ug(language,f,v,8,20,tick)
    open_state=state(language,[selected],tick)
    component(open_state,'root_reopening')
    component_attempts['root_reopening']['declaration']={'eligible_parameter':v,
      'literal_component_formula':f,'only_selected_tile':selected,
      'original_target_boundary_preserved':True,'not_target_proof_route':True}
  except language.OutsideLanguage as ex:
    if type(ex) is not language.OutsideLanguage:raise
    component_reason='Definite original-profile exclusion of component fixture: '+str(ex)
  except Unavailable as ex:component_reason=str(ex)
  if component_reason is not None:
    component_attempts['root_reopening']={'eligibility_gap':component_reason,'authority_accepted':False}
  occupied_reason=None
  try:
    original_fixture=result['artifacts'].get('fixture')
    if original_fixture is None:raise Unavailable('No actual original30 fixture to identify its occupied original AX source.')
    ax_name=original_fixture['derived_from']['AX_name'];u=copy.deepcopy(language.theory['axioms'][ax_name])
    matching=[]
    for rec in records:
      captured=rec['accepted_context']
      if captured is None:continue
      st=captured['state'];d=captured['decision'];selection=captured['receipt']['selection']
      pre=selection['anchor']['placement_key']['type_preimage'];row=d['row']
      actual_ax=[x for x in st['selected'] if x['translation']==[0,1]
        and canonical(x['type_preimage']['primitive_witness'])==canonical({'rule':'axiom','name':ax_name,'formula':u})]
      if (pre['primitive_witness']['rule']=='mp' and row+pre['ordered_offsets'][0]==1
          and canonical(pre['ordered_premise_formulas'][0])==canonical(u) and len(actual_ax)==1):
        matching.append((rec,captured,actual_ax[0]))
    if not matching:
      raise Unavailable('No suitable actual accepted pending BRANCH with matching original AX occupied at source1; no reconstructed parent or scratch replacement.')
    rec,captured,actual_ax=matching[0];e=rec['engine']
    outer=e.checkpoint();finished=e.state_snapshot()
    attempt={'scope':'Component adviser observation at an actually selected prior30 pending BRANCH; active family left unchanged, not executed replacement or target trajectory.',
      'authority_accepted':False,'declaration':{'AX_name_from_actual_original_fixture':ax_name,
        'selected_original_AX_record':copy.deepcopy(actual_ax),'source_row':1,
        'not_target_proof_route':True},
      'actual_callback':{'snapshot':copy.deepcopy(captured['snapshot']),
        'decision':copy.deepcopy(captured['decision']),'request':copy.deepcopy(captured['request']),
        'receipt':copy.deepcopy(captured['receipt']),'before_child_adoption_and_placement':True},
      'finished_outer_before':copy.deepcopy(finished)}
    component_attempts['occupied_compatible_UI_source']=attempt
    try:
      e.rollback(captured['token']);before=e.state_snapshot()
      need(canonical(before)==canonical(captured['snapshot']) and authority_bytes()==captured['authority'],
        'same owned engine whole accepted-callback snapshot and authority restored exactly')
      st=before['state'];d=captured['decision']
      attempt.update(state=copy.deepcopy(st),before=copy.deepcopy(before),
        actual_decision=copy.deepcopy(d),after_decision=copy.deepcopy(before))
      b=adviser(state=copy.deepcopy(st),decision=copy.deepcopy(d),tick=tick,
        maximum_work=50000,maximum_terms=1,maximum_demands=5,maximum_rounds=3,maximum_proposals=8)
      attempt['whole_actual_batch']=copy.deepcopy(b);remember(st,d,b)
      if b['status']!='READY':
        attempt['eligibility_gap']='Actual bounded scheduled-context adviser is '+str(b['status'])+'; partial data diagnostic only.'
      else:
        receipt=fresh_validate(state=copy.deepcopy(st),decision=copy.deepcopy(d),batch=copy.deepcopy(b),tick=tick)
        need(all(receipt[k] is False for k in STRONG_FLAGS),'whole scheduled component false authority flags')
        attempt['whole_actual_receipt']=copy.deepcopy(receipt)
        need(canonical(e.state_snapshot())==canonical(before),
          'component call installs nothing and leaves genuine active pending family unchanged')
    finally:
      e.rollback(outer);final_finished=e.state_snapshot()
      need(canonical(final_finished)==canonical(finished),'exact finished prior30 outer state restored after component observation')
      attempt['finished_outer_after']=copy.deepcopy(final_finished)
      attempt['restored_sha256']=digest(final_finished)
  except language.OutsideLanguage as ex:
    if type(ex) is not language.OutsideLanguage:raise
    occupied_reason='Definite original-profile exclusion of scheduled occupied-source component: '+str(ex)
  except Unavailable as ex:occupied_reason=str(ex)
  if occupied_reason is not None:
    component_attempts['occupied_compatible_UI_source']={'eligibility_gap':occupied_reason,'authority_accepted':False}
  evidence['component_attempts']=component_attempts

  # Recompute from full candidate ports and actual state, independently of the
  # proposal's feature diagnostics. The actual independent validator separately
  # reconstructs all members and temporary point unions, including later ranks.
  def nodes(value):
    stack=[value]
    while stack:
      tick();node=stack.pop()
      if type(node) is list:
        yield node
        stack.extend(reversed([x for x in node if type(x) is list]))
  def features(s,d,p):
    totals={tuple(point):value for point,value in s['t']}
    marks={tuple(point):value for point,value in s['m']}
    root_nodes=set()
    for row in range(d['row'],24):
      tick()
      if totals[(0,row)]==0 and (1,row) in marks:
        value=marks[(1,row)]
        need(type(value) is list and len(value)==2 and value[0]=='formula','literal unfilled current root formula')
        root_nodes.update(canonical(n) for n in nodes(json.loads(value[1])))
    members=p['members'];member_rows={m['candidate']['placement_key']['translation'][1] for m in members}
    interfaces=set();external_occurrences=0
    for m in members:
      tick();key=m['candidate']['placement_key'];pre=key['type_preimage'];row=key['translation'][1]
      for formula,offset in zip(pre['ordered_premise_formulas'],pre['ordered_offsets']):
        tick();read=row+offset
        if read not in member_rows and totals[(0,read)]==0:
          interfaces.add((read,canonical(formula)));external_occurrences+=1
    root=p['goal_root']
    connected=root is not None and any(
      m['candidate']['placement_key']['translation'][1]==root['row'] and
      canonical(m['candidate']['placement_key']['type_preimage']['primitive_witness']['formula'])==canonical(root['formula'])
      for m in members)
    reopens=root is not None and any(f==canonical(root['formula']) for _,f in interfaces)
    quality=0 if reopens else 2 if connected else 1
    anchor=p['anchor_full_key'];formula=anchor['type_preimage']['primitive_witness']['formula']
    selected={canonical(r['type_preimage']['primitive_witness']['formula']) for r in s['selected']}
    novel=canonical(formula) not in selected
    overlap=sum(canonical(n) in root_nodes for n in nodes(formula))
    f={'goal_connected':connected,'anchor_novel':novel,'literal_list_subtree_overlap':overlap,
      'primitive_members':len(members),'quality_class':quality,'reopens_root':reopens,
      'unresolved_interface_pairs':len(interfaces)}
    score=[quality,-len(interfaces),int(novel),overlap,-len(members)]
    need(canonical(p['ranking_features'])==canonical(f) and canonical(p['score'])==canonical(score),
      'independent literal seven features and score5, Boolean distinct from integer')
    return {'features':f,'score':score,'distinct_unoccupied_external_pairs':[[r,json.loads(x)] for r,x in sorted(interfaces)],
      'unoccupied_external_port_occurrences':external_occurrences}
  def check(s,d,b):
    tick();r=fresh_validate(state=copy.deepcopy(s),decision=copy.deepcopy(d),batch=copy.deepcopy(b),tick=tick)
    need(all(r[k] is False for k in STRONG_FLAGS),'independent receipt stronger flags all false')
    return r
  def reject(s,d,b,expected):
    tick();reason=None
    try:check(s,d,b)
    except ValueError as ex:
      if type(ex) is not ValueError:raise
      reason=str(ex)
    tick();need(reason=='advice consumer: '+expected,'exact malformed rejection, not resource/custody failure')
    return {'exception_type':'ValueError','reason':reason,'malformed_batch_sha256':digest(b)}
  fixture=result['artifacts'].get('fixture')
  if fixture is None:
    for label in labels[:7]:skip(label,'No genuine returned READY fixture; no fabricated quality or generation evidence.')
  else:
    s,d,b=fixture['state'],fixture['decision'],fixture['batch']
    need(b['version']=='unit-row-generic-goal-branch-adviser-v3-compatible-source-fibres','actual current fair-interface adviser version')
    receipt=report_receipt(s,d,b,'fixture-scoring');rows=[features(s,d,p) for p in b['proposals']]
    order=[(tuple(-v for v in p['score']),canonical(p['anchor_full_key'])) for p in b['proposals']]
    need(order==sorted(order),'actual whole returned batch has exact score5/full-anchor tie order')
    evidence['scoring']={'source_artifact':'fixture.batch','actual_batch_sha256':digest(b),
      'actual_independent_receipt':receipt,'recomputed_rows':rows,
      'scope':'Distinct interface pairs, not repeated port occurrences; no causal reuse or generation-completeness claim.'}
    passed(labels[0],{'artifact':'fair_interface.scoring','returned_proposals':len(rows)})
    changes=(('quality_class',lambda p:p['ranking_features'].__setitem__('quality_class',p['ranking_features']['quality_class']+1),'independent advisory feature values'),
      ('reopens_root',lambda p:p['ranking_features'].__setitem__('reopens_root',not p['ranking_features']['reopens_root']),'independent advisory feature values'),
      ('unresolved_interface_pairs',lambda p:p['ranking_features'].__setitem__('unresolved_interface_pairs',p['ranking_features']['unresolved_interface_pairs']+1),'independent advisory feature values'),
      ('score_interface_penalty',lambda p:p['score'].__setitem__(1,p['score'][1]-1),'independent literal advisory score'))
    mutations=[]
    for label,edit,why in changes:
      value=copy.deepcopy(b);edit(value['proposals'][0])
      mutations.append({'mutation':label,'result':reject(s,d,value,why)})
    passed(labels[1],{'source_batch_sha256':digest(b),'mutations':mutations},seam)
    mutations=[]
    for label,edit,why in (
        ('integer-for-Boolean',lambda p:p['ranking_features'].__setitem__('goal_connected',int(p['ranking_features']['goal_connected'])),'independent advisory feature values'),
        ('Boolean-for-score-int',lambda p:p['score'].__setitem__(2,bool(p['score'][2])),'independent literal advisory score'),
        ('Boolean-for-feature-int',lambda p:p['ranking_features'].__setitem__('quality_class',bool(p['ranking_features']['quality_class'])),'independent advisory feature values')):
      value=copy.deepcopy(b);edit(value['proposals'][0]);mutations.append({'mutation':label,'result':reject(s,d,value,why)})
    passed(labels[2],{'source_batch_sha256':digest(b),'mutations':mutations},seam)
    value=copy.deepcopy(b);value['version']='unit-row-generic-goal-branch-adviser-v1'
    passed(labels[3],reject(s,d,value,'whole current READY batch only'),seam)
    if len(b['proposals'])<2:skip(labels[4],'Fewer than two genuine returned proposals; no later-rank/order mutation.')
    else:
      value=copy.deepcopy(b);value['proposals'][-1]['score'][0]+=1
      later=reject(s,d,value,'independent literal advisory score')
      value=copy.deepcopy(b);value['proposals'].reverse()
      ordered=reject(s,d,value,'whole original ranked batch order')
      passed(labels[4],{'later_proposal':later,'reversed_actual_order':ordered},seam)
    reopening=[];diversity=[];universals=set();terms=set()
    for batch_sha,entry in returned.items():
      tick();batch=entry['batch'];st=entry['state'];dec=entry['decision']
      observed_receipt=report_receipt(st,dec,batch,'returned-batch-observation')
      for index,p in enumerate(batch['proposals']):
        observed=features(st,dec,p)
        for m in p['members']:
          w=m['candidate']['placement_key']['type_preimage']['primitive_witness']
          if w['rule']=='instantiate':universals.add(canonical(w['universal']));terms.add(canonical(w['term']))
        if observed['features']['reopens_root']:
          reopening.append((batch_sha,entry,index,observed))
      diversity.append({'batch_sha256':batch_sha,'state_sha256':batch['state_sha256'],
        'limits':copy.deepcopy(batch['limits']),'work':copy.deepcopy(batch['work']),
        'returned_proposals':len(batch['proposals']),
        'independent_receipt_sha256':digest(observed_receipt)})
    evidence['returned_observations']={'batches':diversity,'distinct_returned_UI_universals':[json.loads(x) for x in sorted(universals)],
      'distinct_returned_UI_terms':[json.loads(x) for x in sorted(terms)],
      'limitations':'Returned top-k only; best-per-full-anchor and top-k discard descriptors. Absence never proves nongeneration. terms1 controls cannot establish multi-term runtime fairness; finite-index scheduling has static review only.'}
    if not reopening:skip(labels[5],'No genuine returned root-reopening proposal; lawful generation/demotion runtime coverage remains a gap, never fabricated.')
    else:
      sha,entry,index,observed=reopening[0];r=report_receipt(entry['state'],entry['decision'],entry['batch'],'reopening-observation')
      need(observed['features']['quality_class']==0 and entry['batch']['proposals'][index]['installed'] is False,
        'literal open-root debt remains legal but class0, not pruned or installed')
      evidence['reopening']={'actual_batch':{k:copy.deepcopy(entry[k]) for k in ('state','decision','batch')},'proposal_index':index,'recomputed':observed,'independent_receipt':r}
      passed(labels[5],{'artifact':'fair_interface.reopening','actual_returned_class':0})
    if len(universals)<2:
      skip(labels[6],'Fewer than two distinct UI universal descriptors genuinely returned. No inference about unseen generation/top-k; terms1 horizon unchanged.')
    else:passed(labels[6],{'artifact':'fair_interface.returned_observations',
      'distinct_returned_universals':len(universals),'distinct_returned_terms':len(terms),
      'scope':'Observed returned universal diversity only; no multi-term fairness, complete generation or absence claim.'})

  candidates=[r for r in records if r['token'] is not None]
  if len(candidates)!=1:
    for label in labels[7:]:skip(label,'No unique genuine completed pending-rejection checkpoint; no synthetic replacement family.')
  else:
    record=candidates[0];e=record['engine'];outer=e.checkpoint();outer_snapshot=e.state_snapshot()
    inner=record['snapshot'];old_pending=inner['pending_preferences'];reason=None
    try:
      e.rollback(record['token']);before=e.state_snapshot()
      need(canonical(before)==canonical(inner),'actual pending-rejection owned token restores full parent')
      record['mode']='READY_REPLACEMENT';record['fresh_calls']=0
      try:r=e.search()
      except Unavailable as ex:reason=str(ex)
      if reason is None:
        after=e.state_snapshot();child=record['child_snapshot'];replacement=record['replacement']
        if child is None or record['child_token'] is None:
          reason='Actual search did not reach stable nonempty READY replacement child before UNKNOWN.'
        else:
          need(r['status']=='UNKNOWN' and r['found'] is None and r['root_restored'] is True
            and r['stack_restored'] is True and canonical(after)==canonical(before),
            'native-first declared interruption restores full real rejection parent')
          need(record['fresh_calls']==1 and not any(x['kind']=='EXCLUDE' for x in r['events']),
            'one fresh actual batch; interruption/rejection never excludes a base child')
          need(canonical(replacement['state'])==canonical(record['rejection']['state'])
            and canonical(replacement['decision'])==canonical(record['rejection']['decision']),
            'fresh READY replacement at exact same actual independently rejected BRANCH')
          events=[x for x in r['events'] if x['kind']=='ADVICE' and x['abandoned_family'] is not None]
          need(len(events)==1 and events[0]['mode']=='ADVICE_BATCH'
            and events[0]['abandoned_family']['family_id']==old_pending['family_id'],
            'whole old family abandoned then genuine replacement adopted inside same child')
          fresh=child['pending_preferences'];selection=replacement['executed_receipt']['selection']
          need(fresh is not None and fresh['pending_keys'] and fresh['family_id']!=old_pending['family_id']
            and canonical(fresh)==canonical(events[0]['pending_preferences'])
            and {canonical(k) for k in fresh['pending_keys']}=={canonical(k) for k in selection['future_keys']},
            'actual new nonempty advisory family, never fabricated pending state')
          evidence['replacement']={**replacement,'actual_rejection':record['rejection'],
            'before':before,'child':child,'actual_result':r,'after':after}
          passed(labels[7],{'artifact':'fair_interface.replacement','same_branch_fresh_calls':record['fresh_calls']},seam)
          anchor=selection['anchor'];selected_before={canonical(x) for x in before['state']['selected']}
          selected_after={canonical(x) for x in child['state']['selected']}
          expected_record=copy.deepcopy(anchor['selection_record'])
          need(selected_after-selected_before=={canonical(expected_record)} and selected_before<=selected_after,
            'exactly independently selected current anchor added, never a future member')
          expected_tiles=[]
          for rec in before['state']['selected']:
            pre=rec['type_preimage'];row=rec['translation'][1]
            expected_tiles.append(tile(language,pre['primitive_witness'],pre['ordered_premise_formulas'],
              [row+d for d in pre['ordered_offsets']],row,tick))
          expected=state(language,expected_tiles+[anchor],tick,before['state']['excluded'])
          need(canonical(expected)==canonical(child['state']),
            'full child t/m/generations/exclusions equal old selected state plus exactly real anchor')
          installed={canonical({k:rec[k] for k in ('tile_type_id','type_preimage','translation')}) for rec in child['state']['selected']}
          need(all(canonical(k) not in installed for k in fresh['pending_keys']),
            'all replacement future keys remain uninstalled preferences, read obligations not facts')
          passed(labels[8],{'artifact':'fair_interface.replacement','added_anchor':anchor['placement_key'],
            'future_keys_remain_preferences':fresh['pending_keys']})
          e.rollback(record['child_token'])
          need(canonical(e.state_snapshot())==canonical(child),'public owned child token restores exact nonempty replacement family')
          child_sha=digest(e.state_snapshot());e.rollback(record['token'])
          need(canonical(e.state_snapshot())==canonical(before),'public owned original parent token restores whole old pending family')
          passed(labels[9],{'new_child_snapshot_sha256':digest(child),'restored_child_sha256':child_sha,
            'old_parent_sha256':digest(before),'restored_parent_sha256':digest(e.state_snapshot()),
            'search_root_sha256':r['root_snapshot_sha256'],'search_final_sha256':r['final_snapshot_sha256']})
      if record['replacement_attempt'] is not None:
        evidence['replacement_attempt']=record['replacement_attempt']
      if reason is not None:
        for label in labels[7:]:skip(label,reason)
    finally:
      record['mode']='PRIOR30';e.rollback(outer)
      need(canonical(e.state_snapshot())==canonical(outer_snapshot),'exact finished prior30 outer snapshot restored')

  # Source-fibre observations use only actual current returns, not a claim that
  # an omitted descriptor/base candidate was never generated or legally pruned.
  occupied=component_attempts['occupied_compatible_UI_source']
  if 'whole_actual_receipt' not in occupied:
    skip(fibre_labels[0],occupied.get('eligibility_gap','No complete occupied-source actual READY batch.'))
  else:
    matches=[];source_formula=occupied['declaration']['selected_original_AX_record']['type_preimage']['primitive_witness']['formula']
    for index,p in enumerate(occupied['whole_actual_batch']['proposals']):
      tick()
      if p['scheme']!='GENERIC_UI_MP':continue
      for mi,m in enumerate(p['members']):
        pre=m['candidate']['placement_key']['type_preimage'];row=m['candidate']['placement_key']['translation'][1]
        if pre['primitive_witness']['rule']!='mp':continue
        if row+pre['ordered_offsets'][0]==1 and canonical(pre['ordered_premise_formulas'][0])==canonical(source_formula):
          need(m['candidate']['read_obligations'][0]['occupied'] is True
            and m['candidate']['read_obligations'][0]['fact_accepted'] is False,
            'genuine occupied matching AX source retains literal original read semantics')
          matches.append({'proposal_index':index,'member_index':mi,'source_row':1})
    if not matches:skip(fibre_labels[0],'No genuine returned UI_MP uses the compatible occupied AX source; no generated-family inference.')
    else:passed(fibre_labels[0],{'artifact':'fair_interface.component_attempts.occupied_compatible_UI_source',
      'actual_matches':matches,'scope':'Real global BRANCH+whole returned batch independently checked; occupied AX source, not a supplied proof.'})
  bad_contexts=[rec for rec in records if rec['rejection'] is not None]
  incompatible_evidence=None
  for rec in bad_contexts:
    tick();rejection=rec['rejection'];st=rejection['state'];d=rejection['decision']
    actuals=[x for x in returned.values() if canonical(x['state'])==canonical(st) and canonical(x['decision'])==canonical(d)]
    if not actuals:continue
    entry=actuals[0];batch=entry['batch'];rr=report_receipt(st,d,batch,'incompatible-read-observation')
    marks={tuple(p):v for p,v in st['m']};conflicts=[]
    for rejected in rejection['receipt']['rejections']:
      key=rejected['key'];pre=key['type_preimage'];row=key['translation'][1]
      for port,(formula,offset) in enumerate(zip(pre['ordered_premise_formulas'],pre['ordered_offsets'])):
        read=(1,row+offset)
        if read in marks and canonical(marks[read])!=canonical(['formula',canonical(formula)]):
          conflicts.append({'rejected_full_key':key,'port':port,'read_point':list(read),
            'required_formula':copy.deepcopy(formula),'actual_assigned_mark':copy.deepcopy(marks[read])})
    if not conflicts:continue
    for p in batch['proposals']:
      for m in p['members']:
        tick();key=m['candidate']['placement_key'];pre=key['type_preimage'];row=key['translation'][1]
        for formula,offset in zip(pre['ordered_premise_formulas'],pre['ordered_offsets']):
          read=(1,row+offset)
          need(read not in marks or canonical(marks[read])==canonical(['formula',canonical(formula)]),
            'every actual returned member read compatible with assigned literal marks')
        need(all(canonical(key)!=canonical(c['rejected_full_key']) for c in conflicts),
          'actual independently illegal pending key not returned as legal advice')
    remote=result['artifacts'].get('remote_search')
    if remote is None:continue
    need(not any(x['kind']=='EXCLUDE' for x in remote['events']),
      'hint incompatibility/UNKNOWN remains non-pruning, no fake exhausted child')
    attempted={canonical(x['key']) for x in remote['events'] if x['kind']=='TRY'}
    need(all(canonical(c['rejected_full_key']) not in attempted for c in conflicts),
      'genuinely incompatible rejected key not executed in observed remote search')
    incompatible_evidence={'actual_rejection':rejection,'conflicting_original_reads':conflicts,
      'whole_actual_batch':batch,'whole_actual_receipt':rr,'remote_search_artifact':'remote_search',
      'scope':'Returned descriptors and actual TRY only; no unseen-generation, full-fibre, degree/EOF or base pruning claim.'}
    break
  if incompatible_evidence is None:
    skip(fibre_labels[1],'No genuine current incompatible-mark rejection joined to a complete READY return and observed remote search.')
  else:
    evidence['incompatible_read']=incompatible_evidence
    passed(fibre_labels[1],{'artifact':'fair_interface.incompatible_read'})
  missing=None
  for entry in returned.values():
    tick();st=entry['state'];marks={tuple(p):v for p,v in st['m']};totals={tuple(p):v for p,v in st['t']}
    for pi,p in enumerate(entry['batch']['proposals']):
      if p['scheme']!='GENERIC_UI_MP':continue
      for oi,o in enumerate(p['ordered_PENDING_obligations']):
        source_member=p['members'][o['member_index']]['candidate']['placement_key']['type_preimage']
        if (source_member['primitive_witness']['rule']=='mp' and o['port']==0
            and o['occupied'] is False and (1,o['row']) not in marks):
          need(totals[(0,o['row'])]==0 and o['status']=='PENDING' and o['fact_accepted'] is False,
            'truly absent source output/mark remains unproved PENDING obligation')
          receipt=report_receipt(st,entry['decision'],entry['batch'],'missing-source-observation')
          missing={'actual_batch':{k:copy.deepcopy(entry[k]) for k in ('state','decision','batch')},'whole_actual_receipt':receipt,'proposal_index':pi,
            'obligation_index':oi,'missing_literal_point':[1,o['row']],
            'scope':'Generated compatible missing-read preference, never evidence its premise is a fact.'}
          break
      if missing is not None:break
    if missing is not None:break
  if missing is None:skip(fibre_labels[2],'No genuine returned UI_MP external obligation at an actually absent unoccupied source mark.')
  else:
    evidence['missing_source']=missing
    passed(fibre_labels[2],{'artifact':'fair_interface.missing_source'})

  need(len(extra)==13 and {x['case'] for x in extra}==set(labels+fibre_labels),'all thirteen new declared gates retained exactly once')
  used_origins={x['origin_fresh_call'] for x in reuse_log};unique_authorities={};used_entries=[]
  for key,entry in report_receipts.items():
    tick()
    if entry['origin_fresh_call'] not in used_origins:continue
    a,st,dec,batch=key;ah=hashlib.sha256(a).hexdigest()
    if ah in unique_authorities:need(unique_authorities[ah]==a,'whole authority equality before unique output reference')
    else:unique_authorities[ah]=a
    used_entries.append({'origin_fresh_call':entry['origin_fresh_call'],'authority_sha256':ah,
      'state':json.loads(st.decode('utf8')),'decision':json.loads(dec.decode('utf8')),
      'batch':json.loads(batch.decode('utf8')),'receipt':json.loads(entry['receipt'].decode('utf8'))})
  evidence['report_observation_reuse']={'counts':copy.deepcopy(reuse_counts),'sites':reuse_log,
    'authorities':[{'sha256':h,'value':json.loads(b.decode('utf8'))} for h,b in unique_authorities.items()],
    'entries':used_entries,
    'scope':'Same-invocation report observations only; exact whole request/effective authority bytes compared, every engine/negative/injected/replacement delegate stays fresh. One full input/receipt per report-used origin and authority, not every fresh call.'}
  result['cases'].extend(extra);result['artifacts']['fair_interface']=evidence
  need(len(result['cases'])==43 and len({x['case'] for x in result['cases']})==43,'all forty-three unique cases, no old gate replaced')
  result['version']=VERSION;result['declared_cases']=43
  result['passed']=sum(x['status']=='PASSED' for x in result['cases'])
  result['skipped']=sum(x['status']=='SKIPPED' for x in result['cases'])
  result['unqualified_consumer_gates']=[x['case'] for x in result['cases'] if x['status']=='SKIPPED']
  result['all_advice_consumer_gates_qualified']=not result['unqualified_consumer_gates'] and not result['additional_coverage_gaps']
  result['fair_interface_scope']=local
  result['no_generation_claim_from_topk_absence']=True
  result['control_only_real_order_preserving_suppression_never_target_policy']=True
  tick();return result
