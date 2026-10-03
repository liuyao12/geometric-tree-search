// Published construction controls, not GCTS search or learned matching rules.
// Multigrid duality: de Bruijn / Lutfalla. A_n section: Egan's technical notes.
// Integer cyclotomic vertex addresses are exact. Selecting a section uses doubles.
import { P1_EXACT_TILES, P1_EXACT_VERTICES } from '../../assets/penrose-p1-patch.js';

const TAU = 2 * Math.PI;
const dot = (a,b) => a[0]*b[0]+a[1]*b[1];
const add = (a,b) => a.map((v,i)=>v+b[i]);
const sub = (a,b) => a.map((v,i)=>v-b[i]);
export const area = points => points.reduce((s,p,i)=>{const q=points[(i+1)%points.length];return s+p[0]*q[1]-p[1]*q[0];},0)/2;
const polynomialCache = new Map();
export function cyclotomic(n) {
  if(polynomialCache.has(n)) return polynomialCache.get(n);
  let p=Array(n+1).fill(0); p[0]=-1;p[n]=1;
  for(let d=1;d<n;d++) if(n%d===0) {
    const q=cyclotomic(d), result=Array(p.length-q.length+1).fill(0),rem=[...p];
    for(let i=rem.length-q.length;i>=0;i--){const v=rem[i+q.length-1];result[i]=v;for(let j=0;j<q.length;j++)rem[i+j]-=v*q[j];}
    if(rem.some(Boolean))throw Error('Nonintegral cyclotomic division');p=result;
  }
  polynomialCache.set(n,p);return p;
}
export function ring(n) {
  const poly=cyclotomic(n),degree=poly.length-1;
  const reduce=c=>{const a=[...c];while(a.length<degree)a.push(0);for(let i=a.length-1;i>=degree;i--){const v=a[i];for(let j=0;j<degree;j++)a[i-degree+j]-=v*poly[j];}return a.slice(0,degree);};
  const unit=k=>{const c=Array(n).fill(0);c[((k%n)+n)%n]=1;return reduce(c);};
  const embed=(c,power=1)=>c.reduce((p,v,i)=>[p[0]+v*Math.cos(TAU*i*power/n),p[1]+v*Math.sin(TAU*i*power/n)],[0,0]);
  return {n,degree,reduce,unit,embed};
}

function directions(m) {
  const n=m%2?m:2*m,r=ring(n),units=Array.from({length:m},(_,i)=>r.unit(i));
  return {r,units,e:units.map(c=>r.embed(c))};
}
// Offsets have no physical translation component. Odd stars also have zero sum;
// in the pentagrid this preserves the ordinary Penrose class (integer phase sum).
export function offsets(e,phase=0) {
  const m=e.length;
  let a=e.map((_,i)=>.19*Math.sin((i+1)*1.731)+.13*Math.cos((i+1)*(i+2)*.713)+phase*.8*Math.cos(TAU*2*i/m+.37));
  if(m%2){const mean=a.reduce((s,x)=>s+x,0)/m;a=a.map(x=>x-mean);}
  const physical=e.reduce((p,v,i)=>[p[0]+a[i]*v[0]*2/m,p[1]+a[i]*v[1]*2/m],[0,0]);
  return a.map((x,i)=>x-dot(e[i],physical));
}
function record(coords,r,kind,extra={}) {
  let points=coords.map(c=>r.embed(c));
  if(area(points)<0){coords=[...coords].reverse();points.reverse();}
  const center=points.reduce((p,q)=>[p[0]+q[0]/points.length,p[1]+q[1]/points.length],[0,0]);
  const keys=coords.map(c=>c.join(','));
  return {id:keys.slice().sort().join('|'),coords,points,keys,kind,center,...extra};
}
function ordered(tiles){return tiles.sort((a,b)=>dot(a.center,a.center)-dot(b.center,b.center)||a.id.localeCompare(b.id));}

