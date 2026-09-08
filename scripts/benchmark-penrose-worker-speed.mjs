import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const root=process.argv[2]||resolve(new URL('..',import.meta.url).pathname),compact=process.env.COMPACT==='1';
const load=p=>import(pathToFileURL(resolve(root,p)));
const {TILE_PRESETS}=await load('assets/penrose-selection-problem.js');
const {embedding,cycloAdd,latticeKey}=await load('assets/cyclotomic-five.js');
let cache;if(compact){const {createDisplayCache}=await load('apps/penrose-model-set/learning-display.js');cache=createDisplayCache();}
let state,priorTables,frames=0,bytes=0;const start=performance.now();
globalThis.self={postMessage(data){
 state=structuredClone(data);if(state.error)throw Error(state.error);frames++;bytes+=JSON.stringify(state).length;
 if(state.learning&&!state.learning.tables)state.learning.tables=priorTables;priorTables=state.learning?.tables;
 if(compact)cache.frame(state.tiles,state.learning?.tables,true,false);
 else{
  // The previous canvas rebuilt and translated every scalar channel row.
  const points=new Map(),tables=new Map((state.learning?.tables||[]).map(t=>[t.type,t.rows]));
  const get=p=>{const key=latticeKey(p);if(!points.has(key))points.set(key,{point:p,total:0,values:new Map()});return points.get(key);};
  for(const t of state.tiles){t.exactPoints.forEach((p,i)=>get(p).total+=t.weights[i]);for(const r of tables.get(t.type)||[])get(cycloAdd(t.origin,r.offset)).values.set(r.channel,r.value);t.exactPoints.forEach(p=>embedding(p));}
  for(const p of points.values())embedding(p.point);
 }
}};
await load('apps/penrose-model-set/learning-worker.js');
const set=process.env.SET||'P3',targetCorona=Number(process.env.CORONA||3);
self.onmessage({data:{type:'init',mode:'learned',tileKinds:TILE_PRESETS[set],compact}});
while(!state.done&&state.pausedCorona!==targetCorona)self.onmessage({data:{type:'advance',targetCorona}});
console.log(JSON.stringify({set,compact,ms:performance.now()-start,computeMs:state.computeMs,frames,bytes,tiles:state.tiles.length,proposals:state.stats.proposals,corona:state.minimumFrontierGeneration,rules:state.learning.rules}));
