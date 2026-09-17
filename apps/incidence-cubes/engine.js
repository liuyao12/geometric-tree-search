/* Pure mathematical engine. Browser-independent; also tested with Node.
   Coordinates use column vectors, with projective point (x,y,z). */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.IncidenceMath=api;})(globalThis,()=>{
'use strict';
const EDGES=[[0,1],[0,2],[0,4],[1,3],[1,5],[2,3],[2,6],[3,7],[4,5],[4,6],[5,7],[6,7]];
const FACES=[[0,1,3,2],[6,7,5,4],[0,4,5,1],[3,7,6,2],[0,2,6,4],[5,7,3,1]];
const LABELS=['∅','1','2','12','3','13','23','123'];
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),norm=a=>Math.hypot(...a);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const scale=(a,t)=>a.map(x=>x*t),add=(a,b)=>a.map((x,i)=>x+b[i]);
const outer=(a,b=a)=>a.map(x=>b.map(y=>x*y));
const mul=(A,x)=>A.map(r=>dot(r,x));
const quad=(Q,x)=>dot(x,mul(Q,x));
const zeros=n=>Array.from({length:n},()=>Array(n).fill(0));
function det(A){if(!A.length)return 1;if(A.length===1)return A[0][0];return A[0].reduce((s,x,j)=>s+(j%2?-1:1)*x*det(A.slice(1).map(r=>r.filter((_,k)=>k!==j))),0);}
function inverse(A){const n=A.length;if(!n)return [];const B=A.map((r,i)=>[...r,...Array.from({length:n},(_,j)=>+(i===j))]);for(let j=0;j<n;j++){let k=j;for(let i=j+1;i<n;i++)if(Math.abs(B[i][j])>Math.abs(B[k][j]))k=i;if(Math.abs(B[k][j])<1e-10)throw new Error('Singular parameter block');[B[j],B[k]]=[B[k],B[j]];const t=B[j][j];B[j]=B[j].map(x=>x/t);for(let i=0;i<n;i++)if(i!==j){const v=B[i][j];B[i]=B[i].map((x,k)=>x-v*B[j][k]);}}return B.map(r=>r.slice(n));}
const unit=a=>{const n=norm(a);if(n<1e-12)throw new Error('Zero projective representative');return scale(a,1/n);};
const affine=p=>Math.abs(p[2])<1e-9?null:[p[0]/p[2],p[1]/p[2],1];
const parity=n=>{let p=0;for(;n;n>>=1)p^=n&1;return p;};
const edgeId=(a,b)=>EDGES.findIndex(e=>(e[0]===a&&e[1]===b)||(e[0]===b&&e[1]===a));
const faceEdges=f=>f.map((v,i)=>edgeId(v,f[(i+1)%4]));
const POS=FACES.flatMap(f=>[edgeId(f[0],f[1]),edgeId(f[2],f[3])]);
const NEG=FACES.flatMap(f=>[edgeId(f[2],f[1]),edgeId(f[0],f[3])]);
function defaults(){return {couplings:[0.35,-0.25,0.45],offsets:[0.20,0.10,-0.08],angles:[0,2.0943951023931953,4.1887902047863905],diagonal:3.5};}
function penrose(params=defaults()){
 const {couplings:[a,b,c],offsets,angles,diagonal:d}=params;
 const M=[[d,a,b],[a,d,c],[b,c,d]],p=angles.map((t,i)=>[Math.cos(t),Math.sin(t),offsets[i]]),q0=[[1,0,0],[0,1,0],[0,0,-1]],Q=[],blocks=[];
 for(let s=0;s<8;s++){const ix=[0,1,2].filter(i=>s&(1<<i)),A=ix.map(i=>ix.map(j=>M[i][j])),H=inverse(A);blocks.push({ix,A,H});Q[s]=q0.map(r=>r.slice());for(let u=0;u<3;u++)for(let v=0;v<3;v++)for(let i=0;i<ix.length;i++)for(let j=0;j<ix.length;j++)Q[s][u][v]-=p[ix[i]][u]*H[i][j]*p[ix[j]][v];}
 const contacts=EDGES.map(([s,t])=>{const k=Math.log2(s^t),{ix,H}=blocks[s],a=ix.map(i=>M[i][k]),v=mul(H,a),l=p[k].slice();for(let j=0;j<3;j++)for(let i=0;i<ix.length;i++)l[j]-=v[i]*p[ix[i]][j];const delta=M[k][k]-dot(a,v);let err=0;for(let i=0;i<3;i++)for(let j=0;j<3;j++){const left=delta*(Q[s][i][j]-Q[t][i][j]),right=l[i]*l[j];err=Math.max(err,Math.abs(left-right)/(1+Math.abs(left)+Math.abs(right)));}return {s,t,l,delta,error:err};});
 const faces=FACES.map(vs=>{const es=faceEdges(vs),ls=es.map(e=>contacts[e].l),R=cross(ls[0],ls[1]);const n=norm(R);return {edges:es,point:n>1e-12?unit(R):null,error:n>1e-12?Math.max(...ls.map(l=>Math.abs(dot(l,R))/(norm(l)*n))):null};});
 return {Q,p,M,contacts,faces,maxEdge:Math.max(...contacts.map(e=>e.error)),maxFace:Math.max(...faces.map(f=>f.error??Infinity)),minMinor:Math.min(...blocks.map(b=>Math.abs(det(b.A)))),minConic:Math.min(...Q.map(q=>Math.abs(det(q)))),seedIndependent:Math.abs(det(p))>1e-8};
}
function lineConic(Q,l){const n=l[0]*l[0]+l[1]*l[1];if(n<1e-12)return [];const x=[-l[2]*l[0]/n,-l[2]*l[1]/n,1],v=[-l[1],l[0],0];const a=quad(Q,v),b=2*dot(v,mul(Q,x)),c=quad(Q,x),disc=b*b-4*a*c;if(disc<0)return [];if(Math.abs(a)<1e-12)return Math.abs(b)<1e-12?[]:[add(x,scale(v,-c/b))];return [(-b-Math.sqrt(disc))/(2*a),(-b+Math.sqrt(disc))/(2*a)].map(t=>add(x,scale(v,t)));}
function ellipse(Q,n=240){const A=Q[0][0],B=Q[0][1],C=Q[1][1],D=A*C-B*B;if(D<=1e-10||A<=0)return null;const cx=(B*Q[1][2]-C*Q[0][2])/D,cy=(B*Q[0][2]-A*Q[1][2])/D,k=-quad(Q,[cx,cy,1]);if(k<=0)return null;const t=Math.atan2(2*B,A-C)/2,h=Math.hypot(A-C,2*B),r=Math.sqrt(k/((A+C+h)/2)),s=Math.sqrt(k/((A+C-h)/2));return Array.from({length:n+1},(_,i)=>{const u=2*Math.PI*i/n;return [cx+r*Math.cos(u)*Math.cos(t)-s*Math.sin(u)*Math.sin(t),cy+r*Math.cos(u)*Math.sin(t)+s*Math.sin(u)*Math.cos(t)];});}
function fomin(O=[0.08,-0.05,1],ts=[0.57,0.68,0.78]){
 const labels=[],lines=[[0.7,1,-0.8],[-0.9,0.5,-0.9],[0.1,-1,-0.85]],pairs=[[0,1,3],[0,2,5],[1,2,6]],vertices=[];
 labels[0]=O;[1,2,4].forEach((id,i)=>labels[id]=lines[i]);
 pairs.forEach(([i,j,id],k)=>{const A=affine(cross(lines[i],lines[j]));if(!A)throw new Error('Seed intersection is at infinity');vertices.push(A);labels[id]=add(scale(O,1-ts[k]),scale(A,ts[k]));});
 const R1=cross(lines[0],cross(labels[3],labels[5])),R2=cross(lines[1],cross(labels[3],labels[6])),R3=cross(lines[2],cross(labels[5],labels[6]));labels[7]=unit(cross(R1,R2));
 const weights=EDGES.map(([i,j])=>parity(i)===0?dot(labels[j],labels[i]):dot(labels[i],labels[j]));
 const ratios=FACES.map((_,f)=>weights[POS[2*f]]*weights[POS[2*f+1]]/(weights[NEG[2*f]]*weights[NEG[2*f+1]]));
 const minPairing=Math.min(...EDGES.map(([i,j],e)=>Math.abs(weights[e])/(norm(labels[i])*norm(labels[j]))));
 return {labels,vertices,meetings:[R1,R2,R3],ratios,weights,minPairing,error:Math.max(...ratios.map(r=>Math.abs(r-1))),thirdError:Math.abs(dot(labels[7],R3))/norm(R3)};
}
function gcd(a,b){a=a<0n?-a:a;b=b<0n?-b:b;while(b){[a,b]=[b,a%b];}return a;}
function rational(n,d=1n){n=BigInt(n);d=BigInt(d);if(!d)throw new Error('Zero denominator');const g=gcd(n,d)*(d<0n?-1n:1n);return {n:n/g,d:d/g};}
const times=(a,b)=>rational(a.n*b.n,a.d*b.d),ratioString=r=>r.d===1n?`${r.n}`:`${r.n}/${r.d}`;
function surface(weights){if(weights.length!==12||weights.some(v=>!Number.isSafeInteger(v)||v===0))throw new Error('Use twelve nonzero integer edge values');const ratios=FACES.map((_,f)=>rational(BigInt(weights[POS[2*f]])*BigInt(weights[POS[2*f+1]]),BigInt(weights[NEG[2*f]])*BigInt(weights[NEG[2*f+1]])));return {ratios,product:ratios.reduce(times,rational(1))};}
function coherentWeights(){const v=[2,3,5,7,11,13,17,19];return EDGES.map(([a,b])=>v[a]*v[b]);}
function bridge(t=0.45,angle=0.6,offset=0.2){const l=[Math.cos(angle),Math.sin(angle),offset],V=outer(l),Q0=[[1,0,0],[0,1,0],[0,0,-1]],Q=Q0.map((r,i)=>r.map((x,j)=>x-t*V[i][j])),coeff=A=>[A[0][0],A[1][1],A[2][2],2*A[0][1],2*A[0][2],2*A[1][2]];return {l,Q0,Q,veronese:coeff(V),coefficients:coeff(Q),base:coeff(Q0)};}
return {EDGES,FACES,LABELS,POS,NEG,dot,norm,cross,scale,add,outer,mul,quad,det,inverse,unit,affine,parity,edgeId,faceEdges,defaults,penrose,lineConic,ellipse,fomin,rational,times,ratioString,surface,coherentWeights,bridge};
});
