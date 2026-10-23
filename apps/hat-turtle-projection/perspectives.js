// A two-real-parameter family of complex-linear orthogonal projections C^2 -> C.
export const SQRT3=Math.sqrt(3);
export const FAMILY_STOPS={chevron:0,hat:1/3,equal:.5,turtle:2/3,comet:1};
export const familyAngle=m=>(1-m)*Math.PI/2;
export const certifiedMarks=m=>m>=1/3-1e-10&&m<=2/3+1e-10;
export function coefficients(m,phi=0,exact=null){
 if(m<=0)return {u:0,vr:Math.cos(phi),vi:Math.sin(phi)};
 if(m>=1)return {u:1,vr:0,vi:0};
 if(exact){const re=exact.xn/(exact.q*SQRT3),im=exact.yn/exact.q,u=1/Math.sqrt(1+re*re+im*im);return {u,vr:u*re,vi:u*im};}
 const a=familyAngle(m),u=Math.cos(a),v=Math.sin(a);return {u,vr:v*Math.cos(phi),vi:v*Math.sin(phi)};
}
export function projectPerspective(ux,uy,vx,vy,w,frame={re:1,im:0,tx:0,ty:0}){
 const x=w.u*ux+w.vr*vx-w.vi*vy,y=w.u*uy+w.vi*vx+w.vr*vy;
 return [frame.re*x-frame.im*y+frame.tx,frame.im*x+frame.re*y+frame.ty,0];
}
export function alignedPerspective(xn,yn,q=1){
 if(![xn,yn,q].every(Number.isSafeInteger)||q<=0)throw Error('Expected integer rational coordinates');
 const re=xn/(q*SQRT3),im=yn/q,r=Math.hypot(re,im);
 return {m:1-2*Math.atan(r)/Math.PI,phi:r?Math.atan2(im,re):0,exact:{xn,yn,q}};
}
const gcd=(a,b)=>{a=Math.abs(a);b=Math.abs(b);while(b)[a,b]=[b,a%b];return a;};
function bezout(a,b){if(!b)return [Math.abs(a),a<0?-1:1,0];const [g,x,y]=bezout(b,a%b);return [g,y,x-Math.trunc(a/b)*y];}
export function latticeBasis(m,phi=0,exact=null){
 if(m>=1)return [[1,0],[.5,SQRT3/2]];
 if(m<=0){const c=Math.cos(phi),s=Math.sin(phi);return [[c*SQRT3/2-s*.5,s*SQRT3/2+c*.5],[-s,c]];}
 if(!exact)return null;
 const {xn,yn,q}=exact,D=3*q,A=xn-3*yn,B=xn+3*yn;
 const columns=[[D,0],[0,D],[A,B],[-B,A+B]];
 let gy=0,x0=0,index=0;
 for(const [x,y] of columns){const [g,a,b]=bezout(gy,y);x0=a*x0+b*x;gy=g;}
 for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)index=gcd(index,columns[i][0]*columns[j][1]-columns[j][0]*columns[i][1]);
 const h=index/gy,k=((x0%h)+h)%h,c=coefficients(m,phi,exact).u;
 return [[c*h/D,0],[c*(k+gy/2)/D,c*SQRT3*gy/(2*D)]];
}
export function namedAlignment(name){
 if(name==='hat')return alignedPerspective(3,0);
 if(name==='turtle')return alignedPerspective(1,0);
 if(name==='chevron')return {m:0,phi:0,exact:null};
 if(name==='comet')return alignedPerspective(0,0);
 if(name==='aligned-a')return alignedPerspective(2,1);
 if(name==='aligned-b')return alignedPerspective(-1,1);
 if(name==='aligned-c')return alignedPerspective(2,0);
 return null;
}
export function alignmentSamples(){
 const out=new Map();
 const add=(x,y,q)=>{if(!x&&!y)return;const g=gcd(gcd(x,y),q);x/=g;y/=g;q/=g;const id=`${x},${y},${q}`;if(!out.has(id))out.set(id,alignedPerspective(x,y,q));};
 for(let q=1;q<=3;q++)for(let x=-5*q;x<=5*q;x++)for(let y=-3*q;y<=3*q;y++)add(x,y,q);
 for(const scale of [8,16,32,64])for(let x=-3;x<=3;x++)for(let y=-3;y<=3;y++)add(x*scale,y*scale,1);
 return [...out.values()].sort((a,b)=>(a.exact.q+Math.abs(a.exact.xn)+Math.abs(a.exact.yn))-(b.exact.q+Math.abs(b.exact.xn)+Math.abs(b.exact.yn)));
}
