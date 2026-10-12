"""Prospective complete independent static family-pool reconstruction.

Imports only standard library and pinned older independent point/body auditors.
No producer, production graph, controller, search, ranker, decoder or native
imports. ROOT must bind exact terminal evidence and activate a reviewed owner.
Rebuilds source bodies and an independent literal initial point state; this is
more than a metadata check and cannot establish whole-target proof acceptance.
"""
import copy
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def exact_pin(path):
    path = Path(path).resolve(); h = hashlib.sha256(); count = 0
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            h.update(block); count += len(block)
    return dict(path=str(path), sha256=h.hexdigest(), bytes=count)


def verify(plan):
    for group in ('sources', 'libraries', 'inputs', 'preserved'):
        for pin in plan[group]:
            if exact_pin(pin['path']) != {k: pin[k] for k in ('path', 'sha256', 'bytes')}:
                raise ValueError('exact independent prerequisite: ' + pin['path'])


def libraries(plan):
    roles = {p['role']: Path(p['path']) for p in plan['libraries']}
    sys.path.insert(0, str(roles['independent_point'].parent))
    point = importlib.import_module('full_point_oracle_v1')
    body = importlib.import_module('full_family_registry_v1')
    sys.path.insert(0, str(roles['independent_symbolic'].parent))
    result = {}
    for role, name in [('independent_symbolic', 'independent_aggregate_audit_v1'),
                       ('independent_expansion', 'independent_family_pool_expansion_v1')]:
        spec = importlib.util.spec_from_file_location(name, roles[role])
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module; spec.loader.exec_module(module); result[role] = module
    return point, body, result['independent_symbolic'], result['independent_expansion']


def flat_pin(pin):
    return {k: pin[k] for k in ('path', 'sha256', 'bytes')}


def root_state(point, body, data, prior_point_plan, symbolic):
    model, inventory, checker, seeds, primitive_counts = point.validate_model(data, symbolic)
    boundary = model['boundary']
    fixed = sorted(boundary['fixed_exterior_m'] + boundary['fixed_target_m'])
    roots = [p[2] for p in boundary['root_generations']]
    sources = {p['role']: flat_pin(p) for p in prior_point_plan['inputs']}
    epoch = point.digest(dict(height=24, context=model['context'], registry=point.digest(data['formula_codes']),
        authority=data['authority']['epoch'], recipes=[r['id'] for r in inventory], fixed_marks=fixed,
        roots=roots, seed_keys=[body.key_data(k) for k in seeds],
        marking_version='injective-formula-ordered-mp-offset-v1', fixture=False, source_bindings=sources))
    state = point.State(24, inventory, fixed, roots, epoch)
    for key in seeds:
        state.apply(key, generation=0)
    binding = body.graph_binding(state, model['context'], data['authority'], data['formula_codes'], sources, seeds, fixed)
    return state, binding, model, primitive_counts


