// Goodman–Strauss, arXiv:2609.24779v1, Figures 2 and 5.
// Figure 5 folded with the full central face at z=0 and the socket at (1,1,1).
export const SOURCE = 'https://arxiv.org/abs/2609.24779';
export const COLORS = { red: 0xde292d, green: 0x9cc83b, blue: 0x2b407d };
export const FACE_DIRECTIONS = [[0,0,-1],[0,0,1],[0,-1,0],[0,1,0],[-1,0,0],[1,0,0]];
export const add = (a,b) => a.map((v,i)=>v+b[i]);
export const sub = (a,b) => a.map((v,i)=>v-b[i]);
export const key = p => p.join(',');
export const apply = (r,p) => r.map(row=>row.reduce((s,v,i)=>s+v*p[i],0));
export const IDENTITY = [[1,0,0],[0,1,0],[0,0,1]];
export const transpose = r => r[0].map((_,i)=>r.map(row=>row[i]));
export const multiply = (a,b) => a.map(row=>transpose(b).map(col=>row.reduce((s,v,i)=>s+v*col[i],0)));
export const localCells = missing => {
  const out=[];
  for(let x=0;x<2;x++) for(let y=0;y<2;y++) for(let z=0;z<2;z++)
    if(key([x,y,z])!==key(missing)) out.push([x,y,z]);
  return out;
};
const determinant = r => r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])-r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])+r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]);
export const ROTATIONS = [];
for(const p of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]])
  for(let mask=0;mask<8;mask++) {
    const r=p.map((a,i)=>[0,1,2].map(j=>j===a ? (mask>>i&1 ? -1:1):0));
    if(determinant(r)===1) ROTATIONS.push(r);
  }
