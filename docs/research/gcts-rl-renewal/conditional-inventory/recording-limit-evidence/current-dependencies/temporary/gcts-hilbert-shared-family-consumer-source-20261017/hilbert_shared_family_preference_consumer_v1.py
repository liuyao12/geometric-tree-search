"""SOURCE ONLY: Hilbert family hints to one current primitive preference.

No project import, search, global decision call, graph mutation or ordering
installation. A later caller must preserve the complete native fallback and
own transactions. Prior receipts carry requests/provenance, never authority.
"""
import hashlib
import json

VERSION = 'hilbert-shared-family-fresh-primitive-preference-consumer-v1'
RESULT_SCHEMA = 'hilbert-shared-family-primitive-preference-v1'
CONTINUATION_SCHEMA = 'hilbert-shared-family-ground-continuation-v1'
ADAPTER_VERSION = 'hilbert-shared-parametric-family-native-admission-adapter-v3-current-hint-invalidation'
PRIOR_ADAPTER_VERSIONS = ('hilbert-shared-parametric-family-native-admission-adapter-v2-unknown-prefix', ADAPTER_VERSION)
ADAPTER_RESULT_SCHEMA = 'hilbert-shared-family-local-cluster-v1'
PRODUCER_VERSION = 'receptor-family-typed-expander-v1'
CHECKER_VERSION = 'receptor-family-independent-expansion-checker-v1'
ROW_SCHEMA = 'hilbert-shared-family-row-assignment-v1'
INPUT_SOURCE_SCHEMA = 'hilbert-shared-family-current-input-source-v1'
BINDING_SCHEMA = 'exact-selected-domain-membership-binding-v1'
DEFAULT_LIMITS = {'work': 1000000, 'depth': 128, 'clusters': 64, 'string_bytes': 1048576}
FLAGS = {'proposal_only': True, 'fallback_mandatory': True, 'proof_accepted': False,
    'root_proof_accepted': False, 'native_accepted': False, 'degree_or_EOF_accepted': False,
    'scheduler_or_rollback_accepted': False, 'engine_activated': False, 'marking_activated': False,
    'complete_GCTS_model_accepted': False, 'trajectory_accepted': False, 'pruning_accepted': False,
    'RL_accepted': False, 'GCTS_advantage_accepted': False, 'runtime_qualified': False, 'ROOT_resource_accepted': False}


class PreferenceDataError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__('Hilbert family preference '+code+': '+detail)


class _Unfinished(Exception):
    pass


class _CallbackFailure(BaseException):
    def __init__(self, error):
        self.error = error


