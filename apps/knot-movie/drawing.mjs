import { topology, parse, canonical, moves } from './engine.mjs';

const cross = (a,b,c) => (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
const distance = (a,b) => Math.hypot(a[0]-b[0],a[1]-b[1]);
const pointSegmentDistance = (p,a,b) => {const dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)));return distance(p,[a[0]+t*dx,a[1]+t*dy]);};

// Expand each ribbon vertex into its four ports, subdivide every edge and
// triangulate each bounded face. This prevents loops and parallel edges from
// collapsing in a barycentric drawing. The added graph is drawing data only;
// it never participates in tile legality or the search.
export function planarDrawing(word) {
  if (!word.length) return { word, crossings: [], strands: [], points: [], edges: [] };
  const { alpha, sigma, faces } = topology(word), n = alpha.length;
  const groups = new Map(); word.forEach((x,i) => { if(!groups.has(x.id))groups.set(x.id,[]);groups.get(x.id).push(i); });
  const adjacency = Array.from({length:n},()=>new Set()), edges = [], ringMid = new Map(), strandMid = new Map();
  const node = () => {adjacency.push(new Set());return adjacency.length-1;};
  const connect = (a,b) => {if(!adjacency[a].has(b)){adjacency[a].add(b);adjacency[b].add(a);edges.push([a,b]);}};
  for(let d=0;d<n;d++) {
    const mid=node();ringMid.set(d,mid);connect(d,mid);connect(mid,sigma[d]);
    if(d<alpha[d]) {const mid=node();strandMid.set(d,mid);strandMid.set(alpha[d],mid);connect(d,mid);connect(mid,alpha[d]);}
  }
  const boundaries=faces.map(f=>f.flatMap(d=>[d,strandMid.get(d),alpha[d],ringMid.get(alpha[d])]));
  const outerIndex=boundaries.reduce((best,f,i)=>f.length>boundaries[best].length?i:best,0);
  const centers=new Map();
  const fill = boundary => {const center=node();for(const d of boundary)connect(center,d);return center;};
  for(let i=0;i<boundaries.length;i++)if(i!==outerIndex)fill(boundaries[i]);
  for(const [id,indices]of groups){let d=2*indices[0],ports=[];do{ports.push(d,ringMid.get(d));d=sigma[d];}while(d!==2*indices[0]);centers.set(id,fill(ports));}
  const outer=boundaries[outerIndex];
  if(new Set(outer).size!==outer.length)throw Error('Drawing boundary is not a simple cycle.');
  const fixed=new Set(outer),points=Array(adjacency.length);
  outer.forEach((id,k)=>points[id]=[Math.cos(2*Math.PI*k/outer.length),Math.sin(2*Math.PI*k/outer.length)]);
  const interior=adjacency.map((_,i)=>i).filter(i=>!fixed.has(i)),index=new Map(interior.map((id,i)=>[id,i]));
  const matrix=interior.map(id=>{
    const row=Array(interior.length+2).fill(0);row[index.get(id)]=adjacency[id].size;
    for(const neighbor of adjacency[id])if(fixed.has(neighbor)){row[interior.length]+=points[neighbor][0];row[interior.length+1]+=points[neighbor][1];}else row[index.get(neighbor)]--;
    return row;
  });
  // Pivoted Gaussian elimination solves both coordinate right-hand sides.
  for(let k=0;k<interior.length;k++){
    let pivot=k;for(let i=k+1;i<matrix.length;i++)if(Math.abs(matrix[i][k])>Math.abs(matrix[pivot][k]))pivot=i;
    [matrix[k],matrix[pivot]]=[matrix[pivot],matrix[k]];
    if(Math.abs(matrix[k][k])<1e-12)throw Error('Singular drawing system.');
    for(let i=k+1;i<matrix.length;i++){const factor=matrix[i][k]/matrix[k][k];if(!factor)continue;for(let j=k;j<interior.length+2;j++)matrix[i][j]-=factor*matrix[k][j];}
  }
  for(let i=interior.length-1;i>=0;i--){const p=[matrix[i][interior.length],matrix[i][interior.length+1]];for(let j=i+1;j<interior.length;j++){p[0]-=matrix[i][j]*points[interior[j]][0];p[1]-=matrix[i][j]*points[interior[j]][1];}points[interior[i]]=p.map(x=>x/matrix[i][i]);}
  const crossingData=[...groups].map(([id,indices])=>{
    const over=indices.find(i=>word[i].over),under=indices.find(i=>!word[i].over);
    return {id,center:centers.get(id),over:[2*over,2*over+1],under:[2*under,2*under+1],sign:word[over].sign};
  });
  // The screen reverses vertical coordinates. Normalize the mathematical
  // orientation here, before the final display transform.
  const first=crossingData[0],o=first.over,u=first.under;
  const det=(points[o[1]][0]-points[o[0]][0])*(points[u[1]][1]-points[u[0]][1])-(points[o[1]][1]-points[o[0]][1])*(points[u[1]][0]-points[u[0]][0]);
  if(Math.sign(det)!==first.sign)for(const p of points)p[1]*=-1;
  const strands=word.map((x,i)=>[centers.get(x.id),2*i+1,strandMid.get(2*i+1),2*((i+1)%word.length),centers.get(word[(i+1)%word.length].id)]);
  return {word,crossings:crossingData,strands,points,edges,outer};
}

