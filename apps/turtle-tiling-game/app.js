import { buildFrontierCandidateGraphSync, classifyFrontierCandidateGraph } from "../../assets/frontier-candidate-graph.js";

const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d');
const crossingCanvas = document.getElementById('crossingBoard');
const crossingCtx = crossingCanvas.getContext('2d');
const turtleSeedTab = document.getElementById('turtleSeedTab');
const tilingTab = document.getElementById('tilingTab');
const crossingTab = document.getElementById('crossingTab');
const symmetryButtons = [...document.querySelectorAll('.symmetry-toggle')];
const symmetryLabel = document.querySelector('.symmetry-label');
const trefoilTokens = [...document.querySelectorAll('.trefoil-token')];
const trefoilTrash = document.getElementById('trefoilTrash');
const BLUE = '#0072b2', BLUE_STROKE = '#005a8c', ORANGE = '#d55e00', ORANGE_STROKE = '#a74700';
let movingAttachment = null;
let activeTab = 'turtle', selectedSymmetry = 1, draggedTrefoilRotation = 0, draggedTrefoilColor = ORANGE, draggedTrefoilReflect = false, dragPreview = null, nextAttachmentId = 1;
let moveHintCache = new Map(), pairMoveCache = new Map(), viableMoveCache = new Map();
const tabStates = new Map();
let palettePointerDrag = null, pendingDragDraw = null;
const attachedTrefoils = { tiling: [], crossing: [] };
const statusEl = document.getElementById('status');
function setStatus(text = 'ready') { if (statusEl) statusEl.textContent = text; }
setStatus('ready');
const blueStripesToggle = document.getElementById('blueStripes');
const orangeStripesToggle = document.getElementById('orangeStripes');
const buildButton = document.getElementById('build');
const resetButton = document.getElementById('resetView');
const coronaTargetInput = document.getElementById('coronaTarget');

const sqrt2 = Math.sqrt(2), sqrt6 = Math.sqrt(6), latticeScale = 24;
const MAX = 12, markReach = 3;
const turtleVerts = [[3,-2,-1],[2,0,-2],[0,1,-1],[0,2,-2],[-1,3,-2],[-2,2,0],[-1,0,1],[-2,0,2],[-2,-1,3],[0,-2,2],[1,-4,3],[2,-4,2],[3,-5,2],[4,-4,0]];
const turtleAngles = [6,4,9,4,3,4,9,4,3,8,3,8,3,4];
const turtleStripeDefs = [{from:0,to:10,value:1},{from:2,to:8,value:-1},{from:0,to:6,value:-1},{from:4,to:12,value:-1}];
const trefoilVerts = [[1,0,-1],[2,0,-2],[2,1,-3],[0,2,-2],[-1,1,0],[-2,2,0],[-3,2,1],[-2,0,2],[0,-1,1],[0,-2,2],[1,-3,2],[2,-2,0]];
const trefoilAngles = [9,4,3,4,9,4,3,4,9,4,3,4];
const trefoilStripeDefs = [{p1:trefoilVerts[0],p2:trefoilVerts[6],value:-1},{p1:trefoilVerts[4],p2:trefoilVerts[10],value:-1},{p1:trefoilVerts[8],p2:trefoilVerts[2],value:-1}];
const centralHexVerts = [[1,1,-2],[0,2,-2],[-1,2,-1],[-2,2,0],[-2,1,1],[-2,0,2],[-1,-1,2],[0,-2,2],[1,-2,1],[2,-2,0],[2,-1,-1],[2,0,-2]];
const centralHexAngles = [6,4,6,4,6,4,6,4,6,4,6,4];
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