class IndependentPool:
    """Full literal body transport and complete binding census, no engine calls."""
    def __init__(self, point, body, state, binding, model, data, original_body_plan,
                 preparation_plan, certificate, schemas, projected, expansion):
        self.p, self.b, self.s, self.binding = point, body, state, binding
        self.context, self.authority, self.formulas = model['context'], data['authority']['epoch'], data['formula_codes']
        self.registry = point.digest(self.formulas)
        self.bodies, self.source_counts, self.source_receipts = body.family_bodies(certificate, schemas, projected, data, expansion)
        for record in self.bodies:
            record['ordered_receptor_ports'] = body.receptor_ports(record, state.recipes)
        self.original_sources = [flat_pin(p) for p in original_body_plan['inputs']]
        point.need(len(self.original_sources) == len({p['path'] for p in self.original_sources}) == 56, 'original unique body source closure')
        self.original_epoch = point.digest(dict(graph=binding, sources=self.original_sources,
            bodies=[[b['name'], point.digest(b)] for b in self.bodies], version='whole-cluster-lifecycle-v1'))
        by_name = {b['name']: b for b in self.bodies}
        interfaces = []
        for declaration in projected['definitions']:
            source = by_name[declaration['name']]
            point.need(source['full_frozen_definition_sha256'] == point.digest(declaration), 'full declared interface digest')
            row, code = point.integer(declaration['canonical_conclusion_row']), point.integer(declaration['conclusion_code'])
            outputs = [m for m in source['primitive_members'] if m['row'] == row]
            point.need(len(outputs) == 1 and point.integer(outputs[0]['formula_code']) == code, 'explicit declared member/code')
            point.need(self.formulas[code] == declaration['conclusion_ast'] and
                       [self.formulas[c] for c in source['premise_codes']] == declaration['premise_ast'], 'declared formula values')
            interfaces.append(dict(name=source['name'], body_sha256=point.digest(source),
                full_projection_sha256=point.digest(declaration), body=source, conclusion_row=row, conclusion_code=code))
        self.interfaces = sorted(interfaces, key=lambda r: point.canonical([r['name'], r['body_sha256']]))
        self.named = {r['name']: r for r in self.interfaces}
        # Derive roots from boundary seed insertion order through independent
        # State.apply; do not sort or trust producer integer root-token indices.
        self.anchors = []
        for key in state.order:
            recipe = state.recipes[key[0]]
            point.need(state.selected[key] == 0 and recipe['witness']['rule'] == 'assumption' and not key[2], 'original selected hypothesis root')
            t, m = point.points(recipe, key[1], key[2], state.height)
            self.anchors.append(dict(key=body.key_data(key), full_id=point.decorate(key,t,m,state.recipes,
                self.context,self.authority,self.registry)['id'], formula_code=recipe['output'], generation=0))
        point.need(len(self.anchors) == len(self.context['ordered_local_premises']) == 3, 'all and only original global assumptions')
        self.new_sources = [dict(path=preparation_plan['path'], sha256=preparation_plan['sha256'], bytes=preparation_plan['bytes'])]
        self.new_sources += [flat_pin(p) for p in preparation_plan['data']['sources']]
        self.group_specs, self.preliminary, self.type_visits, self.rejected = [], [], [], []
        self.disconnected = 0

    def options(self, record, prior=None):
        choices = []
        for code in record['body']['premise_codes']:
            matches = [dict(kind='root_anchor', index=index) for index, anchor in enumerate(self.anchors)
                       if anchor['formula_code'] == code]
            if prior is not None and prior['conclusion_code'] == code:
                matches.append(dict(kind='earlier_component_output', index=0))
            choices.append(matches)
        return itertools.product(*choices)

    def embedding(self, specification):
        p, b, state = self.p, self.b, self.s
        p.need(type(specification) is list and len(specification) in (1,2), 'single/pair syntax')
        initial_keys = [b.key(a['key']) for a in self.anchors]
        occupied = {k[1]: k for k in initial_keys}
        components, distinct = [], set()
        indices = {r['id']: i for i,r in enumerate(state.recipes)}
        for occurrence, spec in enumerate(specification):
            p.need(set(spec) == {'name','ordered_inputs'} and spec['name'] in self.named, 'registered component')
            record = self.named[spec['name']]; source = record['body']
            p.need(len(spec['ordered_inputs']) == len(source['premise_codes']), 'complete ordered receptors')
            inputs, provenance = [], []
            for token, code in zip(spec['ordered_inputs'], source['premise_codes']):
                p.need(set(token) == {'kind','index'}, 'exact binding token')
                index = p.integer(token['index'])
                if token['kind'] == 'root_anchor':
                    p.need(0 <= index < len(self.anchors) and self.anchors[index]['formula_code'] == code, 'root binding code')
                    anchor = self.anchors[index]; row = anchor['key'][1]
                    provenance.append(dict(binding=copy.deepcopy(token), formula_code=code, row=row,
                        key=anchor['key'], full_id=anchor['full_id'], logical_role='original recipient hypothesis'))
                else:
                    p.need(token['kind']=='earlier_component_output' and occurrence==1 and index==0,
                           'only included first output can bind second')
                    previous = components[0]
                    p.need(previous['conclusion_code']==code, 'exact declared output/receptor formula')
                    row = previous['conclusion_row']
                    output_index = next(j for j,k in enumerate(previous['members']) if k[1]==row)
                    provenance.append(dict(binding=copy.deepcopy(token), formula_code=code, row=row,
                        key=previous['members'][output_index], full_id=previous['full_member_ids'][output_index],
                        prior_component_body_sha256=previous['body_sha256'],
                        logical_role='included conditional output obligation; not a seeded premise'))
                inputs.append(row)
            if occurrence:
                p.need(any(t['kind']=='earlier_component_output' for t in spec['ordered_inputs']), 'connected pair only')
            mapping = dict(zip(source['canonical_input_rows'], inputs))
            output_rows, keys = [], []
            previous_row = -1
            for member in source['primitive_members']:
                refs = tuple(mapping[r] for r in member['ordered_inputs'])
                recipe = indices[member['recipe_id']]
                threshold = max((previous_row,) + refs)
                # Independent row-by-row scan, not producer occupied-key sort.
                row = next((r for r in range(threshold+1,state.height)
                    if r in occupied and occupied[r][0]==recipe and occupied[r][2]==refs), None)
                if row is None:
                    row = next((r for r in range(threshold+1,state.height) if r not in occupied), None)
                    if row is None:
                        return None, 'canonical_embedding_boundary_exhaustion'
                    occupied[row] = (recipe,row,refs)
                key = occupied[row]
                p.need(state.recipes[key[0]]['output']==member['formula_code'], 'literal source output')
                mapping[member['row']] = row; output_rows.append(row); keys.append(key); distinct.add(key); previous_row = row
            component = b.descriptor(source, inputs, output_rows, 0, self.binding, self.original_sources,
                self.original_epoch, state, self.context, self.authority, self.registry)
            p.need(component['members']==[b.key_data(k) for k in keys], 'body-authorized transport')
            components.append(dict(name=record['name'], body_sha256=record['body_sha256'],
                source_body_sha256=source['source_body_sha256'], mapped_body_sha256=source['mapped_body_sha256'],
                full_projection_sha256=record['full_projection_sha256'], dependency_bindings=source['dependency_bindings'],
                earlier_expansion_closure=source['earlier_expansion_closure'], ordered_input_bindings=copy.deepcopy(spec['ordered_inputs']),
                ordered_input_rows=inputs, resolved_ordered_input_provenance=provenance, ordered_member_rows=output_rows,
                conclusion_code=record['conclusion_code'], conclusion_row=mapping[record['conclusion_row']],
                ordered_receptor_ports=component['ordered_receptor_ports'], members=component['members'],
                full_member_ids=component['full_member_ids'],
                full_identity_preimage_sha256=[p.digest(x) for x in component['full_identity_preimages']],
                original_component_descriptor_sha256=p.digest(component), aggregate_t=component['aggregate_t'], aggregate_m=component['aggregate_m']))
        totals, marks, decorated = {}, {}, []
        for key in sorted(distinct):
            t, m = p.points(state.recipes[key[0]],key[1],key[2],state.height)
            if key not in state.selected and (state.totals[key[1]]+1>1 or not state.compatible(m)):
                return None, 'whole_group_point_validation:cluster constituent is not in complete legal base domain'
            if not state.compatible(m):
                return None, 'whole_group_point_validation:cluster conflicts with remote current marking'
            for x,y,value in t:
                totals[x,y] = totals.get((x,y),0)+value
                if totals[x,y]>1:
                    return None, 'whole_group_point_validation:distinct cluster placements overfill positive support'
            for x,y,value in m:
                if (x,y) in marks and marks[x,y]!=value:
                    return None, 'whole_group_point_validation:cluster internally inconsistent marking'
                marks[x,y]=value
            decorated.append(p.decorate(key,t,m,state.recipes,self.context,self.authority,self.registry))
        for component in components:
            for x,y,value in component['aggregate_m']:
                if (x,y) in marks and marks[x,y]!=value:
                    return None, 'component_marking_union_conflict'
                if (x,y) in state.marks and state.marks[x,y]!=value:
                    return None, 'aggregate_receptor_existing_mark_conflict'
                marks[x,y]=value
        occurrence_count = sum(len(c['members']) for c in components)
        return dict(components=components, members=[b.key_data(k) for k in sorted(distinct)],
            full_member_ids=[d['id'] for d in decorated], full_identity_preimage_sha256=[p.digest(d['identity_preimage']) for d in decorated],
            aggregate_t=[[*xy,v] for xy,v in sorted(totals.items())], aggregate_m=[[*xy,v] for xy,v in sorted(marks.items())],
            component_member_occurrences=occurrence_count, distinct_member_count=len(distinct), shared_member_count=occurrence_count-len(distinct)), None

    def enumerate(self):
        def visit(specification):
            value, reason = self.embedding(specification)
            if reason is None:
                self.group_specs.append(copy.deepcopy(specification)); self.preliminary.append(value)
            else:
                self.rejected.append(dict(specification=copy.deepcopy(specification),reason=reason))
        for first in self.interfaces:
            record=dict(names=[first['name']],binding_tuples=0); self.type_visits.append(record)
            for tokens in self.options(first):
                record['binding_tuples']+=1
                visit([dict(name=first['name'],ordered_inputs=list(tokens))])
        for first in self.interfaces:
            for second in self.interfaces:
                record=dict(names=[first['name'],second['name']],binding_tuples=0); self.type_visits.append(record)
                for left in self.options(first):
                    for right in self.options(second,first):
                        if not any(t['kind']=='earlier_component_output' for t in right):
                            self.disconnected+=1; continue
                        record['binding_tuples']+=1
                        visit([dict(name=first['name'],ordered_inputs=list(left)),dict(name=second['name'],ordered_inputs=list(right))])
        self.p.need(len(self.interfaces)==171 and len(self.type_visits)==171+171**2,'complete type census')
        text=[self.p.canonical(s) for s in self.group_specs]
        self.p.need(len(text)==len(set(text)),'distinct complete binding specifications')
        ranking=sorted(range(len(text)),key=lambda i:(-self.preliminary[i]['distinct_member_count'],text[i]))
        priority={index:rank for rank,index in enumerate(ranking)}
        self.priorities=[priority[i] for i in range(len(text))]
        grammar=dict(version='finite-root-single-pair-whole-union-v2',components=[1,2],
            first_inputs='actual selected initial anchors with exact formula codes',
            second_inputs='actual initial anchors or included first declared output; use output at least once',
            bindings='complete formula-filtered ordered Cartesian products; repeated ports retained',
            embedding='one canonical earliest exact-key reuse else earliest unused strict-prior row',
            sharing='same complete primitive key/full decorated identity only; preserve component occurrences',
            priority='decreasing distinct member count then canonical component-and-binding specification',native_accepted=False)
        payload=dict(version=grammar['version'],grammar=grammar,graph=self.binding,
            original_authority_epoch=self.original_epoch, interfaces=self.p.digest(self.interfaces),
            root_anchors=self.anchors,pool_specs=self.group_specs,fixed_priorities=self.priorities,source_bindings=self.new_sources)
        self.epoch=self.p.digest(payload); self.grammar=grammar; self.groups=[]
        for index, (specification, value) in enumerate(zip(self.group_specs,self.preliminary)):
            data=copy.deepcopy(value)
            data.update(version=grammar['version'],relation='finite_source_body_composition_proposal_not_new_lemma',
                graph_binding=self.binding,body_authority_epoch=self.epoch,original_body_authority_epoch=self.original_epoch,
                pool_index=index,binding_specification=specification,fixed_priority=self.priorities[index],
                native_accepted=False,native_authority_activated=False)
            data['descriptor_id']='whole-family-group-'+self.p.digest(data)
            self.groups.append(data)

    def audit(self, evidence):
        p=self.p; equal=self.b.equal
        equal(evidence['grammar'],self.grammar,'declared grammar')
        equal(evidence['root_anchors'],self.anchors,'root seed insertion order and full identities')
        equal(evidence['group_authority_epoch'],self.epoch,'complete group/priority epoch')
        equal(evidence['original_body_authority_epoch'],self.original_epoch,'unchanged source body epoch')
        equal(evidence['formula_codes'],self.formulas,'injective formula values')
        equal(evidence['formula_registry_sha256'],self.registry,'formula registry digest')
        equal(evidence['unchanged_model_epoch'],self.s.epoch,'exact point model epoch')
        summaries=[{k:r[k] for k in ('name','body_sha256','full_projection_sha256','conclusion_row','conclusion_code')}
            |dict(ordered_premise_codes=r['body']['premise_codes'],canonical_input_rows=r['body']['canonical_input_rows'],
                  primitive_member_count=len(r['body']['primitive_members'])) for r in self.interfaces]
        equal(evidence['interface_summary'],summaries,'all explicit declared interface fields')
        equal(evidence['groups'],self.groups,'all body/binding/embedding/identity/port/provenance/point/priority descriptor fields')
        counts=evidence['counters']; reasons={}
        for r in self.rejected:reasons[r['reason']]=reasons.get(r['reason'],0)+1
        expected=dict(interfaces_checked=171,single_types_visited=171,pair_types_visited=171**2,
            binding_tuples_visited=sum(r['binding_tuples'] for r in self.type_visits),
            accepted_binding_specs=len(self.groups),registered_groups=len(self.groups),type_visits=self.type_visits,
            rejected_binding_records=self.rejected,rejections=reasons,
            disconnected_second_bindings_outside_grammar=self.disconnected,
            source_member_occurrences=sum(g['component_member_occurrences'] for g in self.groups),
            group_distinct_members=sum(g['distinct_member_count'] for g in self.groups),
            group_shared_members=sum(g['shared_member_count'] for g in self.groups),
            initial_final_graph_semantic_sha256=self.p.digest(self.s.semantic()))
        for name,value in expected.items():equal(counts[name],value,'complete census '+name)
        for name in ('placements','attempts','forced','branches','backtracks'):
            equal(counts['graph_metrics_before'][name],counts['graph_metrics_after'][name],'unchanged primitive activity '+name)
        return expected

    def mutations(self):
        """Actually validate changed per-group records, not whole altered pool files."""
        p=self.p; receipts=[]
        if not self.groups:return receipts
        pair=next((i for i,g in enumerate(self.groups) if len(g['components'])==2),0)
        tests=[]
        def add(name,index,mutator):
            record=copy.deepcopy(self.groups[index]);mutator(record)
            record['descriptor_id']='whole-family-group-'+p.digest({k:v for k,v in record.items() if k!='descriptor_id'})
            tests.append((name,index,record))
        add('fresh-self-hash-wrong-declared-conclusion',0,lambda r:r['components'][0].__setitem__('conclusion_code',r['components'][0]['conclusion_code']+1))
        add('fresh-self-hash-declared-receptor-instead-of-output',0,lambda r:r['components'][0].__setitem__('conclusion_row',r['components'][0]['ordered_input_rows'][0]))
        add('priority-self-hash-not-epoch-priority',0,lambda r:r.__setitem__('fixed_priority',r['fixed_priority']+1))
        add('stale-group-authority',0,lambda r:r.__setitem__('body_authority_epoch','0'*64))
        add('stale-original-body-authority',0,lambda r:r.__setitem__('original_body_authority_epoch','0'*64))
        add('missing-component-source-binding',0,lambda r:r['components'][0].__setitem__('source_body_sha256','0'*64))
        add('full-projection-conclusion-binding-changed',0,lambda r:r['components'][0].__setitem__('full_projection_sha256','0'*64))
        add('distinct-member-t-overcount',0,lambda r:r['aggregate_t'][0].__setitem__(2,2))
        # The synthetic assigned-zero/absence fixture is separately pinned.
        # This actual payload control adds a conflicting copy of a known mark;
        # it does not assume that an arbitrary coordinate currently has code 0.
        add('hidden-conflicting-assigned-mark',0,lambda r:r['aggregate_m'].append(
            [r['aggregate_m'][0][0],r['aggregate_m'][0][1],r['aggregate_m'][0][2]+1]))
        add('boolean-assigned-mark-is-not-integer',0,lambda r:r['aggregate_m'][0].__setitem__(2,False))
        add('duplicate-physical-member',pair,lambda r:r['members'].append(copy.deepcopy(r['members'][0])))
        add('false-identity-sharing',pair,lambda r:r['full_member_ids'].__setitem__(0,r['full_member_ids'][-1]))
        add('altered-preimage-digest',0,lambda r:r['full_identity_preimage_sha256'].__setitem__(0,'0'*64))
        add('dropped-source-occurrence',pair,lambda r:r['components'][0]['members'].pop())
        add('removed-read-port-multiplicity',0,lambda r:r['components'][0]['ordered_receptor_ports'].pop())
        add('included-output-link-replaced-by-invented-root',pair,lambda r:r['binding_specification'][1]['ordered_inputs'][0].__setitem__('index',99))
        add('altered-member-row-with-stale-body-transport',0,lambda r:r['members'][0].__setitem__(1,r['members'][0][1]+1))
        for name,index,record in tests:
            try:self.b.equal(record,self.groups[index],'independently reconstructed whole group')
            except ValueError as exc:
                receipts.append(dict(name=name,rejected=True,scope='per-group altered payload plus recomputed self-hash compared against independently reconstructed full group; no altered complete-file replay',
                    original_descriptor_id=self.groups[index]['descriptor_id'],mutant_sha256=p.digest(record),reason=str(exc)))
            else:raise ValueError('mutant accepted: '+name)
        return receipts


