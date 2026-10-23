const R3=Math.sqrt(3);
const gcd=(a,b)=>{a=a<0n?-a:a;b=b<0n?-b:b;while(b)[a,b]=[b,a%b];return a;};
function egcd(a,b){if(!b)return [a<0n?-a:a,a<0n?-1n:1n,0n];const [g,x,y]=egcd(b,a%b);return [g,y,x-(a/b)*y];}
export function scalar(text){
 const s=text.trim();if(s.length>32)throw Error('Keep each coefficient to 32 characters or fewer.');let n,d=1n;
 if(/^[+-]?\d+\/\d+$/.test(s)){const parts=s.split('/');n=BigInt(parts[0]);d=BigInt(parts[1]);if(!d)throw Error('Denominators must be nonzero');}
 else if(/^[+-]?(\d+(\.\d*)?|\.\d+)$/.test(s)){
  const sign=s.startsWith('-')?-1n:1n,parts=s.replace(/^[+-]/,'').split('.'),fraction=parts[1]||'';d=10n**BigInt(fraction.length);n=sign*BigInt((parts[0]||'0')+fraction);
 }else if(/^-?sqrt\((2|3|5)\)$/.test(s)){return {value:(s[0]==='-'?-1:1)*Math.sqrt(Number(s.match(/\d/)[0])),rational:null,source:s};}
 else throw Error('Use a decimal, fraction, sqrt(2), sqrt(3), or sqrt(5).');
 const g=gcd(n,d);n/=g;d/=g;const value=Number(n)/Number(d);if(!Number.isFinite(value)||Math.abs(value)>1000)throw Error('Keep coefficients between -1000 and 1000.');return {value,rational:{n,d},source:s};
}
export function integerImageBasis(columns){
 let gy=0n,x0=0n,index=0n;
 for(const [x,y] of columns){const [g,a,b]=egcd(gy,y);x0=a*x0+b*x;gy=g;}
 for(let i=0;i<columns.length;i++)for(let j=i+1;j<columns.length;j++)index=gcd(index,columns[i][0]*columns[j][1]-columns[j][0]*columns[i][1]);
 if(!gy||!index)throw Error('Rank two is required');const h=index/gy,k=((x0%h)+h)%h;return [[h,0n],[k,gy]];
}
export function matrixPerspective(values,pivots=[0,1]){
 if(values.length!==4||new Set(pivots).size!==2||pivots.some(x=>x<0||x>3))throw Error('Invalid coordinate chart');
 const parsed=values.map(scalar),other=[0,1,2,3].filter(i=>!pivots.includes(i));
 const C=[[0,0,0,0],[0,0,0,0]];C[0][pivots[0]]=1;C[1][pivots[1]]=1;
 for(let r=0;r<2;r++)for(let j=0;j<2;j++)C[r][other[j]]=parsed[2*r+j].value;
 const rows=C.map(([p,q,r,s])=>[p,(-p+2*q)/R3,(2*r-s)/R3,s]);
 const norm0=Math.hypot(...rows[0]),u=rows[0].map(v=>v/norm0),dot=rows[1].reduce((s,v,i)=>s+v*u[i],0),w=rows[1].map((v,i)=>v-dot*u[i]),norm1=Math.hypot(...w),v=w.map(x=>x/norm1);
 let basis=null;
 if(parsed.every(p=>p.rational)){
  let D=1n;for(const p of parsed)D=D/gcd(D,p.rational.d)*p.rational.d;
  const columns=Array.from({length:4},()=>[0n,0n]);columns[pivots[0]][0]=D;columns[pivots[1]][1]=D;
  for(let r=0;r<2;r++)for(let j=0;j<2;j++){const f=parsed[2*r+j].rational;columns[other[j]][r]=f.n*(D/f.d);}
  basis=integerImageBasis(columns).map(([x,y])=>{const a=Number(x)/Number(D),b=Number(y)/Number(D);return [a/norm0,(b-dot*a/norm0)/norm1];});
 }
 return {rows:[u,v],basis,rankTwo:!!basis,C,pivots,values:[...values]};
}
export function projectMatrix(point,projection){return projection.rows.map(row=>row.reduce((s,x,i)=>s+x*point[i],0));}
