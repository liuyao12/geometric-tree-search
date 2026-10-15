"""UNEXECUTED M8 adapter: genuine8d22 APIs on disclosed NONLOGICAL fixtures.

No original Q preparation, word, target or theorem is constructed. The cold
caller authenticates/compiles/seals this Source and the actual point module.
The source_guard below complements that caller; it is not a hostile VM sandbox.
"""
import copy
import hashlib
import json
import resource
import sys
import time
import types

VERSION = 'Q-neutral-genuine-point-scheduler-adapter-v1'
POINT_RECORD = {'path': '/Users/liuyao/Documents/Codex/projects/geometric-tree-search/.gcts-active/arithmetic-open-generalize-implementation-source-20261014/arithmetic_q_point_graph_v1.py', 'sha256': '8d22ea390c675349fc9c90057cd152a4d0e75024bb365d70116cef0656597567', 'bytes': 28531}
FIXTURE_RECORD = {'sha256': '1420cd2c0a56d09e629ca65fe4b7f690570ccb283b1998762c10de1190180575', 'bytes': 62584}
SURFACE = 'NONLOGICAL-point-scheduler'
GRAPH_METHODS = ('point_data', '_compatible', 'candidates', 'decision', 'checkpoint',
                 '_apply_legal', 'rollback', 'semantic_state', 'validate_cluster', 'legal')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def sha(value):
    return hashlib.sha256(canonical(value).encode('utf8')).hexdigest()


def function_state(fn):
    if type(fn) is type:
        return ('class', fn, fn.__mro__, fn.__new__, function_state(fn.__init__))
    if type(fn) is types.MethodType:
        owner, fn = fn.__self__, fn.__func__
    else:
        owner = None
    require(type(fn) is types.FunctionType, 'exact original Python function/method')
    return (owner, fn, fn.__code__, fn.__defaults__, fn.__kwdefaults__,
            tuple((cell, cell.cell_contents) for cell in fn.__closure__ or ()))


def same_function(fn, state):
    if type(state[0]) is str and state[0] == 'class':
        return (type(fn) is type and fn is state[1] and fn.__mro__ is state[2]
                and fn.__new__ is state[3] and same_function(fn.__init__, state[4]))
    if type(fn) is types.MethodType:
        owner, fn = fn.__self__, fn.__func__
    else:
        owner = None
    return (owner is state[0] and fn is state[1] and fn.__code__ is state[2]
            and fn.__defaults__ is state[3] and fn.__kwdefaults__ is state[4]
            and len(fn.__closure__ or ()) == len(state[5])
            and all(cell is old and cell.cell_contents is value
                    for cell, (old, value) in zip(fn.__closure__ or (), state[5])))