def require(ok, code, detail):
    if not ok:raise PreferenceDataError(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


class _Work:
    def __init__(self, tick, limits):
        require(callable(tick), 'TICK', 'original cumulative native endpoint')
        self.tick=tick;self.steps=0;self.limits=dict(DEFAULT_LIMITS)
        if limits is not None:
            require(type(limits)is dict and set(limits)<=set(self.limits), 'LIMITS', 'known bounded fields')
            for key,value in limits.items():
                require(type(value)is int and 0<value<=self.limits[key], 'LIMITS', 'exact positive allowance')
                self.limits[key]=value

    def step(self, depth=0):
        if self.steps>=self.limits['work'] or depth>self.limits['depth']:
            raise _Unfinished('FINITE_CONSUMER_WORK_OR_DEPTH')
        try:self.tick()
        except BaseException as error:raise _CallbackFailure(error) from error
        self.steps+=1

    def copy(self, value, depth=0):
        self.step(depth)
        if value is None or type(value)in(bool,int):return value
        if type(value)is str:
            if len(value.encode('utf8'))>self.limits['string_bytes']:raise _Unfinished('FINITE_CONSUMER_STRING_ALLOWANCE')
            return value
        if type(value)is list:return [self.copy(item,depth+1)for item in value]
        require(type(value)is dict and all(type(key)is str for key in value), 'JSON', 'strict builtin JSON data')
        return {self.copy(key,depth+1):self.copy(item,depth+1)for key,item in value.items()}

    def call(self, function, *args, **kwargs):
        self.step();value=function(*args,**kwargs);self.step();return value

    def report(self):return {'steps':self.steps,'limits':dict(self.limits)}


def consume_preferences(*, graph, point_core, host_adapter, producer, expansion_checker,
                        context_checker, logical_oracle, closed_inputs, qualification,
                        decision, clusters, continuation, prototype_census, tick, limits=None):
    """Freshly re-admit all offered alternatives, then prefer one legal member.

    The original ground request/identity survives continuation; actual physical
    source/occupancy and whole proposal/admission are regenerated on every call.
    No family count, absence or UNKNOWN can supply a graph degree or exclusion.
    """
    work=_Work(tick,limits);names={};state=host=request=None;observations=[];authenticated=False
    decision_value=None;entry_raw=None
    def merge(entries):
        require(type(entries)is list, 'CENSUS', 'complete literal ID/preimage list')
        for pair in entries:
            work.step()
            require(type(pair)is list and len(pair)==2 and all(type(v)is str for v in pair), 'CENSUS', 'full ID/preimage strings')
            ident,preimage=pair
            if ident in names:require(names[ident]==preimage, 'COLLISION', 'full preimage mismatch across all alternatives')
            else:names[ident]=preimage
    def census():return [[key,value]for key,value in sorted(names.items())]
    def result(status,reason,candidate=None,pending=None):
        return {'schema':RESULT_SCHEMA,'version':VERSION,'status':status,'reason':reason,
            'request':request,'host':host,'current_state':state,'decision':decision_value,
            'current_branch_authenticated':authenticated,'candidate':candidate,'continuation':pending,
            'observations':observations,'prototype_census':census(),
            'census_join_completed':status!='UNKNOWN' or reason=='FRESH_ADMISSION_UNKNOWN',
            'work':work.report(),'flags':dict(FLAGS)}
    try:
        require(type(decision)is point_core.Decision and type(decision.kind)is str
                and all(value is None or type(value)is int for value in (decision.row,decision.count,decision.generation)),
                'DECISION', 'exact native Decision fields, no arbitrary row object')
        decision_value={'kind':decision.kind,'row':decision.row,'count':decision.count,'generation':decision.generation}
        request={'clusters':work.copy(clusters),'continuation':work.copy(continuation),
            'prototype_census':work.copy(prototype_census),'qualification':work.copy(qualification),
            'decision':work.copy(decision_value)}
        entry_raw=canonical(request)
        require(type(clusters)is list and (continuation is None or type(continuation)is dict), 'REQUEST', 'batch list or explicit continuation')
        require(host_adapter.VERSION==ADAPTER_VERSION and producer.VERSION==PRODUCER_VERSION
                and expansion_checker.VERSION==CHECKER_VERSION, 'APIS', 'exact native/ordinary expansion/independent protocols')
        merge(request['prototype_census'])
        host=work.copy(work.call(host_adapter.describe_host,graph=graph,context_checker=context_checker,
            closed_inputs=closed_inputs,qualification=qualification,tick=work.step))
        state=work.copy(work.call(graph.semantic_state))
        def finish():
            fresh=work.call(host_adapter.describe_host,graph=graph,context_checker=context_checker,
                closed_inputs=closed_inputs,qualification=qualification,tick=work.step)
            require(canonical(fresh)==canonical(host) and canonical(work.call(graph.semantic_state))==canonical(state),
                    'MUTATION', 'whole current host/semantic state unchanged')
            require(canonical({'clusters':work.copy(clusters),'continuation':work.copy(continuation),
                'prototype_census':work.copy(prototype_census),'qualification':work.copy(qualification),
                'decision':work.copy(decision_value)})==entry_raw, 'MUTATION', 'all literal caller inputs unchanged')
            require(host_adapter.VERSION==ADAPTER_VERSION and producer.VERSION==PRODUCER_VERSION
                    and expansion_checker.VERSION==CHECKER_VERSION, 'APIS', 'same component protocols')
        if continuation is None:
            offered=request['clusters']
        else:
            require(not clusters, 'CONTINUATION', 'no silently combined fresh batch')
            value=request['continuation']
            require(set(value)=={'schema','version','source_cluster','source_request','source_request_sha256',
                'entry_host','entry_state','last_preference_key','latest_admission','prototype_census'}
                and value['schema']==CONTINUATION_SCHEMA and value['version']==VERSION,
                'CONTINUATION', 'exact separate Hilbert ground continuation wire')
            require(canonical(value['source_request'])==canonical(value['source_cluster']['request'])
                    and value['source_request_sha256']==digest(value['source_request']),
                    'CONTINUATION', 'whole immutable source request, no digest-only identity')
            latest=value['latest_admission']
            require(type(latest)is dict and latest['schema']==ADAPTER_RESULT_SCHEMA
                    and latest['version']==ADAPTER_VERSION and latest['status']=='READY_LOCAL_CLUSTER'
                    and canonical(latest['host'])==canonical(value['entry_host'])
                    and canonical(latest['current_state'])==canonical(value['entry_state'])
                    and all(canonical(latest['request'][key])==canonical(value['source_request'][key])
                            for key in ('registry','family_id','substitution','row_assignment')),
                    'CONTINUATION', 'whole prior admission/context and immutable ground family identity')
            merge(value['prototype_census']);offered=[value['source_cluster']]
        if len(offered)>work.limits['clusters']:raise _Unfinished('FINITE_OFFERED_CLUSTER_ALLOWANCE')
        # Merge all literal previously exposed names before validating any one
        # alternative; never combine their hypothetical t/m point unions.
        for cluster in offered:
            require(type(cluster)is dict and cluster['schema']==ADAPTER_RESULT_SCHEMA
                    and cluster['version']in PRIOR_ADAPTER_VERSIONS
                    and cluster['status']=='READY_LOCAL_CLUSTER', 'CLUSTER', 'full prior Hilbert local packet, never an arithmetic relabel')
            merge(cluster['prototype_census'])
            ground=cluster['request']
            require(type(ground)is dict and set(ground)=={'registry','family_id','host','substitution',
                'port_bindings','proposal','row_assignment','prototype_census'}, 'GROUND', 'complete original ground request')
            merge(ground['prototype_census'])
        if decision.kind!='branch':
            finish();return result('INVALIDATED','NON_BRANCH_REQUEST_NO_PREFERENCE')
        # Public native endpoint independently checks the actual mandatory global
        # decision, graph instance, authority, revision and full tracked state.
        # Stale/forged branch objects raise unchanged native errors, never pruning.
        token=work.call(graph.membership_binding,decision)
        require(type(token)is tuple and len(token)==9 and token[0]==BINDING_SCHEMA and token[1]is graph,
                'BINDING', 'exact native ephemeral selected-domain binding')
        authenticated=True
        def finish_branch():
            finish();fresh=work.call(graph.membership_binding,decision)
            require(type(fresh)is tuple and len(fresh)==9 and fresh[0]==token[0] and fresh[1]is token[1]
                    and fresh[2:7]==token[2:7] and fresh[7]is token[7] and fresh[8]is token[8],
                    'MUTATION', 'same public native revision/state/domain identity at return')
        selected_rows={}
        for key_data in state['order']:
            require(type(key_data)is list and len(key_data)==3 and type(key_data[0])is int
                    and type(key_data[1])is int and type(key_data[2])is list
                    and all(type(row)is int for row in key_data[2]), 'STATE', 'actual native selected key')
            key=point_core.Key(key_data[0],key_data[1],tuple(key_data[2]))
            placement=work.copy(work.call(graph.decorate,key))
            require(canonical(placement['key'])==canonical(key_data) and key.row not in selected_rows,
                    'STATE', 'one exact selected source placement per row')
            merge([[placement['identity_preimage']['prototype_id'],canonical(placement['identity_preimage']['prototype_preimage'])],
                   [placement['id'],canonical(placement['identity_preimage'])]])
            selected_rows[key.row]=placement
        ready=[];unknown=False;invalidated=False
        for index,cluster in enumerate(offered):
            work.step();ground=cluster['request']
            if canonical(ground['host'])!=canonical(host):
                observations.append({'offer_index':index,'status':'INVALIDATED','reason':'GROUND_HOST_OR_AUTHORITY_CHANGED',
                    'source_cluster':cluster,'current_admission':None})
                invalidated=True;continue
            rows=ground['row_assignment'];old_ports=ground['port_bindings']
            require(type(rows)is dict and set(rows)=={'schema','node_rows','input_rows'} and rows['schema']==ROW_SCHEMA
                    and type(old_ports)is dict and set(old_ports)=={'hypotheses','inputs','outputs'},
                    'GROUND', 'whole physical row/port schema')
            input_rows={}
            for item in rows['input_rows']:
                require(type(item)is list and len(item)==2 and type(item[0])is str
                        and item[0]not in input_rows and type(item[1])is int and 0<=item[1]<24,
                        'GROUND', 'unique literal actual input rows')
                input_rows[item[0]]=item[1]
            current_inputs=[]
            for port in old_ports['inputs']:
                require(type(port)is dict and set(port)=={'port_id','formula','source','occupied','fact_accepted'}
                        and type(port['port_id'])is str and port['port_id']in input_rows and port['fact_accepted']is False,
                        'GROUND', 'exact original input formula/port, no source fact')
                row=input_rows[port['port_id']];selected=selected_rows.get(row)
                current_inputs.append({'port_id':port['port_id'],'formula':work.copy(port['formula']),
                    'source':{'schema':INPUT_SOURCE_SCHEMA,'row':row,'model_epoch':state['model_epoch'],
                        'context_id':host['binding']['context_id'],'selected_key':None if selected is None else work.copy(selected['key']),
                        'selected_placement':None if selected is None else work.copy(selected)},
                    'occupied':state['totals'][row]==1,'fact_accepted':False})
            ports={'hypotheses':work.copy(old_ports['hypotheses']),'inputs':current_inputs,'outputs':work.copy(old_ports['outputs'])}
            proposal=work.copy(work.call(producer.expand_family,registry=work.copy(ground['registry']),family_id=ground['family_id'],
                host=work.copy(host),substitution=work.copy(ground['substitution']),port_bindings=work.copy(ports),tick=work.step))
            admission_census=census()
            expected_current={'registry':work.copy(ground['registry']),'family_id':ground['family_id'],
                'host':work.copy(host),'substitution':work.copy(ground['substitution']),'port_bindings':work.copy(ports),
                'proposal':work.copy(proposal),'row_assignment':work.copy(rows),'prototype_census':work.copy(admission_census)}
            fresh=work.copy(work.call(host_adapter.adapt_expansion,graph=graph,point_core=point_core,
                context_checker=context_checker,logical_oracle=logical_oracle,closed_inputs=closed_inputs,
                qualification=qualification,expansion_checker=expansion_checker,registry=work.copy(ground['registry']),
                family_id=ground['family_id'],host=work.copy(host),substitution=work.copy(ground['substitution']),
                port_bindings=work.copy(ports),proposal=proposal,row_assignment=work.copy(rows),prototype_census=admission_census,tick=work.step))
            require(fresh['schema']==ADAPTER_RESULT_SCHEMA and fresh['version']==ADAPTER_VERSION
                    and fresh['status']in ('READY_LOCAL_CLUSTER','UNKNOWN','INVALIDATED')
                    and canonical(fresh['current_state'])==canonical(state) and canonical(fresh['host'])==canonical(host)
                    and canonical(fresh['request'])==canonical(expected_current),
                    'ADMISSION', 'literal fresh current adapter protocol, no old receipt normalization')
            merge(fresh['prototype_census'])
            observations.append({'offer_index':index,'source_cluster':cluster,'current_admission':fresh,
                'status':fresh['status'],'reason':fresh['reason']})
            if fresh['status']=='READY_LOCAL_CLUSTER':
                require(fresh['local_primitive_members_checked']is True and fresh['local_current_point_union_checked']is True,
                        'ADMISSION', 'full fresh independent/native union required')
                ready.append((cluster,ground,fresh))
            elif fresh['status']=='UNKNOWN':unknown=True
            else:invalidated=True
        candidate=None;chosen=None
        for cluster,ground,fresh in ready:
            for member in fresh['members']:
                placement=member['placement']
                if placement['key'][1]!=decision.row or member['already_selected_in_input']:continue
                key_data=placement['key'];key=point_core.Key(key_data[0],key_data[1],tuple(key_data[2]))
                require(work.call(graph.legal,key)is True, 'MEMBERSHIP', 'fresh chosen primitive still in complete actual current domain')
                candidate=work.copy(placement);chosen=(cluster,ground,fresh);break
            if candidate is not None:break
        if chosen is None:
            for item in ready:
                if any(not member['already_selected_in_input']for member in item[2]['members']):
                    chosen=item;break
        pending=None
        if chosen is not None:
            cluster,ground,fresh=chosen
            pending={'schema':CONTINUATION_SCHEMA,'version':VERSION,'source_cluster':work.copy(cluster),
                'source_request':work.copy(ground),'source_request_sha256':digest(ground),
                'entry_host':work.copy(host),'entry_state':work.copy(state),
                'last_preference_key':None if candidate is None else work.copy(candidate['key']),
                'latest_admission':work.copy(fresh),'prototype_census':census()}
        finish_branch()
        if candidate is not None:return result('READY','FRESH_PRIMITIVE_PREFERENCE_ONLY',candidate,pending)
        if unknown:return result('UNKNOWN','FRESH_ADMISSION_UNKNOWN',pending=pending)
        if invalidated and not ready:return result('INVALIDATED','ALL_OFFERED_HINTS_LOCALLY_INVALIDATED')
        return result('NO_MATCH','NO_MATCH_IN_ADVISORY_POOL_NOT_BASE_ABSENCE',pending=pending)
    except _CallbackFailure as failure:
        raise failure.error
    except _Unfinished as unfinished:
        return result('UNKNOWN',str(unfinished))
