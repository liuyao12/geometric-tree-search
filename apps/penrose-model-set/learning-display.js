import {embedding,cycloAdd,latticeKey} from '../../assets/cyclotomic-five.js?v=20260908-speed';
import {extendBar} from '../../assets/penrose-extensions.js?v=20260908-speed';
// Geometry survives worker snapshots. A point shared by many fiber channels
// is translated once, rather than once per scalar value on every redraw.
export function createDisplayCache(){
 let definitions=null,plans=new Map(),cached=new Map();
 return{frame(tiles,tables,showPoints=true,showBars=false){
  if(definitions!==tables){definitions=tables;plans=new Map();for(const t of tables||[]){const points=new Map();for(const r of t.rows){const key=latticeKey(r.offset);if(!points.has(key))points.set(key,{offset:r.offset,values:[]});points.get(key).values.push([r.channel,r.value]);}plans.set(t.type,[...points.values()]);}}
  const points=new Map(),next=new Map(),drawTiles=[];
  const get=v=>{if(!points.has(v.key))points.set(v.key,{point:v.point,xy:v.xy,total:0,values:new Map(),marked:false});return points.get(v.key);};
  for(const t of tiles){let c=cached.get(t.id);if(!c)c={vertices:t.exactPoints.map(point=>({point,key:latticeKey(point),xy:embedding(point)})),kind:t.kind};next.set(t.id,c);
   c.vertices.forEach((v,i)=>get(v).total+=t.weights[i]);
   if(showPoints){if(c.definitions!==definitions){c.definitions=definitions;c.marking=(plans.get(t.type)||[]).map(r=>{const point=cycloAdd(t.origin,r.offset);return{point,key:latticeKey(point),xy:embedding(point),values:r.values};});}
    for(const v of c.marking||[]){const p=get(v);p.marked=true;for(const[channel,value]of v.values){const prior=p.values.get(channel);p.values.set(channel,prior!==undefined&&prior!==value?'conflict':value);}}
   }
   if(showBars&&!c.bars)c.bars=(t.bars||[]).map(b=>{const ex=extendBar(b,2);return{from:embedding(ex.from),to:embedding(ex.to)};});
   drawTiles.push({kind:t.kind,loop:c.vertices.map(v=>v.xy),bars:showBars?c.bars:[]});
  }
  cached=next;return{points:[...points.values()],tiles:drawTiles};
 }};
}
