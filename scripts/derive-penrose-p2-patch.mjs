import {readFile,writeFile} from 'node:fs/promises';
import {embedding,latticeKey} from '../assets/cyclotomic-five.js';
import {arrowStates} from '../assets/penrose-arrows.js';
import {areaSign} from '../assets/penrose-polygon.js';
const {parts}=JSON.parse(await readFile('/tmp/penrose-common-patch.json'));
const points=new Map(),adj=new Map();
function edge(a,b){const ka=latticeKey(a),kb=latticeKey(b);points.set(ka,a);points.set(kb,b);for(const[x,y]of[[ka,kb],[kb,ka]]){if(!adj.has(x))adj.set(x,new Set());adj.get(x).add(y);}}
for(const{tile,start}of parts){if(tile.kind==='thick')edge(tile.exactPoints[start],tile.exactPoints[(start+2)%4]);else for(const a of arrowStates(tile).find(s=>s.start===start).arrows.filter(a=>a.type===2))edge(a.from,a.to);}
const angle=(a,b)=>{const p=embedding(points.get(a)),q=embedding(points.get(b));return Math.atan2(q.y-p.y,q.x-p.x);};
for(const[k,v]of adj)adj.set(k,[...v].sort((a,b)=>angle(k,a)-angle(k,b)));
const visited=new Set(),tiles=[];
for(const[a,neighbors]of adj)for(const b of neighbors){if(visited.has(a+'>'+b))continue;let x=a,y=b,ids=[],closed=false;for(let step=0;step<1000;step++){const key=x+'>'+y;if(visited.has(key)){closed=x===a&&y===b;break;}visited.add(key);ids.push(x);const at=adj.get(y),z=at[(at.indexOf(x)+at.length-1)%at.length];x=y;y=z;}const poly=ids.map(k=>points.get(k));if(!closed||poly.length!==4||areaSign(poly)<=0)continue;
 const weights=ids.map((v,i)=>{let turn=angle(v,ids[(i+1)%4])-angle(ids[(i+3)%4],v);while(turn<=-Math.PI)turn+=2*Math.PI;while(turn>Math.PI)turn-=2*Math.PI;return Math.round(5-turn*5/Math.PI);});
 tiles.push({kind:weights.some(w=>w>5)?'dart':'kite',presentation:'P2',exactPoints:poly,weights});}
console.log('P2 faces',tiles.length, [...new Set(tiles.map(t=>t.weights.slice().sort().join(',')))]);
await writeFile('/tmp/penrose-p2-patch.json',JSON.stringify(tiles));