// Color tables indexed by the two other coordinate bits, first axis slowest.
const FACE_COLORS = [
  ['green','green','red','blue'], // z=0: (x,y)
  ['blue','green','red',null],   // z=2: (x,y)
  ['red','red','green','blue'],  // y=0: (x,z)
  ['blue','red','green',null],   // y=2: (x,z)
  ['blue','green','red','blue'], // x=0: (y,z)
  ['blue','green','red',null]   // x=2: (y,z)
];
const baseCells=localCells([1,1,1]);
const occupied=new Set(baseCells.map(key));
export const BASE_MARKS=[];
for(const cell of baseCells) for(let face=0;face<6;face++) {
  const direction=FACE_DIRECTIONS[face];
  if(occupied.has(key(add(cell,direction)))) continue;
  const axis=direction.findIndex(v=>v!==0), tangent=[0,1,2].filter(i=>i!==axis);
  const socket=cell[axis]===0 && direction[axis]===1;
  const color=socket ? ['blue','green','red'][axis] : FACE_COLORS[face][2*cell[tangent[0]]+cell[tangent[1]]];
  const arrow=cell.map((v,i)=>i===axis?0:socket?-1:2*v-1);
  BASE_MARKS.push({cell,direction,color,arrow});
}
export const transformCell = (r,cell) => apply(r,cell.map(v=>2*v-1)).map(v=>(v+1)/2);
export const VARIANTS=ROTATIONS.map((rotation,id)=>({
  id,rotation,missingCorner:transformCell(rotation,[1,1,1]),
  cells:baseCells.map(c=>transformCell(rotation,c)),
  marks:BASE_MARKS.map(m=>({...m,cell:transformCell(rotation,m.cell),direction:apply(rotation,m.direction),arrow:apply(rotation,m.arrow)}))
}));
export const rotationId = r => ROTATIONS.findIndex(s=>key(s.flat())===key(r.flat()));
// An equality-valued marking at each doubled-grid panel center. Opposite
// normals and opposite red/green signs give identical polar vectors.
export const markPoint = m => m.cell.map((v,i)=>2*v+1+m.direction[i]);
export const markValue = m => [...m.arrow,...m.direction.map(v=>v*(m.color==='red'?1:m.color==='green'?-1:0))];
export const matches = (a,b) => key(markValue(a))===key(markValue(b));
export function worldMarks(placement) {
  return VARIANTS[placement.variantId].marks.map(m=>({...m,cell:add(m.cell,placement.origin)}));
}
export function verifyPatch(placements) {
  const cells=new Set(), marks=new Map(); let contacts=0;
  for(const p of placements) {
    for(const c of VARIANTS[p.variantId].cells) {
      const k=key(add(c,p.origin)); if(cells.has(k)) return {valid:false,reason:'overlap'}; cells.add(k);
    }
    for(const m of worldMarks(p)) {
      const k=key(markPoint(m)), value=key(markValue(m));
      if(marks.has(k)) { if(marks.get(k)!==value) return {valid:false,reason:'mark mismatch'}; contacts++; }
      marks.set(k,value);
    }
  }
  return {valid:true,cells:cells.size,contacts};
}
export const CANONICAL_CHILDREN=[[[0,0,0],[1,1,1]],[[0,0,2],[1,1,0]],[[0,2,0],[1,0,1]],[[0,2,2],[1,0,0]],[[1,1,1],[1,1,1]],[[2,0,0],[0,1,1]],[[2,0,2],[0,1,0]],[[2,2,0],[0,0,1]]];
// Determine the proper rotations of the eight children from the actual marks.
// Outer supertile corner arrows must also agree with the parent's decoration.
function childDomains() {
  return CANONICAL_CHILDREN.map(([origin,missing],index)=>VARIANTS.filter(v=>key(v.missingCorner)===key(missing)).filter(v=>{
    if(index===4) return v.id===rotationId(IDENTITY);
    const back=missing.map(b=>1-b);
    return v.marks.filter(m=>m.cell.every((c,i)=>c===back[i])).every(m=>{
      const parentCell=origin.map(c=>c/2);
      const parent=BASE_MARKS.find(b=>key(b.cell)===key(parentCell)&&key(b.direction)===key(m.direction));
      return parent && parent.color===m.color && key(parent.arrow)===key(m.arrow);
    });
  }).map(v=>({origin,variantId:v.id})));
}
function findChildren(domains,chosen=[]) {
  if(chosen.length===domains.length) return chosen;
  for(const p of domains[chosen.length]) if(verifyPatch([...chosen,p]).valid) {
    const result=findChildren(domains,[...chosen,p]); if(result) return result;
  }
  return null;
}
export const CHILDREN=findChildren(childDomains());
if(!CHILDREN) throw new Error('Chair44 arrow transcription does not admit its marked substitution.');
export function childSupertile(parent,index) {
  const child=CHILDREN[index], childSize=parent.size/2;
  const center=add(child.origin,[1,1,1]).map(v=>(v-2)*childSize/2);
  const relative=apply(parent.rotation,center).map(v=>v+parent.size/2-childSize/2);
  const rotation=multiply(parent.rotation,VARIANTS[child.variantId].rotation);
  return {origin:add(parent.origin,relative),size:childSize,rotation,missingCorner:transformCell(rotation,[1,1,1])};
}
export function chairLeaves(level,origin=[0,0,0],rotation=IDENTITY,path=[]) {
  if(!level) return [{origin,rotation,variantId:rotationId(rotation),missingCorner:transformCell(rotation,[1,1,1]),path}];
  const parent={origin,rotation,size:2**(level+1)};
  return CHILDREN.flatMap((_,i)=>{const c=childSupertile(parent,i);return chairLeaves(level-1,c.origin,c.rotation,[...path,i]);});
}
export function parentContainingChild(current,index) {
  const rotation=multiply(current.rotation,transpose(VARIANTS[CHILDREN[index].variantId].rotation));
  const parent={origin:[0,0,0],rotation,size:current.size*2,missingCorner:transformCell(rotation,[1,1,1])};
  parent.origin=sub(current.origin,childSupertile(parent,index).origin);
  return parent;
}
