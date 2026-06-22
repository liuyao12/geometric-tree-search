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
  const isIdentity = sym.sign === 1 && sym.permutation.every((value, index) => value === index);
  if (isIdentity) return 'identity';
  if (sym.sign === -1 && sym.permutation.every((value, index) => value === index)) return 'half-turn';
  return sym.planeSign < 0 ? 'reflection' : 'rotation';
}
function pointInPoly(pt, poly) { let inside=false; for(let i=0,j=poly.length-1;i<poly.length;j=i++) { const a=poly[i],b=poly[j]; const cross=(pt.x-a.x)*(b.y-a.y)-(pt.y-a.y)*(b.x-a.x); const dot=(pt.x-a.x)*(pt.x-b.x)+(pt.y-a.y)*(pt.y-b.y); if(Math.abs(cross)<1e-7 && dot<=1e-7) return false; if((a.y>pt.y)!==(b.y>pt.y) && pt.x<((b.x-a.x)*(pt.y-a.y))/(b.y-a.y)+a.x) inside=!inside; } return inside; }

const cellE1 = [1, 0, -1], cellE2 = [0, 1, -1];
function pointInPlacement(point, placement) { return pointInPoly(projectRaw(point), placement.vertices.map(projectRaw)); }
function tileCellKeys(placement) {
  const xs = placement.vertices.map(point => point[0]), ys = placement.vertices.map(point => point[1]);
  const cells = [];
  for (let x = Math.floor(Math.min(...xs)) - 1; x <= Math.ceil(Math.max(...xs)) + 1; x += 1) {
    for (let y = Math.floor(Math.min(...ys)) - 1; y <= Math.ceil(Math.max(...ys)) + 1; y += 1) {
      const p3 = [3 * x, 3 * y, -3 * x - 3 * y];
      const c1 = add(p3, add(cellE1, cellE2));
      const c2 = add(p3, add(cellE1.map(v => 2 * v), cellE2.map(v => 2 * v)));
      if (pointInPlacement(c1.map(v => v / 3), placement)) cells.push(key(c1));
      if (pointInPlacement(c2.map(v => v / 3), placement)) cells.push(key(c2));
    }
  }
  return cells;
}
function pairShapeKey(seed, turtle) { return [...tileCellKeys(seed), ...tileCellKeys(turtle)].sort().join(';'); }
function transformedCellKey(cellKey, op) {
  const cell = cellKey.split(',').map(Number);
  const transformed = add(transformLinear(cell, op.sym), op.translation.map(value => 3 * value));
  return key(transformed);
}
function interiors(verts) { const xs=verts.map(p=>p[0]), ys=verts.map(p=>p[1]), vkeys=new Set(verts.map(key)), poly=verts.map(projectRaw), out=[]; for(let x=Math.min(...xs);x<=Math.max(...xs);x++) for(let y=Math.min(...ys);y<=Math.max(...ys);y++){ const p=[x,y,-x-y]; if(!vkeys.has(key(p)) && pointInPoly(projectRaw(p), poly)) out.push(p); } return out; }
const turtleOcc = [...turtleVerts.map((p,i)=>({point:p,value:turtleAngles[i],kind:'vertex'})), ...interiors(turtleVerts).map(point=>({point,value:MAX,kind:'interior'}))];
const trefoilOcc = trefoilVerts.map((point,i)=>({point,value:trefoilAngles[i],kind:'vertex'}));
const turtleStripes = turtleStripeDefs.map(d=>({...d, p1:turtleVerts[d.from], p2:turtleVerts[d.to], component:componentFor(turtleVerts[d.from], turtleVerts[d.to])}));
const trefoilStripes = trefoilStripeDefs.map(d=>({...d, component:componentFor(d.p1,d.p2)}));
function orientTile(verts, occ, stripes, sym, idx, name) { const vertices=verts.map(p=>transformLinear(p,sym)); const occupancy=occ.map(e=>({...e, point:transformLinear(e.point,sym)})); const marks=[]; const segments=stripes.map(seg=>{ const p1=transformLinear(seg.p1,sym), p2=transformLinear(seg.p2,sym), component=mapComponent(seg.component,sym), value=seg.value*sym.planeSign; segmentPoints(p1,p2,markReach).forEach(point=>marks.push({point,component,value})); return {p1,p2,component,value}; }); return {idx,name,sym,isReflected:sym.planeSign < 0,vertices,occupancy,marks,segments}; }
const allSymmetries = symmetries();
const turtleOrientations = allSymmetries.map((s,i)=>orientTile(turtleVerts,turtleOcc,turtleStripes,s,i,'Turtle'));
const trefoilBase = orientTile(trefoilVerts,trefoilOcc,trefoilStripes,allSymmetries[0],0,'Trefoil');
function place(orientation, translation, extra={}) { return {...extra, orientation, isReflected: orientation.isReflected, translation, vertices:orientation.vertices.map(p=>add(p,translation)), occupancy:orientation.occupancy.map(e=>({...e,point:add(e.point,translation)})), marks:orientation.marks.map(e=>({...e,point:add(e.point,translation)})), segments:orientation.segments.map(s=>({...s,p1:add(s.p1,translation),p2:add(s.p2,translation)}))}; }
function transformPlacement(placement, op) { return {...placement, isReflected: (placement.isReflected || placement.orientation?.isReflected) !== (op.sym.planeSign < 0), vertices: placement.vertices.map(p=>transformAffine(p, op)), occupancy: placement.occupancy.map(e=>({...e, point: transformAffine(e.point, op)})), marks: placement.marks.map(e=>({...e, point: transformAffine(e.point, op), component: mapComponent(e.component, op.sym), value: e.value * op.sym.planeSign})), segments: placement.segments.map(s=>({...s, p1: transformAffine(s.p1, op), p2: transformAffine(s.p2, op), component: mapComponent(s.component, op.sym), value: s.value * op.sym.planeSign}))}; }
let view={scale:.72, x:canvas.width/2, y:canvas.height/2}, placements=[], coronas=[], legalMoveIndices=new Set(), fallbackMovesByIndex=new Map(), activeAnimation=null, hoveredIndex=-1;
const relativeMoveCache = new Map();
function mkey(e){return `${key(e.point)}|${e.component}`;}
function addPlacement(p,sums,markSums){ for(const e of p.occupancy){const k=key(e.point), old=sums.get(k)||{point:e.point,value:0}; old.value+=e.value; sums.set(k,old);} for(const e of p.marks){const k=mkey(e), old=markSums.get(k); if(old && old.value!==e.value) old.conflict=true; markSums.set(k,{value:e.value,count:(old?.count||0)+1, conflict:!!old?.conflict});}}
function frontier(sums){return [...sums.values()].filter(e=>e.value<MAX).sort((a,b)=>norm(a.point)-norm(b.point)||a.value-b.value);}
function validCandidate(o,t,sums,markSums,used){ const pk=`${o.idx}|${key(t)}`; if(used.has(pk)) return null; let newPts=0, overflow=0, line=0; const occ=o.occupancy.map(e=>({...e,point:add(e.point,t)})); for(const e of occ){ const cur=sums.get(key(e.point))?.value||0; if(cur===0)newPts++; overflow=Math.max(overflow,cur+e.value-MAX); } if(overflow>0||newPts===0) return null; const marks=o.marks.map(e=>({...e,point:add(e.point,t)})); for(const e of marks){ const old=markSums.get(mkey(e)); if(old){ if(old.value!==e.value) return null; if(e.value!==0) line++; }} return {orientation:o, translation:t, pk, score:line*100-newPts}; }
function buildPatch(limit=170){ placements=[place(trefoilBase,[0,0,0],{kind:'seed'})]; const sums=new Map(), markSums=new Map(), used=new Set(); addPlacement(placements[0],sums,markSums); for(let step=0; step<limit*40 && placements.length<limit; step++){ let best=null; for(const f of frontier(sums).slice(0,24)){ const need=MAX-f.value; for(const o of turtleOrientations){ for(const a of o.occupancy.filter(e=>e.value<=need)){ const cand=validCandidate(o, sub(f.point,a.point), sums, markSums, used); if(cand && (!best || cand.score>best.score)) best={...cand, frontier:f}; } } if(best?.score>=0) break; } if(!best) break; const p=place(best.orientation,best.translation,{kind:'turtle', placementKey:best.pk}); placements.push(p); used.add(best.pk); addPlacement(p,sums,markSums); }
 coronas=computeCoronas(); updateMoveHints(); statusEl.textContent=`Built ${placements.length-1} turtles; corona ${Math.max(...coronas.filter(Number.isFinite))}. Click a corona-1 turtle to try a legal move.`; draw(); }
