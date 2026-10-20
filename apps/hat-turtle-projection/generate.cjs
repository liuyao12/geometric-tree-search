/* Rebuild the fixed lifted patch from Craig S. Kaplan's BSD-licensed hatviz. */
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = __dirname;
const context = vm.createContext({cos:Math.cos,sin:Math.sin,PI:Math.PI});
const source = fs.readFileSync(path.join(root,'geometry-reference.js'),'utf8')+'\n'+fs.readFileSync(path.join(root,'hat-reference.js'),'utf8');
vm.runInContext(source+`\nlet current=[H_init,T_init,P_init,F_init];
for(let i=0;i<4;i++) current=constructMetatiles(constructPatch(...current));
const leaves=[];
function collect(g,T){if(g instanceof HatTile){leaves.push({label:g.label,points:hat_outline.map(p=>transPt(T,p))});return;}for(const child of g.children)collect(child.geom,mul(T,child.T));}
collect(current[0],ident);globalThis.result=leaves;`,context);
const leaves=context.result;
const points=[],edges=[],tiles=[],labels=[],lookup=new Map(),incidence=new Map();
const key=p=>`${Math.round(p.x*1e6)},${Math.round(p.y*1e6)}`;
function vertex(p){const k=key(p);if(!lookup.has(k)){lookup.set(k,points.length);points.push([p.x,p.y]);edges.push([]);}return lookup.get(k);}
function displacement(p,q){const dx=q.x-p.x,dy=q.y-p.y,L=Math.hypot(dx,dy);let result;
 if(Math.abs(L-.5)<1e-6){const b=dy/(Math.sqrt(3)/4),a=dx/.5-b/2;result=[a,b,0,0];}
 else if(Math.abs(L-Math.sqrt(3)/2)<1e-6){const c=dx/.75,d=dy/(Math.sqrt(3)/2)-c/2;result=[0,0,c,d];}
 else throw Error('Unexpected edge length '+L);
 const rounded=result.map(Math.round);if(result.some((x,i)=>Math.abs(x-rounded[i])>1e-5))throw Error('Noninteger lift');return rounded;
}
for(const leaf of leaves){const poly=[];
 for(let i=0;i<leaf.points.length;i++){const p=leaf.points[i],q=leaf.points[(i+1)%leaf.points.length];poly.push(p);if(Math.abs(Math.hypot(q.x-p.x,q.y-p.y)-1)<1e-6)poly.push({x:(p.x+q.x)/2,y:(p.y+q.y)/2});}
 if(poly.length!==14)throw Error('Expected fourteen vertices');
 const ids=poly.map(vertex);tiles.push(ids);labels.push(leaf.label);
 for(let i=0;i<14;i++){const j=(i+1)%14,a=ids[i],b=ids[j],delta=displacement(poly[i],poly[j]);edges[a].push({to:b,delta});edges[b].push({to:a,delta:delta.map(v=>-v)});const k=a<b?`${a},${b}`:`${b},${a}`;incidence.set(k,(incidence.get(k)||0)+1);}
}
const lift=Array(points.length).fill(null);lift[0]=[0,0,0,0];const queue=[0];
for(let h=0;h<queue.length;h++){const a=queue[h];for(const e of edges[a]){const next=lift[a].map((x,i)=>x+e.delta[i]);if(lift[e.to]===null){lift[e.to]=next;queue.push(e.to);}else if(next.some((x,i)=>x!==lift[e.to][i]))throw Error('Inconsistent shared-edge lift');}}
if(queue.length!==points.length)throw Error('Disconnected patch');
if([...incidence.values()].some(n=>n>2))throw Error('Nonmanifold edge');
// Check the original hat reconstruction and every tile's two edge counts.
let error=0;const x0=points[0][0],y0=points[0][1];
for(let i=0;i<lift.length;i++){const [p,q,r,s]=lift[i];const x=.5*(p+q/2)+Math.sqrt(3)/2*(Math.sqrt(3)/2*r);const y=.5*Math.sqrt(3)/2*q+Math.sqrt(3)/2*(r/2+s);error=Math.max(error,Math.hypot(x-(points[i][0]-x0),y-(points[i][1]-y0)));}
if(error>1e-6)throw Error('Projection does not reproduce hat patch: '+error);
for(const ids of tiles){let a=0,b=0;for(let i=0;i<14;i++){const d=lift[ids[(i+1)%14]].map((v,j)=>v-lift[ids[i]][j]);if(d[0]||d[1])a++;else b++;}if(a!==8||b!==6)throw Error('Unexpected tile edge classes');}
const metadata={tiles:tiles.length,vertices:lift.length,edges:incidence.size,boundaryEdges:[...incidence.values()].filter(n=>n===1).length,sharedEdges:[...incidence.values()].filter(n=>n===2).length,maxHatReconstructionError:error,source:'https://github.com/isohedral/hatviz',method:'H metatile, four substitutions; coherent integer lift; no search engine'};
fs.writeFileSync(path.join(root,'patch.json'),JSON.stringify({metadata,vertices:lift,tiles,labels}));
console.log(JSON.stringify(metadata,null,2));