function interiors(verts) { const xs=verts.map(p=>p[0]), ys=verts.map(p=>p[1]), vkeys=new Set(verts.map(key)), poly=verts.map(projectRaw), out=[]; for(let x=Math.min(...xs);x<=Math.max(...xs);x++) for(let y=Math.min(...ys);y<=Math.max(...ys);y++){ const p=[x,y,-x-y]; if(!vkeys.has(key(p)) && pointInPoly(projectRaw(p), poly)) out.push(p); } return out; }
const turtleOcc = [...turtleVerts.map((p,i)=>({point:p,value:turtleAngles[i],kind:'vertex'})), ...interiors(turtleVerts).map(point=>({point,value:MAX,kind:'interior'}))];
const trefoilOcc = [...trefoilVerts.map((point,i)=>({point,value:trefoilAngles[i],kind:'vertex'})), ...interiors(trefoilVerts).map(point=>({point,value:MAX,kind:'interior'}))];
const centralHexOcc = [...centralHexVerts.map((point,i)=>({point,value:centralHexAngles[i],kind:'vertex'})), ...interiors(centralHexVerts).map(point=>({point,value:MAX,kind:'interior'}))];
const turtleStripes = turtleStripeDefs.map(d=>({...d, p1:turtleVerts[d.from], p2:turtleVerts[d.to], component:componentFor(turtleVerts[d.from], turtleVerts[d.to])}));
const trefoilStripes = trefoilStripeDefs.map(d=>({...d, component:componentFor(d.p1,d.p2)}));
function orientTile(verts, occ, stripes, sym, idx, name) { const vertices=verts.map(p=>transformLinear(p,sym)); const occupancy=occ.map(e=>({...e, point:transformLinear(e.point,sym)})); const marks=[]; const segments=stripes.map(seg=>{ const p1=transformLinear(seg.p1,sym), p2=transformLinear(seg.p2,sym), component=mapComponent(seg.component,sym), value=seg.value*sym.planeSign; segmentPoints(p1,p2,markReach).forEach(point=>marks.push({point,component,value})); return {p1,p2,component,value}; }); return {idx,name,sym,isReflected:sym.planeSign < 0,vertices,occupancy,marks,segments}; }
function segmentSignature(segment) { return [key(segment.p1), key(segment.p2)].sort().join('>') + `:${segment.value}`; }
function orientationSignature(orientation) { return `${orientation.vertices.map(key).sort().join(';')}|${orientation.segments.map(segmentSignature).sort().join(';')}`; }
function uniqueTileOrientations(orientations) {
  const seen = new Set(), unique = [];
  orientations.forEach(orientation => {
    const signature = orientationSignature(orientation);
    if (seen.has(signature)) return;
    seen.add(signature);
    unique.push({ ...orientation, idx: unique.length });
  });
  return unique;
}
const allSymmetries = symmetries();
const turtleOrientations = uniqueTileOrientations(allSymmetries.map((s,i)=>orientTile(turtleVerts,turtleOcc,turtleStripes,s,i,'Turtle')));
const unmarkedTurtleOrientations = uniqueTileOrientations(allSymmetries.map((s,i)=>orientTile(turtleVerts,turtleOcc,[],s,i,'Turtle')));
let currentTurtleOrientations = turtleOrientations, searchOrientations = turtleOrientations;
const trefoilOrientations = uniqueTileOrientations(allSymmetries.map((s,i)=>orientTile(trefoilVerts,trefoilOcc,trefoilStripes,s,i,'Trefoil')));
const trefoilBase = trefoilOrientations[0];
const centralHexBase = {idx:0, name:'Hex', sym:allSymmetries[0], isReflected:false, vertices:centralHexVerts, occupancy:centralHexOcc, marks:[], segments:[]};
function place(orientation, translation, extra={}) { return {...extra, orientation, isReflected: orientation.isReflected, translation, vertices:orientation.vertices.map(p=>add(p,translation)), occupancy:orientation.occupancy.map(e=>({...e,point:add(e.point,translation)})), marks:orientation.marks.map(e=>({...e,point:add(e.point,translation)})), segments:orientation.segments.map(s=>({...s,p1:add(s.p1,translation),p2:add(s.p2,translation)}))}; }
function transformPlacement(placement, op) { return {...placement, isReflected: placement.isReflected !== (op.sym.planeSign < 0), vertices: placement.vertices.map(p=>transformAffine(p, op)), occupancy: placement.occupancy.map(e=>({...e, point: transformAffine(e.point, op)})), marks: placement.marks.map(e=>({...e, point: transformAffine(e.point, op), component: mapComponent(e.component, op.sym), value: e.value * op.sym.planeSign})), segments: placement.segments.map(s=>({...s, p1: transformAffine(s.p1, op), p2: transformAffine(s.p2, op), component: mapComponent(s.component, op.sym), value: s.value * op.sym.planeSign}))}; }
function isTrefoilPlacement(placement) { return placement?.orientation?.name === 'Trefoil' || placement?.kind === 'attached-trefoil'; }
function isTurtlePlacement(placement) { return placement?.orientation?.name === 'Turtle' || placement?.kind === 'turtle' || placement?.kind === 'seed-turtle'; }
let view={scale:.72, x:canvas.width/2, y:canvas.height/2}, placements=[], coronas=[], legalMoveIndices=new Set(), activeAnimation=null, hoveredIndex=-1, moveHistory=[], historyStateKeys=[], resetting=false, buildVersion=0, revealVersion=0;
function mkey(e){return `${key(e.point)}|${e.component}`;}
function addPlacement(p,sums,markSums,addedDepth=0){ for(const e of p.occupancy){const k=key(e.point), old=sums.get(k)||{point:e.point,value:0,addedDepth}; old.value+=e.value; sums.set(k,old);} for(const e of p.marks){const k=mkey(e), old=markSums.get(k); if(old && old.value!==e.value) old.conflict=true; markSums.set(k,{value:e.value,count:(old?.count||0)+1, conflict:!!old?.conflict});}}
function frontier(sums){return [...sums.values()].filter(e=>e.value<MAX).sort((a,b)=>(a.addedDepth??0)-(b.addedDepth??0)||norm(a.point)-norm(b.point)||a.value-b.value);}
function validCandidate(o,t,sums,markSums,used){ const pk=`${o.name}|${o.idx}|${key(t)}`; if(used.has(pk)) return null; let newPts=0, overflow=0, line=0; const occ=o.occupancy.map(e=>({...e,point:add(e.point,t)})); for(const e of occ){ const cur=sums.get(key(e.point))?.value||0; if(cur===0)newPts++; overflow=Math.max(overflow,cur+e.value-MAX); } if(overflow>0||newPts===0) return null; const marks=o.marks.map(e=>({...e,point:add(e.point,t)})); for(const e of marks){ const old=markSums.get(mkey(e)); if(old){ if(old.value!==e.value) return null; if(e.value!==0) line++; }} return {orientation:o, translation:t, pk, score:line*100-newPts}; }
function frontierPointHasCandidate(point, sums, markSums, used) { const need = MAX - point.value; return searchOrientations.some(o => o.occupancy.some(a => a.value <= need && validCandidate(o, sub(point.point, a.point), sums, markSums, used))); }
function randomItem(items) { return items[Math.floor(Math.random() * items.length)]; }
function shuffled(items) { return items.map(value => ({ value, order: Math.random() })).sort((a, b) => a.order - b.order).map(entry => entry.value); }
function angleDiff(a, b) { return Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b))); }
function candidateMovesForFrontier(f, sums, markSums, used) {
  const need = MAX - f.value;
  const candidates = [];
  for (const o of searchOrientations) {
    for (const a of o.occupancy.filter(e => e.value <= need)) {
      const cand = validCandidate(o, sub(f.point, a.point), sums, markSums, used);
      if (cand) candidates.push({ ...cand, frontier: f });
    }
  }
  return candidates.sort((a, b) => b.score - a.score);
}
function placementCoronasFor(list){ const cs=list.map((_,i)=>i===0?0:Infinity), byPoint=new Map(); list.forEach((p,i)=>p.occupancy.forEach(e=>{const k=key(e.point); (byPoint.get(k)||byPoint.set(k,[]).get(k)).push(i);})); for(let q=[0],c=0;c<q.length;c++){ for(const e of list[q[c]].occupancy){ for(const j of byPoint.get(key(e.point))||[]) if(cs[j]>cs[q[c]]+1){cs[j]=cs[q[c]]+1; q.push(j);} } } return cs; }
function maxCoronaFor(list){ const finite=placementCoronasFor(list).filter(Number.isFinite); return finite.length ? Math.max(...finite) : 0; }
function removePlacement(p,sums,markSums){ for(const e of p.occupancy){ const k=key(e.point), old=sums.get(k); if(!old) continue; old.value-=e.value; if(old.value<=0)sums.delete(k); else sums.set(k,old); } for(const e of p.marks){ const k=mkey(e), old=markSums.get(k); if(!old) continue; if(old.count<=1) markSums.delete(k); else markSums.set(k,{...old,count:old.count-1,conflict:false}); } }
function candidateKeepsBoundaryAlive(candidate, sums, markSums, used) {
  const trial = place(candidate.orientation, candidate.translation, generatedPlacementExtra(candidate.orientation, { ...candidate, forced: false, branchCount: 1 }));
  addPlacement(trial, sums, markSums);
  used.add(candidate.pk);
  const affected = new Map();
  trial.occupancy.forEach(entry => { const current = sums.get(key(entry.point)); if (current && current.value < MAX) affected.set(key(entry.point), current); });
  const dead = [...affected.values()].some(point => !candidateMovesForFrontier(point, sums, markSums, used).length);
  used.delete(candidate.pk);
  removePlacement(trial, sums, markSums);
  return !dead;
}
function patchBoundaryGraph(sums, markSums, used) {
  const frontierItems = frontier(sums).slice(0, 12).map(frontierPoint => ({
    frontier: frontierPoint,
    pointKey: key(frontierPoint.point)
  }));
  const graph = buildFrontierCandidateGraphSync(
    frontierItems,
    item => candidateMovesForFrontier(item.frontier, sums, markSums, used),
    {
      frontierKey: item => item.pointKey,
      frontierNode: item => ({
        point: item.frontier.point.slice(),
        value: item.frontier.value,
        added_depth: item.frontier.addedDepth ?? 0
      }),
      candidateKey: candidate => candidate.pk,
      candidateNode: candidate => ({
        tile_name: candidate.orientation?.name,
        orientation_idx: candidate.orientation?.idx,
        translation: candidate.translation.slice(),
        score: candidate.score
      }),
      previewLimit: Infinity
    }
  );
  return classifyFrontierCandidateGraph(
    graph,
    (a, b) =>
      (a.frontier.addedDepth ?? 0) - (b.frontier.addedDepth ?? 0)
      || a.candidates.length - b.candidates.length
      || norm(a.frontier.point) - norm(b.frontier.point)
      || a.frontier.value - b.frontier.value
      || b.candidates[0].score - a.candidates[0].score
  );
}
function analyzePatchBoundary(sums, markSums, used) {
  const analysis = patchBoundaryGraph(sums, markSums, used);
  if (analysis.deadEnd) return { deadEnd: analysis.deadEnd, choice: null, forced: false, graph: analysis };
  if (analysis.forced.length) return { deadEnd: null, choice: analysis.forced[0], forced: true, graph: analysis };
  const ranked = analysis.branches;
  if (!ranked.length) return { deadEnd: null, choice: null, forced: false };
  const first = ranked[0];
  const tied = ranked.filter(option => (option.frontier.addedDepth ?? 0) === (first.frontier.addedDepth ?? 0) && option.candidates.length === first.candidates.length && norm(option.frontier.point) === norm(first.frontier.point) && option.frontier.value === first.frontier.value && option.candidates[0].score === first.candidates[0].score);
  return { deadEnd: null, choice: randomItem(tied), forced: false, graph: analysis };
}
function generatedPlacementExtra(orientation, candidate) {
  if (orientation.name === 'Trefoil') return { kind: 'attached-trefoil', color: orientation.isReflected ? ORANGE : BLUE, placementKey: candidate.pk, forced: candidate.forced, branchCount: candidate.branchCount };
  return { kind: 'turtle', placementKey: candidate.pk, forced: candidate.forced, branchCount: candidate.branchCount };
}
function generatePatch(seedPlacement, guardLimit=170, targetCorona=6, symmetryFold=1, relaxBoundary=false, tileOrientations=currentTurtleOrientations, forcedOnly=false) {
  const previousSearchOrientations = searchOrientations;
  searchOrientations = tileOrientations;
  const initialPlacements = Array.isArray(seedPlacement) ? seedPlacement.map(placement => ({ ...placement })) : [seedPlacement];
  const nextPlacements = initialPlacements.slice();
  const sums = new Map(), markSums = new Map(), used = new Set();
  let best = nextPlacements.slice(), bestCorona = 0, nodes = 0;
  const nodeBudget = Math.max(800, targetCorona * targetCorona * 16);
  const orbit = symmetryOrbitForFold(symmetryFold);
  nextPlacements.forEach((placement, index) => { addPlacement(placement, sums, markSums, index); if (placement.placementKey) used.add(placement.placementKey); });
  const rememberBest = () => { const candidateCorona = maxCoronaFor(nextPlacements); if (candidateCorona > bestCorona || (candidateCorona === bestCorona && nextPlacements.length > best.length)) { best = nextPlacements.slice(); bestCorona = candidateCorona; } };
  const candidateOrbit = (candidate, option, forced) => {
    const seen = new Set();
    return orbit.map((sym, orbitIndex) => {
      const placementKey = `${candidate.pk}|${orbitIndex}`;
      const base = place(candidate.orientation, candidate.translation, generatedPlacementExtra(candidate.orientation, { ...candidate, pk: placementKey, forced, branchCount: option.candidates.length }));
      return orbitIndex ? transformPlacement(base, { sym, translation: [0, 0, 0] }) : base;
    }).filter(placement => {
      const stateKey = placementStateKey(placement);
      if (seen.has(stateKey) || used.has(candidate.pk) || used.has(placement.placementKey)) return false;
      seen.add(stateKey);
      return true;
    });
  };
  const groupFits = group => placementsFitWithSums(group, sums, markSums);
  const applyCandidate = (candidate, option, forced) => {
    const group = candidateOrbit(candidate, option, forced);
    if (!group.length || !groupFits(group)) return null;
    used.add(candidate.pk);
    group.forEach(placement => {
      nextPlacements.push(placement);
      used.add(placement.placementKey);
      addPlacement(placement, sums, markSums, nextPlacements.length - 1);
    });
    return group;
  };
  const undoCandidate = group => {
    used.delete(group[0]?.placementKey?.split('|').slice(0, -1).join('|'));
    group.slice().reverse().forEach(placement => {
      removePlacement(placement, sums, markSums);
      used.delete(placement.placementKey);
      nextPlacements.pop();
    });
  };
  const search = () => {
    rememberBest();
    if (nextPlacements.length >= guardLimit) return bestCorona >= targetCorona;
    if (nodes++ >= nodeBudget) return false;
    const analysis = analyzePatchBoundary(sums, markSums, used);
    if (analysis.deadEnd || !analysis.choice) return false;
    if (forcedOnly && !analysis.forced) return true;
    if (!analysis.forced && bestCorona >= targetCorona) return true;
    const candidates = analysis.forced ? analysis.choice.candidates : shuffled(analysis.choice.candidates);
    for (const candidate of candidates) {
      if (!relaxBoundary && !candidateKeepsBoundaryAlive(candidate, sums, markSums, used)) continue;
      const group = applyCandidate(candidate, analysis.choice, analysis.forced);
      if (!group) continue;
      if (search()) return true;
      undoCandidate(group);
      if (nodes >= nodeBudget) break;
    }
    return false;
  };
  try {
    search();
    return best;
  } finally {
    searchOrientations = previousSearchOrientations;
  }
}
function readTargetCorona() { return Math.max(1, Math.min(12, Number(coronaTargetInput?.value) || 6)); }
function patchIntegrity() {
  const sums = new Map(), markSums = new Map(), used = new Set();
  placements.forEach(placement => { addPlacement(placement, sums, markSums); if (placement.placementKey) used.add(placement.placementKey); });
  const overfilled = [...sums.values()].filter(entry => entry.value > MAX).length;
  const markConflicts = [...markSums.values()].filter(entry => entry.conflict).length;
  const deadFrontier = frontier(sums).filter(point => !frontierPointHasCandidate(point, sums, markSums, used)).length;
  return { overfilled, markConflicts, deadFrontier };
}

