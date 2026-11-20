import {localPoint,markId,minus,plus,worldMark} from '../../research/deterministic-a2/model.mjs';

const siteKey=m=>m.tile+':'+markId(m);

// A certificate consists of excess weight, or one partially filled point
// with an empty unmarked domain. It is independent of the finite board.
export function pairObstruction(model,a,b) {
  const totals=new Map(a.rows.map(r=>[r.key,r.w]));
  for(const r of b.rows) {
    const total=(totals.get(r.key)??0n)+r.w;
    if(total>12n) return 'capacity';
    totals.set(r.key,total);
  }
  for(const r of [...a.rows,...b.rows]) {
    if(totals.get(r.key)===12n) continue;
    const canAdd=model.incident(r.point).some(p=>p.id!==a.id && p.id!==b.id &&
      p.rows.every(v=>(totals.get(v.key)??0n)+v.w<=12n));
    if(!canAdd) return 'dead point';
  }
  return null;
}

export function onlineMarks(model) {
  const table=new Map(),tested=new Map(),proposed=new Set();
  let revisions=0;
  function orbit(a,b) {
    const extra=new Map();
    for(const m of [a,b]) for(const symmetry of model.types.get(m.tile).stabilizer) {
      const v={tile:m.tile,...worldMark(symmetry,m)},key=siteKey(v);
      const old=table.get(key)??extra.get(key);
      if(old && old.value!==v.value) return [];
      if(!old) extra.set(key,v);
    }
    return [...extra.values()];
  }
  function certified(extra) {
    const all=[...table.values(),...extra];
    for(const [left,right] of [[extra,all],[all,extra]]) for(const a of left) {
      const root=model.types.get(a.tile).root;
      const fixed=worldMark(root,a);
      for(const b of right) {
        const type=model.types.get(b.tile);
        for(const form of type.forms) {
          const rotated=worldMark({form,shift:form.offset},b);
          if(rotated.axis!==fixed.axis || rotated.value===fixed.value) continue;
          const shift=plus(form.offset,minus(fixed.point,rotated.point));
          if(!model.allowed(form,shift)) continue;
          const other=type.pose(form,shift);
          if(other.id===root.id) continue;
          const key=root.id+'|'+other.id;
          if(!tested.has(key)) tested.set(key,pairObstruction(model,root,other));
          if(!tested.get(key)) return false;
        }
      }
    }
    return true;
  }
  function consider(patch) {
    let trials=0;
    // Propose on an actual overlapping site of an obstructed pair. Failed
    // higher-order patches can simply backtrack. Unassigned axes are wildcards.
    for(let j=patch.length-1;j>0;j--) for(let i=j-1;i>=0;i--) {
      const a=patch[i],b=patch[j];
      const common=b.rows.filter(r=>a.keys.has(r.key));
      if(!common.length || !pairObstruction(model,a,b)) continue;
      for(const {point:q} of common) for(let axis=0;axis<3;axis++) {
        const local=(p,sign)=>({tile:p.tile,point:localPoint(p,q),
          axis:p.form.sym.permutation[axis],value:sign*p.form.parity});
        for(const sign of [1,-1]) {
          const extra=orbit(local(a,sign),local(b,-sign));
          if(!extra.length) continue;
          const key=extra.map(m=>siteKey(m)+'='+m.value).sort().join(';');
          if(proposed.has(key)) continue;
          proposed.add(key);
          if(certified(extra)) {
            for(const m of extra) table.set(siteKey(m),m);
            revisions++;
            return true;
          }
          if(++trials>=16) return false;
        }
      }
    }
    return false;
  }
  return {table,consider,stats:()=>({revisions,assignments:table.size,tests:tested.size})};
}
