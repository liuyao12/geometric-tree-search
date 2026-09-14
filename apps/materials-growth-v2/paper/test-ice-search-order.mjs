import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const {PointSearch}=await import(pathToFileURL(process.argv[2]).href);
const c=(id,p)=>({id,t:[{point:p,value:1}]});
const dead=new PointSearch({required:['a','b'],candidates:[c('only','a')]});assert.equal(dead.decision().kind,'dead');
const forced=new PointSearch({required:['a','b'],candidates:[c('a1','a'),c('a2','a'),c('b1','b')]});assert.equal(forced.decision().kind,'forced');assert.equal(forced.decision().point,'b');
const generation=new PointSearch({required:['a','b'],candidates:[c('a1','a'),c('a2','a'),c('a3','a'),c('b1','b'),c('b2','b')]});
// Synthetic scheduler state: later generation has fewer candidates.
generation.points.get('b').generation=5;assert.equal(generation.decision().point,'a');
const before=JSON.stringify(generation.semanticState());generation.apply('a1');generation.undo(0);assert.equal(JSON.stringify(generation.semanticState()),before);generation.auditGraph();
console.log('Dead-before-forced, forced-before-branch, generation-before-degree, and rollback controls pass.');