// Audit the actual routing: no unintended crossings, positive strand lengths,
// and the prescribed cyclic order and crossing signs at every crossing.
export function verifyDrawing(drawing) {
  const {points,edges,crossings}=drawing;
  for(const [a,b]of edges)if(distance(points[a],points[b])<1e-10)throw Error('Collapsed drawing edge.');
  for(let i=0;i<edges.length;i++)for(let j=0;j<i;j++){
    const [a,b]=edges[i],[c,d]=edges[j];if([a,b].some(x=>x===c||x===d))continue;
    const p=points[a],q=points[b],r=points[c],s=points[d];
    if(cross(p,q,r)*cross(p,q,s)<-1e-15&&cross(r,s,p)*cross(r,s,q)<-1e-15)throw Error('Unintended drawing crossing.');
  }
  for(const c of crossings){
    const center=points[c.center],ports=[...c.over,...c.under];
    if(ports.some(p=>distance(points[p],center)<1e-10))throw Error('Collapsed crossing.');
    const [a,b]=c.over.map(i=>points[i]),[u,v]=c.under.map(i=>points[i]);
    if(Math.sign((b[0]-a[0])*(v[1]-u[1])-(b[1]-a[1])*(v[0]-u[0]))!==c.sign)throw Error('Crossing sign mismatch.');
    const angles=ports.map(p=>Math.atan2(points[p][1]-center[1],points[p][0]-center[0]));
    const sorted=ports.map((p,i)=>({p,angle:angles[i]})).sort((a,b)=>a.angle-b.angle).map(x=>c.over.includes(x.p));
    if(sorted.some((x,i)=>x===sorted[(i+1)%4]))throw Error('Crossing ports do not alternate.');
  }
  return true;
}

