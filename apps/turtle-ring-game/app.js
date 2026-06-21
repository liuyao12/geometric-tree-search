const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');
const marksToggle = document.getElementById('marks');
const gridToggle = document.getElementById('grid');
const buildButton = document.getElementById('build');
const resetButton = document.getElementById('resetView');

const sqrt2 = Math.sqrt(2), sqrt6 = Math.sqrt(6), latticeScale = 24;
const MAX = 12, markReach = 3;
const turtleVerts = [[3,-2,-1],[2,0,-2],[0,1,-1],[0,2,-2],[-1,3,-2],[-2,2,0],[-1,0,1],[-2,0,2],[-2,-1,3],[0,-2,2],[1,-4,3],[2,-4,2],[3,-5,2],[4,-4,0]];
const turtleAngles = [6,4,9,4,3,4,9,4,3,8,3,8,3,4];
const turtleStripeDefs = [{from:0,to:10,value:1},{from:2,to:8,value:-1},{from:0,to:6,value:-1},{from:4,to:12,value:-1}];
const trefoilVerts = [[1,0,-1],[2,0,-2],[2,1,-3],[0,2,-2],[-1,1,0],[-2,2,0],[-3,2,1],[-2,0,2],[0,-1,1],[0,-2,2],[1,-3,2],[2,-2,0]];
const trefoilAngles = [9,4,3,4,9,4,3,4,9,4,3,4];
const trefoilStripeDefs = [{p1:trefoilVerts[0],p2:trefoilVerts[6],value:-1},{p1:trefoilVerts[4],p2:trefoilVerts[10],value:-1},{p1:trefoilVerts[8],p2:trefoilVerts[2],value:-1}];
const perms = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
const key = p => p.join(',');
const add = (a,b) => [a[0]+b[0],a[1]+b[1],a[2]+b[2]];
const sub = (a,b) => [a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const norm = p => Math.abs(p[0])+Math.abs(p[1])+Math.abs(p[2]);
const gcd2 = (a,b) => { a=Math.abs(a); b=Math.abs(b); while(b) [a,b]=[b,a%b]; return a||1; };
const gcd3 = (a,b,c) => gcd2(gcd2(a,b),c);
function projectRaw([x,y,z]) { return { x: ((z-x)/sqrt2)*latticeScale, y: ((2*y-x-z)/sqrt6)*latticeScale }; }
let allBase = [...turtleVerts, ...trefoilVerts].map(projectRaw); let center = allBase.reduce((s,p)=>({x:s.x+p.x,y:s.y+p.y}),{x:0,y:0}); center.x/=allBase.length; center.y/=allBase.length;
function project(p) { const q=projectRaw(p); return {x:q.x-center.x,y:q.y-center.y}; }
function primitive(a,b) { const d=sub(b,a), steps=gcd3(d[0],d[1],d[2]); return {steps, step:d.map(v=>v/steps)}; }
function segmentPoints(a,b,extra=0) { const {steps,step}=primitive(a,b); return Array.from({length:steps+1+2*extra},(_,i)=>add(a, step.map(v=>v*(i-extra)))); }
function componentFor(a,b) { const {step}=primitive(a,b); const c=step.findIndex((v,i)=>{ const o=[0,1,2].filter(j=>j!==i); return step[o[0]]===step[o[1]] && v===-2*step[o[0]]; }); return c>=0?c:0; }
function parity(p) { return ((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2===0 ? 1 : -1; }
function transformLinear(p,sym) { return sym.permutation.map(i => sym.sign*p[i]); }
function transformAffine(p, op) { return add(transformLinear(p, op.sym), op.translation); }
function mapComponent(c,sym) { const m=sym.permutation.indexOf(c); return m>=0?m:c; }
function symmetries() { return [1,-1].flatMap(sign => perms.map(permutation => ({sign, permutation, planeSign:parity(permutation)}))); }
function symmetryKind(sym) {
  if (sym.sign === -1 && sym.permutation.every((value, index) => value === index)) return 'half-turn';
  return sym.planeSign < 0 ? 'reflection' : 'rotation';
}
function pointInPoly(pt, poly) { let inside=false; for(let i=0,j=poly.length-1;i<poly.length;j=i++) { const a=poly[i],b=poly[j]; const cross=(pt.x-a.x)*(b.y-a.y)-(pt.y-a.y)*(b.x-a.x); const dot=(pt.x-a.x)*(pt.x-b.x)+(pt.y-a.y)*(pt.y-b.y); if(Math.abs(cross)<1e-7 && dot<=1e-7) return false; if((a.y>pt.y)!==(b.y>pt.y) && pt.x<((b.x-a.x)*(pt.y-a.y))/(b.y-a.y)+a.x) inside=!inside; } return inside; }
function interiors(verts) { const xs=verts.map(p=>p[0]), ys=verts.map(p=>p[1]), vkeys=new Set(verts.map(key)), poly=verts.map(projectRaw), out=[]; for(let x=Math.min(...xs);x<=Math.max(...xs);x++) for(let y=Math.min(...ys);y<=Math.max(...ys);y++){ const p=[x,y,-x-y]; if(!vkeys.has(key(p)) && pointInPoly(projectRaw(p), poly)) out.push(p); } return out; }
const turtleOcc = [...turtleVerts.map((p,i)=>({point:p,value:turtleAngles[i],kind:'vertex'})), ...interiors(turtleVerts).map(point=>({point,value:MAX,kind:'interior'}))];
const trefoilOcc = trefoilVerts.map((point,i)=>({point,value:trefoilAngles[i],kind:'vertex'}));
const turtleStripes = turtleStripeDefs.map(d=>({...d, p1:turtleVerts[d.from], p2:turtleVerts[d.to], component:componentFor(turtleVerts[d.from], turtleVerts[d.to])}));
const trefoilStripes = trefoilStripeDefs.map(d=>({...d, component:componentFor(d.p1,d.p2)}));
function orientTile(verts, occ, stripes, sym, idx, name) { const vertices=verts.map(p=>transformLinear(p,sym)); const occupancy=occ.map(e=>({...e, point:transformLinear(e.point,sym)})); const marks=[]; const segments=stripes.map(seg=>{ const p1=transformLinear(seg.p1,sym), p2=transformLinear(seg.p2,sym), component=mapComponent(seg.component,sym), value=seg.value*sym.planeSign; segmentPoints(p1,p2,markReach).forEach(point=>marks.push({point,component,value})); return {p1,p2,component,value}; }); return {idx,name,vertices,occupancy,marks,segments}; }
const allSymmetries = symmetries();
const turtleOrientations = allSymmetries.map((s,i)=>orientTile(turtleVerts,turtleOcc,turtleStripes,s,i,'Turtle'));
const trefoilBase = orientTile(trefoilVerts,trefoilOcc,trefoilStripes,allSymmetries[0],0,'Trefoil');
function place(orientation, translation, extra={}) { return {...extra, orientation, translation, vertices:orientation.vertices.map(p=>add(p,translation)), occupancy:orientation.occupancy.map(e=>({...e,point:add(e.point,translation)})), marks:orientation.marks.map(e=>({...e,point:add(e.point,translation)})), segments:orientation.segments.map(s=>({...s,p1:add(s.p1,translation),p2:add(s.p2,translation)}))}; }
function transformPlacement(placement, op) { return {...placement, vertices: placement.vertices.map(p=>transformAffine(p, op)), occupancy: placement.occupancy.map(e=>({...e, point: transformAffine(e.point, op)})), marks: placement.marks.map(e=>({...e, point: transformAffine(e.point, op), component: mapComponent(e.component, op.sym), value: e.value * op.sym.planeSign})), segments: placement.segments.map(s=>({...s, p1: transformAffine(s.p1, op), p2: transformAffine(s.p2, op), component: mapComponent(s.component, op.sym), value: s.value * op.sym.planeSign}))}; }
let view={scale:.72, x:canvas.width/2, y:canvas.height/2}, placements=[], coronas=[];
function mkey(e){return `${key(e.point)}|${e.component}`;}
function addPlacement(p,sums,markSums){ for(const e of p.occupancy){const k=key(e.point), old=sums.get(k)||{point:e.point,value:0}; old.value+=e.value; sums.set(k,old);} for(const e of p.marks){const k=mkey(e), old=markSums.get(k); if(old && old.value!==e.value) old.conflict=true; markSums.set(k,{value:e.value,count:(old?.count||0)+1, conflict:!!old?.conflict});}}
function frontier(sums){return [...sums.values()].filter(e=>e.value<MAX).sort((a,b)=>norm(a.point)-norm(b.point)||a.value-b.value);}
function validCandidate(o,t,sums,markSums,used){ const pk=`${o.idx}|${key(t)}`; if(used.has(pk)) return null; let newPts=0, overflow=0, line=0; const occ=o.occupancy.map(e=>({...e,point:add(e.point,t)})); for(const e of occ){ const cur=sums.get(key(e.point))?.value||0; if(cur===0)newPts++; overflow=Math.max(overflow,cur+e.value-MAX); } if(overflow>0||newPts===0) return null; const marks=o.marks.map(e=>({...e,point:add(e.point,t)})); for(const e of marks){ const old=markSums.get(mkey(e)); if(old){ if(old.value!==e.value) return null; if(e.value!==0) line++; }} return {orientation:o, translation:t, pk, score:line*100-newPts}; }
function buildPatch(limit=170){ placements=[place(trefoilBase,[0,0,0],{kind:'seed'})]; const sums=new Map(), markSums=new Map(), used=new Set(); addPlacement(placements[0],sums,markSums); for(let step=0; step<limit*40 && placements.length<limit; step++){ let best=null; for(const f of frontier(sums).slice(0,24)){ const need=MAX-f.value; for(const o of turtleOrientations){ for(const a of o.occupancy.filter(e=>e.value<=need)){ const cand=validCandidate(o, sub(f.point,a.point), sums, markSums, used); if(cand && (!best || cand.score>best.score)) best={...cand, frontier:f}; } } if(best?.score>=0) break; } if(!best) break; const p=place(best.orientation,best.translation,{kind:'turtle', placementKey:best.pk}); placements.push(p); used.add(best.pk); addPlacement(p,sums,markSums); }
 coronas=computeCoronas(); statusEl.textContent=`Built ${placements.length-1} turtles; corona ${Math.max(...coronas.filter(Number.isFinite))}. Click a corona-1 turtle.`; draw(); }
function computeCoronas(){ const cs=placements.map((_,i)=>i===0?0:Infinity), byPoint=new Map(); placements.forEach((p,i)=>p.occupancy.forEach(e=>{const k=key(e.point); (byPoint.get(k)||byPoint.set(k,[]).get(k)).push(i);})); for(let q=[0],c=0;c<q.length;c++){ for(const e of placements[q[c]].occupancy){ for(const j of byPoint.get(key(e.point))||[]) if(cs[j]>cs[q[c]]+1){cs[j]=cs[q[c]]+1; q.push(j);} } } return cs; }
function screen(p){ const q=project(p); return {x:view.x+q.x*view.scale,y:view.y+q.y*view.scale}; }
function drawPoly(points, fill, stroke, width=1.5){ ctx.beginPath(); points.forEach((p,i)=>{const s=screen(p); i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y);}); ctx.closePath(); ctx.fillStyle=fill; ctx.fill(); ctx.strokeStyle=stroke; ctx.lineWidth=width; ctx.stroke(); }
function draw(){ ctx.clearRect(0,0,canvas.width,canvas.height); if(gridToggle.checked) drawGrid(); placements.forEach((p,i)=>drawPoly(p.vertices, i?'rgba(0,114,178,.42)':'rgba(78,121,80,.68)', i?'#005a8c':'#355f39', i&&coronas[i]===1?3:1.5)); if(marksToggle.checked) for(const p of placements) for(const s of p.segments){ const a=screen(s.p1), b=screen(s.p2); ctx.strokeStyle=s.value>0?'#d55e00':'#0072b2'; ctx.setLineDash(s.value>0?[]:[6,5]); ctx.lineWidth=2.2; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke(); ctx.setLineDash([]); } }
function drawGrid(){ ctx.fillStyle='rgba(20,60,55,.16)'; for(let x=-12;x<=12;x++) for(let y=-12;y<=12;y++){ const s=screen([x,y,-x-y]); ctx.beginPath(); ctx.arc(s.x,s.y,1.4,0,7); ctx.fill(); } }
function hitTile(ev){ const r=canvas.getBoundingClientRect(), pt={x:(ev.clientX-r.left)*canvas.width/r.width,y:(ev.clientY-r.top)*canvas.height/r.height}; for(let i=placements.length-1;i>0;i--){ if(coronas[i]!==1) continue; const poly=placements[i].vertices.map(screen); if(pointInPoly(pt, poly)) return i; } return -1; }
function candidateLocalOps(seed, turtle) {
  const pairVertices = [...seed.vertices, ...turtle.vertices];
  const pairCenter = pairVertices.reduce((sum, point) => add(sum, point), [0, 0, 0]).map(value => value / pairVertices.length);
  const roundedCenter = pairCenter.map(Math.round);
  const translations = [];
  for (let dx = -8; dx <= 8; dx += 1) {
    for (let dy = -8; dy <= 8; dy += 1) {
      const dz = -dx - dy;
      translations.push(add(roundedCenter, [dx, dy, dz]));
    }
  }
  const ops = [];
  for (const sym of allSymmetries) {
    const kind = symmetryKind(sym);
    if (kind !== 'half-turn' && kind !== 'reflection') continue;
    for (const translation of translations) ops.push({ sym, translation, kind });
  }
  const seen = new Set();
  return ops.filter(op => { const k = `${op.kind}|${op.sym.sign}|${op.sym.permutation.join(',')}|${key(op.translation)}`; if (seen.has(k)) return false; seen.add(k); return true; });
}
function tilingIsValid(nextPlacements) {
  const sums = new Map(), marks = new Map();
  for (const p of nextPlacements) addPlacement(p, sums, marks);
  for (const entry of sums.values()) if (entry.value > MAX) return false;
  for (const entry of marks.values()) if (entry.conflict) return false;
  return true;
}
function localMoveFor(clickedIndex) {
  if (clickedIndex < 0) return null;
  const seed = placements[0], clicked = placements[clickedIndex];
  const moves = candidateLocalOps(seed, clicked).map(op => {
    const movedSeed = transformPlacement(seed, op);
    const movedClicked = transformPlacement(clicked, op);
    const next = placements.slice();
    next[0] = movedSeed;
    next[clickedIndex] = movedClicked;
    return { op, next };
  }).filter(move => tilingIsValid(move.next));
  const halfTurns = moves.filter(move => move.op.kind === 'half-turn');
  const reflections = moves.filter(move => move.op.kind === 'reflection');
  if (halfTurns.length && !reflections.length) return halfTurns[0];
  if (reflections.length && !halfTurns.length) return reflections[0];
  return null;
}
function flipClicked(i){ const move = localMoveFor(i); if(!move) { statusEl.textContent = i < 0 ? 'Click a corona-1 turtle.' : 'That neighboring turtle has no legal local flip.'; return; } placements = move.next; coronas = computeCoronas(); statusEl.textContent = `Applied one local ${move.op.kind}; all other turtles stayed fixed.`; draw(); }
function resizeCanvas() { const ratio = window.devicePixelRatio || 1; const rect = canvas.getBoundingClientRect(); const width = Math.max(1, Math.round(rect.width * ratio)); const height = Math.max(1, Math.round(rect.height * ratio)); if (canvas.width !== width || canvas.height !== height) { const old = {w:canvas.width, h:canvas.height}; canvas.width = width; canvas.height = height; view.x *= width / old.w; view.y *= height / old.h; } draw(); }
let dragging=false,last=null,down=null; canvas.addEventListener('pointerdown',e=>{dragging=true;last={x:e.clientX,y:e.clientY};down={...last}; canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{ if(!dragging)return; const ratio=window.devicePixelRatio||1; view.x+=(e.clientX-last.x)*ratio; view.y+=(e.clientY-last.y)*ratio; last={x:e.clientX,y:e.clientY}; draw();});
canvas.addEventListener('pointerup',e=>{ if(down && Math.hypot(e.clientX-down.x,e.clientY-down.y)<4) flipClicked(hitTile(e)); dragging=false; down=null;});
canvas.addEventListener('wheel',e=>{ e.preventDefault(); const f=Math.exp(-e.deltaY*0.001); view.scale=Math.max(.12,Math.min(3.5,view.scale*f)); draw(); },{passive:false});
marksToggle.addEventListener('change',draw); gridToggle.addEventListener('change',draw); buildButton.addEventListener('click',()=>buildPatch()); resetButton.addEventListener('click',()=>{view={scale:.72,x:canvas.width/2,y:canvas.height/2};draw();});
window.addEventListener('resize', resizeCanvas);
buildPatch();
resizeCanvas();
