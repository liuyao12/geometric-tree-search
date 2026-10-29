// Source-backed specimen authoring. All geometric predicates and coordinates
// here use BigInt Q(tau). The renderer alone makes approximate copies.
import {writeFile,readFile} from 'node:fs/promises';
import {Golden as G,ZERO,ONE,TAU,vector,vadd,vsub,vscale,dot,cross,determinant,pointKey} from '../assets/golden-field.js';
import {STAR} from '../assets/icosahedral-exact.js';
import {AMMANN_ORIENTATIONS} from '../assets/icosahedral-ammann-markings.js';
const q=x=>{if(x instanceof G)return x;const [a,d='1']=String(x).split('/');return new G(a,'0',d);};
const V=p=>vector(...p.map(q)),O=V([0,0,0]);
const centroid=ps=>vscale(ps.reduce(vadd,O),new G(1n,0n,BigInt(ps.length)));
const unique=ps=>[...new Map(ps.map(p=>[pointKey(p),p])).values()];
function planarHull(ps,n){
 const k=n.findIndex(x=>x.sign()),axes=[0,1,2].filter(i=>i!==k),[a,b]=axes;
 const sorted=unique(ps).sort((u,v)=>u[a].compare(v[a])||u[b].compare(v[b]));
 const turn=(u,v,w)=>v[a].sub(u[a]).mul(w[b].sub(u[b])).sub(v[b].sub(u[b]).mul(w[a].sub(u[a]))).sign();
 const half=xs=>{const h=[];for(const p of xs){while(h.length>1&&turn(h.at(-2),h.at(-1),p)<=0)h.pop();h.push(p);}return h;};
 let result=[...half(sorted).slice(0,-1),...half([...sorted].reverse()).slice(0,-1)];
 if(result.length>=3&&dot(cross(vsub(result[1],result[0]),vsub(result[2],result[0])),n).sign()<0)result.reverse();return result;
}
function convexFaces(points){
 const ps=unique(points),found=new Map();
 for(let a=0;a<ps.length;a++)for(let b=a+1;b<ps.length;b++)for(let c=b+1;c<ps.length;c++){
  let n=cross(vsub(ps[b],ps[a]),vsub(ps[c],ps[a]));if(!dot(n,n).sign())continue;
  const signs=ps.map(p=>dot(n,vsub(p,ps[a])).sign());if(signs.some(x=>x>0)&&signs.some(x=>x<0))continue;
  if(signs.some(x=>x>0))n=vscale(n,-1n);
  const coplanar=ps.filter((_,i)=>!signs[i]),key=coplanar.map(pointKey).sort().join('|');
  if(!found.has(key))found.set(key,planarHull(coplanar,n));
 }return [...found.values()];
}
function mesh(id,name,polygons,more={}){
 const vertices=[],ids=new Map();const faces=polygons.filter(p=>p.length>=3).map(poly=>poly.map(p=>{const k=pointKey(p);if(!ids.has(k)){ids.set(k,vertices.length);vertices.push(p);}return ids.get(k);}));
 return {id,name,vertices,faces,...more};
}
function tetra(id,points){return mesh(id,id,convexFaces(points));}
const corners=(lo,hi)=>Array.from({length:8},(_,m)=>V(lo.map((x,i)=>m&(1<<i)?hi[i]:x)));
function voxelUnion(id,name,cells,grid){
 const polygons=[],set=new Set(cells.map(c=>c.join(',')));for(const c of cells)for(let axis=0;axis<3;axis++)for(const sign of [-1,1]){
  const nb=c.map((x,i)=>x+(i===axis?sign:0));if(set.has(nb.join(',')))continue;
  const axes=[0,1,2].filter(i=>i!==axis),ps=[];for(const a of [0,1])for(const b of [0,1]){const p=c.map((x,i)=>q(grid[x]));p[axis]=q(grid[c[axis]+(sign>0?1:0)]);p[axes[0]]=q(grid[c[axes[0]]+a]);p[axes[1]]=q(grid[c[axes[1]]+b]);ps.push(vector(...p));}
  polygons.push(planarHull(ps,V([0,0,0].map((_,i)=>i===axis?sign:0))));
 }return mesh(id,name,polygons,{recipe:{cells,grid:grid.map(String)}});
}
function zonotope(id,name,generators){
 const ps=Array.from({length:1<<generators.length},(_,mask)=>generators.reduce((s,g,i)=>mask&(1<<i)?vadd(s,g):s,O));const polygons=[];
 for(let i=0;i<generators.length;i++)for(let j=i+1;j<generators.length;j++){
  const normal=cross(generators[i],generators[j]);for(const sign of [-1n,1n]){const n=vscale(normal,sign),mx=ps.map(p=>dot(n,p)).reduce((x,y)=>x.compare(y)>0?x:y);polygons.push(planarHull(ps.filter(p=>dot(n,p).equals(mx)),n));}
 }return mesh(id,name,polygons,{recipe:{zonotopeGenerators:generators}});
}
const mirrorPoly=(poly,p,n)=>poly.map(v=>vsub(v,vscale(n,dot(n,vsub(v,p)).mul(2n).div(dot(n,n))))).reverse();
function danzerOcta(t){
 const fs=t.faces.map(f=>f.map(i=>t.vertices[i])),planes=fs.map(f=>({p:f[0],n:cross(vsub(f[1],f[0]),vsub(f[2],f[0]))}));let pair;
 for(let i=0;i<planes.length;i++)for(let j=i+1;j<planes.length;j++)if(!dot(planes[i].n,planes[j].n).sign()){pair??=[i,j];}
 const indices=t.id==='K'?[0,1,2,3].filter(i=>pair.every(j=>i===j||!dot(planes[i].n,planes[j].n).sign())):pair;
 let cells=[fs];for(const index of indices){const {p,n}=planes[index];cells=[...cells,...cells.map(fs=>fs.map(f=>mirrorPoly(f,p,n)))];}
 const exterior=new Map();for(const fs of cells)for(const f of fs){const key=f.map(pointKey).sort().join('|');if(exterior.has(key))exterior.delete(key);else exterior.set(key,f);}
 return mesh('octa-'+t.id,'Octahedron '+t.id,[...exterior.values()],{tetrahedronCount:cells.length});
}
export function buildSpecimens(){
 const out={};out.ammann=['prolate','oblate'].flatMap(kind=>['left','right'].map(hand=>{const t=AMMANN_ORIENTATIONS.find(t=>t.kind===kind&&t.decoration.hand===hand);return {...mesh(kind+'-'+hand,`${kind==='prolate'?'Prolate':'Oblate'} · ${hand}`,t.faces.map(f=>f.map(i=>t.vertices[i]))),dots:t.faceDots.map(d=>({center:d.center,black:d.blackCorner,red:d.redCorner})),pointMarkings:t.pointMarkings,decoration:t.decoration};}));
 const p=AMMANN_ORIENTATIONS.find(t=>t.kind==='prolate');out.socolar=[mesh('ss-hexahedron','Golden rhombohedron',p.faces.map(f=>f.map(i=>p.vertices[i]))),zonotope('ss-dodecahedron','Rhombic dodecahedron',STAR.slice(0,4)),zonotope('ss-icosahedron','Rhombic icosahedron',STAR.slice(0,5)),zonotope('ss-triacontahedron','Rhombic triacontahedron',STAR)];
 const t2=TAU.pow(2n),t3=TAU.pow(3n);out.danzer=[tetra('A',[O,V([t3,0,t2]),V([t2,t2,t2]),V([t2,1,0])]),tetra('B',[O,V([t3,0,t2]),V([t2,t2,t2]),V([t2,TAU,1])]),tetra('C',[O,V([TAU.neg(),0,1]),V([t2,t2,t2]),V([0,t2,1])]),tetra('K',[O,V([-1,TAU,0]),V([TAU,TAU,TAU]),vscale(V([-1,TAU.inv(),TAU]),q('1/2'))])];
 for(const t of out.danzer){t.rightAngleEdges=[];const fs=t.faces.map(f=>({ids:f,n:cross(vsub(t.vertices[f[1]],t.vertices[f[0]]),vsub(t.vertices[f[2]],t.vertices[f[0]]))}));for(let i=0;i<fs.length;i++)for(let j=i+1;j<fs.length;j++)if(!dot(fs[i].n,fs[j].n).sign())t.rightAngleEdges.push(fs[i].ids.filter(k=>fs[j].ids.includes(k)));}
 out.danzerOcta=out.danzer.map(danzerOcta);
 const grid=['-1','-3/4','3/4','1'],inds=Array.from({length:27},(_,i)=>[i%3,Math.floor(i/3)%3,Math.floor(i/9)]),cells=inds.filter(c=>c.filter(x=>x!==1).length<=1);
 const L=voxelUnion('L','L tile',cells,grid),half=sign=>convexFaces([O,...[q('1/4'),ONE].flatMap(x=>[-1,1].flatMap(y=>[-1,1].map(z=>V([x.mul(BigInt(sign)),q(y).div(4n),q(z).div(4n)]))))]);
 const I=mesh('I','I tile',[...half(1),...half(-1)],{note:'Two solid components meet at one point; the interior is disconnected.'});out.goodman=[I,L];
 const X=voxelUnion('X0','Unmarked cross',cells,['-1','-1/4','1/4','1']);out.goodmanCross=[L,X,{...X,id:'X1',name:'Marked cross',endpointMarks:true}];
 const a=V([5,0,0]),b=V([3,4,0]),c=V(['3/2',2,1]),d=V(['5/2',0,-1]);out.scd=[mesh('scd','SCD biprism',convexFaces([O,a,b,vadd(a,b),c,vadd(a,c),d,vadd(b,d)]),{recipe:{lambda:'1/2',b1:'3',b2:'4',height:'1',rotation:[['4/5','3/5','0'],['-3/5','4/5','0'],['0','0','1']]}})];

 return out;
}
export function volume(t){let v=ZERO;for(const f of t.faces)for(let i=1;i+1<f.length;i++)v=v.add(determinant(t.vertices[f[0]],t.vertices[f[i]],t.vertices[f[i+1]]).div(6n));return v;}
export function serialize(t){return {...t,volume:volume(t)};}
if(import.meta.url===new URL(process.argv[1],'file:').href){const systems=buildSpecimens();for(const [key,tiles]of Object.entries(systems)){console.log(key,tiles.map(t=>[t.name,t.vertices.length,t.faces.length,volume(t).toString()]));systems[key]=tiles.map(serialize);}await writeFile(new URL('../apps/quasicrystal-exact/data/polyhedra-exact.json',import.meta.url),JSON.stringify({format:'gcts-polyhedral-specimens-v1',scalar:'(a+b*tau)/d; tau^2=tau+1',systems}));}