function rotationSymmetryForDegrees(degrees) {
  const base = projectRaw([1, 0, -1]);
  const baseAngle = Math.atan2(base.y, base.x);
  const targetAngle = baseAngle + (degrees * Math.PI) / 180;
  return allSymmetries
    .filter(sym => sym.planeSign > 0)
    .reduce((best, candidate) => {
      const edge = projectRaw(transformLinear([1, 0, -1], candidate));
      const score = angleDiff(Math.atan2(edge.y, edge.x), targetAngle);
      return score < best.score ? { sym: candidate, score } : best;
    }, { sym: allSymmetries[0], score: Infinity }).sym;
}
function symmetryOrbitForFold(fold) {
  if (fold <= 1) return [allSymmetries[0]];
  return Array.from({ length: fold }, (_, index) => rotationSymmetryForDegrees(index * 360 / fold));
}
function placementsFitWithSums(group, sums, markSums) {
  const trialSums = new Map([...sums].map(([key, entry]) => [key, { ...entry }])), trialMarks = new Map([...markSums].map(([key, entry]) => [key, { ...entry }]));
  for (const placement of group) {
    addPlacement(placement, trialSums, trialMarks);
    if ([...trialSums.values()].some(entry => entry.value > MAX)) return false;
    if ([...trialMarks.values()].some(entry => entry.conflict)) return false;
  }
  return true;
}
function symmetrizePlacementsForHex(list) {
  const orbit = symmetryOrbitForFold(selectedSymmetry);
  const seen = new Set(), out = [], sums = new Map(), markSums = new Map();
  for (const placement of list) {
    const group = [];
    for (const sym of orbit) {
      const transformed = transformPlacement(placement, { sym, translation: [0, 0, 0] });
      const stateKey = placementStateKey(transformed);
      if (!seen.has(stateKey)) group.push({ placement: transformed, stateKey });
    }
    if (!placementsFitWithSums(group.map(entry => entry.placement), sums, markSums)) continue;
    for (const entry of group) {
      seen.add(entry.stateKey);
      out.push(entry.placement);
      addPlacement(entry.placement, sums, markSums);
    }
  }
  return out;
}

