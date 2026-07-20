import { buildFrontierCandidateGraphSync, classifyFrontierCandidateGraph } from "../../assets/frontier-candidate-graph.js";
import { A2_TILE_LOOPS } from "../../assets/a2-tiling-engine.js";

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
let activeTab = 'tiling', selectedSymmetry = 1, draggedTrefoilRotation = 0, draggedTrefoilColor = ORANGE, draggedTrefoilReflect = false, dragPreview = null, nextAttachmentId = 1;
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
const onlineLearningToggle = document.getElementById('onlineLearning');
const learnedFailuresEl = document.getElementById('learnedFailures');
const learnedMarksEl = document.getElementById('learnedMarks');
const memoHitsEl = document.getElementById('memoHits');
const learningMessageEl = document.getElementById('learningMessage');
const learningLogEl = document.getElementById('learningLog');
const fillTileButtons = [...document.querySelectorAll('.fill-tile-button')];
const customTileButton = document.getElementById('customTileButton');
const customTileDialog = document.getElementById('customTileDialog');
const closeCustomTileButton = document.getElementById('closeCustomTileButton');
const customTileCanvas = document.getElementById('customTileCanvas');
const customTileCtx = customTileCanvas?.getContext('2d');
const customTileNameInput = document.getElementById('customTileName');
const customVertexCountEl = document.getElementById('customVertexCount');
const customAreaEl = document.getElementById('customArea');
const customTileValidationEl = document.getElementById('customTileValidation');
const undoCustomPointButton = document.getElementById('undoCustomPoint');
const clearCustomTileButton = document.getElementById('clearCustomTile');
const useCustomTileButton = document.getElementById('useCustomTile');
const customPresetButtons = [...document.querySelectorAll('[data-custom-preset]')];

const sqrt2 = Math.sqrt(2), sqrt6 = Math.sqrt(6), latticeScale = 24;
const MAX = 12, EPS = 1e-7, markReach = 3;
const turtleVerts = A2_TILE_LOOPS.turtle;
const turtleAngles = [6,4,9,4,3,4,9,4,3,8,3,8,3,4];
const turtleStripeDefs = [{from:0,to:10,value:1},{from:2,to:8,value:-1},{from:0,to:6,value:-1},{from:4,to:12,value:-1}];
const hatVerts = A2_TILE_LOOPS.hat;
const hatAngles = [3,4,9,4,3,8,3,8,3,4,6,4,9,4];
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
function polygonArea(verts) {
  const points = verts.map(projectRaw);
  return points.reduce((area,point,index) => { const next=points[(index+1)%points.length]; return area+point.x*next.y-next.x*point.y; },0)/2/(latticeScale*latticeScale);
}
function normalizedLoop(verts) {
  if (!verts.length) return [];
  const origin=verts[0], shifted=verts.map(point=>sub(point,origin));
  return polygonArea(shifted)<0 ? [shifted[0],...shifted.slice(1).reverse()] : shifted;
}
function customCornerAngles(verts) {
  const points=verts.map(projectRaw), orientation=Math.sign(polygonArea(verts))||1;
  return points.map((point,index) => {
    const previous=points[(index-1+points.length)%points.length], next=points[(index+1)%points.length];
    const incoming={x:point.x-previous.x,y:point.y-previous.y}, outgoing={x:next.x-point.x,y:next.y-point.y};
    let turn=Math.atan2(incoming.x*outgoing.y-incoming.y*outgoing.x,incoming.x*outgoing.x+incoming.y*outgoing.y);
    if (orientation<0) turn=-turn;
    let interior=Math.PI-turn;
    if (interior<=0) interior+=Math.PI*2;
    return Math.round((interior*6/Math.PI)*1e9)/1e9;
  });
}
function boundaryIntermediatePoints(verts) {
  const vertexKeys=new Set(verts.map(key)), points=new Map();
  verts.forEach((point,index) => segmentPoints(point,verts[(index+1)%verts.length]).forEach(entry => { if(!vertexKeys.has(key(entry))) points.set(key(entry),entry); }));
  return [...points.values()];
}
function polygonOccupancy(verts, explicitAngles=null) {
  const angles=explicitAngles||customCornerAngles(verts);
  return [
    ...verts.map((point,index)=>({point,value:angles[index],kind:'vertex'})),
    ...boundaryIntermediatePoints(verts).map(point=>({point,value:6,kind:'edge'})),
    ...interiors(verts).map(point=>({point,value:MAX,kind:'interior'}))
  ];
}
const turtleOcc = [...turtleVerts.map((p,i)=>({point:p,value:turtleAngles[i],kind:'vertex'})), ...interiors(turtleVerts).map(point=>({point,value:MAX,kind:'interior'}))];
const hatOcc = polygonOccupancy(hatVerts,hatAngles);
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
const hatOrientations = uniqueTileOrientations(allSymmetries.map((s,i)=>orientTile(hatVerts,hatOcc,[],s,i,'Hat')));
let activeFillTile = 'turtle';
let hasCustomTile = false;
let customTileLoop = normalizedLoop([[0,0,0],[3,0,-3],[3,2,-5],[1,3,-4],[-1,2,-1]]);
let customTileLabel = 'My lattice tile';
let customDraftLoop = customTileLoop.map(point=>[...point]);
let customDraftClosed = true;
let customDraftHover = null;
let customTileOrientations = [];
function customTileName() { return customTileLabel; }
function rebuildCustomTileOrientations() {
  const loop=normalizedLoop(customTileLoop);
  const occupancy=polygonOccupancy(loop);
  customTileOrientations=uniqueTileOrientations(allSymmetries.map((sym,index)=>orientTile(loop,occupancy,[],sym,index,customTileName())));
}
rebuildCustomTileOrientations();
function baseFillOrientations() {
  if (activeFillTile==='hat') return hatOrientations;
  if (activeFillTile==='custom') return customTileOrientations;
  return unmarkedTurtleOrientations;
}
function fixedFillOrientations() { return activeFillTile==='turtle' ? turtleOrientations : baseFillOrientations(); }
function fillOccupancy() { return baseFillOrientations()[0]?.occupancy||[]; }
function fillTileDisplayName() { return activeFillTile==='custom' ? customTileName() : activeFillTile[0].toUpperCase()+activeFillTile.slice(1); }
let currentTurtleOrientations = turtleOrientations, searchOrientations = turtleOrientations;
const trefoilOrientations = uniqueTileOrientations(allSymmetries.map((s,i)=>orientTile(trefoilVerts,trefoilOcc,trefoilStripes,s,i,'Trefoil')));
const unmarkedTrefoilOrientations = uniqueTileOrientations(allSymmetries.map((s,i)=>orientTile(trefoilVerts,trefoilOcc,[],s,i,'Trefoil')));
const trefoilBase = trefoilOrientations[0];
const unmarkedTrefoilBase = unmarkedTrefoilOrientations[0];
const centralHexBase = {idx:0, name:'Hex', sym:allSymmetries[0], isReflected:false, vertices:centralHexVerts, occupancy:centralHexOcc, marks:[], segments:[]};

