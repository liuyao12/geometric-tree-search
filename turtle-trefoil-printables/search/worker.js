import { solveA2Tiling } from './a2-tiling-engine.js';
import { options, displayPlacement } from './model.js';
// Worker plus acknowledged event batches keeps the exact DFS stack alive while
// the page is paused and prevents a fast solver outrunning its animation.
globalThis.requestAnimationFrame=callback=>setTimeout(()=>callback(performance.now()),0);
let waiting=null,events=[],started=false;
const gate=()=>{
 if(!events.length)return Promise.resolve();
 const batch=events;events=[];
 return new Promise(resolve=>{waiting=resolve;postMessage({type:'batch',events:batch});});
};
onmessage=async({data})=>{
 if(data.type==='next'){const resolve=waiting;waiting=null;resolve?.();return;}
 if(data.type!=='start'||started)return;started=true;
 try{
  await solveA2Tiling({...options(data.mode,data.seed),waitForSearchDemand:gate,onEvent:e=>{
   if(['start','placement','backtrack','finished'].includes(e.type))events.push({type:e.type,placements:e.placements.map(displayPlacement),nodes:e.nodes,backtracks:e.backtracks,forced:e.forced,result:e.result});
  }});
  if(events.length)postMessage({type:'batch',events});
 }catch(error){postMessage({type:'error',message:error.message});}
};