function generateTrefoilPass(basePlacements, guardLimit, symmetryFold) {
  return generatePatch(basePlacements, guardLimit, Infinity, symmetryFold, false, trefoilOrientations, true);
}
function finishPatchReveal(finalPlacements, version) {
  if (version !== buildVersion) return;
  revealVersion += 1;
  placements = finalPlacements;
  coronas = placementCoronasFor(placements);
  updateMoveHints();
  setStatus('ready');
  draw();
}
function revealPatch(finalPlacements, version) {
  const revealId = ++revealVersion;
  const finalCoronas = placementCoronasFor(finalPlacements);
  const finiteCoronas = finalCoronas.filter(Number.isFinite);
  const maxCorona = finiteCoronas.length ? Math.max(...finiteCoronas) : 0;
  let visibleCorona = 0;
  const revealNext = () => {
    if (version !== buildVersion || revealId !== revealVersion) return;
    placements = finalPlacements.filter((_, index) => (finalCoronas[index] ?? Infinity) <= visibleCorona);
    coronas = placementCoronasFor(placements);
    legalMoveIndices = new Set();
    setStatus('computing...');
    draw();
    if (visibleCorona < maxCorona) {
      visibleCorona += 1;
      window.setTimeout(revealNext, 90);
    }
  };
  revealNext();
}
function clearAttachedTrefoils() { attachedTrefoils.tiling = []; attachedTrefoils.crossing = []; dragPreview = null; movingAttachment = null; setTrashHot(false); }
function buildPatch(){
  clearAttachedTrefoils();
  const targetCorona = readTargetCorona();
  const guardLimit = Math.max(500, Math.ceil(targetCorona * targetCorona * 30));
  const version = ++buildVersion;
  currentTurtleOrientations = activeTab === 'crossing' ? unmarkedTurtleOrientations : turtleOrientations;
  const seed = activeTab === 'crossing' ? place(centralHexBase,[0,0,0],{kind:'hex-hole'}) : (activeTab === 'tiling' ? place(trefoilBase,[0,0,0],{kind:'seed'}) : place(turtleOrientations[0],[0,0,0],{kind:'seed'}));
  activeAnimation = null;
  resetting = false;
  moveHistory = [];
  historyStateKeys = [placementStateKey(seed)];
  placements = [seed];
  coronas = computeCoronas();
  legalMoveIndices = new Set();
  clearMoveHintCache();
  setStatus('computing...');
  draw();
  const buildAndReveal = (corona, limit) => {
    if (version !== buildVersion) return;
    setStatus('computing...');
    const generatedPlacements = generatePatch(seed, limit, corona, selectedSymmetry, activeTab === 'crossing');
    const isFinal = corona >= targetCorona;
    const finalPlacements = isFinal && activeTab !== 'crossing' ? generateTrefoilPass(generatedPlacements, guardLimit, selectedSymmetry) : generatedPlacements;
    if (isFinal) finishPatchReveal(finalPlacements, version);
    else revealPatch(finalPlacements, version);
  };
  const warmCorona = Math.min(targetCorona, 2);
  window.setTimeout(() => {
    buildAndReveal(warmCorona, Math.max(80, Math.ceil(warmCorona * warmCorona * 30)));
    if (targetCorona > warmCorona) window.setTimeout(() => buildAndReveal(targetCorona, guardLimit), 500);
  }, 0);
}
function clearMoveHintCache() { moveHintCache = new Map(); viableMoveCache = new Map(); }
function computeCoronas(){ return placementCoronasFor(placements); }
function placementStateKey(placement) { return placement.vertices.map(key).sort().join('|'); }
function rememberHistoryMove(move) {
  const stateKey = placementStateKey(placements[0]);
  const seenIndex = historyStateKeys.lastIndexOf(stateKey);
  if (seenIndex >= 0) {
    moveHistory = moveHistory.slice(0, seenIndex);
    historyStateKeys = historyStateKeys.slice(0, seenIndex + 1);
    return;
  }
  moveHistory.push({ indices: [...move.indices], clickedIndex: move.clickedIndex, op: cloneMoveOp(move.op) });
  historyStateKeys.push(stateKey);
}
function screen(p){ const q=project(p); return {x:view.x+q.x*view.scale,y:view.y+q.y*view.scale}; }
function drawPolyScreen(points, fill, stroke, width=1.5){ ctx.beginPath(); points.forEach((s,i)=>{ i?ctx.lineTo(s.x,s.y):ctx.moveTo(s.x,s.y); }); ctx.closePath(); ctx.fillStyle=fill; ctx.fill(); ctx.strokeStyle=stroke; ctx.lineWidth=width; ctx.stroke(); }
function drawSegmentOnContext(context, a, b, value) { context.strokeStyle=value>0?ORANGE:BLUE; context.setLineDash([]); context.lineWidth=2.2; context.beginPath(); context.moveTo(a.x,a.y); context.lineTo(b.x,b.y); context.stroke(); }
function drawSegmentScreen(a, b, value) { drawSegmentOnContext(ctx, a, b, value); }
function styleForPlacement(p) { if (p.color) return { fill: `${p.color}7a`, stroke: trefoilStrokeFor(p.color) }; const reflected = p.isReflected; return { fill: reflected ? 'rgba(213,94,0,.48)' : 'rgba(0,114,178,.42)', stroke: reflected ? ORANGE_STROKE : BLUE_STROKE }; }
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
function makeAnimationForMove(move, fromPlacements) {
  const from = new Map(), to = new Map();
  move.indices.forEach(index => { from.set(index, fromPlacements[index]); to.set(index, move.next[index]); });
  const animation = { from, to, indices: new Set(move.indices), clickedIndex: move.clickedIndex, op: move.op, started: performance.now(), duration: 520, center: move.op.center || move.op.translation.map(value => value / 2), axis: null };
  if (move.op.kind === 'reflection') animation.axis = move.op.axis || reflectionAxisForOp(move.op);
  return animation;
}
function drawPlacement(p, index, points = p.vertices.map(screen), segments = p.segments.map(segment => ({ a: screen(segment.p1), b: screen(segment.p2), value: segment.value })), styleOverride = null) {
  const style = styleOverride || styleForPlacement(p, index);
  drawPolyScreen(points, style.fill, style.stroke, index === 0 || legalMoveIndices.has(index) ? 4.2 : (index&&coronas[index]===1?2.0:1.5));
  if (activeTab !== 'crossing') segments.filter(segment => segment.value > 0 ? stripeEnabled(orangeStripesToggle) : stripeEnabled(blueStripesToggle)).forEach(segment => drawSegmentScreen(segment.a, segment.b, segment.value));
}
function drawAnimatedPlacement(index, progress) {
  const from = activeAnimation.from.get(index), to = activeAnimation.to.get(index);
  const points = from.vertices.map((point, i) => animatePoint(point, to.vertices[i], progress, activeAnimation));
  const showBackFace = activeAnimation.op.sym.planeSign < 0 && progress >= 0.5;
  const segments = from.segments.map((segment, i) => ({ a: animatePoint(segment.p1, to.segments[i].p1, progress, activeAnimation), b: animatePoint(segment.p2, to.segments[i].p2, progress, activeAnimation), value: showBackFace ? to.segments[i].value : segment.value }));
  drawPlacement(to, index, points, segments, showBackFace ? styleForPlacement(to) : styleForPlacement(from));
}
function drawCentralHexagon(context = ctx) {
  const points = centralHexVerts.map(screen);
  drawPath(context, points, '#f7faf8', '#15312c', 3);
}
function draw(){ ctx.clearRect(0,0,canvas.width,canvas.height); let progress = 1; if (activeAnimation) progress = Math.min(1, (performance.now() - activeAnimation.started) / activeAnimation.duration); placements.forEach((p,i)=>{ if(p.kind === 'hex-hole') return; if(activeAnimation?.indices.has(i)) drawAnimatedPlacement(i, progress); else drawPlacement(p, i); }); if (activeTab === 'crossing') drawCentralHexagon(); refreshAttachmentViability('tiling'); if (dragPreview?.tab === 'tiling') drawAttachedTrefoils(ctx, [dragPreview]); if(activeAnimation && progress < 1) window.requestAnimationFrame(draw); }
function hitTile(ev){ const r=canvas.getBoundingClientRect(), pt={x:(ev.clientX-r.left)*canvas.width/r.width,y:(ev.clientY-r.top)*canvas.height/r.height}; for(let i=placements.length-1;i>=0;i--){ if(!legalMoveIndices.has(i)) continue; const poly=placements[i].vertices.map(screen); if(pointInPoly(pt, poly)) return i; } return -1; }
function moveFromOpForPair(trefoilIndex, turtleIndex, op, clickedIndex = turtleIndex) {
  if (op.kind === 'reflection' && !op.axis) op.axis = reflectionAxisForOp(op);
  const next = placements.slice();
  next[trefoilIndex] = transformPlacement(placements[trefoilIndex], op);
  next[turtleIndex] = transformPlacement(placements[turtleIndex], op);
  return { op, next, clickedIndex, indices: [trefoilIndex, turtleIndex] };
}
function edgeKey(a, b) {
  const ka = key(a), kb = key(b);
  return ka < kb ? `${ka}|${kb}` : `${kb}|${ka}`;
}
function placementBoundaryEdges(placement) {
  const edges = new Map();
  const vertices = placement.vertices;
  for (let i = 0; i < vertices.length; i += 1) {
    const points = segmentPoints(vertices[i], vertices[(i + 1) % vertices.length]);
    for (let j = 0; j < points.length - 1; j += 1) {
      const ek = edgeKey(points[j], points[j + 1]);
      edges.set(ek, (edges.get(ek) || 0) + 1);
    }
  }
  return edges;
}

function sharedBoundaryEdgeCount(aPlacement, bPlacement) {
  const aEdges = placementBoundaryEdges(aPlacement), bEdges = placementBoundaryEdges(bPlacement);
  let shared = 0;
  aEdges.forEach((count, edge) => { if (count > 0 && (bEdges.get(edge) || 0) > 0) shared += 1; });
  return shared;
}
function boundaryPointsForOrientation(orientation) {
  const points = new Map();
  const vertices = orientation.vertices;
  for (let i = 0; i < vertices.length; i += 1) {
    segmentPoints(vertices[i], vertices[(i + 1) % vertices.length]).forEach(point => points.set(key(point), point));
  }
  return [...points.values()];
}
function normalizedMoveForCanonicalPair(trefoil, turtle) {
  const moves = outlineSymmetryOps(trefoil, turtle)
    .map(op => ({ op, next: [transformPlacement(trefoil, op), transformPlacement(turtle, op)], indices: [0, 1], clickedIndex: 1 }));
  const move = chooseUniqueMove(moves);
  return move ? cloneMoveOp(move.op) : null;
}
function buildViableRelativeMoveCache(turtleSet = turtleOrientations) {
  const cache = new Map(), ambiguous = new Set();
  for (const trefoilOrientation of trefoilOrientations) {
    const trefoil = place(trefoilOrientation, [0, 0, 0], { kind: 'attached-trefoil' });
    const trefoilBoundary = boundaryPointsForOrientation(trefoilOrientation);
    for (const turtleOrientation of turtleSet) {
      const turtleBoundary = boundaryPointsForOrientation(turtleOrientation);
      const translations = new Map();
      trefoilBoundary.forEach(trefoilPoint => {
        turtleBoundary.forEach(turtlePoint => {
          const translation = sub(trefoilPoint, turtlePoint);
          translations.set(key(translation), translation);
        });
      });
      translations.forEach(translation => {
        const turtle = place(turtleOrientation, translation, { kind: 'turtle' });
        if (!sharedBoundaryEdgeCount(trefoil, turtle)) return;
        const op = normalizedMoveForCanonicalPair(trefoil, turtle);
        if (!op) return;
        const pairKey = relativePlacementKey(trefoil, turtle);
        const opKey = `${op.sym.sign}|${op.sym.permutation.join(',')}|${key(op.translation)}`;
        if (cache.has(pairKey) && cache.get(pairKey).opKey !== opKey) ambiguous.add(pairKey);
        else cache.set(pairKey, { op, opKey });
      });
    }
  }
  ambiguous.forEach(pairKey => cache.delete(pairKey));
  return cache;
}
let viableRelativeMoveCache = null;
function getViableRelativeMoveCache() {
  if (!viableRelativeMoveCache) viableRelativeMoveCache = buildViableRelativeMoveCache(turtleOrientations);
  return viableRelativeMoveCache;
}

