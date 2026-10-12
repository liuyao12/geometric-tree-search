import {readFileSync,writeFileSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {solveLattice} from '../research/knot-classifier/lattice-search.mjs';
const fixture=JSON.parse(readFileSync(new URL('../research/knot-classifier/fixtures/trefoil-identification.json',import.meta.url)));
const args=process.argv.slice(2),get=(key,fallback)=>args.find(x=>x.startsWith(`--${key}=`))?.split('=').slice(1).join('=')??fallback;
const bounds={...fixture.bounds,depth:Number(get('depth',fixture.bounds.depth))},seed=Number(get('seed',31));
const worker=get('lane',null);
if(worker){
 const result=solveLattice(fixture.source,fixture.target,{...bounds,learn:worker==='online-gcts',seed});
 console.log(JSON.stringify({lane:worker,...result,runtime:{node:process.version,platform:process.platform,arch:process.arch,memoryAtEndBytes:process.memoryUsage(),maxRSSKiB:process.resourceUsage().maxRSS}}));
}else{
 const runs=[];
 for(const lane of ['unmarked','online-gcts']){
  const child=spawnSync(process.execPath,[fileURLToPath(import.meta.url),`--lane=${lane}`,`--depth=${bounds.depth}`,`--seed=${seed}`],{encoding:'utf8',maxBuffer:10*1024*1024});
  if(child.status!==0)throw Error(child.stderr||'Benchmark subprocess failed.');
  const result=JSON.parse(child.stdout);runs.push(result);
  console.log(JSON.stringify({lane,status:result.status,moves:result.certificate?.steps.map(x=>x.kind),states:result.stateCount,tiles:result.tileCount,stats:result.stats,catalogMs:result.catalogMs,searchMs:result.searchMs,totalMs:result.totalMs,maxRSSKiB:result.runtime.maxRSSKiB}));
 }
 const report={fixture:fixture.name,knownKnot:fixture.knownKnot,bounds,seed,runs,scope:'Finite square-face Reidemeister inventory; positive spatial certificates only. Separate fresh Node process per lane, cold learning, no persisted marking import. RSS peak includes process/module startup; totalMs includes catalog, search/probes and JS replay but excludes startup and separate Python replay.'};
 const output=get('output',null);if(output)writeFileSync(output,JSON.stringify(report,null,2)+'\n');
 if(runs.some(x=>x.status!=='equivalent'))process.exitCode=1;
}
