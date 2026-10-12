import {readFileSync,writeFileSync} from 'node:fs';
import {classifyLattice} from '../research/knot-classifier/lattice-search.mjs';
const args=process.argv.slice(2),get=key=>args.find(x=>x.startsWith(`--${key}=`))?.split('=').slice(1).join('=');
if(!get('input')||!get('references'))throw Error('Use --input=<JSON loop or {vertices}> --references=<JSON records or {records}> [--bounds=<JSON>] [--comparison-cap=1] [--output=<JSON>]');
const input=JSON.parse(readFileSync(get('input'))),data=JSON.parse(readFileSync(get('references'))),references=Array.isArray(data)?data:data.records;
const bounds=get('bounds')?JSON.parse(readFileSync(get('bounds'))):{};
const result=classifyLattice(input,references,{...bounds,comparisonCap:Number(get('comparison-cap')||references.length)});
if(get('output'))writeFileSync(get('output'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({status:result.status,label:result.label,reason:result.reason,comparisons:result.attempts.length}));