export function movieDrawings(certificate) {
  let word=parse(certificate.source),before=planarDrawing(word);verifyDrawing(before);
  const frames=[];
  for(const step of certificate.steps){
    const move=moves(word,certificate.crossingCap).find(m=>m.kind===step.kind&&m.key===step.after);
    if(!move)throw Error('Cannot draw an unverified move.');
    const affected=new Set(move.patch.map(d=>word[Math.floor(d/2)]?.id).filter(id=>id!==undefined));
    // Insertion patches are gaps; identify their new crossings instead.
    if(move.kind.endsWith('+')){affected.clear();const old=new Set(word.map(x=>x.id));move.after.forEach(x=>{if(!old.has(x.id))affected.add(x.id);});}
    const after=planarDrawing(move.after);
    // Keep surviving, untouched crossing neighborhoods facing the same way.
    // This is only a rigid rotation of a valid planar drawing, not a morph.
    let dot=0,det=0;
    for(const c of after.crossings)if(!affected.has(c.id)){
      const old=before.crossings.find(x=>x.id===c.id);if(!old)continue;
      for(const [a,b]of [[old.center,c.center],...old.over.map((p,i)=>[p,c.over[i]]),...old.under.map((p,i)=>[p,c.under[i]])]){
        const p=before.points[a],q=after.points[b];dot+=p[0]*q[0]+p[1]*q[1];det+=q[0]*p[1]-q[1]*p[0];
      }
    }
    const angle=Math.atan2(det,dot),cos=Math.cos(angle),sin=Math.sin(angle);
    after.points=after.points.map(([x,y])=>[cos*x-sin*y,sin*x+cos*y]);verifyDrawing(after);
    const beforeStrands=new Set(move.kind.endsWith('+')?[]:move.patch.map(d=>((d%2?Math.floor(d/2):Math.floor(d/2)-1)+word.length)%word.length));
    const occurrence=x=>`${x.id}:${x.over}`;
    const successors=new Map(word.map((x,i)=>[occurrence(x),occurrence(word[(i+1)%word.length])]));
    const afterStrands=new Set(move.after.map((x,i)=>successors.get(occurrence(x))!==occurrence(move.after[(i+1)%move.after.length])?i:-1).filter(i=>i>=0));
    frames.push({kind:move.kind,before,after,affected,beforeStrands,afterStrands});word=move.after;before=after;
  }
  if(canonical(word)!==canonical(parse(certificate.target)))throw Error('Wrong drawing endpoint.');
  return frames;
}

export function drawKnot(canvas,drawing,{affected=new Set(),changedStrands=new Set(),labels=false}={}) {
  const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
  ctx.clearRect(0,0,w,h);ctx.lineCap='round';ctx.lineJoin='round';
  if(!drawing.word.length){ctx.strokeStyle='#a7e7bd';ctx.lineWidth=7;ctx.beginPath();ctx.ellipse(w/2,h/2,w*.27,h*.30,0,0,Math.PI*2);ctx.stroke();return;}
  const scale=Math.min(w,h)*.42,xy=drawing.points.map(p=>[w/2+p[0]*scale,h/2-p[1]*scale]);
  const line=(ids,color,width)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ids.forEach((id,i)=>i?ctx.lineTo(...xy[id]):ctx.moveTo(...xy[id]));ctx.stroke();};
  const segments=drawing.strands.flatMap(s=>s.slice(1).map((p,i)=>[s[i],p]));
  const clearances=new Map(drawing.crossings.map(c=>[c.id,Math.min(...segments.filter(s=>!s.includes(c.center)).map(([a,b])=>pointSegmentDistance(xy[c.center],xy[a],xy[b])))]));
  const minSpacing=Math.min(...drawing.crossings.flatMap(c=>[...c.over,...c.under].map(p=>distance(xy[c.center],xy[p]))));
  const width=Math.min(7,minSpacing*.18,...[...clearances.values()].map(x=>x*.18));
  drawing.strands.forEach((strand,i)=>line(strand,changedStrands.has(i)?'#ffc87b':'#a7e7bd',width));
  for(const c of drawing.crossings){
    const center=xy[c.center],radius=Math.min(...[...c.over,...c.under].map(p=>distance(center,xy[p])))*.34;
    // Only the small crossing neighborhood is redrawn; the planar routing is
    // untouched. The overpass has a clear gap on each side underneath it.
    ctx.fillStyle='#102029';ctx.beginPath();ctx.arc(...center,Math.min(clearances.get(c.id)*.45,width*2.2),0,Math.PI*2);ctx.fill();
    line([c.over[0],c.center,c.over[1]],affected.has(c.id)?'#ffc87b':'#a7e7bd',width);
    if(affected.has(c.id)){ctx.strokeStyle='#ffc87b';ctx.lineWidth=1.5;ctx.setLineDash([5,5]);ctx.beginPath();ctx.arc(...center,Math.max(15,radius+8),0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);}
    if(labels){ctx.fillStyle='#dbe6e8';ctx.font='13px system-ui';ctx.fillText(String(c.id),center[0]+12,center[1]-12);}
  }
}
