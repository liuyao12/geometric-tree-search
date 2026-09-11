// Prospective protocol: EXPERIMENT-PROTOCOL.md. No preparation metadata enters fitting.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {hingeExamples,connectionDescriptor,twistConnection} from '../connection-descriptor.mjs';
const raw=fs.readFileSync(process.argv[2]);
const lines=raw.toString().trim().split(/\r?\n/);
const frames=new Map(); let offset=0;
for(let id=0;id<96;id++){
  const n=Number(lines[offset]), header=lines[offset+1];
  if(!Number.isInteger(n)||n<1)throw Error('Invalid XYZ count');
  if(id>=24){
    const lattice=header.match(/Lattice="([^"]+)"/);
    if(!lattice)throw Error('Missing cell');
    const matrix=lattice[1].trim().split(/\s+/).map(Number), cell=matrix[0];
    if(matrix.length!==9||matrix.some((v,k)=>Math.abs(v-([0,4,8].includes(k)?cell:0))>1e-7))throw Error('Requires cubic cell');
    const atoms=lines.slice(offset+2,offset+n+2).map(line=>{const f=line.trim().split(/\s+/);return {species:f[0],position:f.slice(1,4).map(Number)};});
    if(atoms.some(a=>a.position.some(v=>!Number.isFinite(v))))throw Error('Invalid coordinate');
    frames.set(id,hingeExamples(atoms,{cell,margin:6}));
  }
  offset+=n+2;
}
// Seeded Fisher–Yates, unsigned Numerical Recipes LCG; explicitly reproducible.
let state=1709; const ids=[...frames.keys()];
for(let i=ids.length-1;i>0;i--){state=(Math.imul(1664525,state)+1013904223)>>>0;const j=Math.floor(state/4294967296*(i+1));[ids[i],ids[j]]=[ids[j],ids[i]];}
const split={train:ids.slice(0,48),calibration:ids.slice(48,60),test:ids.slice(60)};
const descriptor=sites=>[connectionDescriptor(sites,true),connectionDescriptor(sites,false)];
const prepared=new Map([...frames].map(([id,examples])=>[id,examples.map(e=>({positive:descriptor(e.sites),twists:[60,120,180].map(a=>descriptor(twistConnection(e.sites,a*Math.PI/180)))}))]));
function nearest(query,refs){let best=Infinity;for(const ref of refs){if(query.key!==ref.key)continue;let d=0;for(let k=0;k<query.values.length;k++){d=Math.max(d,Math.abs(query.values[k]-ref.values[k]));if(d>=best)break;}if(d<best)best=d;}return best;}
function scores(ds,refs){const j=nearest(ds[0],refs[0]),i=nearest(ds[1],refs[1]);return !Number.isFinite(j)||!Number.isFinite(i)?null:{joint:j,excess:j-i,ratio:j/(i+.05)};}
const results=[],rawScores=[]; const started=performance.now();
for(const count of [4,12,48]){
  const refs=[[],[]];for(const id of split.train.slice(0,count))for(const e of prepared.get(id))for(let k=0;k<2;k++)refs[k].push(e.positive[k]);
  const evaluate=frameIds=>frameIds.map(id=>({id,connections:prepared.get(id).map(e=>({positive:scores(e.positive,refs),twists:e.twists.map(t=>scores(t,refs))}))}));
  const calibration=evaluate(split.calibration),test=evaluate(split.test);
  rawScores.push({count,calibration,test});
  for(const score of ['joint','excess','ratio'])for(const policy of ['p99','maximum']){
    const values=calibration.flatMap(f=>f.connections.filter(c=>c.positive).map(c=>c.positive[score])).sort((a,b)=>a-b);
    if(!values.length)throw Error('Empty calibration stratum');
    const threshold=values[policy==='maximum'?values.length-1:Math.ceil(.99*values.length)-1];
    const perFrame=test.map(f=>{
      let rejected=0,unknown=0,twistRejected=0,twistKnown=0;
      for(const c of f.connections){if(!c.positive){unknown++;continue;}if(c.positive[score]>threshold){rejected++;continue;}for(const t of c.twists)if(t){twistKnown++;if(t[score]>threshold)twistRejected++;}}
      return {id:f.id,total:f.connections.length,rejected,unknown,twistRejected,twistKnown};
    });
    const sum=key=>perFrame.reduce((s,f)=>s+f[key],0), preserved=perFrame.filter(f=>!f.rejected).length;
    const r={count,score,policy,threshold,trainingConnections:refs[0].length,preserved,configurations:test.length,total:sum('total'),rejected:sum('rejected'),unknown:sum('unknown'),twistRejected:sum('twistRejected'),twistKnown:sum('twistKnown'),worstRetention:Math.min(...perFrame.map(f=>1-f.rejected/f.total)),perFrame};
    r.promotion=preserved>=11&&r.twistKnown>0&&r.twistRejected/r.twistKnown>=.1&&r.unknown===0;
    results.push(r);
  }
  console.error(`Completed ${count} training configurations`);
}
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const result={schema:'configuration-safety/1',protocol:'EXPERIMENT-PROTOCOL.md',dataset:{url:'https://github.com/lamrosset/aSi-data/blob/main/data/xyz/216-atoms.xyz',doi:'10.5281/zenodo.14203730',license:'CC BY 4.0',sha256:hash(raw)},runnerSha256:hash(fs.readFileSync(fileURLToPath(import.meta.url))),split,seed:1709,shuffle:'Fisher-Yates; uint32 LCG 1664525*x+1013904223',elapsedMs:performance.now()-started,results,rawScores};
fs.writeFileSync(process.argv[3],JSON.stringify(result)+'\n');
console.table(results.map(r=>({train:r.count,score:r.score,cutoff:r.policy,preserved:`${r.preserved}/12`,retention:(100*(1-r.rejected/r.total)).toFixed(2),twistRejection:(100*r.twistRejected/r.twistKnown).toFixed(2),promote:r.promotion})));
