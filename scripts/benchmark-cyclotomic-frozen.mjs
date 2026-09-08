import {performance} from 'node:perf_hooks';
import {writeFileSync} from 'node:fs';
import {blindPenroseProblem} from './penrose-blind-problem.mjs';
import {createObstructionSearch} from '../assets/cyclotomic-obstruction-search.js';
const trainSeeds=[1,17],testSeeds=[5,11,23,47],targetCount=30,nodeLimit=10000,certificates=[],results=[];
function run(seed,options){const start=performance.now(),search=createObstructionSearch({problem:blindPenroseProblem(),seed,targetCount,nodeLimit,...options});while(!search.next().done){}const s=search.snapshot();return{s,ms:performance.now()-start};}
let trainingMs=0;
for(const seed of trainSeeds){const {s,ms}=run(seed,{learn:true});trainingMs+=ms;certificates.push(...s.learning.certificates);console.log('training',seed,ms,s.stats.proposals,s.learning.rules);}
for(const seed of testSeeds)for(const mode of['plain','frozen']){const {s,ms}=run(seed,{learn:mode==='frozen',train:false,initialCertificates:mode==='frozen'?certificates:[]});const result={seed,mode,ms,status:s.status,proposals:s.stats.proposals,backtracks:s.stats.backtracks,rules:s.learning?.rules||0};results.push(result);console.log(JSON.stringify(result));}
const report={trainingMs,trainSeeds,testSeeds,targetCount,nodeLimit,results,certificates};writeFileSync('/tmp/cyclotomic-frozen-report.json',JSON.stringify(report,null,2)+'\n');