class Gate:
    """One original interval and synchronous full caller guard per operation.

    Whole module/global/builtin/class/MRO/property/actual instance custody is a
    cold-caller prerequisite, not proved by the raw pin/function state alone.
    Deliberate mutation must occur in separate disposable controls, never here.
    """
    def __init__(self, guard, began_ns, deadline_ns):
        require(type(guard) is types.FunctionType, 'exact genuine cold caller guard function')
        require(type(began_ns) is int and type(deadline_ns) is int
                and 0 <= began_ns < deadline_ns and deadline_ns-began_ns == 20_000_000_000,
                'unchanged original joint20 native interval')
        self.guard, self.guard_state = guard, function_state(guard)
        self.clock, self.usage = time.perf_counter_ns, resource.getrusage
        self.began, self.deadline, self.extra = began_ns, deadline_ns, None
        self.need, self.state, self.same = require, function_state, same_function
        self.need_code, self.state_code, self.same_code = require.__code__, function_state.__code__, same_function.__code__
        self.check_fn, self.check_code = Gate.check, Gate.check.__code__
        self.check()

    def check(self):
        for phase in (0, 1):
            if (require is not self.need or require.__code__ is not self.need_code
                    or function_state is not self.state or function_state.__code__ is not self.state_code
                    or same_function is not self.same or same_function.__code__ is not self.same_code
                    or Gate.check is not self.check_fn or Gate.check.__code__ is not self.check_code
                    or time.perf_counter_ns is not self.clock or resource.getrusage is not self.usage):
                raise ValueError('original synchronous guard/native/helper endpoint changed')
            if not self.same(self.guard, self.guard_state):
                raise ValueError('actual cold caller guard function/default/closure changed')
            if self.extra is not None and not self.same(self.extra[0], self.extra[1]):
                raise ValueError('actual runner guard function/default/closure changed')
            now = self.clock()
            if now >= self.deadline or now-self.began >= 55_000_000_000:
                raise TimeoutError('complete M8 work exceeded original interval')
            if self.usage(resource.RUSAGE_SELF).ru_maxrss >= 500*1024*1024:
                raise TimeoutError('M8 native self guidance memory exceeded')
            if phase == 0:
                self.guard()
                if self.extra is not None:
                    self.extra[0]()

    def invoke(self, fn, *args, capture_rejection=False, **kwargs):
        state = function_state(fn)
        if Gate.check is not self.check_fn or Gate.check.__code__ is not self.check_code:
            raise ValueError('original immediate operation precheck changed')
        self.check_fn(self)
        if not same_function(fn, state):
            raise ValueError('actual operation changed during preguard')
        error, result = None, None
        try:
            result = fn(*args, **kwargs)
        except ValueError as failure:
            if not capture_rejection:
                raise
            error = {'type': type(failure).__name__, 'message': str(failure)}
        if Gate.check is not self.check_fn or Gate.check.__code__ is not self.check_code:
            raise ValueError('original immediate operation postcheck changed')
        self.check_fn(self)
        if not same_function(fn, state):
            raise ValueError('actual operation changed during delegation')
        return (result, error) if capture_rejection else result


def graph_call(gate, graph, anchors, name, *args, **kwargs):
    method = getattr(graph, name)
    require(type(method) is types.MethodType and method.__self__ is graph
            and same_function(method, anchors[name]), 'exact effective constructed graph method')
    return gate.invoke(method, *args, **kwargs)


def executor_step(gate, point, executor, key):
    method = executor.step
    require(type(executor) is point.Executor and type(method) is types.MethodType
            and method.__self__ is executor and method.__func__ is point.Executor.step,
            'exact effective genuine Executor.step endpoint')
    return gate.invoke(method, key)


def scan(gate, graph, anchors):
    state = graph_call(gate, graph, anchors, 'semantic_state')
    rows = []
    for row in range(graph.height):
        iterator = graph_call(gate, graph, anchors, 'candidates', row)
        keys = []
        while True:
            gate.check()
            require(same_function(graph.candidates, anchors['candidates']), 'effective generator endpoint stable')
            try:
                key = next(iterator)
            except StopIteration:
                break
            keys.append(gate.invoke(key.data))
            gate.check()
        rows.append({'row': row, 'keys': keys, 'EOF': True,
                     'saved_count': state['domains'][row]['count'],
                     'enumerated_count': len(keys)})
        require(len(keys) == state['domains'][row]['count'], 'whole actual tiny row domain EOF agrees')
    gate.check()
    return {'state': state, 'rows': rows, 'whole_state_sha256': sha(state), 'all_rows_EOF': True}


def make_graph(gate, point, formulas, recipes, case_id, *, fixed=(), roots=None, seeds=(), premises=()):
    authority = {'activated': False, 'native_accepted': False,
                 'scope': 'NONLOGICAL-M8-only', 'case_id': case_id,
                 'point_source': POINT_RECORD, 'fixture_sha256': FIXTURE_RECORD['sha256']}
    authority['epoch'] = gate.invoke(point.digest, authority)
    graph = gate.invoke(point.PointGraph, height=len(roots), formulas=formulas,
        recipe_data=recipes, context={'ordered_local_premises': list(premises),
            'scope': 'NONLOGICAL-auxiliary-fixture-not-original-Q', 'case_id': case_id},
        authority=authority, fixed_marks=tuple(fixed), roots=tuple(roots), seed_keys=tuple(seeds),
        fixture=True, source_bindings={'point_graph': POINT_RECORD})
    require(type(graph) is point.PointGraph and graph.fixture is True, 'genuine complete fixture constructor')
    anchors = {name: function_state(getattr(graph, name)) for name in GRAPH_METHODS}
    executor = gate.invoke(point.Executor, graph)
    return graph, anchors, executor


