import assert from 'node:assert/strict';
import {createSearchStatus,activityText} from '../apps/penrose-model-set/search-status.js';
const s=createSearchStatus(),coordinate=k=>k;
s.accept({type:'add'});assert.equal(activityText(s.snapshot(),coordinate),'ready');
for(let i=1;i<=5;i++){
 s.accept({type:'try',forced:true,branchCount:1});
 s.accept({type:'add',forced:true,branchCount:1});
 assert.equal(s.snapshot().count,i);
}
assert.equal(activityText(s.snapshot(),coordinate),'5 forced moves');
s.accept({type:'try',forced:true});assert.equal(s.snapshot().count,5);
s.accept({type:'try',branchCount:3,frontier:'1,2,3,4/1'});
assert.equal(activityText(s.snapshot(),coordinate),'3-way branching at [1,2,3,4/1]');
s.accept({type:'add',forced:true});assert.equal(activityText(s.snapshot(),coordinate),'1 forced move');
s.accept({type:'remove'});assert.equal(activityText(s.snapshot(),coordinate),'backtracking');
s.accept({type:'add',forced:true});assert.equal(s.snapshot().count,1);
s.accept({type:'dead',frontier:'0,0,0,0/1'});assert.match(activityText(s.snapshot(),coordinate),/^dead end at/);
assert.equal(activityText(createSearchStatus().snapshot(),coordinate),'ready');
console.log('ok: all batched events counted, trials not double-counted, branch/dead/backtrack/reset status');
