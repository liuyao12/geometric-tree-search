import assert from 'node:assert/strict';
import fs from 'node:fs';
import {latticeToCartesian,relativeTile,reflectedFrameStats,steadyFrame,projectVertex,HALFROOT3} from './projection.js';
import {originFromMarks,WHITE_PLANE_MATRIX} from './vertex-distance.js';
const COORDINATE_ORIGIN=originFromMarks(JSON.parse(fs.readFileSync(new URL('fixed-marks.json',import.meta.url))));
const shiftedTile=(vertices,ids)=>ids.map(i=>vertices[i].map((x,k)=>x-COORDINATE_ORIGIN[k]));
const data=JSON.parse(fs.readFileSync(new URL('patch.json',import.meta.url)));
const model=data.vertices.map(latticeToCartesian);
const mean=[0,0,0,0];for(const p of model)for(let k=0;k<4;k++)mean[k]+=p[k]/model.length;
for(const p of model)for(let k=0;k<4;k++)p[k]-=mean[k];
const centers=new Float64Array(data.tiles.length*4);
for(let i=0;i<data.tiles.length;i++)for(const id of data.tiles[i])for(let k=0;k<4;k++)centers[4*i+k]+=model[id][k]/14;
const stats=reflectedFrameStats(centers,data.labels),results=[];
for(const fraction of [0,.25,.5,.75,1]){
 const angle=Math.PI/3-fraction*Math.PI/6,c=Math.cos(angle),s=Math.sin(angle),frame=steadyFrame(stats,c,s);
 let residual=0,raw=0;
 for(let i=0;i<data.tiles.length;i++){
  if(data.labels[i]!=='H1')continue;
  const p=centers.subarray(4*i,4*i+4),hat=projectVertex(...p,.5,HALFROOT3,false),steady=projectVertex(...p,c,s,false,frame),unsteady=projectVertex(...p,c,s,false);
  residual+=(steady[0]-hat[0])**2+(steady[1]-hat[1])**2;
  raw+=(unsteady[0]-hat[0])**2+(unsteady[1]-hat[1])**2;
 }
 const rms=Math.sqrt(residual/stats.count);
 assert.ok(Math.abs(rms-frame.rms)<2e-5);
 assert.ok(residual<=raw+1e-7,'Stabilization must improve the full reflected layout');
 assert.ok(frame.scale>0,'Camera cannot reflect or collapse the tiling');
 // A single similarity must preserve all edge-length ratios.
 for(const id of [0,100,1000]){
  const poly=data.tiles[id],p=model[poly[0]],q=model[poly[1]];
  const a=projectVertex(...p,c,s,false),b=projectVertex(...q,c,s,false),x=projectVertex(...p,c,s,false,frame),y=projectVertex(...q,c,s,false,frame);
  assert.ok(Math.abs(Math.hypot(x[0]-y[0],x[1]-y[1])/Math.hypot(a[0]-b[0],a[1]-b[1])-frame.scale)<1e-10);
 }
 results.push({fraction,rotationDegrees:Math.atan2(frame.im,frame.re)*180/Math.PI,scale:frame.scale,rmsLocalDrift:rms,uncorrectedRmsDrift:Math.sqrt(raw/stats.count)});
}
for(const ids of data.tiles){
 const relative=relativeTile(data.vertices,ids),origin=model[ids[0]],shifted=shiftedTile(data.vertices,ids);
 for(let i=0;i<14;i++)for(let k=0;k<4;k++){assert.ok(Math.abs(shifted[i][k]+COORDINATE_ORIGIN[k]-data.vertices[ids[i]][k])<1e-11);assert.ok(Math.abs(shifted[i][k]-shifted[0][k]-relative[i][k])<1e-11);}
 assert.deepEqual(relative[0],[0,0,0,0]);
 assert.equal(new Set(relative.map(p=>p.join(','))).size,14);
 for(let i=0;i<14;i++){
  assert.ok(relative[i].every(Number.isInteger));
  const p=latticeToCartesian(relative[i]);
  for(let k=0;k<4;k++)assert.ok(Math.abs(p[k]-(model[ids[i]][k]-origin[k]))<1e-10);
 }
}
// An exact rank witness using translations between identically oriented reflected
// tiles: these differences are independent of a COMMON local reference point.
// Different local points in different copies are not covered by this witness.
function rank(rows){const a=rows.map(r=>r.slice());let rank=0;for(let k=0;k<4&&rank<a.length;k++){let p=rank;while(p<a.length&&Math.abs(a[p][k])<1e-8)p++;if(p===a.length)continue;[a[p],a[rank]]=[a[rank],a[p]];const x=a[rank][k];for(let j=k;j<4;j++)a[rank][j]/=x;for(let i=0;i<a.length;i++)if(i!==rank){const x=a[i][k];for(let j=k;j<4;j++)a[i][j]-=x*a[rank][j];}rank++;}return rank;}
function determinant(rows){let a=rows.map(r=>r.map(BigInt)),sign=1n,previous=1n;for(let k=0;k<3;k++){let p=k;while(p<4&&a[p][k]===0n)p++;assert.ok(p<4);if(p!==k){[a[p],a[k]]=[a[k],a[p]];sign=-sign;}const pivot=a[k][k];for(let i=k+1;i<4;i++)for(let j=k+1;j<4;j++)a[i][j]=(a[i][j]*pivot-a[i][k]*a[k][j])/previous;for(let i=k+1;i<4;i++)a[i][k]=0n;previous=pivot;}return sign*a[3][3];}
const reflected=data.labels.map((label,i)=>label==='H1'?i:-1).filter(i=>i>=0),first=data.tiles[reflected[0]],origin=data.vertices[first[0]];
const orientation=data.vertices[first[1]].map((x,k)=>x-origin[k]);const witness=[];
for(const i of reflected){const ids=data.tiles[i],p=data.vertices[ids[0]],edge=data.vertices[ids[1]].map((x,k)=>x-p[k]);if(edge.some((x,k)=>x!==orientation[k]))continue;const delta=p.map((x,k)=>x-origin[k]);if(rank([...witness,delta])>witness.length)witness.push(delta);if(witness.length===4)break;}
assert.equal(witness.length,4);const det=determinant(witness);assert.notEqual(det,0n);
const report={sameOrientationTranslations:{rank:4,integerWitness:witness,determinant:det.toString()},reflectedTiles:stats.count,coordinateLabelsChecked:14*data.tiles.length,coordinateFrame:'Translated coordinates with the central white mark at the origin',coordinateOrigin:[0,0,0,0],whitePlaneMatrix:WHITE_PLANE_MATRIX,uniformCamera:true,samples:results};
fs.writeFileSync(new URL('view-validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
