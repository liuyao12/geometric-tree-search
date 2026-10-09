"""Compiler, symbolic-domain, exact-marking and proof-boundary semantics."""
import copy,itertools,json,random,unittest
import wang,lazy_wang
import proof_search
from turtle import Policy
from rewrite_machine import Theory,ProofMachine,check_derivation,tm_theory

class ProofMachineTests(unittest.TestCase):
    def test_generic_compiler_matches_independent_word_semantics(self):
        theory=Theory(('a','b'),((('a',),('b','b')),(('a','b'),('a',)),((),('a',)),(('b',),())))
        rng=random.Random(210)
        for _ in range(100):
            source=tuple(rng.choice(theory.alphabet) for i in range(rng.randrange(4)))
            commands=[];word=source;valid=True
            for j in range(rng.randrange(4)):
                rule=rng.randrange(len(theory.rules));pos=rng.randrange(len(word)+2);commands.append((rule,pos))
                left,right=theory.rules[rule]
                if pos>len(word) or word[pos:pos+len(left)]!=left:valid=False
                elif valid:word=word[:pos]+right+word[pos+len(left):]
            target=word if valid else ('a',)
            machine=ProofMachine(theory,target);direct,_=check_derivation(theory,source,target,commands,8)
            result=machine.run(source,8,machine.certificate_tokens(commands),10000)
            self.assertNotEqual(result['status'],'unknown_step_budget')
            self.assertEqual(result['status']=='accept',direct,(source,target,commands))

    def test_padding_overflow_and_empty_rules(self):
        theory=Theory(('a','b'),((('a',),('b','b','b')),(('b','b','b'),('a',)),((),('a',)),(('a',),())))
        machine=ProofMachine(theory,('a',));tokens=machine.certificate_tokens(((0,0),(1,0)))
        self.assertEqual(machine.run(('a',),2,tokens)['status'],'reject')
        self.assertEqual(machine.run(('a',),3,tokens)['status'],'accept')
        self.assertTrue(check_derivation(theory,('a',),('a',),((0,0),(1,0)))[0])
        self.assertEqual(machine.run((),1,machine.certificate_tokens(((2,0),)))['status'],'accept')
        empty=ProofMachine(theory,());self.assertEqual(empty.run(('a',),1,empty.certificate_tokens(((3,0),)))['status'],'accept')
        self.assertEqual(empty.run((),0,())['status'],'accept')
        self.assertEqual(machine.run(('a',),3,('r:0','p'))['status'],'reject')
        self.assertEqual(machine.run(('a',),3,(';',))['status'],'reject')
        with self.assertRaises(ValueError):machine.certificate_tokens(((0,-1),))

    def test_tm_reduction_preserves_each_transition_and_accept_cleanup(self):
        compiler=wang.Compiler(('B','1'),('start','next','halt'),
                               {('start','B'):('next','1',1),('next','B'):('halt','1',0)},'halt')
        theory,encode=tm_theory(compiler);row=('B',wang.head('start','B'),'B','B');word=encode(row)
        for _ in range(2):
            next_row=wang.direct_step(compiler,row);desired=encode(next_row)
            matches=[(r,pos) for r,(left,right) in enumerate(theory.rules) for pos in range(len(word)+1)
                     if word[pos:pos+len(left)]==left and word[:pos]+right+word[pos+len(left):]==desired]
            self.assertEqual(len(matches),1);self.assertTrue(check_derivation(theory,word,desired,matches)[0])
            row,word=next_row,desired
        commands=[];original=word
        while word!=('ACCEPT',):
            choices=[(r,pos,left,right) for r,(left,right) in enumerate(theory.rules) for pos in range(len(word)+1)
                     if word[pos:pos+len(left)]==left]
            self.assertTrue(choices);r,pos,left,right=choices[0];commands.append((r,pos));word=word[:pos]+right+word[pos+len(left):]
        self.assertTrue(check_derivation(theory,original,('ACCEPT',),commands)[0])
        # Border extension is part of the unbounded-tape reduction.
        left_compiler=wang.Compiler(('B','1'),('q','halt'),{('q','B'):('halt','1',-1)},'halt')
        left_theory,enc=tm_theory(left_compiler);w=enc((wang.head('q','B'),))
        self.assertTrue(any(left==w[:-1] and right[0]=='L' and len(right)==4 for left,right in left_theory.rules))

    def test_symbolic_inventory_and_domains_equal_full_enumeration(self):
        compiler=wang.Compiler((0,1),('a','b','halt'),{('a',0):('b',1,1),('b',0):('halt',1,0)},'halt')
        inventory=compiler.tiles();u=lazy_wang.Universe(compiler);self.assertEqual(u.inventory_count,len(inventory))
        rng=random.Random(250)
        for _ in range(100):
            constraints={}
            for field in ('north','south','west','east'):
                if rng.randrange(2):constraints[field]=rng.choice(inventory)[{'north':'N','south':'S','west':'W','east':'E'}[field]]
            for name in ('allowed_a','allowed_b','allowed_c'):
                if rng.randrange(2):constraints[name]=tuple(s for s in u.symbols if rng.randrange(2))
            d=u.domain(**constraints)
            # Apply each independent restriction without using Domain.contains.
            expected={t['triple'] for t in inventory if all(name not in constraints or t[f]==constraints[name] for f,name in (('N','north'),('S','south'),('W','west'),('E','east')))
                      and all(name not in constraints or t['triple'][i] in constraints[name] for i,name in enumerate(('allowed_a','allowed_b','allowed_c')))}
            self.assertEqual(set(d.options()),expected);self.assertEqual(d.count,len(expected))
            self.assertEqual({t['triple'] for t in inventory if d.contains(t['triple'])},expected)

    def test_graph_domains_mark_dependencies_and_exact_rollback(self):
        compiler=wang.Compiler(('B','1'),('write','halt'),{('write','B'):('halt','1',0)},'halt')
        pattern=(('B',),('B',),(wang.head('write','B'),),('B',),('B',))
        top=('B','B',wang.head('halt','1'),'B','B');inventory=compiler.tiles();u=lazy_wang.Universe(compiler)
        for extended in (False,True):
            g=lazy_wang.Graph(u,pattern,2,top,extended=extended);before=g.fingerprint();rng=random.Random(251)
            for step in range(8):
                for (x,y),domain in g.domains.items():
                    expected=set()
                    for tile in inventory:
                        _,marks=lazy_wang.point_tile(tile,x,y,extended)
                        if any(p in g.marks and g.marks[p]!=v for p,v in marks.items()):continue
                        if y==0 and any(tile['triple'][i] not in (pattern[j] if 0<=j<len(pattern) else ('B',)) for i,j in enumerate((x-1,x,x+1))):continue
                        expected.add(tile['triple'])
                    self.assertEqual(set(domain.options()),expected)
                mode,p,d=g.decision()
                if mode in ('dead','empty'):break
                g.place(p,rng.choice(tuple(d.options())))
            g.rollback(0);self.assertEqual(g.fingerprint(),before)

    def test_unknown_certificate_search_independent_replay_and_tamper(self):
        machine=ProofMachine(Theory(('a','b'),((('a',),('b',)),)),('b',))
        witness=machine.run(('a',),3,machine.certificate_tokens(((0,0),)))
        pattern=machine.pattern(('a',),3,2);height=witness['steps'];top=machine.accepting_row(len(pattern))
        found=lazy_wang.search(machine.compiler,pattern,height,top,node_limit=10000,seconds=5,extended=True)
        self.assertEqual(found['status'],'finite_accepting_proof_rectangle')
        self.assertTrue(lazy_wang.independent_check(machine.compiler,pattern,top,found['rows'],found['placements'],extended=True))
        altered=copy.deepcopy(found['placements']);x,y,t=altered[0];t['N']='bad'
        self.assertFalse(lazy_wang.independent_check(machine.compiler,pattern,top,found['rows'],altered,extended=True))
        self.assertTrue(all(gen==1 for gen in found['tile_generations']))
        unknown=lazy_wang.search(machine.compiler,pattern,height,top,node_limit=0,extended=True)
        self.assertEqual(unknown['status'],'unknown_budget')

    def test_json_proof_replay_requires_external_statement_and_valid_ids(self):
        machine=ProofMachine(Theory(('a','b'),((('a',),('b',)),)),('b',))
        proposal=proof_search.propose(machine,('a',),3,9,Policy())
        preferred=proof_search.rectangle_preference(machine,('a',),3,3,128,proposal)
        for extended in (False,True):
            result=lazy_wang.search(machine.compiler,machine.pattern(('a',),3,3),128,machine.accepting_row(13),
                                    preferred=preferred,extended=extended)
            packed=json.loads(json.dumps(proof_search.pack(result)))
            self.assertTrue(proof_search.replay(machine,('a',),3,3,128,packed))
            other=ProofMachine(machine.theory,('a',))
            self.assertFalse(proof_search.replay(other,('a',),3,3,128,packed))
            other=ProofMachine(Theory(('a','b'),((('b',),('a',)),)),('b',))
            self.assertFalse(proof_search.replay(other,('a',),3,3,128,packed))
            for field,value in (('initial',-1),('initial',True),('grid',-1),('grid',True)):
                changed=copy.deepcopy(packed)
                if field=='initial':changed['certificate'][field][0]=value
                else:changed['certificate'][field][0][0]=value
                self.assertFalse(proof_search.replay(machine,('a',),3,3,128,changed))
            changed=copy.deepcopy(packed);changed['marking']='invented'
            self.assertFalse(proof_search.replay(machine,('a',),3,3,128,changed))
            changed=copy.deepcopy(packed);kind=changed['certificate']['tile_types_used'][0]
            kind[-1]=(kind[-1]+1)%len(changed['certificate']['symbols'])
            self.assertFalse(proof_search.replay(machine,('a',),3,3,128,changed))
        # A bad preference is only an ordering hint; every base option remains.
        found=lazy_wang.search(machine.compiler,machine.pattern(('a',),3,2),62,machine.accepting_row(12),
                               preferred={(0,0):('invented',)*3},extended=True)
        self.assertTrue(found['verified'])

    def test_fair_bound_repetition_and_unknown_outer_budget(self):
        triple=(4,8,128)
        for stage in (12,13,14):
            matches=[b for b in proof_search.bounds(3,stage) if b[:3]==triple]
            self.assertEqual(matches,[triple+(2**stage,)])
        machine=ProofMachine(Theory(('a','b'),((('a',),('b',)),)),('b',))
        bounded=proof_search.fair_search(machine,('a',),max_stage=2)
        self.assertEqual(bounded['status'],'unknown_outer_stage_budget')
        self.assertGreater(bounded['attempts'],0)

    def test_sequence_actions_keep_all_singletons_and_validate_expansion(self):
        theory=Theory(('a','b'),((('a',),('b',)),(('b',),('a',)),((),('a',))))
        word=('a','a');capacity=4;single=dict(proof_search.singles(theory,word,capacity));all_actions=list(proof_search.actions(theory,word,capacity))
        self.assertEqual({commands[0]:after for commands,after in all_actions if len(commands)==1},single)
        for commands,after in all_actions:
            self.assertTrue(check_derivation(theory,word,after,commands,capacity)[0])
        machine=ProofMachine(theory,('b','b'));policy=Policy()
        policy.weights['distance_gain']=1
        proposal=proof_search.propose(machine,word,capacity,2,policy)
        self.assertEqual(proposal['status'],'checked_rewrite_proposal')
        self.assertEqual(proposal['base_steps'],2)
        self.assertEqual(sum(len(e['executed']) for e in proposal['expansions']),proposal['base_steps'])
        limited=proof_search.propose(machine,word,capacity,2,policy,machine_step_limit=1)
        self.assertEqual(limited['status'],'checked_rewrite_proposal')
        self.assertEqual(limited['machine_status'],'unknown_step_budget')

    def test_reduction_all_transition_shapes_and_configuration_invariant(self):
        for direction in (-1,0,1):
            c=wang.Compiler(('B','1'),('q','halt'),{('q','B'):('halt','1',direction)},'halt')
            theory,encode=tm_theory(c)
            for index in (0,1,2):
                row=['B']*3;row[index]=wang.head('q','B');source=encode(row)
                if 0<=index+direction<3:desired=encode(wang.direct_step(c,row))
                elif direction==-1:desired=encode((wang.head('halt','B'),'1','B','B'))
                else:desired=encode(('B','B','1',wang.head('halt','B')))
                choices=list(proof_search.singles(theory,source,30))
                self.assertEqual([after for command,after in choices],[desired])
            with self.assertRaises(ValueError):encode(('B','B'))
            with self.assertRaises(ValueError):encode((wang.head('q','B'),wang.head('q','B')))

if __name__=='__main__':unittest.main()
