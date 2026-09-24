import assert from 'node:assert/strict';
import fs from 'node:fs';
import {NONACUBE_CROSS as tile} from '../apps/3d-lattice-tiler/nonacube-cross.js';
import {catalog,prepareModel} from '../apps/3d-lattice-tiler/v2/model.js';
import {tileSpecs,preprocessTilingSystem} from '../apps/3d-lattice-tiler/engine.js';
const key=p=>p.join(','),canonical=cells=>{const min=[0,1,2].map(a=>Math.min(...cells.map(p=>p[a])));return cells.map(p=>key(p.map((x,a)=>x-min[a]))).sort().join(';');};
// Independent description of the three planar orientations, not the app's rotation code.
const shapes=[[0,1],[0,2],[1,2]].map(axes=>[[0,0,0],...axes.flatMap(a=>[-2,-1,1,2].map(d=>[0,1,2].map(k=>k===a?d:0)))]);
const signatures=new Set(shapes.map(canonical));
const witness=JSON.parse(fs.readFileSync(new URL('../data/nonacube-cross-corona.json',import.meta.url)));
assert.equal(canonical(witness.root),canonical(tile.voxels));assert.equal(tile.voxels.length,9);
const root=new Set(witness.root.map(key)),required=new Set();
for(const p of witness.root)for(const x of [-1,0,1])for(const y of [-1,0,1])for(const z of [-1,0,1]){const k=key([p[0]+x,p[1]+y,p[2]+z]);if(!root.has(k))required.add(k);}
assert.equal(required.size,90);assert.deepEqual(new Set(witness.target.map(key)),required);
const occupied=new Set(root);
for(const cells of witness.corona){assert.equal(cells.length,9);assert.equal(new Set(cells.map(key)).size,9);assert(signatures.has(canonical(cells)),'congruent cross');assert(cells.some(p=>required.has(key(p))),'touches central tile');for(const p of cells){assert(!occupied.has(key(p)),'no overlaps');occupied.add(key(p));}}
for(const p of required)assert(occupied.has(p),'full vertex-contact neighborhood covered');
assert.equal(catalog().filter(c=>c.id===tile.id).length,1);
for(const mirrors of [false,true]){const m=prepareModel({tile:tile.id,mirrors,radius:1});assert.equal(m.orientations.length,3);assert.equal(m.placementDomain.translationStep,2);assert.equal(m.capacity,8);for(const o of m.orientations){assert(signatures.has(canonical(o.voxels)));assert.equal(o.cells.filter(p=>p.pos.every(x=>Math.abs(x%2)===1)&&p.weight===8).length,9);}}
assert(tileSpecs.TILING_REGISTRY[tile.id]);
const legacy=preprocessTilingSystem({mode_key:tile.id,include_mirrors:false,polycube_lattice:'z3'},tileSpecs);assert.equal(legacy.prototiles.length,1);
console.log(`Verified nonacube catalogue/model integration and complete corona: ${witness.corona.length} tiles, ${required.size} surrounding cells, no overlaps; H >= 1 only.`);
