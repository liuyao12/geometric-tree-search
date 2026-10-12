import { parse, canonical, count, solve, examples } from './engine.mjs';
import { latticeLoop, gridLoop, regularProjection } from './projection.mjs';
import { trefoilIdentification } from './cases.mjs';
import { planarDrawing, verifyDrawing, movieDrawings, drawKnot } from './drawing.mjs?v=readable-v1';
import { descriptions, drawMoveDetail } from './move-detail.mjs?v=readable-v1';
import { annularMovie, drawAnnular } from './annular-movie.mjs?v=readable-v1';
const $ = id => document.getElementById(id);
let projection=null,result=null,frames=[],timer=null,current=0;
const cache=new Map();
const crossingLabel=word=>`${count(word)} ${count(word)===1?'crossing':'crossings'}`;
function drawing(word){if(count(word)>8)throw Error('This viewer supports up to eight crossings. Try a simpler diagram or projection.');const key=JSON.stringify(word);if(!cache.has(key)){const d=planarDrawing(word);verifyDrawing(d);cache.set(key,d);}return cache.get(key);}
function stop(){if(timer)clearInterval(timer);timer=null;$('play').textContent='Play moves';}
function clearMovie(){stop();result=null;frames=[];current=0;$('play').disabled=true;$('download').disabled=true;$('previous').disabled=true;$('next').disabled=true;$('frame').max=0;$('frame').value=0;$('tiles').replaceChildren();$('move-panel').hidden=true;$('move-change').textContent='';$('move-description').textContent='';}
function showPair(source,target){drawKnot($('before'),drawing(source));drawKnot($('after'),drawing(target));$('before-label').textContent=`Starting knot · ${crossingLabel(source)}`;$('after-label').textContent=`Target knot · ${crossingLabel(target)}`;$('move-heading').textContent='Find a sequence of moves';$('frame-label').textContent='Starting knot and target';}
function showMove(i){if(!frames.length)return;current=Math.max(0,Math.min(frames.length-1,i));const f=frames[current],description=descriptions[f.kind];
  $('frame').value=current;$('frame-label').textContent=`Move ${current+1} of ${frames.length}`;$('before-label').textContent=`Before · ${crossingLabel(f.before.word)}`;$('after-label').textContent=`After · ${crossingLabel(f.after.word)}`;
  const render=f.before.annular?drawAnnular:drawKnot;
  render($('before'),f.before,{affected:f.affected,changedStrands:f.beforeStrands,changedSegments:f.beforeSegments,labels:$('labels').checked});
  render($('after'),f.after,{affected:f.affected,changedStrands:f.afterStrands,changedSegments:f.afterSegments,labels:$('labels').checked});
  $('move-heading').textContent=description.title;$('move-description').textContent=description.text;$('move-type').textContent=`Reidemeister ${f.kind.replace(/[+−]/g,'')}`;$('move-change').textContent=description.change;
  $('move-hint').textContent=f.before.annular?'Green parts stay in place in the large panels. Only the amber paths change. The small drawing shows this type of move in isolation.':'The small drawing shows this type of move in isolation. The large panels show the actual knot; their paths may shift between drawings.';$('move-panel').hidden=false;drawMoveDetail($('detail'),f.kind);$('previous').disabled=current===0;$('next').disabled=current===frames.length-1;
  [...$('tiles').children].forEach((el,j)=>{el.classList.toggle('active',j===current);el.setAttribute('aria-current',j===current?'step':'false');});
}
function preset(){clearMovie();projection=null;const name=$('example').value;
  if(name==='identification')$('source').value=trefoilIdentification.source;
  else if(['curl','double','trefoil'].includes(name)){const n=name==='curl'?2:name==='double'?3:5,k=name==='trefoil'?2:1;projection=regularProjection(gridLoop(Array.from({length:n},(_,i)=>i),Array.from({length:n},(_,i)=>(i+k)%n)));$('source').value=projection.canonical;}
  else if(name==='bigon')$('source').value=examples.bigon;
  else if(name==='triangle')$('source').value='O1+ O2- O3+ U1+ U2- U3+';
  $('target').value=name==='identification'?trefoilIdentification.target:'';$('depth').value=name==='identification'||name==='triangle'?3:2;
  const source=parse($('source').value),target=parse($('target').value);$('cap').value=Math.max(3,count(source));showPair(source,target);$('status').textContent='Ready';$('summary').textContent='Search details will appear here.';
}
function describe(r){const {certificate,selected,...summary}=r;return JSON.stringify({...summary,certificateTiles:certificate?.steps.length},null,2);}
async function run(compare=false){clearMovie();$('run').disabled=true;$('compare').disabled=true;$('status').textContent='Finding moves…';await new Promise(resolve=>setTimeout(resolve,40));
  try{const source=parse($('source').value),target=parse($('target').value),options={depth:Number($('depth').value),crossingCap:Number($('cap').value),stateCap:1500,nodeCap:10000,episodes:12,seed:31};
    const lanes=compare?['baseline','gcts','gcts+rl']:[$('lane').value],results=lanes.map(lane=>({lane,...solve(source,target,{...options,lane})}));result=results.find(x=>x.lane===$('lane').value)||results[0];
    $('summary').textContent=results.map(r=>`${r.lane}\n${describe(r)}`).join('\n\n');showPair(source,target);
    if(result.certificate){frames=annularMovie(result.certificate)||movieDrawings(result.certificate);$('download').disabled=false;
      if(frames.length){$('status').textContent=`Same knot · ${frames.length} verified ${frames.length===1?'move':'moves'}`;$('frame').max=frames.length-1;$('play').disabled=frames.length<2;frames.forEach((f,j)=>{const button=document.createElement('button');button.className='tile';button.textContent=`${j+1}. ${descriptions[f.kind].title}`;button.addEventListener('click',()=>{stop();showMove(j);});$('tiles').append(button);});showMove(0);}
      else{$('status').textContent='Same diagram · no moves needed';$('move-heading').textContent='These diagrams already agree';}
    }else if(result.status==='inequivalent'){$('status').textContent='Different knots · coloring proof';$('move-heading').textContent='These knots cannot be transformed into each other';}
    else{$('status').textContent='No sequence found within these limits';$('move-heading').textContent='Try a longer sequence or a larger crossing limit';}
  }catch(e){$('status').textContent='Check the input';$('move-heading').textContent='Cannot draw or search this input';$('move-description').textContent=e.message;$('summary').textContent=e.message;}
  finally{$('run').disabled=false;$('compare').disabled=false;}
}
$('example').addEventListener('change',()=>{preset();if($('example').value!=='custom')run();});$('run').addEventListener('click',()=>run());$('compare').addEventListener('click',()=>run(true));
for(const id of ['source','target'])$(id).addEventListener('input',()=>{clearMovie();$('example').value='custom';$('status').textContent='Find moves for the new input';try{showPair(parse($('source').value),parse($('target').value));}catch{}});
$('frame').addEventListener('input',()=>{stop();showMove(Number($('frame').value));});$('previous').addEventListener('click',()=>{stop();showMove(current-1);});$('next').addEventListener('click',()=>{stop();showMove(current+1);});$('labels').addEventListener('change',()=>showMove(current));
$('play').addEventListener('click',()=>{if(timer){stop();return;}if(current===frames.length-1)showMove(0);$('play').textContent='Pause';timer=setInterval(()=>{if(current===frames.length-1)stop();else showMove(current+1);},2400);});
$('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(result.certificate,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='reidemeister-movie.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('import').addEventListener('change',async()=>{try{const file=$('import').files[0];if(!file)return;const data=JSON.parse(await file.text());projection=regularProjection(latticeLoop(data.vertices||data));clearMovie();$('example').value='custom';$('source').value=projection.canonical;$('cap').value=Math.max(3,count(projection.word));showPair(projection.word,parse($('target').value));$('status').textContent='Lattice knot imported · find moves';}catch(e){$('status').textContent='Import error';$('summary').textContent=e.message;}});
const requested=new URLSearchParams(location.search).get('example');if(requested&&[...$('example').options].some(x=>x.value===requested))$('example').value=requested;
preset();run();
