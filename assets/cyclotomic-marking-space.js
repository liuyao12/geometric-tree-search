import {canonical,latticeKey} from './cyclotomic-five.js?v=20260908-speed';
import {num,add,sub,mul,conj} from './penrose-polygon.js?v=20260908-speed';

// The scalar solution space is ker D over Q. For equality rows e_i-e_j,
// its exact representation is an equivalence relation: no numerical rank
// tolerance is needed. The displayed u_i are independent quotient basis
// vectors, not fixed scalar labels. Every scalar solution assigns them values.
export function createMarkingSpace(problem){
 const {catalog,actions,rigid,resolve}=problem,slots=[],plans=new Map(),slotAt=new Map();
 for(const tile of catalog){
  const points=new Map();
  tile.exactPoints.forEach((p,i)=>{
   points.set(latticeKey(p),p);
   const midpoint=mul(add(p,tile.exactPoints[(i+1)%tile.exactPoints.length]),canonical({coeff:[1,0,0,0],denominator:2}));
   points.set(latticeKey(midpoint),midpoint);
  });
  const rows=[...points.values()].map(offset=>{const row={slot:slots.length,type:tile.type,offset};slots.push(row);slotAt.set(tile.type+'@'+latticeKey(offset),row.slot);return row;});
  plans.set(tile.type,rows);
 }
 // All orientations are represented explicitly. The rigid group permutes
 // address variables. Closing each contact under these permutations ensures
 // the quotient inherits an action, including stabilizers and reflections.
 const permutations=actions.map(g=>{
  const permutation=Array(slots.length),act=p=>mul(g.factor,g.reflect?conj(p):p);
  for(const tile of catalog){const target=rigid(resolve(tile.type,num(0)),g);
   for(const row of plans.get(tile.type)){
    const slot=slotAt.get(target.type+'@'+latticeKey(sub(act(row.offset),target.origin)));
    if(slot===undefined)throw Error('Marking support is not closed under rigid transformations');
    permutation[row.slot]=slot;
   }
  }
  if(new Set(permutation).size!==slots.length)throw Error('Marking action is not a permutation');
  return permutation;
 });
 const parent=slots.map((_,i)=>i),sizes=slots.map(()=>1),minimum=slots.map((_,i)=>i),trail=[],frames=[],active=new Map();
 let dimension=slots.length,revision=0,contacts=0,detailCache=null;
 const root=i=>{while(parent[i]!==i)i=parent[i];return i;};
 function unite(i,j){
  let a=root(i),b=root(j);if(a===b)return;
  if(sizes[a]<sizes[b])[a,b]=[b,a];
  trail.push({a,b,size:sizes[a],minimum:minimum[a]});parent[b]=a;sizes[a]+=sizes[b];minimum[a]=Math.min(minimum[a],minimum[b]);dimension--;
 }
 function support(tile){return plans.get(tile.type).map(row=>{const point=add(tile.origin,row.offset);return{slot:row.slot,point,key:latticeKey(point)};});}
 function push(tile){
  const rows=support(tile),frame={id:tile.id,start:trail.length,contacts,rows};
  for(const row of rows){const previous=active.get(row.key)||[];
   // One representative spans all equalities at this world point. Existing
   // occupants have already been equated, together with every group image.
   if(previous.length){contacts++;for(const permutation of permutations)unite(permutation[previous[0]],permutation[row.slot]);}
   previous.push(row.slot);active.set(row.key,previous);
  }
  frames.push(frame);if(trail.length!==frame.start)revision++;
 }
 function pop(tile){
  const frame=frames.at(-1);if(!frame||frame.id!==tile.id)throw Error('Marking-space rollback must follow placement order');
  frames.pop();const changed=trail.length!==frame.start;
  while(trail.length>frame.start){const {a,b,size,minimum:oldMinimum}=trail.pop();parent[b]=b;sizes[a]=size;minimum[a]=oldMinimum;dimension++;}
  for(const row of frame.rows){const occupants=active.get(row.key);occupants.pop();if(!occupants.length)active.delete(row.key);}
  contacts=frame.contacts;if(changed)revision++;
 }
 function tables(){
  if(detailCache?.revision!==revision)detailCache={revision,tables:[...plans].map(([type,rows])=>({type,rows:rows.map(row=>({offset:row.offset,channel:0,value:'u'+minimum[root(row.slot)]}))}))};
  return detailCache.tables;
 }
 return{push,pop,support,get revision(){return revision;},
  memory:()=>({points:active.size,values:active.size}),
  snapshot:({details=true}={})=>({kind:'space',revision,variables:slots.length,dimension,rank:slots.length-dimension,contacts,symmetryOrder:actions.length,addresses:slots.length,entries:slots.length,...(details?{tables:tables()}: {})}),
  // Copies for independent replay and action/rollback tests, never mutable
  // internals. Partition labels identify a basis, not numerical coefficients.
  inspect:()=>({classes:slots.map((_,i)=>minimum[root(i)]),slots:slots.map(r=>({...r})),permutations:permutations.map(p=>p.slice())})
 };
}