def run(plan):
    phase_start=time.monotonic(); verify(plan); p,b,symbolic,expansion=libraries(plan)
    timings=dict(verification_and_independent_import_seconds=time.monotonic()-phase_start)
    roles={pin['role']:Path(pin['path']) for pin in plan['inputs']}
    production=p.read(roles['preparation_plan']);outcome=p.read(roles['preparation_outcome'])
    lifetime=p.read(roles['preparation_lifetime']);supervision=p.read(roles['preparation_supervision'])
    p.need(lifetime['status']=='passed_family_preparation_full_lifetime_resource_phase' and
           supervision['status']=='passed_bounded_family_preparation_resource_phase' and
           lifetime['worker_terminal_reaped_confirmed'] and supervision['owned_child_terminal_wait_reaped'],'actual terminal resource prerequisites')
    p.need(outcome['status']=='complete_declared_proposal_grammar_prepared_pending_independent_audit',
           'unknown/incomplete pool refused for complete-pool acceptance')
    relative_plan=dict(path=str(roles['preparation_plan'].relative_to(ROOT)),
        **{k:exact_pin(roles['preparation_plan'])[k] for k in ('sha256','bytes')})
    relative_evidence=dict(path=str(roles['preparation_evidence'].relative_to(ROOT)),
        **{k:exact_pin(roles['preparation_evidence'])[k] for k in ('sha256','bytes')})
    b.equal(outcome['plan'],relative_plan,'exact preparation outcome plan')
    b.equal(outcome['evidence'],relative_evidence,'exact preparation outcome evidence')
    for receipt in (lifetime,supervision):b.equal(receipt['plan'],relative_plan,'terminal resource plan')
    evidence=p.read(roles['preparation_evidence'])
    p.need(evidence['status']==outcome['status'],'bound complete evidence status')
    b.equal(evidence['plan'],relative_plan,'exact evidence plan')
    b.equal(evidence['inputs'],production['inputs'],'all original ordered role bindings')
    b.equal(evidence['sources'],production['sources'],'all original preparation source bindings')
    expected_pin={k:next(x for x in production['inputs'] if x['role']=='checked_compact_family_projection')[k] for k in ('path','sha256','bytes')}
    p.need(str(roles['family_projection'].relative_to(ROOT))==expected_pin['path'],'exact declared projection role')
    data=p.read(roles['primitive_model']);projected=p.read(roles['family_projection'])
    # Standard JSON decode includes its authored display example. It is then
    # discarded; no example rows/words are used as hints or acceptance authority.
    projected.pop('example',None)
    certificate=p.read(roles['source_certificate']);schemas=p.read(roles['source_schemas'])
    prior=p.read(roles['prior_point_plan']);original=p.read(roles['original_body_plan'])
    setup_start=time.monotonic()
    state,binding,model,primitive_counts=root_state(p,b,data,prior,symbolic)
    timings['independent_point_inventory_and_initial_state_seconds']=time.monotonic()-setup_start
    preparation_pin=next(flat_pin(x) for x in plan['inputs'] if x['role']=='preparation_plan')
    relative=dict(path=str(roles['preparation_plan'].relative_to(ROOT)),sha256=preparation_pin['sha256'],bytes=preparation_pin['bytes'],data=production)
    body_start=time.monotonic()
    pool=IndependentPool(p,b,state,binding,model,data,original,relative,certificate,schemas,projected,expansion)
    timings['independent_symbolic_source_expansion_and_interfaces_seconds']=time.monotonic()-body_start
    enumerate_start=time.monotonic();pool.enumerate()
    timings['complete_binding_transport_and_union_enumeration_seconds']=time.monotonic()-enumerate_start
    compare_start=time.monotonic();counts=pool.audit(evidence)
    timings['exact_complete_saved_evidence_comparison_seconds']=time.monotonic()-compare_start
    control_start=time.monotonic();controls=pool.mutations()
    timings['per_group_payload_corruption_controls_seconds']=time.monotonic()-control_start
    for field in ('target_searches','point_certificates','native_queries'):
        p.need(evidence[field]==0,'no upgraded producer '+field)
    p.need(evidence['new_RL_training'] is False and evidence['native_accepted'] is False and
           evidence['native_authority_activated'] is False,'proposal-only authority')
    return dict(status='passed_complete_independent_static_family_pool_audit',
        source_body_count=len(pool.bodies),source_expansion_counts=pool.source_counts,
        source_logical_receipts=pool.source_receipts,
        independently_checked_recipe_rules=primitive_counts,complete_census=counts,
        groups_checked=[dict(pool_index=g['pool_index'],component_count=len(g['components']),
            descriptor_id=g['descriptor_id'],descriptor_sha256=p.digest(g),distinct_members=g['distinct_member_count'],
            occurrence_members=g['component_member_occurrences'],shared_members=g['shared_member_count'],
            fixed_priority=g['fixed_priority'],aggregate_t_sha256=p.digest(g['aggregate_t']),aggregate_m_sha256=p.digest(g['aggregate_m']),
            all_full_identity_preimages_independently_reconstructed=True) for g in pool.groups],
        full_group_authority_epoch=pool.epoch,original_body_authority_epoch=pool.original_epoch,
        declared_interface_projection_sha256=p.digest(pool.interfaces),root_anchors=pool.anchors,
        phase_timings_before_result_serialization=timings,
        mutations=controls,mutation_scope='Actual changed group records with fresh self-hashes checked against independently rebuilt groups; not whole altered evidence-file/owner replays.',
        independent_literal_point_state_reconstructed=True,production_engine_or_controller_imports=False,
        complete_primitive_candidate_graph_enumerated=False,graph_degree_or_exhaustion_claim=False,
        source_body_symbolic_checks_performed=True,whole_target_proof_checked=False,point_certificates=0,native_queries=0,
        training_or_search_runs=0,logical_acceptance_scope='Primitive inventory licenses and all conditional source body expansions only; no completed recipient proof or native machine correspondence.',
        projection_example_io_scope='Decoded then discarded; no authored example word used as hint or acceptance authority.',
        scope='Exact complete bounded fixed-root single/pair proposal grammar, source transport, identities, port/provenance and compatible initial-state t/m unions only.')


def main():
    plan_path=Path(sys.argv[1]);plan=json.loads(plan_path.read_text())
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('independent pool child deadline')))
    signal.alarm(plan['limits']['child_seconds'])
    started=time.monotonic();result=run(plan)
    result['worker_seconds_before_result_serialization']=time.monotonic()-started
    result['plan']=exact_pin(plan_path)
    result['kernel_peak_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    with Path(plan['outputs']['result']).open('x') as stream:
        json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False);stream.write('\n')
    verify(plan);signal.alarm(0)


if __name__=='__main__':main()
