"""Prospective Root-owned component cases; execute only in the native actual.

No imports of project modules, clocks, search, theorem words or model caches.
Synthetic syntax hosts are deliberately unauthenticated and never native hosts.
"""
import copy
import hashlib
import json

VERSION='ROOT-receptor-family-component-cases-v1'
CASES=[
 'RF-01-joint-interface-and-full-two-MP-expansion',
 'RF-02-wrong-port-order-and-repeated-binding-rejected',
 'RF-03-typed-abstractions-and-capture-hygiene',
 'RF-04-eigenvariable-context-and-symbol-scope-rejected',
 'RF-05-nested-output-references-and-hypothesis-maps',
 'RF-06-cycle-identity-and-expansion-forgery-rejected',
 'RF-07-original-host-pending-port-point-cluster',
 'RF-08-original-six-rule-adapter-paths',
 'RF-09-host-epoch-and-port-provenance-rejected',
 'RF-10-shared-placement-union-and-remote-mark-conflict',
 'RF-11-unknown-and-resource-interruption-preserved',
 'RF-12-input-state-preservation-and-honest-costs']

class DeclaredControlInterruption(TimeoutError):pass

def require(ok,why):
    if not ok:raise ValueError('Root receptor component: '+why)

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)

def finish(descriptor):
    descriptor=copy.deepcopy(descriptor)
    descriptor['family_id']=hashlib.sha256(canonical({k:v for k,v in descriptor.items()
        if k not in ('family_id','provenance')}).encode('ascii')).hexdigest()
    return descriptor

def meta(pid,kind='FORMULA',args=None):
    return {'node':'formula_meta'if kind=='FORMULA'else'term_meta','parameter':pid,
            'arguments':[]if args is None else args}

def variable(pid,role='FREE_PARAMETER'):
    return {'id':pid,'kind':'VARIABLE','role':role,'distinct_from':[],
            'allowed_names_policy':'HOST_DECLARED_SCOPE'}

def abstraction(pid,kind='FORMULA',formals=None,external=None):
    return {'id':pid,'kind':kind,'formal_variables':[]if formals is None else formals,
            'allowed_external_free_variables':[]if external is None else external}

def descriptor(parameters,inputs,body,outputs,hypotheses=None,dependencies=None,conditions=None):
    return finish({'schema':'receptor-lemma-family-v2','family_id':'PENDING',
        'origin':'HUMAN_SPECIFIED','provenance':{'status':'INFRASTRUCTURE_COMPONENT_ONLY',
            'discovered':False,'target_proof_supplied':False},'required_host_features':[],
        'parameters':parameters,'hypotheses':[]if hypotheses is None else hypotheses,
        'inputs':inputs,'body':body,'outputs':outputs,
        'dependencies':[]if dependencies is None else dependencies,
        'side_conditions':[]if conditions is None else conditions})

def input_port(pid,formula,sharing='ALLOW_SAME_EXACT_PRIOR_SOURCE'):
    return {'id':pid,'formula':formula,'ordered_role':pid,'sharing':sharing}

def source(row):
    return {'schema':'receptor-family-six-rule-input-source-v1','row':row,'original_full_key':None}

def bindings(inputs,outputs=None,hypotheses=None):
    return {'hypotheses':[]if hypotheses is None else hypotheses,
        'inputs':[{'port_id':pid,'formula':copy.deepcopy(formula),'source':source(row),
                   'occupied':False,'fact_accepted':False}for pid,formula,row in inputs],
        'outputs':[]if outputs is None else outputs}

