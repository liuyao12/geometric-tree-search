import assert from 'node:assert/strict';
import fs from 'node:fs';
import {prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {verifyCorona} from '../apps/3d-lattice-tiler/corona-graph.js';
import {compileCertifiedPairs} from '../apps/3d-lattice-tiler/certified-marking.js';
const read=name=>JSON.parse(fs.readFileSync(new URL(`../data/nonacube-pair-obstruction/${name}.json`,import.meta.url)));
const data=read('problem'),positive=read('one-corona'),receipt=read('receipt');
const model=prepareModel({tile:'nonacube_cross',mirrors:false,radius:1});
assert.deepEqual(data.model.orientations,model.orientations);
assert.deepEqual(data.model.placementDomain,model.placementDomain);
assert.equal(data.model.capacity,model.capacity);
assert.deepEqual(data.fixed,[{oi:0,translation:[0,0,0]},{oi:0,translation:[0,6,-4]}]);
assert.equal(positive.placements.length,44);
assert(verifyCorona(model,data.fixed,positive.placements).complete);
// This audits compilation only; run the Python verifier to certify the premise.
const marking=compileCertifiedPairs(model,[{pair:data.fixed,status:'invalid',certificate:{kind:'finite_window_rup'}}]);
assert.equal(marking.componentCount,receipt.markingCompilation.components);
assert.equal(marking.values,48);
console.log('Current point model matches proof input; 44-tile one-corona independently valid; exclusion compiles to 24 audited components. Replay UNSAT with the Python verifier.');
