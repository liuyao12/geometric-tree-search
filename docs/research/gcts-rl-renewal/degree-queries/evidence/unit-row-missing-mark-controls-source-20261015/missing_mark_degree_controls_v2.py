"""Source-only local-degree controls: callable endpoints, original language, no proof/runner."""
import copy
import hashlib
import json

VERSION='unit-row-degree-controls-Source-v2-missing-marks'


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


def run_controls(*,language,proposer,checker,carrier,tick):
  cases=[];outside=language.OutsideLanguage
  def skip(name,reason):
    cases.append({'case':name,'status':'SKIPPED','observed':{'reason':reason},'scope':'Unavailable fixture; gap.'})
  def positive(name,s,row,expected):
    tick();private=copy.deepcopy(s)
    proposal=proposer(language=language,state=copy.deepcopy(private),row=row,tick=tick)
    receipt=checker(language=language,state=copy.deepcopy(private),row=row,proposal=copy.deepcopy(proposal),tick=tick)
    need(receipt['schema']=='unit-row-degree-evidence-check-v2' and receipt['status'] in expected,name+' checker status')
    need(receipt['accepted_local_evidence'] is (receipt['status']!='UNKNOWN'),name+' acceptance scope')
    if receipt['status']=='ZERO':need(type(receipt['degree_exact']) is int and receipt['degree_exact']==0,name+' zero')
    if receipt['status']=='SINGLETON':need(type(receipt['degree_exact']) is int and receipt['degree_exact']==1,name+' singleton')
    if receipt['status']=='MANY':need(type(receipt['degree_exact']) is int and receipt['degree_exact']>=2,name+' many')
    if receipt['status'] in ('UNKNOWN','TWO_OR_MORE'):need(receipt['degree_exact'] is None,name+' no exact count')
    cases.append({'case':name,'status':'PASSED','observed':{'state':private,'row':row,'proposal':proposal,'receipt':receipt},
      'scope':'Local tiling; pending reads are not facts.'})
    return proposal,receipt
  def rejected(name,s,row,proposal,extra=None,contains=None):
    tick();reason=None
    try:checker(language=language,state=copy.deepcopy(s),row=row,proposal=copy.deepcopy(proposal),tick=tick)
    except ValueError as error:
      if type(error) is not ValueError:raise
      reason=str(error)
    need(reason is not None,name+' must genuinely reject')
    if contains is not None:need(contains in reason,name+' rejection branch')
    tick();cases.append({'case':name,'status':'PASSED','observed':{'state':copy.deepcopy(s),'row':row,
      'proposal':copy.deepcopy(proposal),'exception_type':'ValueError','reason':reason,'fixture_checks':extra},
      'scope':'Invalid evidence; resource errors propagate.'})
  initial=state(language,[],tick)
  names=sorted(language.theory['axioms'])
  if len(names)>=2:
    initial_p,_=positive('initial-row0-two-named-AX',initial,0,{'TWO_OR_MORE'})
  else:
    skip('initial-row0-two-named-AX','Fewer than two original AX names.')
    initial_p=proposer(language=language,state=copy.deepcopy(initial),row=0,tick=tick)
  target=language.target
  if target[0]=='all' and target[1] in language.parameters and target[1] not in language.forbidden and not any(f==target for f in list(language.theory['axioms'].values())+list(language.gamma)):
    p,r=positive('initial-final-universal-two-pending-UG',initial,23,{'TWO_OR_MORE'})
    need(len(p['candidates'])==2 and all(c['placement_key']['type_preimage']['primitive_witness']['rule']=='generalize'
      and c['read_obligations'] and all(o['occupied'] is False and o['fact_accepted'] is False for o in c['read_obligations'])
      for c in p['candidates']),'two actual unoccupied UG obligations')
  else:skip('initial-final-universal-two-pending-UG','Target/scope cannot isolate pending UG.')
  variables=[v for v in language.parameters if v not in language.forbidden]
  zero=None;many=None;single=None
  if not variables:
    for name in ('covered-zero','covered-original-AX-count','covered-many-UG-occurrences','imp-output-UNKNOWN','missing-prefix-now-ZERO'):
      skip(name,'No Gamma-eligible original parameter.')
  else:
    v=variables[0];bot=['bot']
    if any(f==bot for f in list(language.theory['axioms'].values())+list(language.gamma)):
      skip('covered-zero','Original bottom hint; zero unavailable.')
    else:
      try:
        zs=state(language,[ug(language,bot,v,0,1,tick)],tick)
        zp,zr=positive('covered-zero',zs,0,{'ZERO'});zero=(zs,0,zp,zr)
      except (outside,Unavailable) as error:skip('covered-zero',type(error).__name__+': '+str(error))
    try:
      imp=['imp',bot,bot]
      count=sum(f==imp for f in list(language.theory['axioms'].values())+list(language.gamma))
      if count>1:raise Unavailable('More than one original implication hint.')
      ins=state(language,[ug(language,imp,v,0,1,tick)],tick)
      positive('imp-output-UNKNOWN',ins,0,{'UNKNOWN'})
    except (outside,Unavailable) as error:skip('imp-output-UNKNOWN',type(error).__name__+': '+str(error))
    try:
      if any(f==bot for f in list(language.theory['axioms'].values())+list(language.gamma)):
        raise Unavailable('Original bottom hint blocks this case.')
      ms=state(language,[ug(language,bot,v,1,2,tick)],tick)
      positive('missing-prefix-now-ZERO',ms,1,{'ZERO'})
    except (outside,Unavailable) as error:skip('missing-prefix-now-ZERO',type(error).__name__+': '+str(error))
    if not names:
      skip('covered-original-AX-count','No named original AX exists.')
      skip('covered-many-UG-occurrences','No named original AX exists.')
    else:
      a=copy.deepcopy(language.theory['axioms'][names[0]])
      try:
        ss=state(language,[ug(language,a,v,0,1,tick)],tick)
        expected=sum(f==a for f in list(language.theory['axioms'].values())+list(language.gamma))
        sp,sr=positive('covered-original-AX-count',ss,0,{'SINGLETON'} if expected==1 else {'MANY'})
        need(sr['degree_exact']==expected,'all exact original names/Gamma occurrences counted')
        if expected==1:single=(ss,0,sp,sr)
      except (outside,Unavailable) as error:skip('covered-original-AX-count',type(error).__name__+': '+str(error))
      try:
        ax={'rule':'axiom','name':names[0],'formula':a};d=['all',v,copy.deepcopy(a)]
        ts=state(language,[tile(language,ax,[],[],0,tick),tile(language,ax,[],[],1,tick),ug(language,d,v,2,3,tick)],tick)
        tp,tr=positive('covered-many-UG-occurrences',ts,2,{'MANY'});many=(ts,2,tp,tr)
      except (outside,Unavailable) as error:skip('covered-many-UG-occurrences',type(error).__name__+': '+str(error))
  if many is not None:
    ms,row,mp,mr=many;keys=[copy.deepcopy(c['placement_key']) for c in mp['candidates']]
    need(len(keys)>=2 and len({canonical(k) for k in keys})==len(keys),'complete distinct cover keys')
    es=copy.deepcopy(ms);es['excluded']=keys[:-1]
    ep,er=positive('assumed-exclusions-to-singleton',es,row,{'SINGLETON'});single=(es,row,ep,er)
    es0=copy.deepcopy(ms);es0['excluded']=keys
    positive('assumed-exclusions-to-zero',es0,row,{'ZERO'})
    cases[-1]['scope']='Exact exclusions assumed, not proved pruning.'
    cases[-2]['scope']='Exact exclusions assumed, not proved pruning.'
    bad=copy.deepcopy(mp);bad['candidates'].append(copy.deepcopy(bad['candidates'][0]));rejected('duplicate-key',ms,row,bad)
    bad=copy.deepcopy(mp);bad['logical_proof_accepted']=True;rejected('forged-proof-flag',ms,row,bad)
    bad=copy.deepcopy(mp);bad['degree_zero_or_singleton_accepted']=True;rejected('forged-degree-flag',ms,row,bad)
    bad=copy.deepcopy(mp);bad['state_sha256']='0'*64 if bad['state_sha256']!='0'*64 else '1'*64;rejected('stale-state',ms,row,bad)
    bs=copy.deepcopy(ms);bs['t'][0][0][0]=False;rejected('Boolean-state-coordinate',bs,row,mp)
    bs=copy.deepcopy(ms);bs['excluded']=[copy.deepcopy(keys[0])];bs['excluded'][0]['type_preimage']['input_epoch']='CONTROL_STALE'
    rejected('forged-exclusion-key',bs,row,mp)
    bad=copy.deepcopy(mp);bad['candidates'][0]['global_m_values'][0][1]=['CONTROL_FORGED']
    rejected('forged-candidate-marks',ms,row,bad)
    try:
      c=copy.deepcopy(mp['candidates'][0]['placement_key']['type_preimage']['primitive_witness']['formula'])
      marks={tuple(p):value for p,value in ms['m']};f=json.loads(marks[(1,0)][1]);im=['imp',copy.deepcopy(f),copy.deepcopy(c)]
      remote=tile(language,{'rule':'mp','formula':c},[f,im],[0,1],row,tick)
      totals={p[1]:value for p,value in ms['t']}
      remote['read_obligations']=[{'row':k,'formula':copy.deepcopy(form),'occupied':totals[k]==1,'fact_accepted':False} for k,form in zip([0,1],[f,im])]
      conflict=any(tuple(p) in marks and canonical(marks[tuple(p)])!=canonical(value) for p,value in remote['global_m_values'])
      need(conflict,'independently built member has actual remote formula conflict')
      bad=copy.deepcopy(mp);bad.update(kind='TWO_LEGAL_WITNESSES',coverage=None,complete_cover_proposed=False,rejections=[],candidates=[remote,copy.deepcopy(mp['candidates'][0])])
      rejected('remote-formula-read-conflict',ms,row,bad,{'primitive_membership':remote['membership'],'actual_mark_conflict':True},'whole candidate legality')
    except (outside,Unavailable) as error:skip('remote-formula-read-conflict',type(error).__name__+': '+str(error))
  else:
    for name in ('assumed-exclusions-to-singleton','assumed-exclusions-to-zero','duplicate-key','forged-proof-flag','forged-degree-flag','stale-state','Boolean-state-coordinate','forged-exclusion-key','forged-candidate-marks','remote-formula-read-conflict'):
      skip(name,'No MANY fixture; gap.')
  if single is not None:
    ss,row,sp,sr=single;bad=copy.deepcopy(sp);bad['candidates']=[]
    rejected('missing-survivor',ss,row,bad)
  else:skip('missing-survivor','No singleton fixture; gap.')
  skip('queried-row-metadata-conflict','Unreachable: metadata comes only from the same occupied unit row; query is unfilled. Remote formula conflict is separate.')
  # Tiny DIRECT reference only; no formula registry or profile restriction.
  for maximum in (1,2):
    actual=carrier(language=language,maximum_nodes=maximum,tick=tick)
    need(type(actual) is list and len(actual)<=1000,'complete bounded carrier list, no missing outcome/prefix')
    if language.theory['predicates']:
      skip('tiny-carrier-reference-'+str(maximum),'Nonempty predicate signature; bot/not/all-only direct oracle is inapplicable.')
    else:
      expected=[['bot']]
      if maximum==2:expected += [['not',['bot']]]+[['all',b,['bot']] for b in sorted(language.binder_names)]
      need(canonical(actual)==canonical(expected),'whole tiny constructor carrier, literal order/names/EOF')
      cases.append({'case':'tiny-carrier-reference-'+str(maximum),'status':'PASSED','observed':{'maximum_nodes':maximum,
        'actual':actual,'reference':expected,'count':len(actual),'value_sha256':digest(actual)},
        'scope':'Complete nodes1/2 only under empty predicates; functions cannot form a formula of size<=2. Not full44 registry/count.'})
  new_names=('missing42-two-MP-orders','missing42-assumed-singleton','missing42-assumed-zero','missing43-maxA0-zero',
    'forged-fibre-completion','omitted-ordered-pair','forged-occurs-case','forged-fibre-count','forged-preimage-hash',
    'forged-decision-hash','missing-carrier-fibre-outcome','forged-carrier-bound')
  if not variables:
    for name in new_names:skip(name,'No original Gamma-eligible parameter for generic selected UG.')
  else:
    try:
      v=variables[0];c=['bot']
      for unused in range(41):c=['not',c]
      need(language.formula(c)==42,'literal41not+bot size42')
      if any(f==c for f in list(language.theory['axioms'].values())+list(language.gamma)):
        raise Unavailable('Original zero-port output matches deep control, so two-MP-only count is not asserted.')
      ds=state(language,[ug(language,c,v,2,3,tick)],tick)
      dp,dr=positive('missing42-two-MP-orders',ds,2,{'TWO_OR_MORE'})
      need(dp['kind']=='TWO_LEGAL_WITNESSES' and dp['fibre_cover']['completed'] is False,
        'early two never a completed fibre cover')
      reads=[]
      for item in dp['candidates']:
        pre=item['placement_key']['type_preimage']
        need(pre['primitive_witness']=={'rule':'mp','formula':c} and pre['ordered_premise_formulas']==[['bot'],['imp',['bot'],c]],
          'maxA1 bot-only exact primitive instances')
        reads.append(tuple(2+d for d in pre['ordered_offsets']))
        need(all(o['occupied'] is False and o['fact_accepted'] is False for o in item['read_obligations']),
          'both missing reads remain pending obligations')
      need(set(reads)=={(0,1),(1,0)} and len(reads)==2,'all ordered distinct MP ports, not merged')
      dkeys=[copy.deepcopy(x['placement_key']) for x in dp['candidates']]
      one=copy.deepcopy(ds);one['excluded']=dkeys[:1]
      op,orr=positive('missing42-assumed-singleton',one,2,{'SINGLETON'})
      none=copy.deepcopy(ds);none['excluded']=dkeys
      np,nr=positive('missing42-assumed-zero',none,2,{'ZERO'})
      for proposal,receipt in ((op,orr),(np,nr)):
        need(proposal['kind']=='NON_IMP_MISSING_MARK_COVER' and proposal['complete_cover_proposed'] is True
          and proposal['fibre_cover']['completed'] is True and receipt['missing_mark_cover_checked'] is True,
          'zero/one requires actual full missing-fibre re-enumeration')
      cases[-1]['scope']=cases[-2]['scope']='Exact exclusions are explicit branch assumptions, not proved pruning.'
      bad=copy.deepcopy(dp);bad['kind']='NON_IMP_MISSING_MARK_COVER';bad['complete_cover_proposed']=True;bad['fibre_cover']['completed']=True
      rejected('forged-fibre-completion',ds,2,bad)
      bad=copy.deepcopy(np);bad['fibre_cover']['ordered_MP_fibres'].pop()
      rejected('omitted-ordered-pair',none,2,bad)
      bad=copy.deepcopy(np)
      occurs=next(x for x in bad['fibre_cover']['ordered_MP_fibres'] if x['rows']==[0,0])
      occurs['case']='CONTROL_FALSE_NONEMPTY_OCCURS'
      rejected('forged-occurs-case',none,2,bad)
      for name,field in (('forged-fibre-count','examined'),('forged-preimage-hash','examined_preimages_sha256'),
                         ('forged-decision-hash','decisions_sha256'),('missing-carrier-fibre-outcome','examined_preimages_sha256')):
        bad=copy.deepcopy(np)
        fibre=next(x for x in bad['fibre_cover']['ordered_MP_fibres'] if x['rows']==[0,1])
        need(fibre['case']=='both_absent_full_scoped_carrier' and fibre['completed'] is True,'completed real carrier fibre')
        if name=='missing-carrier-fibre-outcome':del fibre[field]
        elif field=='examined':fibre[field]+=1
        else:fibre[field]='0'*64 if fibre[field]!='0'*64 else '1'*64
        rejected(name,none,2,bad)
      bad=copy.deepcopy(np);bad['fibre_cover']['MP_antecedent_max_nodes']=0
      rejected('forged-carrier-bound',none,2,bad)
    except (outside,Unavailable) as error:
      existing={x['case'] for x in cases}
      for name in new_names:
        if name not in existing and name!='missing43-maxA0-zero':skip(name,type(error).__name__+': '+str(error))
    try:
      c=['bot']
      for unused in range(42):c=['not',c]
      need(language.formula(c)==43,'literal42not+bot size43')
      if any(f==c for f in list(language.theory['axioms'].values())+list(language.gamma)):
        raise Unavailable('Original zero-port output matches size43, zero not asserted.')
      zs=state(language,[ug(language,c,variables[0],2,3,tick)],tick)
      zp,zr=positive('missing43-maxA0-zero',zs,2,{'ZERO'})
      need(zp['kind']=='NON_IMP_MISSING_MARK_COVER' and zp['fibre_cover']['MP_antecedent_max_nodes']==0
        and zp['fibre_cover']['completed'] is True and zr['missing_mark_cover_checked'] is True,
        'empty positive antecedent-size interval has complete zero cover')
    except (outside,Unavailable) as error:skip('missing43-maxA0-zero',type(error).__name__+': '+str(error))
  for endpoint in ('proposer','checker','carrier'):
    used=[0]
    def exhausted():
      tick();used[0]+=1
      if used[0]>=(1 if endpoint=='carrier' else 17):raise CallbackExhausted('CONTROL_CALLBACK_EXHAUSTED')
    caught=False
    try:
      if endpoint=='proposer':proposer(language=language,state=copy.deepcopy(initial),row=0,tick=exhausted)
      elif endpoint=='checker':checker(language=language,state=copy.deepcopy(initial),row=0,proposal=copy.deepcopy(initial_p),tick=exhausted)
      else:carrier(language=language,maximum_nodes=1,tick=exhausted)
    except CallbackExhausted as error:
      need(type(error) is CallbackExhausted and str(error)=='CONTROL_CALLBACK_EXHAUSTED','exact callback exhaustion')
      caught=True
    need(caught,endpoint+' must propagate callback exhaustion, not accept degree evidence')
    cases.append({'case':endpoint+'-callback-exhaustion','status':'PASSED','observed':{'calls':used[0],'exception_type':'CallbackExhausted','reason':'CONTROL_CALLBACK_EXHAUSTED'},'scope':'Control budget; native tick still called.'})
  tick()
  return {'schema':'unit-row-degree-controls-v1','version':VERSION,'cases':cases,'all_declared_cases_completed':True,
    'gap_policy':'SKIPPED is a gap; original theory unchanged.',
    'logical_proof_accepted':False,'complete_candidate_graph_accepted':False,
    'scheduler_or_rollback_accepted':False,'GCTS_advantage_accepted':False,'RL_accepted':False,'ROOT_resource_accepted':False}
