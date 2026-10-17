"""SOURCE ONLY: bounded generic primitive-DAG cut/family proposal mining.

No project, engine, expander, checker or native-kernel import/call. The input
DAG and any purported verification metadata are untrusted structural data.
Every proposed family requires fresh independent expansion and host admission.
"""
import hashlib
import json

VERSION = 'receptor-family-primitive-DAG-miner-v3-interface-coupled-catalogue'
HOST_SCHEMA = 'receptor-family-host-v1'
DAG_SCHEMA = 'receptor-family-primitive-derivation-DAG-v1'
RESULT_SCHEMA = 'receptor-family-mining-prefix-v1'
EXTRACTION_SCHEMA = 'receptor-family-mined-extraction-v1'
DEFAULT_LIMITS = {'work': 300000, 'depth': 64, 'nodes': 256, 'cuts': 48,
                  'members': 16, 'families': 64, 'generalizations_per_cut': 2,
                  'fragment_candidates': 64}
FLAGS = {'proposal_only': True, 'origin_claims_untrusted': True,
         'source_proof_verified': False, 'universal_schema_proved': False,
         'discovered_proof': False, 'ground_roundtrip_checked': False,
         'host_membership_accepted': False, 'point_union_accepted': False,
         'engine_activated': False, 'pruning_accepted': False,
         'RL_accepted': False, 'runtime_qualified': False}


class MiningDataError(ValueError):
    def __init__(self, code, detail):
        self.code = code
        super().__init__('receptor miner ' + code + ': ' + detail)


class _Unfinished(Exception):
    pass


class _CallbackFailure(BaseException):
    def __init__(self, error):
        self.error = error


def require(ok, code, detail):
    if not ok:
        raise MiningDataError(code, detail)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def keys(value, fields, code='FIELDS'):
    require(type(value) is dict and set(value) == set(fields), code, 'exact literal object fields')


def name(value):
    require(type(value) is str and bool(value), 'NAME', 'nonempty literal string')
    return value


def ident(value):
    # Source IDs are opaque nonempty strings; emitted descriptor IDs are fresh ASCII.
    return name(value)


class _Work:
    def __init__(self, tick, limits):
        require(callable(tick), 'TICK', 'caller-owned cumulative tick')
        self.tick = tick; self.steps = 0; self.limits = dict(DEFAULT_LIMITS)
        if limits is not None:
            require(type(limits) is dict and set(limits) <= set(self.limits), 'LIMITS', 'known fields only')
            for k,v in limits.items():
                require(type(v) is int and 0 < v <= self.limits[k], 'LIMITS', 'bounded positive literal int')
                self.limits[k] = v

    def step(self, depth=0):
        if self.steps >= self.limits['work'] or depth > self.limits['depth']:
            raise _Unfinished('finite mining syntax work/depth prefix; no exhaustion claim')
        try:
            self.tick()
        except BaseException as error:
            raise _CallbackFailure(error) from error
        self.steps += 1

    def copy(self, value, depth=0):
        self.step(depth)
        if value is None or type(value) in (bool,int,str): return value
        if type(value) is list: return [self.copy(v,depth+1) for v in value]
        require(type(value) is dict and all(type(k) is str for k in value), 'JSON', 'strict builtin JSON data')
        return {k:self.copy(v,depth+1) for k,v in value.items()}

    def report(self):
        return {'steps':self.steps,'limit':self.limits['work']}


