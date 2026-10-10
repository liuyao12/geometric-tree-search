"""Real pinned rows compared with the older independent radius-one compiler."""
import gzip,itertools,unittest
from pathlib import Path
from shared_wang_inventory import Inventory,points
from wang import Compiler,head

class SharedWangTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        docs=Path(__file__).resolve().parents[2]/'docs/research/gcts-rl-renewal'
        cls.raw=gzip.decompress((docs/'proof-boundary-machine-001.bin.gz').read_bytes())
        cls.inventory=Inventory(cls.raw)
    def test_real_state_submachines(self):
        i=self.inventory;states=(0,1,2,355935,355936,355937,355938,458931)
        transitions={(q,s):a for q in states for s in range(i.A) if (a:=i.transition(q,s)) is not None}
        old=Compiler(range(i.A),states,transitions,0)
        normal=(0,3,4,9,16,17)
        for q,s,position,a,b in itertools.product(states,range(i.A),range(3),normal,normal):
            triple=[a,b,b];triple[position]=i.head(q,s)
            reference=[a,b,b];reference[position]=head(q,s)
            result=old.rule(*reference)
            expected=None if result is None else i.head(result[1],result[2]) if isinstance(result,tuple) else result
            self.assertEqual(i.successor(*triple),expected)
    def test_multhead_and_undefined_center(self):
        i=self.inventory
        for a,b in ((0,1),(0,2),(1,2)):
            triple=[3,3,3];triple[a]=i.head(0,3);triple[b]=i.head(0,3)
            self.assertIsNone(i.successor(*triple))
        self.assertIsNone(i.successor(3,i.head(i.reject,3),3))
        self.assertIsNone(i.successor(3,i.head(i.space,3),3))
    def test_point_parities_and_matching(self):
        i=self.inventory;tile=i.tile(3,4,3);p=points(tile)
        self.assertEqual(p['t'],[[[0,0],1]])
        self.assertEqual({tuple(v[0]) for v in p['m']},{(0,-1),(0,1),(-1,0),(1,0)})
        right=i.tile(4,3,4)
        self.assertEqual(tile['E'],right['W'])
        self.assertNotIn((0,0),{tuple(v[0]) for v in p['m']})
    def test_inventory_trust_and_count(self):
        i=self.inventory
        self.assertEqual(sum(i.counts.values()),264143617200)
        self.assertEqual(i.defined,17899987)
        with self.assertRaises(ValueError):Inventory(self.raw[:-1]+bytes([self.raw[-1]^1]))
        tile=i.tile(3,4,3);self.assertTrue(i.contains(tile));tile['N']=3;self.assertFalse(i.contains(tile))
if __name__=='__main__':unittest.main()
