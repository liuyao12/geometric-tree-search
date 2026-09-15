// Colored-cloud adapter for the full factorized decorated candidate universe.
// Pair-disjointness is only a necessary rejection test. Terminal certification
// separately requires one common value for all assignments at each mark point.
import {FactorizedPointSearch} from './factorized-point-search.mjs';
import {cloudContains,cloudConsensus} from './portable-cloud-filter.mjs';
export function factorizedCloudWitnesses(state,pool,radius){
 const witnesses=[];
 for(const [id,p] of state.points)if(p.marks.length){
  const result=cloudConsensus(p.marks.map(m=>pool[m.value.cloud]),radius);
  if(result.status!=='verified-witness')return {valid:false,status:'unknown-common-value',reason:'Common cloud value not certified',point:id,witnesses:[]};
  witnesses.push({point:JSON.stringify([id,'portable']),...result});
 }
 return {valid:true,status:'verified-common-values',witnesses};
}
export function makeFactorizedCloudSearch(model,pool,{Engine=FactorizedPointSearch}={}){
 if(!Number.isFinite(model.cloudRadius)||model.cloudRadius<0)throw Error('Invalid cloud radius');
 const used=new Set(model.blocks.flatMap(b=>b.endpointChoices.flat().map(c=>c.cloud)));
 for(const index of used){
  if(!Number.isSafeInteger(index)||index<0||index>=pool.length)throw Error('Invalid cloud reference');
  const c=pool[index];
  if(!c.vectors.length||c.vectors.length!==c.colors.length||c.vectors.some(v=>v.length!==3||v.some(x=>!Number.isFinite(x))))throw Error('Invalid cloud');
 }
 const cache=new Map(),stats={checks:0,hits:0,evictions:0};
 const compatible=(value,active)=>active.every(a=>{
  const i=value.cloud,j=a.value.cloud;stats.checks++;
  if(i===j)return true;
  const key=i<j?`${i}:${j}`:`${j}:${i}`;
  if(cache.has(key)){stats.hits++;return cache.get(key);}
  const result=cloudContains(pool[i],pool[j],2*model.cloudRadius+1e-10)!==null;
  // Immutable-value cache only. Clearing it changes cost, never legality.
  if(cache.size>=200000){cache.clear();stats.evictions++;}
  cache.set(key,result);return result;
 });
 const state=new Engine(model,{compatible,terminalCheck:e=>factorizedCloudWitnesses(e,pool,model.cloudRadius)});
 state.cloudStats=stats;state.cloudCheck=()=>factorizedCloudWitnesses(state,pool,model.cloudRadius);
 return state;
}