class _Graph:
    def __init__(self, host, derivation, work):
        self.w = work; self.host = work.copy(host); self.dag = work.copy(derivation)
        self._host()
        d=self.dag;keys(d,('schema','host_binding','inputs','hypotheses','nodes','outputs','origin'),'DAG')
        require(d['schema']==DAG_SCHEMA and canonical(d['host_binding'])==canonical(self.host['binding']), 'BINDING','same complete original host binding')
        require(type(d['origin'])is dict,'ORIGIN','full opaque origin object, never proof authority')
        for field in ('inputs','hypotheses','nodes','outputs'):
            require(type(d[field])is list,'DAG','ordered arrays')
        require(bool(d['nodes']),'DAG','nonempty primitive derivation data')
        if len(d['nodes'])>self.w.limits['nodes']: raise _Unfinished('finite source-node allowance; no partial graph validated')
        self.inputs={};self.hyps={};self.nodes={};self.position={};self.outgoing={}
        for p in d['inputs']:
            self.w.step();keys(p,('id','formula','sharing','source','occupied','fact_accepted'),'INPUT')
            pid=ident(p['id']);require(pid not in self.inputs,'ID','unique input ID')
            require(p['sharing'] in ('ALLOW_SAME_EXACT_PRIOR_SOURCE','DISTINCT_SOURCE_REQUIRED') and
                    type(p['occupied'])is bool and p['fact_accepted']is False,'INPUT','explicit sharing/occupancy without fact acceptance')
            self.native(p['formula'],'FORMULA')
            for other in self.inputs.values():
                if canonical(other['source'])==canonical(p['source']):
                    require(other['formula']==p['formula'] and other['sharing']==p['sharing']=='ALLOW_SAME_EXACT_PRIOR_SOURCE',
                            'SHARING','one exact source metadata identity requires consistent formula and sharing')
            self.inputs[pid]=p
        for p in d['hypotheses']:
            self.w.step();keys(p,('id','gamma_index','formula'),'HYPOTHESIS')
            pid=ident(p['id']);require(pid not in self.hyps,'ID','unique hypothesis port')
            self.gamma(p['gamma_index'],p['formula']);self.hyps[pid]=p
        for i,n in enumerate(d['nodes']):
            self.w.step();keys(n,('id','rule','formula','arguments','ordered_inputs','origin'),'NODE')
            nid=ident(n['id']);require(nid not in self.nodes,'ID','unique primitive node ID')
            rule=name(n['rule']);require(rule in self.host['rules'],'RULE','declared host primitive syntax')
            spec=self.host['rules'][rule]
            require(type(n['arguments'])is dict and set(n['arguments'])==set(spec['arguments']) and
                    type(n['ordered_inputs'])is list and len(n['ordered_inputs'])==spec['input_count'], 'RULE','full ordered primitive arity/arguments')
            require(type(n['origin'])is dict,'ORIGIN','full node provenance retained as opaque data')
            self.native(n['formula'],'FORMULA')
            for k,v in n['arguments'].items():self.argument(v,spec['arguments'][k])
            for j,r in enumerate(n['ordered_inputs']):
                self.resolve(r)
                if 'node' in r:self.outgoing.setdefault(r['node'],[]).append({'consumer_node_id':nid,'ordered_index':j})
            if rule=='assumption':self.gamma(n['arguments'].get('index'),n['formula'])
            self.nodes[nid]=n;self.position[nid]=i
        seen=set()
        for p in d['outputs']:
            self.w.step();keys(p,('id','formula','source'),'OUTPUT');pid=ident(p['id'])
            require(pid not in seen,'ID','unique output ID');seen.add(pid)
            self.native(p['formula'],'FORMULA')
            require(self.resolve(p['source'])['formula']==p['formula'],'OUTPUT','literal referenced formula')
        self.sha=digest(self.dag)

    def _host(self):
        h=self.host;keys(h,('schema','host_id','dialect','binding','authority','functions','predicates','variable_names','features','rules','ordered_Gamma'),'HOST')
        require(h['schema']==HOST_SCHEMA and type(h['binding'])is dict and bool(h['binding']) and type(h['authority'])is dict,'HOST','full host data')
        name(h['host_id']);name(h['dialect'])
        for k in ('functions','predicates'):
            require(type(h[k])is dict,'HOST','signature table')
            for s,a in h[k].items():name(s);require(type(a)is int and a>=0,'ARITY','literal arity')
        for k in ('variable_names','features'):
            require(type(h[k])is list and all(type(x)is str and x for x in h[k]),'HOST','finite literal name list')
            require(len(h[k])==len(set(h[k])),'HOST','distinct names/features')
        require(type(h['rules'])is dict,'HOST','declared rule syntax table')
        for rule,spec in h['rules'].items():
            name(rule);keys(spec,('input_count','arguments'),'HOST')
            require(type(spec['input_count'])is int and spec['input_count']>=0 and type(spec['arguments'])is dict,'HOST','primitive syntax arity')
            for k,v in spec['arguments'].items():name(k);require(v in ('FORMULA','TERM','VARIABLE','PREDICATE_SYMBOL','LITERAL'),'HOST','typed rule argument')
        require(type(h['ordered_Gamma'])is list,'HOST','complete original context')
        for f in h['ordered_Gamma']:self.native(f,'FORMULA')

    def native(self,a,kind,depth=0):
        self.w.step(depth);require(type(a)is list and bool(a) and type(a[0])is str,'AST','native literal list AST');tag=a[0]
        if kind=='TERM':
            if tag=='var':require(len(a)==2 and type(a[1])is str and a[1] in self.host['variable_names'],'SCOPE','allowed native variable')
            else:
                require(len(a)==3 and tag=='fun' and type(a[1])is str and type(a[2])is list and self.host['functions'].get(a[1])==len(a[2]),'ARITY','literal function')
                for t in a[2]:self.native(t,'TERM',depth+1)
        elif tag=='bot':require(len(a)==1,'AST','bottom fields')
        elif tag=='eq':
            require(len(a)==3,'AST','equality fields')
            for t in a[1:]:self.native(t,'TERM',depth+1)
        elif tag=='pred':
            require(len(a)==3 and type(a[1])is str and type(a[2])is list and self.host['predicates'].get(a[1])==len(a[2]),'ARITY','literal predicate')
            for t in a[2]:self.native(t,'TERM',depth+1)
        elif tag=='all':
            require(len(a)==3 and type(a[1])is str and a[1] in self.host['variable_names'],'SCOPE','allowed literal binder')
            self.native(a[2],'FORMULA',depth+1)
        else:
            require((tag=='not' and len(a)==2) or (tag in ('imp','and','or') and len(a)==3),'AST','known formula constructor')
            for f in a[1:]:self.native(f,'FORMULA',depth+1)

    def argument(self,a,kind):
        if kind in ('FORMULA','TERM'):self.native(a,kind)
        elif kind=='VARIABLE':require(type(a)is str and a in self.host['variable_names'],'SCOPE','native variable argument')
        elif kind=='PREDICATE_SYMBOL':require(type(a)is str and a in self.host['predicates'],'ARITY','native predicate name')
        else:self.w.copy(a)

    def gamma(self,index,formula):
        require(type(index)is int and 0<=index<len(self.host['ordered_Gamma']) and self.host['ordered_Gamma'][index]==formula,'GAMMA','exact original occurrence and formula')
        self.native(formula,'FORMULA')

    def resolve(self,ref):
        require(type(ref)is dict and len(ref)==1,'REFERENCE','one explicit source kind')
        category=next(iter(ref));value=ident(ref[category])
        table={'node':self.nodes,'input':self.inputs,'hypothesis':self.hyps}.get(category)
        require(table is not None and value in table,'REFERENCE','strict prior node or declared port')
        return table[value]

    def free(self,a,kind):
        self.w.step();tag=a[0]
        if kind=='TERM':return {a[1]} if tag=='var' else set().union(*(self.free(t,'TERM') for t in a[2]))
        if tag=='bot':return set()
        if tag=='all':return self.free(a[2],'FORMULA')-{a[1]}
        if tag=='eq':return self.free(a[1],'TERM')|self.free(a[2],'TERM')
        if tag=='pred':return set().union(*(self.free(t,'TERM') for t in a[2]))
        return set().union(*(self.free(f,'FORMULA') for f in a[1:]))

    def fragment_key(self,a,kind,scope):
        fv=self.free(a,kind)
        return {'kind':kind,'native_fragment':a,'formal_names':sorted(fv&set(scope)),
                'external_free_names':sorted(fv-set(scope))}

    def fragments(self,a,kind,scope,location,catalog):
        self.w.step();key=self.fragment_key(a,kind,scope);text=canonical(key)
        if text not in catalog and len(catalog)>=self.w.limits['fragment_candidates']:
            return  # Advisory fragment catalogue prefix only; full literal variant remains.
        if text not in catalog:catalog[text]=dict(self.w.copy(key),occurrences=[],node_count=0)
        entry=catalog[text];entry['occurrences'].append(self.w.copy(location))
        tag=a[0];count=1
        if kind=='TERM':children=[(t,'TERM',scope,location+[2,i]) for i,t in enumerate(a[2])] if tag=='fun' else []
        elif tag=='all':children=[(a[2],'FORMULA',set(scope)|{a[1]},location+[2])]
        elif tag=='eq':children=[(a[i],'TERM',scope,location+[i]) for i in (1,2)]
        elif tag=='pred':children=[(t,'TERM',scope,location+[2,i]) for i,t in enumerate(a[2])]
        elif tag=='bot':children=[]
        else:children=[(f,'FORMULA',scope,location+[i]) for i,f in enumerate(a[1:],1)]
        for child,child_kind,child_scope,child_loc in children:
            self.fragments(child,child_kind,child_scope,child_loc,catalog)
            count+=self.size(child,child_kind)
        entry['node_count']=count

    def size(self,a,kind):
        self.w.step();tag=a[0]
        if kind=='TERM':return 1+sum(self.size(t,'TERM') for t in a[2]) if tag=='fun' else 1
        if tag=='bot':return 1
        if tag=='all':return 1+self.size(a[2],'FORMULA')
        if tag=='eq':return 1+self.size(a[1],'TERM')+self.size(a[2],'TERM')
        if tag=='pred':return 1+sum(self.size(t,'TERM') for t in a[2])
        return 1+sum(self.size(f,'FORMULA') for f in a[1:])

    def cut(self,anchor,selected):
        selected=set(selected);members=[n for n in self.dag['nodes'] if n['id'] in selected]
        steps={n['id']:'s'+str(i) for i,n in enumerate(members)}
        boundary=[];boundary_by_ref={};edges=[]
        for n in members:
            for j,ref in enumerate(n['ordered_inputs']):
                self.w.step()
                if 'node' in ref and ref['node'] in selected:target={'step':steps[ref['node']]}
                else:
                    key=canonical(ref)
                    if key not in boundary_by_ref:
                        source=self.resolve(ref);hyp=('hypothesis' in ref or ('node'in ref and source['rule']=='assumption'))
                        kind='hypothesis' if hyp else 'input';index=sum(v['kind']==kind for v in boundary)
                        pid=('h' if hyp else 'i')+str(index)
                        value={'kind':kind,'port_id':pid,'reference':self.w.copy(ref),'source':source}
                        boundary.append(value);boundary_by_ref[key]=value
                    b=boundary_by_ref[key];target={b['kind']:b['port_id']}
                edges.append({'source_node_id':n['id'],'ordered_index':j,'original_reference':self.w.copy(ref),'descriptor_reference':target})
        exposed=[]
        for n in members:
            self.w.step();nid=n['id'];uses=[u for u in self.outgoing.get(nid,[]) if u['consumer_node_id'] not in selected]
            labels=[o['id'] for o in self.dag['outputs'] if o['source']=={'node':nid}]
            if nid==anchor or uses or labels:
                exposed.append({'port_id':'o'+str(len(exposed)),'source_node_id':nid,'source_output_ids':labels,'outgoing_uses':self.w.copy(uses)})
        return members,steps,boundary,edges,exposed

    def _probe_interface_fragments(self,a,kind,scope,location,catalog,field,depth=0):
        # Probe only admitted keys, but never let an untracked ancestor hide an
        # already catalogued descendant. The old catalogue capacity is unchanged.
        self.w.step(depth);text=canonical(self.fragment_key(a,kind,scope))
        if text in catalog:
            catalog[text]['interface_probe'][field].append(self.w.copy(location))
        tag=a[0]
        if kind=='TERM':children=[(t,'TERM',scope,location+[2,i]) for i,t in enumerate(a[2])] if tag=='fun' else []
        elif tag=='all':children=[(a[2],'FORMULA',set(scope)|{a[1]},location+[2])]
        elif tag=='eq':children=[(a[i],'TERM',scope,location+[i]) for i in (1,2)]
        elif tag=='pred':children=[(t,'TERM',scope,location+[2,i]) for i,t in enumerate(a[2])]
        elif tag=='bot':children=[]
        else:children=[(f,'FORMULA',scope,location+[i]) for i,f in enumerate(a[1:],1)]
        for child,child_kind,child_scope,child_loc in children:
            self._probe_interface_fragments(child,child_kind,child_scope,child_loc,catalog,field,depth+1)

    def catalogue(self,members,boundary,exposed,fragment_priority):
        catalog={}
        for b in boundary:self.fragments(b['source']['formula'],'FORMULA',set(),['boundary',b['kind'],b['port_id'],'formula'],catalog)
        for n in members:
            self.fragments(n['formula'],'FORMULA',set(),['nodes',n['id'],'formula'],catalog)
            for k,kind in self.host['rules'][n['rule']]['arguments'].items():
                if kind in ('FORMULA','TERM'):self.fragments(n['arguments'][k],kind,set(),['nodes',n['id'],'arguments',k],catalog)
        if fragment_priority=='LARGEST_REPEATED_FIRST':
            repeated=[v for v in catalog.values() if len(v['occurrences'])>=2]
            return sorted(repeated,key=lambda v:(-v['node_count'],canonical({k:v[k] for k in ('kind','native_fragment','formal_names','external_free_names')})))
        for entry in catalog.values():
            self.w.step();entry['interface_probe']={'open_input_occurrences':[],'output_occurrences':[]}
        for b in boundary:
            self.w.step()
            # A cut-out node becomes a conditional descriptor input; that alone
            # says nothing about physical vacancy. Only explicit source-DAG input
            # occupancy data is used here, and remains untrusted until rechecked.
            if b['kind']=='input' and 'input' in b['reference'] and b['source']['occupied'] is False:
                self._probe_interface_fragments(b['source']['formula'],'FORMULA',set(),
                    ['boundary','input',b['port_id'],'formula'],catalog,'open_input_occurrences')
        for p in exposed:
            self.w.step()
            self._probe_interface_fragments(self.nodes[p['source_node_id']]['formula'],'FORMULA',set(),
                ['outputs',p['port_id'],'formula'],catalog,'output_occurrences')
        repeated=[]
        for entry in catalog.values():
            self.w.step();probe=entry['interface_probe']
            coupled=bool(probe['open_input_occurrences'] and probe['output_occurrences'])
            probe['open_input_output_coupled']=coupled
            probe['whole_output_formula']=entry['kind']=='FORMULA' and any(len(p)==3 for p in probe['output_occurrences'])
            if len(entry['occurrences'])>=2 or coupled:repeated.append(entry)
        return sorted(repeated,key=lambda v:(
            0 if v['interface_probe']['open_input_output_coupled'] else 1,
            0 if v['interface_probe']['open_input_output_coupled'] and v['interface_probe']['whole_output_formula'] else 1,
            -v['node_count'],canonical({k:v[k] for k in ('kind','native_fragment','formal_names','external_free_names')})))


