import {readFileSync,writeFileSync} from 'node:fs';
import {classifyLattice} from '../research/knot-classifier/lattice-search.mjs';
import {classifyLatticeBlind} from '../research/knot-classifier/lattice-blind-search.mjs';
import {classifyLatticeLazy} from '../research/knot-classifier/lattice-lazy-search.mjs';
const args=process.argv.slice(2),get=key=>args.find(x=>x.startsWith(`--${key}=`))?.split('=').slice(1).join('=');
if(!get('input')||!get('references'))throw Error('Use --input=<JSON loop or {vertices}> --references=<JSON records or {records}> [--bounds=<JSON>] [--engine=blind|lazy|eager] [--comparison-cap=1] [--output=<JSON>]');
const input=JSON.parse(readFileSync(get('input'))),data=JSON.parse(readFileSync(get('references'))),references=Array.isArray(data)?data:data.records;
const bounds=get('bounds')?JSON.parse(readFileSync(get('bounds'))):{};
if(bounds.maxDepth===undefined&&bounds.depth!==undefined)bounds.maxDepth=bounds.depth;
let result;
if(get('engine')==='blind'){
 const cap=Number(get('comparison-cap')||references.length);if(!Number.isInteger(cap)||cap<1)throw Error('Invalid comparison cap.');
 const bank=references.slice(0,cap);
 result=classifyLatticeBlind(input,bank.map(r=>Array.isArray(r)?r:r.vertices),bounds);
 result.label=result.certificate?(bank[result.referenceIndex].id??bank[result.referenceIndex].evaluatorKnot??null):null;
 result.bankSize=bank.length;result.fullSuppliedBank=bank.length===references.length;
}else{
 const classifier=get('engine')==='eager'?classifyLattice:classifyLatticeLazy;
 result=classifier(input,references,{iterativeDepth:true,extensionLearn:bounds.learn!==false,...bounds,comparisonCap:Number(get('comparison-cap')||references.length)});
}
if(get('output'))writeFileSync(get('output'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,label:result.label,reason:result.reason,comparisons:result.referenceChecks??result.attempts.length}));
