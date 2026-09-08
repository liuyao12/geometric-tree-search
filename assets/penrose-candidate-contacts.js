import {canonical,latticeKey} from './cyclotomic-five.js';
import {extendedBars,tileStates} from './penrose-mixed-markings.js?v=20260907-frontier';
import {onSegment,pointInPolygon,segmentCuts,lerp,num,add,mul,div,sub,cmp,box,separated} from './penrose-polygon.js';

// Critical points are induced by a candidate's geometry. There is no uniform
// subdivision and no attempt to enumerate the dense projected integer ring.
export function candidateBarContacts(placed,candidate,extent){
  const output=new Map(),targetBars=extendedBars(candidate,extent);
  const targetBounds=box([...candidate.exactPoints,...targetBars.flatMap(b=>[b.from,b.to])]);
  const original=tileStates(placed)[0].bars;
  extendedBars(placed,extent).forEach((bar,index)=>{
    if(separated(box([bar.from,bar.to]),targetBounds))return;
    const matches=targetBars.filter(b=>b.family===bar.family);
    const value=p=>matches.some(b=>onSegment(p,b.from,b.to))?1:pointInPolygon(p,candidate.exactPoints)?0:null;
    const record=(point,type)=>{
      const v=value(point);if(v===null)return;
      const key=latticeKey(point)+':'+bar.family,vertex=candidate.vertices.indexOf(latticeKey(point));
      const entry={point:canonical(point),family:bar.family,value:v,type,weight:vertex<0?0:candidate.weights[vertex],extension:!onSegment(point,original[index].from,original[index].to)};
      const old=output.get(key);if(!old||type==='witness'||type==='vertex')output.set(key,entry);
    };
    candidate.exactPoints.forEach(p=>{if(onSegment(p,bar.from,bar.to))record(p,'vertex');});
    for(const b of tileStates(candidate)[0].bars)for(const p of[b.from,b.to])if(onSegment(p,bar.from,bar.to))record(p,'port');
    const cuts=new Map(segmentCuts(bar.from,bar.to,candidate.exactPoints).map(t=>[latticeKey(t),t]));
    // Split also at endpoints of collinear candidate bars. One witness in each
    // resulting open interval suffices because m is constant on that interval.
    for(const b of matches)for(const p of[b.from,b.to])if(onSegment(p,bar.from,bar.to)){
      const t=div(sub(p,bar.from),sub(bar.to,bar.from));cuts.set(latticeKey(t),t);record(p,'port');
    }
    const ordered=[...cuts.values()].sort(cmp);
    for(const t of ordered){const p=lerp(bar.from,bar.to,t);if(pointInPolygon(p,candidate.exactPoints))record(p,'boundary');}
    for(let k=0;k<ordered.length-1;k++){
      const p=lerp(bar.from,bar.to,mul(add(ordered[k],ordered[k+1]),num(1,2)));
      if(value(p)===0)record(p,'witness');
    }
  });
  return [...output.values()];
}
export function collectCandidateContacts(placed,candidates,extent){
  const points=new Map(),metadata=[];
  for(const candidate of candidates){
    const index=metadata.length;metadata.push({kind:candidate.tile.kind,legal:candidate.legal});
    placed.forEach((tile,placedIndex)=>{
      for(const contact of candidateBarContacts(tile,candidate.tile,extent)){
        const key=latticeKey(contact.point);
        if(!points.has(key))points.set(key,{point:contact.point,extension:false,records:[]});
        const p=points.get(key);p.extension ||= contact.extension;
        p.records.push({candidate:index,placed:placedIndex,family:contact.family,value:contact.value,weight:contact.weight,type:contact.type});
      }
    });
  }
  return {points:[...points.values()],candidates:metadata};
}