export function multigrid({m=5,radius=12,phase=0}={}) {
  const {r,units,e}=directions(m),gamma=offsets(e,phase),tiles=[],duals=[];
  // Projection of floors differs from (m/2)q by at most m. This range encloses
  // every grid intersection whose dual center can lie in the requested disc.
  const extent=2*radius/m+3,range=Math.ceil(extent+1);
  let margin=Infinity;
  for(let i=0;i<m;i++)for(let j=i+1;j<m;j++) {
    const det=e[i][0]*e[j][1]-e[i][1]*e[j][0];
    for(let a=-range;a<=range;a++)for(let b=-range;b<=range;b++){
      const ai=a-gamma[i],bj=b-gamma[j];
      const q=[(ai*e[j][1]-bj*e[i][1])/det,(e[i][0]*bj-e[j][0]*ai)/det];
      if(dot(q,q)>extent*extent)continue;
      const values=e.map((v,k)=>dot(v,q)+gamma[k]);
      const base=values.map((v,k)=>k===i?a-1:k===j?b-1:Math.floor(v));
      let origin=Array(r.degree).fill(0);
      base.forEach((v,k)=>{origin=add(origin,units[k].map(x=>x*v));});
      const coords=[origin,add(origin,units[i]),add(add(origin,units[i]),units[j]),add(origin,units[j])];
      const angle=Math.acos(Math.min(1,Math.abs(dot(e[i],e[j]))));
      const k=Math.round(angle*m/Math.PI);
      const tile=record(coords,r,`rhomb-${k}`,{angle:k,families:[i,j],lift:base,sourceCoords:coords,dual:q});
      if(dot(tile.center,tile.center)>radius*radius)continue;
      for(let k=0;k<m;k++)if(k!==i&&k!==j)margin=Math.min(margin,Math.abs(values[k]-Math.round(values[k])));
      tiles.push(tile);duals.push(q);
    }
  }
  // Never silently skip a triple crossing: callers can retain the last regular
  // patch when animation lands at a numerically ambiguous phason value.
  if(margin<1e-9)throw Error('This section is at a tile flip. Move the phase slightly.');
  return {tiles:ordered(tiles),r,m,e,gamma,duals,radius,margin,construction:'multigrid'};
}

export function robinson(model) {
  const tiles=[];
  for(const t of model.tiles){
    // Long diagonal of the thick rhomb; short diagonal of the thin rhomb.
    const c=t.sourceCoords,diag=dot(sub(t.points[0],t.points[2]),sub(t.points[0],t.points[2]));
    const thick=t.angle===2,use02=thick?diag>2:diag<2;
    const parts=use02?[[0,1,2],[0,2,3]]:[[1,2,3],[1,3,0]];
    for(const indices of parts)tiles.push(record(indices.map(i=>t.coords[i]),model.r,thick?'acute':'obtuse',{parent:t.id}));
  }
  return {...model,tiles:ordered(tiles),sourceTiles:model.tiles,construction:'local subdivision'};
}

export function kiteDart(model) {
  const vertices=new Map(),adj=new Map();
  function edge(a,b){const ka=a.join(','),kb=b.join(',');vertices.set(ka,a);vertices.set(kb,b);for(const[x,y]of[[ka,kb],[kb,ka]]){if(!adj.has(x))adj.set(x,new Set());adj.get(x).add(y);}}
  const markings=penroseArrows(model);
  for(const t of model.tiles){const c=t.coords;
    if(t.angle===2){const d=sub(t.points[0],t.points[2]);if(dot(d,d)>2)edge(c[0],c[2]);else edge(c[1],c[3]);}
    else for(const a of markings.get(t.id))if(a.type===2)edge(c[a.from],c[a.to]);
  }
  const pos=new Map([...vertices].map(([k,c])=>[k,model.r.embed(c)]));
  const angle=(a,b)=>Math.atan2(pos.get(b)[1]-pos.get(a)[1],pos.get(b)[0]-pos.get(a)[0]);
  for(const[k,v]of adj)adj.set(k,[...v].sort((a,b)=>angle(k,a)-angle(k,b)));
  const visited=new Set(),tiles=[];
  for(const[a,neighbors]of adj)for(const b of neighbors){
    if(visited.has(a+'>'+b))continue;
    let x=a,y=b,ids=[],closed=false;
    for(let step=0;step<500;step++){
      const key=x+'>'+y;if(visited.has(key)){closed=x===a&&y===b;break;}
      visited.add(key);ids.push(x);const at=adj.get(y),z=at[(at.indexOf(x)+at.length-1)%at.length];x=y;y=z;
    }
    const points=ids.map(k=>pos.get(k));if(!closed||ids.length!==4||area(points)<=1e-8)continue;
    const concave=points.some((p,i)=>{const u=sub(points[(i+1)%4],p),v=sub(points[(i+2)%4],points[(i+1)%4]);return u[0]*v[1]-u[1]*v[0]<-1e-8;});
    tiles.push(record(ids.map(k=>vertices.get(k)),model.r,concave?'dart':'kite'));
  }
  return {...model,tiles:ordered(tiles),sourceTiles:model.tiles,construction:'local recutting'};
}