function pairOutlineEdges(aPlacement, bPlacement) {
  const edges = new Map();
  for (const placement of [aPlacement, bPlacement]) {
    for (const [ek, count] of placementBoundaryEdges(placement)) edges.set(ek, (edges.get(ek) || 0) + count);
  }
  return new Set([...edges.entries()].filter(([, count]) => count === 1).map(([ek]) => ek));
}
function transformEdgeKey(ek, op) {
  const [a, b] = ek.split('|').map(pointKey => pointKey.split(',').map(Number));
  return edgeKey(transformAffine(a, op), transformAffine(b, op));
}
function outlineSymmetryOps(aPlacement, bPlacement) {
  const outline = pairOutlineEdges(aPlacement, bPlacement);
  const outlinePoints = [...outline].flatMap(ek => ek.split('|')).map(pointKey => pointKey.split(',').map(Number));
  const ops = [];
  for (const sym of allSymmetries) {
    const kind = symmetryKind(sym);
    if (kind !== 'reflection' && kind !== 'half-turn') continue;
    for (const source of outlinePoints) {
      const transformedSource = transformLinear(source, sym);
      for (const target of outlinePoints) {
        const op = { sym, kind, translation: sub(target, transformedSource), center: null };
        if ([...outline].every(ek => outline.has(transformEdgeKey(ek, op)))) ops.push(op);
      }
    }
  }
  const seen = new Set();
  return ops.filter(op => {
    const opKey = `${op.sym.sign}|${op.sym.permutation.join(',')}|${key(op.translation)}`;
    if (seen.has(opKey)) return false;
    seen.add(opKey);
    return true;
  });
}
function relativePlacementKey(trefoil, turtle) {
  const relative = sub(turtle.translation || [0,0,0], trefoil.translation || [0,0,0]);
  return `${trefoil.orientation?.idx}|${trefoil.isReflected}|${turtle.orientation?.idx}|${turtle.isReflected}|${key(relative)}`;
}
function translatePlacementToOrigin(placement, origin) {
  return transformPlacement(placement, { sym: allSymmetries[0], translation: origin.map(value => -value) });
}
function translateOpFromOrigin(op, origin) {
  return { ...op, translation: add(origin, sub(op.translation, transformLinear(origin, op.sym))) };
}
function cachedOutlineSymmetryOps(trefoil, turtle) {
  const cacheKey = relativePlacementKey(trefoil, turtle);
  let normalizedOps = pairMoveCache.get(cacheKey);
  if (!normalizedOps) {
    const origin = trefoil.translation || [0,0,0];
    normalizedOps = outlineSymmetryOps(translatePlacementToOrigin(trefoil, origin), translatePlacementToOrigin(turtle, origin));
    pairMoveCache.set(cacheKey, normalizedOps);
  }
  return normalizedOps.map(op => translateOpFromOrigin(op, trefoil.translation || [0,0,0]));
}
function validatorWithoutPair(indexA, indexB) {
  const baseSums = new Map(), baseMarks = new Map();
  placements.forEach((placement, index) => {
    if (index !== indexA && index !== indexB) addPlacement(placement, baseSums, baseMarks);
  });
  return move => {
    const pairSums = new Map(), pairMarks = new Map();
    addPlacement(move.next[indexA], pairSums, pairMarks);
    addPlacement(move.next[indexB], pairSums, pairMarks);
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
function outlinePreservingMoveForPair(trefoilIndex, turtleIndex, clickedIndex) {
  if (!sharedBoundaryEdgeCount(placements[trefoilIndex], placements[turtleIndex])) return null;
  const cached = getViableRelativeMoveCache().get(relativePlacementKey(placements[trefoilIndex], placements[turtleIndex]));
  if (!cached) return null;
  const op = translateOpFromOrigin(cloneMoveOp(cached.op), placements[trefoilIndex].translation || [0, 0, 0]);
  const move = moveFromOpForPair(trefoilIndex, turtleIndex, op, clickedIndex);
  return validatorWithoutPair(trefoilIndex, turtleIndex)(move) ? move : null;
}
function chooseUniqueMove(moves) {
  const rotations = moves.filter(move => move.op.kind === 'half-turn' || move.op.kind === 'rotation');
  const reflections = moves.filter(move => move.op.kind === 'reflection');
  if (rotations.length === 1 && !reflections.length) return rotations[0];
  if (reflections.length === 1 && !rotations.length) return reflections[0];
  return null;
}
function neighboringTrefoilTurtlePairs() {
  const byPoint = new Map(), pairs = new Set();
  placements.forEach((placement, index) => {
    placement.occupancy.forEach(entry => {
      const pointKey = key(entry.point);
      if (!byPoint.has(pointKey)) byPoint.set(pointKey, []);
      byPoint.get(pointKey).push(index);
    });
  });
  byPoint.forEach(indices => {
    for (const a of indices) for (const b of indices) {
      if (a >= b) continue;
      const first = placements[a], second = placements[b];
      if (isTrefoilPlacement(first) && isTurtlePlacement(second)) pairs.add(`${a}|${b}`);
      if (isTurtlePlacement(first) && isTrefoilPlacement(second)) pairs.add(`${b}|${a}`);
    }
  });
  return [...pairs].map(pair => pair.split('|').map(Number));
}
function rebuildViableMoveCache() {
  viableMoveCache = new Map();
  const movesByTurtle = new Map();
  neighboringTrefoilTurtlePairs().forEach(([trefoilIndex, turtleIndex]) => {
    const move = outlinePreservingMoveForPair(trefoilIndex, turtleIndex, turtleIndex);
    if (!move) return;
    if (!movesByTurtle.has(turtleIndex)) movesByTurtle.set(turtleIndex, []);
    movesByTurtle.get(turtleIndex).push(move);
  });
  movesByTurtle.forEach((moves, turtleIndex) => {
    const move = chooseUniqueMove(moves);
    if (move) viableMoveCache.set(turtleIndex, move);
  });
}
function localMoveFor(clickedIndex) {
  if (clickedIndex < 0) return null;
  if (viableMoveCache.has(clickedIndex)) return viableMoveCache.get(clickedIndex);
  return null;
}
function updateMoveHints() {
  clearMoveHintCache();
  rebuildViableMoveCache();
  legalMoveIndices = new Set(viableMoveCache.keys());
}
function finishAnimation(move) { activeAnimation = null; placements = move.next; coronas = computeCoronas(); clearMoveHintCache(); updateMoveHints(); setStatus(move.op.kind === 'reflection' ? 'made a reflection' : 'made a half-turn'); draw(); }
function cloneMoveOp(op) { return { sym: op.sym, kind: op.kind, translation: [...op.translation], center: op.center ? [...op.center] : null }; }
function finishUserMove(move) { finishAnimation(move); rememberHistoryMove(move); }
function animateMove(move, onFinish = finishAnimation) {
  const fromPlacements = placements.slice();
  placements = move.next;
  legalMoveIndices = new Set();
  hoveredIndex = -1;
  activeAnimation = makeAnimationForMove(move, fromPlacements);
  setStatus(move.op.kind === 'reflection' ? 'made a reflection' : 'made a half-turn');
  window.requestAnimationFrame(draw);
  window.setTimeout(() => onFinish(move), activeAnimation.duration + 30);
}
function flipClicked(i){ if(activeAnimation || resetting) return; const move = localMoveFor(i); if(!move) { setStatus('blocked'); return; } animateMove(move, finishUserMove); }
function resetToCenter() {
  if (activeAnimation || resetting) return;
  if (!moveHistory.length) { view={scale:.72,x:canvas.width/2,y:canvas.height/2}; trefoilTokens.forEach(drawTrefoilToken); setStatus('ready'); draw(); return; }
  resetting = true;
  setStatus('resetting');
  const stepBack = () => {
    const previous = moveHistory.pop();
    if (previous) historyStateKeys.pop();
    if (!previous) { resetting = false; view={scale:.72,x:canvas.width/2,y:canvas.height/2}; trefoilTokens.forEach(drawTrefoilToken); updateMoveHints(); setStatus('ready'); draw(); return; }
    const [a, b] = previous.indices || [0, previous.clickedIndex];
    const trefoilIndex = isTrefoilPlacement(placements[a]) ? a : b;
    const turtleIndex = trefoilIndex === a ? b : a;
    const move = moveFromOpForPair(trefoilIndex, turtleIndex, { ...previous.op }, previous.clickedIndex);
    animateMove(move, () => { finishAnimation(move); window.setTimeout(stepBack, 80); });
  };
  stepBack();
}

function polygonPoints(cx, cy, radius, sides, rotation = 0) {
  return Array.from({ length: sides }, (_, index) => {
    const angle = rotation + (Math.PI * 2 * index) / sides;
    return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius };
  });
}
function drawPath(context, points, fill, stroke = '#15312c', width = 2) {
  context.beginPath();
  points.forEach((point, index) => index ? context.lineTo(point.x, point.y) : context.moveTo(point.x, point.y));
  context.closePath();
  context.fillStyle = fill;
  context.fill();
  context.strokeStyle = stroke;
  context.lineWidth = width;
  context.stroke();
}

function transformedTrefoilPoints(rotation = 0, scale = 1, reflect = false) {
  const raw = trefoilVerts.map(project);
  const cx = raw.reduce((sum, point) => sum + point.x, 0) / raw.length;
  const cy = raw.reduce((sum, point) => sum + point.y, 0) / raw.length;
  const angle = (rotation * Math.PI) / 180;
  return raw.map(point => {
    const x = (point.x - cx) * scale * (reflect ? -1 : 1), y = (point.y - cy) * scale;
    return { x: x * Math.cos(angle) - y * Math.sin(angle), y: x * Math.sin(angle) + y * Math.cos(angle) };
  });
}
function trefoilStrokeFor(color) { return color === BLUE ? BLUE_STROKE : ORANGE_STROKE; }
function drawTrefoilShape(context, x, y, rotation = 0, scale = 0.38, color = ORANGE, reflect = false) {
  const points = transformedTrefoilPoints(rotation, scale, reflect);
  context.save();
  context.translate(x, y);
  drawPath(context, points, color, trefoilStrokeFor(color), 2.2);
  context.restore();
}
function drawTrefoilTokenStripes(context, x, y, rotation = 0, scale = 0.28, reflect = false, fillColor = null) {
  const points = transformedTrefoilPoints(rotation, scale, reflect);
  const mapVertex = vertex => points[trefoilVerts.findIndex(point => key(point) === key(vertex))];
  context.save();
  context.translate(x, y);
  context.lineWidth = 2;
  trefoilStripeDefs.forEach(def => {
    const value = def.value * (reflect ? -1 : 1);
    if (value > 0 && !stripeEnabled(orangeStripesToggle)) return;
    if (value < 0 && !stripeEnabled(blueStripesToggle)) return;
    const a = mapVertex(def.p1), b = mapVertex(def.p2);
    if (!a || !b) return;
    const stripeColor = value > 0 ? ORANGE : BLUE;
    context.lineCap = 'round';
    context.strokeStyle = '#fffdf8';
    context.lineWidth = 4.2;
    context.beginPath();
    context.moveTo(a.x, a.y);
    context.lineTo(b.x, b.y);
    context.stroke();
    context.strokeStyle = stripeColor;
    context.lineWidth = 2.4;
    context.beginPath();
    context.moveTo(a.x, a.y);
    context.lineTo(b.x, b.y);
    context.stroke();
  });
  context.restore();
}

function strokeTrefoilShape(context, x, y, rotation = 0, scale = 0.46, stroke = 'rgba(44,160,44,.75)', reflect = false) {
  const points = transformedTrefoilPoints(rotation, scale, reflect);
  context.save();
  context.translate(x, y);
  context.beginPath();
  points.forEach((point, index) => index ? context.lineTo(point.x, point.y) : context.moveTo(point.x, point.y));
  context.closePath();
  context.strokeStyle = stroke;
  context.lineWidth = 5;
  context.stroke();
  context.restore();
}
function drawTrefoilToken(button) {
  const context = button.getContext('2d');
  const ratio = window.devicePixelRatio || 1;
  const cssSize = Math.max(132, Math.ceil(150 * view.scale / 0.72));
  button.style.width = `${cssSize}px`;
  button.style.height = `${cssSize}px`;
  const pixelSize = Math.round(cssSize * ratio);
  if (button.width !== pixelSize || button.height !== pixelSize) { button.width = pixelSize; button.height = pixelSize; }
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, cssSize, cssSize);
  const rotation = Number(button.dataset.rotation) || 0, reflect = button.dataset.reflect === 'true';
  const color = button.dataset.color || ORANGE;
  drawFloatingTrefoil(context, { x: cssSize / 2, y: cssSize / 2, rotation, reflect, color });
}

