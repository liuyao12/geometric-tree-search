import { parse, canonical, count, solve, examples } from './engine.mjs';
import { latticeLoop, gridLoop, regularProjection } from './projection.mjs';
const $ = id => document.getElementById(id);
let projection = null, result = null, frames = [], timer = null;
function clearMovie() { if(timer) clearInterval(timer); timer = null; $('play').textContent = 'Play seams'; result = null; frames = []; $('play').disabled = true; $('download').disabled = true; $('frame').max = 0; $('frame').value = 0; $('tiles').replaceChildren(); }
function drawProjection() {
  const c = $('projection'), ctx = c.getContext('2d'); ctx.clearRect(0,0,c.width,c.height);
  if (!projection) { ctx.fillStyle='#a5b8bf';ctx.font='18px system-ui';ctx.fillText('No lattice lift supplied for this diagram.',35,210);return; }
  const [a,b,d]=projection.direction,un=Math.hypot(a,b),vn=un*Math.hypot(a,b,d),norm=p=>[p[0]/un,p[1]/vn];
  const xy=projection.xy.map(norm),crossings=projection.crossings.map(x=>({...x,xy:norm(x.xy)})), xs=xy.map(p=>p[0]),ys=xy.map(p=>p[1]),minX=Math.min(...xs),minY=Math.min(...ys),dx=Math.max(...xs)-minX,dy=Math.max(...ys)-minY;
  const scale=Math.min(560/Math.max(1,dx),340/Math.max(1,dy)), trans=p=>[340+(p[0]-minX-dx/2)*scale,220-(p[1]-minY-dy/2)*scale];
  ctx.strokeStyle='#a7e7bd';ctx.lineWidth=5;ctx.lineJoin='round';ctx.lineCap='round';ctx.beginPath();xy.forEach((p,i)=>{const q=trans(p);i?ctx.lineTo(...q):ctx.moveTo(...q)});ctx.closePath();ctx.stroke();
  for(const x of crossings){const edge=x.iOver?x.i:x.j,p=trans(x.xy),a=trans(xy[edge]),b=trans(xy[(edge+1)%xy.length]),len=Math.hypot(b[0]-a[0],b[1]-a[1]),v=[(b[0]-a[0])/len,(b[1]-a[1])/len];
    for(const [color,width]of[['#102029',14],['#a7e7bd',5]]){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();ctx.moveTo(p[0]-v[0]*10,p[1]-v[1]*10);ctx.lineTo(p[0]+v[0]*10,p[1]+v[1]*10);ctx.stroke();}}
}
function drawSeam(word) {
  const c=$('seam'),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);ctx.font='16px system-ui';ctx.textAlign='center';
  if(!word.length){ctx.strokeStyle='#a7e7bd';ctx.lineWidth=5;ctx.beginPath();ctx.ellipse(340,215,130,100,0,0,Math.PI*2);ctx.stroke();ctx.fillStyle='#a7e7bd';ctx.fillText('Unknot diagram',340,365);return;}
  const ids=[...new Set(word.map(x=>x.id))],centers=new Map(ids.map((id,i)=>[id,[340+140*Math.cos(i*2*Math.PI/ids.length-.8),215+130*Math.sin(i*2*Math.PI/ids.length-.8)]]));
  function port(x,out){const [cx,cy]=centers.get(x.id);return x.over?[cx+(out?26:-26),cy]:[cx,cy+(out? -26*x.sign:26*x.sign)];}
  ctx.strokeStyle='#688797';ctx.lineWidth=2;
  word.forEach((x,i)=>{const next=word[(i+1)%word.length],a=port(x,true),b=port(next,false);ctx.beginPath();ctx.moveTo(...a);const ca=[a[0]+(a[0]-centers.get(x.id)[0])*2,a[1]+(a[1]-centers.get(x.id)[1])*2],cb=[b[0]+(b[0]-centers.get(next.id)[0])*2,b[1]+(b[1]-centers.get(next.id)[1])*2];ctx.bezierCurveTo(...ca,...cb,...b);ctx.stroke();});
  for(const id of ids){const [x,y]=centers.get(id);ctx.fillStyle='#223642';ctx.beginPath();ctx.arc(x,y,29,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#7198a9';ctx.lineWidth=3;ctx.beginPath();ctx.moveTo(x,y-24);ctx.lineTo(x,y+24);ctx.stroke();ctx.strokeStyle='#223642';ctx.lineWidth=11;ctx.beginPath();ctx.moveTo(x-24,y);ctx.lineTo(x+24,y);ctx.stroke();ctx.strokeStyle='#a7e7bd';ctx.lineWidth=4;ctx.stroke();ctx.fillStyle='#eee9df';ctx.fillText(`${id}${word.find(q=>q.id===id).sign>0?'+':'−'}`,x,y+52);}
}
function preset() {
  clearMovie();projection=null;const name=$('example').value;
  if(['curl','double','trefoil'].includes(name)){const n=name==='curl'?2:name==='double'?3:5,k=name==='trefoil'?2:1;projection=regularProjection(gridLoop(Array.from({length:n},(_,i)=>i),Array.from({length:n},(_,i)=>(i+k)%n)));$('source').value=projection.canonical;}
  else if(name==='bigon')$('source').value=examples.bigon;
  else if(name==='triangle')$('source').value='O1+ O2- O3+ U1+ U2- U3+';
  $('target').value='';$('cap').value=Math.max(3,count(parse($('source').value)));drawProjection();drawSeam(parse($('source').value));
  $('projection-caption').textContent=projection?(projection.direction.every(x=>x===1)?'Exact body-diagonal source projection.':'Body-diagonal view is degenerate here; a nearby rational direction supplies a regular source diagram.'):'Signed diagram input; a spatial realization is a future step.';
  $('status').textContent='Ready';$('summary').textContent='Run a search to inspect its graph, learning cost, and certificate.';
}
function showFrame(i){if(!frames.length)return;$('frame').value=i;drawSeam(frames[i]);$('frame-label').textContent=i?`Tile ${i}: ${result.certificate.steps[i-1].kind}`:'Source';[...$('tiles').children].forEach((el,j)=>el.classList.toggle('active',j===i-1));}
function describe(r){const {certificate,selected,...summary}=r;return JSON.stringify({...summary,certificateTiles:certificate?.steps.length},null,2);}
async function run(compare=false) {
  clearMovie();$('run').disabled=true;$('compare').disabled=true;$('status').textContent='Building complete finite catalog…';
  await new Promise(resolve=>setTimeout(resolve,40));
  try{
    const source=parse($('source').value),target=parse($('target').value),options={depth:Number($('depth').value),crossingCap:Number($('cap').value),stateCap:1500,nodeCap:10000,episodes:12,seed:31};
    if(!projection||projection.canonical!==canonical(source)){projection=null;drawProjection();$('projection-caption').textContent='Signed diagram input; no lattice lift is supplied.';}
    const lanes=compare?['baseline','gcts','gcts+rl']:[$('lane').value],results=lanes.map(lane=>({lane,...solve(source,target,{...options,lane})}));
    result=results.find(x=>x.lane===$('lane').value)||results[0];
    $('status').textContent=result.status==='equivalent'?'Equivalent · replay verified':result.status==='inequivalent'?'Inequivalent · coloring obstruction':result.status==='exhausted-finite-search'?'Finite bounds exhausted · equivalence unknown':'Unknown · budget reached';
    $('summary').textContent=results.map(r=>`${r.lane}\n${describe(r)}`).join('\n\n');
    drawSeam(source);if(result.certificate){frames=[parse(result.certificate.source),...result.certificate.steps.map(x=>parse(x.after))];$('frame').max=frames.length-1;$('play').disabled=frames.length<2;$('download').disabled=false;
      for(const step of result.certificate.steps){const el=document.createElement('div');el.className='tile';el.textContent=`Type ${step.kind}`;$('tiles').append(el);}showFrame(0);}
  }catch(e){$('status').textContent='Input or bound error';$('summary').textContent=e.message;}
  finally{$('run').disabled=false;$('compare').disabled=false;}
}
$('example').addEventListener('change',preset);$('run').addEventListener('click',()=>run());$('compare').addEventListener('click',()=>run(true));
for(const id of ['source','target'])$(id).addEventListener('input',()=>{clearMovie();$('status').textContent='Input changed · run a new search';if(id==='source'){projection=null;drawProjection();try{drawSeam(parse($('source').value));}catch{}}});
$('frame').addEventListener('input',()=>showFrame(Number($('frame').value)));
$('play').addEventListener('click',()=>{if(timer){clearInterval(timer);timer=null;$('play').textContent='Play seams';return;}$('play').textContent='Pause';if(Number($('frame').value)===frames.length-1)showFrame(0);timer=setInterval(()=>{const i=Number($('frame').value)+1;if(i>=frames.length){clearInterval(timer);timer=null;$('play').textContent='Play seams';}else showFrame(i);},900);});
$('download').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(result.certificate,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='reidemeister-movie.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
$('import').addEventListener('change',async()=>{try{const file=$('import').files[0];if(!file)return;const data=JSON.parse(await file.text());projection=regularProjection(latticeLoop(data.vertices||data));clearMovie();$('example').value='custom';$('source').value=projection.canonical;$('cap').value=Math.max(3,count(projection.word));drawProjection();drawSeam(projection.word);$('projection-caption').textContent='Imported lattice loop; rational regular projection and signed planar diagram checked.';$('status').textContent='Imported';}catch(e){$('status').textContent='Import error';$('summary').textContent=e.message;}});
preset();
