import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=process.argv[2]||resolve(new URL('..',import.meta.url).pathname);
const load=name=>import(pathToFileURL(resolve(root,name)));
const {selectedPenroseProblem,TILE_PRESETS}=await load('assets/penrose-selection-problem.js');
const {knownPenroseBenchmark}=await load('assets/penrose-known-benchmark.js');
const {createObstructionSearch}=await load('assets/cyclotomic-obstruction-search.js');
const set=process.env.SET||'P1',mode=process.env.MODE||'learned',targetCount=Number(process.env.TILES||8),start=performance.now(),problem=selectedPenroseProblem(TILE_PRESETS[set]);
const search=createObstructionSearch({...(mode==='known'?knownPenroseBenchmark(problem):{problem}),learn:mode==='learned',targetCount,nodeLimit:500,seed:1});
const hash=createHash('sha256');let events=0;
while(true){const r=search.next();if(r.done)break;events++;hash.update(JSON.stringify([r.value.type,r.value.tile?.id,r.value.frontier,r.value.forced,r.value.branchCount]));}
const s=search.snapshot();console.log(JSON.stringify({set,mode,ms:performance.now()-start,status:s.status,tiles:s.tiles.length,proposals:s.stats.proposals,rules:s.learning?.rules||0,events,trace:hash.digest('hex'),marking:createHash('sha256').update(JSON.stringify(s.learning?.tables||[])).digest('hex')}));
