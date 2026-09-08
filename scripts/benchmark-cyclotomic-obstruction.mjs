import {knownPenroseBenchmark} from './penrose-known-benchmark.mjs';
import {performance} from 'node:perf_hooks';
import {writeFileSync} from 'node:fs';
import {blindPenroseProblem} from './penrose-blind-problem.mjs';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
const problem=blindPenroseProblem(),targetCount=Number(process.env.TARGET||18),nodeLimit=Number(process.env.NODES||2000),seeds=(process.env.SEEDS||'1,17').split(',').map(Number),results=[];
for(const seed of seeds)for(const mode of(process.env.KNOWN?['plain','learned','known']:['plain','learned'])){
 const learn=mode==='learned',benchmark=mode==='known'?knownPenroseBenchmark(problem):{problem};
 const start=performance.now(),search=createObstructionSearch({...benchmark,learn,targetCount,nodeLimit,seed});let n=0;
 while(!search.next().done){if(++n>nodeLimit*4+100)throw Error('Unexpected event count');}
 const s=search.snapshot(),result={seed,mode,ms:performance.now()-start,status:s.status,tiles:s.tiles.length,corona:s.minimumFrontierGeneration,...s.stats,learning:s.learning?{...s.learning,tables:undefined}:null};results.push(result);console.log(JSON.stringify(result));
}
if(process.env.OUTPUT)writeFileSync(process.env.OUTPUT,JSON.stringify({targetCount,nodeLimit,slots:problem.movesAt({coeff:[0,0,0,0],denominator:1}).length,results},null,2)+'\n');
