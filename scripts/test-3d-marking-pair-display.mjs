import assert from 'node:assert/strict';
import {inspectPairMarking,pairInspectionText} from '../apps/3d-lattice-tiler/marking-pair-display.js';
import {learnMarking,pairCompatible} from '../apps/3d-lattice-tiler/marking-learning.js';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
const pair=[{oi:0,translation:[3,2,1]},{oi:1,translation:[2,2,1]}];
const fields=[[{pos:[0,0,0],value:[0,'*',3]}],[{pos:[1,0,0],value:[0,9,4]}]];
const view=inspectPairMarking(fields,pair);
assert.equal(view.points.length,3);assert.equal(view.overlaps.length,2);assert.equal(view.conflicts.length,1);
assert.deepEqual(view.conflicts[0].pos,[3,2,1]);assert.equal(view.conflicts[0].component,2);
assert.deepEqual(view.conflicts[0].assignments,[{tile:0,value:3},{tile:1,value:4}]);
assert.equal(view.compatible,false);
assert.match(pairInspectionText({status:'invalid',nodes:15,backtracks:4},view),/rejects this pair \(correct\)/);
assert.match(pairInspectionText({status:'valid'},view),/rejects this pair \(mismatch\)/);
assert.match(pairInspectionText({status:'unresolved',reason:'attempt budget'},view),/Unresolved: attempt budget.*not a validity label/);
assert.doesNotMatch(pairInspectionText({status:'valid'},view),/0 attempts/);
assert.equal(inspectPairMarking([[{pos:[0,0,0],value:0}],[{pos:[1,0,0],value:0}]],pair).compatible,true);
assert.equal(inspectPairMarking([[{pos:[0,0,0],value:null}],[]],pair).points.length,0);
// Compare the independent display reconstruction against the production matcher
// for every positive and negative in a genuine, freshly learned field.
let marking;for await(const e of learnMarking(prepareModel({tile:'a2_turtle_prism',radius:1,mirrors:true}),{timeMs:30000}))if(e.marking)marking=e.marking;
assert.ok(marking.accepted);
let rejected=0;for(const row of marking.evidence){const inspection=inspectPairMarking(marking.fields,row.pair);assert.equal(inspection.compatible,pairCompatible(marking.fields,row.pair));if(!inspection.compatible)rejected++;}
assert.equal(rejected,marking.negativeBlocked);
console.log(`PASS component *, zero, translated conflicts, truthful labels, and ${marking.evidence.length} Turtle pair decisions (${rejected} rejected).`);
