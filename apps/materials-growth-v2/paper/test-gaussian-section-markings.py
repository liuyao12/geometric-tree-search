import importlib.util
import itertools
import math
from pathlib import Path
import unittest
import numpy as np
from decimal import Decimal,localcontext
spec=importlib.util.spec_from_file_location('fields',Path(__file__).with_name('gaussian-section-markings.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class FieldTest(unittest.TestCase):
    def test_periodic_images_against_independent_brute_force(self):
        cell=np.array([[1.2,0,0],[.8,.9,0],[.3,.4,1.1]])
        points=np.array([[.1,.2,.3],[.7,.5,.8]])
        anchor=np.array([.2,.1,.15]);radius=1.6
        got=m.periodic_field(points,['X','Y'],cell,anchor,radius,.3)
        vectors=[];labels=[]
        # Deliberately independent fixed image box, ample for this test cell.
        for i,p in enumerate(points):
            for n in itertools.product(range(-6,7),repeat=3):
                v=p+np.asarray(n)@cell-anchor
                if np.linalg.norm(v)<radius:vectors.append(v);labels.append(['X','Y'][i])
        expected=m.from_points(vectors,labels,radius,.3)
        self.assertEqual(len(got['vectors']),len(vectors))
        self.assertGreater(len(vectors),len(points))
        self.assertLess(m.discrepancy(got,expected)['squared'],1e-10)

    def test_periodic_covariance_and_cell_representation(self):
        cell=np.array([[1.2,0,0],[.8,.9,0],[.3,.4,1.1]])
        p=np.array([[.1,.2,.3],[.7,.5,.8]]);o=np.array([.2,.1,.15])
        a=m.periodic_field(p,['X','Y'],cell,o,1.6,.3)
        q,_=np.linalg.qr(np.random.default_rng(91).normal(size=(3,3)))
        if np.linalg.det(q)<0:q[:,0]*=-1
        b=m.periodic_field(p@q+3,['X','Y'],cell@q,o@q+3,1.6,.3)
        self.assertLess(m.discrepancy(m.transform(a,q),b)['squared'],1e-10)
        shifted=p+np.array([[4,-3,2],[-2,3,-4]])@cell
        c=m.periodic_field(shifted,['X','Y'],cell,o,1.6,.3)
        self.assertLess(m.discrepancy(a,c)['squared'],1e-10)
        # Integer unimodular basis change preserves the same lattice.
        d=m.periodic_field(p,['X','Y'],np.array([[1,1,0],[0,1,0],[0,0,1]])@cell,o,1.6,.3)
        self.assertEqual(len(a['vectors']),len(d['vectors']))
        self.assertLess(m.discrepancy(a,d)['squared'],1e-10)

    def test_periodic_cutoff_and_invalid_input(self):
        cell=np.eye(3)*4
        a=m.periodic_field([[1-1e-4,0,0]],['X'],cell,[0,0,0],1,.25)
        b=m.periodic_field([[1+1e-4,0,0]],['X'],cell,[0,0,0],1,.25)
        self.assertEqual(len(a['vectors']),1);self.assertEqual(len(b['vectors']),0)
        self.assertLess(m.discrepancy(a,b)['squared'],1e-20)
        with self.assertRaises(ValueError):m.from_points([[float('nan'),0,0]],['X'],1,.25)
        with self.assertRaises(ValueError):m.periodic_field([[0,0,0]],['X'],cell,[0,0,0],10,.25,max_images=1)
        with self.assertRaises(ValueError):m.periodic_field([[0,0,0]],['X'],np.zeros((3,3)),[0,0,0],1,.25)
    def test_rotation_and_permutation(self):
        a=m.from_points([[.1,.2,0],[-.3,.1,.2]],[['X'],['Y']],1,.25)
        b=m.from_points([[.15,.2,0],[-.4,.1,.2]],[['X'],['Y']],1,.25)
        q,_=np.linalg.qr(np.random.default_rng(14).normal(size=(3,3)))
        if np.linalg.det(q)<0:q[:,0]*=-1
        self.assertAlmostEqual(m.discrepancy(a,b)['squared'],m.discrepancy(m.transform(a,q),m.transform(b,q))['squared'],places=12)
        perm=dict(a,vectors=a['vectors'][::-1],colors=a['colors'][::-1],amplitudes=a['amplitudes'][::-1])
        self.assertLessEqual(m.discrepancy(a,perm)['squared'],1e-14)
        p=np.array([[.1,.5,.2],[-.2,0,.1]])
        self.assertTrue(np.allclose(m.evaluate(a,p,['X']),m.evaluate(m.transform(a,q),p@q,['X'])))
    def test_smooth_entry_not_fixed_cardinality(self):
        empty=m.from_points([],[],1,.25)
        inside=m.from_points([[1-1e-4,0,0]],[['X']],1,.25)
        outside=m.from_points([[1+1e-4,0,0]],[['X']],1,.25)
        self.assertEqual(outside['vectors'],[])
        self.assertLess(m.discrepancy(inside,empty)['squared'],1e-20)
    def test_midpoint_and_label_separation(self):
        a=m.from_points([[0,0,0]],[['X']],1,.25);b=m.from_points([[.2,0,0]],[['X']],1,.25)
        w=m.mixture(a,b);d=m.discrepancy(a,b)['squared']
        self.assertAlmostEqual(m.discrepancy(a,w)['squared'],d/4,places=12)
        self.assertAlmostEqual(m.discrepancy(b,w)['squared'],d/4,places=12)
        c=dict(a,colors=[['Y']]);self.assertAlmostEqual(m.discrepancy(a,c)['squared'],2)
        self.assertEqual(m.pair_status(a,c,.1)['status'],'separated')
        self.assertEqual(m.pair_status(a,b,1)['status'],'compatible')
        self.assertEqual(m.pair_status(a,a,0)['status'],'numerically-unresolved')
    def test_low_moment_collision_is_distinguished(self):
        def points(offset):
            angles=[0,120,240,offset,offset+120,offset+240]
            return np.array([[.5*math.cos(math.radians(t)),.5*math.sin(math.radians(t)),0] for t in angles])
        a,b=points(60),points(30)
        self.assertTrue(np.allclose(a.sum(axis=0),b.sum(axis=0)))
        self.assertTrue(np.allclose(a.T@a,b.T@b))
        self.assertGreater(m.discrepancy(m.from_points(a,[['X']]*6,1,.2),m.from_points(b,[['X']]*6,1,.2))['lower'],.01)
    def test_decimal_reference(self):
        a=m.from_points([[.1,0,0],[-.2,.3,0]],[['X'],['X']],1,.3)
        b=m.from_points([[.2,0,.1]],[['X']],1,.3)
        with localcontext() as ctx:
            ctx.prec=60
            def D(v):return Decimal.from_float(float(v))
            points=a['vectors']+b['vectors'];weights=a['amplitudes']+[-x for x in b['amplitudes']]
            value=sum(D(weights[i])*D(weights[j])*(-sum((D(u)-D(v))**2 for u,v in zip(x,y))/(2*D(a['sigma'])**2)).exp() for i,x in enumerate(points) for j,y in enumerate(points))
        report=m.discrepancy(a,b)
        self.assertLessEqual(abs(float(value)-report['rawSquared']),report['roundoffGuard'])
if __name__=='__main__':unittest.main()
