import collections,copy,itertools,unittest
import propositional_receptors as R
import check_propositional_receptors as A
from turtle import State,Graph,Placement

class ReceptorTests(unittest.TestCase):
    def tiny(self,length=2):
        # The test grammar is independent of the fixed benchmark inventory.
        b=dict(rules=[dict(kind='H1',inputs=(),output=R.imp(R.P,R.imp(R.Q,R.P))),
                      dict(kind='H1',inputs=(),output=R.imp(R.Q,R.imp(R.P,R.Q))),
                      dict(kind='mp',inputs=(R.P,R.imp(R.P,R.Q)),output=R.Q)])
        return R.Model(b,R.Q,length,(R.P,R.imp(R.P,R.Q)))
    def exhaustive(self,m,s):
        ds={p:set() for p in s.frontier()};allkeys={}
        for slot in range(m.length):
            for rid,r in enumerate(m.catalog['rules']):
                for refs in itertools.product(range(-len(m.hypotheses),slot),repeat=len(r['inputs'])):
                    pairs=[(slot,r['output'])]+list(zip(refs,r['inputs']));marks={};ok=True
                    for j,a in pairs:
                        entries=[((2*j,2+k),v) for k,v in enumerate(A.word(a)+'e')]+[((2*j,1),0)]
                        for p,v in entries:
                            if p in marks and marks[p]!=v:ok=False
                            marks[p]=v
                    if not ok:continue
                    key=(slot,rid,refs);allkeys[key]=tuple(sorted(marks.items()))
                    p=(2*slot,0)
                    if p in ds and key not in s.selected and s.totals.get(p,0)+12<=12 and all(q not in s.marks or s.marks[q]==v for q,v in marks.items()):ds[p].add(key)
        self.assertEqual(set(allkeys),set(m.cache))
        for k,v in allkeys.items():self.assertEqual(v,m.cache[k].marks)
        return ds
    def graph_equal(self,m,s,g):
        ds=self.exhaustive(m,s);self.assertEqual(g.domains,ds);edges=collections.defaultdict(set)
        for p,keys in ds.items():
            for k in keys:edges[k].add(p)
        self.assertEqual(g.edges,dict(edges))
    def test_complete_fixed_inventory(self):
        self.assertEqual(len(A.inventory(A.frozen(R.basis()),())),996)
    def test_prefix_encoding_and_terminator(self):
        for a in R.basis()['formulas']:self.assertEqual(A.decode_word(R.encode(a)+'e'),a)
        for s in ('PeP','iPe','x','P','Pee'):
            with self.assertRaises(ValueError):A.decode_word(s)
    def test_complete_domains_and_rollback(self):
        m=self.tiny();s=m.initial();g=Graph(m,s)
        def walk(s,g,depth):
            self.graph_equal(m,s,g);before=copy.deepcopy(s);pin=g.fingerprint()
            if not depth:return
            for key in list(g.edges):
                child=s.copy();cg=g.copy();cg.update(m,child,child.place(m.placement(key)));walk(child,cg,depth-1)
                self.assertEqual(s,before);self.assertEqual(g.fingerprint(),pin)
        walk(s,g,2)
    def test_fixed_basis_candidate_completeness(self):
        m=R.Model(R.basis(),R.imp(R.P,R.P),2);s=m.initial();self.graph_equal(m,s,Graph(m,s))
    def test_mark_only_remote_updates(self):
        m=self.tiny(4);s=m.initial();g=Graph(m,s);candidate=next(k for k in g.edges if k[0]==3 and k[2] and 0 in k[2])
        old=g.domains[R.cell(0)].copy();g.update(m,s,s.place(m.placement(candidate)))
        self.graph_equal(m,s,g);self.assertNotEqual(old,g.domains[R.cell(0)]);self.assertNotIn(R.scope(0),g.domains)
    def test_dead_then_forced_then_generation(self):
        m=self.tiny(3);s=m.initial();g=Graph(m,s)
        # These graph fixtures isolate the contractual ordering independently.
        ps=list(sorted(g.domains));g.domains={ps[0]:{('a',),('b',)},ps[1]:{('c',)},ps[2]:set()}
        self.assertEqual(g.decision(s)[0],'dead');g.domains[ps[2]]={('d',),('e',)}
        self.assertEqual(g.decision(s)[:2],('forced',ps[1]));g.domains[ps[1]]={('c',),('f',)}
        s.generations={ps[0]:2,ps[1]:0,ps[2]:1};g.domains[ps[1]].add(('g',))
        self.assertEqual(g.decision(s)[:2],('branch',ps[1]))
    def test_zero_is_assigned_missing_is_free(self):
        s=State();c=Placement((1,),(),(((0,0),0),),());self.assertTrue(s.legal(c));s.marks[(0,0)]=1;self.assertFalse(s.legal(c))
    def test_fractional_and_shared_candidate(self):
        m=R.Model(dict(rules=[]),R.P,2);s=m.initial();c=Placement((9,),((R.cell(0),6),(R.cell(1),6)),(),())
        m.cache={c.key:c};m.align_cache={R.cell(0):(c.key,),R.cell(1):(c.key,)}
        m.dependencies={R.cell(0):{c.key},R.cell(1):{c.key}}
        g=Graph(m,s);self.assertEqual(len(g.edges[c.key]),2)
        g.update(m,s,s.place(c));self.assertEqual(g.decision(s)[0],'dead')
    def test_repeated_refs_are_single_valued(self):
        m=self.tiny(3);self.assertNotIn((2,2,(0,0)),m.cache)
    def test_complete_tiny_certificate_sets(self):
        m=self.tiny(2);point=set()
        def walk(s,g):
            kind,p,keys=g.decision(s)
            if kind=='empty':point.add(tuple(sorted(s.order)));return
            for key in keys:
                ss=s.copy();gg=g.copy();gg.update(m,ss,ss.place(m.placement(key)));walk(ss,gg)
        walk(m.initial(),Graph(m,m.initial()));logical=set()
        for keys in itertools.product(*(m.alignments(R.cell(j)) for j in range(2))):
            proof=R.decode(m,keys)
            try:A.logical(proof,R.Q,m.hypotheses);logical.add(keys)
            except ValueError:pass
        self.assertEqual(point,logical);self.assertTrue(point)
    def test_unused_invalid_line_is_rejected(self):
        a=R.imp(R.P,R.imp(R.Q,R.P))
        with self.assertRaises(ValueError):A.logical([dict(kind='H1',formula=R.P,refs=()),dict(kind='H1',formula=a,refs=())],a)
    def test_schema_forgery_and_scope_leak(self):
        with self.assertRaises(ValueError):A.logical([dict(kind='mp',formula=R.Q,refs=(-2,-1))],R.Q,(R.P,))
        with self.assertRaises(ValueError):A.logical([dict(kind='H2',formula=R.imp(R.P,R.P),refs=())],R.imp(R.P,R.P))
    def test_proposals_are_scheduler_valid_expansions(self):
        m=self.tiny(3);s=m.initial();g=Graph(m,s);policy=R.Policy();seq,_,end,eg=R.propose(m,s,g,policy,R.random.Random(13))
        for key in seq:
            kind,p,keys=g.decision(s);self.assertIn(key,keys);g.update(m,s,s.place(m.placement(key)))
        self.assertEqual(s,end);self.assertEqual(g.fingerprint(),eg.fingerprint());self.assertTrue(1<=len(seq)<=3)
    def test_budget_unknown_and_exhaustion_distinct(self):
        m=self.tiny(2);self.assertEqual(R.search(m,node_limit=0)['status'],'unknown_search_budget')
        m=R.Model(R.basis(),R.P,1);self.assertEqual(R.search(m)['status'],'exhausted_finite_envelope')

if __name__=='__main__':unittest.main()
