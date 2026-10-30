/** Explicitly restricted controls, not ports of missing aperiodic markings. */
import {Golden as G,ONE,vector,vadd,vscale} from '../../assets/golden-field.js';
import {preparePrototype,place,I,O,mv,mm} from '../../assets/polyhedral-exact-search.js';
const rotations=[I,[vector(0n,1n,0n),vector(-1n,0n,0n),vector(0n,0n,1n)],[vector(0n,0n,1n),vector(0n,1n,0n),vector(-1n,0n,0n)]];
const mod=(n,p)=>(n%p+p)%p;
function voxelCells(raw){const {cells,grid}=raw.recipe,step=grid.map(s=>new G(...(()=>{const [a,d='1']=s.split('/');return [a,'0',d];})()).mul(4n));if(step.some(x=>!x.isInteger()))throw Error('Quarter-grid control requires integer voxel boundaries');const out=[];for(const cell of cells)for(let x=step[cell[0]].a;x<step[cell[0]+1].a;x++)for(let y=step[cell[1]].a;y<step[cell[1]+1].a;y++)for(let z=step[cell[2]].a;z<step[cell[2]+1].a;z++)out.push({p:[x,y,z],weight:3n});return out;}
function iCells(axis){const out=[];for(let a=-4n;a<4n;a++)for(let b=-1n;b<=0n;b++)for(let c=-1n;c<=0n;c++){const p=axis===0?[a,b,c]:axis===1?[-b-1n,a,c]:[-c-1n,b,a];out.push({p,weight:a===-1n||a===0n?1n:3n});}return out;}
export function goodmanControl(id,data,{periods=3}={}){
 if(!Number.isInteger(periods)||periods<2||periods>4)throw Error('Registered control period must be 2–4');const side=8n*BigInt(periods),required=[];for(let x=0n;x<side;x++)for(let y=0n;y<side;y++)for(let z=0n;z<side;z++)required.push(`${x},${y},${z}`);
 const raw=data.systems[id],L=raw.find(t=>t.id==='L'),prototypes=raw.map(t=>preparePrototype({...t,color:({L:'#dcb477',I:'#83afcf',X0:'#70b9b2',X1:'#b29bce'})[t.id]})),placements=[];
 for(let i=0;i<periods;i++)for(let j=0;j<periods;j++)for(let k=0;k<periods;k++)for(const p of prototypes){
  const axes=p.kind==='I'?[0,1,2]:[0],offset=p.kind==='L'?0n:4n,translation=[BigInt(i)*8n+offset,BigInt(j)*8n+offset,BigInt(k)*8n+offset];
  for(const axis of axes){const tile=place(p,p.kind==='I'?rotations[axis]:I,vector(...translation.map(x=>new G(x,0n,4n)))),cells=p.kind==='I'?iCells(axis):voxelCells(p.raw);tile.occupancy=cells.map(c=>({key:c.p.map((x,n)=>mod(x+translation[n],side)).join(','),weight:c.weight}));tile.pointMarkings=[];placements.push(tile);}
 }
 const root=placements.find(t=>t.kind==='L'&&t.translation.every(x=>!x.sign()));return {id,mode:'registered-geometry',prototypes,placements,required,capacity:3n,seedId:root.id,completion:'finite exact registered periodic point cover; source boundary colours not enforced',domain:{kind:'quarter-grid periodic control',periods,sideQuarterUnits:String(side),registration:'L centres on 2Z^3; I/cross centres on (2Z+1)^3',weights:'full cells 1; central I-pyramid cells 1/3; exact integer capacity 3'},scope:'Registered geometry-only control on a finite periodic quarter-grid target. The geometric L/X partition and the three-I dissection of X define these point weights. Source boundary colours are not enforced. This is not the unrestricted geometric search or an aperiodicity certificate.'};
}
function power(m,k){let r=I,base=k<0?[0,1,2].map(i=>vector(...m.map(c=>c[i]))):m;for(let i=0;i<Math.abs(k);i++)r=mm(r,base);return r;}
function* choices(steps,at=0,values=[]){if(at===steps.length){yield values;return;}for(const value of [-1n,0n,1n])yield*choices(steps,at+1,[...values,value]);}
export function scdControl(data,{width=3,layers=5}={}){
 const proto=preparePrototype(data.systems.scd[0]),a=vector(5n,0n,0n),b=vector(3n,4n,0n),c=vector(new G(3n,0n,2n),2n,1n),R=[vector(new G(3n,0n,5n),new G(-4n,0n,5n),0n),vector(new G(4n,0n,5n),new G(3n,0n,5n),0n),vector(0n,0n,1n)];
 if(mv(R,b).some((x,i)=>!x.equals(a[i])))throw Error('SCD layer ridges fail exact alignment');
 const radius=Math.floor(width/2),depth=Math.floor(layers/2),placements=[],required=[];
 for(let k=-depth;k<=depth;k++)for(let i=-radius;i<=radius;i++)for(let j=-radius;j<=radius;j++){
  const key=`${i},${j},${k}`;required.push(key);const steps=k>0?Array.from({length:k},(_,n)=>n):Array.from({length:-k},(_,n)=>-n-1),rot=power(R,k);
  for(const values of choices(steps)){let shift=O;steps.forEach((l,n)=>{shift=vadd(shift,vscale(mv(power(R,l),b),values[n]*(k>0?1n:-1n)));});const base=vadd(vscale(a,BigInt(i)),vscale(b,BigInt(j))),translation=vadd(vadd(vector(0n,0n,BigInt(k)),shift),mv(rot,vadd(base,vscale(c,-1n)))),tile=place(proto,rot,translation);tile.color=['#83afcf','#70b9b2','#dcb477','#b29bce','#cf9687'][k+depth];tile.id+=`#${steps.map((l,n)=>l+':'+values[n]).join(';')}`;tile.occupancy=[{key,weight:1n}];tile.pointMarkings=steps.map((l,n)=>({point:vector(1000000n,BigInt(l),0n),components:{'scd:layer-offset':values[n]}}));placements.push(tile);}
 }
 const root=placements.find(t=>t.occupancy[0].key==='0,0,0');return {id:'scd',mode:'layer-address-control',prototypes:[proto],placements,required,capacity:1n,seedId:root.id,completion:'finite SCD layer-address assignment complete; Euclidean coverage outside the crop is not claimed',domain:{kind:'finite layer-address adaptation',width,layers,stepChoices:['-1','0','1'],rotation:R.map(p=>p.map(x=>x.toJSON()))},scope:'Exact source-style screw-layer construction with a finite address crop and three discrete inter-layer offsets. Mark-only components enforce a single offset history across each layer. This is an explicitly restricted construction-domain search; continuous sliding and unrestricted geometric attachment are not enumerated.'};
}
