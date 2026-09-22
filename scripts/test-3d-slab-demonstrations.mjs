import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {runExperiment} from '../apps/3d-lattice-tiler/v2/experiment.js';
import {DEMONSTRATIONS,demonstrationConfig} from '../apps/3d-lattice-tiler/v2/demonstrations.js';
for(const d of DEMONSTRATIONS){
 const config=demonstrationConfig(d.tile),model=prepareModel(config);
 assert.equal(model.required.length,2*(1+3*config.radius*(config.radius+1)));
 assert.ok(model.orientations.every(o=>o.marks.length===0),'Presets contain no learned assignments');
 const support=prepareModel({...config,radius:8});let result;
 for await(const e of runExperiment({...config,radius:8,mode:'gcts',timeMs:60000}))if(e.type==='result')result=e;
 assert.equal(result.result,'finite_exact');assert.equal(result.verification.ok,true);
 assert.equal(result.marking.extent,0);assert.equal(result.marking.positivePassed,result.marking.counts.valid);assert.equal(result.marking.negativeBlocked,result.marking.counts.invalid);
 result.marking.fields.forEach((field,oi)=>{const points=new Set(support.orientations[oi].cells.map(c=>c.pos.join()));assert.ok(field.every(m=>points.has(m.pos.join())));});
 console.log(d.tile,'PASS complete pair classification and independently verified larger marked slab');
}
assert.throws(()=>prepareModel({tile:'a2_turtle_prism',radius:19}),/radius/);
assert.throws(()=>prepareModel({tile:'cube',radius:4}),/radius/);

const measured=JSON.parse(await readFile(new URL('../apps/3d-lattice-tiler/v2/reference/showcase-summary.json',import.meta.url)));
for(const d of DEMONSTRATIONS){
 const preset=demonstrationConfig(d.tile);for(const key of ['radius','mirrors','timeMs','nodes','pairNodes','markingExtent'])assert.equal(preset[key],measured.protocol[key]);assert.ok(measured.protocol.seeds.includes(preset.seed));
 assert.ok(['gcts','both'].some(mode=>measured.protocol.seeds.every(seed=>{
  const find=m=>measured.rows.find(r=>r.tile===d.tile&&r.seed===seed&&r.mode===m),base=find('free'),marked=find(mode);
  const baseline=base.result==='finite_exact'?base.stats.totalMs:base.result==='unknown'&&base.reason==='time budget'&&base.stats.totalMs>=measured.protocol.timeMs?measured.protocol.timeMs:0;
  return marked.result==='finite_exact'&&marked.verification.ok&&marked.stats.totalMs*2<=baseline;
 })),`${d.tile} must satisfy the recorded inclusion rule`);
}
console.log('PASS every showcased tile has a cold marked completion and >=2x advantage on every recorded seed.');
