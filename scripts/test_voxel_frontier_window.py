#!/usr/bin/env python3
import copy,json,subprocess,sys,tempfile,unittest
from collections import Counter
from itertools import product
from pathlib import Path
from solve_voxel_pair_corona import solve,solve_window
from certify_voxel_obstruction import construct

ROOT=Path(__file__).resolve().parents[1]
def support(voxels):
    totals=Counter()
    for v in voxels:
        totals[tuple(2*x+1 for x in v)]+=8
        for d in product([0,1],repeat=3):totals[tuple(2*(v[i]+d[i]) for i in range(3))]+=1
    return [{'pos':list(q),'weight':n} for q,n in totals.items()]
def model(orientations):return {'capacity':8,'placementDomain':{'kind':'scaled_cubic','translationStep':2},'required':[{'pos':[1,1,1]}],'orientations':[{'voxels':o,'cells':support(o)} for o in orientations]}
def point_replay(data,result):
    m=data['model'];totals=Counter();seen=set()
    for p in result['placements']:
        ident=(p['oi'],tuple(p['translation']));assert ident not in seen;seen.add(ident)
        assert all(type(x) is int and x%2==0 for x in p['translation'])
        for c in m['orientations'][p['oi']]['cells']:totals[tuple(c['pos'][i]+p['translation'][i] for i in range(3))]+=c['weight']
    assert max(totals.values())<=8
    assert all(totals[tuple(p['pos'])]==8 for p in m['required'])
    assert all((p['oi'],tuple(p['translation'])) in seen for p in data.get('fixed',[]))
    for q,n in totals.items():
        if n==8:continue
        found=False
        for oi,o in enumerate(m['orientations']):
            for c in o['cells']:
                t=tuple(q[i]-c['pos'][i] for i in range(3))
                if any(x%2 for x in t) or (oi,t) in seen:continue
                if all(totals[tuple(s['pos'][i]+t[i] for i in range(3))]+s['weight']<=8 for s in o['cells']):found=True;break
            if found:break
        assert found,('dead point',q)

class FrontierWindow(unittest.TestCase):
    def setUp(self):self.cube={'model':model([[[0,0,0]]]),'fixed':[{'oi':0,'translation':[0,0,0]}]}
    def test_outside_pool_candidates(self):
        r=solve_window(self.cube,resume_points=[[0,0,0]])
        self.assertEqual(r['result'],'finite_exact');self.assertEqual(r['stats']['candidates'],1);point_replay(self.cube,r)
    def test_fixed_tile_outside_target(self):
        self.cube['fixed'][0]['translation']=[20,0,0]
        r=solve_window(self.cube);self.assertEqual(r['result'],'finite_exact');point_replay(self.cube,r)
    def test_pair_window_equivalence(self):
        geometry=json.loads((ROOT/'data/3d-p9-42947-pair-obstructions-2026-09-21.json').read_text())
        m=model(geometry['orientations']);pair=geometry['obstructions'][0]['pair']
        points={tuple(c['pos'][i]+p['translation'][i] for i in range(3)) for p in pair for c in m['orientations'][p['oi']]['cells']}
        m['required']=[{'pos':list(q)} for q in sorted(points)]
        window={'model':m,'fixed':pair};original={'model':m,'pair':pair}
        self.assertEqual(construct(window)[0].clauses,construct(original)[0].clauses)
        self.assertEqual(solve_window(window)['result'],'exhausted_finite')
        self.assertEqual(solve(original)['status'],'invalid')
    def test_unknown_and_invalid_inputs(self):
        self.assertEqual(solve_window(self.cube,max_rounds=0)['result'],'unknown')
        for change in [lambda d:d.update(pair=d['fixed']),lambda d:d.update(pairExclusions=[d['fixed']*2]),lambda d:d['model'].update(required=[]),lambda d:d['model']['orientations'][0].update(marks=[{'pos':[0,0,0],'value':1}]),lambda d:d['model']['orientations'][0]['cells'][0].update(weight=7)]:
            bad=copy.deepcopy(self.cube);change(bad)
            with self.assertRaises(ValueError):solve_window(bad)
    def test_resume_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory);(p/'input.json').write_text(json.dumps(self.cube))
            cmd=[sys.executable,str(ROOT/'scripts/solve_voxel_frontier_window.py'),'--input='+str(p/'input.json'),'--output='+str(p/'result.json')]
            subprocess.run(cmd,check=True,capture_output=True)
            result=json.loads((p/'result.json').read_text());self.assertEqual(result['stats']['problem'],'point-window')
            (p/'prior.json').write_text(json.dumps(result));subprocess.run(cmd+['--resume='+str(p/'prior.json')],check=True,capture_output=True)
            result['problemSha256']='wrong';(p/'prior.json').write_text(json.dumps(result))
            self.assertNotEqual(subprocess.run(cmd+['--resume='+str(p/'prior.json')],capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