function computeCoronas(){ const cs=placements.map((_,i)=>i===0?0:Infinity), byPoint=new Map(); placements.forEach((p,i)=>p.occupancy.forEach(e=>{const k=key(e.point); (byPoint.get(k)||byPoint.set(k,[]).get(k)).push(i);})); for(let q=[0],c=0;c<q.length;c++){ for(const e of placements[q[c]].occupancy){ for(const j of byPoint.get(key(e.point))||[]) if(cs[j]>cs[q[c]]+1){cs[j]=cs[q[c]]+1; q.push(j);} } } return cs; }
function screen(p){ const q=project(p); return {x:view.x+q.x*view.scale,y:view.y+q.y*view.scale}; }
function drawPolyScreen(points, fill, stroke, width=1.5){ ctx.beginPath(); points.forEach((s,i)=>{ i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y); }); ctx.closePath(); ctx.fillStyle=fill; ctx.fill(); ctx.strokeStyle=stroke; ctx.lineWidth=width; ctx.stroke(); }
function drawSegmentScreen(a, b, value) { ctx.strokeStyle=value>0?'#d55e00':'#0072b2'; ctx.setLineDash(value>0?[]:[6,5]); ctx.lineWidth=2.2; ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y); ctx.stroke(); ctx.setLineDash([]); }
function styleForPlacement(p) { const reflected = p.isReflected || p.orientation?.isReflected; return { fill: reflected ? 'rgba(213,94,0,.48)' : 'rgba(0,114,178,.42)', stroke: reflected ? '#a74700' : '#005a8c' }; }
function eased(value) { return value < 0.5 ? 2 * value * value : 1 - Math.pow(-2 * value + 2, 2) / 2; }
function lerp(a, b, t) { return a + (b - a) * t; }
function animatePoint(from, to, progress, animation) {
  const a = screen(from), b = screen(to), t = eased(progress);
  if (animation.op.kind === 'half-turn') {
    const c = screen(animation.center);
    const angle = Math.PI * t;
    const dx = a.x - c.x, dy = a.y - c.y;
    return { x: c.x + dx * Math.cos(angle) - dy * Math.sin(angle), y: c.y + dx * Math.sin(angle) + dy * Math.cos(angle) };
  }
  if (animation.axis) {
    const { point, unit } = animation.axis;
    const dx = a.x - point.x, dy = a.y - point.y;
    const parallel = dx * unit.x + dy * unit.y;
    const px = unit.x * parallel, py = unit.y * parallel;
    const qx = dx - px, qy = dy - py;
    const scale = 1 - 2 * t;
    return { x: point.x + px + qx * scale, y: point.y + py + qy * scale };
  }
  return { x: lerp(a.x, b.x, t), y: lerp(a.y, b.y, t) };
}
function reflectionAxisForOp(op) {
  const e1 = transformLinear([1, 0, -1], op.sym);
  const e2 = transformLinear([0, 1, -1], op.sym);
  const rows = [
    [1 - e1[0], -e2[0], op.translation[0]],
    [-e1[1], 1 - e2[1], op.translation[1]]
  ];
  const row = rows.sort((a, b) => (b[0] * b[0] + b[1] * b[1]) - (a[0] * a[0] + a[1] * a[1]))[0];
  const denom = row[0] * row[0] + row[1] * row[1];
  if (denom < 1e-9) return null;
  const point = [row[0] * row[2] / denom, row[1] * row[2] / denom];
  const direction = [-row[1], row[0]];
  const axisPoint = [point[0], point[1], -point[0] - point[1]];
  const axisToward = [point[0] + direction[0], point[1] + direction[1], -point[0] - point[1] - direction[0] - direction[1]];
  const a = screen(axisPoint), b = screen(axisToward);
  const length = Math.hypot(b.x - a.x, b.y - a.y);
  if (length < 1e-9) return null;
  return { point: a, unit: { x: (b.x - a.x) / length, y: (b.y - a.y) / length } };
}
function makeAnimation(fromSeed, fromClicked, toSeed, toClicked, clickedIndex, op) {
  const animation = { from: new Map([[0, fromSeed], [clickedIndex, fromClicked]]), to: new Map([[0, toSeed], [clickedIndex, toClicked]]), indices: new Set([0, clickedIndex]), clickedIndex, op, started: performance.now(), duration: 520, center: op.center || op.translation.map(value => value / 2), axis: null };
  if (op.kind === 'reflection') animation.axis = op.axis || reflectionAxisForOp(op);
  return animation;
}
function drawPlacement(p, index, points = p.vertices.map(screen), segments = p.segments.map(segment => ({ a: screen(segment.p1), b: screen(segment.p2), value: segment.value }))) {
  const style = styleForPlacement(p, index);
  drawPolyScreen(points, style.fill, style.stroke, hoveredIndex === index && legalMoveIndices.has(index) ? 4.2 : (index&&coronas[index]===1?2.2:1.5));
  if (marksToggle.checked) segments.forEach(segment => drawSegmentScreen(segment.a, segment.b, segment.value));
}
function drawAnimatedPlacement(index, progress) {
  const from = activeAnimation.from.get(index), to = activeAnimation.to.get(index);
  const points = from.vertices.map((point, i) => animatePoint(point, to.vertices[i], progress, activeAnimation));
  const segments = from.segments.map((segment, i) => ({ a: animatePoint(segment.p1, to.segments[i].p1, progress, activeAnimation), b: animatePoint(segment.p2, to.segments[i].p2, progress, activeAnimation), value: progress < 0.5 ? segment.value : to.segments[i].value }));
  drawPlacement(to, index, points, segments);
}
function draw(){ ctx.clearRect(0,0,canvas.width,canvas.height); if(gridToggle.checked) drawGrid(); let progress = 1; if (activeAnimation) progress = Math.min(1, (performance.now() - activeAnimation.started) / activeAnimation.duration); placements.forEach((p,i)=>{ if(activeAnimation?.indices.has(i)) drawAnimatedPlacement(i, progress); else drawPlacement(p, i); }); if(activeAnimation && progress < 1) window.requestAnimationFrame(draw); }
function drawGrid(){ ctx.fillStyle='rgba(20,60,55,.16)'; for(let x=-12;x<=12;x++) for(let y=-12;y<=12;y++){ const s=screen([x,y,-x-y]); ctx.beginPath(); ctx.arc(s.x,s.y,1.4,0,7); ctx.fill(); } }
function hitTile(ev){ const r=canvas.getBoundingClientRect(), pt={x:(ev.clientX-r.left)*canvas.width/r.width,y:(ev.clientY-r.top)*canvas.height/r.height}; for(let i=placements.length-1;i>0;i--){ if(coronas[i]!==1) continue; const poly=placements[i].vertices.map(screen); if(pointInPoly(pt, poly)) return i; } return -1; }
function relativeSignature(seed, turtle) {
  const anchor = seed.vertices[0];
  const seedShape = seed.vertices.map(point => key(sub(point, anchor))).sort().join(';');
  const turtleShape = turtle.vertices.map(point => key(sub(point, anchor))).sort().join(';');
  return `${seedShape}|${turtleShape}`;
}
function placementCentroid(placement) {
  return placement.vertices.reduce((sum, point) => add(sum, point), [0, 0, 0]).map(value => value / placement.vertices.length);
}
function cacheValueForMove(seed, move) {
  return {
    kind: move.op.kind,
    sign: move.op.sym.sign,
    permutation: move.op.sym.permutation,
    relativeTranslation: sub(move.op.translation, transformLinear(seed.vertices[0], move.op.sym)),
    relativeCenter: move.op.center ? sub(move.op.center, seed.vertices[0]) : null,
    axis: move.op.kind === 'reflection' ? true : false
  };
}
function opFromCache(seed, cached) {
  const sym = { sign: cached.sign, permutation: cached.permutation, planeSign: parity(cached.permutation) };
  const op = { sym, kind: cached.kind, translation: add(transformLinear(seed.vertices[0], sym), cached.relativeTranslation), center: cached.relativeCenter ? add(seed.vertices[0], cached.relativeCenter) : null, axis: null };
  if (op.kind === 'reflection' && cached.axis) op.axis = reflectionAxisForOp(op);
  return op;
}
function moveFromOp(clickedIndex, op) {
  if (op.kind === 'reflection' && !op.axis) op.axis = reflectionAxisForOp(op);
  const movedSeed = transformPlacement(placements[0], op);
  const movedClicked = transformPlacement(placements[clickedIndex], op);
  const next = placements.slice();
  next[0] = movedSeed;
  next[clickedIndex] = movedClicked;
  return { op, next, clickedIndex };
}
function shapeCellsForPair(seed, turtle) {
  return [...tileCellKeys(seed), ...tileCellKeys(turtle)];
}
function candidateLocalOps(seed, turtle) {
  const cells = shapeCellsForPair(seed, turtle);
  const cellSet = new Set(cells);
  const ops = [];
  for (const sym of allSymmetries) {
    const kind = symmetryKind(sym);
    if (kind === 'identity') continue;
    for (const sourceKey of cells) {
      const source = sourceKey.split(',').map(Number);
      const transformedSource = transformLinear(source, sym);
      for (const targetKey of cells) {
        const target = targetKey.split(',').map(Number);
        const delta = sub(target, transformedSource);
        if (delta.some(value => value % 3 !== 0)) continue;
        const translation = delta.map(value => value / 3);
        const op = { sym, kind, translation, center: null };
        if (cells.every(cellKey => cellSet.has(transformedCellKey(cellKey, op)))) ops.push(op);
      }
    }
  }
  const seen = new Set();
  return ops.filter(op => {
    const opKey = `${op.kind}|${op.sym.sign}|${op.sym.permutation.join(',')}|${key(op.translation)}`;
    if (seen.has(opKey)) return false;
    seen.add(opKey);
    return true;
  });
}
function tilingIsValid(nextPlacements) {
  const sums = new Map(), marks = new Map();
  for (const p of nextPlacements) addPlacement(p, sums, marks);
  for (const entry of sums.values()) if (entry.value > MAX) return false;
  for (const entry of marks.values()) if (entry.conflict) return false;
  return true;
}
function placementCoverage(placement) {
  const sums = new Map();
  placement.occupancy.forEach(entry => sums.set(key(entry.point), (sums.get(key(entry.point)) || 0) + entry.value));
  return sums;
}
function combinedCoverageKey(first, second) {
  const sums = placementCoverage(first);
  second.occupancy.forEach(entry => sums.set(key(entry.point), (sums.get(key(entry.point)) || 0) + entry.value));
  return [...sums.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([pointKey, value]) => `${pointKey}:${value}`).join(';');
}
function pairFitsSameHole(seed, clicked, move) {
  return pairShapeKey(seed, clicked) === pairShapeKey(move.next[0], move.next[move.clickedIndex]);
}
function validatorWithoutPair(clickedIndex) {
  const baseSums = new Map(), baseMarks = new Map();
  placements.forEach((placement, index) => {
    if (index !== 0 && index !== clickedIndex) addPlacement(placement, baseSums, baseMarks);
  });
  return move => {
    const pairSums = new Map(), pairMarks = new Map();
    addPlacement(move.next[0], pairSums, pairMarks);
    addPlacement(move.next[clickedIndex], pairSums, pairMarks);
    for (const [pointKey, entry] of pairSums) {
      if ((baseSums.get(pointKey)?.value || 0) + entry.value > MAX) return false;
    }
    for (const [markKey, entry] of pairMarks) {
      if (entry.conflict) return false;
      const base = baseMarks.get(markKey);
      if (base && (base.conflict || base.value !== entry.value)) return false;
    }
    return true;
  };
}
function moveDistance(move, clickedIndex) {
  const beforeSeed = placementCentroid(placements[0]);
  const beforeClicked = placementCentroid(placements[clickedIndex]);
  const afterSeed = placementCentroid(move.next[0]);
  const afterClicked = placementCentroid(move.next[clickedIndex]);
  const squared = (a, b) => (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2;
  return squared(beforeSeed, afterSeed) + squared(beforeClicked, afterClicked);
}
function fallbackCandidateOps(seed, turtle) {
  const pairVertices = [...seed.vertices, ...turtle.vertices];
  const pairCenter = pairVertices.reduce((sum, point) => add(sum, point), [0, 0, 0]).map(value => value / pairVertices.length);
  const ops = [];
  for (const sym of allSymmetries) {
    const kind = symmetryKind(sym);
    if (kind === 'identity') continue;
    const centerShift = sub(pairCenter, transformLinear(pairCenter, sym)).map(Math.round);
    for (let dx = -2; dx <= 2; dx += 1) {
      for (let dy = -2; dy <= 2; dy += 1) ops.push({ sym, kind, translation: add(centerShift, [dx, dy, -dx - dy]), center: pairCenter });
    }
  }
  const seen = new Set();
  return ops.filter(op => {
    const opKey = `${op.kind}|${op.sym.sign}|${op.sym.permutation.join(',')}|${key(op.translation)}`;
    if (seen.has(opKey)) return false;
    seen.add(opKey);
    return true;
  });
}
function nearestUnambiguousFallback(clickedIndex) {
  const isValidPairMove = validatorWithoutPair(clickedIndex);
  const moves = fallbackCandidateOps(placements[0], placements[clickedIndex]).map(op => moveFromOp(clickedIndex, op)).filter(isValidPairMove);
  if (!moves.length) return null;
  const scored = moves.map(move => ({ move, distance: moveDistance(move, clickedIndex) }));
  const best = Math.min(...scored.map(item => item.distance));
  return chooseUniqueMove(scored.filter(item => item.distance <= best + 1e-9 && item.distance <= 2).map(item => item.move));
}
function identifyFallbackMoves() {
  fallbackMovesByIndex = new Map();
  const seedCenter = placementCentroid(placements[0]);
  placements
    .map((placement, index) => ({ placement, index }))
    .filter(item => item.index > 0 && coronas[item.index] === 1)
    .map(item => {
      const delta = sub(placementCentroid(item.placement), seedCenter);
      const projected = project(delta);
      return { ...item, angle: Math.atan2(projected.y, projected.x) };
    })
    .sort((a, b) => a.angle - b.angle)
    .forEach((item, slot) => {
      if (slot % 2 !== 0) return;
      const move = nearestUnambiguousFallback(item.index);
      if (move) fallbackMovesByIndex.set(item.index, move);
    });
}
function chooseUniqueMove(moves) {
  const rotations = moves.filter(move => move.op.kind === 'half-turn' || move.op.kind === 'rotation');
  const reflections = moves.filter(move => move.op.kind === 'reflection');
  if (rotations.length && !reflections.length) return rotations[0];
  if (reflections.length && !rotations.length) return reflections[0];
  return null;
}
function localMoveFor(clickedIndex) {
  if (clickedIndex < 0) return null;
  const seed = placements[0], clicked = placements[clickedIndex];
  const signature = relativeSignature(seed, clicked);
  if (relativeMoveCache.has(signature)) {
    const cached = relativeMoveCache.get(signature);
    if (!cached) return fallbackMovesByIndex.get(clickedIndex) || null;
    const move = moveFromOp(clickedIndex, opFromCache(seed, cached));
    return pairFitsSameHole(seed, clicked, move) && validatorWithoutPair(clickedIndex)(move) ? move : (fallbackMovesByIndex.get(clickedIndex) || null);
  }
  const isValidPairMove = validatorWithoutPair(clickedIndex);
  const fittingMoves = candidateLocalOps(seed, clicked).map(op => moveFromOp(clickedIndex, op)).filter(move => pairFitsSameHole(seed, clicked, move) && isValidPairMove(move));
  const move = chooseUniqueMove(fittingMoves);
  relativeMoveCache.set(signature, move ? cacheValueForMove(seed, move) : null);
  return move || fallbackMovesByIndex.get(clickedIndex) || null;
}
function updateMoveHints() {
  legalMoveIndices = new Set();
  identifyFallbackMoves();
  for (let index = 1; index < placements.length; index += 1) {
    if (coronas[index] === 1 && localMoveFor(index)) legalMoveIndices.add(index);
  }
}
function finishAnimation(move) { activeAnimation = null; placements = move.next; coronas = computeCoronas(); updateMoveHints(); statusEl.textContent = `Applied one local ${move.op.kind}; all other turtles stayed fixed.`; draw(); }
function flipClicked(i){ if(activeAnimation) return; const move = localMoveFor(i); if(!move) { statusEl.textContent = i < 0 ? 'Click a corona-1 turtle.' : 'That neighboring turtle cannot be moved without breaking the tiling.'; return; } const fromSeed = placements[0], fromClicked = placements[i]; placements = move.next; legalMoveIndices = new Set(); hoveredIndex = -1; activeAnimation = makeAnimation(fromSeed, fromClicked, move.next[0], move.next[i], i, move.op); statusEl.textContent = `Animating local ${move.op.kind}...`; window.requestAnimationFrame(draw); window.setTimeout(() => finishAnimation(move), activeAnimation.duration + 30); }
function resizeCanvas() { const ratio = window.devicePixelRatio || 1; const rect = canvas.getBoundingClientRect(); const width = Math.max(1, Math.round(rect.width * ratio)); const height = Math.max(1, Math.round(rect.height * ratio)); if (canvas.width !== width || canvas.height !== height) { const old = {w:canvas.width, h:canvas.height}; canvas.width = width; canvas.height = height; view.x *= width / old.w; view.y *= height / old.h; } draw(); }
let dragging=false,last=null,down=null; canvas.addEventListener('pointerdown',e=>{dragging=true;last={x:e.clientX,y:e.clientY};down={...last}; canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{ if(!dragging){ const hit=hitTile(e); const nextHover=legalMoveIndices.has(hit)?hit:-1; if(nextHover!==hoveredIndex){ hoveredIndex=nextHover; draw(); } return; } const ratio=window.devicePixelRatio||1; view.x+=(e.clientX-last.x)*ratio; view.y+=(e.clientY-last.y)*ratio; last={x:e.clientX,y:e.clientY}; draw();});
canvas.addEventListener('pointerleave',()=>{ if(hoveredIndex!==-1){ hoveredIndex=-1; draw(); }});
canvas.addEventListener('pointerup',e=>{ if(down && Math.hypot(e.clientX-down.x,e.clientY-down.y)<4) flipClicked(hitTile(e)); dragging=false; down=null;});
canvas.addEventListener('wheel',e=>{ e.preventDefault(); const f=Math.exp(-e.deltaY*0.001); view.scale=Math.max(.12,Math.min(3.5,view.scale*f)); draw(); },{passive:false});
marksToggle.addEventListener('change',draw); gridToggle.addEventListener('change',draw); buildButton.addEventListener('click',()=>buildPatch()); resetButton.addEventListener('click',()=>{view={scale:.72,x:canvas.width/2,y:canvas.height/2};draw();});
window.addEventListener('resize', resizeCanvas);
buildPatch();
resizeCanvas();
