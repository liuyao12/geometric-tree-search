import json,struct,subprocess,tempfile,unittest
from pathlib import Path
from tape_binary import write_micro,write_micro_input
from micro_cert import compile_tools,write_cuts,run
from audit_logical_wang_clusters import apply

HERE=Path(__file__).resolve().parent
class ObservedClusterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='gcts-observed-tests-',dir='/private/tmp');cls.p=Path(cls.tmp.name)
        compile_tools(cls.p)
        for source,name in (('micro_line_builder.cpp','observed-builder'),('micro_line_check.cpp','observed-checker')):
            subprocess.run(['clang++','-O3','-std=c++17',str(HERE/source),'-o',str(cls.p/name)],check=True)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def example(self,reject=False):
        # A right sweep, cross-band write, left sweep and final observation.
        m=dict(rows=[None,None,None,[0,{'0':[3,'0',1],'B':[4,'1',0]}],
            [1,{'1':[5,'0',-1]}],[0,{'0':[5,'0',-1],'1':[5,'1',-1],'^':[6,'^',0]}],
            [1,{'B':[1 if reject else 0,'1',0]}]],start=3,accept=0,reject=1,space=2,tapes=2,names=['x']*7)
        initial=dict(words=['000','B1'],heads=[1,2],capacities=[12,12])
        write_micro(m,self.p/'code');write_micro_input(initial,self.p/'input');write_cuts([],self.p/'cuts')
        (self.p/'focus').write_bytes(struct.pack('<6I',0x474c4631,4,1,2,0,1))
        old=run(self.p/'builder',[self.p/'code',self.p/'input',self.p/'old-grammar',self.p/'old-output',1000,10000,self.p/'cuts'])
        new=run(self.p/'observed-builder',[self.p/'code',self.p/'input',self.p/'grammar',self.p/'output',1000,10000,self.p/'cuts',self.p/'focus',self.p/'events'])
        events=[json.loads(v) for v in (self.p/'events').read_text().splitlines()]
        ids=[e['node'] for e in events if e['kind']=='fragment'];write_cuts(ids,self.p/'ids')
        checked=run(self.p/'observed-checker',[self.p/'code',self.p/'input',self.p/'grammar',self.p/'checked',1000,100000,self.p/'root',self.p/'ids'])
        independently=run(self.p/'checker',[self.p/'code',self.p/'input',self.p/'grammar',self.p/'old-checked',1000,100000,self.p/'old-root'])
        for key in ('micro_steps','physical_steps'):self.assertEqual(old[key],new[key]);self.assertEqual(checked[key],new[key]);self.assertEqual(independently[key],new[key])
        self.assertEqual(new['status'],'rejected' if reject else 'accepted')
        for name in ('old-output','checked','old-checked'):self.assertEqual((self.p/name).read_bytes(),(self.p/'output').read_bytes())
        root=json.loads((self.p/'root').read_text());responses={r['node']:r['response'] for r in root['observations']}
        tapes=[bytearray('B^01:,;'.index(s) for s in '^'+w+'B'*(n-len(w)-1)) for w,n in zip(initial['words'],initial['capacities'])]
        heads=list(initial['heads']);base=[2,16];q=3;p=physical=0
        for e in events:
            if e['kind']=='fragment':
                q,p,cost=apply(responses[e['node']],tapes,heads,base,q,p);physical+=cost
                self.assertEqual(physical,e['end_physical']);self.assertEqual(p,e['output_head'])
        self.assertEqual(physical,new['physical_steps']);self.assertEqual(new['focus_events'],1)
        return root
    def test_fragment_chain_preserves_sweeps_and_nonzero_incoming_head(self):self.example()
    def test_rejected_computation_has_the_same_checked_expansion(self):self.example(True)
    def test_observation_ids_cannot_replace_or_forge_interfaces(self):
        self.example();write_cuts([0xffffffff],self.p/'ids')
        r=subprocess.run([str(self.p/'observed-checker'),str(self.p/'code'),str(self.p/'input'),str(self.p/'grammar'),str(self.p/'bad'), '1000','100000',str(self.p/'bad-root'),str(self.p/'ids')],capture_output=True)
        self.assertNotEqual(r.returncode,0)
if __name__=='__main__':unittest.main()