class SignedUnionFind {
  constructor(names) {
    this.parent = new Map(names.map(name => [name, name]));
    this.sign = new Map(names.map(name => [name, 1]));
  }
  find(name) {
    const parent = this.parent.get(name);
    if (parent === name) return { root: name, sign: 1 };
    const found = this.find(parent);
    const sign = this.sign.get(name) * found.sign;
    this.parent.set(name, found.root);
    this.sign.set(name, sign);
    return { root: found.root, sign };
  }
  union(left, right, relation) {
    const a = this.find(left), b = this.find(right);
    if (a.root === b.root) return a.sign === relation * b.sign;
    if (a.root < b.root) {
      this.parent.set(b.root, a.root);
      this.sign.set(b.root, relation * a.sign * b.sign);
    } else {
      this.parent.set(a.root, b.root);
      this.sign.set(a.root, relation * b.sign * a.sign);
    }
    return true;
  }
}

const onlineMemory = { support:new Map(), assignments:new Map(), failures:[], memoHits:0, skipped:0, events:[] };
function onlineMode() { return !!onlineLearningToggle?.checked; }
function resetOnlineMemory() {
  onlineMemory.support = new Map();
  onlineMemory.assignments = new Map();
  onlineMemory.failures = [];
  onlineMemory.memoHits = 0;
  onlineMemory.skipped = 0;
  onlineMemory.events = [];
  updateLearningReadout('Empty marking: geometric search has not memoized a failure yet.');
}
function updateLearningReadout(message) {
  if (learnedFailuresEl) learnedFailuresEl.textContent = String(onlineMemory.failures.length);
  if (learnedMarksEl) learnedMarksEl.textContent = String(onlineMemory.support.size);
  if (memoHitsEl) memoHitsEl.textContent = String(onlineMemory.memoHits);
  if (learningMessageEl && message) learningMessageEl.textContent = message;
  if (learningLogEl) learningLogEl.innerHTML = onlineMemory.events.map(event => {
    if (event.type === 'memoized') return `<li>Failure ${event.failure}: added ${event.added.length} witness ${event.added.length===1?'entry':'entries'}; replayed ${event.accepted} placements.</li>`;
    if (event.type === 'memo-hit') return `<li>${event.count} geometric ${event.count===1?'trial':'trials'} rejected by the current marking.</li>`;
    return `<li>Accepted Turtle ${event.accepted}; prefix replay remains valid.</li>`;
  }).join('');
}
function inverseTransformLinear(point, sym) {
  const out = [0,0,0];
  sym.permutation.forEach((sourceIndex, outputIndex) => { out[sourceIndex] = sym.sign * point[outputIndex]; });
  return out;
}
function localMarkName(point, component) { return `${key(point)}|${component}`; }
function localMark(point, component) { return { name:localMarkName(point, component), point:[...point], component }; }
function fillPlacementOnly(list) { return list.filter(isFillPlacement); }
function orientedOnlineEntries(placement, support=onlineMemory.support, assignments=onlineMemory.assignments) {
  const sym = placement.orientation.sym;
  return [...support.values()].map(mark => {
    const globalPoint = add(transformLinear(mark.point, sym), placement.translation || [0,0,0]);
    const globalComponent = mapComponent(mark.component, sym);
    const baseValue = assignments.get(mark.name);
    return {
      name:mark.name,
      contactKey:`${key(globalPoint)}|${globalComponent}`,
      value:baseValue == null ? null : baseValue * sym.planeSign
    };
  });
}
function assignmentsForAccepted(support, acceptedPlacements) {
  const names = [...support.keys()];
  const union = new SignedUnionFind(names);
  const contacts = new Map();
  for (const placement of fillPlacementOnly(acceptedPlacements)) {
    const sym = placement.orientation.sym;
    for (const mark of support.values()) {
      const globalPoint = add(transformLinear(mark.point, sym), placement.translation || [0,0,0]);
      const contactKey = `${key(globalPoint)}|${mapComponent(mark.component, sym)}`;
      const entry = { name:mark.name, coefficient:sym.planeSign };
      const previous = contacts.get(contactKey);
      if (previous && !union.union(entry.name, previous.name, entry.coefficient * previous.coefficient)) return null;
      if (!previous) contacts.set(contactKey, entry);
    }
  }
  const rootMagnitude = new Map(), assignments = new Map();
  let nextMagnitude = 1;
  for (const name of names.sort()) {
    const found = union.find(name);
    if (!rootMagnitude.has(found.root)) rootMagnitude.set(found.root, nextMagnitude++);
    assignments.set(name, found.sign * rootMagnitude.get(found.root));
  }
  return assignments;
}
function onlineContactMap(placements, support, assignments) {
  const map = new Map();
  for (const placement of fillPlacementOnly(placements)) {
    for (const entry of orientedOnlineEntries(placement, support, assignments)) {
      if (!map.has(entry.contactKey)) map.set(entry.contactKey, entry.value);
    }
  }
  return map;
}
function failureHasMismatch(record, support, assignments) {
  const previous = onlineContactMap(record.parents, support, assignments);
  const orientation = baseFillOrientations()[record.orientationIdx];
  const candidate = { orientation, translation:record.translation };
  return orientedOnlineEntries(candidate, support, assignments).some(entry => previous.has(entry.contactKey) && previous.get(entry.contactKey) !== entry.value);
}
function allFailuresEncoded(failures, support, assignments) {
  return failures.every(record => failureHasMismatch(record, support, assignments));
}
function learnedTurtleOrientations(support=onlineMemory.support, assignments=onlineMemory.assignments) {
  return baseFillOrientations().map(orientation => ({
    ...orientation,
    marks:[...support.values()].map(mark => ({
      point:transformLinear(mark.point, orientation.sym),
      component:mapComponent(mark.component, orientation.sym),
      value:(assignments.get(mark.name) || 0) * orientation.sym.planeSign
    })),
    segments:[]
  }));
}
function replayWithOnlineMarking(list, orientations=learnedTurtleOrientations()) {
  const sums = new Map(), markSums = new Map(), replayed = [];
  try {
    for (const placement of list) {
      const next = isFillPlacement(placement)
        ? place(orientations[placement.orientation.idx], placement.translation, { ...placement, orientation:undefined, vertices:undefined, occupancy:undefined, marks:undefined, segments:undefined })
        : placement;
      addPlacement(next, sums, markSums, replayed.length);
      if ([...markSums.values()].some(entry => entry.conflict)) return null;
      replayed.push(next);
    }
  } catch (_) {
    return null;
  }
  return replayed;
}
function witnessExtensions(record) {
  const candidateOrientation = baseFillOrientations()[record.orientationIdx];
  const witnesses = new Map();
  const candidateTranslation = record.translation;
  for (const previous of fillPlacementOnly(record.parents)) {
    const previousSym = previous.orientation.sym;
    for (const point of fillOccupancy().map(entry => entry.point)) {
      const globalPoint = add(transformLinear(point, candidateOrientation.sym), candidateTranslation);
      const previousLocal = inverseTransformLinear(sub(globalPoint, previous.translation || [0,0,0]), previousSym);
      for (let component=0; component<3; component+=1) {
        const globalComponent = mapComponent(component, candidateOrientation.sym);
        const previousComponent = [0,1,2].find(value => mapComponent(value, previousSym) === globalComponent);
        const additions = [localMark(point, component), localMark(previousLocal, previousComponent)]
          .filter(mark => !onlineMemory.support.has(mark.name));
        if (!additions.length) continue;
        const signature = additions.map(mark => mark.name).sort().join('::');
        witnesses.set(signature, additions);
      }
    }
  }
  return [...witnesses.values()].sort((a,b) => a.length-b.length || Math.max(...a.map(mark=>norm(mark.point)))-Math.max(...b.map(mark=>norm(mark.point))));
}
function learnOnlineFailure(candidate, acceptedPlacements) {
  const record = {
    orientationIdx:candidate.orientation.idx,
    translation:[...candidate.translation],
    placementKey:candidate.pk,
    parents:acceptedPlacements.map(placement => ({ ...placement }))
  };
  const failures = [...onlineMemory.failures, record];
  for (const additions of witnessExtensions(record)) {
    const support = new Map(onlineMemory.support);
    additions.forEach(mark => support.set(mark.name, mark));
    const assignments = assignmentsForAccepted(support, acceptedPlacements);
    if (!assignments || !allFailuresEncoded(failures, support, assignments)) continue;
    const replayed = replayWithOnlineMarking(acceptedPlacements, learnedTurtleOrientations(support, assignments));
    if (!replayed) continue;
    onlineMemory.support = support;
    onlineMemory.assignments = assignments;
    onlineMemory.failures = failures;
    onlineMemory.events.push({ type:'memoized', failure:failures.length, placementKey:candidate.pk, added:additions.map(mark=>mark.name), accepted:acceptedPlacements.length });
    updateLearningReadout(`Failure ${failures.length} encoded by ${additions.length} new local witness${additions.length===1?'':'es'}; ${acceptedPlacements.length} accepted placements replayed.`);
    return true;
  }
  onlineMemory.skipped += 1;
  return false;
}
function place(orientation, translation, extra={}) { return {...extra, orientation, isReflected: orientation.isReflected, translation, vertices:orientation.vertices.map(p=>add(p,translation)), occupancy:orientation.occupancy.map(e=>({...e,point:add(e.point,translation)})), marks:orientation.marks.map(e=>({...e,point:add(e.point,translation)})), segments:orientation.segments.map(s=>({...s,p1:add(s.p1,translation),p2:add(s.p2,translation)}))}; }
function transformPlacement(placement, op) { return {...placement, isReflected: placement.isReflected !== (op.sym.planeSign < 0), vertices: placement.vertices.map(p=>transformAffine(p, op)), occupancy: placement.occupancy.map(e=>({...e, point: transformAffine(e.point, op)})), marks: placement.marks.map(e=>({...e, point: transformAffine(e.point, op), component: mapComponent(e.component, op.sym), value: e.value * op.sym.planeSign})), segments: placement.segments.map(s=>({...s, p1: transformAffine(s.p1, op), p2: transformAffine(s.p2, op), component: mapComponent(s.component, op.sym), value: s.value * op.sym.planeSign}))}; }
function isTrefoilPlacement(placement) { return placement?.orientation?.name === 'Trefoil' || placement?.kind === 'attached-trefoil'; }
function isTurtlePlacement(placement) { return placement?.orientation?.name === 'Turtle' || placement?.kind === 'turtle' || placement?.kind === 'seed-turtle'; }
function isFillPlacement(placement) { return placement?.orientation?.name === baseFillOrientations()[0]?.name || placement?.kind === 'fill-tile' || (activeFillTile==='turtle'&&isTurtlePlacement(placement)); }
let view={scale:.72, x:canvas.width/2, y:canvas.height/2}, placements=[], coronas=[], legalMoveIndices=new Set(), activeAnimation=null, hoveredIndex=-1, moveHistory=[], historyStateKeys=[], resetting=false, buildVersion=0, revealVersion=0;
function mkey(e){return `${key(e.point)}|${e.component}`;}
function addPlacement(p,sums,markSums,addedDepth=0){ for(const e of p.occupancy){const k=key(e.point), old=sums.get(k)||{point:e.point,value:0,addedDepth}; old.value=Math.round((old.value+e.value)*1e9)/1e9; sums.set(k,old);} for(const e of p.marks){const k=mkey(e), old=markSums.get(k); if(old && old.value!==e.value) old.conflict=true; markSums.set(k,{value:e.value,count:(old?.count||0)+1, conflict:!!old?.conflict});}}
function frontier(sums){return [...sums.values()].filter(e=>e.value<MAX-EPS).sort((a,b)=>(a.addedDepth??0)-(b.addedDepth??0)||norm(a.point)-norm(b.point)||a.value-b.value);}
function polygonInteriorOverlap(firstVerts,secondVerts) {
  const first=firstVerts.map(projectRaw),second=secondVerts.map(projectRaw);
  const strictCross=(a,b,c,d)=>{const abC=orientation2d(a,b,c),abD=orientation2d(a,b,d),cdA=orientation2d(c,d,a),cdB=orientation2d(c,d,b);return ((abC>EPS&&abD<-EPS)||(abC<-EPS&&abD>EPS))&&((cdA>EPS&&cdB<-EPS)||(cdA<-EPS&&cdB>EPS));};
  for(let i=0;i<first.length;i+=1)for(let j=0;j<second.length;j+=1)if(strictCross(first[i],first[(i+1)%first.length],second[j],second[(j+1)%second.length]))return true;
  if(first.some(point=>pointInPoly(point,second)))return true;
  if(second.some(point=>pointInPoly(point,first)))return true;
  return false;
}
function validCandidate(o,t,sums,markSums,used,placedTiles=[]){ const pk=`${o.name}|${o.idx}|${key(t)}`; if(used.has(pk)) return null; let newPts=0, overflow=0, line=0; const vertices=o.vertices.map(point=>add(point,t)); if(placedTiles.some(placement=>polygonInteriorOverlap(vertices,placement.vertices)))return null; const occ=o.occupancy.map(e=>({...e,point:add(e.point,t)})); for(const e of occ){ const cur=sums.get(key(e.point))?.value||0; if(Math.abs(cur)<EPS)newPts++; overflow=Math.max(overflow,cur+e.value-MAX); } if(overflow>EPS||newPts===0) return null; const marks=o.marks.map(e=>({...e,point:add(e.point,t)})); for(const e of marks){ const old=markSums.get(mkey(e)); if(old){ if(old.value!==e.value) return null; if(e.value!==0) line++; }} return {orientation:o, translation:t, pk, score:line*100-newPts}; }
function frontierPointHasCandidate(point, sums, markSums, used,placedTiles=[]) { const need = MAX - point.value; return searchOrientations.some(o => o.occupancy.some(a => a.value <= need+EPS && validCandidate(o, sub(point.point, a.point), sums, markSums, used,placedTiles))); }
function randomItem(items) { return items[Math.floor(Math.random() * items.length)]; }
function shuffled(items) { return items.map(value => ({ value, order: Math.random() })).sort((a, b) => a.order - b.order).map(entry => entry.value); }
function angleDiff(a, b) { return Math.abs(Math.atan2(Math.sin(a - b), Math.cos(a - b))); }
function candidateMovesForFrontier(f, sums, markSums, used,placedTiles=[]) {
  const need = MAX - f.value;
  const candidates = [];
  for (const o of searchOrientations) {
    for (const a of o.occupancy.filter(e => e.value <= need+EPS)) {
      const cand = validCandidate(o, sub(f.point, a.point), sums, markSums, used,placedTiles);
      if (cand) candidates.push({ ...cand, frontier: f });
    }
  }
  return candidates.sort((a, b) => b.score - a.score);
}
function placementCoronasFor(list){ const cs=list.map((_,i)=>i===0?0:Infinity), byPoint=new Map(); list.forEach((p,i)=>p.occupancy.forEach(e=>{const k=key(e.point); (byPoint.get(k)||byPoint.set(k,[]).get(k)).push(i);})); for(let q=[0],c=0;c<q.length;c++){ for(const e of list[q[c]].occupancy){ for(const j of byPoint.get(key(e.point))||[]) if(cs[j]>cs[q[c]]+1){cs[j]=cs[q[c]]+1; q.push(j);} } } return cs; }
function maxCoronaFor(list){ const finite=placementCoronasFor(list).filter(Number.isFinite); return finite.length ? Math.max(...finite) : 0; }
function removePlacement(p,sums,markSums){ for(const e of p.occupancy){ const k=key(e.point), old=sums.get(k); if(!old) continue; old.value=Math.round((old.value-e.value)*1e9)/1e9; if(old.value<=EPS)sums.delete(k); else sums.set(k,old); } for(const e of p.marks){ const k=mkey(e), old=markSums.get(k); if(!old) continue; if(old.count<=1) markSums.delete(k); else markSums.set(k,{...old,count:old.count-1,conflict:false}); } }
function candidateKeepsBoundaryAlive(candidate, sums, markSums, used,placedTiles=[]) {
  const trial = place(candidate.orientation, candidate.translation, generatedPlacementExtra(candidate.orientation, { ...candidate, forced: false, branchCount: 1 }));
  addPlacement(trial, sums, markSums);
  used.add(candidate.pk);
  const affected = new Map();
  trial.occupancy.forEach(entry => { const current = sums.get(key(entry.point)); if (current && current.value < MAX-EPS) affected.set(key(entry.point), current); });
  const dead = [...affected.values()].some(point => !candidateMovesForFrontier(point, sums, markSums, used,[...placedTiles,trial]).length);
  used.delete(candidate.pk);
  removePlacement(trial, sums, markSums);
  return !dead;
}
function patchBoundaryGraph(sums, markSums, used,placedTiles=[]) {
  const frontierItems = frontier(sums).slice(0, 12).map(frontierPoint => ({
    frontier: frontierPoint,
    pointKey: key(frontierPoint.point)
  }));
  const graph = buildFrontierCandidateGraphSync(
    frontierItems,
    item => candidateMovesForFrontier(item.frontier, sums, markSums, used,placedTiles),
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
function analyzePatchBoundary(sums, markSums, used, deterministic=false,placedTiles=[]) {
  const analysis = patchBoundaryGraph(sums, markSums, used,placedTiles);
  if (analysis.deadEnd) return { deadEnd: analysis.deadEnd, choice: null, forced: false, graph: analysis };
  if (analysis.forced.length) return { deadEnd: null, choice: analysis.forced[0], forced: true, graph: analysis };
  const ranked = analysis.branches;
  if (!ranked.length) return { deadEnd: null, choice: null, forced: false };
  const first = ranked[0];
  const tied = ranked.filter(option => (option.frontier.addedDepth ?? 0) === (first.frontier.addedDepth ?? 0) && option.candidates.length === first.candidates.length && norm(option.frontier.point) === norm(first.frontier.point) && option.frontier.value === first.frontier.value && option.candidates[0].score === first.candidates[0].score);
  return { deadEnd: null, choice:deterministic ? tied[0] : randomItem(tied), forced: false, graph: analysis };
}
function generatedPlacementExtra(orientation, candidate) {
  if (orientation.name === 'Trefoil') return { kind: 'attached-trefoil', color: orientation.isReflected ? ORANGE : BLUE, placementKey: candidate.pk, forced: candidate.forced, branchCount: candidate.branchCount };
  return { kind: activeFillTile==='turtle'?'turtle':'fill-tile', placementKey: candidate.pk, forced: candidate.forced, branchCount: candidate.branchCount };
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
  const groupFits = group => placementsFitWithSums(group, sums, markSums,nextPlacements);
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
    const analysis = analyzePatchBoundary(sums, markSums, used,false,nextPlacements);
    if (analysis.deadEnd || !analysis.choice) return false;
    if (forcedOnly && !analysis.forced) return true;
    if (!analysis.forced && bestCorona >= targetCorona) return true;
    const candidates = analysis.forced ? analysis.choice.candidates : shuffled(analysis.choice.candidates);
    for (const candidate of candidates) {
      if (!relaxBoundary && !candidateKeepsBoundaryAlive(candidate, sums, markSums, used,nextPlacements)) continue;
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
function geometricCandidateKeepsBoundaryAlive(candidate, sums, used,placedTiles=[]) {
  const previousOrientations = searchOrientations;
  const baseOrientations=baseFillOrientations();
  searchOrientations = baseOrientations;
  const geometric = { ...candidate, orientation:baseOrientations[candidate.orientation.idx] };
  try { return candidateKeepsBoundaryAlive(geometric, sums, new Map(), used,placedTiles); }
  finally { searchOrientations = previousOrientations; }
}
function countMemoHitsAt(frontierPoint, sums, markSums, used, markedCandidates, seenHits,placedTiles=[]) {
  const previousOrientations = searchOrientations;
  searchOrientations = baseFillOrientations();
  let geometricCandidates;
  try { geometricCandidates = candidateMovesForFrontier(frontierPoint, sums, new Map(), used,placedTiles); }
  finally { searchOrientations = previousOrientations; }
  const markedKeys = new Set(markedCandidates.map(candidate => candidate.pk));
  let addedHits = 0;
  geometricCandidates.forEach(candidate => {
    if (markedKeys.has(candidate.pk)) return;
    const hitKey = `${placements.length}|${candidate.pk}`;
    if (seenHits.has(hitKey)) return;
    seenHits.add(hitKey);
    onlineMemory.memoHits += 1;
    addedHits += 1;
  });
  if (addedHits) onlineMemory.events.push({ type:'memo-hit', count:addedHits });
}
function generateOnlinePatch(seedPlacement, guardLimit=170, targetCorona=6) {
  resetOnlineMemory();
  const previousOrientations = searchOrientations;
  let accepted = [seedPlacement], best = accepted.slice(), bestCorona = 0;
  const locallyFailed = new Set(), seenHits = new Set();
  let steps = 0;
  try {
    while (accepted.length < guardLimit && steps++ < Math.max(900, targetCorona * targetCorona * 24)) {
      const learnedOrientations = learnedTurtleOrientations();
      searchOrientations = learnedOrientations;
      const replayed = replayWithOnlineMarking(accepted, learnedOrientations);
      if (!replayed) break;
      accepted = replayed;
      const sums = new Map(), markSums = new Map(), used = new Set();
      accepted.forEach((placement,index) => { addPlacement(placement,sums,markSums,index); if (placement.placementKey) used.add(placement.placementKey); });
      const corona = maxCoronaFor(accepted);
      if (corona > bestCorona || (corona === bestCorona && accepted.length > best.length)) { best = accepted.slice(); bestCorona = corona; }
      if (bestCorona >= targetCorona) break;
      const analysis = analyzePatchBoundary(sums,markSums,used,true,accepted);
      if (analysis.deadEnd || !analysis.choice) break;
      countMemoHitsAt(analysis.choice.frontier,sums,markSums,used,analysis.choice.candidates,seenHits,accepted);
      const candidates = analysis.choice.candidates.filter(candidate => !locallyFailed.has(`${accepted.length}|${candidate.pk}`));
      let advanced = false, learned = false;
      for (const candidate of candidates) {
        if (!geometricCandidateKeepsBoundaryAlive(candidate,sums,used,accepted)) {
          if (learnOnlineFailure(candidate,accepted)) { learned = true; break; }
          locallyFailed.add(`${accepted.length}|${candidate.pk}`);
          continue;
        }
        const placement = place(candidate.orientation,candidate.translation,generatedPlacementExtra(candidate.orientation,{...candidate,forced:analysis.forced,branchCount:analysis.choice.candidates.length}));
        accepted.push(placement);
        onlineMemory.events.push({ type:'accept', accepted:accepted.length });
        advanced = true;
        break;
      }
      if (learned) continue;
      if (!advanced) break;
    }
    onlineMemory.assignments = assignmentsForAccepted(onlineMemory.support,best) || onlineMemory.assignments;
    const finalOrientations = learnedTurtleOrientations();
    const finalPatch = replayWithOnlineMarking(best,finalOrientations) || best;
    currentTurtleOrientations = finalOrientations;
    updateLearningReadout(onlineMemory.failures.length
      ? `${onlineMemory.failures.length} failed branch${onlineMemory.failures.length===1?'':'es'} encoded; the ${finalPatch.length}-placement patch passed final replay.`
      : `No failed branch needed a marking before this ${finalPatch.length}-placement patch was reached.`);
    return finalPatch;
  } finally {
    searchOrientations = previousOrientations;
  }
}
function readTargetCorona() { return Math.max(1, Math.min(12, Number(coronaTargetInput?.value) || 3)); }
function patchIntegrity() {
  const sums = new Map(), markSums = new Map(), used = new Set();
  placements.forEach(placement => { addPlacement(placement, sums, markSums); if (placement.placementKey) used.add(placement.placementKey); });
  const overfilled = [...sums.values()].filter(entry => entry.value > MAX+EPS).length;
  const markConflicts = [...markSums.values()].filter(entry => entry.conflict).length;
  const deadFrontier = frontier(sums).filter(point => !frontierPointHasCandidate(point, sums, markSums, used,placements)).length;
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
function placementsFitWithSums(group, sums, markSums,existingPlacements=[]) {
  const trialSums = new Map([...sums].map(([key, entry]) => [key, { ...entry }])), trialMarks = new Map([...markSums].map(([key, entry]) => [key, { ...entry }]));
  for (const placement of group) {
    if([...existingPlacements,...group.slice(0,group.indexOf(placement))].some(existing=>polygonInteriorOverlap(placement.vertices,existing.vertices)))return false;
    addPlacement(placement, trialSums, trialMarks);
    if ([...trialSums.values()].some(entry => entry.value > MAX+EPS)) return false;
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
    if (!placementsFitWithSums(group.map(entry => entry.placement), sums, markSums,out)) continue;
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
  if (onlineMode()) { clearMoveHintCache(); legalMoveIndices = new Set(); }
  else updateMoveHints();
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
  currentTurtleOrientations = onlineMode() ? baseFillOrientations() : fixedFillOrientations();
  const seed = activeTab === 'crossing'
    ? place(centralHexBase,[0,0,0],{kind:'hex-hole'})
    : (activeTab === 'tiling'
      ? place(onlineMode() ? unmarkedTrefoilBase : trefoilBase,[0,0,0],{kind:'seed'})
      : place(currentTurtleOrientations[0],[0,0,0],{kind:activeFillTile==='turtle'?'seed':'fill-tile'}));
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
  if (onlineMode()) {
    window.setTimeout(() => {
      if (version !== buildVersion) return;
      const finalPlacements = generateOnlinePatch(seed,guardLimit,targetCorona);
      finishPatchReveal(finalPlacements,version);
    },0);
    return;
  }
  resetOnlineMemory();
  updateLearningReadout('Fixed-stripe comparison mode: no online failure memory is being learned.');
  const buildAndReveal = (corona, limit) => {
    if (version !== buildVersion) return;
    setStatus('computing...');
    const generatedPlacements = generatePatch(seed, limit, corona, selectedSymmetry, activeTab === 'crossing');
    const isFinal = corona >= targetCorona;
    const finalPlacements = isFinal && activeTab !== 'crossing' && activeFillTile==='turtle' ? generateTrefoilPass(generatedPlacements, guardLimit, selectedSymmetry) : generatedPlacements;
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
function styleForPlacement(p) {
  if (p.color) return { fill:`${p.color}7a`,stroke:trefoilStrokeFor(p.color) };
  const reflected=p.isReflected;
  if(p.orientation?.name==='Hat') return {fill:reflected?'rgba(130,84,156,.46)':'rgba(44,137,105,.43)',stroke:reflected?'#70428a':'#176f5f'};
  if(p.kind==='fill-tile'&&activeFillTile==='custom') return {fill:reflected?'rgba(198,112,44,.44)':'rgba(55,120,151,.40)',stroke:reflected?'#a45119':'#245f7c'};
  return {fill:reflected?'rgba(213,94,0,.48)':'rgba(0,114,178,.42)',stroke:reflected?ORANGE_STROKE:BLUE_STROKE};
}
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
  if (onlineMode() && isFillPlacement(p)) {
    p.marks.forEach(mark => {
      const point = screen(mark.point);
      ctx.beginPath();
      ctx.arc(point.x,point.y,Math.max(2.4,3.6*view.scale),0,Math.PI*2);
      ctx.fillStyle = mark.value < 0 ? BLUE : ORANGE;
      ctx.fill();
      ctx.strokeStyle = '#fffdf8';
      ctx.lineWidth = 1;
      ctx.stroke();
    });
  }
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
      if ((baseSums.get(pointKey)?.value || 0) + entry.value > MAX+EPS) return false;
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
  if (onlineMode()) return [1];
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
  if (!onlineMode() && restoreTabState(activeTab)) draw();
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

function updateFillTilePicker() {
  fillTileButtons.forEach(button => button.setAttribute('aria-pressed',button.dataset.fillTile===activeFillTile?'true':'false'));
  if (customTileButton) customTileButton.textContent=hasCustomTile ? `Edit ${customTileName()}` : 'Draw custom tile';
}
function selectFillTile(kind,{run=true}={}) {
  if (!['turtle','hat','custom'].includes(kind)) return;
  if(kind==='custom'&&!hasCustomTile){openCustomTileEditor();return;}
  activeFillTile=kind;
  if (kind==='custom') rebuildCustomTileOrientations();
  currentTurtleOrientations=onlineMode()?baseFillOrientations():fixedFillOrientations();
  tabStates.clear();
  selectedSymmetry=1;
  updateFillTilePicker();
  updateSymmetryAvailability();
  setStatus(`${fillTileDisplayName()} selected`);
  if (run) buildPatch();
}

function axialArea(verts) {
  if (verts.length<3) return 0;
  return Math.abs(verts.reduce((sum,point,index) => { const next=verts[(index+1)%verts.length]; return sum+point[0]*next[1]-next[0]*point[1]; },0)/2);
}
function orientation2d(a,b,c) { return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x); }
function onSegment2d(a,b,p) { return Math.abs(orientation2d(a,b,p))<1e-8 && p.x>=Math.min(a.x,b.x)-1e-8 && p.x<=Math.max(a.x,b.x)+1e-8 && p.y>=Math.min(a.y,b.y)-1e-8 && p.y<=Math.max(a.y,b.y)+1e-8; }
function segmentsIntersect2d(a,b,c,d) {
  const abC=orientation2d(a,b,c),abD=orientation2d(a,b,d),cdA=orientation2d(c,d,a),cdB=orientation2d(c,d,b);
  if (((abC>0&&abD<0)||(abC<0&&abD>0))&&((cdA>0&&cdB<0)||(cdA<0&&cdB>0))) return true;
  return (Math.abs(abC)<1e-8&&onSegment2d(a,b,c))||(Math.abs(abD)<1e-8&&onSegment2d(a,b,d))||(Math.abs(cdA)<1e-8&&onSegment2d(c,d,a))||(Math.abs(cdB)<1e-8&&onSegment2d(c,d,b));
}
function loopSelfIntersects(verts,closed=true) {
  const points=verts.map(point=>{const projected=projectRaw(point);return{x:projected.x,y:projected.y};});
  const edgeCount=closed?points.length:Math.max(0,points.length-1);
  for(let i=0;i<edgeCount;i+=1){
    const a=points[i],b=points[(i+1)%points.length];
    for(let j=i+1;j<edgeCount;j+=1){
      if(j===i||j===i+1||(closed&&i===0&&j===edgeCount-1)) continue;
      const c=points[j],d=points[(j+1)%points.length];
      if(segmentsIntersect2d(a,b,c,d)) return true;
    }
  }
  return false;
}
function customDraftValidation() {
  const unique=new Set(customDraftLoop.map(key));
  if(!customDraftLoop.length) return {state:'empty',title:'Choose a starting point',message:'A valid tile is a simple, nonzero-area closed loop.',valid:false};
  if(unique.size!==customDraftLoop.length) return {state:'invalid',title:'A vertex is repeated',message:'Undo the repeated point; only the first point may be revisited to close the loop.',valid:false};
  if(loopSelfIntersects(customDraftLoop,customDraftClosed)) return {state:'invalid',title:'The boundary crosses itself',message:'Undo points until every non-neighboring edge is disjoint.',valid:false};
  if(!customDraftClosed) return {state:'empty',title:`Open path · ${customDraftLoop.length} point${customDraftLoop.length===1?'':'s'}`,message:customDraftLoop.length<3?'Choose at least three vertices.':'Click the highlighted first point to close the boundary.',valid:false};
  if(customDraftLoop.length<3) return {state:'invalid',title:'At least three vertices are required',message:'Open the loop and add another point.',valid:false};
  if(axialArea(customDraftLoop)<EPS) return {state:'invalid',title:'The loop has zero area',message:'Choose vertices that enclose part of the plane.',valid:false};
  return {state:'valid',title:'Ready to tile',message:'Simple closed A₂ polygon. Interior and boundary occupancy will be compiled automatically.',valid:true};
}
const builderGridSize=42;
function builderScreen(point) {
  const u=point[0],v=point[1];
  return {x:customTileCanvas.width/2+(u+v/2)*builderGridSize,y:customTileCanvas.height/2-v*Math.sqrt(3)/2*builderGridSize};
}
function builderLatticePoint(event) {
  const rect=customTileCanvas.getBoundingClientRect(),x=(event.clientX-rect.left)*customTileCanvas.width/rect.width,y=(event.clientY-rect.top)*customTileCanvas.height/rect.height;
  const v=Math.round((customTileCanvas.height/2-y)/(Math.sqrt(3)/2*builderGridSize));
  const u=Math.round((x-customTileCanvas.width/2)/builderGridSize-v/2);
  return [u,v,-u-v];
}
function drawCustomBuilder() {
  if(!customTileCtx||!customTileCanvas) return;
  const context=customTileCtx,width=customTileCanvas.width,height=customTileCanvas.height;
  context.clearRect(0,0,width,height); context.fillStyle='#edf2ef'; context.fillRect(0,0,width,height);
  context.lineWidth=1;
  for(let u=-14;u<=14;u+=1) for(let v=-11;v<=11;v+=1){
    const point=[u,v,-u-v],screenPoint=builderScreen(point);
    if(screenPoint.x<12||screenPoint.x>width-12||screenPoint.y<12||screenPoint.y>height-12) continue;
    context.beginPath(); context.arc(screenPoint.x,screenPoint.y,1.7,0,Math.PI*2); context.fillStyle='#9bb1aa'; context.fill();
  }
  const screens=customDraftLoop.map(builderScreen);
  if(customDraftClosed&&screens.length>=3){ context.beginPath(); screens.forEach((point,index)=>index?context.lineTo(point.x,point.y):context.moveTo(point.x,point.y)); context.closePath(); context.fillStyle='rgba(23,111,95,.15)'; context.fill(); }
  if(screens.length){
    context.beginPath(); screens.forEach((point,index)=>index?context.lineTo(point.x,point.y):context.moveTo(point.x,point.y));
    if(customDraftClosed) context.closePath(); else if(customDraftHover){const hover=builderScreen(customDraftHover);context.lineTo(hover.x,hover.y);}
    context.strokeStyle=customDraftValidation().state==='invalid'?'#a54136':'#176f5f'; context.lineWidth=4; context.lineJoin='round'; context.stroke();
  }
  screens.forEach((point,index)=>{context.beginPath();context.arc(point.x,point.y,index===0?8:6,0,Math.PI*2);context.fillStyle=index===0&&!customDraftClosed?'#d55e00':'#fffdf8';context.fill();context.strokeStyle='#104c43';context.lineWidth=2.5;context.stroke();});
  if(customDraftHover&&!customDraftClosed){const hover=builderScreen(customDraftHover);context.beginPath();context.arc(hover.x,hover.y,5,0,Math.PI*2);context.fillStyle='#d55e00';context.fill();}
  const validation=customDraftValidation();
  if(customVertexCountEl) customVertexCountEl.textContent=String(customDraftLoop.length);
  if(customAreaEl) customAreaEl.textContent=axialArea(customDraftLoop).toFixed(axialArea(customDraftLoop)%1?1:0);
  if(customTileValidationEl){customTileValidationEl.dataset.state=validation.state;customTileValidationEl.innerHTML=`<strong>${validation.title}</strong><p>${validation.message}</p>`;}
  if(useCustomTileButton) useCustomTileButton.disabled=!validation.valid;
  if(undoCustomPointButton) undoCustomPointButton.disabled=!customDraftLoop.length;
  if(clearCustomTileButton) clearCustomTileButton.disabled=!customDraftLoop.length;
}
function openCustomTileEditor() {
  if(customTileNameInput)customTileNameInput.value=customTileLabel;
  customDraftLoop=(hasCustomTile?customTileLoop:[]).map(point=>[...point]);
  customDraftClosed=hasCustomTile&&customDraftLoop.length>=3;
  customDraftHover=null;
  drawCustomBuilder();
  if(typeof customTileDialog?.showModal==='function') customTileDialog.showModal(); else customTileDialog?.setAttribute('open','');
}
function closeCustomTileEditor() { if(customTileDialog?.open&&typeof customTileDialog.close==='function')customTileDialog.close();else customTileDialog?.removeAttribute('open'); }
function undoCustomPoint() { if(customDraftClosed){customDraftClosed=false;}else customDraftLoop.pop();customDraftHover=null;drawCustomBuilder(); }
function setCustomPreset(name) {
  if(name==='turtle')customDraftLoop=normalizedLoop(turtleVerts);
  else if(name==='hat')customDraftLoop=normalizedLoop(hatVerts);
  else customDraftLoop=[];
  customDraftClosed=name!=='blank';customDraftHover=null;drawCustomBuilder();
}
function addCustomDraftPoint(point) {
  if(customDraftClosed)return;
  if(customDraftLoop.length>=3&&key(point)===key(customDraftLoop[0])){customDraftClosed=true;drawCustomBuilder();return;}
  if(customDraftLoop.some(existing=>key(existing)===key(point)))return;
  customDraftLoop.push(point);customDraftHover=null;drawCustomBuilder();
}
function useCustomTile() {
  if(!customDraftValidation().valid)return;
  customTileLabel=customTileNameInput?.value.trim()||'Custom tile';
  customTileLoop=normalizedLoop(customDraftLoop);customDraftLoop=customTileLoop.map(point=>[...point]);customDraftClosed=true;
  hasCustomTile=true;rebuildCustomTileOrientations();closeCustomTileEditor();selectFillTile('custom');
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
blueStripesToggle.addEventListener('click',()=>toggleStripe(blueStripesToggle)); orangeStripesToggle.addEventListener('click',()=>toggleStripe(orangeStripesToggle)); symmetryButtons.forEach(button => button.addEventListener('click', () => { if (button.disabled) return; selectedSymmetry = Number(button.dataset.symmetry) || 1; updateSymmetryAvailability(); buildPatch(); })); buildButton.addEventListener('click',()=>buildPatch()); coronaTargetInput?.addEventListener('change',()=>buildPatch()); onlineLearningToggle?.addEventListener('change',()=>{ tabStates.clear(); selectedSymmetry=1; updateSymmetryAvailability(); buildPatch(); }); resetButton.addEventListener('click', resetToCenter); turtleSeedTab.addEventListener('click',()=>showTab('turtle')); tilingTab.addEventListener('click',()=>showTab('tiling')); crossingTab.addEventListener('click',()=>showTab('crossing'));
fillTileButtons.forEach(button=>button.addEventListener('click',()=>selectFillTile(button.dataset.fillTile)));
customTileButton?.addEventListener('click',openCustomTileEditor);
closeCustomTileButton?.addEventListener('click',closeCustomTileEditor);
undoCustomPointButton?.addEventListener('click',undoCustomPoint);
clearCustomTileButton?.addEventListener('click',()=>setCustomPreset('blank'));
useCustomTileButton?.addEventListener('click',useCustomTile);
customPresetButtons.forEach(button=>button.addEventListener('click',()=>setCustomPreset(button.dataset.customPreset)));
customTileDialog?.addEventListener('click',event=>{if(event.target===customTileDialog)closeCustomTileEditor();});
customTileCanvas?.addEventListener('pointermove',event=>{if(customDraftClosed)return;customDraftHover=builderLatticePoint(event);drawCustomBuilder();});
customTileCanvas?.addEventListener('pointerleave',()=>{customDraftHover=null;drawCustomBuilder();});
customTileCanvas?.addEventListener('pointerdown',event=>{event.preventDefault();addCustomDraftPoint(builderLatticePoint(event));});
document.addEventListener('keydown',event=>{
  if(!customTileDialog?.open)return;
  if(event.key==='Escape'){event.preventDefault();closeCustomTileEditor();return;}
  if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='z'){event.preventDefault();undoCustomPoint();}
});
window.addEventListener('resize', resizeCanvas);
window.__turtleGctsDebug = {
  runOnline(centerKind='trefoil',targetCorona=2,fillKind=activeFillTile) {
    if(['turtle','hat','custom'].includes(fillKind)) activeFillTile=fillKind;
    if(fillKind==='custom') rebuildCustomTileOrientations();
    const seed = centerKind === 'hexagon'
      ? place(centralHexBase,[0,0,0],{kind:'hex-hole'})
      : place(unmarkedTrefoilBase,[0,0,0],{kind:'seed'});
    const patch = generateOnlinePatch(seed,Math.max(120,targetCorona*targetCorona*30),targetCorona);
    return {
      center:centerKind,
      fill:activeFillTile,
      tiles:patch.length,
      corona:maxCoronaFor(patch),
      learnedFailures:onlineMemory.failures.length,
      supportEntries:onlineMemory.support.size,
      memoHits:onlineMemory.memoHits,
      replayValid:!!replayWithOnlineMarking(patch,learnedTurtleOrientations())
    };
  },
  setCustomLoop(points,name='Test custom tile') {
    customTileLabel=name;if(customTileNameInput)customTileNameInput.value=name;
    customTileLoop=normalizedLoop(points.map(point=>[...point]));hasCustomTile=true;
    rebuildCustomTileOrientations();
    return {vertices:customTileLoop.length,area:axialArea(customTileLoop),orientations:customTileOrientations.length};
  },
  validateLoop(points,closed=true) {
    const previousLoop=customDraftLoop,previousClosed=customDraftClosed;
    customDraftLoop=points.map(point=>[...point]);customDraftClosed=closed;
    const result=customDraftValidation();
    customDraftLoop=previousLoop;customDraftClosed=previousClosed;
    return result;
  }
};
updateSymmetryAvailability();
updateFillTilePicker();
resizeCanvas();
setStatus('computing...');
window.setTimeout(() => buildPatch(), 60);