def zero_recipe(name, formula):
    return {'id': name, 'primitive_witness': {'rule': 'fixture_zero', 'formula': formula},
            'ordered_premise_formulas': []}


def run_case(gate, point, case, expected):
    case_id, prefix = case['id'], case['id'].split('-')[0]
    evidence = {'point_source': POINT_RECORD, 'NONLOGICAL': True,
                'original_Q_model_used': False, 'original_Q_problem_equivalence_claimed': False,
                'observations_source': 'actual8d22 engine methods, not literal expected oracle'}
    if prefix in ('M01', 'M02', 'M03'):
        declared = case['required_points']
        formulas = [['NONLOGICAL', case_id, 'row', row] for row in range(len(declared))]
        recipes, identities = [], {}
        for row, entry in enumerate(declared):
            for name in entry['candidates']:
                identities[len(recipes)] = name
                recipes.append(zero_recipe(name, formulas[row]))
        graph, anchors, executor = make_graph(gate, point, formulas, recipes, case_id,
            fixed=[(1,row,row) for row in range(len(declared))], roots=[entry['generation'] for entry in declared])
        initial = scan(gate, graph, anchors)
        decision = graph_call(gate, graph, anchors, 'decision')
        observed = {'decision': decision.kind, 'point': declared[decision.row]['id']}
        if decision.kind == 'forced':
            key = next(graph_call(gate, graph, anchors, 'candidates', decision.row))
            observed['candidate'] = identities[key.recipe]
        evidence.update({'mapping': {'required_point_to_engine_row': [[entry['id'],row] for row,entry in enumerate(declared)],
            'output_code_by_row': list(range(len(declared))), 'literal_roots': graph.roots,
            'candidate_identity_to_recipe_index': [[name,index] for index,name in identities.items()]},
            'initial_complete_scan': initial, 'decision': {'kind':decision.kind,'row':decision.row,
                'count':decision.count,'generation':decision.generation}, 'observed':observed,
            'scope': 'real global dead/forced/earliest-generation decision on compiled NONLOGICAL zero-port groups'})
        passed = observed == expected
    elif prefix in ('M04', 'M05'):
        formulas = [['NONLOGICAL', case_id, 'code0']]
        graph, anchors, executor = make_graph(gate, point, formulas, [zero_recipe('compatibility-carrier',formulas[0])],
            case_id, fixed=case['current_m'], roots=[0])
        initial = scan(gate, graph, anchors)
        point_literal = tuple(case['candidate_m'][0][:2]); value = case['candidate_m'][0][2]
        compatible = graph_call(gate, graph, anchors, '_compatible', point_literal, value)
        key = gate.invoke(point.Key,0,0,())
        actual_data = graph_call(gate,graph,anchors,'point_data',key)
        evidence.update({'initial_complete_scan':initial,'observed':{'compatible':compatible},
            'literal_point':list(point_literal),'literal_value':value,
            'actual_carrier_key':gate.invoke(key.data),'actual_carrier_point_data':actual_data,
            'carrier_emits_literal_arbitrary_mark':any(tuple(mark[:2])==point_literal for mark in actual_data[1]),
            'scope':'exact arbitrary mark-only compatibility API only; production point_data does not emit(7,9), no arbitrary-candidate pruning qualification'})
        passed = type(compatible) is bool and compatible is expected['compatible']
    elif prefix in ('M06', 'M07'):
        formula = ['NONLOGICAL',case_id,'code0']
        placement_ids = [entry['id'] for entry in case['primitive_placements']]
        recipes = [zero_recipe(name,formula) for name in placement_ids]
        graph, anchors, executor = make_graph(gate,point,[formula],recipes,case_id,roots=[0])
        initial = scan(gate,graph,anchors)
        by_name = {name:gate.invoke(point.Key,index,0,()) for index,name in enumerate(placement_ids)}
        keys = tuple(by_name[name] for name in case['cluster_members'])
        members,error = graph_call(gate,graph,anchors,'validate_cluster',keys,graph.model_epoch,capture_rejection=True)
        evidence.update({'mapping':{'positive_point':[0,0],'descriptor_mark':[7,9],'engine_mark':[1,0],
            'value_code0':0,'placement_id_to_key':[[name,gate.invoke(key.data)] for name,key in by_name.items()]},
            'initial_complete_scan':initial,'requested_keys':[gate.invoke(key.data) for key in keys],
            'validation_error':error,'scope':'genuine exact Key identity deduplication or distinct positive overfill; NONLOGICAL model'})
        if prefix=='M06':
            require(error is None, 'shared exact key cluster must return actual members')
            checkpoint = graph_call(gate,graph,anchors,'checkpoint')
            executor_step(gate,point,executor,members[0])
            placed = scan(gate,graph,anchors)
            graph_call(gate,graph,anchors,'rollback',checkpoint)
            restored = scan(gate,graph,anchors)
            actual_total = [[0,row,total] for row,total in enumerate(placed['state']['totals']) if total]
            evidence.update({'returned_members':[gate.invoke(key.data) for key in members],
                'placed':placed,'restored':restored,'observed':{'distinct_placements':len(members),'total_t':actual_total}})
            passed = evidence['observed']==expected and restored['state']==initial['state']
        else:
            restored = scan(gate,graph,anchors)
            evidence.update({'after_rejection':restored,'observed':{'compatible':error is None}})
            passed = error is not None and error['type']=='ValueError' and 'overfill' in error['message'] and restored['state']==initial['state'] and expected['compatible'] is False
    elif prefix=='M08':
        # Injective extension: all descriptor rows0/1/2 ->1/2/3. Source row0
        # is an additional occupied toy assumption, not an original Q hypothesis.
        formulas = [['NONLOGICAL',case_id,'code',code] for code in range(4)]
        recipes = [{'id':'auxiliary-code0-occurrence','primitive_witness':{'rule':'assumption','index':0,'formula':formulas[0]},'ordered_premise_formulas':[]}]
        for name,code in (('a',1),('b',2)):
            recipes.append({'id':name,'primitive_witness':{'rule':'opaque_pair','formula':formulas[code]},
                            'ordered_premise_formulas':[formulas[0],formulas[0]]})
        recipes.append(zero_recipe('unused-original-row2-carrier',formulas[3]))
        seed = gate.invoke(point.Key,0,0,())
        graph,anchors,executor = make_graph(gate,point,formulas,recipes,case_id,
            fixed=[(1,row,row) for row in (1,2,3)], roots=[0,0,0,0],seeds=[seed],premises=[formulas[0]])
        initial = scan(gate,graph,anchors); root = graph_call(gate,graph,anchors,'checkpoint')
        a,b = gate.invoke(point.Key,1,1,(0,0)),gate.invoke(point.Key,2,2,(0,0))
        first_decision = graph_call(gate,graph,anchors,'decision')
        executor_step(gate,point,executor,a)
        after_a = scan(gate,graph,anchors); child = graph_call(gate,graph,anchors,'checkpoint')
        second_decision = graph_call(gate,graph,anchors,'decision')
        executor_step(gate,point,executor,b)
        after_b = scan(gate,graph,anchors)
        graph_call(gate,graph,anchors,'rollback',child)
        child_restored = scan(gate,graph,anchors)
        graph_call(gate,graph,anchors,'rollback',root)
        root_restored = scan(gate,graph,anchors)
        def shared(scan_record):
            return next(mark for mark in scan_record['state']['marks'] if mark[:2]==[1,0])
        shared_observations = [shared(record) for record in (initial,after_a,after_b,child_restored,root_restored)]
        evidence.update({'mapping':{'original_required_rows_to_engine_rows':[[0,1],[1,2],[2,3]],
            'original_shared_mark_to_engine_mark':[[7,9],[1,0]],'mark_value0_to_formula_code0':0,
            'extra_auxiliary_row0':{'occupied':True,'toy_original_occurrence_index':0,'seed_key':gate.invoke(seed.data)},
            'extension':'extra occupied source row/seed, fixed output marks1/2/3 and ordered offset channels; not identical problem equivalence'},
            'initial_complete_scan':initial,'after_a':after_a,'after_b':after_b,
            'child_restored':child_restored,'root_restored':root_restored,
            'actual_keys':[gate.invoke(a.data),gate.invoke(b.data)],
            'actual_point_data':[graph_call(gate,graph,anchors,'point_data',a),graph_call(gate,graph,anchors,'point_data',b)],
            'actual_step_decisions':[{'kind':decision.kind,'row':decision.row,'count':decision.count} for decision in (first_decision,second_decision)],
            'actual_shared_mark_records':shared_observations,
            'observed':{'child_rollback_exact':child_restored['state']==after_a['state'],
                'root_rollback_exact':root_restored['state']==initial['state']},
            'scope':'real Executor.step/complete EOF/state/shared assigned0/refcounts/generations/rollback on explicit extended NONLOGICAL fixture',
            'nonempty_failed_child_exclusion_trail_exercised':False,
            'empty_exclusion_fields_compared':True})
        passed = (evidence['observed']['child_rollback_exact'] and evidence['observed']['root_rollback_exact']
            and [mark[2:] for mark in shared_observations]==[[0,1],[0,2],[0,3],[0,2],[0,1]]
            and [(decision.kind,decision.row) for decision in (first_decision,second_decision)]==[('forced',1),('forced',2)])
    else:
        raise ValueError('unsupported frozen M8 ID, no computed expected oracle')
    gate.check()
    return {'schema':'Q-split-neutral-surface-observation-v1','case_id':case_id,'surface':SURFACE,
        'completed':True,'observed_predicate':bool(passed),'expected_source':'frozen-neutral-fixture','evidence':evidence,
        'original_Q_theorem_accepted':False,'selected_accepted':False,'point_union_accepted':False,
        'full24_accepted':False,'trajectory_accepted':False,'ROOT_resource_accepted':False,'RL_accepted':False}


