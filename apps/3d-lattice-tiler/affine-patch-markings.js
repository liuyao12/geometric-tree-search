// Experimental affine constraints on a shared section. Not fixed-value GCTS.
import {POINT_GROUP,transform,transformedPlacement,composeIndex} from './patch-constraint-markings.js';
export function compileAffinePatch(fixed,anchor){
  if(fixed.length<2||new Set(fixed.map(s=>JSON.stringify(s))).size!==fixed.length)throw Error('Expected distinct patch placements');
  const fields=[[],[],[]];
  for(let channel=0;channel<48;channel++){
    const g=POINT_GROUP[channel],q=transform(g,anchor);
    fixed.forEach((s,role)=>{const [oi,t]=transformedPlacement(g,s);if(!fields[oi])throw Error('Unknown orientation');fields[oi].push({pos:q.map((x,i)=>x-t[i]),channel,zeroCoordinate:role});});
  }
  // At each point/channel the shared vector satisfies sum(z_i)=1.
  // An atom imposes z_role=0; an absent atom is the wildcard.
  return {kind:'normalized-affine-section',dimension:fixed.length,fields,componentAction:POINT_GROUP.map(g=>POINT_GROUP.map(h=>composeIndex(g,h)))};
}
export class AffinePatchSection{
  constructor(marking,{requiredPoints=null}={}){this.marking=marking;this.requiredPoints=requiredPoints;this.sites=new Map();this.stack=[];this.used=new Set();}
  push([oi,t]){
    const id=JSON.stringify([oi,t]);if(this.used.has(id))throw Error('Duplicate placement');const touched=[];
    for(const atom of this.marking.fields[oi]){const point=atom.pos.map((x,i)=>x+t[i]),key=`${point}|${atom.channel}`;let s=this.sites.get(key);if(!s){s={point,channel:atom.channel,counts:Array(this.marking.dimension).fill(0),refs:0};this.sites.set(key,s);}s.counts[atom.zeroCoordinate]++;s.refs++;touched.push([key,atom.zeroCoordinate]);}
    this.stack.push({id,touched});this.used.add(id);return this.conflicts();
  }
  pop(){const u=this.stack.pop();if(!u)throw Error('Empty rollback');for(const [key,i] of u.touched){const s=this.sites.get(key);s.counts[i]--;if(!--s.refs)this.sites.delete(key);}this.used.delete(u.id);}
  conflicts(){return [...this.sites.values()].filter(s=>(!this.requiredPoints||this.requiredPoints.has(s.point.join(',')))&&s.counts.every(n=>n>0)).map(s=>({point:s.point,channel:s.channel}));}
  snapshot(){return [...this.sites].sort(([a],[b])=>a.localeCompare(b)).map(([key,s])=>[key,s.refs,[...s.counts]]);}
}
