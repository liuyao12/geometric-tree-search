import assert from 'node:assert/strict';
import fs from 'node:fs';
import {latticeToCartesian} from './projection.js';
import {FAMILY_STOPS,familyAngle,coefficients,projectPerspective,alignedPerspective,latticeBasis,alignmentSamples,certifiedMarks} from './perspectives.js';
import {matrixPerspective,scalar} from './matrix-perspectives.js';
const patch=JSON.parse(fs.readFileSync(new URL('patch.json',import.meta.url))),report={checks:[],familySamples:[],alignedExamples:0,matrixCharts:0};
const points=patch.vertices.map(latticeToCartesian),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const close=(a,b,eps=1e-9)=>assert.ok(Math.abs(a-b)<eps,`${a} != ${b}`);
close(familyAngle(FAMILY_STOPS.hat),Math.PI/3);close(familyAngle(FAMILY_STOPS.turtle),Math.PI/6);assert.equal(coefficients(0).u,0);assert.equal(coefficients(1).vr,0);assert.ok(certifiedMarks(1/3)&&certifiedMarks(2/3)&&!certifiedMarks(.05));
for(const m of [0,.01,1/6,1/3,.5,2/3,5/6,.99,1]){
 const w=coefficients(m),areas=[],counts=new Set();
 const projected=points.map(p=>projectPerspective(...p,w));
 for(const ids of patch.tiles){const ps=ids.map(i=>projected[i]),area=Math.abs(ps.reduce((a,p,j)=>a+p[0]*ps[(j+1)%14][1]-p[1]*ps[(j+1)%14][0],0)/2);areas.push(area);if(m===0||m===1)counts.add(new Set(ps.map(p=>p.slice(0,2).map(x=>Math.round(x*1e8)).join(','))).size);}
 assert.ok(Math.min(...areas)>1e-6);assert.ok(Math.max(...areas)-Math.min(...areas)<1e-7);
 report.familySamples.push({fraction:m,angleDegrees:familyAngle(m)*180/Math.PI,tileArea:areas[0],limitingVertexCounts:[...counts]});
}
report.checks.push('Full interval including both limiting shapes has positive congruent tile areas; hat/turtle stop positions and zero coefficients are correct');
function inLattice(p,basis){const [a,b]=basis,det=a[0]*b[1]-a[1]*b[0];const x=(p[0]*b[1]-p[1]*b[0])/det,y=(a[0]*p[1]-a[1]*p[0])/det;close(x,Math.round(x),2e-8);close(y,Math.round(y),2e-8);}
for(const exact of [{xn:3,yn:0,q:1},{xn:1,yn:0,q:1},{xn:2,yn:1,q:1},{xn:-1,yn:1,q:1},{xn:1,yn:-2,q:3},{xn:0,yn:1,q:2}]){
 const p=alignedPerspective(exact.xn,exact.yn,exact.q),w=coefficients(p.m,p.phi,p.exact),b=latticeBasis(p.m,p.phi,p.exact);
 close(w.u*w.u+w.vr*w.vr+w.vi*w.vi,1);for(const q of [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1],...patch.vertices.slice(0,100)])inLattice(projectPerspective(...latticeToCartesian(q),w),b);report.alignedExamples++;
}
assert.equal(latticeBasis(.5,0,null),null);assert.ok(alignmentSamples().length>100);report.checks.push('Exact rational alignment examples map all four lattice generators and sample vertices into the computed image lattice');
const projector=rows=>Array.from({length:4},(_,i)=>Array.from({length:4},(_,j)=>rows.reduce((s,r)=>s+r[i]*r[j],0)));
for(const [xn,yn,q] of [[1,0,1],[3,0,1],[2,1,1],[-1,1,2]]){
 const a=alignedPerspective(xn,yn,q),w=coefficients(a.m,a.phi,a.exact),rows=[[w.u,0,w.vr,-w.vi],[0,w.u,w.vi,w.vr]],A=xn-3*yn,B=xn+3*yn,D=3*q;
 const matrix=matrixPerspective([`${A}/${D}`,`${-B}/${D}`,`${B}/${D}`,`${A+B}/${D}`]);
 const one=projector(rows),two=projector(matrix.rows);for(let i=0;i<4;i++)for(let j=0;j<4;j++)close(one[i][j],two[i][j]);
}
report.checks.push('The two-parameter family is exactly a slice of the general four-parameter plane charts, up to screen rotation');
for(const pivots of [[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]){
 const m=matrixPerspective(['1/3','-2','0.125','3/2'],pivots);close(dot(m.rows[0],m.rows[0]),1);close(dot(m.rows[1],m.rows[1]),1);close(dot(m.rows[0],m.rows[1]),0);assert.ok(m.rankTwo);
 for(const q of [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1],...patch.vertices.slice(0,80)]){const p=latticeToCartesian(q);inLattice(m.rows.map(r=>dot(r,p)),m.basis);}report.matrixCharts++;
}
const irrational=matrixPerspective(['sqrt(2)','0','0','1']);assert.equal(irrational.basis,null);assert.equal(irrational.rankTwo,false);close(dot(irrational.rows[0],irrational.rows[1]),0);assert.throws(()=>scalar('1/0'));assert.throws(()=>scalar('alert(1)'));
report.checks.push('All six charts use orthonormal screen rows, exact rational HNF lattice bases, and distinguish an explicitly irrational example');
report.scope='Finite numerical rendering and lattice-basis checks. The commensurability criterion and six-chart completeness are derived in README.md. Free floating-point views are not classified as exact alignments.';
fs.writeFileSync(new URL('perspectives-validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
