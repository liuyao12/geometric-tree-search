// Isolated proposed extension: constraints on a shared vector-bundle section.
// Existing GCTS markings require equality of assigned values. This module uses
// intersections of admissible basis-vector sets, and is NOT enabled in its lanes.
export const POINT_GROUP=[];
for(const perm of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]])
  for(let bits=0;bits<8;bits++)POINT_GROUP.push({perm,sign:[0,1,2].map(i=>bits&(1<<i)?-1:1)});
export const transform=(g,p)=>g.perm.map((axis,i)=>g.sign[i]*p[axis]);
export const orient=(g,oi)=>[2,1,0].indexOf(g.perm.indexOf([2,1,0][oi]));
export const transformedPlacement=(g,[oi,p])=>[orient(g,oi),transform(g,p)];
const signature=g=>JSON.stringify([g.perm,g.sign]);
const lookup=new Map(POINT_GROUP.map((g,i)=>[signature(g),i]));
export function composeIndex(g,h){return lookup.get(signature({perm:g.perm.map(j=>h.perm[j]),sign:g.perm.map((j,i)=>g.sign[i]*h.sign[j])}));}
export function compilePatchConstraints(fixed,anchor,{fiberStates,allowedMasks}){
  // The exact-pattern guarantee currently relies on one role per orientation.
  // Repeated orientations need a separate compiler and cross-talk proof.
  if(fixed.length!==3||new Set(fixed.map(s=>s[0])).size!==3||fixed.some(s=>![0,1,2].includes(s[0])))throw Error('This prototype requires three distinct cross orientations');
  if(fiberStates<1||fiberStates>20||allowedMasks.length!==fixed.length)throw Error('Invalid finite-state marking');
  const full=(1<<fiberStates)-1,fields=[[],[],[]];
  if(allowedMasks.some(m=>!Number.isInteger(m)||m<0||m>full))throw Error('Invalid admissible-state mask');
  for(let channel=0;channel<POINT_GROUP.length;channel++){
    const g=POINT_GROUP[channel],q=transform(g,anchor);
    fixed.forEach((s,role)=>{const [oi,t]=transformedPlacement(g,s);fields[oi].push({pos:q.map((x,i)=>x-t[i]),channel,allowed:allowedMasks[role],role});});
  }
  return {kind:'constraint-valued-section',fiberStates,full,fields,
    componentAction:POINT_GROUP.map(g=>POINT_GROUP.map(h=>composeIndex(g,h)))};
}
export class ConstraintSection {
  constructor(marking,{requiredPoints=null}={}){this.marking=marking;this.requiredPoints=requiredPoints;this.sites=new Map();this.stack=[];this.placements=new Set();}
  push([oi,t]){
    const placement=JSON.stringify([oi,t]);if(this.placements.has(placement))throw Error('Duplicate placement');
    const touched=[];
    for(const atom of this.marking.fields[oi]){
      const pos=atom.pos.map((x,i)=>x+t[i]),key=`${pos.join(',')}|${atom.channel}`;
      let site=this.sites.get(key);if(!site){site={pos,channel:atom.channel,counts:Array(this.marking.fiberStates).fill(0),refs:0};this.sites.set(key,site);}
      site.refs++;
      for(let v=0;v<site.counts.length;v++)if(!(atom.allowed&(1<<v)))site.counts[v]++;
      touched.push({key,allowed:atom.allowed});
    }
    this.placements.add(placement);this.stack.push({placement,touched});return this.conflicts();
  }
  pop(){
    const undo=this.stack.pop();if(!undo)throw Error('Empty rollback');
    for(const {key,allowed} of undo.touched){const site=this.sites.get(key);for(let v=0;v<site.counts.length;v++)if(!(allowed&(1<<v)))site.counts[v]--;if(--site.refs===0)this.sites.delete(key);}
    this.placements.delete(undo.placement);
  }
  conflicts(){return [...this.sites.values()].filter(s=>(!this.requiredPoints||this.requiredPoints.has(s.pos.join(',')))&&s.counts.every(n=>n>0)).map(s=>({point:s.pos,channel:s.channel}));}
  snapshot(){return [...this.sites].sort(([a],[b])=>a.localeCompare(b)).map(([key,s])=>[key,s.refs,[...s.counts]]);}
}
