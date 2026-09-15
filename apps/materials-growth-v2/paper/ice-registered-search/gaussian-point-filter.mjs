// Gaussian Hilbert-ball markings on a declared finite point model.
// At most two selected assignments per marking point must be certified by
// inventory or integer t-capacity. No physical potential is evaluated.
import assert from 'node:assert/strict';
export function gaussianDistanceSquared(a,b){
  assert.equal(a.sigma,b.sigma);
  const inner=(u,v)=>{let sum=0;for(let i=0;i<u.vectors.length;i++)for(let j=0;j<v.vectors.length;j++)if(u.colors[i]===v.colors[j]){
    let d=0;for(let k=0;k<3;k++)d+=(u.vectors[i][k]-v.vectors[j][k])**2;
    sum+=u.amplitudes[i]*v.amplitudes[j]*Math.exp(-d/(2*u.sigma**2));
  }return sum;};
  return (a.norm??inner(a,a))+(b.norm??inner(b,b))-2*inner(a,b);
}
export function gaussianPointClass(Base,model,{enabled=true}={}){
  const pool=model.fields,cache=new Map(),inventories=new Map(),at=new Map();
  assert(!model.expand&&model.complete!==false,'Static finite candidate model required');
  assert(Number.isFinite(model.radius)&&model.radius>=0);
  for(const f of pool){assert(f.sigma>0&&Number.isFinite(f.sigma));assert(f.vectors.length===f.colors.length&&f.colors.length===f.amplitudes.length);assert(f.vectors.every(v=>v.length===3&&v.every(Number.isFinite)));assert(f.amplitudes.every(x=>Number.isFinite(x)&&x>=0));}
  for(const c of model.candidates){
    assert(typeof c.base==='string');assert.equal(new Set(c.fieldM.map(m=>m.point)).size,c.fieldM.length,'Duplicate marking point in one candidate');
    for(const m of c.fieldM){assert(pool[m.field]);if(!inventories.has(m.point)){inventories.set(m.point,new Set());at.set(m.point,[]);}inventories.get(m.point).add(c.base);at.get(m.point).push(c);}
  }
  const certificates=[];
  for(const [point,owners] of inventories){
    if(owners.size<=2){certificates.push({point,kind:'inventory',maximum:owners.size});continue;}
    const candidates=at.get(point);
    const support=candidates[0].t.find(t=>Number.isSafeInteger(t.value)&&t.value>0&&3*t.value>model.capacity&&candidates.every(c=>c.t.some(u=>u.point===t.point&&Number.isSafeInteger(u.value)&&u.value>0&&3*u.value>model.capacity)));
    assert(support,'No two-assignment inventory or t-capacity certificate');
    certificates.push({point,kind:'integer-capacity',supportPoint:support.point,capacity:model.capacity,minimumContribution:Math.min(...candidates.map(c=>c.t.find(t=>t.point===support.point).value)),maximum:2});
  }
  const stats={pairChecks:0,cacheHits:0};
  function compatible(i,j){
    stats.pairChecks++;if(i===j)return true;
    const key=i<j?`${i}:${j}`:`${j}:${i}`;if(cache.has(key)){stats.cacheHits++;return cache.get(key);}
    const a=pool[i],b=pool[j],sq=gaussianDistanceSquared(a,b),mass=[...a.amplitudes,...b.amplitudes].reduce((x,y)=>x+y,0);
    const guard=1024*Number.EPSILON*Math.max(1,mass**2);assert(sq>=-guard);
    // Uncertain comparisons are retained. Completion reports unknown.
    const value=sq-guard>(2*model.radius)**2?false:sq+guard<=(2*model.radius)**2?true:null;
    cache.set(key,value);return value;
  }
  return class GaussianPointSearch extends Base{
    addCandidate(c){super.addCandidate(c);for(const m of c.fieldM){this.ensure(m.point);if(!this.dependencies.has(m.point))this.dependencies.set(m.point,new Set());this.dependencies.get(m.point).add(c.id);}}
    reason(c){const why=super.reason(c);if(why)return why;if(this.fieldOwners?.has(c.base))return 'inventory';
      if(enabled)for(const m of c.fieldM)for(const a of this.fieldAssignments?.get(m.point)||[])if(compatible(m.field,a)===false)return 'gaussian-field';return null;}
    refresh(){this.fieldOwners=new Set();this.fieldAssignments=new Map();for(const id of this.placed.keys()){
      const c=this.candidates.get(id);assert(!this.fieldOwners.has(c.base));this.fieldOwners.add(c.base);
      for(const m of c.fieldM){if(!this.fieldAssignments.has(m.point))this.fieldAssignments.set(m.point,[]);this.fieldAssignments.get(m.point).push(m.field);}
    }this.fieldStats=stats;this.fieldArityCertificates=certificates;super.refresh(new Set(this.points.keys()));}
    decision(){const d=super.decision();if(d.kind==='complete'&&enabled)for(const values of this.fieldAssignments.values()){
      assert(values.length<=2);if(values.length===2&&compatible(...values)!==true)return {kind:'unknown',reason:'numerically unresolved common field'};
    }return d;}
  };
}
