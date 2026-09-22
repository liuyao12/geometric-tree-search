import unittest
from a2_online_marking_sat import MarkingSolver

class MarkingTests(unittest.TestCase):
    def test_initially_free(self):
        r = MarkingSolver(3).solve()
        self.assertEqual(r['values'], [None,None,None])

    def test_signed_zero_is_assigned(self):
        s = MarkingSolver(2)
        s.add(True, [[0,0,-1]])
        s.add(False, [[0,1,1]])
        r = s.solve()
        self.assertEqual(r['status'],'sat')
        self.assertEqual(r['values'][0],0)
        self.assertNotEqual(r['values'][0],r['values'][1])

    def test_free_breaks_path(self):
        s = MarkingSolver(3)
        s.add(True, [[0,1,1],[1,2,1]])
        s.add(False, [[0,2,1]])
        r = s.solve()
        self.assertEqual(r['status'],'sat')
        self.assertIsNone(r['values'][1])
        self.assertNotEqual(r['values'][0],r['values'][2])

    def test_contradictory_pair_is_unsat(self):
        s = MarkingSolver(2)
        s.add(True, [[0,1,1]])
        s.add(False, [[0,1,1]])
        self.assertEqual(s.solve()['status'],'unsat')

    def test_distinct_labels_preserve_earlier_negatives(self):
        s=MarkingSolver(3)
        s.add(False,[[0,1,1]])
        self.assertEqual(s.solve()['status'],'sat')
        s.add(False,[[1,2,1]])
        s.add(True,[[0,2,1]])
        r=s.solve()['values']
        self.assertIsNotNone(r[0]);self.assertIsNotNone(r[1]);self.assertIsNotNone(r[2])
        self.assertEqual(r[0],r[2]);self.assertNotEqual(r[0],r[1])

if __name__=='__main__':unittest.main()
