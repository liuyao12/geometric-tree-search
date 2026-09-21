// Heuristic period proposals from repeated placements, followed by exact quotient
// cover and the independent periodic certificate verifier. Failure is inconclusive.
import {verifyPolycubePeriodicCertificate} from '../../assets/polycube-periodic-tiler.js';
import {polycubeOrientations} from '../../assets/polycube-enumerator.js';
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0),cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const mod=(x,n)=>(x%n+n)%n;
export function patchPeriodProposals(voxels,placements,{timeMs=5000,maxVectors=36,nodesPerBasis=10000,includeReflections=false}={}){
 const start=performance.now(),deadline=start+timeMs,orientations=polycubeOrientations(voxels,{includeReflections});
 const vectors=new Map();
 for(let i=0;i<placements.length;i++)for(let j=0;j<i;j++)if(placements[i].oi===placements[j].oi){
  let v=placements[i].translation.map((x,k)=>(x-placements[j].translation[k])/2);
  if(v.some(x=>!Number.isInteger(x)))throw Error('Expected half-unit coordinates with even translations');
  if(!v.some(Boolean))continue;if(v.find(x=>x)!==Math.abs(v.find(x=>x)))v=v.map(x=>-x);
  const key=v.join();if(!vectors.has(key))vectors.set(key,{v,count:0});vectors.get(key).count++;
 }
 const ranked=[...vectors.values()].sort((a,b)=>b.count-a.count||dot(a.v,a.v)-dot(b.v,b.v)).slice(0,maxVectors);
 const stats={vectors:vectors.size,selectedVectors:ranked.length,bases:0,fullPoolBases:0,searchNodes:0,budgetStops:0};let certificate=null,reason='proposal pool exhausted';
 outer:for(let i=0;i<ranked.length;i++)for(let j=0;j<i;j++)for(let k=0;k<j;k++){
  if(performance.now()>=deadline){reason='time budget';break outer;}
  const basis=[ranked[i].v,ranked[j].v,ranked[k].v],det=Math.abs(dot(basis[0],cross(basis[1],basis[2])));
  if(!det||det%voxels.length||det>placements.length*voxels.length)continue;stats.bases++;
  const numerators=[cross(basis[1],basis[2]),cross(basis[2],basis[0]),cross(basis[0],basis[1])],sites=new Map(),unique=new Map();
  for(const p of placements){
   const orientation=orientations[p.oi];if(!orientation)throw Error('Unknown orientation');
   const translation=p.translation.map(x=>x/2);if(translation.some(x=>!Number.isInteger(x)))throw Error('Invalid translation');
   const keys=orientation.voxels.map(v=>{const q=v.map((x,l)=>x+translation[l]);return numerators.map(n=>mod(dot(n,q),det)).join();});
   if(new Set(keys).size!==voxels.length)continue;
   let mask=0n;for(const key of keys){if(!sites.has(key))sites.set(key,sites.size);mask|=1n<<BigInt(sites.get(key));}
   unique.set(mask,{mask,orientation_index:p.oi,orientation_key:orientation.key,translation});
  }
  if(sites.size!==det)continue;stats.fullPoolBases++;
  const pool=[...unique.values()],bySite=Array.from({length:det},()=>[]);
  for(const p of pool)for(let x=0;x<det;x++)if(p.mask&(1n<<BigInt(x)))bySite[x].push(p);
  const full=(1n<<BigInt(det))-1n,selected=[];let nodes=0,stopped=false;
  const visit=used=>{
   if(used===full)return true;
   if(++nodes>nodesPerBasis||performance.now()>=deadline){stopped=true;return false;}
   let options=null;
   for(let x=0;x<det;x++)if(!(used&(1n<<BigInt(x)))){const list=bySite[x].filter(p=>!(p.mask&used));if(!list.length)return false;if(!options||list.length<options.length)options=list;}
   for(const p of options){selected.push(p);if(visit(used|p.mask))return true;selected.pop();if(stopped)return false;}return false;
  };
  const found=visit(0n);stats.searchNodes+=nodes;if(stopped)stats.budgetStops++;
  if(found){
   certificate={certified:true,can_tile:true,copies:det/voxels.length,period_vectors:basis,placements:selected.map(({mask,...p})=>p)};
   const replay=verifyPolycubePeriodicCertificate(voxels,certificate,{includeReflections});if(!replay.verified)throw Error('Periodic proposal failed independent replay');
   certificate.verification=replay;reason='verified periodic construction';break outer;
  }
 }
 return {found:!!certificate,certificate,reason,stats:{...stats,elapsedMs:performance.now()-start},scope:'Heuristic period bases and placement pool from a finite patch; no negative periodicity or aperiodicity claim.'};
}
