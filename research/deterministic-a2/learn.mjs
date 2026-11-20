import {hex,localPoint,markId,minus,origin,pointOrder,worldMark,worldPoint} from './model.mjs';
import {fill,rng} from './search.mjs';

// Every proof uses empty marking support. Memo entries are local to this tile
// model and proof budget. Only an exhausted proof authorizes a rejection.
export function learner(model,{extent,proofRadius,proofNodes,proposals}) {
  const support=new Map(), proved=new Map(), revisions=[];
  const band=new Map();
  for (let radius=0;radius<=extent;radius++) for (const site of model.sites) {
    for (const point of hex(site.point,radius)) {
      const key=String(point);
      if (!band.has(key)) band.set(key,{point,radius});
    }
  }
  let proofWork=0, attempted=0;
  function impossible(b) {
    if (b.id===model.root.id) return false;
    if (!proved.has(b.id)) {
      const required=[...model.root.rows,...b.rows].flatMap(r=>hex(r.point,proofRadius));
      const result=fill(model,required,[model.root,b],[],rng(1),proofNodes);
      proofWork+=result.nodes;
      proved.set(b.id,result.status==='exhausted');
    }
    return proved.get(b.id);
  }
  // Give the marking the same affine stabilizer as the underlying tile.
  // This also handles a reflection or rotation about a center away from zero.
  function orbit(a,b) {
    const extra=new Map();
    for (const m of [a,b]) for (const p of model.stabilizer) {
      const v=worldMark(p,m), k=markId(v), old=support.get(k)??extra.get(k);
      if (old && old.value!==v.value) return null;
      if (!old) extra.set(k,v);
    }
    return extra.size ? [...extra.values()] : null;
  }
  function certified(extra) {
    const all=[...support.values(),...extra];
    // Each ordered unequal overlap can be moved into the first tile's
    // canonical frame. Check both orders when one endpoint is newly assigned.
    for (const [left,right] of [[extra,all],[all,extra]]) {
      for (const form of model.forms) {
        const atOrigin={form,shift:origin};
        const rotated=right.map(m=>worldMark(atOrigin,m));
        for (const a of left) for (const b of rotated) {
          if (a.axis===b.axis && a.value!==b.value && !impossible(model.pose(form,minus(a.point,b.point)))) return false;
        }
      }
    }
    return true;
  }
  function consider(patch) {
    if (patch.length<2 || !proposals) return false;
    let tried=0;
    const candidates=new Set();
    for (let j=patch.length-1;j>=1;j--) for (let i=j-1;i>=0;i--) {
      const a=patch[i], b=patch[j];
      const overlaps=[];
      for (const {point:u,radius} of band.values()) {
        const q=worldPoint(a,u), v=localPoint(b,q), other=band.get(String(v));
        if (other) overlaps.push({u,v,q,radius:Math.max(radius,other.radius)});
      }
      overlaps.sort((x,y)=>x.radius-y.radius || pointOrder(x.u,y.u));
      for (const {u,v,q} of overlaps) {
        for (let axis=0;axis<3;axis++) for (const [left,right] of [[1,-1],[-1,1],[0,1],[1,0],[0,-1],[-1,0]]) {
          const m={point:u,axis:a.form.sym.permutation[axis],value:left*a.form.parity};
          const n={point:v,axis:b.form.sym.permutation[axis],value:right*b.form.parity};
          const extra=orbit(m,n);
          if (!extra) continue;
          const key=extra.map(r=>markId(r)+'='+r.value).sort().join(';');
          if (candidates.has(key)) continue;
          candidates.add(key);
          if (tried++>=proposals) return false;
          attempted++;
          if (!certified(extra)) continue;
          for (const e of extra) support.set(markId(e),e);
          revisions.push({branch:patch.map(p=>p.id),pair:[a.id,b.id],point:String(q),axis,
            values:[left,right],added:extra.map(e=>[String(e.point),e.axis,e.value])});
          return true;
        }
      }
    }
    return false;
  }
  return {support,revisions,consider,stats:()=>({proposalsTried:attempted,pairTests:proved.size,proofNodes:proofWork})};
}
