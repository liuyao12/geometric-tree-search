import {readFileSync,writeFileSync} from 'node:fs';
import {performance} from 'node:perf_hooks';
import {blindPenroseProblem} from './penrose-blind-problem.mjs';
import {knownPenroseBenchmark} from './penrose-known-benchmark.mjs';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
const trained=JSON.parse(readFileSync(process.env.MODEL||'/tmp/cyclotomic-validation.json','utf8'));
const targetCorona=Number(process.env.CORONA||3),nodeLimit=Number(process.env.NODES||2000),seed=Number(process.env.SEED||5),results=[];
for(const mode of (process.env.MODES||'frozen,plain,known').split(',')){
 const start=performance.now(),problem=blindPenroseProblem(),adapter=mode==='known'?knownPenroseBenchmark(problem):{problem};
 const search=createObstructionSearch({...adapter,seed,targetCorona,nodeLimit,learn:mode==='frozen',train:false,initialCertificates:mode==='frozen'?trained.certificates:[]});
 while(!search.next().done){}
 const s=search.snapshot(),r={mode,seed,ms:performance.now()-start,status:s.status,tiles:s.tiles.length,corona:s.minimumFrontierGeneration,...s.stats,rules:s.learning?.rules||0,addresses:s.learning?.addresses||0};results.push(r);console.log(JSON.stringify(r));
}
writeFileSync(process.env.OUTPUT||'/tmp/cyclotomic-corona.json',JSON.stringify({targetCorona,nodeLimit,results},null,2)+'\n');
