import assert from 'node:assert/strict';
import fs from 'node:fs';
import {latticeToCartesian,fixedMarkFrame,projectVertex,HALFROOT3} from './projection.js';
const read=name=>JSON.parse(fs.readFileSync(new URL(name,import.meta.url)));
const patch=read('patch.json'),marks=read('fixed-marks.json');
const reflected=patch.labels.flatMap((label,i)=>label==='H1'?[i]:[]);
assert.deepEqual(marks.anchors.map(a=>a.tile),reflected);
const model=patch.vertices.map(latticeToCartesian),mean=[0,0,0,0];
for(const p of model)for(let k=0;k<4;k++)mean[k]+=p[k]/model.length;
let maxDrift=0,maxBarycentricError=0,minWeight=1;
for(const anchor of marks.anchors){
 assert.equal(anchor.triangle.length,3);
 assert.ok(Math.abs(anchor.weights.reduce((a,b)=>a+b,0)-1)<1e-12);
 minWeight=Math.min(minWeight,...anchor.weights);assert.ok(minWeight>0);
 for(let k=0;k<4;k++){
  const expected=anchor.weights.reduce((sum,w,j)=>sum+w*patch.vertices[patch.tiles[anchor.tile][anchor.triangle[j]]][k],0);
  maxBarycentricError=Math.max(maxBarycentricError,Math.abs(expected-anchor.coordinates[k]));
 }
 for(const offset of [[0,0,0,0],mean]){
  const p=latticeToCartesian(anchor.coordinates).map((v,k)=>v-offset[k]);
  const hat=projectVertex(...p,.5,HALFROOT3,false);
  for(let j=0;j<=100;j++){
   const angle=j/100*Math.PI/2,c=Math.cos(angle),s=Math.sin(angle),frame=fixedMarkFrame(c,s,offset);
   assert.ok(frame.scale>0);
   const actual=projectVertex(...p,c,s,false,frame);
   maxDrift=Math.max(maxDrift,Math.hypot(actual[0]-hat[0],actual[1]-hat[1]));
  }
 }
}
assert.ok(maxDrift<1e-10);assert.ok(maxBarycentricError<1e-10);
const report={reflectedTiles:reflected.length,parameterSamples:101,coordinateFrames:['raw','mean-centered'],maxDrift,maxBarycentricError,minWeight,scope:'Full-family stationarity check. Interior-point certificate is restricted to the Hat–Turtle interval; marks are hidden outside it.'};
fs.writeFileSync(new URL('fixed-marks-validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