def run_component_cases(*,producer,checker,host_adapter,language,base_semantics,
                        marked_semantics,state,human_descriptor,tick):
    tick();initial=canonical(state);visits_before=language.kernel.visits
    controls=[];records=[];negative=[]
    host=host_adapter.describe_host(language=language,tick=tick)
    def passed(index,evidence):
        tick();controls.append({'case':CASES[index],'status':'PASSED','evidence':evidence})
    def rejected(label,fn,request,kind,codes=None,prefix=None):
        tick()
        try:fn()
        except BaseException as error:
            require(type(error)is kind,'negative exact declared data error '+label)
            if codes is not None:require(getattr(error,'code',None)in codes,'negative exact code '+label)
            if prefix is not None:require(str(error).startswith(prefix),'negative exact reason family '+label)
            packet={'label':label,'request':copy.deepcopy(request),'exception_type':type(error).__name__,
                'exception_code':getattr(error,'code',None),'reason':str(error),'rejected':True,
                'timeout_or_unknown_accepted_as_negative':False}
            negative.append(packet);tick();return packet
        raise ValueError('Root receptor component: invalid request accepted '+label)
    def expand(label,registry,fid,subst,ports,selected_host=None):
        h=host if selected_host is None else selected_host
        req={'registry':copy.deepcopy(registry),'family_id':fid,'host':copy.deepcopy(h),
             'substitution':copy.deepcopy(subst),'port_bindings':copy.deepcopy(ports)}
        p=producer.expand_family(**req,tick=tick)
        require(p['status']=='READY_PROPOSAL','complete producer expansion '+label)
        c=checker.check_expansion(**req,proposal=copy.deepcopy(p),tick=tick)
        require(c['status']=='CONDITIONAL_EXPANSION_CHECKED'and c['conditional_expansion_checked']is True,
                'fresh independent expansion '+label)
        require(c['flags']['proof_accepted']is False,'conditional checker has no theorem authority')
        result={'label':label,'request':req,'proposal':p,'check':c,
                'original_native_host':selected_host is None}
        records.append(result);return result
    def adapt(label,record,row_assignment=None):
        p=record['proposal'];ports=p['input_ports']
        if row_assignment is None:
            row_assignment={'schema':'receptor-family-six-rule-row-assignment-v1',
              'input_rows':[[v['port_id'],v['source']['row']]for v in ports],
              'node_rows':[[n['id'],len(ports)+i]for i,n in enumerate(p['primitive_nodes'])]}
        req=dict(record['request'],proposal=copy.deepcopy(p),state=copy.deepcopy(state),
                 row_assignment=copy.deepcopy(row_assignment))
        result=host_adapter.adapt_expansion(language=language,base_semantics=base_semantics,
          marked_semantics=marked_semantics,expansion_checker=checker,**req,tick=tick)
        require(result['status']=='READY_LOCAL_CLUSTER'and result['local_member_membership_checked']is True
            and result['local_point_union_checked']is True,'complete native point cluster '+label)
        require(result['proof_accepted']is result['engine_activated']is result['scheduler_or_rollback_accepted']is False,
                'component never accepts root or search')
        packet={'label':label,'request':req,'result':result};records.append(packet);return packet

    # Existing generic illustration, explicitly upgraded; no theorem/row route given to search.
    base=copy.deepcopy(human_descriptor);base['schema']='receptor-lemma-family-v2';base=finish(base)
    ax_name=sorted(language.theory['axioms'])[0];A=copy.deepcopy(language.theory['axioms'][ax_name])
    B=['bot'];C=copy.deepcopy(A)
    checked_marking=marked_semantics.check_marking(language,tick)
    require(A not in checked_marking['marking']['definition']['certified_literals'],
            'declaration-derived first AX is not a forbidden row-zero literal')
    subst={k:{'formal_names':[],'body':copy.deepcopy(v)}for k,v in [('A',A),('B',B),('C',C)]}
    ports=bindings([('in_a',A,0),('in_ab',['imp',A,B],1),('in_bc',['imp',B,C],2)],
                   [{'port_id':'out_c','formula':C}])
    core=expand('existing-two-MP',[base],base['family_id'],subst,ports)
    require(len(core['proposal']['primitive_nodes'])==2 and
       [n['rule']for n in core['proposal']['primitive_nodes']]==['mp','mp'],'full two-node expansion')
    matched=producer.match_family(registry=[base],family_id=base['family_id'],host=host,
        receptors=ports,candidate_bindings=[{}],tick=tick)
    require(matched['status']=='PROPOSALS'and matched['matching_complete']is False
            and len(matched['proposals'])==1,'joint inferred binding produces checked proposal')
    require(canonical(matched['proposals'][0]['request']['substitution'])==canonical(subst),
            'inferred repeated parameters fit all ports')
    checker.check_expansion(**core['request'],proposal=matched['proposals'][0],tick=tick)
    passed(0,{'core':core,'matching':matched})
    wrong=copy.deepcopy(ports);wrong['inputs'][2]['formula']=['imp',A,C]
    bad_req=dict(core['request'],port_bindings=wrong)
    failures=[rejected('incompatible-third-port',lambda:producer.expand_family(**bad_req,tick=tick),
      bad_req,producer.DescriptorError,{'PORT_MISMATCH'})]
    wrong_order=copy.deepcopy(ports);wrong_order['inputs'][0],wrong_order['inputs'][1]=wrong_order['inputs'][1],wrong_order['inputs'][0]
    req_order=dict(core['request'],port_bindings=wrong_order)
    failures.append(rejected('ordered-inputs',lambda:producer.expand_family(**req_order,tick=tick),
      req_order,producer.DescriptorError,{'PORT_BINDING'}))
    passed(1,failures)

    # All typed kinds and formula constructors on a separately labelled syntax-only host.
    syntax=copy.deepcopy(host);syntax.update(host_id='SYNTACTIC_TEST_ONLY',dialect='UNTRUSTED_SYNTAX_CONTROL',
      binding={'test_only':True},authority={'mode':'SYNTACTIC_TEST_ONLY_NO_NATIVE_AUTHORITY'},
      functions={'RF_f':1},predicates={'RF_R':1},variable_names=['x','y','z'],ordered_Gamma=[])
    vx={'node':'var','variable_id':'x'}
    pattern={'node':'all','binder_id':'x','body':{'node':'and',
      'left':{'node':'not','body':meta('F',args=[vx])},
      'right':{'node':'or','left':{'node':'pred','symbol':{'parameter':'P'},
        'arguments':[meta('T','TERM',[vx])]},'right':{'node':'eq',
        'left':{'node':'fun','symbol':'RF_f','arguments':[vx]},'right':vx}}}}
    typed=descriptor([variable('x','BOUND'),variable('u'),abstraction('F',formals=['u']),
      abstraction('T','TERM',['u']),{'id':'P','kind':'PREDICATE_SYMBOL','arity':1}],
      [input_port('typed_in',pattern)],[],[{'id':'typed_out','formula':pattern,'source':{'input':'typed_in'}}],
      conditions=[{'relation':'DECLARED_SYMBOL_ARITY','arguments':['P','1']}])
    ts={'x':'x','u':'y','P':'RF_R','F':{'formal_names':['q'],
       'body':['all','x',['eq',['var','q'],['var','x']]]},
       'T':{'formal_names':['q'],'body':['fun','RF_f',[['var','q']]]}}
    literal=['all','x',['and',['not',['all','y',['eq',['var','x'],['var','y']]]],
       ['or',['pred','RF_R',[['fun','RF_f',[['var','x']]]]],
             ['eq',['fun','RF_f',[['var','x']]],['var','x']]]]]
    tp=bindings([('typed_in',literal,0)],[{'port_id':'typed_out','formula':literal}])
    typed_record=expand('typed-and-capture',[typed],typed['family_id'],ts,tp,syntax)
    require(any(r['reason']=='ABSTRACTION_CAPTURE'and r['from']=='x'and r['to']=='y'
                for r in typed_record['proposal']['binder_renamings']),'actual capture avoidance recorded')
    passed(2,typed_record)
    eigen=copy.deepcopy(typed);next(p for p in eigen['parameters']if p['id']=='u')['role']='EIGEN';eigen=finish(eigen)
    context=copy.deepcopy(syntax);context['ordered_Gamma']=[['pred','RF_R',[['var','y']]]]
    er={'registry':[eigen],'family_id':eigen['family_id'],'host':context,'substitution':ts,'port_bindings':tp}
    scoped=[rejected('complete-Gamma-eigenvariable',lambda:producer.expand_family(**er,tick=tick),
      er,producer.DescriptorError,{'EIGEN'})]
    foreign=copy.deepcopy(ts);foreign['P']='ABSENT'
    fr={'registry':[typed],'family_id':typed['family_id'],'host':syntax,'substitution':foreign,'port_bindings':tp}
    scoped.append(rejected('foreign-predicate',lambda:producer.expand_family(**fr,tick=tick),
      fr,producer.DescriptorError,{'ARITY'}))
    passed(3,scoped)

    child=copy.deepcopy(base);child['outputs'].append({'id':'out_b','formula':meta('B'),'source':{'step':'mp_first'}});child=finish(child)
    calls={pid:{'formal_variables':[],'body':meta(pid)}for pid in ('A','B','C')}
    wrapper=descriptor(copy.deepcopy(base['parameters']),copy.deepcopy(base['inputs']),
      [{'id':'nested','kind':'FAMILY_CALL','family_ref':child['family_id'],'substitution':calls,
        'ordered_inputs':[{'input':v['id']}for v in base['inputs']],'ordered_hypotheses':[]}],
      [{'id':'out_c','formula':meta('C'),'source':{'step':'nested','output':'out_c'}},
       {'id':'out_b','formula':meta('B'),'source':{'step':'nested','output':'out_b'}}],dependencies=[child['family_id']])
    nested=expand('explicit-child-outputs',[child,wrapper],wrapper['family_id'],subst,ports)
    require([o['formula']for o in nested['proposal']['outputs']]==[C,B]
            and len(nested['proposal']['call_frames'])==2,'explicit nested output identities')
    hyp=descriptor([variable('u'),abstraction('H',external=['u'])],[],[],
      [{'id':'o','formula':meta('H'),'source':{'hypothesis':'h'}}],
      hypotheses=[{'id':'h','formula':meta('H'),'ordered_context_role':'original_occurrence',
                   'discharge':'NONE_UNLESS_EXPLICIT_HOST_RULE'}])
    hs={'u':'y','H':{'formal_names':[],'body':context['ordered_Gamma'][0]}}
    hp=bindings([],hypotheses=[{'port_id':'h','gamma_index':0,'formula':context['ordered_Gamma'][0]}])
    hyp_record=expand('original-context-port',[hyp],hyp['family_id'],hs,hp,context)
    require(hyp_record['proposal']['primitive_nodes'][0]['rule']=='assumption'
            and hyp_record['proposal']['primitive_nodes'][0]['arguments']=={'index':0},
            'explicit Gamma materializes real assumption syntax, not facts')
    hyp_wrapper=descriptor(copy.deepcopy(hyp['parameters']),[],
      [{'id':'hc','kind':'FAMILY_CALL','family_ref':hyp['family_id'],
        'substitution':{'u':{'variable_id':'u'},'H':{'formal_variables':[],'body':meta('H')}},
        'ordered_inputs':[],'ordered_hypotheses':[{'hypothesis':'h'}]}],
      [{'id':'o','formula':meta('H'),'source':{'step':'hc','output':'o'}}],
      hypotheses=copy.deepcopy(hyp['hypotheses']),dependencies=[hyp['family_id']])
    hyp_nested=expand('nested-original-Gamma-map',[hyp,hyp_wrapper],hyp_wrapper['family_id'],hs,hp,context)
    require(hyp_nested['proposal']['call_frames'][1]['hypotheses'][0]['gamma_index']==0
       and len(hyp_nested['proposal']['primitive_nodes'])==1,'nested call retains original occurrence and source node')
    passed(4,{'nested':nested,'syntactic_context_only':hyp_record,'nested_syntactic_context_only':hyp_nested})
    forged=copy.deepcopy(core['proposal']);forged['primitive_nodes'][0]['formula']=A
    forged_req=dict(core['request'],proposal=forged)
    forgery=[rejected('forged-expanded-node',lambda:checker.check_expansion(**forged_req,tick=tick),
      forged_req,checker.ExpansionCheckError)]
    bad_id=copy.deepcopy(base);bad_id['dependencies']=[base['family_id']]
    br={'registry':[bad_id],'family_id':base['family_id'],'host':host,'substitution':subst,'port_bindings':ports}
    forgery.append(rejected('forged-self-dependency-identity',lambda:producer.expand_family(**br,tick=tick),
      br,producer.DescriptorError,{'IDENTITY'}))
    passed(5,forgery)
    point=adapt('actual-pending-cluster',core)
    require(all(p['occupied']is p['fact_accepted']is False for p in point['result']['input_ports']),
            'pending input rows never become accepted facts')
    passed(6,point)

    # General six-rule wire builder, using original declared primitive witnesses.
    def one(witness,premises):
        params=[];env={};native_ids={}
        def var_id(name):
            if name not in native_ids:
                vid='V'+str(len(native_ids));native_ids[name]=vid;params.append(variable(vid));env[vid]=name
            return native_ids[name]
        def bind(pid,kind,value):
            free=language.term_names(value)if kind=='TERM'else language.free(value)
            ids=[var_id(n)for n in sorted(free)]
            params.append(abstraction(pid,kind,external=ids));env[pid]={'formal_names':[],'body':copy.deepcopy(value)}
            return meta(pid,kind)
        out=bind('Output','FORMULA',witness['formula']);ins=[];refs=[];bound=[]
        for i,f in enumerate(premises):
            pid='p'+str(i);ins.append(input_port(pid,bind('Premise'+str(i),'FORMULA',f)))
            refs.append({'input':pid});bound.append((pid,f,i))
        args={}
        for k,kind in host['rules'][witness['rule']]['arguments'].items():
            value=witness[k]
            args[k]={'type':kind,'value':bind('Arg'+k,kind,value)if kind in('FORMULA','TERM')
                 else {'variable_id':var_id(value)}if kind=='VARIABLE'else copy.deepcopy(value)}
        d=descriptor(params,ins,[{'id':'member','kind':'PRIMITIVE','rule':witness['rule'],
          'formula':out,'arguments':args,'ordered_inputs':refs}],
          [{'id':'out','formula':out,'source':{'step':'member'}}])
        return expand('native-'+witness['rule'],[d],d['family_id'],env,bindings(bound))
    zero_name=next(k for k,v in sorted(language.theory['functions'].items())if v==0);zero=['fun',zero_name,[]]
    universal=A;require(universal[0]=='all','original first AX has universal binder')
    ui={'rule':'instantiate','universal':universal,'term':zero,
        'formula':['imp',universal,language.substitute(universal[2],universal[1],zero)]}
    template=['eq',['var',language.hole],['var',language.hole]]
    left=language.substitute(template,language.hole,zero)
    eq={'rule':'eq_subst','variable':language.hole,'template':template,'left':zero,'right':zero,
        'formula':['imp',['eq',zero,zero],['imp',left,left]]}
    parameter=language.parameters[0]
    native_specs=[({'rule':'axiom','name':ax_name,'formula':A},[]),(ui,[]),(eq,[]),
      ({'rule':'mp','formula':A},[A,['imp',A,A]]),
      ({'rule':'generalize','variable':parameter,'formula':['all',parameter,A]},[A])]
    native=[adapt('native-'+w['rule'],one(w,p))for w,p in native_specs]
    require(language.gamma==[],'original Gamma remains empty')
    assumption={'rule':'assumption','formula':A,'index':0}
    no_assumption=rejected('original-empty-Gamma',lambda:language.primitive(assumption,[]),
      {'primitive_witness':assumption,'ordered_premises':[]},language.OutsideLanguage,
      prefix='OUT_OF_PROFILE_PRIMITIVE: ')
    passed(7,{'positive_adapter_rules':[w['rule']for w,p in native_specs],'native_records':native,
      'original_assumption_positive_unavailable':True,'original_native_assumption_rejection':no_assumption})
    bad_host=copy.deepcopy(host);bad_host['binding']['language_epoch']='0'*64
    req=dict(point['request'],host=bad_host)
    host_fail=[rejected('different-host-epoch',lambda:host_adapter.adapt_expansion(language=language,
      base_semantics=base_semantics,marked_semantics=marked_semantics,expansion_checker=checker,**req,tick=tick),
      req,ValueError,prefix='six-rule receptor adapter: exact actual original host')]
    req_source=copy.deepcopy(point['request']);req_source['port_bindings']['inputs'][0]['source']['row']=9
    # Rebuild syntax for the modified provenance, so physical adapter checking is exercised.
    rr={k:v for k,v in req_source.items()if k not in('proposal','state','row_assignment')}
    req_source['proposal']=producer.expand_family(**rr,tick=tick)
    host_fail.append(rejected('wrong-actual-port-source',lambda:host_adapter.adapt_expansion(language=language,
      base_semantics=base_semantics,marked_semantics=marked_semantics,expansion_checker=checker,**req_source,tick=tick),
      req_source,ValueError,prefix='six-rule receptor adapter: exact actual input source'))
    passed(8,host_fail)

    ax_record=one({'rule':'axiom','name':ax_name,'formula':A},[])
    duplicate=copy.deepcopy(ax_record['request']['registry'][0]);duplicate['body'].append(copy.deepcopy(duplicate['body'][0]));duplicate['body'][1]['id']='duplicate';duplicate=finish(duplicate)
    dup_record=expand('shared-physical-member',[duplicate],duplicate['family_id'],ax_record['request']['substitution'],bindings([]))
    dup_rows={'schema':'receptor-family-six-rule-row-assignment-v1','input_rows':[],
        'node_rows':[[n['id'],0]for n in dup_record['proposal']['primitive_nodes']]}
    shared=adapt('same-full-placement-once',dup_record,dup_rows)
    require(shared['result']['costs']['expanded_nodes']==2 and shared['result']['costs']['unique_member_placements']==1,
            'shared exact placement counted once, expanded commands retained')
    remote_subst=copy.deepcopy(subst);remote_subst['A']['body']=['bot']
    remote_ports=bindings([('in_a',['bot'],0),('in_ab',['imp',['bot'],B],1),('in_bc',['imp',B,C],2)])
    remote=expand('remote-boundary-conflict',[base],base['family_id'],remote_subst,remote_ports)
    remote_rows={'schema':'receptor-family-six-rule-row-assignment-v1','input_rows':[['in_a',0],['in_ab',1],['in_bc',2]],
        'node_rows':[[n['id'],3+i]for i,n in enumerate(remote['proposal']['primitive_nodes'])]}
    remote_req=dict(remote['request'],proposal=remote['proposal'],state=copy.deepcopy(state),row_assignment=remote_rows)
    conflict=rejected('remote-row-zero-mark',lambda:host_adapter.adapt_expansion(language=language,
      base_semantics=base_semantics,marked_semantics=marked_semantics,expansion_checker=checker,**remote_req,tick=tick),
      remote_req,ValueError,prefix='six-rule receptor adapter: current whole point legality: ')
    unused=copy.deepcopy(ax_record['request']['registry'][0])
    unused['parameters'].append(abstraction('Unused'))
    unused['inputs'].append(input_port('unused',meta('Unused')));unused=finish(unused)
    us=copy.deepcopy(ax_record['request']['substitution']);us['Unused']={'formal_names':[],'body':['bot']}
    ur=expand('unused-interface-contradiction',[unused],unused['family_id'],us,bindings([('unused',['bot'],0)]))
    uq=dict(ur['request'],proposal=ur['proposal'],state=copy.deepcopy(state),
       row_assignment={'schema':'receptor-family-six-rule-row-assignment-v1',
        'input_rows':[['unused',0]],'node_rows':[[ur['proposal']['primitive_nodes'][0]['id'],0]]})
    unused_failure=rejected('unused-port-final-formula-disagrees',lambda:host_adapter.adapt_expansion(
      language=language,base_semantics=base_semantics,marked_semantics=marked_semantics,
      expansion_checker=checker,**uq,tick=tick),uq,ValueError,
      prefix='six-rule receptor adapter: literal final external input marking')
    distinct=copy.deepcopy(ax_record['request']['registry'][0])
    distinct['inputs']=[input_port('d0',meta('Output'),'DISTINCT_SOURCE_REQUIRED'),
                        input_port('d1',meta('Output'),'DISTINCT_SOURCE_REQUIRED')]
    distinct=finish(distinct)
    physical_parent=copy.deepcopy(duplicate)
    physical_parent['dependencies']=[distinct['family_id']]
    physical_parent['body'].append({'id':'dc','kind':'FAMILY_CALL','family_ref':distinct['family_id'],
      'substitution':{pid:{'formal_variables':[],'body':meta(pid)}
                       for pid in ('Output',)},
      'ordered_inputs':[{'step':'member'},{'step':'duplicate'}],'ordered_hypotheses':[]})
    # The axiom name is a LITERAL argument; only Output is a family parameter here.
    physical_parent=finish(physical_parent)
    physical=expand('nested-distinct-logical-IDs',[distinct,physical_parent],physical_parent['family_id'],
       ax_record['request']['substitution'],bindings([]))
    nodes=physical['proposal']['primitive_nodes']
    pq=dict(physical['request'],proposal=physical['proposal'],state=copy.deepcopy(state),
      row_assignment={'schema':'receptor-family-six-rule-row-assignment-v1','input_rows':[],
        'node_rows':[[n['id'],0 if i<2 else 1]for i,n in enumerate(nodes)]})
    physical_failure=rejected('nested-distinct-collapse-to-one-placement',lambda:host_adapter.adapt_expansion(
      language=language,base_semantics=base_semantics,marked_semantics=marked_semantics,
      expansion_checker=checker,**pq,tick=tick),pq,ValueError,
      prefix='six-rule receptor adapter: physical call input sharing policy')
    passed(9,{'shared':shared,'remote_conflict':conflict,'unused_interface':unused_failure,
              'nested_physical_distinct':physical_failure})
    unknown=producer.expand_family(**core['request'],tick=tick,limits={'work':1})
    require(unknown['status']=='UNKNOWN'and unknown['primitive_nodes']==[]and unknown['request']is None,
            'bounded incomplete expansion clears partial data')
    checker_unknown=checker.check_expansion(**core['request'],proposal=core['proposal'],tick=tick,limits={'work':1})
    require(checker_unknown['status']=='UNKNOWN'and checker_unknown['expansion']is None
        and checker_unknown['conditional_expansion_checked']is False,'independent unfinished expansion clears acceptance')
    unknown_request=dict(point['request'],proposal=unknown)
    adapter_unknown=host_adapter.adapt_expansion(language=language,base_semantics=base_semantics,
      marked_semantics=marked_semantics,expansion_checker=checker,**unknown_request,tick=tick)
    require(adapter_unknown['status']=='UNKNOWN'and adapter_unknown['members']==[]
       and adapter_unknown['union_state']is None and adapter_unknown['local_point_union_checked']is False,
       'unresolved conditional expansion never becomes a local cluster')
    empty=producer.match_family(registry=[base],family_id=base['family_id'],host=host,
      receptors=ports,candidate_bindings=[],tick=tick)
    require(empty['status']=='UNKNOWN'and empty['matching_complete']is False,'empty proposals not absence proof')
    marker=DeclaredControlInterruption('declared native-first compiler callback seam')
    def interrupted_tick():
        tick();raise marker
    try:producer.expand_family(**core['request'],tick=interrupted_tick)
    except BaseException as error:require(error is marker,'external timeout propagated unchanged')
    else:raise ValueError('Root receptor component: injected callback interruption swallowed')
    passed(10,{'own_work_limit':unknown,'checker_work_limit':checker_unknown,
      'adapter_unresolved_expansion':adapter_unknown,'empty_candidate_prefix':empty,
      'declared_native_first_interruption_propagated':True,'real_native_deadline_exhaustion_tested':False})
    require(canonical(state)==initial,'input state unchanged by all hypothetical clusters')
    require(language.kernel.visits>=visits_before,'native cumulative visits never reset')
    for record in records:
        if 'result' in record:
            result=record['result'];cost=result['costs'];node_count=len(record['request']['proposal']['primitive_nodes'])
            require(cost['expanded_nodes']==node_count and 0<=cost['unique_member_placements']<=node_count
              and cost['direct_expansion_checker_calls']==1
              and cost['native_kernel_visits_after']-cost['native_kernel_visits_before']==cost['native_kernel_visits_delta']
              and cost['native_kernel_visits_delta']>=node_count
              and cost['direct_counts_exclude_nested_delegations']is True,'full direct cost metadata preserved')
    require(len(controls)==11 and [v['case']for v in controls]==CASES[:11],'all prior cases in declared order')
    passed(11,{'input_state_unchanged':True,'kernel_visits_before':visits_before,
       'kernel_visits_after':language.kernel.visits,'engine_search_or_rollback_exercised':False,
       'all_direct_costs_preserved':True})
    tick();return {'schema':VERSION,'controls':controls,'records':records,'negative_cases':negative,
      'original_host':host,'original_state':copy.deepcopy(state),'all_controls_completed':True,
      'proof_accepted':False,'engine_activated':False,'library_activated':False,
      'RL_accepted':False,'GCTS_advantage_claimed':False}
