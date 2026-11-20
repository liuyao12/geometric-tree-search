import {readFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {A2_TILE_LOOPS,tileOrientations} from '../../assets/a2-tiling-engine.js';
import {hex,origin,tileModel} from './model.mjs';
import {fill,leastCover,rng} from './search.mjs';
import {learner} from './learn.mjs';

export function* windows(input,options={}) {
  const defaults={radius:1,extent:1,proofRadius:0,proofNodes:8,proposals:24,
    seed:1,nodes:10000};
  const {through,stabilize=through!==undefined,...specified}=options;
  if (typeof stabilize!=='boolean') throw new Error('stabilize must be a boolean');
  const config={...defaults,...specified};
  for (const [key,v] of Object.entries(config)) {
    if (!Object.hasOwn(defaults,key)) throw new Error('Unknown option '+key);
    if (key==='nodes' && v===null) continue;
    if (!Number.isSafeInteger(v) || v<0) throw new Error('Expected a nonnegative integer for '+key);
  }
  if (through!==undefined && through!==null && (!Number.isSafeInteger(through)||through<config.radius)) {
    throw new Error('through must be at least radius, or null for successive windows');
  }
  const last=through===null ? Infinity : through??config.radius;
  const model=tileModel(input), learning=learner(model,config);
  for (let radius=config.radius; radius<=last; radius++) {
    const targets=hex(origin,radius), exhausted=new Set();
    let nodes=0,failures=0,backtracks=0,result;
    do {
      // Rebuild domains and the live prefix after a certified revision.
      result=fill(model,targets,[model.root],[...learning.support.values()],rng(config.seed),
        (config.nodes??Infinity)-nodes,learning.consider,exhausted);
      nodes+=result.nodes; failures+=result.failures; backtracks+=result.backtracks;
    } while (result.status==='revised');
    let orderNodes=0,orderQueries=0;
    if (stabilize && result.status==='covered') {
      result=leastCover(model,targets,[...learning.support.values()],result.placements,config.seed,
        (config.nodes??Infinity)-nodes);
      orderNodes=result.nodes; orderQueries=result.queries; nodes+=orderNodes;
    }
    yield {status:result.status,config:{...config,radius,stabilize},nodes,orderNodes,orderQueries,
      failures,backtracks,...learning.stats(),
      revisions:learning.revisions.slice(),placements:result.placements.map(p=>p.id),
      marking:[...learning.support.values()].map(m=>[String(m.point),m.axis,m.value])};
    if (result.status!=='covered') return;
  }
}
export const search=(input,options={})=>windows(input,options).next().value;
export function builtIn(name) {
  const loop=A2_TILE_LOOPS[name];
  if (!Array.isArray(loop)) throw new Error('Unknown built-in tile');
  const sites=tileOrientations(name,loop)[0].occupancy;
  return {capacity:12,points:[...sites.values()].map(({point,weight})=>[...point.slice(0,2),weight])};
}
export const readTile=source=>Object.hasOwn(A2_TILE_LOOPS,source)
  ? builtIn(source) : JSON.parse(readFileSync(source,'utf8'));
if (process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  const [source,settings]=process.argv.slice(2);
  if (!source) throw new Error('Usage: node run.mjs tile.json|hat|turtle|hexagon [options.json]');
  const input=readTile(source);
  const options=settings?JSON.parse(readFileSync(settings,'utf8')):{};
  for (const result of windows(input,options)) console.log(JSON.stringify(result));
}