// Standard two rigid arrow orientations per rhomb, solved against every shared
// edge. This decorates an already constructed patch; it is not a GCTS tiler.
export function penroseArrows(model) {
  const options=model.tiles.map(t=>{
    const acute=t.points.flatMap((p,i)=>{const a=sub(t.points[(i+1)%4],p),b=sub(t.points[(i+3)%4],p);return dot(a,b)>0?[i]:[];});
    const template=t.angle===2?[[1,1],[2,1],[2,-1],[1,-1]]:[[1,1],[1,-1],[2,1],[2,-1]];
    return acute.map(start=>template.map(([type,sign],i)=>{const a=(start+i)%4,b=(a+1)%4,from=sign>0?a:b,to=sign>0?b:a;return {type,from,to,edge:[t.keys[a],t.keys[b]].sort().join('|'),signature:type+':'+t.keys[from]+'>'+t.keys[to]};}));
  });
  const edges=new Map(),neighbors=model.tiles.map(()=>[]);
  options.forEach((s,i)=>s[0].forEach(a=>{if(!edges.has(a.edge))edges.set(a.edge,[]);edges.get(a.edge).push(i);}));
  for(const [edge,owners] of edges)if(owners.length===2){const[i,j]=owners,mask=[0,0],reverse=[0,0];
    for(let a=0;a<2;a++)for(let b=0;b<2;b++)if(options[i][a].find(v=>v.edge===edge).signature===options[j][b].find(v=>v.edge===edge).signature){mask[a]|=1<<b;reverse[b]|=1<<a;}
    neighbors[i].push([j,mask]);neighbors[j].push([i,reverse]);
  }
  const solve=d=>{const q=d.map((_,i)=>i);for(let h=0;h<q.length;h++){const i=q[h];for(const[j,m]of neighbors[i]){const allowed=((d[i]&1)?m[0]:0)|((d[i]&2)?m[1]:0),next=d[j]&allowed;if(!next)return null;if(next!==d[j]){d[j]=next;q.push(j);}}}
    const i=d.indexOf(3);if(i<0)return d;for(const v of [1,2]){const next=[...d];next[i]=v;const answer=solve(next);if(answer)return answer;}return null;};
  const d=solve(model.tiles.map(()=>3));if(!d)throw Error('Penrose arrow validation failed');
  return new Map(model.tiles.map((t,i)=>[t.id,options[i][d[i]===1?0:1]]));
}

