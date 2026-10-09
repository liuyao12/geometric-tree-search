import copy,math,random,unittest
import cyclotomic as ring
import penrose_sectors as p

class SectorTests(unittest.TestCase):
    def test_exact_embedding_signs_and_overlap_control(self):
        rng=random.Random(104)
        for _ in range(200):
            a=tuple(rng.randrange(-4,5) for _ in range(4))
            re=sum(a[i]*math.cos(2*i*math.pi/5) for i in range(4));im=sum(a[i]*math.sin(2*i*math.pi/5) for i in range(4))
            if abs(re)>1e-10:self.assertEqual(p.real_sign(a),(re>0)-(re<0))
            if abs(im)>1e-10:self.assertEqual(p.imag_sign(a),(im>0)-(im<0))
        control=p.dense_support_obstruction();self.assertTrue(control["point_capacity_legal"])
        self.assertTrue(p.overlaps(p.polygon(control["placements"][0]),p.polygon(control["placements"][1])))
        a=p.polygon(("thick",0,ring.ZERO));b=p.polygon(("thick",0,ring.ONE))
        self.assertFalse(p.overlaps(a,b))

    def test_all_rotations_zero_roots_and_inventory(self):
        for kind in p.KINDS:
            for r in range(10):
                m=p.Model();c=m.placement((kind,r,ring.ZERO));s=p.State();s.place(c,seed=True)
                self.assertEqual(len(c.positive),10);self.assertEqual(len(s.active),40)
                self.assertEqual(set(s.roots),s.active);self.assertEqual(set(s.generations.values()),{0})
                g=p.Graph(m,s);self.assertEqual(len(g.domains),30)
                self.assertEqual(g.domains,p.exhaustive_domains(m,s))
                self.assertFalse(s.legal(c));self.assertTrue(all(g.domains.values()))

    def test_incremental_domains_reverse_incidence_and_rollback(self):
        m=p.Model();s=p.rooted(m);g=p.Graph(m,s);rng=random.Random(125)
        for _ in range(10):
            mode,point,keys=g.decision(s)
            if mode=="dead":break
            parent=copy.deepcopy((s.totals,s.marks,s.active,s.roots,s.generations,s.order,s.tile_generations,g.domains,g.edges))
            child,cg=s.copy(),g.copy();key=rng.choice(keys);cg.update(child,child.place(m.placement(key)))
            self.assertEqual(cg.domains,p.exhaustive_domains(m,child))
            reverse={}
            for q,cs in cg.domains.items():
                for c in cs:reverse.setdefault(c,set()).add(q)
            self.assertEqual(cg.edges,reverse)
            self.assertEqual(parent,(s.totals,s.marks,s.active,s.roots,s.generations,s.order,s.tile_generations,g.domains,g.edges))
            self.assertEqual(child.tile_generations[-1],1)
            s,g=child,cg

    def test_global_dead_forced_generation_order(self):
        m=p.Model();s=p.rooted(m);g=p.Graph(m,s);points=sorted(g.domains);a,b=points[:2]
        g.domains={a:set(),b:{("fake",)}};self.assertEqual(g.decision(s)[0],"dead")
        g.domains={a:{1,2,3},b:{4}};s.generations[a]=0;s.generations[b]=10
        self.assertEqual(g.decision(s)[:2],("forced",b))
        g.domains={a:{1,2,3},b:{4,5}};self.assertEqual(g.decision(s)[:2],("branch",a))

    def test_mark_only_dependency_including_assigned_zero(self):
        local=(p.VERTICES["thick"][0],5)
        self.assertNotIn(local,p.BASE["thick"])
        m=p.Model({"thick":{local:0}});s=p.rooted(m);g=p.Graph(m,s)
        candidate=next((k for k in g.edges if m.placement(k).marks and m.placement(k).marks[0][0] not in s.marks),None)
        self.assertIsNotNone(candidate);q=m.placement(candidate).marks[0][0]
        self.assertIn(candidate,m.dependencies[q]);s.marks[q]=1;g.update(s,{q})
        self.assertNotIn(candidate,g.edges);self.assertEqual(g.domains,p.exhaustive_domains(m,s))

    def test_independent_positive_corona_and_tamper(self):
        for i,kind in enumerate(p.KINDS):
            m=p.Model();r=p.corona(m,kind,seed=91000+i,node_limit=1000,seconds=5)
            self.assertEqual(r["status"],"positive")
            self.assertTrue(p.verify_patch(m,r["placements"],r["required_points"]))
            self.assertFalse(p.verify_patch(m,r["placements"]+[r["placements"][0]]))
            self.assertFalse(p.verify_patch(m,[(kind,10,ring.ZERO)]))
            self.assertFalse(p.verify_patch(m,[(kind,0,(0,0,0))]))
            self.assertFalse(p.verify_patch(m,[(kind,False,ring.ZERO)]))
        limited=p.corona(p.Model(),node_limit=0,seconds=5)
        self.assertEqual(limited["status"],"unresolved");self.assertIsNone(limited["certificate"])

    def test_exhausted_dead_certificate_and_fabricated_leaf(self):
        # A deliberately restrictive marking control, never discovery input.
        markings={kind:{(v,s):40*i+10*j+s for j,v in enumerate(p.VERTICES[kind]) for s in range(10)}
                  for i,kind in enumerate(p.KINDS)}
        model=p.Model(markings);result=p.corona(model)
        self.assertEqual(result["status"],"negative")
        ok,n=p.check_failure(model,"thick",None,result["certificate"])
        self.assertTrue(ok);self.assertEqual(n,1)
        occupied=min(p.BASE["thick"])
        self.assertFalse(p.check_failure(model,"thick",None,{"dead":occupied})[0])

if __name__=="__main__":unittest.main()
