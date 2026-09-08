import assert from 'node:assert/strict';
import * as old from './fixtures/cyclotomic-bigint-reference.mjs';
import * as fresh from '../assets/cyclotomic-five.js';
let seed=1;const rand=()=>((seed=Math.imul(seed,1664525)+1013904223>>>0)/2**32);
function result(fn,args){try{return fn(...args);}catch(e){return {error:e.name,message:e.message};}}
for(let i=0;i<20000;i++){
 const magnitude=[5,100,10**6,10**9,Number.MAX_SAFE_INTEGER][i%5];
 const point=()=>({coeff:Array.from({length:i%2?4:5},()=>Math.trunc((rand()*2-1)*magnitude)),denominator:[1,2,3,100,1000000][i%5]});const a=point(),b=point();
 for(const [fn,args] of [['canonical',[a]],['cycloAdd',[a,b]],['cycloMultiply',[a,b]]])assert.deepEqual(result(fresh[fn],args),result(old[fn],args),fn+':'+JSON.stringify(args));
}
console.log('60,000 exact arithmetic comparisons match the original BigInt implementation, including overflow behavior');
