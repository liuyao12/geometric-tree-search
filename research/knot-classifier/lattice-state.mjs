// Exact cubic-lattice states. No diagram representation or knot invariants.
const key = p => p.join(',');
export function unitLoop(input) {
  if (!Array.isArray(input) || input.length < 4) throw Error('A lattice loop needs at least four vertices.');
  const points=input.map(p=>{
    if (!Array.isArray(p)||p.length!==3||p.some(x=>!Number.isSafeInteger(x)||Math.abs(x)>10000)) throw Error('Invalid integer lattice vertex.');
    return [...p];
  });
  if (key(points[0])===key(points.at(-1))) points.pop();
  const unit=[];
  for (let i=0;i<points.length;i++) {
    const a=points[i],b=points[(i+1)%points.length],d=b.map((x,k)=>x-a[k]);
    const axes=d.flatMap((x,k)=>x?[k]:[]);
    if(axes.length!==1)throw Error('Edges must be nonzero and parallel to a coordinate axis.');
    const axis=axes[0];
    for(let k=0;k<Math.abs(d[axis]);k++) {
      const p=[...a];p[axis]+=k*Math.sign(d[axis]);unit.push(p);
      if(unit.length>100000)throw Error('Lattice edge budget exceeded.');
    }
  }
  if(unit.length<4||new Set(unit.map(key)).size!==unit.length)throw Error('Loop is degenerate or self-intersects.');
  return unit;
}
export function gridLift(grid) {
  if (!Array.isArray(grid)||grid.length<4||grid.length%2||grid.some(p=>!Array.isArray(p)||p.length!==2||p.some(x=>!Number.isSafeInteger(x))))throw Error('Invalid grid coordinates.');
  const rows=new Map(),cols=new Map();
  grid.forEach(([x,y],i)=>{if(!rows.has(y))rows.set(y,[]);if(!cols.has(x))cols.set(x,[]);rows.get(y).push(i);cols.get(x).push(i);});
  const n=grid.length/2;
  if(new Set(grid.map(key)).size!==grid.length||rows.size!==n||cols.size!==n||[...rows.values(),...cols.values()].some(x=>x.length!==2))throw Error('Each grid row and column must contain exactly two points.');
  const bends=[],visited=new Set();let i=0,horizontal=true;
  do {
    if(visited.has(i))throw Error('Malformed grid traversal.');visited.add(i);
    const [x,y]=grid[i],pair=(horizontal?rows.get(y):cols.get(x));
    const j=pair[0]===i?pair[1]:pair[0],[u,v]=grid[j],height=horizontal?0:1;
    bends.push([x,y,height],[u,v,height]);i=j;horizontal=!horizontal;
  }while(i!==0);
  if(!horizontal||visited.size!==grid.length)throw Error('Grid has multiple link components.');
  // Endpoint connectors alternate height. Each vertical strand passes above
  // the horizontal strands, exactly as in the source grid convention.
  unitLoop(bends);return bends;
}
export function translationKey(input) {
  const points=unitLoop(input),mins=[0,1,2].map(k=>Math.min(...points.map(p=>p[k])));
  const words=points.map(p=>p.map((x,k)=>x-mins[k]));
  // Choose a unique lexicographic root without identifying spatial mirrors.
  let root=0;for(let i=1;i<words.length;i++)for(let k=0;k<3;k++){
    if(words[i][k]===words[root][k])continue;if(words[i][k]<words[root][k])root=i;break;
  }
  const a=Array.from({length:words.length},(_,k)=>words[(root+k)%words.length]);
  const b=Array.from({length:words.length},(_,k)=>words[(root-k+words.length)%words.length]);
  return [JSON.stringify(a),JSON.stringify(b)].sort()[0];
}
export function mirror(input) {return unitLoop(input).map(([x,y,z])=>[-x,y,z]);}
export function bounds(input) {
  const points=unitLoop(input);
  return {edges:points.length,min:[0,1,2].map(k=>Math.min(...points.map(p=>p[k]))),max:[0,1,2].map(k=>Math.max(...points.map(p=>p[k])))};
}
// Labels are deliberately discarded at the search boundary. A candidate
// index can be mapped to its evaluator label only after certificate replay.
export function searchInput(record,mirrored=false) {
  return {vertices:mirrored?mirror(record.vertices):unitLoop(record.vertices)};
}
// Exact spatial seams: traversal root/orientation are immaterial, but the
// coordinate frame is fixed. Bounds therefore describe one physical region.
export function embeddingKey(input) {
  const p=unitLoop(input),mins=[0,1,2].map(k=>Math.min(...p.map(x=>x[k])));
  return JSON.stringify(JSON.parse(translationKey(p)).map(x=>x.map((v,k)=>v+mins[k])));
}
