// Independent periodic seven-grid dual and union-find edge-state witness.
// Decoration labels are reconstructed from row propagation, not the catalog.
export async function socolarWitness(){
const {catalog,placement,ZERO,direction,add,sub,key,compare,edgeAxis}=await import('../assets/sevenfold-rhombs.js');
const templates=catalog(),phase=[.13,.23,.31,.41,.53,.61,.71],e=Array.from({length:7},(_,i)=>({x:Math.cos(2*Math.PI*i/7),y:Math.sin(2*Math.PI*i/7)}));
const tiles=[];
for(let m=0;m<7;m++)for(let n=m+1;n<7;n++)for(let a=-4;a<=4;a++)for(let b=-4;b<=4;b++){
 const det=e[m].x*e[n].y-e[n].x*e[m].y,x=((a+phase[m])*e[n].y-(b+phase[n])*e[m].y)/det,y=(e[m].x*(b+phase[n])-e[n].x*(a+phase[m]))/det;
 if(x*x+y*y>9)continue;
 const c=e.map((v,i)=>i===m?a-1:i===n?b-1:Math.floor(x*v.x+y*v.y-phase[i]));
 const origin=c.reduce((p,v,i)=>add(p,direction(2*i).map(z=>z*v)),ZERO);
 let points=[origin,add(origin,direction(2*m)),add(add(origin,direction(2*m)),direction(2*n)),add(origin,direction(2*n))];
 if(det<0)points.reverse();const offset=points.slice().sort(compare)[0],sig=points.map(p=>key(sub(p,offset))).sort().join('|');
 const template=templates.find(t=>t.points.map(key).sort().join('|')===sig);if(!template)throw Error('template');
 tiles.push(placement(template,offset));
}
const parents=new Map(),fixed=new Map();function root(k){if(!parents.has(k))parents.set(k,k);if(parents.get(k)!==k)parents.set(k,root(parents.get(k)));return parents.get(k);}
const edgeKey=(t,i,k)=>key(add(t.points[i],t.points[(i+1)%4]))+'/'+edgeAxis(sub(t.points[(i+1)%4],t.points[i])).axis+'/'+k;
for(const t of tiles)for(let i=0;i<2;i++){
 const a=edgeAxis(sub(t.points[(i+1)%4],t.points[i])),b=edgeAxis(sub(t.points[(i+2)%4],t.points[(i+1)%4])),d=(b.axis-a.axis+7)%7,k=Math.min(d,7-d)-1;
 for(let j=0;j<3;j++)if(j!==k)parents.set(root(edgeKey(t,i,j)),root(edgeKey(t,i+2,j)));
}
for(const t of tiles)for(let i=0;i<4;i++){
 const a=edgeAxis(sub(t.points[(i+1)%4],t.points[i])),b=edgeAxis(sub(t.points[(i+2)%4],t.points[(i+1)%4])),d=(b.axis-a.axis+7)%7,k=Math.min(d,7-d)-1,value=a.sign*(d<=3?1:-1)>0?1:0;
 const r=root(edgeKey(t,i,k));if(fixed.has(r)&&fixed.get(r)!==value)throw Error('contradiction');fixed.set(r,value);
}
const decorated=catalog([1,2,3],'socolar');const counts=new Map();
for(const t of tiles){const values=t.points.map((_,i)=>[0,1,2].reduce((v,k)=>v|((fixed.get(root(edgeKey(t,i,k)))||0)<<k),0));
 const variants=decorated.filter(v=>v.type.startsWith(t.type+'~s'));const v=variants.find(v=>v.edgeCodes.every((m,i)=>m.value===values[i]));if(!v)throw Error('invalid decoration');
 if(t.type===templates[0].type){const ix=variants.indexOf(v);counts.set(ix,(counts.get(ix)||0)+1);}
}

const marked=[];
for(const t of tiles){const values=t.points.map((_,i)=>[0,1,2].reduce((v,k)=>v|((fixed.get(root(edgeKey(t,i,k)))||0)<<k),0));const v=decorated.find(v=>v.type===t.type+'~s'+values.join('.'));marked.push(placement(v,t.origin));}
const {geometryAllowed,markingsAgree,translated}=await import('../assets/sevenfold-rhombs.js');
for(let i=0;i<marked.length;i++)for(let j=0;j<i;j++)if(!geometryAllowed(marked[i],marked[j])||!markingsAgree(marked[i],marked[j]))throw Error('invalid witness pair '+i+' '+j);


return marked;
}
