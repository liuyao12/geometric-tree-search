// Integer coefficient coordinates in two triangular planes, not orthonormal Z^4.
export const VERSION='hat-turtle-lift-search-1';
export const CAPACITY=12;
export const BASE=Object.freeze([[0,0,0,0],[0,0,0,1],[-1,0,0,1],[-1,-1,0,1],[-1,-2,0,1],[0,-3,0,1],[0,-3,-1,1],[0,-3,-1,0],[1,-3,-1,0],[1,-2,-1,0],[1,-2,0,-1],[1,-2,1,-1],[0,-1,1,-1],[0,0,1,-1]]);
export const TRIANGLES=[[0,1,3],[1,2,3],[0,3,4],[0,4,13],[4,5,13],[5,6,8],[6,7,8],[5,8,9],[5,9,12],[9,10,12],[10,11,12],[5,12,13]];
export const KERNEL=[[ -1,-1,1,0],[1,-2,0,1]];
export const H=([p,q,r,s])=>[p+r-s,q+r+2*s];
export const T=([p,q,r,s])=>[2*p+q+r,-p+q+s];
export const add=(a,b)=>a.map((x,k)=>x+b[k]);
export const sub=(a,b)=>a.map((x,k)=>x-b[k]);
export const rotate=([p,q,r,s])=>[-q,p+q,-s,r+s];
export const reflect=([p,q,r,s])=>[p+q,-q,r,-r-s];
export const cartesian=([p,q,r,s])=>[p+q/2,Math.sqrt(3)*q/2,Math.sqrt(3)*r/2,r/2+s];
export const key=(layer,x,y)=>`${layer}:${x},${y}`;
export const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
export const area2=poly=>poly.reduce((s,p,i)=>s+p[0]*poly[(i+1)%poly.length][1]-p[1]*poly[(i+1)%poly.length][0],0);
export function inside(p,poly){
 let odd=false;
 for(let i=0,j=poly.length-1;i<poly.length;j=i++){
  const a=poly[j],b=poly[i],det=cross(a,b,p);
  if(det===0&&p[0]>=Math.min(a[0],b[0])&&p[0]<=Math.max(a[0],b[0])&&p[1]>=Math.min(a[1],b[1])&&p[1]<=Math.max(a[1],b[1]))return 0;
  if((a[1]>p[1])!==(b[1]>p[1])&&((det>0)===(b[1]>a[1])))odd=!odd;
 }
 return odd?1:-1;
}
// Every allowed edge lies in the triangular-grid/median arrangement. Splitting
// each elementary triangle by its three medians produces six atomic triangles.
// Their centroids have integer numerators (11,5,2) over the denominator 18.
export function atoms(poly){
 const scaled=poly.map(p=>p.map(x=>18*x)),out=[];
 const lo=[0,1].map(k=>Math.min(...poly.map(p=>p[k]))-1),hi=[0,1].map(k=>Math.max(...poly.map(p=>p[k]))+1);
 for(let q=lo[0];q<=hi[0];q++)for(let r=lo[1];r<=hi[1];r++)for(const upper of [false,true]){
  const vs=upper?[[q+1,r+1],[q,r+1],[q+1,r]]:[[q,r],[q+1,r],[q,r+1]];
  for(let i=0;i<3;i++)for(let j=0;j<3;j++)if(i!==j){
   const k=3-i-j,p=[0,1].map(d=>11*vs[i][d]+5*vs[j][d]+2*vs[k][d]);
   const location=inside(p,scaled);if(location===0)throw Error('Atomic centroid on a tile edge');
   if(location===1)out.push(p);
  }
 }
 if(out.length!==Math.abs(area2(poly))*6)throw Error('Atomic area does not match tile area');
 return out;
}
function angleWeights(poly){
 const orientation=Math.sign(area2(poly));
 const c=p=>[p[0]+p[1]/2,Math.sqrt(3)*p[1]/2],ps=poly.map(c);
 return ps.map((p,i)=>{const a=sub(p,ps[(i+13)%14]),b=sub(ps[(i+1)%14],p),turn=Math.atan2(a[0]*b[1]-a[1]*b[0],a[0]*b[0]+a[1]*b[1])*orientation;
  const units=(Math.PI-turn)*6/Math.PI,n=Math.round(units);if(Math.abs(n-units)>1e-10)throw Error('Non-integral angle');return n;});
}
// Angles are quantized once from the exact 30-degree direction classes; all
// subsequent capacities, supports, translations and markings are integer.
const weightsH=angleWeights(BASE.map(H)),weightsT=angleWeights(BASE.map(T));
const baseAtomsH=atoms(BASE.map(H)),baseAtomsT=atoms(BASE.map(T));
function apply2(p,rot,flip){let [x,y]=p;if(flip)[x,y]=[x+y,-y];for(let i=0;i<rot;i++)[x,y]=[-y,x+y];return [x,y];}
// T's triangular coordinate basis is rotated 30 degrees: horizontal reflection
// has a different coefficient matrix even though it is the SAME physical map.
function applyT(p,rot,flip){let [x,y]=p;if(flip)[x,y]=[x,-x-y];for(let i=0;i<rot;i++)[x,y]=[-y,x+y];return [x,y];}
export const ORIENTATIONS=[];
for(let flip=0;flip<2;flip++)for(let rot=0;rot<6;rot++){
 const verts=BASE.map(p=>{let z=flip?reflect(p):p;for(let i=0;i<rot;i++)z=rotate(z);return z;});
 const support=[];
 for(const [layer,projection,weights,aa,transform] of [['h',H,weightsH,baseAtomsH,apply2],['t',T,weightsT,baseAtomsT,applyT]]){
  verts.forEach((p,i)=>{const [x,y]=projection(p);support.push({layer,x:18*x,y:18*y,weight:weights[i],lift:p,vertex:i});});
  for(const a of aa){const [x,y]=transform(a,rot,flip);support.push({layer,x,y,weight:12,lift:null});}
 }
 ORIENTATIONS.push({index:ORIENTATIONS.length,rot,flip,vertices:verts,support,anchors:support.filter(e=>e.lift)});
}
export function materialize(orientation,translation){
 const o=ORIENTATIONS[orientation],dh=H(translation).map(x=>18*x),dt=T(translation).map(x=>18*x);
 const support=o.support.map(e=>{const d=e.layer==='h'?dh:dt,x=e.x+d[0],y=e.y+d[1];return {...e,x,y,key:key(e.layer,x,y),lift:e.lift?add(e.lift,translation):null};});
 return {id:`${orientation}|${translation.join(',')}`,orientation,translation:[...translation],vertices:o.vertices.map(p=>add(p,translation)),support};
}
export const MODEL_INFO={version:VERSION,orientations:12,hatAtoms:baseAtomsH.length,turtleAtoms:baseAtomsT.length,capacity:12,pointCoordinateDenominator:18,hatAngles:weightsH,turtleAngles:weightsT};

