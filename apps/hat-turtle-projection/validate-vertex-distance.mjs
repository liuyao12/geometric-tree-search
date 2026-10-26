import assert from 'node:assert/strict';
import fs from 'node:fs';
import {WHITE_PLANE_MATRIX as A,WHITE_PLANE_OFFSET,COORDINATE_ORIGIN,ORIGIN_TILE,planeManhattanDistance,distanceColor,originPlaneFrame} from './vertex-distance.js';
import {latticeToCartesian,fixedMarkFrame,projectVertex} from './projection.js';
const option=(flag,fallback)=>{const i=process.argv.indexOf(flag);return i<0?new URL(fallback,import.meta.url):process.argv[i+1];};
const data=JSON.parse(fs.readFileSync(option('--patch','patch.json')));
const marks=JSON.parse(fs.readFileSync(option('--marks','fixed-marks.json')));
const origin=COORDINATE_ORIGIN,shift=p=>p.map((v,k)=>v-origin[k]),dot=(a,b)=>a.reduce((s,v,k)=>s+v*b[k],0);
assert.ok(origin.every(Number.isInteger));
for(let k=0;k<2;k++)assert.ok(Math.abs(WHITE_PLANE_OFFSET[k]-([4,14][k]-dot(A[k],origin)))<1e-11);
const shifted=data.vertices.map(shift),distances=shifted.map(planeManhattanDistance);
// Independent dual problem: maximize (Ax-b).z subject to |A_column.z| <= 1.
const dual=[];
for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)for(const s of [-1,1])for(const t of [-1,1]){
 const d=A[0][i]*A[1][j]-A[1][i]*A[0][j];if(Math.abs(d)<1e-12)continue;
 const z=[(s*A[1][j]-t*A[1][i])/d,(A[0][i]*t-A[0][j]*s)/d];
 if([0,1,2,3].every(k=>Math.abs(A[0][k]*z[0]+A[1][k]*z[1])<=1+1e-12))dual.push(z);
}
let maxDualError=0,maxDistanceChange=0;
for(let i=0;i<shifted.length;i++){
 const x=shifted[i],b=A.map((row,k)=>dot(row,x)-WHITE_PLANE_OFFSET[k]),expected=Math.max(...dual.map(z=>dot(b,z)));
 const originalDefect=A.map((row,k)=>dot(row,data.vertices[i])-[4,14][k]),originalDistance=Math.max(...dual.map(z=>dot(originalDefect,z)));
 maxDualError=Math.max(maxDualError,Math.abs(expected-distances[i]));
 maxDistanceChange=Math.max(maxDistanceChange,Math.abs(originalDistance-distances[i]));
 assert.ok(Math.abs(expected-distances[i])<1e-10,'Primal and dual distances must agree for every vertex');
 assert.ok(x.every(Number.isInteger),'Every displayed vertex tuple must be integral');
 assert.deepEqual(x.map((v,k)=>v+origin[k]),data.vertices[i]);
}
assert.ok(maxDistanceChange<1e-10,'An origin translation must preserve all physical plane distances');
const translatedMarks=marks.anchors.map(a=>shift(a.coordinates));
const maxMarkDefect=Math.max(...translatedMarks.flatMap(p=>A.map((a,k)=>Math.abs(dot(a,p)-WHITE_PLANE_OFFSET[k]))));
assert.ok(maxMarkDefect<1e-10);assert.deepEqual(shift(origin),[0,0,0,0]);
const cart=shifted.map(latticeToCartesian),mean=[0,0,0,0];
for(const p of cart)for(let k=0;k<4;k++)mean[k]+=p[k]/cart.length;
const oldOrigin=latticeToCartesian(origin),oldMean=mean.map((v,k)=>v+oldOrigin[k]);
let maxStationarityError=0,maxCameraChange=0;
for(let sample=0;sample<=100;sample++){
 const theta=sample*Math.PI/200,c=Math.cos(theta),s=Math.sin(theta),frame=originPlaneFrame(c,s,mean),oldFrame=fixedMarkFrame(c,s,oldMean);
 for(const p of translatedMarks.map(latticeToCartesian)){
  const centered=p.map((v,k)=>v-mean[k]),hat=projectVertex(...centered,.5,Math.sqrt(3)/2,false),now=projectVertex(...centered,c,s,false,frame),old=projectVertex(...centered,c,s,false,oldFrame);
  maxStationarityError=Math.max(maxStationarityError,Math.hypot(now[0]-hat[0],now[1]-hat[1]));
  maxCameraChange=Math.max(maxCameraChange,Math.hypot(now[0]-old[0],now[1]-old[1]));
 }
}
assert.ok(maxStationarityError<1e-9);assert.ok(maxCameraChange<1e-9);
assert.equal(distanceColor(0),'rgb(35,77,176)');assert.equal(distanceColor(5),'rgb(181,43,67)');
const maximum=Math.max(...distances),maxId=distances.indexOf(maximum),selected=data.tiles[ORIGIN_TILE].map(i=>shifted[i]);
assert.equal(data.vertices.length,49246);assert.ok(Math.abs(maximum-4.64793068843926)<1e-10);
const report={coordinateFrame:'One shared integer lattice origin in the original triangular coefficient units',originNearTile:ORIGIN_TILE,sourceCoordinateOrigin:origin,originCoordinates:[0,0,0,0],integerVerticesChecked:shifted.length,planeMatrix:[['-2','-1-sqrt(5)','4','0'],['2*sqrt(5)','sqrt(5)-3','4','8']],affinePlaneOffset:['-119+53*sqrt(5)','217-97*sqrt(5)'],vertices:distances.length,whiteMarks:translatedMarks.length,minimum:Math.min(...distances),maximum,maximumVertex:shifted[maxId],withinDistanceTwo:distances.filter(d=>d<=2+1e-10).length,centralTileCoordinateRange:[Math.min(...selected.flat()),Math.max(...selected.flat())],maxDualError,maxDistanceChange,maxMarkDefect,maxStationarityError,maxCameraChange,fullFamilySamples:101,scope:'Every displayed vertex tuple is checked exactly integral. Plane distance and camera checks use floating-point arithmetic for the finite substitution patch; the actual white-dot plane is affine and unchanged geometrically. No distance cutoff is applied to vertex rendering.'};
fs.writeFileSync(option('--output','vertex-distance-validation.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
