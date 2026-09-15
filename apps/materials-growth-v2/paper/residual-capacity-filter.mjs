// Proven necessary local subset-sum filter; not learned m-values or chemistry.
// Complete finite candidate pool, integer capacity <= 24. Full rebuild after
// each state change deliberately favors auditability over incremental speed.
export function residualCapacityClass(PointSearch){
 return class ResidualCapacitySearch extends PointSearch{
  constructor(model){
   const required=new Set(model.required.map(p=>typeof p==='string'?p:p.id));
   if(model.expand||model.constraint||model.complete===false||model.capacity>24||model.required.some(p=>typeof p!=='string'&&p.complete===false)||
      model.candidates.some(c=>c.t.some(x=>!required.has(x.point))))
    throw Error('Residual filter requires a complete fixed pool and capacity <= 24');
   super(model);
  }
  reason(c){return super.reason(c)||(this.capacityBlocked?.has(c.id)?'residual-capacity':null);}
  refresh(_changed){
   this.capacityBlocked=new Set();
   this.capacityDiagnostics??={rebuilds:0,pointTests:0,subsetTests:0,removed:0};
   this.capacityDiagnostics.rebuilds++;
   // Recompute from physical point totals and marks, never reuse child cuts.
   super.refresh(new Set(this.points.keys()));
   const queue=[...this.graph.keys()],queued=new Set(queue);
   for(let cursor=0;cursor<queue.length;cursor++){
    const p=queue[cursor];queued.delete(p);const point=this.points.get(p),rows=[...(this.graph.get(p)||[])];
    if(!point?.complete||!rows.length)continue;
    this.capacityDiagnostics.pointTests++;
    const deficit=this.capacity-point.total,mask=(2**(deficit+1))-1;
    const possible=(skip,target)=>{
     this.capacityDiagnostics.subsetTests++;if(target<0)return false;
     let bits=1;for(let i=0;i<rows.length;i++)if(i!==skip)bits=(bits|(bits<<rows[i][1]))&mask;
     return !!(bits&(1<<target));
    };
    const feasible=possible(-1,deficit);
    const remove=rows.filter(([,value],i)=>!feasible||!possible(i,deficit-value)).map(([id])=>id);
    for(const id of remove){
     if(this.capacityBlocked.has(id))continue;
     const touched=[...this.reverse.get(id)];this.capacityBlocked.add(id);this.capacityDiagnostics.removed++;
     this.updateCandidate(id);
     for(const q of touched)if(!queued.has(q)&&this.graph.has(q)){queue.push(q);queued.add(q);}
    }
   }
  }
 };
}

// Independent slow checker: explicit integer-sum sets, not the filter bitsets.
export function independentResidualDomains(engine,model){
 const totals=new Map(model.required.map(p=>[typeof p==='string'?p:p.id,0])),marks=new Map(),chosen=new Set(engine.placed.keys());
 const putMark=x=>{const key=JSON.stringify([x.point,x.channel??'0']),range=marks.get(key)||[-Infinity,Infinity];range[0]=Math.max(range[0],x.lo);range[1]=Math.min(range[1],x.hi);marks.set(key,range);};
 for(const x of model.fixedMarks||[])putMark(x);
 for(const c of model.candidates)if(chosen.has(c.id)){for(const x of c.t)totals.set(x.point,(totals.get(x.point)||0)+x.value);for(const x of c.m||[])putMark(x);}
 const alive=new Set(model.candidates.filter(c=>!chosen.has(c.id)&&!engine.staticCertifiedExclusions?.has(c.id)&&!engine.branchBlocked?.has(c.id)&&c.t.every(x=>(totals.get(x.point)||0)+x.value<=model.capacity)&&
  (c.m||[]).every(x=>{const range=marks.get(JSON.stringify([x.point,x.channel??'0']));return !range||Math.max(range[0],x.lo)<=Math.min(range[1],x.hi);})).map(c=>c.id));
 const frontier=new Map([...totals].filter(([p,v])=>engine.points.get(p)?.active&&v<model.capacity).map(([p])=>[p,[]]));
 for(const c of model.candidates)for(const x of c.t)if(frontier.has(x.point))frontier.get(x.point).push([c.id,x.value]);
 let changed=true;
 while(changed){changed=false;
  for(const [p,all] of frontier){if(!engine.points.get(p).complete)continue;
   const rows=all.filter(([id])=>alive.has(id)),deficit=model.capacity-totals.get(p);
   for(let omit=0;omit<rows.length;omit++){
    let sums=new Set([0]);for(let k=0;k<rows.length;k++)if(k!==omit){const next=new Set(sums);for(const s of sums)if(s+rows[k][1]<=deficit)next.add(s+rows[k][1]);sums=next;}
    if(!sums.has(deficit-rows[omit][1])){alive.delete(rows[omit][0]);changed=true;}
   }
  }
 }
 return new Map([...frontier].map(([p,rows])=>[p,new Map(rows.filter(([id])=>alive.has(id)))]));
}
