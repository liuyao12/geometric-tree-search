// Exhaustive finite quotients of Z^3. Yielding never discards a search frame.
export function* hermiteDomains(det) {
  for (let a=1;a<=det;a++) if(det%a===0)
    for(let d=1;d<=det/a;d++) if(det%(a*d)===0) {
      const f=det/(a*d);
      for(let b=0;b<a;b++) for(let c=0;c<a;c++) for(let e=0;e<d;e++)
        yield [a,b,c,d,e,f];
    }
}
export function quotientIndex(point, h) {
  const [a,b,c,d,e,f]=h;let [x,y,z]=point;
  let q=Math.floor(z/f);x-=q*c;y-=q*e;z-=q*f;
  q=Math.floor(y/d);x-=q*b;y-=q*d;x-=Math.floor(x/a)*a;
  return (z*d+y)*a+x;
}
export function exactDomainModel(orientations, capacity) {
  if(!Number.isSafeInteger(capacity)||capacity<=0||!orientations.length)return null;
  let mass=null;
  for(const o of orientations) {
    if(!o.points.length||o.points.some(p=>!Number.isSafeInteger(p.weight)||p.weight<=0||p.pos.length!==3||p.pos.some(x=>!Number.isSafeInteger(x))))return null;
    const sum=o.points.reduce((s,p)=>s+p.weight,0);
    if(!Number.isSafeInteger(sum)||sum<=0||(mass!==null&&mass!==sum))return null;
    mass=sum;
  }
  return {orientations,capacity,mass};
}
// A finite state tree for each HNF, then the next determinant. No per-domain
// truncation, no display-goal cutoff, and no discarded DFS continuation.
// Rejected complete solutions remain searchable: isohedral certification must
// inspect ALL periodic solutions, not just the first exact cover of a domain.
export function* periodicDomainSearch(model,{rootOrientation=0,maxCopies=Infinity,domainAllowed=()=>true,translationAllowed=()=>true}={}) {
  const {orientations,capacity,mass}=model;
  let domains=0,nodes=0;
  for(let det=1;det<=Math.floor(maxCopies*mass/capacity);det++) {
    const copies=det*capacity/mass;
    if(!Number.isInteger(copies))continue;
    for(const hnf of hermiteDomains(det)) {
      domains++;
      yield {type:'domain',determinant:det,copies,hnf,domains,nodes};
      if(!domainAllowed(hnf))continue;
      const rows=[],byPoint=Array.from({length:det},()=>[]);
      let root=-1;
      for(let oi=0;oi<orientations.length;oi++)
        for(let z=0;z<hnf[5];z++)for(let y=0;y<hnf[3];y++)for(let x=0;x<hnf[0];x++) {
          const translation=[x,y,z],weights=new Map();
          if(!translationAllowed(translation))continue;
          for(const p of orientations[oi].points) {
            const k=quotientIndex(p.pos.map((v,i)=>v+translation[i]),hnf);
            weights.set(k,(weights.get(k)||0)+p.weight);
          }
          if([...weights.values()].every(w=>w<=capacity)) {
            const index=rows.length;
            rows.push({orientation:oi,translation,weights:[...weights]});
            for(const [k]of weights)byPoint[k].push(index);
            if(oi===rootOrientation&&x===0&&y===0&&z===0)root=index;
          }
          yield {type:'work',domains,nodes:++nodes};
        }
      if(root<0)continue;
      const remaining=Array(det).fill(capacity),chosen=[root],used=new Set([root]);
      for(const [k,w]of rows[root].weights)remaining[k]-=w;
      const stack=[{options:null,next:0}];
      while(stack.length) {
        const frame=stack.at(-1);
        if(frame.options===null) {
          yield {type:'work',domains,nodes:++nodes};
          if(chosen.length===copies) {
            if(remaining.every(w=>w===0))yield {type:'solution',determinant:det,copies,hnf,domains,nodes,
              placements:chosen.map(i=>({orientation:rows[i].orientation,translation:rows[i].translation.slice()}))};
            frame.options=[];
          } else {
            for(let k=0;k<det;k++)if(remaining[k]>0) {
              const legal=byPoint[k].filter(i=>!used.has(i)&&rows[i].weights.every(([j,w])=>w<=remaining[j]));
              if(frame.options===null||legal.length<frame.options.length)frame.options=legal;
              if(!legal.length)break;
            }
            frame.options ??= [];
          }
        }
        if(frame.next>=frame.options.length) {
          stack.pop();
          if(stack.length){const i=chosen.pop();for(const [k,w]of rows[i].weights)remaining[k]+=w;used.delete(i);}
        } else {
          const i=frame.options[frame.next++];chosen.push(i);used.add(i);
          for(const [k,w]of rows[i].weights)remaining[k]-=w;
          stack.push({options:null,next:0});
        }
      }
    }
  }
  return {domains,nodes,exhausted:true,maxCopies};
}
