import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {hex,markId,origin,minus,tileModel,worldMark} from './model.mjs';
import {fill,rng} from './search.mjs';
import {readTile} from './run.mjs';

// Replay an exported table independently of the proposal history.
export function verify(input,result) {
  const model=tileModel(input), marks=[], seen=new Map();
  function vector(str) {
    const p=str.split(',').map(BigInt);
    assert.equal(p.length,3); assert.equal(p[0]+p[1]+p[2],0n);
    return p;
  }
  for (const [point,axis,value] of result.marking) {
    assert.ok([0,1,2].includes(axis) && [-1,0,1].includes(value));
    const m={point:vector(point),axis,value};
    assert.ok(!seen.has(markId(m))); seen.set(markId(m),value); marks.push(m);
  }
  for (const h of model.stabilizer) for (const m of marks) {
    const image=worldMark(h,m);
    assert.equal(seen.get(markId(image)),image.value,'marking breaks a symmetry of the prototile');
  }
  const conflicts=new Map();
  for (const form of model.forms) for (const n of marks) {
    const image=worldMark({form,shift:origin},n);
    for (const m of marks) if (m.axis===image.axis && m.value!==image.value) {
      const b=model.pose(form,minus(m.point,image.point));
      assert.notEqual(b.id,model.root.id,'conflict within one placement');
      conflicts.set(b.id,b);
    }
  }
  for (const b of conflicts.values()) {
    const targets=[...model.root.rows,...b.rows].flatMap(r=>hex(r.point,result.config.proofRadius));
    const pair=fill(model,targets,[model.root,b],[],rng(1),result.config.proofNodes);
    assert.equal(pair.status,'exhausted','unproved exclusion '+b.id);
  }
  if (result.status==='covered') {
    const used=new Set(), sums=new Map(), assigned=new Map();
    for (const id of result.placements) {
      const [index,shift]=id.split('@'), p=model.pose(model.forms[Number(index)],vector(shift));
      assert.ok(!used.has(p.id)); used.add(p.id);
      for (const r of p.rows) {
        const total=(sums.get(r.key)??0n)+r.w;
        assert.ok(total<=model.capacity); sums.set(r.key,total);
      }
      for (const m of marks) {
        const v=worldMark(p,m), k=markId(v);
        if (assigned.has(k)) assert.equal(assigned.get(k),v.value);
        assigned.set(k,v.value);
      }
    }
    assert.ok(used.has(model.root.id));
    for (const q of hex(origin,result.config.radius)) assert.equal(sums.get(String(q)),model.capacity);
  }
  return conflicts.size;
}
if (process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  const [source,file]=process.argv.slice(2);
  if (!file) throw new Error('Usage: node verify.mjs tile.json|hat|turtle|hexagon results.jsonl');
  const input=readTile(source);
  for (const line of readFileSync(file,'utf8').trim().split('\n')) {
    const r=JSON.parse(line);
    console.log(JSON.stringify({radius:r.config.radius,status:r.status,verifiedRelativeExclusions:verify(input,r)}));
  }
}
