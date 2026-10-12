import { canonical, parse, topology } from './engine.mjs';
import { verifyDrawing } from './drawing.mjs?v=readable-v1';

// An authored geometric presentation of the trefoil braid closure. Empty
// sectors remain in place when a cancelling pair is removed. Search still
// uses the complete ordinary catalog; this module only presents its result.
const initial = { radii:[.44,.70,1],slots:[1,1,2,1,2,-1].map((g,i)=>({g,id:i+1})) };
const copy = state => ({radii:[...state.radii],slots:state.slots.map(x=>x?{...x}:null)});
const signature=x=>`${x.id}:${x.over}:${x.sign}`;
function sameLabels(a,b){
  if(a.length!==b.length)return false;if(!a.length)return true;
  const key=a.map(signature).join(' ');
  return [b,[...b].reverse()].some(w=>w.some((_,i)=>[...w.slice(i),...w.slice(0,i)].map(signature).join(' ')===key));
}
function geometry(state){
  const n=state.radii.length,samples=32,sector=2*Math.PI/state.slots.length,start=-sector/2;
  const points=[],walk=[],events=[],crossings=new Map();
  const put=p=>{points.push(p);return points.length-1;};
  const first=put([state.radii[0]*Math.cos(start),state.radii[0]*Math.sin(start)]);walk.push(first);
  let lane=0,passes=0;
  do{
    for(let row=0;row<state.slots.length;row++){
      const slot=state.slots[row],i=slot?Math.abs(slot.g)-1:-2,swap=lane===i||lane===i+1;
      const outgoing=swap?2*i+1-lane:lane;
      for(let k=1;k<=samples;k++){
        const t=k/samples,theta=start+(row+t)*sector;
        const s=Math.max(0,Math.min(1,(t-.25)*2)),blend=(1-Math.cos(Math.PI*s))/2;
        const radius=state.radii[lane]+(state.radii[outgoing]-state.radii[lane])*blend;
        const p=[radius*Math.cos(theta),radius*Math.sin(theta)];
        if(slot&&swap&&k===samples/2){
          if(!crossings.has(slot.id))crossings.set(slot.id,{id:slot.id,center:put(p),sign:Math.sign(slot.g)});
          const c=crossings.get(slot.id);walk.push(c.center);
          events.push({id:slot.id,over:slot.g>0?lane===i:lane===i+1,sign:Math.sign(slot.g),at:walk.length-1});
        }else walk.push(put(p));
      }
      lane=outgoing;
    }
    passes++;if(passes>n)throw Error('Annular closure is not a knot.');
  }while(lane!==0);
  if(passes!==n)throw Error('Annular closure has multiple components.');
  walk.pop();const length=walk.length;
  const slice=(from,to)=>Array.from({length:to-from+1},(_,k)=>walk[(from+k+length)%length]);
  for(const e of events){const c=crossings.get(e.id),ports=[walk[(e.at-3+length)%length],walk[(e.at+3)%length]];if(e.over){c.over=ports;c.overPath=slice(e.at-3,e.at+3);}else c.under=ports;}
  const word=events.map(({id,over,sign})=>({id,over,sign}));topology(word);
  const strands=events.map((e,i)=>slice(e.at,i+1<events.length?events[i+1].at:events[0].at+length));
  const edges=strands.flatMap(s=>s.slice(1).map((b,k)=>[s[k],b]));
  const drawing={word,points,strands,edges,crossings:[...crossings.values()],annular:true};verifyDrawing(drawing);return drawing;
}
function candidates(state,kind){
  const active=state.slots.map((x,i)=>x?i:-1).filter(i=>i>=0),out=[];
  if(kind==='II−')for(let j=0;j<active.length;j++){
    const a=active[j],b=active[(j+1)%active.length];if(state.slots[a].g!==-state.slots[b].g)continue;
    const next=copy(state);next.slots[a]=null;next.slots[b]=null;out.push(next);
  }
  if(kind==='III')for(let j=0;j<active.length&&active.length>=3;j++){
    const indices=[0,1,2].map(k=>active[(j+k)%active.length]),[a,b,c]=indices.map(i=>state.slots[i]);
    if(Math.abs(a.g)!==Math.abs(c.g)||Math.abs(Math.abs(a.g)-Math.abs(b.g))!==1)continue;
    if(a.g===c.g&&Math.sign(a.g)!==Math.sign(b.g))continue; // cyclic depth order
    const next=copy(state);next.slots[indices[0]]={g:Math.abs(b.g)*Math.sign(c.g),id:c.id};next.slots[indices[1]]={g:Math.abs(a.g)*Math.sign(b.g),id:b.id};next.slots[indices[2]]={g:Math.abs(b.g)*Math.sign(a.g),id:a.id};out.push(next);
  }
  if(kind==='I−')for(const side of [0,state.radii.length-1]){
    if(state.radii.length<=2)continue;
    const generator=side===0?1:state.radii.length-1,touched=active.filter(i=>Math.abs(state.slots[i].g)===generator);if(touched.length!==1)continue;
    const next=copy(state);next.radii.splice(side,1);next.slots[touched[0]]=null;
    if(side===0)for(const x of next.slots)if(x)x.g-=Math.sign(x.g);out.push(next);
  }
  return out;
}
// Validate the precise labeled face mutation, including all strand endpoints.
// A canonical match alone would not establish that the pictured region moves.
function presentationMove(before,after,kind){
  const {faces,alpha}=topology(before.word),w=before.word;
  for(const f of faces){
    const ids=new Set(f.flatMap(d=>[w[Math.floor(d/2)].id,w[Math.floor(alpha[d]/2)].id]));
    let expected=null;
    if(kind==='I−'&&f.length===1&&ids.size===1)expected=w.filter(x=>!ids.has(x.id));
    if(kind==='II−'&&f.length===2&&ids.size===2&&f.every(d=>w[Math.floor(d/2)].over===w[Math.floor(alpha[d]/2)].over)){
      const [a,b]=[...ids];if(w.find(x=>x.id===a).sign!==w.find(x=>x.id===b).sign)expected=w.filter(x=>!ids.has(x.id));
    }
    if(kind==='III'&&f.length===3&&ids.size===3){
      const pairs=f.map(d=>[Math.floor(d/2),Math.floor(alpha[d]/2)]),types=pairs.map(([a,b])=>Number(w[a].over)+Number(w[b].over));
      if(new Set(pairs.flat()).size===6&&types.includes(0)&&types.includes(2)){expected=w.map(x=>({...x}));for(const [a,b]of pairs)[expected[a],expected[b]]=[expected[b],expected[a]];}
    }
    if(expected&&sameLabels(expected,after.word))return {affected:ids,face:f};
  }
  return null;
}
const occurrence=x=>`${x.id}:${x.over}`;
function changed(before,after){const successors=new Map(after.word.map((x,i)=>[occurrence(x),occurrence(after.word[(i+1)%after.word.length])]));return new Set(before.word.map((x,i)=>successors.get(occurrence(x))!==occurrence(before.word[(i+1)%before.word.length])?i:-1).filter(i=>i>=0));}
const coordinate=p=>p.map(x=>Math.round(x*1e8)).join(',');
export const segmentKey=(drawing,a,b)=>[coordinate(drawing.points[a]),coordinate(drawing.points[b])].sort().join('|');
const segmentSet=d=>new Set(d.edges.map(([a,b])=>segmentKey(d,a,b)));