const trefoilTokenOrientationCache = new Map();
function trefoilOrientationForToken(rotation = 0, reflect = false) {
  const cacheKey = `${rotation}|${reflect}`;
  if (trefoilTokenOrientationCache.has(cacheKey)) return trefoilTokenOrientationCache.get(cacheKey);
  const target = transformedTrefoilPoints(rotation, 1, reflect);
  const candidates = allSymmetries.filter(sym => (sym.planeSign < 0) === reflect);
  const sym = candidates.reduce((best, candidate) => {
    const raw = trefoilVerts.map(point => project(transformLinear(point, candidate)));
    const cx = raw.reduce((sum, point) => sum + point.x, 0) / raw.length;
    const cy = raw.reduce((sum, point) => sum + point.y, 0) / raw.length;
    const points = raw.map(point => ({ x: point.x - cx, y: point.y - cy }));
    const score = target.reduce((sum, point) => sum + Math.min(...points.map(candidatePoint => Math.hypot(point.x - candidatePoint.x, point.y - candidatePoint.y))), 0);
    return score < best.score ? { sym: candidate, score } : best;
  }, { sym: candidates[0], score: Infinity }).sym;
  const orientation = orientTile(trefoilVerts, trefoilOcc, trefoilStripes, sym, trefoilTokenOrientationCache.size, 'Trefoil');
  trefoilTokenOrientationCache.set(cacheKey, orientation);
  return orientation;
}
function trefoilTilePlacement(item) {
  return place(trefoilOrientationForToken(item.rotation, !!item.reflect), item.translation || [0, 0, 0], { kind: 'attached-trefoil', color: item.color || ORANGE, attachmentId: item.attachmentId });
}
function syncAttachedTrefoilPlacement(item, updateHints = true) {
  const index = placements.findIndex(placement => placement.attachmentId === item.attachmentId);
  if (index >= 0) placements[index] = trefoilTilePlacement(item);
  coronas = computeCoronas();
  if (updateHints) { clearMoveHintCache(); updateMoveHints(); }
}
function trefoilCentroidOffset(item) {
  const orientation = trefoilOrientationForToken(item.rotation, !!item.reflect);
  const points = orientation.vertices.map(project);
  return points.reduce((sum, point) => ({ x: sum.x + point.x / points.length, y: sum.y + point.y / points.length }), { x: 0, y: 0 });
}
function latticePointForTrefoilCenter(point, item) {
  const offset = trefoilCentroidOffset(item);
  return latticePointForCanvasPoint({ x: point.x - offset.x * view.scale, y: point.y - offset.y * view.scale });
}
function drawFloatingTrefoil(context, item) {
  const offset = trefoilCentroidOffset(item);
  const origin = { x: item.x - offset.x * view.scale, y: item.y - offset.y * view.scale };
  const tile = trefoilTilePlacement({ ...item, translation: [0, 0, 0] });
  const toFloating = point => { const projected = project(point); return { x: origin.x + projected.x * view.scale, y: origin.y + projected.y * view.scale }; };
  const style = styleForPlacement(tile);
  drawPath(context, tile.vertices.map(toFloating), style.fill, style.stroke, 2.2);
  tile.segments
    .filter(segment => segment.value > 0 ? stripeEnabled(orangeStripesToggle) : stripeEnabled(blueStripesToggle))
    .forEach(segment => drawSegmentOnContext(context, toFloating(segment.p1), toFloating(segment.p2), segment.value));
}
function drawTrefoilTile(context, item) {
  const tile = trefoilTilePlacement(item);
  const style = styleForPlacement(tile);
  drawPath(context, tile.vertices.map(screen), style.fill, style.stroke, 2.2);
  tile.segments
    .filter(segment => segment.value > 0 ? stripeEnabled(orangeStripesToggle) : stripeEnabled(blueStripesToggle))
    .forEach(segment => drawSegmentOnContext(context, screen(segment.p1), screen(segment.p2), segment.value));
}
function drawCrossingPiece(context, x, y, kind, color) {
  context.save();
  context.translate(x, y);
  if (kind === 'trefoil') {
    drawTrefoilShape(context, 0, 0, 0, 0.34, color);
  } else {
    drawPath(context, polygonPoints(0, 0, 17, 6, Math.PI / 6), color, '#005a8c', 2);
  }
  context.restore();
}
function drawTrefoilCrossing() {
  const context = crossingCtx;
  context.clearRect(0, 0, crossingCanvas.width, crossingCanvas.height);
  const previousView = view;
  view = { ...view, x: crossingCanvas.width / 2, y: crossingCanvas.height / 2 };
  drawCentralHexagon(context);
  view = previousView;
}



function saveTabState(tab = activeTab) {
  tabStates.set(tab, {
    placements: placements.slice(),
    coronas: coronas.slice(),
    legalMoveIndices: new Set(legalMoveIndices),
    attachedTiling: attachedTrefoils.tiling.map(item => ({ ...item, translation: item.translation ? [...item.translation] : item.translation })),
    attachedCrossing: attachedTrefoils.crossing.map(item => ({ ...item })),
    view: { ...view },
    selectedSymmetry
  });
}
function restoreTabState(tab) {
  const state = tabStates.get(tab);
  if (!state) return false;
  placements = state.placements.slice();
  coronas = state.coronas.slice();
  legalMoveIndices = new Set(state.legalMoveIndices);
  attachedTrefoils.tiling = state.attachedTiling.map(item => ({ ...item, translation: item.translation ? [...item.translation] : item.translation }));
  attachedTrefoils.crossing = state.attachedCrossing.map(item => ({ ...item }));
  view = { ...state.view };
  selectedSymmetry = state.selectedSymmetry || selectedSymmetry;
  clearMoveHintCache();
  return true;
}

