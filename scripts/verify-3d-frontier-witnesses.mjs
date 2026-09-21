import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {verifyCorona} from '../apps/3d-lattice-tiler/corona-graph.js';
import {verifyPointWindowFrontier} from './lib/verify-point-window-frontier.mjs';
import {prepareVoxelPointModel,verifyVoxelPatch} from '../apps/3d-lattice-tiler/voxel-point-model.js';
const bundle=JSON.parse(await readFile(new URL('../data/3d-viable-frontier-witnesses-2026-09-21.json',import.meta.url)));
for(const c of bundle.cases){
 const model={...bundle.models[c.input.model],...c.input.target},fixed=c.input.fixed;
 assert.equal(model.capacity,8);assert.deepEqual(model.placementDomain,{kind:'scaled_cubic',translationStep:2});assert.equal(model.allowReflections,false);
 const rebuilt=prepareVoxelPointModel(model.orientations[0].voxels,{radius:0});
 const geometry=m=>m.orientations.map(o=>({voxels:o.voxels,cells:o.cells}));assert.deepEqual(geometry(model),geometry(rebuilt));
 const point=c.input.pair?verifyCorona(model,c.input.pair,c.placements):verifyPointWindowFrontier(model,c.placements,fixed),voxel=verifyVoxelPatch(model,c.placements,{requireTarget:false});assert.ok(point.complete&&voxel.ok);
 console.log(JSON.stringify({tile:c.tile,target:c.target,tiles:c.placements.length,required:point.required,frontierPoints:point.frontierPoints,deadPoints:point.deadPoints.length,verified:true}));
}