class _Builder:
    def __init__(self,graph,fragment):
        self.g=graph;self.w=graph.w;self.fragment=fragment;self.parameters=[];self.substitution={}
        self.free_variables={};self.abstractions={};self.bound_count=0;self.meta_count={'FORMULA':0,'TERM':0};self.abstraction_map=[]

    def variable(self,native):
        if native not in self.free_variables:
            pid='v'+str(len(self.free_variables));self.free_variables[native]=pid
            self.parameters.append({'id':pid,'kind':'VARIABLE','role':'FREE_PARAMETER','distinct_from':[],'allowed_names_policy':'HOST_DECLARED_SCOPE'})
            self.substitution[pid]=native
        return self.free_variables[native]

    def abstract(self,a,kind,scope,location,reason):
        key=self.g.fragment_key(a,kind,scope);literal=canonical(key)
        if literal not in self.abstractions:
            pid=('F' if kind=='FORMULA' else 'T')+str(self.meta_count[kind]);self.meta_count[kind]+=1
            formals=[scope[n] for n in key['formal_names']]
            externals=[self.variable(n) for n in key['external_free_names']]
            self.parameters.append({'id':pid,'kind':kind,'formal_variables':formals,'allowed_external_free_variables':externals})
            self.substitution[pid]={'formal_names':list(key['formal_names']),'body':self.w.copy(a)}
            self.abstractions[literal]=pid
        pid=self.abstractions[literal]
        self.abstraction_map.append({'location':self.w.copy(location),'kind':kind,'parameter_id':pid,
            'native_fragment':self.w.copy(a),'formal_names':list(key['formal_names']),
            'external_free_names':list(key['external_free_names']),'reason':reason})
        return {'node':'formula_meta' if kind=='FORMULA' else 'term_meta','parameter':pid,
                'arguments':[{'node':'var','variable_id':scope[n]} for n in key['formal_names']]}

    def chosen(self,a,kind,scope):
        if self.fragment is None:return False
        return self.g.fragment_key(a,kind,scope)=={k:self.fragment[k] for k in ('kind','native_fragment','formal_names','external_free_names')}

    def template(self,a,kind,scope=None,location=None):
        self.w.step();scope={} if scope is None else scope;location=[] if location is None else location;tag=a[0]
        if self.chosen(a,kind,scope):return self.abstract(a,kind,scope,location,'REPEATED_FRAGMENT')
        if kind=='TERM':
            if tag=='var':return {'node':'var','variable_id':scope[a[1]] if a[1]in scope else self.variable(a[1])}
            return {'node':'fun','symbol':a[1],'arguments':[self.template(t,'TERM',scope,location+[2,i]) for i,t in enumerate(a[2])]}
        if tag=='bot':return {'node':'bot'}
        if tag=='all':
            if a[1]in scope:return self.abstract(a,'FORMULA',scope,location,'LITERAL_BINDER_SHADOWING')  # Literal shadowing retained, never silently alpha-normalized.
            pid='b'+str(self.bound_count);self.bound_count+=1
            self.parameters.append({'id':pid,'kind':'VARIABLE','role':'BOUND','distinct_from':[],'allowed_names_policy':'HOST_DECLARED_SCOPE'})
            self.substitution[pid]=a[1];inner=dict(scope);inner[a[1]]=pid
            return {'node':'all','binder_id':pid,'body':self.template(a[2],'FORMULA',inner,location+[2])}
        if tag=='eq':return {'node':'eq','left':self.template(a[1],'TERM',scope,location+[1]),'right':self.template(a[2],'TERM',scope,location+[2])}
        if tag=='pred':return {'node':'pred','symbol':{'literal':a[1]},'arguments':[self.template(t,'TERM',scope,location+[2,i]) for i,t in enumerate(a[2])]}
        if tag=='not':return {'node':'not','body':self.template(a[1],'FORMULA',scope,location+[1])}
        return {'node':tag,'left':self.template(a[1],'FORMULA',scope,location+[1]),'right':self.template(a[2],'FORMULA',scope,location+[2])}

    def argument(self,value,kind,location):
        if kind in ('FORMULA','TERM'):out=self.template(value,kind,location=location)
        elif kind=='VARIABLE':out={'variable_id':self.variable(value)}
        elif kind=='PREDICATE_SYMBOL':out={'literal':value}
        else:out=self.w.copy(value)
        return {'type':kind,'value':out}

    def build(self,anchor,members,steps,boundary,edges,exposed):
        hyps=[];inputs=[];hp=[];ip=[];boundary_map=[]
        for b in boundary:
            self.w.step();source=b['source'];ref=b['reference'];pid=b['port_id'];formula=self.template(source['formula'],'FORMULA',location=['boundary',b['kind'],pid,'formula'])
            if b['kind']=='hypothesis':
                idx=source['gamma_index'] if 'hypothesis'in ref else source['arguments']['index']
                hyps.append({'id':pid,'formula':formula,'ordered_context_role':'original_context_occurrence','discharge':'NONE_UNLESS_EXPLICIT_HOST_RULE'})
                hp.append({'port_id':pid,'gamma_index':idx,'formula':self.w.copy(source['formula'])})
                original_sharing=None
            else:
                original_sharing=source['sharing'] if 'input'in ref else 'DISTINCT_SOURCE_REQUIRED'
                inputs.append({'id':pid,'formula':formula,'ordered_role':'cut_derivation_input','sharing':original_sharing})
                provenance=self.w.copy(source['source']) if 'input'in ref else {'schema':'receptor-family-mined-cut-source-v1','source_node_id':source['id'],'source_origin':self.w.copy(source['origin']),'source_DAG_sha256':self.g.sha}
                ip.append({'port_id':pid,'formula':self.w.copy(source['formula']),'source':provenance,
                           'occupied':source['occupied'] if 'input'in ref else False,'fact_accepted':False})
            boundary_map.append({'port_kind':b['kind'],'port_id':pid,'original_reference':self.w.copy(ref),
                'source_node_id':ref.get('node'),'source_input_id':ref.get('input'),'source_hypothesis_id':ref.get('hypothesis'),
                'source_formula':self.w.copy(source['formula']),'original_origin':self.w.copy(source.get('origin')),'original_sharing':original_sharing})
        body=[]
        edge_refs={(e['source_node_id'],e['ordered_index']):e['descriptor_reference'] for e in edges}
        for n in members:
            self.w.step();spec=self.g.host['rules'][n['rule']]
            body.append({'id':steps[n['id']],'kind':'PRIMITIVE','rule':n['rule'],
                'formula':self.template(n['formula'],'FORMULA',location=['nodes',n['id'],'formula']),
                'arguments':{k:self.argument(n['arguments'][k],spec['arguments'][k],['nodes',n['id'],'arguments',k]) for k in sorted(spec['arguments'])},
                'ordered_inputs':[self.w.copy(edge_refs[(n['id'],j)]) for j in range(len(n['ordered_inputs']))]})
        outputs=[];op=[]
        for p in exposed:
            n=self.g.nodes[p['source_node_id']]
            outputs.append({'id':p['port_id'],'formula':self.template(n['formula'],'FORMULA',location=['outputs',p['port_id'],'formula']),'source':{'step':steps[n['id']]}})
            op.append({'port_id':p['port_id'],'formula':self.w.copy(n['formula'])})
        selected=[n['id'] for n in members]
        desc={'schema':'receptor-lemma-family-v2','family_id':'','origin':'SEARCH_EXTRACTED',
            'provenance':{'schema':'receptor-family-automatic-DAG-extraction-origin-v1','mechanism':'AUTOMATIC_PRIMITIVE_DAG_CUT',
                'source_DAG_sha256':self.g.sha,'source_node_ids':selected,'input_origin_claims_untrusted':self.w.copy(self.g.dag['origin']),
                'source_proof_verified':False,'discovered_proof':False,'universal_schema_proved':False},
            'required_host_features':[],'parameters':self.parameters,'hypotheses':hyps,'inputs':inputs,
            'outputs':outputs,'body':body,'side_conditions':[],'dependencies':[]}
        pre={k:v for k,v in desc.items() if k not in ('family_id','provenance')};desc['family_id']=digest(pre)
        return {'schema':EXTRACTION_SCHEMA,'cut':{'anchor':anchor,'selected_node_ids':selected,'source_DAG_sha256':self.g.sha},
            'descriptor':desc,'family_preimage':self.w.copy(pre),'family_id':desc['family_id'],
            'substitution':self.substitution,'source_port_bindings':{'hypotheses':hp,'inputs':ip,'outputs':op},
            'source_node_map':[{'source_node_id':n['id'],'descriptor_step_id':steps[n['id']]} for n in members],
            'boundary_source_map':boundary_map,'abstraction_map':self.abstraction_map,'boundary_edge_map':self.w.copy(edges),'output_map':self.w.copy(exposed),
            'fragment_generalization':self.w.copy(self.fragment),'costs':{'selected_members':len(members),'ordered_edges':len(edges),
                'external_inputs':len(inputs),'hypothesis_ports':len(hyps),'exposed_outputs':len(outputs),'parameters':len(self.parameters),'actual_repeated_abstractions':sum(a['reason']=='REPEATED_FRAGMENT' for a in self.abstraction_map),'literal_shadow_abstractions':sum(a['reason']=='LITERAL_BINDER_SHADOWING' for a in self.abstraction_map)},'flags':dict(FLAGS)}


