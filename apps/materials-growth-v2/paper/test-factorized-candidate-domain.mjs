import assert from 'node:assert/strict';
import {FactorizedCandidateDomain,factorizedDecision} from './factorized-candidate-domain.mjs';
import {linearFrontierClass} from './linear-frontier-decision.mjs';
const Reference=linearFrontierClass(class{});
let seed=731891,states=0,candidatesChecked=0,schedulerChecks=0;
const random=n=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed%n;};
function explicit(m){
  const out=[];
  for(let a=0;a<m.sizes[0];a++)for(let b=0;b<m.sizes[1];b++)
    if(m.enabled&&(m.allowed[0]===null||m.allowed[0].includes(a))&&(m.allowed[1]===null||m.allowed[1].includes(b))&&!m.exclusions.some(([x,y])=>x===a&&y===b))out.push([a,b]);
  return out;
}
for(let trial=0;trial<200;trial++){
  const domains=Array.from({length:3},()=>new FactorizedCandidateDomain(1+random(6),1+random(6)));
  const models=domains.map(d=>({sizes:[...d.sizes],enabled:true,allowed:[null,null],exclusions:[]}));
  const checkpoints=[];
  const audit=()=>{
    const lists=models.map(explicit);
    for(let i=0;i<domains.length;i++){
      const d=domains[i],expected=lists[i];
      assert.deepEqual([...d.values()],expected);assert.equal(d.count,BigInt(expected.length));
      assert.deepEqual(d.first(),expected[0]??null);assert.deepEqual(d.sole(),expected.length===1?expected[0]:null);
      for(let a=0;a<models[i].sizes[0];a++)for(let b=0;b<models[i].sizes[1];b++){
        assert.equal(d.has(a,b),expected.some(([x,y])=>x===a&&y===b));candidatesChecked++;
      }
    }
    const points=Array.from({length:1+random(5)},(_,i)=>({id:`p${i}`,generation:random(5),complete:random(5)!==0,indices:[0,1,2].filter(()=>random(2))}));
    const graph=new Map(),referencePoints=new Map(),candidates=new Map();
    for(const p of points){
      referencePoints.set(p.id,p);const cs=new Map();
      for(const index of p.indices)for(const pair of lists[index]){const id=JSON.stringify([index,...pair]);cs.set(id,1);candidates.set(id,{id});}
      graph.set(p.id,cs);
    }
    const expected=Reference.prototype.decision.call({points:referencePoints,graph,candidates,preference:()=>0});
    const actual=factorizedDecision(points.map(p=>({...p,blocks:p.indices.map(i=>domains[i])})));
    assert.equal(actual.kind,expected.kind);assert.equal(actual.point,expected.point);
    if(actual.kind==='branch')assert.equal(actual.provisional,expected.provisional);
    states++;schedulerChecks++;
  };
  for(let step=0;step<100;step++){
    const index=random(3),d=domains[index],m=models[index],action=random(5);
    if(action===0){const value=Boolean(random(2));d.setEnabled(value);m.enabled=value;}
    if(action===1){const side=random(2),allowed=random(4)?Array.from({length:m.sizes[side]},(_,i)=>i).filter(()=>random(2)):null;d.setAllowed(side,allowed);m.allowed[side]=allowed;}
    if(action===2){const a=random(m.sizes[0]),b=random(m.sizes[1]);d.forbid(a,b);if(!m.exclusions.some(([x,y])=>x===a&&y===b))m.exclusions.push([a,b]);}
    if(action===3)checkpoints.push({marks:domains.map(d=>d.checkpoint()),models:structuredClone(models),snapshots:domains.map(d=>d.snapshot())});
    if(action===4&&checkpoints.length){const old=checkpoints.pop();for(let i=0;i<3;i++){domains[i].undo(old.marks[i]);models[i]=old.models[i];assert.deepEqual(domains[i].snapshot(),old.snapshots[i]);}}
    audit();
  }
}
// A shared geometric block with six markings is six choices, never one forced move.
const block=new FactorizedCandidateDomain(2,3),root=block.checkpoint();
assert.equal(factorizedDecision([{id:'p',generation:0,complete:true,blocks:[block]}]).kind,'branch');
block.setAllowed(0,[1]);block.setAllowed(1,[2]);assert.deepEqual(block.sole(),[1,2]);
assert.equal(factorizedDecision([{id:'p',generation:0,complete:true,blocks:[block]}]).kind,'forced');
block.forbid(1,2);assert.equal(block.count,0n);block.undo(root);assert.equal(block.count,6n);
// Cardinality beyond Number's exact range is retained, without product allocation.
const huge=new FactorizedCandidateDomain(2**30,2**30);assert.equal(huge.count,2n**60n);
huge.forbid(0,0);assert.equal(huge.count,2n**60n-1n);assert.deepEqual(huge.first(),[0,1]);
const full=new FactorizedCandidateDomain(2**30,2**30);
assert.equal(factorizedDecision([{id:'a',generation:0,complete:true,blocks:[full]},{id:'b',generation:0,complete:true,blocks:[huge]}]).point,'b');
const empty=new FactorizedCandidateDomain(2**40,0);assert.equal(empty.first(),null);
assert.throws(()=>block.setAllowed(0,[2]));assert.throws(()=>block.forbid(-1,0));assert.throws(()=>block.undo(-1));
assert.throws(()=>factorizedDecision([{id:'p',generation:0,complete:true,blocks:[block,block]}]));
console.log(JSON.stringify({models:200,states,candidatesChecked,schedulerChecks,exactBigIntCounts:true,rollback:true,falseForcedMoveRegression:true,
  limits:'Domain storage and supplied-graph scheduling only; not material integration, geometric validity, cloud intersections, inventory enforcement or complete tree search.'}));
