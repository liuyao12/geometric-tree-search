#!/usr/bin/env python3
"""Check the proof-derived relative pairs against the independent point action."""
import argparse,json,os,shutil,subprocess
from pathlib import Path
from solve_patch_period_quotients import certificate_templates
p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--checker',type=Path,required=True);a=p.parse_args()
data=json.loads((a.bundle/'pair.input.json').read_text());orientations=[o['voxels'] for o in data['model']['orientations']]
templates,receipt=certificate_templates(a.bundle,a.checker,orientations)
root=Path(__file__).resolve().parents[1]
module=(root/'apps/3d-lattice-tiler/marking-learning.js').as_uri()
node=os.environ.get('GCTS_NODE_BINARY') or shutil.which('node');assert node,'Set GCTS_NODE_BINARY'
js=f"""import {{pointSymmetries}} from {json.dumps(module)};
let raw='';for await(const x of process.stdin)raw+=x;const {{model,pair}}=JSON.parse(raw),seen=new Set();
for(const g of pointSymmetries(model)){{
 const transformed=pair.map(p=>({{oi:g.map[p.oi].oi,t:g.transform(p.translation).map((x,i)=>x+g.map[p.oi].shift[i])}}));
 for(const [a,b] of [transformed,[...transformed].reverse()]){{const delta=b.t.map((x,i)=>(x-a.t[i])/2);if(delta.some(x=>!Number.isInteger(x)))throw Error('Non-grid translation');seen.add(JSON.stringify([a.oi,b.oi,delta]));}}
}}
console.log(JSON.stringify([...seen].map(x=>JSON.parse(x))));"""
r=subprocess.run([node,'--input-type=module','-e',js],input=json.dumps(data),text=True,capture_output=True)
assert r.returncode==0,r.stderr
actual={(a,b,tuple(delta)) for a,b,delta in json.loads(r.stdout)}
assert set(templates)==actual
assert len(templates)==receipt['geometry']['relativePairSchemas']
print(json.dumps({'verified':True,'schemas':len(templates),'method':'RUP proof replay plus independent JS point-symmetry transport','manifestSha256':receipt['manifestSha256']}))