function allowedSymmetriesForTab(tab) {
  if (tab === 'turtle') return [1];
  if (tab === 'tiling') return [1, 3];
  if (tab === 'crossing') return [1, 2, 3, 6];
  return [1];
}
function updateSymmetryAvailability() {
  const allowed = allowedSymmetriesForTab(activeTab);
  const onlyTrivial = allowed.length === 1 && allowed[0] === 1;
  if (!allowed.includes(selectedSymmetry)) selectedSymmetry = allowed[0];
  if (symmetryLabel) symmetryLabel.hidden = onlyTrivial;
  symmetryButtons.forEach(button => {
    const value = Number(button.dataset.symmetry) || 1;
    const isAllowed = allowed.includes(value) && !onlyTrivial;
    button.hidden = !isAllowed;
    button.disabled = !isAllowed;
    button.setAttribute('aria-pressed', value === selectedSymmetry ? 'true' : 'false');
  });
}
function showTab(nextTab) {
  if (nextTab === activeTab) return;
  const hadSavedState = tabStates.has(nextTab);
  const savedSymmetry = tabStates.get(nextTab)?.selectedSymmetry;
  saveTabState(activeTab);
  activeTab = nextTab;
  selectedSymmetry = hadSavedState ? (savedSymmetry || selectedSymmetry) : Math.max(...allowedSymmetriesForTab(activeTab));
  updateSymmetryAvailability();
  const showCrossing = activeTab === 'crossing';
  canvas.classList.remove('hidden');
  crossingCanvas.classList.add('hidden');
  turtleSeedTab.setAttribute('aria-pressed', activeTab === 'turtle' ? 'true' : 'false');
  tilingTab.setAttribute('aria-pressed', activeTab === 'tiling' ? 'true' : 'false');
  crossingTab.setAttribute('aria-pressed', showCrossing ? 'true' : 'false');
  buildButton.textContent = 'Initialize tiling';
  trefoilTokens.forEach(drawTrefoilToken);
  if (restoreTabState(activeTab)) draw();
  else buildPatch();
}


function drawAttachedTrefoils(context, items) {
  items.forEach(item => {
    if (item.translation && !item.previewOnly) {
      drawTrefoilTile(context, item);
      return;
    }
    drawFloatingTrefoil(context, item);
  });
}
function placementScreenCenter(placement) {
  const points = placement.vertices.map(screen);
  return points.reduce((sum, point) => ({ x: sum.x + point.x / points.length, y: sum.y + point.y / points.length }), { x: 0, y: 0 });
}
function refreshAttachmentViability(tab) {
  if (tab === 'crossing') { attachedTrefoils.crossing.forEach(item => { item.viable = true; }); return; }
  const centers = [...legalMoveIndices].map(index => placementScreenCenter(placements[index]));
  attachedTrefoils.tiling.forEach(item => {
    const itemCenter = item.translation ? screen(item.translation) : item;
    item.viable = centers.some(center => Math.hypot(center.x - itemCenter.x, center.y - itemCenter.y) < 150);
  });
}

function scheduleBoardRedraw(targetCanvas = canvas) {
  if (pendingDragDraw) return;
  pendingDragDraw = targetCanvas;
  window.requestAnimationFrame(() => {
    const target = pendingDragDraw;
    pendingDragDraw = null;
    target === crossingCanvas ? drawTrefoilCrossing() : draw();
  });
}
function eventPointOnCanvas(event, targetCanvas) {
  const rect = targetCanvas.getBoundingClientRect();
  const scaleX = targetCanvas.width / rect.width, scaleY = targetCanvas.height / rect.height;
  return { x: (event.clientX - rect.left) * scaleX, y: (event.clientY - rect.top) * scaleY };
}
function latticePointForCanvasPoint(point) {
  const world = { x: (point.x - view.x) / view.scale, y: (point.y - view.y) / view.scale };
  const a = project([1,0,-1]), b = project([0,1,-1]);
  const det = a.x * b.y - a.y * b.x || 1;
  const u = Math.round((world.x * b.y - world.y * b.x) / det);
  const v = Math.round((a.x * world.y - a.y * world.x) / det);
  return [u, v, -u - v];
}
function snapToLattice(point, targetCanvas) {
  if (targetCanvas === crossingCanvas) {
    const cx = targetCanvas.width / 2, cy = targetCanvas.height / 2 + 10;
    const r = Math.round((point.y - cy) / 30);
    const q = Math.round((point.x - cx) / 34 - r / 2);
    return { x: cx + (q + r / 2) * 34, y: cy + r * 30 };
  }
  return screen(latticePointForCanvasPoint(point));
}
function trefoilAttachmentFor(event, targetCanvas, { snap = false } = {}) {
  const point = eventPointOnCanvas(event, targetCanvas);
  const base = { rotation: draggedTrefoilRotation, color: draggedTrefoilColor, reflect: draggedTrefoilReflect, viable: true, tab: targetCanvas === crossingCanvas ? 'crossing' : 'tiling' };
  if (targetCanvas === crossingCanvas) return { ...base, ...(snap ? snapToLattice(point, targetCanvas) : point) };
  const translation = latticePointForTrefoilCenter(point, base);
  return snap ? { ...base, translation } : { ...base, x: point.x, y: point.y, translation, previewOnly: true };
}
function updateDragPreview(event, targetCanvas) {
  event.preventDefault();
  dragPreview = trefoilAttachmentFor(event, targetCanvas);
  scheduleBoardRedraw(targetCanvas);
}
function attachTrefoilAt(event, targetCanvas) {
  event.preventDefault();
  const tab = targetCanvas === crossingCanvas ? 'crossing' : 'tiling';
  const attachment = trefoilAttachmentFor(event, targetCanvas, { snap: true });
  delete attachment.tab;
  attachment.attachmentId = nextAttachmentId++;
  attachedTrefoils[tab].push(attachment);
  if (tab === 'tiling' && attachment.translation) {
    placements.push(trefoilTilePlacement(attachment));
    coronas = computeCoronas();
    updateMoveHints();
  }
  dragPreview = null;
  refreshAttachmentViability(tab);
  setStatus('snapped');
  targetCanvas === crossingCanvas ? drawTrefoilCrossing() : draw();
}


function pointInTrash(event) {
  if (!trefoilTrash) return false;
  const rect = trefoilTrash.getBoundingClientRect();
  return event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
}
function setTrashHot(isHot) { trefoilTrash?.classList.toggle('trash-hot', !!isHot); }
function hitAttachedTrefoil(event, targetCanvas) {
  const tab = targetCanvas === crossingCanvas ? 'crossing' : 'tiling';
  const point = eventPointOnCanvas(event, targetCanvas);
  const items = attachedTrefoils[tab];
  for (let index = items.length - 1; index >= 0; index -= 1) {
    const item = items[index];
    const center = item.translation ? screen(item.translation) : item;
    if (Math.hypot(point.x - center.x, point.y - center.y) <= 72) return { tab, index, item, targetCanvas };
  }
  return null;
}
function updateDraggedAttachmentFromEvent(item, event, targetCanvas) {
  const point = eventPointOnCanvas(event, targetCanvas);
  item.previewOnly = true;
  item.x = point.x;
  item.y = point.y;
  if (targetCanvas === crossingCanvas) return;
  item.translation = latticePointForTrefoilCenter(point, item);
}
function removeAttachedPlacement(item) {
  if (!item?.attachmentId) return;
  placements = placements.filter(placement => placement.attachmentId !== item.attachmentId);
  coronas = computeCoronas();
}
function restoreDraggedAttachment() {
  if (!movingAttachment?.original) return;
  Object.assign(movingAttachment.item, movingAttachment.original);
  if (movingAttachment.tab === 'tiling') placements.push(trefoilTilePlacement(movingAttachment.item));
}
function finishDraggedAttachmentItem(item, event, targetCanvas) {
  if (targetCanvas === crossingCanvas) Object.assign(item, snapToLattice(eventPointOnCanvas(event, targetCanvas), targetCanvas));
  delete item.previewOnly;
  if (targetCanvas !== crossingCanvas) { delete item.x; delete item.y; }
}
function startAttachmentDrag(event, targetCanvas) {
  const hit = hitAttachedTrefoil(event, targetCanvas);
  if (!hit) return false;
  event.preventDefault();
  movingAttachment = { ...hit, pointerId: event.pointerId, original: { ...hit.item, translation: hit.item.translation ? [...hit.item.translation] : hit.item.translation } };
  dragPreview = null;
  if (hit.tab === 'tiling') removeAttachedPlacement(hit.item);
  updateDraggedAttachmentFromEvent(hit.item, event, targetCanvas);
  targetCanvas.setPointerCapture?.(event.pointerId);
  setStatus('drag trefoil');
  scheduleBoardRedraw(targetCanvas);
  return true;
}
function moveAttachmentDrag(event) {
  if (!movingAttachment || event.pointerId !== movingAttachment.pointerId) return false;
  event.preventDefault();
  const { item, targetCanvas } = movingAttachment;
  updateDraggedAttachmentFromEvent(item, event, targetCanvas);
  setTrashHot(pointInTrash(event));
  scheduleBoardRedraw(targetCanvas);
  return true;
}
function endAttachmentDrag(event) {
  if (!movingAttachment || event.pointerId !== movingAttachment.pointerId) return false;
  event.preventDefault();
  const { tab, index, item, targetCanvas } = movingAttachment;
  if (pointInTrash(event)) {
    attachedTrefoils[tab].splice(index, 1);
    if (tab === 'tiling') { clearMoveHintCache(); updateMoveHints(); }
    setStatus('deleted');
  } else {
    updateDraggedAttachmentFromEvent(item, event, targetCanvas);
    finishDraggedAttachmentItem(item, event, targetCanvas);
    if (tab === 'tiling') {
      placements.push(trefoilTilePlacement(item));
      coronas = computeCoronas();
      clearMoveHintCache();
      updateMoveHints();
    }
    refreshAttachmentViability(tab);
    setStatus('snapped');
  }
  movingAttachment = null;
  setTrashHot(false);
  targetCanvas === crossingCanvas ? drawTrefoilCrossing() : draw();
  return true;
}
function cancelAttachmentDrag(event) {
  if (!movingAttachment || event.pointerId !== movingAttachment.pointerId) return false;
  const { targetCanvas } = movingAttachment;
  restoreDraggedAttachment();
  movingAttachment = null;
  setTrashHot(false);
  clearMoveHintCache();
  updateMoveHints();
  targetCanvas === crossingCanvas ? drawTrefoilCrossing() : draw();
  return true;
}