def validate_derivation(*,host,derivation,tick,limits=None):
    work=_Work(tick,limits)
    try:
        graph=_Graph(host,derivation,work)
        return {'schema':'receptor-family-derivation-structure-check-v1','version':VERSION,'status':'STRUCTURE_CHECKED',
                'request':{'host':work.copy(graph.host),'derivation':work.copy(graph.dag)},'source_DAG_sha256':graph.sha,
                'node_count':len(graph.nodes),'work':work.report(),'reason':None,'flags':dict(FLAGS)}
    except _CallbackFailure as error:raise error.error
    except _Unfinished as error:
        return {'schema':'receptor-family-derivation-structure-check-v1','version':VERSION,'status':'UNKNOWN','request':None,
                'source_DAG_sha256':None,'node_count':None,'work':work.report(),'reason':str(error),'flags':dict(FLAGS)}


def _interface_coupling(graph,boundary,record,fragment_priority):
    """Describe actual built parameter uses, never template usefulness or facts."""
    w=graph.w;open_inputs={};input_evidence=[]
    for b in boundary:
        w.step()
        if b['kind']=='input':
            explicit='input' in b['reference']
            occupied=b['source']['occupied'] if explicit else None
            is_open=explicit and occupied is False
            open_inputs[b['port_id']]=is_open
            input_evidence.append({'port_id':b['port_id'],'original_reference':w.copy(b['reference']),
                'source_DAG_input_occupied':occupied,'explicit_open_input':is_open,
                'physical_occupancy_verified':False})
    uses={p['id']:{'parameter_id':p['id'],'kind':p['kind'],
        'input_occurrences':[],'output_occurrences':[],'explicit_open_input_occurrences':[]}
        for p in record['descriptor']['parameters'] if p['kind'] in ('FORMULA','TERM')}
    chosen_parameters=set();fragment=record['fragment_generalization']
    selected_key=None if fragment is None else {k:fragment[k] for k in ('kind','native_fragment','formal_names','external_free_names')}
    for item in record['abstraction_map']:
        w.step();pid=item['parameter_id'];loc=item['location'];use=uses[pid]
        if selected_key is not None and {k:item[k] for k in selected_key}==selected_key:
            chosen_parameters.add(pid)
        if len(loc)>=4 and loc[:2]==['boundary','input'] and loc[3]=='formula':
            use['input_occurrences'].append(w.copy(loc))
            if open_inputs[loc[2]]:use['explicit_open_input_occurrences'].append(w.copy(loc))
        elif len(loc)>=3 and loc[0]=='outputs' and loc[2]=='formula':
            use['output_occurrences'].append(w.copy(loc))
    coupled=[]
    for use in uses.values():
        w.step()
        if use['input_occurrences'] and use['output_occurrences']:coupled.append(use)
    open_coupled=[u for u in coupled if u['explicit_open_input_occurrences']]
    return {'schema':'receptor-family-built-interface-coupling-v1','fragment_priority':fragment_priority,
        'input_evidence':input_evidence,'coupled_parameters':coupled,
        'input_output_parameter_count':len(coupled),'explicit_open_input_output_parameter_count':len(open_coupled),
        'selected_fragment_coupled_after_build':None if fragment is None else any(u['parameter_id'] in chosen_parameters for u in open_coupled),
        'literal_shadow_abstraction_count':record['costs']['literal_shadow_abstractions'],
        'scope':'Actual FORMULA/TERM parameter identity and template locations only; source-DAG occupancy is untrusted supplied evidence, not fresh native physical acceptance.',
        'shadowing_caveat':'Literal binder shadowing may abstract an enclosing formula and hide the chosen descendant; pre-build rank never guarantees post-build coupling, inferability or useful transfer.'}


