import copy,random,unittest,json
import budget_family_policy as P
import budget_family_search as S
import check_budget_families as V
import dependency_budget as B
import dependency_budget_search as Base
import quantifier_family_patterns as Patterns
from budget_family_join import Join
from quantifier_family_cases import case
from run_adaptive_clusters import inventory
from budget_family_worker import HEURISTIC

def run(spec,library=(),weights=None,stochastic=False,seed=0,feature_mode='justified'):
    cat=inventory(spec);raw=B.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    cert=B.synthesis(raw);model=B.Model(cat,spec['target'],spec['bound'],spec['hypotheses'],cert)
    r=S.search(model,library,'policy' if weights is not None else 'base',weights,stochastic,seed,attempts=10000,seconds=60,feature_mode=feature_mode)
    r['tiles']=[dict(key=k,occupancy=model.placement(k).occupancy,marks=model.placement(k).marks) for k in r['placements']]
    r['root_marks']=tuple(sorted(model.initial().marks.items()));r['total_seconds']=r['seconds']+.001
    return cat,cert,model,r

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.library=[]
        for n in (1,2,3):
            spec=case('quantifier-donor-test-budget-'+str(n),hops=n)
            cat,cert,model,r=run(spec,cls.library,HEURISTIC if cls.library else None)
            cls.library.extend(Patterns.promote(spec,cat,r,cls.library,maximum=6))

    def audit(self,spec,cat,cert,r):
        required=V.D.certificate(cat['rules'],spec,cert)
        return V.result(cat['rules'],dict(spec,_formulas=cat['formulas']),{t['name']:t for t in self.library},r,required)

    def test_justification_excludes_dangling_goal_and_is_monotone(self):
        spec=case('future-goal',hops=3);cat,cert,m,r=run(spec,self.library,HEURISTIC)
        state=m.initial();g=B.Graph(m,state)
        key=(spec['bound'],-1,());self.assertIn(key,g.domains[V.A.cell(key[0])]);g.update(m,state,state.place(m.placement(key)))
        rid=next(i for i,row in enumerate(cat['rules']) if row['kind']=='generalize' and row['output']==m.target)
        key=(spec['bound']-1,rid,(spec['bound']-2,));self.assertIn(key,g.domains[V.A.cell(key[0])]);g.update(m,state,state.place(m.placement(key)))
        self.assertIn(m.target,g.ports.values())
        self.assertNotIn(m.target,P.justified(m,state.order).values())
        self.assertEqual(P.justified(m,state.order),V.established(V.F(cat['rules']),spec,V.F(state.order)))
        self.assertTrue(all(e['features'][i][3]>=0 for e in r['policy_events'] for i in range(len(e['features']))))
        self.audit(spec,cat,cert,r)

    def test_zero_and_occupied_controls_preserve_complete_base_trace(self):
        spec=case('defer-controls',hops=2)
        cat,cert,m,zero=run(spec,self.library,[0.]*12)
        _,_,_,occupied=run(spec,self.library,HEURISTIC,feature_mode='occupied')
        _,_,_,base=run(spec)
        self.assertEqual(zero['placements'],base['placements']);self.assertFalse(zero['hints'])
        self.assertIn(occupied['status'],('finite_exact_proof_region','unknown_search_budget'))
        for r in (zero,occupied,base):self.audit(spec,cat,cert,r)
        original=Base.search(B.Model(cat,spec['target'],spec['bound'],spec['hypotheses'],cert),attempts=10000,seconds=60)
        self.assertEqual(original['placements'],base['placements']);self.assertEqual(original['metrics']['attempts'],base['metrics']['attempts'])

    def test_three_levels_and_longer_proof_expand_to_original_tiles(self):
        self.assertEqual(sorted(set(t['level'] for t in self.library)),[1,2,3])
        spec=case('longer-budget-proof',hops=5);cat,cert,m,r=run(spec,self.library,HEURISTIC)
        self.assertEqual(r['status'],'finite_exact_proof_region');self.assertEqual(len(r['proof']),12)
        self.assertTrue(r['solution_hints']);self.audit(spec,cat,cert,r)
        for item in r['hints']:V.check_item(V.F(cat['rules']),spec,{t['name']:t for t in self.library},item['item'],V.F(item['chosen']),m.requirements)

    def test_sampled_actions_update_and_corruptions(self):
        spec=case('sampled-budget',hops=2);cat,cert,m,r=run(spec,self.library,[0.]*12,True,73)
        self.audit(spec,cat,cert,r)
        after,baseline,u=P.update([0.]*12,.4,r)
        self.assertEqual((after,baseline),V.update([0.]*12,.4,r,u))
        for field in ('census','feature','order','query','mark'):
            bad=json.loads(json.dumps(r))
            if field=='census':bad['search_tree']['census'][0][1]+=1
            elif field=='feature':bad['policy_events'][0]['features'][0]=[1.]*12
            elif field=='order':bad['search_tree']['children'][0]['key']=(0,999,())
            elif field=='query':bad['index']['queries'].pop()
            else:
                mark=next(x for x in bad['tiles'][0]['marks'] if x[0][0]==-3000)
                bad['tiles'][0]['marks']=tuple((p,1 if p==mark[0] else v) for p,v in bad['tiles'][0]['marks'])
            with self.assertRaises(ValueError):self.audit(spec,cat,cert,bad)

    def test_indexed_and_enumerated_join_and_exact_caller_rollback(self):
        spec=case('join-budget',hops=2);cat,cert,m,r=run(spec)
        state=m.initial();g=B.Graph(m,state)
        while g.decision(state)[0]=='forced':
            key=g.decision(state)[2][0];g.update(m,state,state.place(m.placement(key)))
        point=g.decision(state)[1];before=(state.copy(),g.fingerprint())
        indexed=Join(m,self.library)(m,state,g,point,self.library,32)
        enumerated=Join(m,self.library,enumerated=True)(m,state,g,point,self.library,32)
        self.assertEqual(indexed,enumerated);self.assertEqual(state,before[0]);self.assertEqual(g.fingerprint(),before[1])

if __name__=='__main__':unittest.main()
