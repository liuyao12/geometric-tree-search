// Exact storage of a Cartesian product of decorated choices. NOT a quotient:
// each (left,right) remains a different candidate with the same base inventory.
// Endpoint filters must be separable; arbitrary rejected pairs use exclusions.
// This class does not decide geometric/cloud legality or implement tree search.
export class FactorizedCandidateDomain {
  constructor(leftSize,rightSize){
    for(const n of [leftSize,rightSize])if(!Number.isSafeInteger(n)||n<0)throw Error('Invalid choice count');
    this.sizes=[leftSize,rightSize];this.allowed=[null,null];this.enabled=true;
    this.exclusions=new Map();this.trail=[];
  }
  validate(side,index){
    if(![0,1].includes(side)||!Number.isSafeInteger(index)||index<0||index>=this.sizes[side])throw Error('Invalid endpoint choice');
  }
  checkpoint(){return this.trail.length;}
  setEnabled(value){
    if(typeof value!=='boolean')throw Error('Expected Boolean');
    if(value!==this.enabled){this.trail.push(['enabled',this.enabled]);this.enabled=value;}
  }
  setAllowed(side,indices){
    if(![0,1].includes(side))throw Error('Invalid endpoint');
    let next=null;
    if(indices!==null){
      next=new Set(indices);
      for(const i of next)this.validate(side,i);
    }
    this.trail.push(['allowed',side,this.allowed[side]]);this.allowed[side]=next;
  }
  containsEndpoint(side,index){return this.allowed[side]===null||this.allowed[side].has(index);}
  forbid(left,right){
    this.validate(0,left);this.validate(1,right);const key=`${left}:${right}`;
    if(!this.exclusions.has(key)){this.trail.push(['exclude',key]);this.exclusions.set(key,[left,right]);}
  }
  has(left,right){
    this.validate(0,left);this.validate(1,right);
    return this.enabled&&this.containsEndpoint(0,left)&&this.containsEndpoint(1,right)&&!this.exclusions.has(`${left}:${right}`);
  }
  get count(){
    if(!this.enabled)return 0n;
    let n=BigInt(this.allowed[0]?.size??this.sizes[0])*BigInt(this.allowed[1]?.size??this.sizes[1]);
    for(const [a,b] of this.exclusions.values())if(this.containsEndpoint(0,a)&&this.containsEndpoint(1,b))n--;
    return n;
  }
  *endpointIndices(side){
    if(this.allowed[side]!==null){yield* [...this.allowed[side]].sort((a,b)=>a-b);return;}
    for(let i=0;i<this.sizes[side];i++)yield i;
  }
  *values(){
    if(this.count===0n)return;
    for(const a of this.endpointIndices(0))for(const b of this.endpointIndices(1))if(!this.exclusions.has(`${a}:${b}`))yield [a,b];
  }
  first(){return this.values().next().value??null;}
  sole(){return this.count===1n?this.first():null;}
  undo(checkpoint){
    if(!Number.isInteger(checkpoint)||checkpoint<0||checkpoint>this.trail.length)throw Error('Invalid checkpoint');
    while(this.trail.length>checkpoint){
      const [kind,a,b]=this.trail.pop();
      if(kind==='enabled')this.enabled=a;
      else if(kind==='allowed')this.allowed[a]=b;
      else this.exclusions.delete(a);
    }
  }
  snapshot(){return {sizes:[...this.sizes],enabled:this.enabled,allowed:this.allowed.map(s=>s===null?null:[...s].sort((a,b)=>a-b)),exclusions:[...this.exclusions.values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1])};}
}

// Cardinality-only reference scheduler comparison. Points and their incident
// blocks are supplied by the caller; this does not construct/update that graph.
// Returns the point/domain count without materializing all branch candidates.
export function factorizedDecision(points){
  let forced=null,unknown=null,branch=null;
  const earlier=(a,b)=>!b||a.generation<b.generation||(a.generation===b.generation&&(a.count<b.count||(a.count===b.count&&a.id.localeCompare(b.id)<0)));
  for(const point of points){
    if(new Set(point.blocks).size!==point.blocks.length)throw Error('Repeated incident block');
    const row={...point,count:point.blocks.reduce((n,b)=>n+b.count,0n)};
    if(row.count===0n&&row.complete)return {kind:'dead',point:row.id};
    if(row.count===1n&&row.complete&&earlier(row,forced))forced=row;
    if(row.count===0n&&!row.complete&&!unknown)unknown=row;
    if(earlier(row,branch))branch=row;
  }
  if(forced)return {kind:'forced',point:forced.id};
  if(unknown)return {kind:'unknown',point:unknown.id};
  if(!branch)return {kind:'complete'};
  return {kind:'branch',point:branch.id,provisional:!branch.complete};
}
