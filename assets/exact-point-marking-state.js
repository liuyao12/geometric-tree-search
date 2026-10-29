/** Reversible m-values on explicitly supplied exact support points.
 * Missing channels are unconstrained; an assigned zero is a value.
 * Dependency lookup is independent of geometric bounds and the frontier.
 */
import { pointKey } from './golden-field.js';
export function markingValueKey(value){
 if(value===null)return 'null';
 if(typeof value==='bigint')return `integer:${value}`;
 if(typeof value==='number'){if(!Number.isSafeInteger(value))throw new TypeError('Marking numbers must be exact safe integers');return `integer:${value}`;}
 if(typeof value==='string'||typeof value==='boolean')return `${typeof value}:${value}`;
 if(value?.key instanceof Function)return `field:${value.key()}`;
 if(Array.isArray(value))return `array:${JSON.stringify(value.map(markingValueKey))}`;
 throw new TypeError('Unsupported assigned marking value');
}
export class PointMarkingState{
 constructor({set,add}){this.values=new Map();this.dependencies=new Map();this.set=set;this.add=add;}
 compatible(tile){
  for(const mark of tile.pointMarkings||[]){const old=this.values.get(pointKey(mark.point));if(!old)continue;
   for(const [channel,value]of Object.entries(mark.components)){if(value===undefined)continue;const assigned=old.get(channel);if(assigned&&assigned.key!==markingValueKey(value))return false;}
  }return true;
 }
 register(tile){for(const mark of tile.pointMarkings||[]){
  if(!Object.values(mark.components).some(v=>v!==undefined))continue;
  const key=pointKey(mark.point);if(!this.dependencies.has(key))this.set(this.dependencies,key,new Set());this.add(this.dependencies.get(key),tile.id);
 }}
 affected(tile){const result=new Set();for(const mark of tile.pointMarkings||[])for(const id of this.dependencies.get(pointKey(mark.point))||[])result.add(id);return result;}
 assign(tile){
  if(!this.compatible(tile))throw new Error('Conflicting point marking assignment');
  for(const mark of tile.pointMarkings||[]){
   const entries=Object.entries(mark.components).filter(([,value])=>value!==undefined);if(!entries.length)continue;
   const key=pointKey(mark.point);if(!this.values.has(key))this.set(this.values,key,new Map());const values=this.values.get(key);
   for(const [channel,value]of entries){const old=values.get(channel);this.set(values,channel,{value,key:markingValueKey(value),refs:(old?.refs||0)+1});}
  }
 }
 get pointCount(){return this.values.size;}
 get componentCount(){let n=0;for(const value of this.values.values())n+=value.size;return n;}
 inspect(){const sort=(a,b)=>a[0].localeCompare(b[0]);return {
  values:[...this.values].map(([key,channels])=>[key,[...channels].map(([channel,r])=>[channel,r.key,r.refs]).sort(sort)]).sort(sort),
  dependencies:[...this.dependencies].map(([key,ids])=>[key,[...ids].sort()]).sort(sort)
 };}
}
