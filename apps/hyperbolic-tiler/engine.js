/* Hyperbolic tile geometry and genuine edge-to-edge DFS. No construction oracle in Search.
 * UMD: usable in a browser without a build step, and with node:test. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.Hyperbolic = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const EPS = 1e-8, TAU = 2 * Math.PI;
  const add=(a,b)=>[a[0]+b[0],a[1]+b[1]], sub=(a,b)=>[a[0]-b[0],a[1]-b[1]];
  const mul=(a,b)=>[a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0]];
  const div=(a,b)=>{const s=b[0]*b[0]+b[1]*b[1];return [(a[0]*b[0]+a[1]*b[1])/s,(a[1]*b[0]-a[0]*b[1])/s];};
  const conj=a=>[a[0],-a[1]], norm2=a=>a[0]*a[0]+a[1]*a[1], norm=a=>Math.hypot(...a);
  const scale=(a,s)=>[a[0]*s,a[1]*s];
  const near=(a,b)=>norm(sub(a,b))<EPS;
  const key=p=>p.map(x=>x.toFixed(8)).join(',');
  const phi=(z,a)=>div(sub(z,a),sub([1,0],mul(conj(a),z)));
  const invPhi=(z,a)=>div(add(z,a),add([1,0],mul(conj(a),z)));
  const klein=p=>scale(p,2/(1+norm2(p)));
  const fromKlein=p=>scale(p,1/(1+Math.sqrt(Math.max(0,1-norm2(p)))));
  const distance=(a,b)=>2*Math.asinh(norm(sub(a,b))/Math.sqrt(Math.max(1e-30,(1-norm2(a))*(1-norm2(b)))));
  const upperToDisk=(p,cx=0,cy=1)=>div([(p[0]-cx)/cy,p[1]/cy-1],[(p[0]-cx)/cy,p[1]/cy+1]);
  const diskToUpper=(p,cx=0,cy=1)=>{const q=mul([0,1],div(add([1,0],p),sub([1,0],p)));return [cx+cy*q[0],cy*q[1]];};
  const signedArea=v=>v.reduce((s,a,i)=>{const b=v[(i+1)%v.length];return s+a[0]*b[1]-a[1]*b[0];},0)/2;
  function segmentDistance(a,b) {
    const d=sub(b,a), t=Math.max(0,Math.min(1,-(a[0]*d[0]+a[1]*d[1])/(norm2(d)||1)));
    return norm(add(a,scale(d,t)));
  }
  function tile(v, spec, extra={}) {
    const k=v.map(klein), c=scale(v.reduce(add,[0,0]),1/v.length);
    return {v,k,c,angles:spec.angles,...extra};
  }
  function family(m=2) {
    if (![2,3,4].includes(m)) throw new Error('Supported branching factors: 2, 3, 4.');
    const upper=Array.from({length:m+1},(_,j)=>[j,1]).concat([[m,m],[0,m]]);
    const angles=upper.map((_,j)=>j===0||j===m?'a':j<=m?'b':'c');
    const v=upper.map(p=>upperToDisk(p,m/2,Math.sqrt(m)));
    return {id:'binary-'+m,m,upper,v,angles,cx:m/2,cy:Math.sqrt(m),
      name:m===2?'Böröczky pentagon':m===3?'Ternary hexagon':'Quaternary heptagon',
      lengths:v.map((p,i)=>distance(p,v[(i+1)%v.length])),area:2*(m-1)*Math.atan(0.5)};
  }
  function align(v,i,a,b) {
    // Map source directed edge i to a -> b by an orientation-preserving disk isometry.
    const s=v[i],t=v[(i+1)%v.length];
    let u=div(phi(b,a),phi(t,s));u=scale(u,1/norm(u));
    const out=v.map(z=>invPhi(mul(u,phi(z,s)),a));
    out[i]=a;out[(i+1)%v.length]=b;
    return out;
  }
  function overlaps(a,b) {
    // Separating-axis test in the Klein disk: hyperbolic convexity becomes Euclidean convexity.
    for (const p of [a.k,b.k]) for(let i=0;i<p.length;i++) {
      const q=p[(i+1)%p.length],n=[p[i][1]-q[1],q[0]-p[i][0]],len=norm(n);
      let amin=Infinity,amax=-Infinity,bmin=Infinity,bmax=-Infinity;
      for(const v of a.k){const d=(v[0]*n[0]+v[1]*n[1])/len;amin=Math.min(amin,d);amax=Math.max(amax,d);}
      for(const v of b.k){const d=(v[0]*n[0]+v[1]*n[1])/len;bmin=Math.min(bmin,d);bmax=Math.max(bmax,d);}
      if(Math.min(amax,bmax)-Math.max(amin,bmin)<1e-10) return false;
    }
    return true;
  }
  function interiorOnSegment(p,a,b) {
    const d=sub(b,a),q=sub(p,a),s=norm2(d),t=(q[0]*d[0]+q[1]*d[1])/s;
    return t>1e-7&&t<1-1e-7&&Math.abs(q[0]*d[1]-q[1]*d[0])/Math.sqrt(s)<1e-9;
  }
  function vertexCounts(tiles) {
    const map=new Map();
    for(const t of tiles) t.v.forEach((p,i)=>{const id=key(p);if(!map.has(id))map.set(id,{a:0,b:0,c:0});map.get(id)[t.angles[i]]++;});
    return map;
  }
  function anglePossible(c) {
    // alpha = atan(1/2) is irrational relative to pi. Complete vertex multisets:
    // a+a+c+c, or b+c+c; a=pi/2-alpha, b=pi-2alpha, c=pi/2+alpha.
    return c.c<=2 && ((c.b===0&&c.a<=2)||(c.b<=1&&c.a===0));
  }
  function validate(candidate,tiles,pruneAngles=true) {
    for(const t of tiles) if(overlaps(candidate,t)) return {ok:false,reason:'interior overlap',conflict:t.node};
    for(const t of tiles) {
      for(const p of candidate.k) for(let j=0;j<t.k.length;j++)
        if(interiorOnSegment(p,t.k[j],t.k[(j+1)%t.k.length]))return {ok:false,reason:'non-edge-to-edge contact',conflict:t.node};
      for(const p of t.k) for(let j=0;j<candidate.k.length;j++)
        if(interiorOnSegment(p,candidate.k[j],candidate.k[(j+1)%candidate.k.length]))return {ok:false,reason:'non-edge-to-edge contact',conflict:t.node};
    }
    if(pruneAngles){
      const counts=vertexCounts(tiles);
      for(let i=0;i<candidate.v.length;i++){
        const c={a:0,b:0,c:0,...counts.get(key(candidate.v[i]))};c[candidate.angles[i]]++;
        if(!anglePossible(c))return {ok:false,reason:'unfillable vertex-angle sum',vertex:candidate.v[i]};
      }
    }
    return {ok:true};
  }
  function frontier(tiles) {
    const map=new Map();
    for(const t of tiles) for(let i=0;i<t.v.length;i++){
      const a=t.v[i],b=t.v[(i+1)%t.v.length],ka=key(a),kb=key(b),id=ka<kb?ka+'|'+kb:kb+'|'+ka;
      if(map.has(id))map.delete(id);else map.set(id,{a,b,t,i,d:segmentDistance(klein(a),klein(b))});
    }
    return [...map.values()];
  }
  function candidates(spec,e,tiles) {
    const out=[], len=distance(e.a,e.b), known=tiles.flatMap(t=>t.v);
    for(let i=0;i<spec.v.length;i++)if(Math.abs(spec.lengths[i]-len)<1e-6){
      let v=align(spec.v,i,e.b,e.a);
      v=v.map(p=>known.find(q=>near(p,q))||p);
      const t=tile(v,spec,{edge:i});
      if(!out.some(o=>t.v.every(p=>o.v.some(q=>near(p,q)))))out.push(t);
    }
    // These presets are reflection-symmetric; reflected copies give no extra candidates.
    return out;
  }
  function rng(seed) {let s=seed>>>0;return ()=>{s+=0x6D2B79F5;let t=s;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return ((t^t>>>14)>>>0)/4294967296;};}
  class Search {
    constructor(spec,{radius=1.6,seed=1,anglePrune=true,maxTiles=600,order='shuffle'}={}) {
      if(!(radius>0&&radius<=3))throw new Error('Search radius must be in (0,3].');
      this.spec=spec;this.options={radius,seed,anglePrune,maxTiles,order};this.random=rng(seed);
      this.tiles=[tile(spec.v,spec,{node:0})];this.stats={attempts:0,rejected:0,placed:1,backtracks:0,deadEnds:0,maxDepth:1,events:0};
      this.done=false;this.iterator=this.run();
    }
    next(){const r=this.iterator.next();if(r.done){this.done=true;return null;}this.stats.events++;return {...r.value,depth:this.tiles.length,event:this.stats.events};}
    *run(){yield {type:'seed',node:0};const result=yield* this.visit();yield {type:result===true?'solved':result==='limit'?'limit':'exhausted'};}
    *visit(){
      const edges=frontier(this.tiles).filter(e=>e.d<Math.tanh(this.options.radius)-1e-9).sort((a,b)=>a.d-b.d);
      if(!edges.length)return true;
      if(this.tiles.length>=this.options.maxTiles)return 'limit';
      const e=edges[0],cs=candidates(this.spec,e,this.tiles);
      if(this.options.order==='shuffle')for(let i=cs.length-1;i>0;i--){const j=Math.floor(this.random()*(i+1));[cs[i],cs[j]]=[cs[j],cs[i]];}
      yield {type:'choose',edge:[e.a,e.b],choices:cs.length};
      for(const t of cs){
        const node=++this.stats.attempts,parent=this.tiles.at(-1).node;t.node=node;
        yield {type:'try',tile:t,node,parent,edge:[e.a,e.b]};
        const check=validate(t,this.tiles,this.options.anglePrune);
        if(!check.ok){this.stats.rejected++;yield {type:'reject',tile:t,node,...check};continue;}
        this.tiles.push(t);this.stats.placed++;this.stats.maxDepth=Math.max(this.stats.maxDepth,this.tiles.length);
        yield {type:'place',tile:t,node,parent};
        const result=yield* this.visit();if(result===true||result==='limit')return result;
        this.tiles.pop();this.stats.backtracks++;yield {type:'backtrack',tile:t,node};
      }
      this.stats.deadEnds++;yield {type:'dead-end',edge:[e.a,e.b]};return false;
    }
  }
  function construction(spec,radius=4.8){
    const {m,cx,cy}=spec,lo=cy*Math.exp(-radius),hi=cy*Math.exp(radius),centerY=cy*Math.cosh(radius),rad=cy*Math.sinh(radius);
    const kmin=Math.floor(Math.log(lo/(m*Math.sqrt(1.25)))/Math.log(m)),kmax=Math.ceil(Math.log(hi)/Math.log(m));
    const result=[];
    for(let k=kmin;k<=kmax;k++){
      const s=m**k,yl=s,yh=s*m*Math.sqrt(1.25);
      if(yh<lo||yl>hi)continue;
      const y=Math.max(yl,Math.min(yh,centerY)),dx=Math.sqrt(Math.max(0,rad*rad-(y-centerY)**2));
      const jmin=Math.floor((cx-dx)/(m*s))-1,jmax=Math.ceil((cx+dx)/(m*s));
      for(let j=jmin;j<=jmax;j++){
        const v=spec.upper.map(([x,y])=>upperToDisk([s*(x+m*j),s*y],cx,cy));
        const t=tile(v,spec,{row:k,column:j,node:result.length});
        // Include tiles intersecting the radius ball, not just those whose centers lie inside.
        if(t.k.some(p=>norm(p)<Math.tanh(radius))||t.k.some((p,i)=>segmentDistance(p,t.k[(i+1)%t.k.length])<Math.tanh(radius)))result.push(t);
      }
    }
    return result.sort((a,b)=>norm2(a.c)-norm2(b.c));
  }
  return {EPS,TAU,add,sub,mul,div,conj,norm,norm2,scale,near,key,phi,invPhi,klein,fromKlein,distance,
    upperToDisk,diskToUpper,signedArea,segmentDistance,tile,family,align,overlaps,validate,frontier,candidates,anglePossible,Search,construction};
});
