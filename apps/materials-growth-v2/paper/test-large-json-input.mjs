import assert from 'node:assert/strict';
import {parseLargeJSON} from './large-json-input.mjs';
const texts=['null','true','-1.3e20','"☃\\\"x"','[]','{}','{"__proto__":{"x":1},"a":2,"a":3}',
 JSON.stringify({clouds:Array.from({length:100},(_,i)=>({vectors:[[i,-i,1e-99]],colors:[['☃','escaped\\"']]})),models:[{a:[1,null,false,{x:'end'}]}]})];
for(const s of texts)for(const chunkBytes of [1,5,31,1024])assert.deepEqual(parseLargeJSON(Buffer.from(` \n${s}\t`),{chunkBytes}),JSON.parse(s));
for(const s of ['','{','[1,]','{"a":1,}','{"a" 1}','[1} x','{}{}','{"a":tru}','[1 2]','{"a":[1}}'])assert.throws(()=>parseLargeJSON(Buffer.from(s),{chunkBytes:1}));
console.log(JSON.stringify({boundedStringEquivalence:true,unicodeEscapes:true,duplicateAndPrototypeKeys:true,malformedRejected:true}));