export const dependencyChunk=e=>`${e.layer}:${Math.floor(e.x/72)},${Math.floor(e.y/72)}`;
export function compactPlacement(orientation,translation){
 const o=ORIENTATIONS[orientation],offsets={h:H(translation).map(x=>18*x),t:T(translation).map(x=>18*x)};
 const chunks=[];
 for(const layer of ['h','t']){
  const ps=o.support.filter(e=>e.layer===layer),d=offsets[layer];
  const lo=[0,1].map(k=>Math.floor((Math.min(...ps.map(e=>k?e.y:e.x))+d[k])/72));
  const hi=[0,1].map(k=>Math.floor((Math.max(...ps.map(e=>k?e.y:e.x))+d[k])/72));
  for(let x=lo[0];x<=hi[0];x++)for(let y=lo[1];y<=hi[1];y++)chunks.push(`${layer}:${x},${y}`);
 }
 return {id:`${orientation}|${translation.join(',')}`,orientation,translation:[...translation],offsets,chunks,
  vertices:o.vertices.map(p=>add(p,translation)),
  get support(){return translatedSupport(this);}};
}
export function* translatedSupport(c){
 for(const e of ORIENTATIONS[c.orientation].support){const d=c.offsets[e.layer],x=e.x+d[0],y=e.y+d[1];
  yield {layer:e.layer,x,y,weight:e.weight,key:key(e.layer,x,y),lift:e.lift?add(e.lift,c.translation):null};}
}
