import assert from 'node:assert/strict';
import fs from 'node:fs';
import {latticeToCartesian,fixedMarkFrame,projectVertex,HALFROOT3} from './projection.js';
import {whiteMarkAlignment,rotateFrame} from './white-mark-alignment.js';
const read=name=>JSON.parse(fs.readFileSync(new URL(name,import.meta.url)));
const marks=read('fixed-marks.json'),patch=read('patch.json');
const points=marks.anchors.map(a=>latticeToCartesian(a.coordinates));
const hat=points.map(p=>projectVertex(...p,.5,HALFROOT3,false));
const rotation=whiteMarkAlignment(hat),rotated=hat.map(([x,y])=>[rotation.re*x-rotation.im*y,rotation.im*x+rotation.re*y]);
assert.equal(rotation.count,1009);
assert.ok(Math.abs(Math.hypot(rotation.re,rotation.im)-1)<1e-14);
assert.ok(Math.abs(whiteMarkAlignment(rotated).angle)<1e-12);
assert.equal(whiteMarkAlignment([]).angle,0);
assert.equal(whiteMarkAlignment([[0,0]]).angle,0);
const mean=[0,0,0,0];
for(const p of patch.vertices.map(latticeToCartesian))for(let k=0;k<4;k++)mean[k]+=p[k]/patch.vertices.length;
let maxDrift=0,maxLengthError=0;
for(const offset of [[0,0,0,0],mean])for(let j=0;j<=100;j++){
  const angle=j*Math.PI/200,c=Math.cos(angle),s=Math.sin(angle),raw=fixedMarkFrame(c,s,offset),frame=rotateFrame(raw,rotation);
  assert.equal(frame.scale,raw.scale);
  for(const point of points){
    const p=point.map((x,k)=>x-offset[k]);
    const target=projectVertex(...p,.5,HALFROOT3,false,rotateFrame(fixedMarkFrame(.5,HALFROOT3,offset),rotation));
    const actual=projectVertex(...p,c,s,false,frame);
    maxDrift=Math.max(maxDrift,Math.hypot(actual[0]-target[0],actual[1]-target[1]));
  }
  for(const id of [0,100,1000]){
    const ids=patch.tiles[id],p=latticeToCartesian(patch.vertices[ids[0]]),q=latticeToCartesian(patch.vertices[ids[1]]);
    const a=projectVertex(...p,c,s,false,raw),b=projectVertex(...q,c,s,false,raw),A=projectVertex(...p,c,s,false,frame),B=projectVertex(...q,c,s,false,frame);
    maxLengthError=Math.max(maxLengthError,Math.abs(Math.hypot(a[0]-b[0],a[1]-b[1])-Math.hypot(A[0]-B[0],A[1]-B[1])));
  }
}
assert.ok(maxDrift<1e-10);
assert.ok(maxLengthError<1e-10);
const report={marks:points.length,rotationDegrees:rotation.angle*180/Math.PI,sixfoldCoherence:rotation.coherence,residualAverageDirectionDegrees:whiteMarkAlignment(rotated).angle*180/Math.PI,parameterSamples:101,coordinateFrames:['raw','mean-centered'],maxDrift,maxLengthError,scope:'One global rotation aligns the average sixfold nearest-neighbor direction horizontally. It preserves the tiling and stationary material marks. It does not place the marks on an exact lattice; see white-lattice-validation.json.'};
fs.writeFileSync(new URL('white-alignment-validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
