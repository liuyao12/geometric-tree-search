import {A2_SYMMETRIES, a2Add, a2Sub, a2Transform, a2InverseTransform} from '../../assets/a2-tiling-engine.js';

// All geometry and capacities are exact integers. Doubled or otherwise weighted
// points use the common denominator supplied as the capacity.
export const origin = [0n,0n,0n];
const order = (a,b) => a < b ? -1 : a > b ? 1 : 0;
export const pointOrder = (a,b) => order(a[0],b[0]) || order(a[1],b[1]);
export const plus = a2Add, minus = a2Sub;
function integer(value) {
  if (Number.isSafeInteger(value) || (typeof value === 'string' && /^-?\d+$/.test(value))) return BigInt(value);
  throw new TypeError('Use exact integers, encoded as strings for large coordinates or weights');
}
export function hex(center,radius) {
  const points = [];
  for (let x=-radius; x<=radius; x++) {
    for (let y=Math.max(-radius,-radius-x); y<=Math.min(radius,radius-x); y++) {
      points.push(plus(center,[BigInt(x),BigInt(y),BigInt(-x-y)]));
    }
  }
  return points;
}
export const markId = m => m.point+'|'+m.axis;
export const worldPoint = (p,q) => plus(minus(a2Transform(q,p.form.sym),p.form.anchor),p.shift);
export const localPoint = (p,q) => a2InverseTransform(plus(minus(q,p.shift),p.form.anchor),p.form.sym);
export function worldMark(p,m) {
  return {point:worldPoint(p,m.point),axis:p.form.sym.permutation.indexOf(m.axis),value:p.form.parity*m.value || 0};
}
export function tileModel(input) {
  const capacity = integer(input.capacity);
  if (capacity <= 0n || !Array.isArray(input.points)) throw new Error('Expected positive capacity and a points array');
  const seen = new Set(), sites = [];
  for (const row of input.points) {
    if (!Array.isArray(row) || row.length !== 3) throw new Error('Use [x,y,weight] rows');
    const [x,y,w] = row.map(integer), point = [x,y,-x-y];
    if (w < 0n || w > capacity || seen.has(String(point))) throw new Error('Duplicate point or weight outside the capacity');
    seen.add(String(point));
    if (w) sites.push({point,w});
  }
  if (!sites.length) throw new Error('A tile needs positive support');
  sites.sort((a,b)=>pointOrder(a.point,b.point));
  const anchor = sites[0].point;
  for (const row of sites) row.point = minus(row.point,anchor);
  const forms=[], signatures=new Map(), stabilizer=[];
  for (const symmetry of A2_SYMMETRIES) {
    const sym = {...symmetry,sign:BigInt(symmetry.sign)};
    const p = sym.permutation, parity = (Number(p[0]>p[1])+Number(p[0]>p[2])+Number(p[1]>p[2]))%2 ? -1 : 1;
    const rows = sites.map(({point,w})=>({point:a2Transform(point,sym),w})).sort((a,b)=>pointOrder(a.point,b.point));
    const anchor = rows[0].point;
    const normalized = rows.map(({point,w})=>({point:minus(point,anchor),w}));
    const signature = normalized.map(r=>r.point+'='+r.w).join(';');
    const form = {sym,parity,anchor,sites:normalized,index:signatures.get(signature) ?? forms.length};
    if (!signatures.has(signature)) { signatures.set(signature,form.index); forms.push(form); }
    if (form.index===0) stabilizer.push({form,shift:origin});
  }
  const cache = new Map();
  function pose(form,shift) {
    const id = form.index+'@'+shift;
    if (!cache.has(id)) {
      const rows = form.sites.map(r=>{
        const point=plus(r.point,shift);
        return {key:String(point),point,w:r.w};
      });
      cache.set(id,{id,form,shift,rows,keys:new Set(rows.map(r=>r.key))});
    }
    return cache.get(id);
  }
  function incident(point) {
    return forms.flatMap(f=>f.sites.map(row=>pose(f,minus(point,row.point))));
  }
  return {capacity,sites,forms,stabilizer,pose,incident,root:pose(forms[0],origin)};
}
