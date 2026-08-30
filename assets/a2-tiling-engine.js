import { GeometricFailureMemo } from "./geometric-failure-memo.js";

export const A2_TILE_LOOPS = Object.freeze({
  turtle: [[3,-2,-1],[2,0,-2],[0,1,-1],[0,2,-2],[-1,3,-2],[-2,2,0],[-1,0,1],[-2,0,2],[-2,-1,3],[0,-2,2],[1,-4,3],[2,-4,2],[3,-5,2],[4,-4,0]],
  hat: [[0,0,0],[1,0,-1],[1,1,-2],[3,0,-3],[4,1,-5],[3,2,-5],[3,3,-6],[1,4,-5],[0,6,-6],[-1,6,-5],[-1,5,-4],[-1,4,-3],[0,3,-3],[-1,2,-1]],
  hexagon: [[2,0,-2],[2,-2,0],[0,-2,2],[-2,0,2],[-2,2,0],[0,2,-2]]
});

const PERMUTATIONS = [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]];
export const A2_SYMMETRIES = Object.freeze([1,-1].flatMap(sign =>
  PERMUTATIONS.map(permutation => ({ sign, permutation }))
));

export const a2Key = point => point.join(",");
export const a2Add = (a,b) => [a[0]+b[0],a[1]+b[1],a[2]+b[2]];
export const a2Sub = (a,b) => [a[0]-b[0],a[1]-b[1],a[2]-b[2]];
export const a2Transform = (point, symmetry) => symmetry.permutation.map(index => symmetry.sign * point[index]);
export const a2InverseTransform = (point, symmetry) => {
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

// Shared by the intrinsic A2 solver and the three-dimensional layered tiles.
// Return fresh records so callers can rescale weights without mutating the
// solver's occupancy representation.
export function a2PolygonOccupancy(loop) {
  return new Map([...polygonOccupancy(loop)].map(([key, entry]) => [key, {
    point: entry.point.slice(),
    weight: entry.weight
  }]));
}

const cellVertices = (q,r,kind) => kind==="u"
  ? [[q,r],[q+1,r],[q,r+1]]
  : [[q+1,r+1],[q,r+1],[q+1,r]];
const cellKey = (q,r,kind) => `${q},${r},${kind}`;

export function polygonCells(loop) {
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

export function makeHexBoundary(radius) {
  const r=Math.max(2,radius|0);
  return [[r,0,-r],[r,-r,0],[0,-r,r],[-r,0,r],[-r,r,0],[0,r,-r]];
}

function orientationSignature(loop){return loop.map(a2Key).sort().join("|");}
export function tileOrientations(tile, loop) {
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

export class OnlineA2Marking {
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

export class NoA2Marking {
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

export class SparseA2Marking extends NoA2Marking{
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
export class FixedTurtleMarking extends NoA2Marking{
  constructor(extension=1){
    super();this.prunes=0;this.support=[];this.contacts=new Map();this.entryCache=new Map();
    const origin=A2_TILE_LOOPS.turtle[0];
    for(const segment of TURTLE_MARK_SEGMENTS){const a=A2_TILE_LOOPS.turtle[segment.from],b=A2_TILE_LOOPS.turtle[segment.to],component=primitiveComponent(a,b);for(const point of extendedSegmentPoints(a,b,extension))this.support.push({tile:"turtle",point:a2Sub(point,origin),component,value:segment.value});}
  }
  entries(placement){
    const cacheKey=placement.id??`${placement.tile}:${placement.orientation.index}:${a2Key(placement.translation)}`;
    if(this.entryCache.has(cacheKey))return this.entryCache.get(cacheKey);
    const result=new Map(),symmetry=placement.orientation.symmetry,coefficient=permutationParity(symmetry.permutation);
    for(const mark of this.support){if(mark.tile!==placement.tile)continue;const global=a2Add(a2Transform(mark.point,symmetry),placement.translation),component=symmetry.permutation.indexOf(mark.component);result.set(`${a2Key(global)}|${component}`,mark.value*coefficient);}
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
  stats(){return{revision:0,supportSites:this.support.length,failures:0,prunes:this.prunes,unencodable:0,support:this.support.map(entry=>({...entry,point:[...entry.point],color:entry.value>0?1:2}))};}
}

export const a2ClusterProposalToken=(prior,candidate)=>`${prior.tile}:${prior.orientation.index}>${candidate.tile}:${candidate.orientation.index}@${a2Key(a2Sub(candidate.translation,prior.translation))}`;

export function learnA2ClusterProposals(placements,{maxDistance=12,window=16}={}){
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

export async function solveA2Tiling({boundary,seed=null,startPoints=[],tiles=["hat"],customTiles={},maximize=false,targetPlacements=500,preferredPlacements=[],clusterProposals=[],placementFilter=null,pointTarget=null,nodeLimit=250000,animationDelayMs=0,learningWarmupDepth=0,maxMarkingRevisions=Infinity,markingStagnationNodes=1200,randomSeed=1,marking=null,onEvent=()=>{},stopToken={stop:false}}){
  const desired=polygonOccupancy(boundary),seedOccupancy=seed?polygonOccupancy(seed.loop):new Map();
  const tileDefs={};for(const tile of tiles)tileDefs[tile]=customTiles[tile]??A2_TILE_LOOPS[tile];
  const orientedTiles=Object.entries(tileDefs).flatMap(([tile,loop])=>tileOrientations(tile,loop));
  const memoRadius=Math.max(1,...orientedTiles.map(orientation=>{const points=[...orientation.occupancy.values()].map(entry=>entry.point);let diameter=1;for(const left of points)for(const right of points)diameter=Math.max(diameter,...a2Sub(left,right).map(Math.abs));return diameter;}));
  const preferredRanks=new Map(preferredPlacements.map((id,index)=>[id,index]));
  const clusterWeights=new Map(clusterProposals);
  const candidateCache=new Map();
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
  const startPointMap=new Map(startPoints.map(point=>[a2Key(point),point]));
  const learner=marking??new OnlineA2Marking(),markingSeed=seed?.markingPlacement??null,sums=new Map([...seedOccupancy].map(([key,entry])=>[key,entry.weight])),pointDepth=new Map([...seedOccupancy.keys()].map(key=>[key,0])),chosen=[],usedPlacements=new Set(),exhaustedBranches=new Set();for(const key of startPointMap.keys()){if(!sums.has(key))sums.set(key,0);pointDepth.set(key,0);}let nodes=0,backtracks=0,exactMemoPrunes=0,best=[],bestFilled=0,lastImprovementNode=0;
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
  learner.reset?.(markingSeed?[markingSeed]:[]);
  let rngState=(randomSeed|0)||1;const random=()=>((rngState=Math.imul(rngState,1664525)+1013904223|0)>>>0)/4294967296;
  const filledWeight=()=>[...desired].reduce((sum,[key,entry])=>sum+Math.min(entry.weight,sums.get(key)||0),0),totalWeight=[...desired.values()].reduce((sum,e)=>sum+e.weight,0);
  const branchKey=(candidate,context=chosen)=>`${context.map(placement=>placement.id).sort().join(";")}=>${candidate.id}`;
  const clusterProposalScore=candidate=>{
    let score=0;
    for(const prior of chosen)score+=clusterWeights.get(a2ClusterProposalToken(prior,candidate))??0;
    return score;
  };
  const emit=(type,extra={})=>onEvent({type,nodes,backtracks,placed:chosen.length,targetPlacements:maximize?targetPlacements:null,totalCells:totalWeight,coveredCells:filledWeight(),marking:learner.stats(),searchMemo:{failures:exhaustedBranches.size,prunes:exactMemoPrunes},placements:chosen.slice(),...extra});
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
    if(stopToken.stop)return "unknown";
    if(nodes>=nodeLimit)return "unknown";
    if(maximize&&learner.revision>0&&nodes-lastImprovementNode>=markingStagnationNodes)return "stagnant";
    if(maximize?chosen.length>=targetPlacements:[...desired].every(([key,entry])=>Math.abs((sums.get(key)||0)-entry.weight)<1e-7))return true;
    let choice=null,options=null,choiceInfo={forced:false,branchCount:0,frontierValue:0};
    const legalAt=(point,limit=Infinity,ignoreMarking=false)=>{
      const legal=[];
      for(const p of candidatesForPoint(point)){
        if(usedPlacements.has(p.id))continue;
        if(exhaustedBranches.has(branchKey(p))){exactMemoPrunes++;continue;}
        let newPoints=0,valid=true;
        const materialized=!!p.occupancy,source=materialized?p.occupancy.values():p.orientation.occupancy.values();
        for(const local of source){
          const e=materialized?local:{point:a2Add(local.point,p.translation),weight:local.weight},key=a2Key(e.point);
          const current=sums.get(key)||0,target=targetAt(e.point);
          if(current+e.weight>target+1e-7){valid=false;break;}
          if(current<1e-7)newPoints++;
        }
        if(maximize&&placementFilter&&!placementFilter(materializePlacement(p)))valid=false;
        if(!valid||(maximize&&!newPoints)||(!maximize&&(chosen.some(other=>polygonsOverlap(p.loop,other.loop))||(seed&&polygonsOverlap(p.loop,seed.loop))))||(!ignoreMarking&&!learner.compatible(p,markingSeed?[markingSeed,...chosen]:chosen)))continue;
        legal.push(p);if(legal.length>=limit)break;
      }
      return legal;
    };
    if(maximize){
      // Close the geometric shell nearest the initial tile before touching a
      // farther shell. Forcedness is only a tie-breaker inside that nearest
      // shell; it must never jump the search across a nearer branching point.
      const frontier=[...sums].filter(([point,value])=>value<targetAt(point.split(",").map(Number))-1e-7).map(([point,value])=>{
        const coordinates=point.split(",").map(Number);
        return{point,value,distance:distanceFromInitial(point),introduced:pointDepth.get(point)??Infinity,norm:coordinates.reduce((sum,v)=>sum+Math.abs(v),0)};
      }).sort((a,b)=>a.distance-b.distance||b.value-a.value||a.introduced-b.introduced||a.norm-b.norm||lexicalCompare(a.point,b.point));
      if(!frontier.length)return true;
      const nearestDistance=frontier[0].distance,nearest=frontier.filter(entry=>entry.distance===nearestDistance);
      let selected=null;
      for(const entry of nearest){
        const legal=legalAt(entry.point);
        if(!legal.length){if(!legalAt(entry.point,1,true).length)learner.rememberFrontierFailure?.(frontierPattern(entry.point));noteFailedPath(trackers,entry.point);emit("fail",{choice:entry.point,frontierValue:entry.value});return false;}
        if(!selected||legal.length<selected.legal.length)selected={...entry,legal};
      }
      if(chosen.length>best.length){best=chosen.slice();bestFilled=filledWeight();lastImprovementNode=nodes;learner.rememberPositive?.(best);}
      choice=selected.point;options=selected.legal.map(placement=>{
        let atChoice=0,coverage=0,size=0;
        const materialized=!!placement.occupancy,source=materialized?placement.occupancy.values():placement.orientation.occupancy.values();
        for(const local of source){const entry=materialized?local:{point:a2Add(local.point,placement.translation),weight:local.weight},key=a2Key(entry.point);size++;if(key===choice)atChoice=entry.weight;if((sums.get(key)||0)>0)coverage++;}
        const newPoints=size-coverage;
        return{placement,clusterScore:clusterProposalScore(placement),markScore:learner.score?.(placement)??0,fills:selected.value+atChoice>=targetAt(choice.split(",").map(Number))-1e-7,coverage,newPoints,tie:random()};
      }).sort((a,b)=>b.clusterScore-a.clusterScore||b.markScore-a.markScore||Number(b.fills)-Number(a.fills)||b.coverage-a.coverage||b.newPoints-a.newPoints||a.tie-b.tie).map(entry=>entry.placement);
      choiceInfo={forced:options.length===1,branchCount:options.length,frontierValue:selected.value,frontierDistance:selected.distance,nearestFrontierDistance:nearestDistance};
    }else{
      for(const [point,target] of desired){const current=sums.get(point)||0;if(current>=target.weight-1e-7)continue;
        const legal=legalAt(point).sort((left,right)=>(preferredRanks.get(left.id)??Infinity)-(preferredRanks.get(right.id)??Infinity));if(!legal.length){noteFailedPath(trackers,point);emit("fail",{choice:point,frontierValue:current});return false;}
        choice=point;options=legal;choiceInfo={forced:legal.length===1,branchCount:legal.length,frontierValue:current};break;
      }
    }
    if(!options)return false;
    for(const placement of options){
      if(stopToken.stop)return "unknown";
      if(nodes>=nodeLimit)return "unknown";
      // A learned revision may have invalidated options computed earlier at this node.
      if(usedPlacements.has(placement.id)||!learner.compatible(placement,markingSeed?[markingSeed,...chosen]:chosen))continue;
      materializePlacement(placement);
      if(maximize&&[...placement.occupancy].some(([key,entry])=>(sums.get(key)||0)+entry.weight<targetAt(entry.point)-1e-7&&!learner.frontierCompatible?.(frontierPattern(key,placement.occupancy))))continue;
      emit("trial",{candidate:placement,choice,...choiceInfo});
      if(animationDelayMs>0)await new Promise(resolve=>setTimeout(resolve,animationDelayMs));
      const context=chosen.slice(),candidateContacts=new Set(placement.occupancy.keys());
      const branchTracker={rootDepth:chosen.length,path:[],failurePoint:null,failurePoints:new Map(),footprint:new Map(),frontier:context.filter(prior=>[...prior.occupancy.keys()].some(key=>candidateContacts.has(key)))},childTrackers=[...trackers,branchTracker];
      nodes++;chosen.push(placement);usedPlacements.add(placement.id);learner.push?.(placement);for(const [key,e] of placement.occupancy){if(!sums.has(key))pointDepth.set(key,depth+1);sums.set(key,(sums.get(key)||0)+e.weight);}
      noteFailedPath(childTrackers);
      const filled=filledWeight();if(!maximize&&filled>bestFilled){bestFilled=filled;best=chosen.slice();}
      emit("placement",{choice,...choiceInfo});await new Promise(requestAnimationFrame);
      // A placement can strand a different point than the one it just filled.
      // Detect that local certificate immediately instead of burying it beneath
      // thousands of unrelated outward moves.
      const stranded=maximize?[...placement.occupancy].find(([key,entry])=>(sums.get(key)||0)<targetAt(entry.point)-1e-7&&!legalAt(key,1).length)?.[0]??null:null;
      if(stranded){if(!legalAt(stranded,1,true).length)learner.rememberFrontierFailure?.(frontierPattern(stranded));noteFailedPath(childTrackers,stranded);emit("fail",{choice:stranded,frontierValue:sums.get(stranded)||0});}
      const result=stranded?false:await search(depth+1,childTrackers);
      if(result===true)return true;
      chosen.pop();usedPlacements.delete(placement.id);learner.pop?.(placement);for(const [key,e] of placement.occupancy){const next=(sums.get(key)||0)-e.weight;if(next<1e-7){if(startPointMap.has(key)){sums.set(key,0);pointDepth.set(key,0);}else{sums.delete(key);pointDepth.delete(key);}}else sums.set(key,next);}
      if(result==="unknown"||result==="stagnant")return result;
      // This exact candidate and placement context has been exhausted. Keep it
      // across marking re-encodings: a new geometric witness may generalize a
      // permanent failure differently, but it may not make the same observed
      // failed branch unknown again.
      exhaustedBranches.add(branchKey(placement,context));
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
        if(update?.revision||update?.geometricRevision){learner.reset?.(markingSeed?[markingSeed,...context]:context);emit("learn",{update,removed:placement});}
        else if(update?.skipped)emit("learning-skip",{update,removed:placement});
      }
      if(nodes%32===0)await new Promise(requestAnimationFrame);
    }
    return false;
  }
  let result=await search();
  while((result===false||result==="stagnant")&&!stopToken.stop){
    const reencoding=await learner.reencodeLatest?.({shouldStop:()=>stopToken.stop,onProgress:attempts=>emit("learning-progress",{attempts,reencoding:true})});if(!reencoding||reencoding.aborted)break;
    chosen.splice(0,chosen.length);usedPlacements.clear();sums.clear();pointDepth.clear();
    for(const [key,e] of seedOccupancy){sums.set(key,e.weight);pointDepth.set(key,0);}for(const key of startPointMap.keys()){if(!sums.has(key))sums.set(key,0);pointDepth.set(key,0);}
    learner.reset?.(markingSeed?[markingSeed]:[]);
    emit("marking-reencoded",{reencoding,reason:result==="stagnant"?"stagnation":"root-exhausted"});
    lastImprovementNode=nodes;
    const nodesBeforeRestart=nodes;
    result=await search();
    if(result===false&&nodes===nodesBeforeRestart){emit("memo-fixed-point",{reason:"all-root-options-memoized"});break;}
  }
  if(result!==true){chosen.splice(0,chosen.length,...best);sums.clear();for(const [key,e] of seedOccupancy)sums.set(key,e.weight);for(const p of chosen)for(const [key,e] of p.occupancy)sums.set(key,(sums.get(key)||0)+e.weight);}
  emit("finished",{result:result===true?"yes":result===false?"no":"unknown"});
  return {result:result===true?"yes":result===false?"no":"unknown",placements:chosen,stats:{nodes,backtracks,exactMemoPrunes,memoizedBranches:exhaustedBranches.size,...learner.stats()}};
}

// A failed branch is only a negative example for one local configuration.  A
// newly encoded geometric inequality can recognize many transformed copies of
// it, which is the source of both GCTS's leverage and its risk of
// over-generalization.  Select a revision on a fresh run before treating the
// learned marking as a reusable search add-on.  Revision zero is deliberately
// included as the safe, geometry-only fallback.
export async function selectA2FrozenMarking({learner,solveOptions,validationSeed=2,validationSeeds=null,validationNodeLimit=3000,confirmationCandidates=2,onValidation=()=>{}}){
  const all=learner.freezeCandidates(),indexes=new Set([0,1,2,3,all.length-1]);
  for(let index=4;index<all.length;index*=2)indexes.add(index);
  const candidates=[...indexes].filter(index=>index>=0&&index<all.length).sort((a,b)=>a-b).map(index=>all[index]);
  return selectA2MarkingCandidates({candidates,solveOptions,validationSeed,validationSeeds,validationNodeLimit,confirmationCandidates,onValidation});
}

export async function selectA2MarkingCandidates({candidates,solveOptions,validationSeed=2,validationSeeds=null,validationNodeLimit=3000,confirmationCandidates=2,onValidation=()=>{}}){
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