def make_point_scheduler_adapter(*, point_module, point_source_raw, point_source_record,
                                 complete_fixtures_raw, source_guard, joint_began_ns, joint_deadline_ns):
    require(sys.platform == 'darwin', 'pinned native Darwin ru_maxrss byte semantics')
    gate = Gate(source_guard,joint_began_ns,joint_deadline_ns)
    require(type(point_source_record) is dict and point_source_record==POINT_RECORD and type(point_source_raw) is bytes
            and len(point_source_raw)==POINT_RECORD['bytes'] and hashlib.sha256(point_source_raw).hexdigest()==POINT_RECORD['sha256'], 'exact same-buffer original8d22 Source')
    require(type(point_module) is types.ModuleType and point_module.__file__==POINT_RECORD['path']
            and sys.modules.get(point_module.__name__) is point_module, 'genuine registered cold-loaded point namespace/origin')
    require(type(complete_fixtures_raw) is bytes and len(complete_fixtures_raw)==FIXTURE_RECORD['bytes']
            and hashlib.sha256(complete_fixtures_raw).hexdigest()==FIXTURE_RECORD['sha256'], 'whole current52 fixture bytes')
    fixtures = json.loads(complete_fixtures_raw.decode('utf8'))
    cases = {case['id']:case for case in fixtures['point_and_scheduler_NONLOGICAL_cases']}
    require(len(cases)==8 and all(case['NONLOGICAL'] is True for case in cases.values()), 'all8 frozen NONLOGICAL cases')
    gate.check()
    def surface_adapter(*, request, literal_expected, joint_began_ns, joint_deadline_ns, source_guard):
        require(type(joint_began_ns) is int and type(joint_deadline_ns) is int
                and joint_began_ns==gate.began and joint_deadline_ns==gate.deadline,
                'same original caller interval; no reset or toy current clock')
        require(type(source_guard) is types.FunctionType, 'exact genuine runner guard function')
        require(type(request) is dict and request.get('id') in cases, 'exact current frozen M8 request')
        case = cases[request['id']]
        require(canonical(request)==canonical(case) and canonical(literal_expected)==canonical(case['expected']),
                'whole literal current case and independent frozen expectation, no altered subset')
        extra_state = function_state(source_guard)
        if gate.extra is None:
            gate.extra = (source_guard,extra_state)
        else:
            require(same_function(source_guard,gate.extra[1]), 'same genuine original runner callback')
        gate.check()
        response = run_case(gate,point_module,copy.deepcopy(case),copy.deepcopy(literal_expected))
        canonical(response); gate.check()
        return response
    return surface_adapter