def _connected_cut(graph, cut):
    """Only an advisory emission predicate on the full induced primitive DAG.

    Every internal ordered edge remains in graph.cut's unchanged wire. The
    undirected neighbor sets below test weak connectivity only, not legality,
    proof closure, generation, candidate-domain completeness or source authority.
    """
    graph.w.step()
    if len(cut) < 2:
        return False
    selected = set(cut)
    adjacent = {nid: set() for nid in cut}
    for nid in cut:
        graph.w.step()
        for ref in graph.nodes[nid]['ordered_inputs']:
            graph.w.step()
            if 'node' in ref and ref['node'] in selected:
                source = ref['node']
                adjacent[nid].add(source)
                adjacent[source].add(nid)
    queue, reached = [cut[0]], set()
    while queue:
        graph.w.step()
        nid = queue.pop(0)
        if nid not in reached:
            reached.add(nid)
            # Source-topological order makes this diagnostic traversal stable;
            # it never reorders primitive ports or the ancestor mining queue.
            queue.extend(sorted(adjacent[nid]-reached, key=graph.position.get))
    return reached == selected


def mine_families(*,host,derivation,tick,limits=None,cut_selection='ANY',fragment_priority='LARGEST_REPEATED_FIRST'):
    require(type(cut_selection) is str and cut_selection in ('ANY', 'CONNECTED_AT_LEAST_TWO'),
            'CUT_SELECTION', 'explicit generic advisory emission policy')
    require(type(fragment_priority) is str and fragment_priority in ('LARGEST_REPEATED_FIRST','OPEN_INPUT_OUTPUT_FIRST'),
            'FRAGMENT_PRIORITY', 'explicit generic advisory catalogue order')
    work=_Work(tick,limits);families=[];attempts=0;duplicates=0;request=None
    reason='finite declared DAG/cut/fragment prefix ended; no substitution or family exhaustion claim'
    try:
        graph=_Graph(host,derivation,work)
        request={'host':work.copy(graph.host),'derivation':work.copy(graph.dag)}
        states=[{'anchor':n['id'],'queue':[n['id']],'selected':[]} for n in graph.dag['nodes']]
        seen_cuts=set();family_names={};active=True;stopped=False
        while active and not stopped:
            active=False
            for state in states:
                work.step()
                if len(state['selected'])>=work.limits['members']:continue
                next_node=None
                while state['queue']:
                    work.step();candidate=state['queue'].pop(0)
                    if candidate not in state['selected']:next_node=candidate;break
                if next_node is None:continue
                active=True;state['selected'].append(next_node)
                state['queue'].extend(r['node'] for r in graph.nodes[next_node]['ordered_inputs'] if 'node'in r)
                if attempts>=work.limits['cuts']:
                    reason='finite cut prefix bound; no exhaustion claim';stopped=True;break
                attempts+=1;cut=tuple(sorted(state['selected'],key=graph.position.get))
                if cut in seen_cuts:duplicates+=1;continue
                seen_cuts.add(cut)
                if cut_selection == 'CONNECTED_AT_LEAST_TWO' and not _connected_cut(graph, cut):
                    continue  # Unemitted syntax prefix, never a base-candidate exclusion.
                members,steps,boundary,edges,exposed=graph.cut(state['anchor'],cut)
                def variants():
                    yield None  # Complete literal record retained before optional catalogue work.
                    yield from graph.catalogue(members,boundary,exposed,fragment_priority)[:work.limits['generalizations_per_cut']]
                for fragment in variants():
                    work.step()
                    if len(families)>=work.limits['families']:
                        reason='finite family proposal prefix bound; no exhaustion claim';stopped=True;break
                    record=_Builder(graph,fragment).build(state['anchor'],members,steps,boundary,edges,exposed)
                    record['costs']['interface_coupling']=_interface_coupling(graph,boundary,record,fragment_priority)
                    if fragment is not None and record['costs']['actual_repeated_abstractions']==0:
                        continue  # Conservative shadow fallback can hide a selected catalogue fragment.
                    fid=record['family_id'];pre=canonical(record['family_preimage'])
                    require(fid not in family_names or family_names[fid]==pre,'COLLISION','same family digest requires identical complete preimage')
                    family_names[fid]=pre;families.append(record)
                    if len(families) >= work.limits['families']:
                        reason='finite family proposal prefix bound; no exhaustion claim';stopped=True;break
                if stopped:break
    except _CallbackFailure as error:raise error.error
    except _Unfinished as error:reason=str(error)
    return {'schema':RESULT_SCHEMA,'version':VERSION,'status':'PROPOSALS' if families else 'UNKNOWN',
            'request':request,'families':families,'cut_attempts':attempts,'duplicate_cuts':duplicates,
            'mining_complete':False,'work':work.report(),
            'reason':'cut_selection='+cut_selection+'; fragment_priority='+fragment_priority+'; '+reason,'flags':dict(FLAGS)}