export function annularMovie(certificate){
  if(canonical(geometry(initial).word)!==canonical(parse(certificate.source)))return null;
  function visit(state,before,index){
    if(index===certificate.steps.length)return canonical(before.word)===canonical(parse(certificate.target))?[]:null;
    const step=certificate.steps[index];
    for(const next of candidates(state,step.kind)){
      const after=geometry(next);if(canonical(after.word)!==step.after)continue;
      const patch=presentationMove(before,after,step.kind);if(!patch)continue;
      const tail=visit(next,after,index+1);if(!tail)continue;
      const beforeSegments=segmentSet(before),afterSegments=segmentSet(after);
      return [{kind:step.kind,before,after,affected:patch.affected,beforeStrands:changed(before,after),afterStrands:changed(after,before),beforeSegments:new Set([...beforeSegments].filter(x=>!afterSegments.has(x))),afterSegments:new Set([...afterSegments].filter(x=>!beforeSegments.has(x)))},...tail];
    }
    return null;
  }
  return visit(copy(initial),geometry(initial),0);
}

export function drawAnnular(canvas,drawing,{affected=new Set(),changedSegments=new Set(),labels=false}={}){
  const ctx=canvas.getContext('2d'),scale=Math.min(canvas.width,canvas.height)*.42,xy=drawing.points.map(p=>[canvas.width/2+p[0]*scale,canvas.height/2-p[1]*scale]);
  ctx.clearRect(0,0,canvas.width,canvas.height);ctx.lineJoin='round';ctx.lineCap='round';
  const line=(ids,color,width)=>{ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ids.forEach((id,i)=>i?ctx.lineTo(...xy[id]):ctx.moveTo(...xy[id]));ctx.stroke();};
  for(const s of drawing.strands)for(let i=1;i<s.length;i++)line([s[i-1],s[i]],changedSegments.has(segmentKey(drawing,s[i-1],s[i]))?'#ffc87b':'#a7e7bd',7);
  for(const c of drawing.crossings){
    const p=xy[c.center];ctx.fillStyle='#102029';ctx.beginPath();ctx.arc(...p,12,0,Math.PI*2);ctx.fill();
    line(c.overPath,affected.has(c.id)?'#ffc87b':'#a7e7bd',7);
    if(affected.has(c.id)){ctx.strokeStyle='#ffc87b';ctx.lineWidth=1.3;ctx.setLineDash([4,5]);ctx.beginPath();ctx.arc(...p,21,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);}
    if(labels){ctx.fillStyle='#dbe6e8';ctx.font='13px system-ui';ctx.fillText(String(c.id),p[0]+17,p[1]-17);}
  }
}
