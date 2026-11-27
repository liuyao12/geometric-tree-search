// GCTS-I: interactive Hat / Turtle tiling on the A2 lattice.
// MathBB widget; native Canvas 2D, no Three.js dependency.
// Standalone: original GCTS engine and matching-rule modules embedded below.
(async function () {
  document.body.className = 'widget-layout';
  const area = document.createElement('div'); area.className = 'widget-stage-area';
  const ui = document.createElement('div'); ui.className = 'widget-ui';
  document.body.append(area, ui);
  Object.assign(document.body.style,{display:'flex',flexDirection:'row',alignItems:'stretch',gap:'0',overflow:'hidden'});
  Object.assign(ui.style,{display:'flex',flexDirection:'column',alignItems:'stretch',justifyContent:'flex-start',flex:'0 0 205px',width:'205px',boxSizing:'border-box',padding:'12px',gap:'9px',borderLeft:'1px solid #d9dee5',background:'#fafbfc',overflowY:'auto',color:'#202a35',font:'13px system-ui'});
  Object.assign(area.style,{flex:'1 1 0',minWidth:'0',width:'auto'});
  Object.assign(area.style, {position:'relative', overflow:'hidden', minHeight:'240px', background:'#fff'});
  const canvas = document.createElement('canvas');
  Object.assign(canvas.style,{width:'100%',height:'100%',display:'block',position:'absolute',inset:'0',touchAction:'none',cursor:'grab'});
  area.append(canvas);
  const ctx=canvas.getContext('2d');
  const status=document.createElement('div'); status.className='math-label';
  Object.assign(status.style,{position:'absolute',top:'12px',left:'14px',font:'13px system-ui',pointerEvents:'none',background:'rgba(255,255,255,.9)',padding:'5px 8px',borderRadius:'5px'});
  status.textContent='Initializing tiler…'; area.append(status);
// ---------- Embedded geometric-failure-memo.js ----------
const memo = (() => {

const rounded = value => Math.round(value * 1e9) / 1e9;
const vectorKey = vector => vector.map(rounded).join(",");
const matrixKey = matrix => matrix.flat().map(rounded).join(",");
const transposeVector = (matrix, vector) => [0, 1, 2].map(column =>
  matrix[0][column] * vector[0] + matrix[1][column] * vector[1] + matrix[2][column] * vector[2]
);
const transposeMatrix = (left, right) => [0, 1, 2].map(row =>
  [0, 1, 2].map(column =>
    left[0][row] * right[0][column]
    + left[1][row] * right[1][column]
    + left[2][row] * right[2][column]
  )
);

/**
 * Translation-equivariant geometric nogoods.
 *
 * Each clause stores a failed candidate and its complete placed context in
 * coordinates relative to that candidate. Absolute position is discarded, so
 * translated copies are recognized; requiring the complete recorded context
 * keeps the clause exact and monotone when more tiles have been placed.
 */
class GeometricFailureMemo {
  constructor({ describePlacement, contextMatch = "subset", allAnchors = false }) {
    this.describePlacement = describePlacement;
    this.contextMatch = contextMatch;
    this.allAnchors = allAnchors;
    this.clauses = [];
    this.byCandidate = new Map();
    this.signatures = new Set();
    this.prunes = 0;
  }

  representation(context, candidate) {
    const head = this.describePlacement(candidate);
    if (!head) return null;
    const required = [];
    for (const placement of context) {
      const descriptor = this.describePlacement(placement);
      if (!descriptor) continue;
      const delta = descriptor.translation.map((value, axis) => value - head.translation[axis]);
      if (head.frame && descriptor.frame) {
        const relative = transposeVector(head.frame, delta);
        const relativeFrame = transposeMatrix(head.frame, descriptor.frame);
        required.push(`${descriptor.kind}|${matrixKey(relativeFrame)}|${vectorKey(relative)}`);
      } else {
        required.push(`${descriptor.kind}|${descriptor.orientation}|${vectorKey(delta)}`);
      }
    }
    required.sort();
    return {
      candidate: head.frame ? `${head.kind}|local-frame` : `${head.kind}|${head.orientation}`,
      required
    };
  }

  encode(context, candidate, metadata = {}) {
    const patch = [...context, candidate];
    const rawVariants = this.allAnchors
      ? patch.map((anchor, index) => this.representation(patch.filter((_, other) => other !== index), anchor))
      : [this.representation(context, candidate)];
    if (rawVariants.some(representation => !representation)) {
      return { encoded: false, reason: "missing-geometric-descriptor" };
    }
    const variantsBySignature = new Map();
    for (const representation of rawVariants) {
      const variantSignature = `${representation.candidate}=>${representation.required.join(";")}`;
      if (!variantsBySignature.has(variantSignature)) {
        variantsBySignature.set(variantSignature, { ...representation, signature: variantSignature });
      }
    }
    const variants = [...variantsBySignature.values()];
    const signature = variants.map(variant => variant.signature).sort()[0];
    if (this.signatures.has(signature)) {
      return {
        encoded: true,
        duplicate: true,
        clauses: this.clauses.length,
        indexedVariants: this.indexedVariantCount(),
        signature
      };
    }
    const clause = { ...variants[0], variants, signature, metadata: { ...metadata } };
    this.signatures.add(signature);
    this.clauses.push(clause);
    for (const variant of variants) {
      if (!this.byCandidate.has(variant.candidate)) this.byCandidate.set(variant.candidate, []);
      this.byCandidate.get(variant.candidate).push(variant);
    }
    return {
      encoded: true,
      duplicate: false,
      clauses: this.clauses.length,
      indexedVariants: this.indexedVariantCount(),
      signature
    };
  }

  compatible(candidate, context, count = true) {
    const representation = this.representation(context, candidate);
    if (!representation) return true;
    const clauses = this.byCandidate.get(representation.candidate);
    if (!clauses?.length) return true;
    const available = new Set(representation.required);
    for (const clause of clauses) {
      if (clause.required.length > available.size) continue;
      if (this.contextMatch === "exact" && clause.required.length !== available.size) continue;
      if (!clause.required.every(token => available.has(token))) continue;
      if (count) this.prunes += 1;
      return false;
    }
    return true;
  }

  indexedVariantCount() {
    let count = 0;
    for (const variants of this.byCandidate.values()) count += variants.length;
    return count;
  }

  stats() {
    return {
      clauses: this.clauses.length,
      indexedVariants: this.indexedVariantCount(),
      prunes: this.prunes
    };
  }
}

return {GeometricFailureMemo};
})();
// ---------- Embedded gcts-point-branching.js ----------
const branch = (() => {

// Geometry-free GCTS scheduling over frontier points and legal placement IDs.
// Callers supply complete domains and restore point introduction ages on rollback.
function selectPointBranch(frontier, random = Math.random, { restrictToPoint = true, isAdjacent } = {}) {
  const dead = frontier.find(point => point.legal.length === 0);
  if (dead) return { dead, forced: false, moves: [] };
  const forced = frontier.find(point => point.legal.length === 1);
  if (forced) return { dead: null, forced: true, moves: [{ placement: forced.legal[0], frontier: forced }] };
  let oldest = Infinity;
  for (const point of frontier) oldest = Math.min(oldest, point.introducedAt);
  const pool = new Map();
  for (const point of frontier) {
    if (point.introducedAt !== oldest) continue;
    for (const placement of point.legal) {
      if (!pool.has(placement.id)) pool.set(placement.id, { placement, frontier: point });
    }
  }
  let moves = [...pool.values()];
  for (let i = moves.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [moves[i], moves[j]] = [moves[j], moves[i]];
  }
  if (isAdjacent) {
    const nearby = [], others = [];
    for (const move of moves) {
      (isAdjacent(move.placement) ? nearby : others).push(move);
    }
    moves = [...nearby, ...others];
  }
  if (restrictToPoint && moves.length) {
    const point = moves[0].frontier;
    const alternatives = new Set(point.legal.map(placement => placement.id));
    moves = moves.filter(move => alternatives.has(move.placement.id))
      .map(move => ({ ...move, frontier: point }));
  }
  return { dead: null, forced: false, moves };
}

return {selectPointBranch};
})();
// ---------- Embedded a2-tiling-engine.js ----------
const E = (() => {
const {GeometricFailureMemo}=memo; const {selectPointBranch:selectBaseTilingMoves}=branch;



const A2_TILE_LOOPS = Object.freeze({
  turtle: [[3,-2,-1],[2,0,-2],[0,1,-1],[0,2,-2],[-1,3,-2],[-2,2,0],[-1,0,1],[-2,0,2],[-2,-1,3],[0,-2,2],[1,-4,3],[2,-4,2],[3,-5,2],[4,-4,0]],
  hat: [[0,0,0],[1,0,-1],[1,1,-2],[3,0,-3],[4,1,-5],[3,2,-5],[3,3,-6],[1,4,-5],[0,6,-6],[-1,6,-5],[-1,5,-4],[-1,4,-3],[0,3,-3],[-1,2,-1]],
  hexagon: [[2,0,-2],[2,-2,0],[0,-2,2],[-2,0,2],[-2,2,0],[0,2,-2]]
});

const PERMUTATIONS = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
const A2_SYMMETRIES = Object.freeze([1,-1].flatMap(sign =>
  PERMUTATIONS.map(permutation => ({ sign, permutation }))
));

const a2Key = point => point.join(",");
const a2Add = (a,b) => [a[0]+b[0],a[1]+b[1],a[2]+b[2]];
const a2Sub = (a,b) => [a[0]-b[0],a[1]-b[1],a[2]-b[2]];
const a2Transform = (point, symmetry) => symmetry.permutation.map(index => symmetry.sign * point[index]);
const a2InverseTransform = (point, symmetry) => {
  const result=[0,0,0];
  symmetry.permutation.forEach((source, output) => { result[source]=symmetry.sign*point[output]; });
  return result;
};

const polygonArea2 = loop => loop.reduce((sum, point, index) => {
  const next=loop[(index+1)%loop.length];
  return sum + point[0]*next[1]-next[0]*point[1];
},0);

const normalizedLoop = loop => {
  if (!loop.length) return [];
  const origin=loop[0];
  const shifted=loop.map(point=>a2Sub(point,origin));
  return polygonArea2(shifted)<0 ? [shifted[0],...shifted.slice(1).reverse()] : shifted;
};

const pointInPolygon = (point, loop) => {
  let inside=false;
  for(let i=0,j=loop.length-1;i<loop.length;j=i++){
    const a=loop[i],b=loop[j];
    if((a[1]>point[1])!==(b[1]>point[1]) && point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]) inside=!inside;
  }
  return inside;
};
const pointOnSegment=(p,a,b)=>Math.abs((b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))<1e-8&&(p[0]-a[0])*(p[0]-b[0])+(p[1]-a[1])*(p[1]-b[1])<=1e-8;
const pointInOrOn=(point,loop)=>pointInPolygon(point,loop)||loop.some((a,i)=>pointOnSegment(point,a,loop[(i+1)%loop.length]));
const polygonContained=(inner,outer)=>{const a=inner.map(([x,y])=>[x,y]),b=outer.map(([x,y])=>[x,y]);return a.every((p,i)=>pointInOrOn(p,b)&&pointInOrOn([(p[0]+a[(i+1)%a.length][0])/2,(p[1]+a[(i+1)%a.length][1])/2],b));};
const properIntersection=(a,b,c,d)=>{const cross=(p,q,r)=>(q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0]);return cross(a,b,c)*cross(a,b,d)<-1e-8&&cross(c,d,a)*cross(c,d,b)<-1e-8;};
const polygonsOverlap=(left,right)=>{const a=left.map(([x,y])=>[x,y]),b=right.map(([x,y])=>[x,y]);for(let i=0;i<a.length;i++)for(let j=0;j<b.length;j++)if(properIntersection(a[i],a[(i+1)%a.length],b[j],b[(j+1)%b.length]))return true;const strictlyInside=(point,loop)=>!loop.some((start,index)=>pointOnSegment(point,start,loop[(index+1)%loop.length]))&&pointInPolygon(point,loop);if(a.some(point=>strictlyInside(point,b))||b.some(point=>strictlyInside(point,a)))return true;const aKeys=new Set(a.map(point=>point.join(",")));return a.length===b.length&&b.every(point=>aKeys.has(point.join(",")));};

const gcd2=(a,b)=>{a=Math.abs(a);b=Math.abs(b);while(b)[a,b]=[b,a%b];return a||1;};
const gcd3=(a,b,c)=>gcd2(gcd2(a,b),c);
const segmentLatticePoints=(a,b)=>{const d=a2Sub(b,a),steps=gcd3(d[0],d[1],d[2]),step=d.map(v=>v/steps);return Array.from({length:steps+1},(_,i)=>a2Add(a,step.map(v=>v*i)));};
function polygonBoundaryEdges(loop) {
  const edges = [];
  const winding = Math.sign(polygonArea2(loop));
  for (let index = 0; index < loop.length; index++) {
    const points = segmentLatticePoints(loop[index], loop[(index + 1) % loop.length]);
    for (let step = 1; step < points.length; step++) {
      const from = a2Key(points[step - 1]);
      const to = a2Key(points[step]);
      if (from === to) continue;
      const forward = from < to;
      edges.push({
        key: forward ? `${from}|${to}` : `${to}|${from}`,
        from, to, direction: (forward ? 1 : -1) * winding
      });
    }
  }
  return edges;
}
const projected=([x,y])=>[x+y*.5,y*Math.sqrt(3)/2];
function polygonOccupancy(loop){
  const map=new Map(),projectedLoop=loop.map(projected),orientation=Math.sign(polygonArea2(loop))||1;
  loop.forEach((point,index)=>{
    const prev=projectedLoop[(index-1+loop.length)%loop.length],cur=projectedLoop[index],next=projectedLoop[(index+1)%loop.length];
    const incoming=[cur[0]-prev[0],cur[1]-prev[1]],outgoing=[next[0]-cur[0],next[1]-cur[1]];
    let turn=Math.atan2(incoming[0]*outgoing[1]-incoming[1]*outgoing[0],incoming[0]*outgoing[0]+incoming[1]*outgoing[1]);
    if(orientation<0)turn=-turn;let interior=Math.PI-turn;if(interior<=0)interior+=Math.PI*2;
    // A2 polygon angles are integer multiples of pi/6. Store those exact
    // combinatorial units so frontier ordering is stable across JS runtimes.
    map.set(a2Key(point),{point,weight:Math.round(interior*6/Math.PI)});
    segmentLatticePoints(point,loop[(index+1)%loop.length]).slice(1,-1).forEach(p=>map.set(a2Key(p),{point:p,weight:6}));
  });
  const xs=loop.map(p=>p[0]),ys=loop.map(p=>p[1]);
  for(let x=Math.min(...xs);x<=Math.max(...xs);x++)for(let y=Math.min(...ys);y<=Math.max(...ys);y++){
    const p=[x,y,-x-y];if(!map.has(a2Key(p))&&pointInPolygon([x,y],loop.map(([q,r])=>[q,r])))map.set(a2Key(p),{point:p,weight:12});
  }
  return map;
}

const cellVertices = (q,r,kind) => kind==="u"
  ? [[q,r],[q+1,r],[q,r+1]]
  : [[q+1,r+1],[q,r+1],[q+1,r]];
const cellKey = (q,r,kind) => `${q},${r},${kind}`;

function polygonCells(loop) {
  if (!loop?.length) return new Set();
  const axial=loop.map(([x,y])=>[x,y]);
  const xs=axial.map(p=>p[0]), ys=axial.map(p=>p[1]);
  const cells=new Set();
  for(let q=Math.floor(Math.min(...xs))-1;q<=Math.ceil(Math.max(...xs))+1;q++){
    for(let r=Math.floor(Math.min(...ys))-1;r<=Math.ceil(Math.max(...ys))+1;r++){
      for(const kind of ["u","d"]){
        const vertices=cellVertices(q,r,kind);
        const center=[vertices.reduce((s,p)=>s+p[0],0)/3,vertices.reduce((s,p)=>s+p[1],0)/3];
        if(pointInPolygon(center,axial)) cells.add(cellKey(q,r,kind));
      }
    }
  }
  return cells;
}

function makeHexBoundary(radius) {
  const r=Math.max(2,radius|0);
  return [[r,0,-r],[r,-r,0],[0,-r,r],[-r,0,r],[-r,r,0],[0,r,-r]];
}

function orientationSignature(loop){return loop.map(a2Key).sort().join("|");}
function tileOrientations(tile, loop) {
  const base=normalizedLoop(loop), seen=new Set(), result=[];
  for(const symmetry of A2_SYMMETRIES){
    const transformed=normalizedLoop(base.map(point=>a2Transform(point,symmetry)));
    const signature=orientationSignature(transformed);
    if(seen.has(signature))continue;
    seen.add(signature);
    result.push({tile,symmetry,loop:transformed,cells:polygonCells(transformed),occupancy:polygonOccupancy(transformed),index:result.length});
  }
  return result;
}

const translatedCellKey = (key,translation) => {
  const [q,r,kind]=key.split(",");
  return cellKey(+q+translation[0],+r+translation[1],kind);
};
const translatedLoop = placement => placement.orientation.loop.map(point=>a2Add(point,placement.translation));

function enumeratePlacements(boundary, desired, tileDefs) {
  const minQ=Math.min(...boundary.map(p=>p[0])),maxQ=Math.max(...boundary.map(p=>p[0]));
  const minR=Math.min(...boundary.map(p=>p[1])),maxR=Math.max(...boundary.map(p=>p[1]));
  const placements=[];
  for(const [tile,loop] of Object.entries(tileDefs)){
    for(const orientation of tileOrientations(tile,loop)){
      const own=[...orientation.occupancy.values()].map(entry=>entry.point);
      const ownMinQ=Math.min(...own.map(p=>p[0])),ownMaxQ=Math.max(...own.map(p=>p[0]));
      const ownMinR=Math.min(...own.map(p=>p[1])),ownMaxR=Math.max(...own.map(p=>p[1]));
      for(let q=minQ-ownMinQ;q<=maxQ-ownMaxQ;q++)for(let r=minR-ownMinR;r<=maxR-ownMaxR;r++){
        const translation=[q,r,-q-r];
        const occupancy=new Map([...orientation.occupancy.values()].map(entry=>{const point=a2Add(entry.point,translation);return[a2Key(point),{point,weight:entry.weight}]}));
        const loop=translatedLoop({orientation,translation});
        if(polygonContained(loop,boundary)&&[...occupancy].every(([key,entry])=>desired.has(key)&&entry.weight<=desired.get(key).weight+1e-7)) placements.push({
          id:`${tile}:${orientation.index}:${a2Key(translation)}`,tile,orientation,translation,occupancy,
          loop
        });
      }
    }
  }
  return placements;
}

class SignedUnionFind{
  constructor(keys){this.parent=new Map([...keys].map(key=>[key,key]));this.sign=new Map([...keys].map(key=>[key,1]));}
  clone(){const copy=new SignedUnionFind([]);copy.parent=new Map(this.parent);copy.sign=new Map(this.sign);return copy;}
  find(key){const parent=this.parent.get(key);if(parent===key)return{root:key,sign:1};const found=this.find(parent),sign=this.sign.get(key)*found.sign;this.parent.set(key,found.root);this.sign.set(key,sign);return{root:found.root,sign};}
  union(left,right,relation){const a=this.find(left),b=this.find(right);if(a.root===b.root)return a.sign===relation*b.sign;if(a.root<b.root){this.parent.set(b.root,a.root);this.sign.set(b.root,relation*a.sign*b.sign);}else{this.parent.set(a.root,b.root);this.sign.set(a.root,relation*b.sign*a.sign);}return true;}
}

const permutationParity=permutation=>((permutation[0]>permutation[1])+(permutation[0]>permutation[2])+(permutation[1]>permutation[2]))%2===0?1:-1;
const lexicalCompare=(left,right)=>left<right?-1:left>right?1:0;
const A2_MARK_ENTRY_CACHE_LIMIT=4096;
const cacheMarkEntries=(cache,key,value)=>{if(cache.size>=A2_MARK_ENTRY_CACHE_LIMIT&&!cache.has(key))cache.delete(cache.keys().next().value);cache.set(key,value);return value;};

class OnlineA2Marking {
  constructor({maxWitnessTrials=Infinity,yieldEvery=32,fixedLive=false,initialRank=3,maxRank=3,enableLocalInequalities=true}={}){
    this.maxWitnessTrials=maxWitnessTrials;this.yieldEvery=yieldEvery;
    this.fixedLive=fixedLive;
    this.support=new Map();this.assignments=new Map();this.liveAssignments=new Map();this.inequalities=[];
    this.failures=[];this.failureLedger=[];this.pendingFailures=[];this.prefixes=[];this.bestPrefix=[];this.contacts=new Map();this.variableContacts=new Map();this.liveContext=[];this.liveStack=[];this.pendingStates=new Map();this.history=[];
    this.rejectedWitnesses=new Set();this.reencodeCursor=-1;this.revision=0;this.prunes=0;
    this.unencodable=0;this.skipped=0;this.reencodings=0;
    this.rank=Math.max(3,Math.ceil(initialRank/3)*3);this.maxRank=Math.max(this.rank,Math.ceil(maxRank/3)*3);this.rankExpansions=0;this.enableLocalInequalities=!!enableLocalInequalities;this.geometricRevision=0;
    this.geometricMemo=new GeometricFailureMemo({contextMatch:"exact",describePlacement:placement=>placement?.orientation&&placement?.translation?{kind:placement.tile,orientation:placement.orientation.index,translation:placement.translation}:null});
    this.frontierFailures=new Set();this.frontierPrunes=0;
  }
  site(tile,point,component){return `${tile}:${a2Key(point)}:${component}`;}
  rememberPositive(prefix){if(prefix.length>this.bestPrefix.length)this.bestPrefix=prefix.slice();}
  entries(placement,support=this.support,assignments=this.liveAssignments){
    const result=new Map(),symmetry=placement.orientation.symmetry,coefficient=permutationParity(symmetry.permutation);
    for(const mark of support.values()){
      if(mark.tile!==placement.tile)continue;
      const global=a2Add(a2Transform(mark.point,symmetry),placement.translation),component=symmetry.permutation.indexOf(mark.component);
      result.set(`${a2Key(global)}|${component}`,{key:mark.key,coefficient,value:(assignments.get(mark.key)||0)*coefficient});
    }
    return result;
  }
  compatible(candidate,context,support=this.support,assignments=this.assignments,count=true){
    if(support===this.support&&!this.geometricMemo.compatible(candidate,context,count))return false;
    if(!support.size)return true;
    if(support===this.support){
      if(!this.fixedLive){
        const trial=this.extendState(this.liveUnion,this.variableContacts,candidate);
        if(!trial){if(count)this.prunes++;return false;}
        this.pendingStates.set(candidate.id,trial);return true;
      }
      for(const [contact,entry] of this.entries(candidate,support,this.assignments)){
        const old=this.contacts.get(contact);
        if(old&&old.value!==entry.value){if(count)this.prunes++;return false;}
      }
      return true;
    }
    const previous=support===this.support&&assignments===this.assignments?this.contacts:new Map();
    if(previous!==this.contacts)for(const placement of context)for(const [contact,entry] of this.entries(placement,support,assignments))if(!previous.has(contact))previous.set(contact,entry.value);
    for(const [contact,entry] of this.entries(candidate,support,assignments)){const old=previous.get(contact);if(old!==undefined&&(old.value??old)!==entry.value){if(count)this.prunes++;return false;}}
    return true;
  }
  rebuildContacts(){this.contacts=new Map();}
  reset(context=[]){
    if(!this.fixedLive){
      const base=this.unionFor([this.bestPrefix,...this.prefixes],this.support)??new SignedUnionFind(this.support.keys());
      this.liveContext=[];this.liveStack=[{union:base,contacts:new Map()}];
      for(const placement of context){const prior=this.liveStack.at(-1),state=this.extendState(prior.union,prior.contacts,placement);if(!state)break;this.liveContext.push(placement);this.liveStack.push(state);}
      const state=this.liveStack.at(-1);this.liveUnion=state.union;this.variableContacts=state.contacts;this.liveAssignments=this.assignments;this.pendingStates.clear();return;
    }
    this.contacts=new Map();this.liveAssignments=this.assignments;
    for(const placement of context)this.push(placement);
  }
  push(placement){
    if(!this.fixedLive){
      const state=this.pendingStates.get(placement.id)??this.extendState(this.liveUnion,this.variableContacts,placement);
      this.liveContext.push(placement);this.liveStack.push(state);this.liveUnion=state.union;this.variableContacts=state.contacts;this.liveAssignments=this.assignments;this.pendingStates.clear();return;
    }
    for(const [contact,entry] of this.entries(placement,this.support,this.assignments)){
      const old=this.contacts.get(contact);this.contacts.set(contact,{value:entry.value,count:(old?.count||0)+1});
    }
  }
  pop(placement){
    if(!this.fixedLive){
      this.liveContext.pop();this.liveStack.pop();const state=this.liveStack.at(-1);
      this.liveUnion=state?.union??new SignedUnionFind(this.support.keys());this.variableContacts=state?.contacts??new Map();this.liveAssignments=this.assignments;this.pendingStates.clear();return;
    }
    for(const [contact] of this.entries(placement,this.support,this.assignments)){
      const old=this.contacts.get(contact);if(!old)continue;
      if(old.count<=1)this.contacts.delete(contact);else this.contacts.set(contact,{...old,count:old.count-1});
    }
  }
  score(candidate){if(!this.fixedLive)return 0;let matches=0,lineUps=0;for(const [contact,entry] of this.entries(candidate,this.support,this.assignments)){const old=this.contacts.get(contact);if(old?.value===entry.value){matches++;if(entry.value)lineUps++;}}return lineUps*100+matches;}
  rememberFrontierFailure(signature){if(signature)this.frontierFailures.add(signature);}
  frontierCompatible(signature,count=true){if(!signature||!this.frontierFailures.has(signature))return true;if(count)this.frontierPrunes++;return false;}
  fixLive(){this.fixedLive=true;this.reset();return this;}
  unionFor(prefixes,support){
    const union=new SignedUnionFind(support.keys());
    for(const prefix of prefixes){
      const contacts=new Map();
      for(const placement of prefix)for(const [contact,entry] of this.entries(placement,support,new Map())){
        const previous=contacts.get(contact);
        if(previous&&!union.union(entry.key,previous.key,entry.coefficient*previous.coefficient))return null;
        if(!previous)contacts.set(contact,entry);
      }
    }
    return union;
  }
  feasible(union,inequalities=this.inequalities){
    for(const inequality of inequalities){const left=union.find(inequality.left),right=union.find(inequality.right);if(left.root===right.root&&left.sign===inequality.relation*right.sign)return false;}
    return true;
  }
  extendState(union,contacts,placement){
    const nextUnion=union.clone(),nextContacts=new Map(contacts);
    for(const [contact,entry] of this.entries(placement,this.support,new Map())){
      const previous=nextContacts.get(contact);
      if(previous&&!nextUnion.union(entry.key,previous.key,entry.coefficient*previous.coefficient))return null;
      if(!previous)nextContacts.set(contact,entry);
    }
    return this.feasible(nextUnion)?{union:nextUnion,contacts:nextContacts}:null;
  }
  realize(union,support,inequalities){
    const constraints=[];
    for(const inequality of inequalities){
      const left=union.find(inequality.left),right=union.find(inequality.right);
      const relation=inequality.relation*left.sign*right.sign;
      if(left.root===right.root&&relation===1)return null;
      constraints.push({left:left.root,right:right.root,relation});
    }
    // Real values are unrestricted.  Choose a conservative realization that
    // reuses 0, then small signed integers, unless an explicit inequality
    // requires two equality classes to differ.  Unknown never means unequal.
    const roots=[...new Set([...support.keys()].map(key=>union.find(key).root))];
    const degree=new Map(roots.map(root=>[root,0]));
    for(const edge of constraints){degree.set(edge.left,(degree.get(edge.left)||0)+1);degree.set(edge.right,(degree.get(edge.right)||0)+1);}
    roots.sort((a,b)=>(degree.get(b)||0)-(degree.get(a)||0)||lexicalCompare(a,b));
    // Prefer the smallest signed values first. Zero remains available, but
    // making every unconstrained class zero creates accidental long-range
    // matches and performs poorly when the hypothesis is frozen for replay.
    // The palette is still unbounded with the number of equality classes.
    const rootValues=new Map(),palette=[];
    for(let value=1;value<=roots.length+1;value++)palette.push(value,-value);
    palette.push(0);
    for(const root of roots){
      const value=palette.find(candidate=>constraints.every(edge=>{
        if(edge.left!==root&&edge.right!==root)return true;
        const left=edge.left===root?candidate:rootValues.get(edge.left);
        const right=edge.right===root?candidate:rootValues.get(edge.right);
        return left===undefined||right===undefined||left!==edge.relation*right;
      }));
      if(value===undefined)return null;
      rootValues.set(root,value);
    }
    const assignments=new Map();
    for(const key of support.keys()){const found=union.find(key);assignments.set(key,found.sign*rootValues.get(found.root));}
    return assignments;
  }
  assignmentsFor(prefixes,support,inequalities){const union=this.unionFor(prefixes,support);return union&&this.feasible(union,inequalities)?this.realize(union,support,inequalities):null;}
  solveFailureClauses(support,positivePrefixes,failures){
    const union=this.unionFor(positivePrefixes,support);if(!union)return null;
    const inequalities=[];
    for(const failure of failures){
      let selected=null;
      const priorIndex=this.failures.indexOf(failure),prior=priorIndex>=0?this.inequalities[priorIndex]:null;
      if(prior&&support.has(prior.left)&&support.has(prior.right)&&this.feasible(union,[prior]))selected=prior;
      if(selected){inequalities.push(selected);continue;}
      for(const witness of this.witnesses(failure.candidate,failure.context,failure)){
        if(!witness.sites.every(entry=>support.has(entry.key)))continue;
        const inequality={left:witness.sites[0].key,right:witness.sites[1].key,relation:witness.relation,witnessKey:`${failure.candidate.id}|${witness.sites.map(entry=>entry.key).sort().join("::")}|${witness.relation}`,sourceGlobal:witness.sourceGlobal,branchDepth:failure.failedBranch.length};
        if(this.feasible(union,[inequality])){selected=inequality;break;}
      }
      if(!selected)return null;
      inequalities.push(selected);
    }
    const assignments=this.realize(union,support,inequalities);if(!assignments)return null;
    return{assignments,inequalities};
  }
  *witnesses(candidate,context,{failurePoint=null,failurePoints=[],failureFootprint=[],failedBranch=[],frontier=[],componentStart=0}={}){
    // D_c grows only over the actual failed branch footprint. There is no
    // revision-indexed shell: a local failure stays local, while a branch that
    // reaches farther before unwinding may justify correspondingly long probes.
    const globalPoints=[],seenGlobal=new Set(),addGlobal=point=>{if(!point)return;const key=a2Key(point);if(!seenGlobal.has(key)){seenGlobal.add(key);globalPoints.push(point);}};
    const asPoint=point=>typeof point==="string"?point.split(",").map(Number):point;
    addGlobal(asPoint(failurePoint));
    for(const point of failurePoints)addGlobal(asPoint(point));
    for(const point of failureFootprint)addGlobal(asPoint(point));
    for(const placement of failedBranch.slice().reverse())for(const entry of placement.occupancy.values())addGlobal(entry.point);
    for(const entry of candidate.occupancy.values())addGlobal(entry.point);
    const candidateContacts=new Set(candidate.occupancy.keys());
    // The memo is attached at the interface where this branch left the
    // current frontier. Unrelated frontier tiles are not allowed to acquire a
    // long domain merely because they happened to coexist with the failure.
    const adjacent=context.filter(placement=>[...placement.occupancy.keys()].some(key=>candidateContacts.has(key)));
    const frontierContext=frontier.length?frontier:adjacent;
    const orderedContext=frontierContext.slice().reverse();
    const candidateCoefficient=permutationParity(candidate.orientation.symmetry.permutation);
    for(const global of globalPoints){
      const point=a2InverseTransform(a2Sub(global,candidate.translation),candidate.orientation.symmetry);
      for(const placement of orderedContext){
        const local=a2InverseTransform(a2Sub(global,placement.translation),placement.orientation.symmetry);
        const relation=candidateCoefficient*permutationParity(placement.orientation.symmetry.permutation);
        for(let component=componentStart;component<this.rank;component++){
          const block=Math.floor(component/3),localComponent=component%3,globalComponent=candidate.orientation.symmetry.permutation.indexOf(localComponent),previousComponent=block*3+placement.orientation.symmetry.permutation[globalComponent];
          yield{sites:[{key:this.site(candidate.tile,point,component),tile:candidate.tile,point:[...point],component},{key:this.site(placement.tile,local,previousComponent),tile:placement.tile,point:local,component:previousComponent}],relation,sourceGlobal:[...global]};
        }
      }
    }
  }
  async learn(context,candidate,{shouldStop=()=>false,onProgress=()=>{},alternatives=[],failurePoint=null,failurePoints=[],failureFootprint=[],failedBranch=[],frontier=[],defer=false}={}){
    const failureCertificate={context:context.slice(),candidate,alternatives:alternatives.slice(),failedBranch:failedBranch.slice(),failurePoint,failurePoints:failurePoints.map(as=>typeof as==="string"?as:[...as]),failureFootprint:failureFootprint.map(point=>[...point]),frontier:frontier.slice()};
    this.failureLedger.push(failureCertificate);
    const geometricUpdate=this.geometricMemo.encode(context,candidate,{failure:this.failureLedger.length,branchDepth:failedBranch.length});
    if(!geometricUpdate.duplicate)this.geometricRevision++;
    if(!this.enableLocalInequalities)return{committed:true,geometric:true,geometricRevision:this.geometricRevision,revision:this.revision,branchDepth:failedBranch.length,subtreeSites:failureFootprint.length,leafFailures:failurePoints.length,frontierTiles:frontier.length};
    if(defer){this.pendingFailures.push(failureCertificate);return{skipped:true,attempts:0,pending:false,pairPending:true,geometric:true,reason:"rank-3-witness-deferred"};}
    if(!context.length){this.unencodable++;this.pendingFailures.push(failureCertificate);return{skipped:true,attempts:0,pending:false,pairPending:true,geometric:true,reason:"no-rank-3-interface"};}
    const prefixes=[...this.prefixes,context.slice()],positivePrefixes=[this.bestPrefix,...prefixes],failures=[...this.failures,failureCertificate];
    let attempts=0,best=null,componentStart=0;
    for(;;){
      let rankAttempts=0;
      for(const witness of this.witnesses(candidate,context,{failurePoint,failurePoints,failureFootprint,failedBranch,frontier,componentStart})){
        if(shouldStop())return{aborted:true,attempts};
        const witnessKey=`${candidate.id}|${witness.sites.map(entry=>entry.key).sort().join("::")}|${witness.relation}`;
        if(this.rejectedWitnesses.has(witnessKey))continue;
        attempts++;rankAttempts++;
        if(attempts%this.yieldEvery===0){onProgress(attempts);await new Promise(requestAnimationFrame);}
        if(rankAttempts>this.maxWitnessTrials)break;
        const support=new Map([...this.support].map(([key,entry])=>[key,{...entry,point:[...entry.point]}]));
        for(const entry of witness.sites)if(!support.has(entry.key))support.set(entry.key,entry);
        const solved=this.solveFailureClauses(support,positivePrefixes,failures);if(!solved)continue;
        const {assignments,inequalities}=solved;
        const reach=Math.max(...witness.sites.map(entry=>Math.max(...entry.point.map(Math.abs))));
        const survivors=alternatives.reduce((count,placement)=>count+(this.assignmentsFor([...positivePrefixes,[...context,placement]],support,inequalities)?1:0),0);
        const added=witness.sites.reduce((count,entry)=>count+(this.support.has(entry.key)?0:1),0);
        if(!best||survivors>best.survivors||(survivors===best.survivors&&(added<best.added||(added===best.added&&reach<best.reach))))best={support,assignments,inequalities,witnessKey,reach,survivors,added,sourceGlobal:witness.sourceGlobal};
        if(survivors===alternatives.length)break;
        if(best&&rankAttempts>=Math.min(this.maxWitnessTrials,6))break;
      }
      if(best||this.rank>=this.maxRank)break;
      componentStart=this.rank;this.rank+=3;this.rankExpansions++;
    }
    if(!best){this.unencodable++;this.pendingFailures.push(failureCertificate);return{skipped:true,attempts,pending:false,pairPending:true,geometric:true,reason:"no-compatible-rank-3-witness"};}
    if(best.inequalities.length!==failures.length)throw new Error("Every learned failure must retain a geometric witness");
    if(failures.length!==this.failures.length+1||!this.failures.every((failure,index)=>failures[index]===failure))throw new Error("A marking update may not alter the failure ledger");
    this.history.push({support:this.support,assignments:this.assignments,inequalities:this.inequalities,prefixes:this.prefixes,failures:this.failures,revision:this.revision,witnessKey:best.witnessKey});
    this.support=best.support;this.assignments=best.assignments;this.inequalities=best.inequalities;this.prefixes=prefixes;this.failures=failures;this.revision++;
    const auditSupport=new Map(this.support);
    this.pendingFailures=this.pendingFailures.filter(failure=>this.compatible(failure.candidate,failure.context,auditSupport,this.assignments,false));
    return{revision:this.revision,rank:this.rank,supportSites:this.support.size,inequalities:this.inequalities.length,reach:best.reach,attempts,siblingSurvivors:best.survivors,siblingCount:alternatives.length,branchDepth:failedBranch.length,subtreeSites:failureFootprint.length,leafFailures:failurePoints.length,frontierTiles:frontier.length,sourceGlobal:best.sourceGlobal,failurePoint};
  }
  async reencodeLatest({shouldStop=()=>false,onProgress=()=>{}}={}){
    // Witnesses are provisional representatives of persistent failure clauses.
    // If the marking stalls, replace one representative while every other
    // inequality stays fixed and the target failure receives another witness.
    // Thus no failure is ever made admissible during an update.
    if(!this.failures.length)return null;
    const positivePrefixes=[this.bestPrefix,...this.prefixes],start=this.reencodeCursor<0?this.failures.length-1:this.reencodeCursor;
    let totalAttempts=0;
    for(let offset=0;offset<this.failures.length;offset++){
      const target=(start-offset+this.failures.length)%this.failures.length,certificate=this.failures[target],current=this.inequalities[target];
      const rejected=new Set(this.rejectedWitnesses);rejected.add(current.witnessKey);
      let attempts=0,best=null;
      for(const witness of this.witnesses(certificate.candidate,certificate.context,certificate)){
        if(shouldStop())return{aborted:true,attempts:totalAttempts+attempts};
        const witnessKey=`${certificate.candidate.id}|${witness.sites.map(entry=>entry.key).sort().join("::")}|${witness.relation}`;
        if(rejected.has(witnessKey))continue;
        attempts++;totalAttempts++;
        if(totalAttempts%this.yieldEvery===0){onProgress(totalAttempts);await new Promise(requestAnimationFrame);}
        if(attempts>this.maxWitnessTrials)break;
        const retainedKeys=new Set(this.inequalities.flatMap((inequality,index)=>index===target?[]:[inequality.left,inequality.right]));
        const support=new Map([...retainedKeys].map(key=>{const entry=this.support.get(key);return[key,{...entry,point:[...entry.point]}];}));
        for(const entry of witness.sites)if(!support.has(entry.key))support.set(entry.key,entry);
        const inequality={left:witness.sites[0].key,right:witness.sites[1].key,relation:witness.relation,witnessKey,sourceGlobal:witness.sourceGlobal,branchDepth:certificate.failedBranch.length};
        const inequalities=this.inequalities.slice();inequalities[target]=inequality;
        const assignments=this.assignmentsFor(positivePrefixes,support,inequalities);if(!assignments)continue;
        const reach=Math.max(...witness.sites.map(entry=>Math.max(...entry.point.map(Math.abs))));
        const survivors=certificate.alternatives.reduce((count,placement)=>count+(this.assignmentsFor([...positivePrefixes,[...certificate.context,placement]],support,inequalities)?1:0),0);
        const added=witness.sites.reduce((count,entry)=>count+(this.support.has(entry.key)?0:1),0);
        if(!best||survivors>best.survivors||(survivors===best.survivors&&(added<best.added||(added===best.added&&reach<best.reach))))best={support,assignments,inequalities,witnessKey,reach,survivors,added,sourceGlobal:witness.sourceGlobal};
        if(survivors===certificate.alternatives.length)break;
        if(best&&attempts>=Math.min(this.maxWitnessTrials,6))break;
      }
      if(!best)continue;
      if(best.inequalities.length!==this.failures.length)throw new Error("Re-encoding may not drop a failure clause");
      this.rejectedWitnesses=rejected;this.support=best.support;this.assignments=best.assignments;this.inequalities=best.inequalities;this.reencodeCursor=(target-1+this.failures.length)%this.failures.length;this.reencodings++;
      return{revision:this.revision,targetFailure:target+1,replacedWitness:current.witnessKey,witnessKey:best.witnessKey,reach:best.reach,attempts:totalAttempts,siblingSurvivors:best.survivors,siblingCount:certificate.alternatives.length,preservedFailures:this.failures.length,preservedInequalities:this.inequalities.length-1};
    }
    return null;
  }
  frozenFromState(state){
    const assignments=this.assignmentsFor([this.bestPrefix,...state.prefixes],state.support,state.inequalities)??state.assignments;
    return new SparseA2Marking([...state.support.values()].map(entry=>({...entry,point:[...entry.point],value:assignments.get(entry.key)??0})),{learnedRevisions:state.revision,inequalities:state.inequalities.length,rank:this.rank});
  }
  freeze(){return this.frozenFromState(this);}
  freezeCandidates(){
    const states=[...this.history.map(state=>({support:state.support,assignments:state.assignments,inequalities:state.inequalities,prefixes:state.prefixes,revision:state.revision})),this];
    const distinct=new Map();
    for(const state of states){const key=`${state.revision}|${state.support.size}|${state.inequalities.length}`;if(!distinct.has(key))distinct.set(key,this.frozenFromState(state));}
    return [...distinct.values()];
  }
  checkoutRevision(revision){
    const states=[...this.history.map(state=>({state,historyEntry:true})),{state:this,historyEntry:false}],match=states.find(entry=>entry.state.revision===revision);
    if(!match)throw new Error(`Unknown marking revision ${revision}`);
    const state=match.state;
    this.support=state.support;this.assignments=state.assignments;this.inequalities=state.inequalities;this.prefixes=state.prefixes;this.failures=state.failures??this.failures;this.revision=state.revision;
    this.history=this.history.filter(entry=>entry.revision<revision);
    this.reset();
    return this;
  }
  stats(){const geometric=this.geometricMemo.stats();return{revision:this.revision,geometricRevision:this.geometricRevision,rank:this.rank,rankExpansions:this.rankExpansions,localInequalitiesEnabled:this.enableLocalInequalities,supportSites:this.support.size,inequalities:this.inequalities.length,failures:this.failures.length,observedFailures:this.failureLedger.length,encodedFailures:this.failureLedger.length,pendingFailures:0,pairEncodedFailures:this.failures.length,pairPendingFailures:this.pendingFailures.length,geometricClauses:geometric.clauses,geometricPrunes:geometric.prunes,frontierClauses:this.frontierFailures.size,frontierPrunes:this.frontierPrunes,prunes:this.prunes+geometric.prunes+this.frontierPrunes,unencodable:this.unencodable,skipped:this.skipped,reencodings:this.reencodings,suspended:false,support:[...this.support.values()].map(entry=>{const value=this.liveAssignments.get(entry.key)??this.assignments.get(entry.key)??0;return{tile:entry.tile,point:[...entry.point],component:entry.component,value,color:value===0?0:value>0?value*2-1:-value*2};})};}
}

class NoA2Marking {
  compatible(){return true;}
  score(){return 0;}
  learn(){return null;}
  reset(){}
  push(){}
  pop(){}
  rememberFrontierFailure(){}
  frontierCompatible(){return true;}
  stats(){return{revision:0,supportSites:0,failures:0,prunes:0,unencodable:0,support:[]};}
}

class SparseA2Marking extends NoA2Marking{
  constructor(support=[],metadata={}){
    super();this.support=support.map(entry=>({...entry,point:[...entry.point]}));this.metadata={...metadata};this.contacts=new Map();this.entryCache=new Map();this.prunes=0;
  }
  entries(placement){
    const cacheKey=placement.id??`${placement.tile}:${placement.orientation.index}:${a2Key(placement.translation)}`;
    if(this.entryCache.has(cacheKey))return this.entryCache.get(cacheKey);
    const result=new Map(),symmetry=placement.orientation.symmetry,coefficient=permutationParity(symmetry.permutation);
    for(const mark of this.support){if(mark.tile!==placement.tile)continue;const global=a2Add(a2Transform(mark.point,symmetry),placement.translation),component=symmetry.permutation.indexOf(mark.component);result.set(`${a2Key(global)}|${component}`,mark.value*coefficient);}
    return cacheMarkEntries(this.entryCache,cacheKey,result);
  }
  compatible(candidate,context,count=true){for(const [contact,value] of this.entries(candidate)){const old=this.contacts.get(contact);if(old&&old.value!==value){if(count)this.prunes++;return false;}}return true;}
  reset(context=[]){this.contacts=new Map();for(const placement of context)this.push(placement);}
  push(placement){for(const [contact,value] of this.entries(placement)){const old=this.contacts.get(contact);this.contacts.set(contact,{value,count:(old?.count||0)+1});}}
  pop(placement){for(const [contact] of this.entries(placement)){const old=this.contacts.get(contact);if(!old)continue;if(old.count<=1)this.contacts.delete(contact);else this.contacts.set(contact,{...old,count:old.count-1});}}
  score(candidate){let matches=0,lineUps=0;for(const [contact,value] of this.entries(candidate)){const old=this.contacts.get(contact);if(old?.value===value){matches++;if(value)lineUps++;}}return lineUps*100+matches;}
  stats(){return{revision:this.metadata.learnedRevisions??0,supportSites:this.support.length,inequalities:this.metadata.inequalities??0,failures:0,prunes:this.prunes,unencodable:0,frozen:true,structured:!!this.metadata.structured,lineMask:this.metadata.lineMask,label:this.metadata.label,support:this.support.map(entry=>({...entry,point:[...entry.point],color:entry.value===0?0:entry.value>0?entry.value*2-1:-entry.value*2}))};}
}

const TURTLE_LINE_DOMAINS=[{from:0,to:10},{from:2,to:8},{from:0,to:6},{from:4,to:12}];
const TURTLE_MARK_SEGMENTS=TURTLE_LINE_DOMAINS.map((segment,index)=>({...segment,value:index?-1:1}));
const primitiveComponent=(a,b)=>{const d=a2Sub(b,a),steps=gcd3(d[0],d[1],d[2]),step=d.map(value=>value/steps);const component=step.findIndex((value,index)=>{const other=[0,1,2].filter(i=>i!==index);return step[other[0]]===step[other[1]]&&value===-2*step[other[0]];});return component<0?0:component;};
const extendedSegmentPoints=(a,b,extra)=>{const d=a2Sub(b,a),steps=gcd3(d[0],d[1],d[2]),step=d.map(value=>value/steps);return Array.from({length:steps+1+extra*2},(_,raw)=>a2Add(a,step.map(value=>value*(raw-extra))));};
const HAT_LINE_DOMAINS=[{from:0,to:6},{from:2,to:10},{from:4,to:12},{from:8,to:10}];
class FixedA2Marking extends NoA2Marking{
  constructor(extension=1,{pointFilter=null,rank=3,tiles=["turtle"]}={}){
    super();this.prunes=0;this.support=[];this.contacts=new Map();this.entryCache=new Map();this.rank=rank===1?1:3;
    this.extension=extension;this.lineDomains=new Map();
    for(const tile of new Set(tiles)){
      if(tile!=="turtle"&&(tile!=="hat"||this.rank!==1))throw new Error(`No fixed rank-${this.rank} marking for ${tile}`);
      const loop=A2_TILE_LOOPS[tile],origin=loop[0];
      const segments=tile==="turtle"?TURTLE_MARK_SEGMENTS:HAT_LINE_DOMAINS;
      this.lineDomains.set(tile,segments);
      for(const segment of segments){const a=loop[segment.from],b=loop[segment.to],component=this.rank===1?0:primitiveComponent(a,b),value=this.rank===1?1:segment.value;for(const point of extendedSegmentPoints(a,b,extension))this.support.push({tile,point:a2Sub(point,origin),component,value});}
      const markedPoints=new Set(this.support.filter(entry=>entry.tile===tile).map(entry=>a2Key(entry.point)));
      for(const entry of polygonOccupancy(loop).values()){
        const point=a2Sub(entry.point,origin);if(markedPoints.has(a2Key(point)))continue;
        for(let component=0;component<this.rank;component++)this.support.push({tile,point,component,value:0});
      }
      if(this.rank===3){
        const valuesByPoint=new Map();
        for(const entry of this.support){const key=a2Key(entry.point);if(!valuesByPoint.has(key))valuesByPoint.set(key,new Map());valuesByPoint.get(key).set(entry.component,entry.value);}
        for(const [key,values] of valuesByPoint){
          if([...values.values()].filter(value=>value!==0).length!==2)continue;
          const component=[0,1,2].find(index=>!values.has(index));if(component!==undefined)this.support.push({tile,point:key.split(",").map(Number),component,value:0});
        }
      }
    }
    if(pointFilter)this.support=this.support.filter(entry=>pointFilter(entry.point));
  }
  segments(placement){
    const loop=A2_TILE_LOOPS[placement.tile],origin=loop[0];
    const transform=point=>a2Add(a2Transform(a2Sub(point,origin),placement.orientation.symmetry),placement.translation);
    return (this.lineDomains.get(placement.tile)||[]).map(segment=>{
      const a=loop[segment.from],b=loop[segment.to],extended=extendedSegmentPoints(a,b,this.extension);
      return {fromPoint:transform(a),toPoint:transform(b),displayFromPoint:transform(extended[0]),displayToPoint:transform(extended.at(-1)),value:this.rank===1?1:segment.value*permutationParity(placement.orientation.symmetry.permutation)};
    });
  }
  entries(placement){
    const cacheKey=placement.id??`${placement.tile}:${placement.orientation.index}:${a2Key(placement.translation)}`;
    if(this.entryCache.has(cacheKey))return this.entryCache.get(cacheKey);
    const result=new Map(),symmetry=placement.orientation.symmetry,coefficient=this.rank===1?1:permutationParity(symmetry.permutation);
    for(const mark of this.support){if(mark.tile!==placement.tile)continue;const global=a2Add(a2Transform(mark.point,symmetry),placement.translation),component=this.rank===1?0:symmetry.permutation.indexOf(mark.component);result.set(`${a2Key(global)}|${component}`,mark.value*coefficient);}
    return cacheMarkEntries(this.entryCache,cacheKey,result);
  }
  compatible(candidate,context,count=true){
    for(const [contact,value] of this.entries(candidate)){const old=this.contacts.get(contact);if(old&&old.value!==value){if(count)this.prunes++;return false;}}
    return true;
  }
  reset(context=[]){this.contacts=new Map();for(const placement of context)this.push(placement);}
  push(placement){for(const [contact,value] of this.entries(placement)){const old=this.contacts.get(contact);this.contacts.set(contact,{value,count:(old?.count||0)+1});}}
  pop(placement){for(const [contact] of this.entries(placement)){const old=this.contacts.get(contact);if(!old)continue;if(old.count<=1)this.contacts.delete(contact);else this.contacts.set(contact,{...old,count:old.count-1});}}
  score(candidate){let matches=0,lineUps=0;for(const [contact,value] of this.entries(candidate)){const old=this.contacts.get(contact);if(old?.value===value){matches++;if(value)lineUps++;}}return lineUps*100+matches;}
  stats(){return{revision:0,supportSites:this.support.length,failures:0,prunes:this.prunes,unencodable:0,support:this.support.map(entry=>({...entry,point:[...entry.point],color:entry.value===0?0:entry.value>0?1:2}))};}
}

// Backward-compatible Turtle-only entry point for existing demos and experiments.
class FixedTurtleMarking extends FixedA2Marking {}

const a2ClusterProposalToken=(prior,candidate)=>`${prior.tile}:${prior.orientation.index}>${candidate.tile}:${candidate.orientation.index}@${a2Key(a2Sub(candidate.translation,prior.translation))}`;

function learnA2ClusterProposals(placements,{maxDistance=12,window=16}={}){
  const weights=new Map();
  for(let index=1;index<placements.length;index++){
    const candidate=placements[index],start=Math.max(0,index-window);
    for(let priorIndex=start;priorIndex<index;priorIndex++){
      const prior=placements[priorIndex],delta=a2Sub(candidate.translation,prior.translation);
      if(Math.max(...delta.map(Math.abs))>maxDistance)continue;
      const token=a2ClusterProposalToken(prior,candidate);
      weights.set(token,(weights.get(token)??0)+1+(priorIndex===index-1?3:0));
    }
  }
  return [...weights.entries()];
}


async function solveA2Tiling({boundary,seed=null,initialPlacements=[],fixedInitialPlacements=false,completePointGrowth=false,requiredPoints=null,requireViableFrontier=false,allowReflections=true,startPoints=[],tiles=["hat"],customTiles={},maximize=false,targetPlacements=500,preferredPlacements=[],clusterProposals=[],placementFilter=null,latticePointFilter=null,pointTarget=null,nodeLimit=250000,animationDelayMs=0,learningWarmupDepth=0,maxMarkingRevisions=Infinity,markingStagnationNodes=1200,randomSeed=1,branchPolicy="oldest-frontier",requireEdgeSharing=false,marking=null,auditFrontierGraph=false,waitForSearchDemand=null,onEvent=()=>{},stopToken={stop:false}}){
  if(requiredPoints!==null&&(!maximize||!completePointGrowth||!Array.isArray(requiredPoints)||requiredPoints.some(p=>!Array.isArray(p)||p.length!==3||!p.every(Number.isSafeInteger)||p.reduce((s,v)=>s+v,0)!==0)))throw new Error("Finite required points need complete point growth and integer A2 coordinates");
  if(requireViableFrontier&&requiredPoints===null)throw new Error("Viable frontier checks need finite required points");
  const requiredPointMap=requiredPoints===null?null:new Map(requiredPoints.map(p=>[a2Key(p),p]));
  const isRequired=key=>requiredPointMap===null||requiredPointMap.has(key);
  // Outer points are viability probes, not additional corona fill obligations.
  const isTracked=key=>requireViableFrontier||isRequired(key);
  const pointAllowed=point=>!latticePointFilter||latticePointFilter(point);
  const desired=polygonOccupancy(boundary),seedOrigin=seed?.loop?.[0]??[0,0,0],seedOccupancy=new Map([...(seed?polygonOccupancy(seed.loop):new Map())].filter(([,entry])=>pointAllowed(a2Sub(entry.point,seedOrigin))));
  const tileDefs={};for(const tile of tiles)tileDefs[tile]=customTiles[tile]??A2_TILE_LOOPS[tile];
  const orientedTiles=Object.entries(tileDefs).flatMap(([tile,loop])=>tileOrientations(tile,loop)).filter(orientation=>allowReflections||permutationParity(orientation.symmetry.permutation)>0).map(orientation=>({...orientation,occupancy:new Map([...orientation.occupancy].filter(([,entry])=>pointAllowed(entry.point)))}));
  const memoRadius=Math.max(1,...orientedTiles.map(orientation=>{const points=[...orientation.occupancy.values()].map(entry=>entry.point);let diameter=1;for(const left of points)for(const right of points)diameter=Math.max(diameter,...a2Sub(left,right).map(Math.abs));return diameter;}));
  const preferredRanks=new Map(preferredPlacements.map((id,index)=>[id,index]));
  const clusterWeights=new Map(clusterProposals);
  const candidateCache=new Map();
  // Signed elementary segments cancel on internal edges of the patch.
  const exposedBoundary = new Map();
  const boundaryEdgesFor = placement => placement.boundaryEdges ??= polygonBoundaryEdges(placement.loop);
  const updatePatchBoundary = (placement, change) => {
    if (!requireEdgeSharing) return;
    for (const edge of boundaryEdgesFor(placement)) {
      const next = (exposedBoundary.get(edge.key) ?? 0) + change * edge.direction;
      if (next === 0) exposedBoundary.delete(edge.key);
      else exposedBoundary.set(edge.key, next);
    }
  };
  const rebuildPatchBoundary = () => {
    if (!requireEdgeSharing) return;
    exposedBoundary.clear();
    if (seed) updatePatchBoundary(seed, 1);
    for (const placement of chosen) updatePatchBoundary(placement, 1);
  };
  const frontierGraph=new Map(),frontierGraphDeltaStack=[],candidateIncidence=new Map(),candidateLegal=new Map(),candidatesByOccupancy=new Map(),candidatesByMarking=new Map();
  let frontierGraphEpoch=0,frontierGraphFullBuilds=0,frontierGraphLocalUpdates=0,frontierGraphPointRevalidations=0,frontierGraphCandidateRevalidations=0,frontierGraphEdgeRevalidations=0;
  const cacheCandidates=(key,value)=>{if(candidateCache.size>=1024&&!candidateCache.has(key))candidateCache.delete(candidateCache.keys().next().value);candidateCache.set(key,value);return value;};
  const materializePlacement=placement=>{
    if(placement.occupancy&&placement.loop)return placement;
    placement.occupancy=new Map([...placement.orientation.occupancy.values()].map(entry=>{const point=a2Add(entry.point,placement.translation);return[a2Key(point),{point,weight:entry.weight}]}));
    placement.loop=translatedLoop(placement);
    return placement;
  };
  const targetAt=point=>maximize?(pointTarget?.(point)??12):desired.get(a2Key(point))?.weight??-Infinity;
  const candidatesForPoint=pointKey=>{
    if(candidateCache.has(pointKey))return candidateCache.get(pointKey);
    const target=maximize?pointKey.split(",").map(Number):desired.get(pointKey)?.point;if(!target)return[];
    const dedup=new Map();
    for(const orientation of orientedTiles)for(const anchor of orientation.occupancy.values()){
      const translation=a2Sub(target,anchor.point);
      const id=`${orientation.tile}:${orientation.index}:${a2Key(translation)}`;
      if(dedup.has(id))continue;
      if(maximize){dedup.set(id,{id,tile:orientation.tile,orientation,translation,occupancy:null,loop:null});continue;}
      const occupancy=new Map([...orientation.occupancy.values()].map(entry=>{const point=a2Add(entry.point,translation);return[a2Key(point),{point,weight:entry.weight}]}));
      const loop=translatedLoop({orientation,translation});
      if(![...occupancy].every(([key,entry])=>desired.has(key)&&entry.weight<=desired.get(key).weight+1e-7)||!polygonContained(loop,boundary))continue;
      dedup.set(id,{id,tile:orientation.tile,orientation,translation,occupancy,loop});
    }
    return cacheCandidates(pointKey,[...dedup.values()]);
  };
  const sameSymmetry=(left,right)=>left?.sign===right?.sign&&left?.permutation?.every((value,index)=>value===right?.permutation?.[index]);
  const initialChosen=initialPlacements.map(spec=>{
    const orientation=orientedTiles.find(candidate=>candidate.tile===(spec.tile??"turtle")&&sameSymmetry(candidate.symmetry,spec.orientation?.symmetry??spec.orientation));
    if(!orientation)throw new Error(`Unknown initial placement orientation for ${spec.tile??"turtle"}`);
    const translation=[...spec.translation],id=`${orientation.tile}:${orientation.index}:${a2Key(translation)}`;
    return materializePlacement({id,tile:orientation.tile,orientation,translation,occupancy:null,loop:null,generation:Number.isFinite(spec.generation)?spec.generation:null});
  });
  const startPointMap=new Map([...startPoints,...(requiredPointMap?.values()??[])].map(point=>[a2Key(point),point]));
  const learner=marking??new OnlineA2Marking(),markingSeed=seed?.markingPlacement??null,sums=new Map([...seedOccupancy].map(([key,entry])=>[key,entry.weight])),pointDepth=new Map([...seedOccupancy.keys()].map(key=>[key,0])),chosen=initialChosen.slice(),usedPlacements=new Set(initialChosen.map(placement=>placement.id)),exhaustedBranches=new Set();
  const placementGeneration=placement=>{const adjacent=[...placement.occupancy.keys()].map(key=>pointDepth.get(key)).filter(Number.isFinite);return adjacent.length?Math.min(...adjacent)+1:0;};
  initialChosen.forEach(placement=>{if(!Number.isFinite(placement.generation))placement.generation=completePointGrowth?0:placementGeneration(placement);for(const [key,entry] of placement.occupancy){const next=(sums.get(key)||0)+entry.weight;if(next>targetAt(entry.point)+1e-7)throw new Error(`Initial placements exceed the t-value maximum at ${key}`);pointDepth.set(key,Math.min(pointDepth.get(key)??Infinity,placement.generation));sums.set(key,next);}});
  rebuildPatchBoundary();
  for(const key of startPointMap.keys()){if(!sums.has(key))sums.set(key,0);pointDepth.set(key,0);}let nodes=0,backtracks=0,exactMemoPrunes=0,best=initialChosen.slice(),bestFilled=0,lastImprovementNode=0;
  // Track when a point first entered the current board independently of its
  // geometric generation, which is used for corona display and ranked search.
  const useBasePolicy=branchPolicy==="oldest-frontier";
  const pointIntroducedAt=useBasePolicy?new Map():null;
  const recordPointIntroductions=(placement,step)=>{
    if(pointIntroducedAt)for(const key of placement.occupancy.keys())if(!pointIntroducedAt.has(key))pointIntroducedAt.set(key,step);
  };
  const rebuildPointIntroductions=()=>{
    if(!pointIntroducedAt)return;
    pointIntroducedAt.clear();
    if (!maximize) for (const key of desired.keys()) pointIntroducedAt.set(key, 0);
    for(const key of seedOccupancy.keys())pointIntroducedAt.set(key,0);
    for(const key of startPointMap.keys())pointIntroducedAt.set(key,0);
    chosen.forEach((placement,index)=>recordPointIntroductions(placement,fixedInitialPlacements?0:index+1));
  };
  rebuildPointIntroductions();
  const frontierPattern=(pointKey,additions=null)=>{
    const center=pointKey.split(",").map(Number),tokens=[];
    for(let dq=-memoRadius;dq<=memoRadius;dq++)for(let dr=Math.max(-memoRadius,-dq-memoRadius);dr<=Math.min(memoRadius,-dq+memoRadius);dr++){
      const delta=[dq,dr,-dq-dr],point=a2Add(center,delta),key=a2Key(point);
      const value=(sums.get(key)||0)+(additions?.get(key)?.weight||0);
      if(value>0)tokens.push(`${dq},${dr}:${value}`);
    }
    return tokens.join(";");
  };
  const initialSites=seedOccupancy.size?[...seedOccupancy.values()].map(entry=>entry.point):startPoints.length?startPoints:[[0,0,0]],distanceCache=new Map();
  const distanceFromInitial=pointKey=>{
    if(distanceCache.has(pointKey))return distanceCache.get(pointKey);
    const point=pointKey.split(",").map(Number),distance=Math.min(...initialSites.map(origin=>Math.max(...point.map((value,index)=>Math.abs(value-origin[index])))));
    distanceCache.set(pointKey,distance);return distance;
  };
  const initialMarkingContext=markingSeed?[markingSeed]:[];learner.reset?.(initialMarkingContext);
  for(const placement of initialChosen){if(!learner.compatible(placement,initialMarkingContext,false))throw new Error(`Initial placements disagree on m-values at ${placement.id}`);learner.push?.(placement);initialMarkingContext.push(placement);}
  let rngState=(randomSeed|0)||1;const random=()=>((rngState=Math.imul(rngState,1664525)+1013904223|0)>>>0)/4294967296;
  const filledWeight=()=>[...desired].reduce((sum,[key,entry])=>sum+Math.min(entry.weight,sums.get(key)||0),0),totalWeight=[...desired.values()].reduce((sum,e)=>sum+e.weight,0);
  const branchKey=(candidate,context=chosen)=>`${context.map(placement=>placement.id).sort().join(";")}=>${candidate.id}`;
  const exhaustedByContext = new Map();
  let memoExcluded = new Set();
  const rememberExhaustedBranch = (candidate, context) => {
    exhaustedBranches.add(branchKey(candidate, context));
    if (!useBasePolicy && !requireEdgeSharing) return;
    const key = context.map(placement => placement.id).sort().join(";");
    const excluded = new Set(exhaustedByContext.get(key));
    excluded.add(candidate.id);
    exhaustedByContext.set(key, excluded);
  };
  const clusterProposalScore=candidate=>{
    let score=0;
    for(const prior of chosen)score+=clusterWeights.get(a2ClusterProposalToken(prior,candidate))??0;
    return score;
  };
  const addIncidence=(index,key,candidateId)=>{if(!index.has(key))index.set(key,new Set());index.get(key).add(candidateId);};
  const candidateMarkingKeys=placement=>typeof learner.entries==="function"?[...learner.entries(placement).keys()]:[];
  const rememberCandidateBeforeChange=(delta,candidateId)=>{if(delta&&!delta.candidates.has(candidateId))delta.candidates.set(candidateId,candidateLegal.has(candidateId)?candidateLegal.get(candidateId):undefined);};
  const indexCandidate=(placement,pointKey=null,delta=null)=>{
    materializePlacement(placement);
    let incidence=candidateIncidence.get(placement.id);
    if(!incidence){
      const markingEntries=typeof learner.entries==="function"?learner.entries(placement):new Map();
      incidence={placement,frontierPoints:new Set(),occupancyKeys:new Set(placement.occupancy.keys()),markingKeys:new Set(markingEntries.keys()),markingEntries};
      candidateIncidence.set(placement.id,incidence);
      for(const key of incidence.occupancyKeys)addIncidence(candidatesByOccupancy,key,placement.id);
      for(const key of incidence.markingKeys)addIncidence(candidatesByMarking,key,placement.id);
    }
    if(!candidateLegal.has(placement.id)){rememberCandidateBeforeChange(delta,placement.id);candidateLegal.set(placement.id,candidateIsLegal(placement,{ignoreMemo:useBasePolicy||requireEdgeSharing}));frontierGraphCandidateRevalidations++;}
    if(pointKey!==null)incidence.frontierPoints.add(pointKey);
    return incidence;
  };
  const candidateIsLegal=(placement,{ignoreMarking=false,count=false,ignoreMemo=false}={})=>{
    if(usedPlacements.has(placement.id)||(!ignoreMemo&&!requireViableFrontier&&exhaustedBranches.has(branchKey(placement))))return false;
    let newPoints=0;
    materializePlacement(placement);
    for(const [key,entry] of placement.occupancy){
      const current=sums.get(key)||0,target=targetAt(entry.point);
      if(current+entry.weight>target+1e-7)return false;
      if(current<1e-7)newPoints++;
    }
    if(maximize&&placementFilter&&!placementFilter(placement))return false;
    if(maximize&&!completePointGrowth&&!newPoints)return false;
    if(!maximize&&(chosen.some(other=>polygonsOverlap(placement.loop,other.loop))||(seed&&polygonsOverlap(placement.loop,seed.loop))))return false;
    return ignoreMarking||learner.compatible(placement,markingSeed?[markingSeed,...chosen]:chosen,count);
  };
  const sharedFrontierEdge = (placement, pointKey) => {
    for (const edge of boundaryEdgesFor(placement)) {
      if (edge.from !== pointKey && edge.to !== pointKey) continue;
      if (exposedBoundary.get(edge.key) === -edge.direction) return edge;
    }
    return null;
  };
  // Unoccupied anchors can start a patch or a disconnected finite component.
  const sharesFrontierEdge = (placement, pointKey) =>
    !requireEdgeSharing || !(sums.get(pointKey) > 0) || sharedFrontierEdge(placement, pointKey) !== null;
  const legalAt=(point,limit=Infinity,ignoreMarking=false)=>{
    const legal=[];
    for(const placement of candidatesForPoint(point)){
      if(!candidateIsLegal(placement,{ignoreMarking}))continue;
      if(!sharesFrontierEdge(placement,point))continue;
      legal.push(placement);if(legal.length>=limit)break;
    }
    return legal;
  };
  const frontierMeta=pointKey=>{
    if(!isTracked(pointKey))return null;
    const value=sums.get(pointKey)||0,point=pointKey.split(",").map(Number),target=targetAt(point);
    if(!((value>1e-7||startPointMap.has(pointKey))&&value<target-1e-7))return null;
    return{point:pointKey,value,distance:distanceFromInitial(pointKey),introduced:pointDepth.get(pointKey)??Infinity,norm:point.reduce((sum,coordinate)=>sum+Math.abs(coordinate),0)};
  };
  // Corona completion depends only on frontier t-values and generations, not
  // candidate degrees. Keep it local even when the marking learner rebuilds
  // candidate lists, and snapshot the minimum when an event is queued.
  const frontierGenerations=new Map(),frontierGenerationCounts=new Map();
  let minimumFrontierGeneration=null,frontierGenerationFullBuilds=0,frontierGenerationPointUpdates=0;
  const updateFrontierGeneration=key=>{
    frontierGenerationPointUpdates++;
    const value=sums.get(key)||0;
    const active=isTracked(key)&&(value>1e-7||startPointMap.has(key))&&value<targetAt(key.split(",").map(Number))-1e-7;
    const previous=frontierGenerations.get(key),next=active?(pointDepth.get(key)??Infinity):undefined;
    if(previous===next)return;
    if(previous!==undefined){
      const count=frontierGenerationCounts.get(previous)-1;
      if(count)frontierGenerationCounts.set(previous,count);else frontierGenerationCounts.delete(previous);
      frontierGenerations.delete(key);
    }
    if(next!==undefined){frontierGenerations.set(key,next);frontierGenerationCounts.set(next,(frontierGenerationCounts.get(next)||0)+1);}
    if(minimumFrontierGeneration===null||!frontierGenerationCounts.has(minimumFrontierGeneration)){
      minimumFrontierGeneration=frontierGenerationCounts.size?Math.min(...frontierGenerationCounts.keys()):null;
    }else if(next!==undefined)minimumFrontierGeneration=Math.min(minimumFrontierGeneration,next);
  };
  const rebuildFrontierGenerations=()=>{
    frontierGenerations.clear();frontierGenerationCounts.clear();minimumFrontierGeneration=null;
    for(const key of sums.keys())updateFrontierGeneration(key);
    frontierGenerationFullBuilds++;
  };
  const cloneFrontierOption=option=>option?{...option,legal:new Map(option.legal)}:null;
  const rememberPointBeforeChange=(delta,pointKey)=>{if(delta&&!delta.points.has(pointKey))delta.points.set(pointKey,cloneFrontierOption(frontierGraph.get(pointKey)));};
  const initializeFrontierPoint=(pointKey,meta=frontierMeta(pointKey),delta=null)=>{
    if(!meta)return null;
    const candidates=candidatesForPoint(pointKey),legal=new Map();
    for(const placement of candidates){
      indexCandidate(placement,pointKey,delta);frontierGraphEdgeRevalidations++;
      if(candidateLegal.get(placement.id)&&!memoExcluded.has(placement.id)&&sharesFrontierEdge(placement,pointKey))legal.set(placement.id,placement);
    }
    frontierGraphPointRevalidations++;
    const option={...meta,candidates,legal};frontierGraph.set(pointKey,option);return option;
  };
  const rebuildFrontierGraph=()=>{
    const contextKey = chosen.map(placement => placement.id).sort().join(";");
    memoExcluded = requireViableFrontier ? new Set() : exhaustedByContext.get(contextKey) ?? new Set();
    frontierGraph.clear();candidateIncidence.clear();candidateLegal.clear();candidatesByOccupancy.clear();candidatesByMarking.clear();
    for(const pointKey of sums.keys())initializeFrontierPoint(pointKey);
    frontierGraphFullBuilds++;
  };
  const affectedCandidateIds=(occupancyKeys,markingKeys)=>{
    const ids=new Set();
    for(const key of occupancyKeys)for(const id of candidatesByOccupancy.get(key)??[])ids.add(id);
    for(const key of markingKeys)for(const id of candidatesByMarking.get(key)??[])ids.add(id);
    return ids;
  };
  const updateFrontierGraphLocally=placement=>{
    const delta={epoch:frontierGraphEpoch,points:new Map(),candidates:new Map(),memoExcluded},occupancyKeys=new Set(placement.occupancy.keys()),markingEntries=typeof learner.entries==="function"?learner.entries(placement):new Map(),markingKeys=new Set(markingEntries.keys());
    const candidateIds=affectedCandidateIds(occupancyKeys,markingKeys),pointKeys=new Set(occupancyKeys),incidentByPoint=new Map();candidateIds.add(placement.id);
    const incidencePointsToRecheck = new Set();
    if (requireEdgeSharing) for (const edge of boundaryEdgesFor(placement)) {
      incidencePointsToRecheck.add(edge.from);
      incidencePointsToRecheck.add(edge.to);
      pointKeys.add(edge.from);
      pointKeys.add(edge.to);
    }
    const contextPrefix=chosen.map(candidate=>candidate.id).sort().join(";");
    memoExcluded = requireViableFrontier ? new Set() : exhaustedByContext.get(contextPrefix) ?? new Set();
    // Exact failed branches belong to a placement context. Entering a child
    // must release its parent's exclusions and apply the child's own ones.
    for (const candidateId of new Set([...delta.memoExcluded, ...memoExcluded])) {
      for (const pointKey of candidateIncidence.get(candidateId)?.frontierPoints ?? []) {
        pointKeys.add(pointKey);
        incidencePointsToRecheck.add(pointKey);
      }
    }
    for(const candidateId of candidateIds){
      const incidence=candidateIncidence.get(candidateId);if(!incidence)continue;
      if(!candidateLegal.get(candidateId))continue;
      frontierGraphCandidateRevalidations++;
      let invalid=usedPlacements.has(candidateId)||(!useBasePolicy&&!requireEdgeSharing&&!requireViableFrontier&&exhaustedBranches.has(`${contextPrefix}=>${candidateId}`));
      if(!invalid)for(const key of occupancyKeys){
        const entry=incidence.placement.occupancy.get(key);if(!entry)continue;
        if((sums.get(key)||0)+entry.weight>targetAt(entry.point)+1e-7){invalid=true;break;}
      }
      if(!invalid)for(const key of markingKeys){
        const value=incidence.markingEntries.get(key),contact=learner.contacts?.get(key);
        if(value!==undefined&&contact&&contact.value!==value){invalid=true;break;}
      }
      if(!invalid&&!completePointGrowth&&![...incidence.placement.occupancy.keys()].some(key=>(sums.get(key)||0)<1e-7))invalid=true;
      if(invalid){rememberCandidateBeforeChange(delta,candidateId);candidateLegal.set(candidateId,false);}
      if(invalid)for(const pointKey of incidence.frontierPoints){
        if(!frontierGraph.get(pointKey)?.legal.has(candidateId))continue;
        pointKeys.add(pointKey);if(!incidentByPoint.has(pointKey))incidentByPoint.set(pointKey,[]);incidentByPoint.get(pointKey).push(candidateId);
      }
    }
    for(const pointKey of pointKeys){
      rememberPointBeforeChange(delta,pointKey);
      const meta=frontierMeta(pointKey),option=frontierGraph.get(pointKey);
      if(!meta){frontierGraph.delete(pointKey);continue;}
      if(!option){initializeFrontierPoint(pointKey,meta,delta);continue;}
      option.value=meta.value;option.distance=meta.distance;option.introduced=meta.introduced;option.norm=meta.norm;
      for(const candidateId of incidentByPoint.get(pointKey)??[]){
        frontierGraphEdgeRevalidations++;
        option.legal.delete(candidateId);
      }
      // Contact can appear as well as disappear. Recheck incidences at both
      // ends of each changed boundary segment, including previously absent ones.
      if (incidencePointsToRecheck.has(pointKey)) for (const candidate of option.candidates) {
        frontierGraphEdgeRevalidations++;
        if (candidateLegal.get(candidate.id) && !memoExcluded.has(candidate.id) && sharesFrontierEdge(candidate, pointKey)) {
          option.legal.set(candidate.id, candidate);
        } else {
          option.legal.delete(candidate.id);
        }
      }
      frontierGraphPointRevalidations++;
    }
    frontierGraphLocalUpdates++;return delta;
  };
  const restoreFrontierGraph=delta=>{
    if(!delta||delta.epoch!==frontierGraphEpoch){rebuildFrontierGraph();return;}
    memoExcluded = delta.memoExcluded;
    for(const [key,option] of delta.points){if(option)frontierGraph.set(key,option);else frontierGraph.delete(key);}
    for(const [candidateId,legal] of delta.candidates){if(legal===undefined)candidateLegal.delete(candidateId);else candidateLegal.set(candidateId,legal);}
  };
  const graphNeedsGlobalPlacementUpdate=()=>learner instanceof OnlineA2Marking&&!learner.fixedLive;
  const updateGraphAfterPlacement=placement=>{
    for(const key of placement.occupancy.keys())updateFrontierGeneration(key);
    if(!maximize)return null;
    if(graphNeedsGlobalPlacementUpdate())return null;
    return updateFrontierGraphLocally(placement);
  };
  const invalidateExhaustedCandidate=candidateId=>{
    const incidence=candidateIncidence.get(candidateId);if(!incidence)return;
    const activeDelta=frontierGraphDeltaStack.at(-1)??null;let removed=false;
    if (!useBasePolicy && !requireEdgeSharing) {
      rememberCandidateBeforeChange(activeDelta, candidateId);
      candidateLegal.set(candidateId, false);
    }
    const contextKey = chosen.map(placement => placement.id).sort().join(";");
    memoExcluded = exhaustedByContext.get(contextKey) ?? new Set();
    for(const pointKey of incidence.frontierPoints){const option=frontierGraph.get(pointKey);if(!option?.legal.has(candidateId))continue;rememberPointBeforeChange(activeDelta,pointKey);option.legal.delete(candidateId);removed=true;}
    if(removed)exactMemoPrunes++;
  };
  const emit=(type,extra={})=>onEvent({type,nodes,backtracks,placed:chosen.length,minimumFrontierGeneration,targetPlacements:maximize?targetPlacements:null,totalCells:totalWeight,coveredCells:filledWeight(),marking:learner.stats(),searchMemo:{failures:exhaustedBranches.size,prunes:exactMemoPrunes},placements:chosen.slice(),...extra});
  rebuildFrontierGenerations();
  if(maximize&&!graphNeedsGlobalPlacementUpdate())rebuildFrontierGraph();
  emit("start",{orientationCount:orientedTiles.length});
  const noteFailedPath=(trackers,failurePoint=null)=>{
    for(const tracker of trackers){
      const path=chosen.slice(tracker.rootDepth);
      if(path.length>=tracker.path.length)tracker.path=path;
      for(const placement of path)for(const entry of placement.occupancy.values())tracker.footprint.set(a2Key(entry.point),entry.point);
      if(failurePoint){const point=typeof failurePoint==="string"?failurePoint.split(",").map(Number):failurePoint,key=a2Key(point);tracker.failurePoints.set(key,point);tracker.footprint.set(key,point);tracker.failurePoint=failurePoint;}
    }
  };
  async function search(depth=0,trackers=[]){
    if(waitForSearchDemand)await waitForSearchDemand();
    if(stopToken.stop)return "unknown";
    const coreComplete=requiredPointMap&&[...requiredPointMap].every(([key,p])=>(sums.get(key)||0)===targetAt(p));
    if(coreComplete&&!requireViableFrontier)return true;
    if(nodes>=nodeLimit&&!coreComplete)return "unknown";
    if(maximize&&learner.revision>0&&nodes-lastImprovementNode>=markingStagnationNodes)return "stagnant";
    if(!maximize&&[...desired].every(([key,entry])=>Math.abs((sums.get(key)||0)-entry.weight)<1e-7))return true;
    let choicePoint=null,options=null,choiceByPlacement=null,nearestDistance,baseChoiceInfo={forced:false,branchCount:0,frontierValue:0};
    const selectBaseOptions=frontier=>{
      const last = chosen.at(-1) ?? seed;
      const lastPoints = new Set(chosen.at(-1)?.occupancy.keys() ?? seedOccupancy.keys());
      const lastEdges = requireEdgeSharing && last
        ? new Map(boundaryEdgesFor(last).map(edge => [edge.key, edge.direction])) : null;
      const isAdjacent = placement => lastEdges
        ? boundaryEdgesFor(placement).some(edge => lastEdges.get(edge.key) === -edge.direction)
        : [...placement.occupancy.keys()].some(key => lastPoints.has(key));
      const selected = selectBaseTilingMoves(frontier, random, {
        restrictToPoint: !requireEdgeSharing, isAdjacent
      });
      let moves = selected.moves;
      const first = moves[0];
      const edge = requireEdgeSharing && first
        ? sharedFrontierEdge(first.placement, first.frontier.point) : null;
      if (edge && !selected.forced) {
        // Keep the uniform first draw from the full priority pool. That move
        // fixes one exposed segment to fill at this node, including on retries.
        const alternatives = new Set(first.frontier.legal.filter(placement =>
          boundaryEdgesFor(placement).some(candidate =>
            candidate.key === edge.key && candidate.direction === edge.direction
          )
        ).map(placement => placement.id));
        moves = moves.filter(move => alternatives.has(move.placement.id))
          .map(move => ({ ...move, frontier: first.frontier }));
      }
      options=moves.map(move=>move.placement);
      choiceByPlacement=new Map(moves.map(({placement,frontier})=>[placement.id,frontier]));
      baseChoiceInfo = {
        forced: selected.forced || options.length === 1,
        branchCount: options.length,
        nearestFrontierDistance: nearestDistance,
        branchEdge: edge ? [edge.from.split(",").map(Number), edge.to.split(",").map(Number)] : null
      };
    };
    if(maximize){
      // The frontier-candidate graph is the branching engine.
      const incrementalGraphActive=!graphNeedsGlobalPlacementUpdate();
      const frontier=(incrementalGraphActive?[...frontierGraph.values()]:[...sums].filter(([point,value])=>isTracked(point)&&value<targetAt(point.split(",").map(Number))-1e-7).map(([point,value])=>{
        const coordinates=point.split(",").map(Number);return{point,value,distance:distanceFromInitial(point),introduced:pointDepth.get(point)??Infinity,norm:coordinates.reduce((sum,v)=>sum+Math.abs(v),0)};
      })).sort((a,b)=>a.distance-b.distance||b.value-a.value||a.introduced-b.introduced||a.norm-b.norm||lexicalCompare(a.point,b.point));
      if(auditFrontierGraph&&incrementalGraphActive)for(const entry of frontier){
        const direct=new Set(legalAt(entry.point).map(placement=>placement.id)),incremental=new Set(entry.legal.keys());
        const missing=[...direct].filter(id=>!incremental.has(id)),extra=[...incremental].filter(id=>!direct.has(id));
        if(missing.length||extra.length)throw new Error(`Frontier graph divergence at ${entry.point}: missing ${missing.slice(0,3).join(",")}; extra ${extra.slice(0,3).join(",")}`);
      }
      if(!frontier.length)return true;
      nearestDistance=frontier[0].distance;
      const viable=[];
      for(const entry of frontier){
        const legal=incrementalGraphActive?[...entry.legal.values()]:legalAt(entry.point);
        if(!legal.length){if(!legalAt(entry.point,1,true).length)learner.rememberFrontierFailure?.(frontierPattern(entry.point));noteFailedPath(trackers,entry.point);emit("fail",{choice:entry.point,frontierValue:entry.value});return false;}
        if(isRequired(entry.point))viable.push({...entry,legal});
      }
      // Completing the core is only a success after all exposed points pass.
      if(coreComplete&&requireViableFrontier){emit("frontier-viable",{frontierPoints:frontier.length});return true;}
      // A growth checkpoint must pass the whole-frontier dead-point scan.
      if(!requiredPointMap&&chosen.length>=targetPlacements)return true;
      const byGeneration=(left,right)=>left.introduced-right.introduced||left.legal.length-right.legal.length||left.distance-right.distance||right.value-left.value||left.norm-right.norm||lexicalCompare(left.point,right.point);
      if(chosen.length>best.length){best=chosen.slice();bestFilled=filledWeight();lastImprovementNode=nodes;learner.rememberPositive?.(best);}
      if(useBasePolicy){
        selectBaseOptions(viable.map(entry=>({...entry,introducedAt:pointIntroducedAt.get(entry.point)})));
      }else{
        const forced=viable.filter(entry=>entry.legal.length===1).sort(byGeneration);
        const selected=forced[0]??viable.sort(byGeneration)[0];
        choicePoint=selected.point;
        options=selected.legal.map(placement=>{
          let atChoice=0,coverage=0,size=0;
          const materialized=!!placement.occupancy,source=materialized?placement.occupancy.values():placement.orientation.occupancy.values();
          for(const local of source){const entry=materialized?local:{point:a2Add(local.point,placement.translation),weight:local.weight},key=a2Key(entry.point);size++;if(key===choicePoint)atChoice=entry.weight;if((sums.get(key)||0)>0)coverage++;}
          const newPoints=size-coverage;
          const graphDegree=incrementalGraphActive?[...(candidateIncidence.get(placement.id)?.frontierPoints??[])].filter(pointKey=>frontierGraph.get(pointKey)?.legal.has(placement.id)).length:0;
          return{placement,clusterScore:clusterProposalScore(placement),markScore:learner.score?.(placement)??0,fills:selected.value+atChoice>=targetAt(choicePoint.split(",").map(Number))-1e-7,graphDegree,coverage,newPoints,tie:random()};
        }).sort((a,b)=>b.clusterScore-a.clusterScore||b.markScore-a.markScore||Number(b.fills)-Number(a.fills)||b.graphDegree-a.graphDegree||b.coverage-a.coverage||b.newPoints-a.newPoints||a.tie-b.tie).map(entry=>entry.placement);
        baseChoiceInfo={forced:options.length===1,branchCount:options.length,frontierValue:selected.value,frontierDistance:selected.distance,nearestFrontierDistance:nearestDistance};
      }
    }else if(useBasePolicy){
      const frontier=[];
      for(const [point,introducedAt] of pointIntroducedAt){
        const value=sums.get(point)||0,target=desired.get(point);
        if(target&&value<target.weight-1e-7)frontier.push({point,value,introducedAt});
      }
      // An empty board (or a new disconnected component) needs an anchor.
      if(!frontier.length)for(const [point,target] of desired){
        const value=sums.get(point)||0;
        if(value<target.weight-1e-7){frontier.push({point,value,introducedAt:chosen.length});break;}
      }
      for(const entry of frontier){
        entry.legal=legalAt(entry.point);
        if(!entry.legal.length){noteFailedPath(trackers,entry.point);emit("fail",{choice:entry.point,frontierValue:entry.value});return false;}
      }
      selectBaseOptions(frontier);
    }else{
      for(const [point,target] of desired){const current=sums.get(point)||0;if(current>=target.weight-1e-7)continue;
        const legal=legalAt(point).sort((left,right)=>(preferredRanks.get(left.id)??Infinity)-(preferredRanks.get(right.id)??Infinity));if(!legal.length){noteFailedPath(trackers,point);emit("fail",{choice:point,frontierValue:current});return false;}
        choicePoint=point;options=legal;baseChoiceInfo={forced:legal.length===1,branchCount:legal.length,frontierValue:current};break;
      }
    }
    if(!options)return false;
    for(const placement of options){
      const frontier=choiceByPlacement?.get(placement.id);
      const choice=frontier?.point??choicePoint;
      const choiceInfo=frontier?{...baseChoiceInfo,frontierValue:frontier.value,frontierDistance:frontier.distance,frontierIntroducedAt:frontier.introducedAt}:baseChoiceInfo;
      if(waitForSearchDemand)await waitForSearchDemand();
      if(stopToken.stop)return "unknown";
      if(nodes>=nodeLimit)return "unknown";
      if(requireViableFrontier&&exhaustedBranches.has(branchKey(placement)))continue;
      // A learned revision may have invalidated options computed earlier at this node.
      if(usedPlacements.has(placement.id)||!learner.compatible(placement,markingSeed?[markingSeed,...chosen]:chosen))continue;
      materializePlacement(placement);
      placement.generation=placementGeneration(placement);
      if(maximize&&[...placement.occupancy].some(([key,entry])=>isRequired(key)&&(sums.get(key)||0)+entry.weight<targetAt(entry.point)-1e-7&&!learner.frontierCompatible?.(frontierPattern(key,placement.occupancy))))continue;
      emit("trial",{candidate:placement,choice,...choiceInfo});
      if(animationDelayMs>0)await new Promise(resolve=>setTimeout(resolve,animationDelayMs));
      const context=chosen.slice(),candidateContacts=new Set(placement.occupancy.keys());
      const branchTracker={rootDepth:chosen.length,path:[],failurePoint:null,failurePoints:new Map(),footprint:new Map(),frontier:context.filter(prior=>[...prior.occupancy.keys()].some(key=>candidateContacts.has(key)))},childTrackers=[...trackers,branchTracker];
      nodes++;chosen.push(placement);usedPlacements.add(placement.id);learner.push?.(placement);for(const [key,e] of placement.occupancy){pointDepth.set(key,Math.min(pointDepth.get(key)??Infinity,placement.generation));sums.set(key,(sums.get(key)||0)+e.weight);}
      recordPointIntroductions(placement,chosen.length);
      updatePatchBoundary(placement,1);
      const frontierGraphDelta=updateGraphAfterPlacement(placement);
      if(maximize&&frontierGraphDelta)frontierGraphDeltaStack.push(frontierGraphDelta);
      noteFailedPath(childTrackers);
      const filled=filledWeight();if(!maximize&&filled>bestFilled){bestFilled=filled;best=chosen.slice();}
      emit("placement",{choice,...choiceInfo});await new Promise(requestAnimationFrame);
      // A placement can strand a different point than the one it just filled.
      // Detect that local certificate immediately instead of burying it beneath
      // thousands of unrelated outward moves.
      const stranded=maximize?[...placement.occupancy].find(([key,entry])=>isRequired(key)&&(sums.get(key)||0)<targetAt(entry.point)-1e-7&&(frontierGraphDelta?frontierGraph.get(key)?.legal.size===0:!legalAt(key,1).length))?.[0]??null:null;
      if(stranded){if(!legalAt(stranded,1,true).length)learner.rememberFrontierFailure?.(frontierPattern(stranded));noteFailedPath(childTrackers,stranded);emit("fail",{choice:stranded,frontierValue:sums.get(stranded)||0});}
      const result=stranded?false:await search(depth+1,childTrackers);
      if(result===true)return true;
      updatePatchBoundary(placement,-1);
      chosen.pop();usedPlacements.delete(placement.id);learner.pop?.(placement);for(const [key,e] of placement.occupancy){const next=(sums.get(key)||0)-e.weight;if(next<1e-7){if(startPointMap.has(key)){sums.set(key,0);pointDepth.set(key,0);}else{sums.delete(key);pointDepth.delete(key);}}else{const incident=[seedOccupancy.has(key)||startPointMap.has(key)?0:Infinity,...chosen.filter(prior=>prior.occupancy.has(key)).map(prior=>prior.generation)];sums.set(key,next);pointDepth.set(key,Math.min(...incident));}}if(frontierGraphDelta){restoreFrontierGraph(frontierGraphDelta);frontierGraphDeltaStack.pop();}
      for(const key of placement.occupancy.keys())updateFrontierGeneration(key);
      if(pointIntroducedAt)for(const key of placement.occupancy.keys())if(!sums.has(key))pointIntroducedAt.delete(key);
      if(result==="unknown"||result==="stagnant")return result;
      // This exact candidate and placement context has been exhausted. Keep it
      // across marking re-encodings: a new geometric witness may generalize a
      // permanent failure differently, but it may not make the same observed
      // failed branch unknown again.
      rememberExhaustedBranch(placement,context);
      // A failed corona extension is still a legal one-step frontier candidate.
      // Keep finite-search memo exclusions out of the geometric viability graph.
      if(maximize&&!requireViableFrontier)invalidateExhaustedCandidate(placement.id);
      backtracks++;emit("backtrack",{removed:placement,choice,...choiceInfo});
      if(animationDelayMs>0)await new Promise(resolve=>setTimeout(resolve,animationDelayMs));
      let update=null;
      // Record every exhausted branch alternative exactly once. Forced stack
      // frames merely carry the same descendant failure upward and are not new
      // branch decisions; encoding them again would over-generalize one failure.
      // The complete descendant footprint still bounds how far D_c may grow.
      if(options.length>1&&context.length){
        emit("learning-start",{removed:placement});
        update=await learner.learn(context,placement,{alternatives:options.filter(option=>option.id!==placement.id),failurePoint:branchTracker.failurePoint??stranded??choice,failurePoints:[...branchTracker.failurePoints.values()],failureFootprint:[...branchTracker.footprint.values()],failedBranch:branchTracker.path,frontier:branchTracker.frontier,defer:context.length<learningWarmupDepth||learner.revision>=maxMarkingRevisions,shouldStop:()=>stopToken.stop,onProgress:attempts=>emit("learning-progress",{attempts,removed:placement})});
        if(update?.revision||update?.geometricRevision){learner.reset?.(markingSeed?[markingSeed,...context]:context);frontierGraphEpoch++;if(maximize&&!graphNeedsGlobalPlacementUpdate())rebuildFrontierGraph();emit("learn",{update,removed:placement});}
        else if(update?.skipped)emit("learning-skip",{update,removed:placement});
      }
      if(nodes%32===0)await new Promise(requestAnimationFrame);
    }
    return false;
  }
  const initialDepth=initialChosen.length;
  let result=await search(initialDepth);
  // A retained live patch is a provisional search prefix, not a frozen
  // boundary condition. If it cannot continue under a newly selected mode,
  // unwind its newest placement and resume from the preceding graph state.
  while(!fixedInitialPlacements&&result===false&&chosen.length&&initialChosen.length&&!stopToken.stop){
    const removed=chosen[chosen.length-1],context=chosen.slice(0,-1);rememberExhaustedBranch(removed,context);
    chosen.pop();usedPlacements.delete(removed.id);learner.pop?.(removed);backtracks++;
    sums.clear();pointDepth.clear();for(const [key,e] of seedOccupancy){sums.set(key,e.weight);pointDepth.set(key,0);}chosen.forEach(placement=>{for(const [key,e] of placement.occupancy){pointDepth.set(key,Math.min(pointDepth.get(key)??Infinity,placement.generation));sums.set(key,(sums.get(key)||0)+e.weight);}});for(const key of startPointMap.keys()){if(!sums.has(key))sums.set(key,0);pointDepth.set(key,0);}
    rebuildPatchBoundary();rebuildPointIntroductions();rebuildFrontierGenerations();frontierGraphEpoch++;if(maximize&&!graphNeedsGlobalPlacementUpdate())rebuildFrontierGraph();emit("backtrack",{removed,reason:"retained-prefix"});
    result=await search(chosen.length);
  }
  while((result===false||result==="stagnant")&&!stopToken.stop){
    const reencoding=await learner.reencodeLatest?.({shouldStop:()=>stopToken.stop,onProgress:attempts=>emit("learning-progress",{attempts,reencoding:true})});if(!reencoding||reencoding.aborted)break;
    chosen.splice(0,chosen.length,...initialChosen);usedPlacements.clear();for(const placement of initialChosen)usedPlacements.add(placement.id);sums.clear();pointDepth.clear();
    for(const [key,e] of seedOccupancy){sums.set(key,e.weight);pointDepth.set(key,0);}initialChosen.forEach(placement=>{for(const [key,e] of placement.occupancy){pointDepth.set(key,Math.min(pointDepth.get(key)??Infinity,placement.generation));sums.set(key,(sums.get(key)||0)+e.weight);}});for(const key of startPointMap.keys()){if(!sums.has(key))sums.set(key,0);pointDepth.set(key,0);}
    learner.reset?.(markingSeed?[markingSeed,...initialChosen]:initialChosen);
    rebuildPatchBoundary();rebuildPointIntroductions();rebuildFrontierGenerations();
    frontierGraphEpoch++;if(maximize&&!graphNeedsGlobalPlacementUpdate())rebuildFrontierGraph();
    emit("marking-reencoded",{reencoding,reason:result==="stagnant"?"stagnation":"root-exhausted"});
    lastImprovementNode=nodes;
    const nodesBeforeRestart=nodes;
    result=await search(initialDepth);
    if(result===false&&nodes===nodesBeforeRestart){emit("memo-fixed-point",{reason:"all-root-options-memoized"});break;}
  }
  if(result!==true){
    chosen.splice(0,chosen.length,...best);sums.clear();pointDepth.clear();
    for(const [key,e] of seedOccupancy){sums.set(key,e.weight);pointDepth.set(key,0);}
    for(const p of chosen)for(const [key,e] of p.occupancy){sums.set(key,(sums.get(key)||0)+e.weight);pointDepth.set(key,Math.min(pointDepth.get(key)??Infinity,p.generation));}
    for(const key of startPointMap.keys()){if(!sums.has(key))sums.set(key,0);pointDepth.set(key,0);}
    rebuildFrontierGenerations();
  }
  emit("finished",{result:result===true?"yes":result===false?"no":"unknown"});
  return {result:result===true?"yes":result===false?"no":"unknown",placements:chosen,stats:{nodes,backtracks,exactMemoPrunes,memoizedBranches:exhaustedBranches.size,frontierGenerationFullBuilds,frontierGenerationPointUpdates,frontierGraphFullBuilds,frontierGraphLocalUpdates,frontierGraphPointRevalidations,frontierGraphCandidateRevalidations,frontierGraphEdgeRevalidations,...learner.stats()}};
}

// A failed branch is only a negative example for one local configuration.  A
// newly encoded geometric inequality can recognize many transformed copies of
// it, which is the source of both GCTS's leverage and its risk of
// over-generalization.  Select a revision on a fresh run before treating the
// learned marking as a reusable search add-on.  Revision zero is deliberately
// included as the safe, geometry-only fallback.
async function selectA2FrozenMarking({learner,solveOptions,validationSeed=2,validationSeeds=null,validationNodeLimit=3000,confirmationCandidates=2,onValidation=()=>{}}){
  const all=learner.freezeCandidates(),indexes=new Set([0,1,2,3,all.length-1]);
  for(let index=4;index<all.length;index*=2)indexes.add(index);
  const candidates=[...indexes].filter(index=>index>=0&&index<all.length).sort((a,b)=>a-b).map(index=>all[index]);
  return selectA2MarkingCandidates({candidates,solveOptions,validationSeed,validationSeeds,validationNodeLimit,confirmationCandidates,onValidation});
}

async function selectA2MarkingCandidates({candidates,solveOptions,validationSeed=2,validationSeeds=null,validationNodeLimit=3000,confirmationCandidates=2,onValidation=()=>{}}){
  if(!candidates.length)throw new Error("At least one marking hypothesis is required");
  const seeds=[...new Set((validationSeeds?.length?validationSeeds:[validationSeed]).map(Number).filter(Number.isFinite))];
  if(!seeds.length)seeds.push(validationSeed);
  const validation=[];
  const evaluate=async(marking,index,total,seed,round)=>{
    if(solveOptions.stopToken?.stop)return null;
    const revision=marking.metadata.learnedRevisions??0;
    onValidation({type:"candidate-start",index,total,revision,support:marking.support.length,seed,round});
    const result=await solveA2Tiling({...solveOptions,nodeLimit:validationNodeLimit,animationDelayMs:0,randomSeed:seed,marking,onEvent:()=>{}});
    const entry={marking,result,revision,support:marking.support.length,seed,round};validation.push(entry);
    onValidation({type:"candidate-finish",index,total,revision,support:marking.support.length,result:result.result,nodes:result.stats.nodes,tiles:result.placements.length,seed,round});
    return entry;
  };
  for(let index=0;index<candidates.length;index++){
    if(solveOptions.stopToken?.stop)break;
    await evaluate(candidates[index],index,candidates.length,seeds[0],1);
  }
  let pool=candidates;
  if(seeds.length>1&&!solveOptions.stopToken?.stop){
    const firstRound=validation.filter(entry=>entry.seed===seeds[0]&&entry.result.result==="yes");
    const learned=firstRound.filter(entry=>entry.revision>0).sort((left,right)=>left.result.stats.nodes-right.result.stats.nodes||left.support-right.support).slice(0,confirmationCandidates).map(entry=>entry.marking);
    pool=[...new Set([candidates[0],...learned])];
    for(let round=1;round<seeds.length;round++)for(let index=0;index<pool.length;index++){
      if(solveOptions.stopToken?.stop)break;
      await evaluate(pool[index],index,pool.length,seeds[round],round+1);
    }
  }
  const scored=pool.map(marking=>{
    const results=validation.filter(entry=>entry.marking===marking),revision=marking.metadata.learnedRevisions??0;
    return{marking,revision,support:marking.support.length,results,totalNodes:results.reduce((sum,entry)=>sum+entry.result.stats.nodes,0),successful:results.length===seeds.length&&results.every(entry=>entry.result.result==="yes")};
  });
  const selected=scored.filter(entry=>entry.successful).sort((left,right)=>left.totalNodes-right.totalNodes||left.support-right.support||left.revision-right.revision)[0]??null;
  return{marking:selected?.marking??candidates[0],selected,candidates,validation,seeds};
}

return {A2_TILE_LOOPS,tileOrientations,a2Add,makeHexBoundary,solveA2Tiling,NoA2Marking,FixedA2Marking,SparseA2Marking,polygonBoundaryEdges};
})();
// ---------- Embedded hat-rank3-marking.js ----------
const H = (() => {
const {FixedA2Marking,SparseA2Marking}=E;

// Rank-3 signs on the existing Hat rank-1 Kagome pattern, 2026-10-30.
// There are eight core Kagome points, two nonzero directions per point:
// 16 independent signs. Complete enumeration gives eight full assignments
// matching the 7,921-tile patch. All give the same 228 excluded Hat pairs;
// independent unmarked integer-capacity certificates prove those impossible.
// The canonical interior values also follow the periodic Kagome sign rule.
// A sparse core retains ten negative entries and leaves six line entries *.
// Its 115 exclusions also have independently replayed unmarked certificates.
// It reached 100 Hats in 158 nodes versus 1546 for the full rule in seed 10.
// research/hat-kagome-phase/verify.py certifies the common field and the
// full marking at extents 0–3 for complete Hat-only point tilings.
const HAT_RANK3_ID='hat-kagome-rank3';
const HAT_RANK3_MAX_EXTENT=9;
const HAT_RANK3_CERTIFIED_EXTENT=3;
const HAT_RANK3_ZERO_POINTS=Object.freeze([
 [1,0,-1],[3,0,-3],[3,2,-5],[1,4,-5],[-1,6,-5],[-1,4,-3],[-1,2,-1],
 [0,1,-1],[0,2,-2],[0,4,-4],[0,5,-5],[1,2,-3],[1,3,-4],[2,1,-3],[2,3,-5],[3,1,-4]
].map(Object.freeze));
const HAT_RANK3_CORE_POINTS=Object.freeze([
 [-1,5,-4],[0,0,0],[0,3,-3],[0,6,-6],[1,1,-2],[2,2,-4],[3,3,-6],[4,1,-5]
].map(Object.freeze));
// These are exactly the four Hat rank-1 segment domains, including their
// complete lattice sampling. Extent adds primitive Kagome steps at both ends.
const HAT_RANK3_SEGMENTS=Object.freeze([
 [[0,0,0],[3,3,-6]],[[1,1,-2],[-1,5,-4]],[[4,1,-5],[0,3,-3]],[[0,6,-6],[-1,5,-4]]
].map(pair=>Object.freeze(pair.map(Object.freeze))));
function hatKagomeValues([x,y,z]){
 if(x+y+z!==0||(x-y)%3!==0)return null;
 const i=(-2*x-y)/3,j=(-x-2*y)/3;
 if(!(i&1)&&!(j&1))return [1,0,-1];
 if((i&1)&&(j&1))return [0,-1,1];
 if((i&1)&&!(j&1))return [-1,1,0];
 return null;
}
const HAT_RANK3_POINTS=Object.freeze([
 ...HAT_RANK3_CORE_POINTS.map(point=>Object.freeze({point,values:Object.freeze(hatKagomeValues(point))})),
 ...HAT_RANK3_ZERO_POINTS.map(point=>Object.freeze({point,values:Object.freeze([0,0,0])}))
]);
const HAT_RANK3_SPARSE_POINTS=Object.freeze([
 [[-1,5,-4],[0,-1,-1]],[[0,0,0],[-1,0,-1]],[[0,3,-3],[-1,-1,0]],
 [[0,6,-6],['*',0,'*']],[[1,1,-2],[0,-1,-1]],[[2,2,-4],[-1,0,-1]],
 [[3,3,-6],[0,'*','*']],[[4,1,-5],['*','*',0]]
].map(([point,values])=>Object.freeze({point:Object.freeze(point),values:Object.freeze(values)})));
function normalizeHatRank3Extent(value){
 const n=Number.parseInt(value,10);
 return Number.isFinite(n)?Math.max(0,Math.min(HAT_RANK3_MAX_EXTENT,n)):0;
}
const gcd=(a,b)=>b?gcd(b,a%b):Math.abs(a);
function alternatingSupport(tiles, extent) {
  const core = new FixedA2Marking(0, {tiles, rank: 1});
  const entries = new Map();
  function assign(tile, point, component, value) {
    entries.set(`${tile}:${point}|${component}`, {tile, point, component, value});
  }
  for (const {tile, point} of core.support) {
    const values = hatKagomeValues(point) ?? [0, 0, 0];
    values.forEach((value, component) => assign(tile, point, component, value));
  }
  if (extent > 0) {
    const orientation = {symmetry: {sign: 1, permutation: [0, 1, 2]}};
    for (const tile of new Set(tiles)) {
      const lines = core.segments({tile, orientation, translation: [0, 0, 0]});
      for (const {fromPoint, toPoint} of lines) {
        const delta = toPoint.map((v, i) => v - fromPoint[i]);
        const steps = delta.reduce(gcd);
        const step = delta.map(v => v / steps);
        const component = step.findIndex(v => Math.abs(v) === 2);
        for (let k = 1; k <= extent; k++) {
          const before = fromPoint.map((v, i) => v - k * step[i]);
          const after = toPoint.map((v, i) => v + k * step[i]);
          for (const point of [before, after]) {
            // Other directions remain unassigned unless their own stripes reach this point.
            assign(tile, point, component, hatKagomeValues(point)[component]);
          }
        }
      }
    }
  }
  return [...entries.values()];
}

function hatRank3Support({extent=0,pattern='sparse'}={}){
 const sparse=pattern==='sparse'||pattern==='sparse-reverse';
 const reverse=pattern==='alternate'||pattern==='reverse'||pattern==='sparse-reverse';
 if(!sparse){
  const support=alternatingSupport(['hat'],normalizeHatRank3Extent(extent));
  return reverse?support.map(entry=>({...entry,value:entry.value===0?0:-entry.value})):support;
 }
 const points=new Map(HAT_RANK3_ZERO_POINTS.map(point=>[point.join(','),{point,values:[0,0,0]}]));
 for(const entry of HAT_RANK3_SPARSE_POINTS)points.set(entry.point.join(','),entry);
 return [...points.values()].flatMap(({point,values})=>values.flatMap((value,component)=>value==='*'?[]:[{tile:'hat',point:[...point],component,value:reverse&&value!==0?-value:value}]));
}
function createHatRank3Marking(options={}){
 const sparse=(options.pattern??'sparse').startsWith('sparse');
 const extent=sparse?0:normalizeHatRank3Extent(options.extent??0);
 return new SparseA2Marking(hatRank3Support({...options,extent}),{
  label:`Hat rank 3 Kagome · ${sparse?'sparse core':`extent ${extent}`}`,valueAction:'signed-permutation',version:'hat-kagome-rank3-v3',
  coreSignMask:sparse?0:42598,activeLineMask:sparse?3903:65535,coreAssignments:sparse?66:72,coreCertified:true,exteriorCertified:!sparse && extent>0 && extent<=HAT_RANK3_CERTIFIED_EXTENT
 });
}

// Both prototiles sample the same Kagome field in first-vertex coordinates.
// The fixed scalar stripes supply the four geometric line domains per tile.
// An exterior stripe samples only its own directional component of the field.
const MIXED_RANK3_ID = 'mixed-hat-turtle-rank3';
function createAlternatingMarking(tiles = ['turtle'], extent = 0, {pointFilter = null} = {}) {
  extent = normalizeHatRank3Extent(extent);
  const tileSet = [...new Set(tiles)];
  let support;
  if (tileSet.length === 1 && tileSet[0] === 'turtle') {
    // On all four Turtle stripes the opposite phase matches the constant sign at
    // both original endpoints. Only the signs at odd steps along the stripe flip.
    const constant = new FixedA2Marking(extent, {tiles: tileSet, rank: 3});
    support = constant.support.map(entry => ({
      ...entry, value: entry.value === 0 ? 0 : -hatKagomeValues(entry.point)[entry.component]
    }));
  } else {
    support = alternatingSupport(tileSet, extent);
  }
  if (pointFilter) support = support.filter(entry => pointFilter(entry.point));
  return new SparseA2Marking(support, {label: 'Alternating rank 3 · extent ' + extent});
}

return {createHatRank3Marking,createAlternatingMarking};
})();
// ---------- Embedded failure-rank3-data.js ----------
const data = (() => {

// Generated by research/failure-marking/encode.py. Each row is [tile, x, y, axis, value, extent].
const failureSupport = {
  hat: [
    ["hat",-5,9,2,-1,4],
    ["hat",-4,3,1,-1,3],
    ["hat",-3,1,2,-1,3],
    ["hat",-3,2,1,-1,2],
    ["hat",-3,6,2,-1,2],
    ["hat",-2,3,0,-1,1],
    ["hat",-2,4,1,1,1],
    ["hat",-2,6,0,-1,1],
    ["hat",-2,6,2,-1,1],
    ["hat",-1,0,1,1,1],
    ["hat",-1,0,2,1,1],
    ["hat",-1,2,2,1,0],
    ["hat",-1,5,1,1,0],
    ["hat",-1,6,0,-1,0],
    ["hat",-1,8,2,1,2],
    ["hat",0,0,0,-1,0],
    ["hat",0,0,1,-1,0],
    ["hat",0,2,1,-1,0],
    ["hat",0,6,0,1,0],
    ["hat",1,0,0,-1,0],
    ["hat",1,3,0,1,0],
    ["hat",1,4,1,1,0],
    ["hat",1,5,0,-1,1],
    ["hat",1,7,1,1,2],
    ["hat",2,-1,2,-1,1],
    ["hat",2,0,0,-1,1],
    ["hat",2,4,1,1,1],
    ["hat",4,-1,0,1,1],
    ["hat",4,0,1,-1,1],
    ["hat",4,2,2,-1,1],
    ["hat",4,4,2,1,2],
    ["hat",5,0,0,1,1],
    ["hat",5,3,1,-1,2],
  ],
  mixed: [
    ["hat",-5,5,1,-1,4],
    ["hat",-5,8,0,-1,4],
    ["hat",-4,3,0,1,3],
    ["hat",-4,7,0,-1,3],
    ["hat",-4,9,0,-1,3],
    ["hat",-4,9,1,1,3],
    ["hat",-3,2,0,-1,2],
    ["hat",-3,8,1,-1,2],
    ["hat",-3,11,0,-1,5],
    ["hat",-2,1,0,-1,2],
    ["hat",-2,3,1,1,1],
    ["hat",-1,4,0,-1,0],
    ["hat",-1,4,2,-1,0],
    ["hat",0,-1,0,-1,1],
    ["hat",0,3,2,1,0],
    ["hat",0,7,2,1,1],
    ["hat",0,8,1,-1,2],
    ["hat",1,0,1,-1,0],
    ["hat",1,2,1,-1,0],
    ["hat",2,0,0,-1,1],
    ["hat",2,7,2,-1,3],
    ["hat",3,-8,0,-1,8],
    ["hat",3,3,2,1,0],
    ["hat",3,4,0,-1,1],
    ["hat",3,5,0,-1,2],
    ["hat",4,-3,0,-1,3],
    ["hat",4,3,1,-1,1],
    ["hat",5,-2,0,-1,2],
    ["hat",5,-1,1,-1,2],
    ["hat",7,1,0,1,3],
    ["hat",10,-3,2,-1,6],
    ["turtle",-9,5,0,-1,4],
    ["turtle",-7,0,0,-1,3],
    ["turtle",-7,1,0,1,2],
    ["turtle",-7,4,1,1,2],
    ["turtle",-6,7,1,1,2],
    ["turtle",-5,0,1,-1,1],
    ["turtle",-5,1,2,1,0],
    ["turtle",-5,4,1,-1,0],
    ["turtle",-5,5,0,-1,1],
    ["turtle",-5,8,2,-1,3],
    ["turtle",-4,1,0,1,0],
    ["turtle",-4,5,1,1,0],
    ["turtle",-3,-4,0,-1,3],
    ["turtle",-3,-4,1,-1,3],
    ["turtle",-3,-1,2,1,1],
    ["turtle",-3,4,0,-1,0],
    ["turtle",-3,5,2,-1,1],
    ["turtle",-3,7,2,-1,3],
    ["turtle",-2,0,2,-1,0],
    ["turtle",-1,-2,1,-1,0],
    ["turtle",0,-6,1,-1,3],
    ["turtle",0,0,2,1,0],
    ["turtle",0,2,0,1,1],
    ["turtle",1,8,1,-1,8],
    ["turtle",2,-9,0,-1,6],
    ["turtle",2,-2,0,1,1],
    ["turtle",2,0,0,1,2],
    ["turtle",3,-2,0,1,2],
    ["turtle",5,0,1,-1,5],
    ["turtle",6,-7,2,-1,5],
  ],
};

return {failureSupport};
})();
// ---------- Embedded failure-rank3-marking.js ----------
const F = (() => {
const {SparseA2Marking}=E; const {failureSupport}=data;


function failureExtent(setId) {
  if (!Object.hasOwn(failureSupport, setId)) throw new RangeError('Unsupported tile set');
  return Math.max(...failureSupport[setId].map(row => row[5]));
}

function createFailureMarking(setId, extent = failureExtent(setId)) {
  if (!Object.hasOwn(failureSupport, setId) || !Number.isInteger(extent) || extent < 0 || extent > 9) {
    throw new RangeError('Unsupported tile set or marking extent');
  }
  const support = failureSupport[setId].filter(row => row[5] <= extent)
    .map(([tile,x,y,component,value]) => ({tile, point:[x,y,-x-y], component, value}));
  // Missing components are wildcards. The standard signed permutation action
  // and equality on overlap are both implemented by SparseA2Marking.
  return new SparseA2Marking(support, {label:'Rank 3 from failures'});
}

return {failureExtent,createFailureMarking};
})();
  const {A2_TILE_LOOPS,tileOrientations,a2Add,makeHexBoundary,solveA2Tiling,NoA2Marking,FixedA2Marking}=E;
  const sets={turtle:['turtle'],hat:['hat'],mixed:['turtle','hat']};
  const mk=(tag,props={})=>Object.assign(document.createElement(tag),props);
  function label(text,el){const l=mk('label');Object.assign(l.style,{display:'inline-flex',alignItems:'center',gap:'5px',font:'13px system-ui'});l.append(document.createTextNode(text),el);return l;}
  function radios(name,options,initial){const el=mk('div');Object.assign(el.style,{display:'flex',flexDirection:'column',gap:'4px'});el.setAttribute('role','radiogroup');for(const [value,text] of options){const input=mk('input',{type:'radio',name,value,checked:value===initial});const l=label(text,input);l.replaceChildren(input,document.createTextNode(text));el.append(l);}Object.defineProperty(el,'value',{get(){return el.querySelector('input:checked')?.value},set(v){for(const x of el.querySelectorAll('input'))x.checked=x.value===v;}});return el;}
  const set=radios('gcts-search',[['hat','Hats'],['turtle','Turtles'],['mixed','Both']],'turtle');
  const manual=radios('gcts-manual',[['hat','Hat'],['turtle','Turtle']],'hat');
  const add=mk('button',{textContent:'Add'}),remove=mk('button',{textContent:'Delete selected'}),edit=mk('button',{textContent:'Edit seed'}),flip=mk('button',{textContent:'Flip'});
  const rule=radios('gcts-rule',[['none','None'],['rank1','Rank 1'],['constant','Rank 3 constant'],['alternating','Rank 3 wave']],'none');
  const start=mk('button',{textContent:'Start tiling'}),reset=mk('button',{textContent:'Reset'}),fit=mk('button',{textContent:'Fit'});
  const marks=mk('input',{type:'checkbox',checked:true}),grid=mk('input',{type:'checkbox',checked:true});
  const extent=mk('input',{type:'number',min:'0',max:'9',step:'1',value:'1'});extent.style.width='45px';
  const speed=mk('input',{type:'range',min:'1',max:'60',value:'20'});speed.style.width='90px';
  start.style.fontWeight='600';
  function group(title,...children){const g=mk('div');Object.assign(g.style,{display:'flex',flexDirection:'column',gap:'7px'});const h=mk('div',{textContent:title});h.style.fontWeight='600';g.append(h,...children);return g;}
  function line(...children){const l=mk('div');Object.assign(l.style,{display:'flex',alignItems:'center',flexWrap:'wrap',gap:'6px'});l.append(...children);return l;}
  const notice=mk('div');Object.assign(notice.style,{fontSize:'12px',color:'#a13a32',overflowWrap:'anywhere'});notice.setAttribute('role','status');
  const hint=mk('div',{textContent:'Click to rotate · right-click to flip · drag to move'});Object.assign(hint.style,{position:'absolute',bottom:'10px',left:'10px',right:'10px',textAlign:'center',font:'12px system-ui',color:'#66717f',pointerEvents:'none',background:'rgba(255,255,255,.88)',padding:'4px'});area.append(hint);
  const seedControls=group('Initial tiles',add,manual,remove,flip);
  ui.append(seedControls,edit,group('Tile with',set,start,reset,fit),group('Matching rules',rule,label('Extent',extent),label('Show markings',marks)),group('View',label('Grid',grid),label('Speed',speed)),notice);
  let W=1,HH=1,scale=24,cx=0,cy=0,dpr=1,patch=[],ghost=null,marking=null,job=null,running=false,finished=false,nodes=0,backtracks=0,message='',autoFit=true, manualPatch=[], selected=-1, editing=true;
  const project=([x,y,z])=>[(z-x)/Math.sqrt(2),(2*y-x-z)/Math.sqrt(6)];
  const screen=p=>{const [x,y]=project(p);return [W/2+(x-cx)*scale,HH/2+(y-cy)*scale];};
  const loop=p=>p.loop||p.orientation.loop.map(v=>a2Add(v,p.translation));
  const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
  const orientations=Object.fromEntries(['hat','turtle'].map(t=>[t,tileOrientations(t,A2_TILE_LOOPS[t])]));
  function seed(tile=sets[set.value][0],translation=[0,0,0]){return {tile,orientation:orientations[tile][0],translation,generation:0};}
  function snap(x,y){const q=-x/Math.sqrt(2)-y/Math.sqrt(6),r=2*y/Math.sqrt(6),z=-q-r;const f=[q,r,z],a=f.map(Math.round);let k=0;for(let i=1;i<3;i++)if(Math.abs(a[i]-f[i])>Math.abs(a[k]-f[k]))k=i;a[k]-=a.reduce((u,v)=>u+v,0);return a;}
  function world(x,y){return [cx+(x-W/2)/scale,cy+(y-HH/2)/scale];}
  function validateSeed(checkMarks=true){const sums=new Map(),ms=new Map();for(const p of manualPatch){for(const v of p.orientation.occupancy.values()){const k=a2Add(v.point,p.translation).join(',');const n=(sums.get(k)||0)+v.weight;if(n>12)return 'Seed tiles overlap';sums.set(k,n);}if(checkMarks&&marking?.entries){for(const [k,v] of marking.entries(p)){if(ms.has(k)&&ms.get(k)!==v)return 'Seed markings disagree';ms.set(k,v);}}}return '';}
  function refreshEdit(){patch=manualPatch.slice();ghost=null;options();marking=makeMarking();message=validateSeed();draw();button();}
  function transformTile(flipIt,pivot=null){if(!editing||selected<0)return;const p=manualPatch[selected],s=p.orientation.symmetry;const perm=flipIt?[s.permutation[2],s.permutation[1],s.permutation[0]]:[s.permutation[1],s.permutation[2],s.permutation[0]],sign=flipIt?s.sign:-s.sign;const o=orientations[p.tile].find(o=>o.symmetry.sign===sign&&o.symmetry.permutation.every((v,i)=>v===perm[i]));if(o){let translation=p.translation;if(pivot&&!flipIt){const [px,py]=world(...pivot),[tx,ty]=project(p.translation);const dx=tx-px,dy=ty-py;// determine actual 60° direction from the lattice rotation
      const v=[1,-1,0],w=[-v[1],-v[2],-v[0]],u2=project(v),w2=project(w),cos=(u2[0]*w2[0]+u2[1]*w2[1])/2,sin=(u2[0]*w2[1]-u2[1]*w2[0])/2;
      translation=snap(px+cos*dx-sin*dy,py+sin*dx+cos*dy);}
      manualPatch[selected]={...p,orientation:o,translation};refreshEdit();}}
  function hit(x,y){for(let i=manualPatch.length-1;i>=0;i--){path(manualPatch[i]);if(ctx.isPointInPath(x*dpr,y*dpr))return i;}return -1;}
  function toEdit(){cancel();editing=true;finished=false;nodes=backtracks=0;marking=makeMarking();refreshEdit();}

  const activeTiles=()=>[...new Set([...sets[set.value],...manualPatch.map(p=>p.tile)])];
  function options(){const constant=rule.querySelector('input[value="constant"]');constant.disabled=activeTiles().includes('hat');constant.parentElement.style.opacity=constant.disabled?'0.45':'1';constant.parentElement.title=constant.disabled?'Constant rank-3 marking is defined only for turtles':'';if(constant.disabled&&rule.value==='constant')rule.value='none';extent.disabled=marks.disabled=rule.value==='none';}
  function makeMarking(){const tiles=activeTiles(),n=Math.max(0,Math.min(9,Math.trunc(Number(extent.value)||0)));if(rule.value==='none')return new NoA2Marking();if(rule.value==='alternating')return tiles.length===1&&tiles[0]==='hat'?H.createHatRank3Marking({extent:n,pattern:'more'}):H.createAlternatingMarking(tiles,n);return new FixedA2Marking(n,{rank:rule.value==='rank1'?1:3,tiles});}
  function fitPatch(){if(!patch.length)return;let x0=Infinity,x1=-Infinity,y0=Infinity,y1=-Infinity;for(const p of patch)for(const v of loop(p)){const [x,y]=project(v);x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);}cx=(x0+x1)/2;cy=(y0+y1)/2;scale=Math.max(.25,Math.min(35,(W-45)/Math.max(1,x1-x0),(HH-65)/Math.max(1,y1-y0)));}
  function path(p){ctx.beginPath();loop(p).forEach((v,i)=>{const [x,y]=screen(v);i?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.closePath();}
  function draw(){ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,W,HH);ctx.fillStyle='#fff';ctx.fillRect(0,0,W,HH);
    if(grid.checked&&scale>4){const radius=Math.ceil((Math.hypot(W,HH)/2)/scale)+3;const q0=Math.round(-cx/Math.sqrt(2)-cy/Math.sqrt(6)),r0=Math.round(2*cy/Math.sqrt(6));ctx.strokeStyle='#e6e8eb';ctx.lineWidth=.65;ctx.beginPath();for(let q=q0-radius;q<=q0+radius;q++)for(let r=r0-radius;r<=r0+radius;r++){const p=[q,r,-q-r],a=screen(p);if(a[0]<-scale*2||a[0]>W+scale*2||a[1]<-scale*2||a[1]>HH+scale*2)continue;for(const v of [[1,-1,0],[1,0,-1],[0,1,-1]]){const b=screen(a2Add(p,v));ctx.moveTo(...a);ctx.lineTo(...b);}}ctx.stroke();}
    for(const [i,p] of patch.entries()){path(p);const reflected=parity(p.orientation.symmetry.permutation)<0;ctx.fillStyle=p.tile==='hat'?(reflected?'#f1b684':'#f5d79a'):(reflected?'#86afdc':'#b6d4ef');ctx.fill();ctx.strokeStyle=editing&&i===selected?'#175fba':'#344454';ctx.lineWidth=editing&&i===selected?2.5:1;ctx.stroke();}
    if(marks.checked&&marking&&rule.value!=='none'){
      const blue='#2563b7',green='#23945d',width=Math.min(1.5,scale*.055);
      ctx.lineCap='round';ctx.lineWidth=width;
      function stroke(a,b,va,vb=va){
        if(va===vb)ctx.strokeStyle=va<0?green:blue;
        else{const g=ctx.createLinearGradient(...a,...b);g.addColorStop(0,va<0?green:blue);g.addColorStop(1,vb<0?green:blue);ctx.strokeStyle=g;}
        ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();
      }
      for(const p of patch){
        if(typeof marking.segments==='function'){
          for(const m of marking.segments(p))stroke(screen(m.fromPoint),screen(m.toPoint),m.value);
        }else if(typeof marking.entries==='function'){
          const entries=marking.entries(p);
          // Interpolate only between adjacent assigned nonzero samples in the same directional component.
          // Missing and zero samples are not bridged, and the discrete search values are unchanged.
          for(const [key,value] of entries){
            if(!value)continue;
            const [coord,comp]=key.split('|'),v=coord.split(',').map(Number),dir=[0,1,2].map(i=>i===Number(comp)?-2:1);
            const next=v.map((x,i)=>x+dir[i]),prev=v.map((x,i)=>x-dir[i]);
            const nv=entries.get(next.join(',')+'|'+comp),pv=entries.get(prev.join(',')+'|'+comp);
            if(nv)stroke(screen(v),screen(next),value,nv);
            else stroke(screen(v),screen(v.map((x,i)=>x+dir[i]*.23)),value);
            if(!pv)stroke(screen(v.map((x,i)=>x-dir[i]*.23)),screen(v),value);
          }
        }
      }
      ctx.lineCap='butt';
    }
    // Draw the exterior boundary of the entire initial patch above all tiles.
    const boundary=new Map();for(const p of manualPatch)for(const e of E.polygonBoundaryEdges(loop(p))){const n=(boundary.get(e.key)||0)+e.direction;if(n)boundary.set(e.key,n);else boundary.delete(e.key);}
    ctx.beginPath();for(const k of boundary.keys()){const [a,b]=k.split('|').map(x=>screen(x.split(',').map(Number)));ctx.moveTo(...a);ctx.lineTo(...b);}ctx.strokeStyle='#172e4a';ctx.lineWidth=Math.min(3,Math.max(.8,scale*.13));ctx.stroke();
    if(ghost){path(ghost);ctx.fillStyle='rgba(230,90,70,.25)';ctx.fill();ctx.strokeStyle='#d34838';ctx.lineWidth=2;ctx.stroke();}
    const hats=patch.filter(p=>p.tile==='hat').length,turtles=patch.length-hats;status.textContent=`${patch.length} tiles · ${hats} hats · ${turtles} turtles`;notice.textContent=/^(Seed |Add a seed)/.test(message)||finished&&message!=='search ended'?message:'';
  }
  function resize(){const r=area.getBoundingClientRect();W=Math.max(1,r.width);HH=Math.max(1,r.height);dpr=Math.min(2,window.devicePixelRatio||1);canvas.width=Math.round(W*dpr);canvas.height=Math.round(HH*dpr);if(autoFit)fitPatch();draw();}
  function button(){seedControls.style.display=editing?'flex':'none';edit.style.display=editing?'none':'block';hint.style.display=editing?'block':'none';add.disabled=remove.disabled=flip.disabled=!editing;remove.disabled=flip.disabled=!editing||selected<0;edit.disabled=editing;start.textContent=running?'Pause':finished?'Start again':job?'Resume':'Start tiling';start.style.background=running?'#d9534f':'#4a90d9';start.style.color='#fff';}
  function cancel(){if(job){job.token.stop=true;job.wake?.();job=null;}running=false;}
  function clear(){cancel();finished=false;editing=true;nodes=backtracks=0;ghost=null;extent.disabled=rule.value==='none';marks.disabled=rule.value==='none';manualPatch=[seed()];options();marking=makeMarking();selected=0;patch=manualPatch.slice();autoFit=false;cx=cy=0;scale=24;refreshEdit();}
  const sleep=ms=>new Promise(r=>setTimeout(r,ms));
  async function begin(){if(finished)toEdit();if(!job){if(!manualPatch.length){message='Add a seed tile first';draw();return;}const invalid=validateSeed();if(invalid){message=invalid;draw();return;}editing=false;autoFit=true;}running=true;button();if(job){job.wake?.();return;}const current={token:{stop:false},wake:null};job=current;const initial=manualPatch.slice(),allowed=sets[set.value],tiles=[...new Set([...allowed,...initial.map(p=>p.tile)])];
    marking=makeMarking();
    const wait=async()=>{while(!running&&!current.token.stop)await new Promise(r=>current.wake=r);current.wake=null;if(!current.token.stop)await sleep(1000/Number(speed.value));while(!running&&!current.token.stop)await new Promise(r=>current.wake=r);current.wake=null;};
    try{await solveA2Tiling({boundary:makeHexBoundary(220),initialPlacements:initial,tiles,allowReflections:true,placementFilter:p=>allowed.includes(p.tile)&&(set.value!=='mixed'||parity(p.orientation.symmetry.permutation)>0),fixedInitialPlacements:true,completePointGrowth:true,maximize:true,targetPlacements:1000,nodeLimit:1000000,marking,branchPolicy:'oldest-frontier',requireEdgeSharing:true,randomSeed:1,stopToken:current.token,waitForSearchDemand:wait,onEvent:e=>{if(job!==current)return;nodes=e.nodes;backtracks=e.backtracks;if(['placement','backtrack','fail'].includes(e.type)){patch=e.placements;ghost=e.type==='backtrack'?e.removed:null;message=e.type==='backtrack'?'backtracking':e.type==='fail'?'dead frontier':e.forced?'forced move':'growing';if(autoFit)fitPatch();draw();}}});if(job===current){finished=true;message='search ended';}}
    catch(error){if(job===current){finished=true;message=error.message;}}
    finally{if(job===current){job=null;running=false;button();draw();}}
  }
  start.onclick=()=>{if(running){running=false;button();}else begin();};reset.onclick=clear;edit.onclick=toEdit;flip.onclick=()=>transformTile(true);remove.onclick=()=>{if(editing&&selected>=0){manualPatch.splice(selected,1);selected=-1;refreshEdit();}};add.onclick=()=>{if(!editing)return;const t=manual.value;const pos=snap(cx,cy);let p=seed(t,pos);const occupied=new Set(manualPatch.map(p=>p.translation.join(',')));const sums=new Map();for(const q of manualPatch)for(const v of q.orientation.occupancy.values()){const k=a2Add(v.point,q.translation).join(',');sums.set(k,(sums.get(k)||0)+v.weight);}while(occupied.has(p.translation.join(','))||[...p.orientation.occupancy.values()].some(v=>(sums.get(a2Add(v.point,p.translation).join(','))||0)+v.weight>12))p=seed(t,a2Add(p.translation,[1,-1,0]));manualPatch.push(p);selected=manualPatch.length-1;refreshEdit();};fit.onclick=()=>{autoFit=true;fitPatch();draw();};set.onchange=()=>{options();toEdit();};rule.onchange=extent.onchange=()=>{extent.disabled=marks.disabled=rule.value==='none';toEdit();};marks.onchange=grid.onchange=draw;
  let drag=null;
  function local(e){const r=canvas.getBoundingClientRect();return [e.clientX-r.left,e.clientY-r.top];}
  canvas.addEventListener('contextmenu',e=>{e.preventDefault();if(!editing)return;selected=hit(...local(e));if(selected>=0)transformTile(true);});
  canvas.addEventListener('pointerdown',e=>{if(e.button!==0)return;autoFit=false;const [x,y]=local(e);const i=editing?hit(x,y):-1;if(editing)selected=i;drag={x,y,cx,cy,i,moved:false,translation:i>=0?[...manualPatch[i].translation]:null};canvas.setPointerCapture(e.pointerId);canvas.style.cursor='grabbing';draw();button();});
  canvas.addEventListener('pointermove',e=>{if(!drag)return;const [x,y]=local(e),dx=x-drag.x,dy=y-drag.y;if(Math.hypot(dx,dy)>4)drag.moved=true;if(!drag.moved)return;if(drag.i>=0&&editing){const delta=snap(dx/scale,dy/scale);manualPatch[drag.i]={...manualPatch[drag.i],translation:a2Add(drag.translation,delta)};refreshEdit();}else{cx=drag.cx-dx/scale;cy=drag.cy-dy/scale;draw();}});
  canvas.addEventListener('pointerup',()=>{if(drag&&!drag.moved&&drag.i>=0&&editing)transformTile(false,[drag.x,drag.y]);drag=null;canvas.style.cursor='grab';});
  for(const type of ['pointercancel','lostpointercapture'])canvas.addEventListener(type,()=>{drag=null;canvas.style.cursor='grab';});
  canvas.addEventListener('wheel',e=>{e.preventDefault();autoFit=false;const r=canvas.getBoundingClientRect(),x=e.clientX-r.left-W/2,y=e.clientY-r.top-HH/2,old=scale;scale=Math.max(.25,Math.min(150,scale*Math.exp(-e.deltaY*.0015)));cx+=x/old-x/scale;cy+=y/old-y/scale;draw();},{passive:false});
  options();clear();new ResizeObserver(resize).observe(area);resize();fitPatch();scale=Math.min(scale,24);draw();
  window.addEventListener('pagehide',cancel,{once:true});
})();