function resizeCanvas() { const ratio = window.devicePixelRatio || 1; const rect = canvas.getBoundingClientRect(); const width = Math.max(1, Math.round(rect.width * ratio)); const height = Math.max(1, Math.round(rect.height * ratio)); if (canvas.width !== width || canvas.height !== height) { const old = {w:canvas.width, h:canvas.height}; canvas.width = width; canvas.height = height; view.x *= width / old.w; view.y *= height / old.h; } draw(); }
let dragging=false,last=null,down=null; canvas.addEventListener('pointerdown',e=>{ if(startAttachmentDrag(e, canvas)){ dragging=false; down=null; return; } dragging=true;last={x:e.clientX,y:e.clientY};down={...last}; canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{ if(moveAttachmentDrag(e)) return; if(!dragging){ const hit=hitTile(e); const nextHover=legalMoveIndices.has(hit)?hit:-1; if(nextHover!==hoveredIndex){ hoveredIndex=nextHover; draw(); } return; } const ratio=window.devicePixelRatio||1; view.x+=(e.clientX-last.x)*ratio; view.y+=(e.clientY-last.y)*ratio; last={x:e.clientX,y:e.clientY}; draw();});
canvas.addEventListener('pointerleave',()=>{ if(hoveredIndex!==-1){ hoveredIndex=-1; draw(); }});
canvas.addEventListener('pointerup',e=>{ if(endAttachmentDrag(e)) return; if(down && Math.hypot(e.clientX-down.x,e.clientY-down.y)<4) flipClicked(hitTile(e)); dragging=false; down=null;});
crossingCanvas.addEventListener('pointerdown', e => startAttachmentDrag(e, crossingCanvas));
crossingCanvas.addEventListener('pointermove', e => moveAttachmentDrag(e));
crossingCanvas.addEventListener('pointerup', e => endAttachmentDrag(e));
canvas.addEventListener('pointercancel', e => cancelAttachmentDrag(e));
crossingCanvas.addEventListener('pointercancel', e => cancelAttachmentDrag(e));
canvas.addEventListener('wheel',e=>{ e.preventDefault(); const f=Math.exp(-e.deltaY*0.001); view.scale=Math.max(.12,Math.min(3.5,view.scale*f)); trefoilTokens.forEach(drawTrefoilToken); draw(); },{passive:false});
function stripeEnabled(button) { return button?.getAttribute('aria-pressed') === 'true'; }
function toggleStripe(button) { button.setAttribute('aria-pressed', stripeEnabled(button) ? 'false' : 'true'); trefoilTokens.forEach(drawTrefoilToken); draw(); }
trefoilTokens.forEach(drawTrefoilToken);
function canvasUnderPointer(event) {
  const visibleCanvases = [canvas, crossingCanvas].filter(target => !target.classList.contains('hidden'));
  return visibleCanvases.find(target => {
    const rect = target.getBoundingClientRect();
    return event.clientX >= rect.left && event.clientX <= rect.right && event.clientY >= rect.top && event.clientY <= rect.bottom;
  }) || null;
}
function beginPalettePointerDrag(event, button) {
  event.preventDefault();
  draggedTrefoilRotation = Number(button.dataset.rotation) || 0;
  draggedTrefoilColor = button.dataset.color || ORANGE;
  draggedTrefoilReflect = button.dataset.reflect === 'true';
  palettePointerDrag = { pointerId: event.pointerId };
  document.addEventListener('pointermove', movePalettePointerDrag);
  document.addEventListener('pointerup', endPalettePointerDrag, { once: true });
  document.addEventListener('pointercancel', cancelPalettePointerDrag, { once: true });
  updatePaletteDragPreview(event);
  setStatus('drag trefoil');
}
function updatePaletteDragPreview(event) {
  const target = canvasUnderPointer(event);
  if (target) {
    updateDragPreview(event, target);
    setTrashHot(false);
  } else {
    const previousTarget = dragPreview?.tab === 'crossing' ? crossingCanvas : canvas;
    dragPreview = null;
    setTrashHot(pointInTrash(event));
    scheduleBoardRedraw(previousTarget);
  }
}
function movePalettePointerDrag(event) {
  if (!palettePointerDrag || event.pointerId !== palettePointerDrag.pointerId) return false;
  event.preventDefault();
  updatePaletteDragPreview(event);
  return true;
}
function finishPalettePointerDrag() {
  document.removeEventListener('pointermove', movePalettePointerDrag);
  palettePointerDrag = null;
  setTrashHot(false);
}
function cancelPalettePointerDrag(event) {
  if (!palettePointerDrag || event.pointerId !== palettePointerDrag.pointerId) return;
  finishPalettePointerDrag();
  dragPreview = null;
  setStatus('ready');
  draw();
  if (activeTab === 'crossing') drawTrefoilCrossing();
}
function endPalettePointerDrag(event) {
  if (!palettePointerDrag || event.pointerId !== palettePointerDrag.pointerId) return false;
  event.preventDefault();
  const target = canvasUnderPointer(event);
  finishPalettePointerDrag();
  if (pointInTrash(event)) { dragPreview = null; setStatus('deleted'); draw(); return true; }
  if (!target) { dragPreview = null; setStatus('drop on board'); draw(); if (activeTab === 'crossing') drawTrefoilCrossing(); return true; }
  attachTrefoilAt(event, target);
  return true;
}
trefoilTokens.forEach(button => {
  button.addEventListener('pointerdown', event => beginPalettePointerDrag(event, button));
  button.addEventListener('dragstart', event => event.preventDefault());
  button.addEventListener('click', () => { draggedTrefoilRotation = Number(button.dataset.rotation) || 0; draggedTrefoilColor = button.dataset.color || ORANGE; draggedTrefoilReflect = button.dataset.reflect === 'true'; setStatus('drag trefoil'); });
});
trefoilTrash?.addEventListener('dragover', event => { event.preventDefault(); dragPreview = null; setTrashHot(true); });
trefoilTrash?.addEventListener('dragleave', () => setTrashHot(false));
trefoilTrash?.addEventListener('drop', event => { event.preventDefault(); dragPreview = null; setTrashHot(false); setStatus('deleted'); draw(); if (activeTab === 'crossing') drawTrefoilCrossing(); });
blueStripesToggle.addEventListener('click',()=>toggleStripe(blueStripesToggle)); orangeStripesToggle.addEventListener('click',()=>toggleStripe(orangeStripesToggle)); symmetryButtons.forEach(button => button.addEventListener('click', () => { if (button.disabled) return; selectedSymmetry = Number(button.dataset.symmetry) || 1; updateSymmetryAvailability(); buildPatch(); })); buildButton.addEventListener('click',()=>buildPatch()); coronaTargetInput?.addEventListener('change',()=>buildPatch()); resetButton.addEventListener('click', resetToCenter); turtleSeedTab.addEventListener('click',()=>showTab('turtle')); tilingTab.addEventListener('click',()=>showTab('tiling')); crossingTab.addEventListener('click',()=>showTab('crossing'));
window.addEventListener('resize', resizeCanvas);
updateSymmetryAvailability();
resizeCanvas();
setStatus('computing...');
window.setTimeout(() => buildPatch(), 60);