// Sections of A_(m-1) Voronoi cells, dual to triangular Delaunay faces.
// For x with sum x_i=0, nearest lattice points result from flooring x and
// rounding up the largest -sum(floor(x_i)) fractional parts. Triple ties
// straddling this cutoff give exactly the three vertices of a triangle.
export function rootTriangles({m=5,radius=12,phase=0}={}) {
  if(m%2===0)throw Error('Root-lattice gallery requires odd m');
  const {r,e,units}=directions(m),gamma=offsets(e,phase),tiles=[],seen=new Set();
  const extent=2*radius/m+3,range=Math.ceil(2*extent+2);let margin=Infinity;
  for(let i=0;i<m;i++)for(let j=i+1;j<m;j++)for(let k=j+1;k<m;k++){
    const u=sub(e[i],e[j]),v=sub(e[i],e[k]),det=u[0]*v[1]-u[1]*v[0];
    for(let a=-range;a<=range;a++)for(let b=-range;b<=range;b++){
      const ai=a-gamma[i]+gamma[j],bj=b-gamma[i]+gamma[k];
      const q=[(ai*v[1]-bj*u[1])/det,(u[0]*bj-v[0]*ai)/det];
      if(dot(q,q)>extent*extent)continue;
      const x=e.map((w,l)=>dot(w,q)+gamma[l]);
      const base=x.map(Math.floor);base[j]=base[i]-a;base[k]=base[i]-b;
      const fraction=x[i]-base[i],others=Array.from({length:m},(_,l)=>l).filter(l=>l!==i&&l!==j&&l!==k);
      const above=others.filter(l=>x[l]-base[l]>fraction);
      const needed=-base.reduce((s,t)=>s+t,0)-above.length;
      if(needed!==1&&needed!==2)continue;
      above.forEach(l=>base[l]++);
      const lifts=[i,j,k].map(t=>base.map((v,l)=>v+([i,j,k].includes(l)&&(needed===1?l===t:l!==t)?1:0)));
      const coords=lifts.map(c=>c.reduce((p,v,l)=>add(p,units[l].map(w=>w*v)),Array(r.degree).fill(0)));
      const tile=record(coords,r,'triangle',{dual:q,lifts});
      if(dot(tile.center,tile.center)>radius*radius||seen.has(tile.id))continue;
      for(const l of others)margin=Math.min(margin,Math.abs((x[l]-Math.floor(x[l]))-fraction));
      const angles=tile.points.map((p,l)=>{const u=sub(tile.points[(l+1)%3],p),v=sub(tile.points[(l+2)%3],p);return Math.round(Math.acos(dot(u,v)/Math.sqrt(dot(u,u)*dot(v,v)))*m/Math.PI);}).sort((a,b)=>a-b);
      tile.kind='triangle-'+angles.join('-');tile.angles=angles;seen.add(tile.id);tiles.push(tile);
    }
  }
  if(margin<1e-9)throw Error('This section is at a tile flip. Move the phase slightly.');
  return {tiles:ordered(tiles),r,m,e,gamma,radius,margin,construction:'root-lattice section'};
}

export function pentagonalReference() {
  const r=ring(5),vertices=P1_EXACT_VERTICES.map(c=>r.reduce(c));
  return {r,m:5,radius:14,construction:'finite reference',tiles:ordered(P1_EXACT_TILES.map(([kind,indices])=>record(indices.map(i=>vertices[i]),r,kind)))};
}

export function buildAtlas(id,{radius=12,phase=0}={}) {
  if(id==='p1')return pentagonalReference();
  if(id==='ttt'||id==='tri7')return rootTriangles({m:id==='ttt'?5:7,radius,phase});
  const m=({ab:4,seven:7,twelve:6,eleven:11})[id]||5;
  const model=multigrid({m,radius,phase});
  if(id==='p2')return kiteDart(model);
  if(id==='robinson')return robinson(model);
  return model;
}

export function inspectPatch(model) {
  const edges=new Map(),ids=new Set();let unitError=0,duplicates=0,minArea=Infinity;
  for(const t of model.tiles){if(ids.has(t.id))duplicates++;ids.add(t.id);minArea=Math.min(minArea,area(t.points));
    t.keys.forEach((v,i)=>{const key=[v,t.keys[(i+1)%t.keys.length]].sort().join('|');edges.set(key,(edges.get(key)||0)+1);
      if(model.construction==='multigrid'){const d=sub(t.points[i],t.points[(i+1)%t.points.length]);unitError=Math.max(unitError,Math.abs(dot(d,d)-1));}});
  }
  return {duplicates,minArea,unitError,nonmanifold:[...edges.values()].filter(n=>n>2).length,boundary:[...edges.values()].filter(n=>n===1).length,edges:edges.size};
}
