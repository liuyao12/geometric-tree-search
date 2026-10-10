"""Sound motif expansion, whole-instance joins, exact graphs and adversarial traces."""
import copy,itertools,unittest
import logic as L
import induction_proof_catalogs as C,induction_proof_problems as P,induction_proof_tiles as T
import induction_clusters as H,audit_induction_clusters as A
from audit_serialized_kernel import freeze,replay
from run_semantic_proofs import declaration
from turtle import Graph

class MotifTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=P.problems()[0];cls.source=C.catalog(cls.p['theory'],cls.p['target'],4)
        cls.result=T.search(cls.source,7,support=True,seconds=30)
        if cls.result['status']!='finite_exact_proof_tiling':raise ValueError('fresh test donor failed')
        cls.library=H.merge([],H.mine(cls.source,cls.result,cls.p))
        z=L.F('zero');start=L.F('add',z,z);f0=L.Eq(start,start);f1=L.Eq(start,z)
        seed=next(r for r in cls.source['rules'] if not r['inputs'] and cls.source['formulas'][r['output']]==f0)
        rewrite=next(r for r in cls.source['rules'] if r['inputs']==[cls.source['formulas'].index(f0)] and cls.source['formulas'][r['output']]==f1)
        rules=[dict(seed,inputs=[],output=0),dict(rewrite,inputs=[0],output=1)]
        rules.extend(dict(inputs=[i],output=i,recipe=dict(kind='copy')) for i in range(2))
        cls.tiny=dict(theory=cls.p['theory'],target=f1,target_id=1,formulas=[f0,f1],rules=rules,close_variables=[],configuration={})
        cls.tiny_p=dict(cls.p,id='test-tiny',target=f1,length=2)
        cls.tiny_result=H.search(cls.tiny,2,seconds=5)
        cls.tiny_library=H.merge([],H.mine(cls.tiny,cls.tiny_result,cls.tiny_p))

    def test_every_connected_source_fragment_and_provenance(self):
        actual=H.mine(self.source,self.result,self.p)
        independent=A.learned(freeze(declaration(self.source)),freeze(self.result),freeze(self.p))
        self.assertEqual(freeze(actual),freeze(independent));self.assertTrue(actual)
        self.assertTrue(all(2<=x['size']<=3 for x in actual))

    def test_duplicate_patterns_preserve_distinct_source_bindings(self):
        new=copy.deepcopy(self.library)
        for t in new:
            for source in t['sources']:source['problem']='different-donor'
        merged=H.merge(self.library,new)
        self.assertEqual(len(merged),len(self.library));self.assertEqual(freeze(merged),freeze(A.merged([copy.deepcopy(self.library),new])))
        self.assertTrue(all(any(s['problem']=='different-donor' for s in t['sources']) for t in merged))

    def test_provenance_rejects_changed_or_omitted_source_fragments(self):
        mined=H.mine(self.source,self.result,self.p)
        row=freeze(dict(catalog=declaration(self.source),problem=self.p,run=dict(result=self.result),mined=mined))
        report=A.provenance([row],freeze(H.merge([],mined)));self.assertEqual(report['patterns'],len(self.library))
        for field in ('certificate','family','omission'):
            library=copy.deepcopy(self.library)
            if field=='certificate':library[0]['sources'][0]['certificate_sha256']='0'*64
            elif field=='family':library[0]['nodes'][0]['family']['kind']='invented'
            else:library.pop()
            with self.assertRaisesRegex(ValueError,'entire learned library'):A.provenance([row],freeze(library))

    def test_rewrite_family_does_not_restrict_literal_terms_or_ast_path(self):
        rules=[r for r in self.source['rules'] if r['recipe'].get('operation')=='conditional-rewrite']
        groups={}
        for r in rules:groups.setdefault(H.digest(H.family(r)),[]).append(r)
        candidates=[g for g in groups.values() if len({tuple(r['recipe']['move']['path']) for r in g})>1]
        self.assertTrue(candidates)
        for group in candidates:
            self.assertTrue(all('path' not in H.family(r) for r in group))
            self.assertTrue(all(H.family(r)==A.family(freeze(r)) for r in group))

    def test_independent_relational_join_equals_cartesian_enumeration(self):
        n=3;c=freeze(self.tiny);library=freeze(self.tiny_library)
        actual=A.instances(c,n,library);universe=A.A.candidates(c,n);brute={}
        for pattern in library:
            buckets=[[i for i,r in enumerate(c['rules']) if A.family(r)==node['family']] for node in pattern['nodes']]
            for start in range(n-pattern['span']+1):
                for rids in itertools.product(*buckets):
                    members=tuple((start+node['offset'],rid,tuple(start+j for j in node['refs'])) for rid,node in zip(rids,pattern['nodes']))
                    if any(k not in universe for k in members):continue
                    ports={};good=True
                    for k in members:
                        for p,v in universe[k].items():
                            if p in ports and ports[p]!=v:good=False
                            ports[p]=v
                    if good:
                        if members not in brute:brute[members]=dict(members=members,patterns=[],start=start)
                        brute[members]['patterns'].append(pattern['name'])
        self.assertEqual(freeze(actual),freeze([brute[k] for k in sorted(brute)]))
        self.assertEqual(freeze(H.instances(self.tiny,n,self.tiny_library)),freeze(actual))

    def test_complete_instances_and_fixed_hypothesis_transfer(self):
        p=P.problems()[3];c=C.catalog(p['theory'],p['target'],p['term_bound'])
        actual=H.instances(c,p['length'],self.library);independent=A.instances(freeze(declaration(c)),p['length'],freeze(self.library))
        self.assertEqual(freeze(actual),freeze(independent));self.assertGreater(len(actual),0)
        hyp=[c['rules'][k[1]]['recipe']['context']['hypothesis'] for x in actual for k in x['members'] if c['rules'][k[1]]['recipe'].get('axiom')=='fixed-induction-hypothesis']
        self.assertTrue(hyp);self.assertTrue(all(h!=self.p['target'][2] for h in hyp))

    def solutions(self,points):
        out=set()
        def visit(ids):
            ds=points.domains(ids)
            if not ds:out.add(tuple(sorted(points.expand(ids))));return
            p=min(ds)
            for cid in sorted(ds[p]):visit(ids+[cid])
        visit([]);return out

    def test_metatiles_and_resource_marks_preserve_every_tiny_solution(self):
        for n in (2,3):
            c=freeze(self.tiny)
            original=self.solutions(A.I.Points(c,n,'none'))
            self.assertTrue(original)
            for marked in (False,True):
                self.assertEqual(original,self.solutions(A.Points(c,n,freeze(self.tiny_library),marked)))

    def test_incremental_graph_matches_all_remote_marks_and_rollback(self):
        model=H.Model(self.tiny,3,self.tiny_library);s=model.initial();g=Graph(model,s);oracle=A.Points(freeze(self.tiny),3,freeze(self.tiny_library))
        saved=s.copy();fingerprint=g.fingerprint()
        def visit(state,graph,ids,depth):
            self.assertEqual(graph.domains,oracle.domains(ids))
            if depth==3:return
            for cid in sorted(graph.edges):
                child=state.copy();cg=graph.copy();cg.update(model,child,child.place(model.placement(cid)));visit(child,cg,ids+[cid],depth+1)
                self.assertEqual(graph.domains,oracle.domains(ids))
        visit(s,g,[],0);self.assertEqual(saved.__dict__,s.__dict__);self.assertEqual(fingerprint,g.fingerprint())

    def test_every_primitive_fallback_remains(self):
        model=H.Model(self.tiny,3,self.tiny_library);base=H.Model(self.tiny,3,())
        self.assertGreater(len(model.cache),len(base.cache))
        for cid,t in base.cache.items():self.assertEqual(t,model.cache[cid])

    def run_pair(self,**kw):
        for fn,auditor in ((H.search,A.point_run),(H.csp_search,A.csp_run)):
            result=fn(self.tiny,3,self.tiny_library,seconds=5,**kw)
            auditor(freeze(self.tiny),3,freeze(result),freeze(self.tiny_library));yield result

    def test_checked_successful_prefixes_both_representations(self):
        for r in self.run_pair():self.assertEqual(r['status'],'finite_exact_proof_tiling')

    def test_attempt_cutoffs_are_open_unknown(self):
        for r in self.run_pair(attempt_limit=0):self.assertEqual(r['status'],'unknown_search_budget');self.assertIsNone(r['search_tree'])

    def test_wall_cutoffs_are_open_unknown(self):
        for fn,auditor in ((H.search,A.point_run),(H.csp_search,A.csp_run)):
            r=fn(self.tiny,3,self.tiny_library,seconds=0)
            self.assertEqual(r['status'],'unknown_search_budget');auditor(freeze(self.tiny),3,freeze(r),freeze(self.tiny_library))

    def test_unmarked_prefixes(self):
        for r in self.run_pair(marked=False):self.assertIsNone(r['support_certificate'])

    def test_short_original_induction_envelope_exhausts_with_motifs(self):
        for fn,auditor in ((H.search,A.point_run),(H.csp_search,A.csp_run)):
            r=fn(self.source,6,self.library,seconds=15)
            self.assertEqual(r['status'],'exhausted_finite_proof_envelope');auditor(freeze(declaration(self.source)),6,freeze(r),freeze(self.library))

    def test_mutated_graph_or_expansion_is_rejected(self):
        for field in ('graph','expansion','children','leaf'):
            r=H.search(self.tiny,3,self.tiny_library,seconds=5);t=r['search_tree']
            if field=='graph':t['graph_sha256']='0'*64
            elif field=='expansion':r['placements'][0]=(0,3,())
            elif field=='children':t['children'].pop()
            else:
                while 'children' in t:t=t['children'][-1]['tree']
                t['children']=[]
            with self.assertRaises((ValueError,KeyError)):A.point_run(freeze(self.tiny),3,freeze(r),freeze(self.tiny_library))

    def test_mutated_ac_or_macro_witness_is_rejected(self):
        for field in ('revision','choice','leaf','witness'):
            r=H.csp_search(self.tiny,3,self.tiny_library,seconds=5);t=r['search_tree']
            if field=='revision':i,j,_=t['revisions'][0];t['revisions'][0]=(i,j,'0xffff')
            elif field=='choice':t['children'][0]['choice']=-1
            elif field=='witness':r['placements'][0]=(0,3,())
            else:
                while t['children']:t=t['children'][-1]['tree']
                t['children']=[dict(mode='base',choice=0,tree={})]
            with self.assertRaises((ValueError,KeyError)):A.csp_run(freeze(self.tiny),3,freeze(r),freeze(self.tiny_library))

    def test_dead_ac_cannot_hide_extra_events_or_children(self):
        r=H.csp_search(self.source,6,self.library,seconds=15)
        for field in ('revisions','children'):
            bad=copy.deepcopy(r)
            bad['search_tree'][field].append((0,1,'0x0') if field=='revisions' else dict(mode='base',choice=0,tree={}))
            with self.assertRaises((ValueError,KeyError)):A.csp_run(freeze(declaration(self.source)),6,freeze(bad),freeze(self.library))

    def test_generalization_with_open_assumption_is_not_a_lemma(self):
        p=L.Eq(L.F('add',L.F('zero'),L.V('n')),L.V('n'));target=L.All('n',p)
        block=dict(name='invalid-open-generalization',premises=[p],conclusion=target,proof=[dict(rule='assumption',index=0,formula=p),dict(rule='generalize',variable='n',source=0,formula=target)])
        root=L.Eq(L.F('zero'),L.F('zero'))
        request=dict(protocol='gcts-fol-1',theory=self.p['theory'],target=root,blocks=[block],proof=[dict(rule='refl',formula=root)])
        result=replay(A.A.packed(request),A.A.pin(request))
        self.assertNotEqual(result['status'],'accepted');self.assertIn('eigenvariable restriction',result['reason'])

if __name__=='__main__':unittest.main(verbosity=2)
