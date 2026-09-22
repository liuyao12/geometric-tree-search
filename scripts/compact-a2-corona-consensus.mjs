#!/usr/bin/env node
import fs from 'node:fs';import path from 'node:path';import {pathToFileURL} from 'node:url';
import {a2Transform} from '../assets/a2-tiling-engine.js';
import {pointModel} from './experiment-a2-corona-consensus.mjs';
export function compactConsensus(source){
 if(!source.complete||!source.solutions)throw Error('Incomplete corona intersection is only a hypothesis');
 const {tile,rank,lattice,support}=source,model=pointModel({tile,rank,lattice}),base=new Map(model.orientations[0].marks.map(m=>[`${m.pos}|${m.component}`,m.value]));
 const fixed=new Set(),root=new Map();support.forEach((s,i)=>{root.set(`${s.point}|${s.component}`,{...s,id:i});if(base.get(`${s.point}|${s.component}`)===s.value&&base.has(`${s.point}|${s.component}`))fixed.add(i);});
 if(fixed.size!==base.size||root.size!==support.length)throw Error('Consensus must contain every original assignment without duplicates');
 const parity=p=>((p[0]>p[1])+(p[0]>p[2])+(p[1]>p[2]))%2?-1:1;
 const oriented=model.oriented.map(o=>support.map((s,id)=>({id,pos:a2Transform(s.point,o.symmetry),component:rank===1?0:o.symmetry.permutation.indexOf(s.component),value:s.value*(rank===1?1:parity(o.symmetry.permutation))})));
 const tRoot=new Map(model.orientations[0].cells.map(c=>[c.pos.join(),c.weight]));
 const constraints=[];let translations=0,capacityLegal=0,knownPass=0,newConflicts=0;
 for(let oi=0;oi<oriented.length;oi++){
  const fields=oriented[oi],shifts=new Set();for(const r of support)for(const m of fields)if(r.component===m.component)shifts.add(r.point.map((v,i)=>v-m.pos[i]).join());
  for(const key of shifts){if(oi===0&&key==='0,0,0')continue;translations++;const t=key.split(',').map(Number);
   if(model.orientations[oi].cells.some(c=>(tRoot.get(c.pos.map((v,i)=>v+t[i]).join())??0)+c.weight>12))continue;capacityLegal++;
   const conflicts=[];let knownConflict=false;
   for(const m of fields){const r=root.get(`${m.pos.map((v,i)=>v+t[i])}|${m.component}`);if(r&&r.value!==m.value){conflicts.push([r.id,m.id]);if(fixed.has(r.id)&&fixed.has(m.id)){knownConflict=true;break;}}}
   if(knownConflict)continue;knownPass++;if(!conflicts.length)continue;newConflicts++;
   constraints.push({oi,translation:t,witnesses:conflicts});
  }
 }
 const added=support.map((_,i)=>i).filter(i=>!fixed.has(i)),incident=support.map(()=>new Set());constraints.forEach((c,j)=>{for(const w of c.witnesses)for(const i of w)incident[i].add(j);});
 let best=null;
 for(const order of [added,[...added].reverse(),[...added].sort((a,b)=>incident[a].size-incident[b].size),[...added].sort((a,b)=>incident[b].size-incident[a].size)]){
  const kept=support.map(()=>true);
  for(const i of order){kept[i]=false;if([...incident[i]].some(j=>!constraints[j].witnesses.some(([a,b])=>kept[a]&&kept[b])))kept[i]=true;}
  if(!best||kept.filter(Boolean).length<best.filter(Boolean).length)best=kept;
 }
 // Deleting entries cannot add a conflict. Every previously rejecting pair
 // still has an assigned disagreement; all pair conflicts, including contacts
 // only in extended marking support, are therefore exactly preserved.
 if(constraints.some(c=>!c.witnesses.some(([a,b])=>best[a]&&best[b])))throw Error('Compaction lost a pair conflict');
 return {support:support.filter((_,i)=>best[i]),summary:{translationAlignments:translations,capacityLegal,knownPass,newConflicts,originalValues:base.size,extendedValues:support.length,compactValues:best.filter(Boolean).length,compactAddedValues:best.filter(Boolean).length-base.size,scope:'Exhaustive relative marking-support alignments, including mark-only contacts; retains every original entry and every additional pair conflict.'}};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const file=process.argv[2],source=JSON.parse(fs.readFileSync(file)),started=performance.now(),result=compactConsensus(source);const out=file.replace(/\.json$/,'-compact.json');fs.writeFileSync(out,JSON.stringify({...source,fullCommonValues:source.commonValues,support:result.support,compaction:{...result.summary,elapsedMs:performance.now()-started}}));console.log(JSON.stringify({file:out,...result.summary,elapsedMs:performance.now()-started}));}
