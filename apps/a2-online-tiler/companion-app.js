import {tiles} from './companions.js';
import {kite} from './companion-model.js';

const $=id=>document.getElementById(id);
const ns='http://www.w3.org/2000/svg';
function svg(tag,attrs) {
  const e=document.createElementNS(ns,tag);
  for(const [key,value] of Object.entries(attrs)) e.setAttribute(key,value);
  return e;
}
const xy=([x,y])=>[x+y/2,-y*Math.sqrt(3)/2];
const points=loop=>loop.map(p=>xy(p).join(',')).join(' ');
function bounds(coords,pad) {
  const flat=coords.map(xy),xs=flat.map(p=>p[0]),ys=flat.map(p=>p[1]);
  const x=Math.min(...xs),y=Math.min(...ys);
  return [x-pad,y-pad,Math.max(...xs)-x+2*pad,Math.max(...ys)-y+2*pad].join(' ');
}
const selected=new Set(['hat','turtle','K6-074']);
const catalog=new Map(tiles.map(t=>[t.id,t]));
const history=new Map();
let worker=null,frame=null,config=null,outline=[],grid=[];
const getLearning=()=>document.querySelector('input[name=mode]:checked').value==='learn';
function settings() {
  return {ids:tiles.filter(t=>selected.has(t.id)).map(t=>t.id),first:$('first').value,
    radius:Number($('radius').value),seed:$('seed').valueAsNumber,learning:getLearning()};
}
function key(c) {return JSON.stringify([c.ids,c.first,c.radius,c.seed]);}
function controls() {
  $('stop').disabled=!worker;
  $('run').disabled=!!worker || !selected.size || !$('seed').checkValidity();
  $('showMarks').disabled=!getLearning();
  $('modeInfo').textContent=getLearning()?'Starts blank. Failed branches can add certified signed values.':'Uses the unmarked point values.';
}
function library() {
  const first=$('first').value;
  $('first').replaceChildren();
  for(const t of tiles) {
    const el=document.querySelector('[data-tile="'+t.id+'"]');
    el.setAttribute('aria-pressed',String(selected.has(t.id)));
    if(selected.has(t.id)) $('first').add(new Option(t.name,t.id));
  }
  if(selected.has(first)) $('first').value=first;
}
for(const tile of tiles) {
  const b=document.createElement('button');
  b.className='piece'; b.dataset.tile=tile.id;
  b.title=tile.name+(tile.name==='Trefoil'?' (K6-074)':'')+' · '+tile.cells.length+' kites';
  const icon=svg('svg',{viewBox:bounds(tile.loop,.4),'aria-hidden':true});
  icon.append(svg('polygon',{points:points(tile.loop),fill:tile.color,stroke:'#4f605a','stroke-width':.12}));
  b.append(icon,document.createTextNode(tile.name));
  b.onclick=()=>{selected.has(tile.id)?selected.delete(tile.id):selected.add(tile.id);library();reset();};
  $('picker').append(b);
}
function boardGeometry(radius) {
  const edges=new Map(),cells=[];
  for(let h=-radius;h<=radius;h++) for(let k=Math.max(-radius,-radius-h);k<=Math.min(radius,radius-h);k++) {
    for(let s=0;s<6;s++) {
      const {corners}=kite(h,k,s);cells.push(corners);
      corners.forEach((a,i)=>{
        const b=corners[(i+1)%4],id=[String(a),String(b)].sort().join('|');
        if(edges.has(id)) edges.delete(id);else edges.set(id,[a,b]);
      });
    }
  }
  grid=cells;outline=[...edges.values()];
}
function render() {
  const scene=$('board'),placements=frame?.placements??[];
  $('markLegend').hidden=!(getLearning() && $('showMarks').checked && frame?.assignments);
  const loops=placements.map(p=>p.loop);
  scene.setAttribute('viewBox',bounds([...outline.flat(),...loops.flat()],1.25));
  const group=svg('g',{}),add=(tag,attrs)=>group.append(svg(tag,attrs));
  for(const cell of grid) add('polygon',{points:points(cell),fill:'#f8f9f2',stroke:'#d6ddd1','stroke-width':.045});
  for(const p of placements) add('polygon',{points:points(p.loop),fill:catalog.get(p.tile).color,stroke:'#314a42','stroke-width':.085,'data-piece':p.tile});
  for(const [a,b] of outline) add('polyline',{points:points([a,b]),fill:'none',stroke:'#466354','stroke-width':.075,'stroke-dasharray':'.24 .16'});
  if(getLearning() && $('showMarks').checked) {
    const done=new Set();
    for(const p of placements) for(const [x,y,axis,value] of p.marks) {
      const id=[x,y,axis,value].join();
      if(done.has(id)) continue;
      done.add(id);
      const dir=[[2,-1],[-1,2],[-1,-1]][axis],d=dir.map(n=>n*.20);
      add('polyline',{points:points([[x-d[0],y-d[1]],[x+d[0],y+d[1]]]),
        stroke:value>0?'#174a99':'#ae332f','stroke-width':.13,'stroke-linecap':'round','data-mark':value});
    }
  }
  scene.replaceChildren(group);
  for(const [el,value] of Object.entries({count:placements.length,nodes:frame?.nodes,backtracks:frame?.backtracks,marks:frame?.assignments})) $(el).textContent=(value??0).toLocaleString();
}
function halt() {worker?.terminate();worker=null;controls();}
function reset() {
  halt();config=settings();boardGeometry(config.radius);
  const tile=catalog.get(config.first);
  frame={placements:tile?[{tile:tile.id,loop:tile.loop,marks:[]}]:[]};
  $('status').textContent=selected.size?'Ready':'Select a tile';
  $('progress').textContent='';$('comparison').textContent='';controls();render();
}
function start() {
  if(!$('seed').reportValidity() || !selected.size) return;
  reset();
  const w=new Worker(new URL('./companion-worker.js',import.meta.url),{type:'module'});
  worker=w;controls();$('status').textContent='Searching';
  w.onerror=e=>{if(worker===w){halt();$('status').textContent='Search error';$('progress').textContent=e.message;}};
  w.onmessage=({data})=>{
    if(worker!==w) return;
    if(data.status==='error') {halt();$('status').textContent='Search error';$('progress').textContent=data.message;return;}
    frame=data;render();
    $('progress').textContent='Ring '+data.ring+' of '+config.radius;
    $('status').textContent=({searching:'Searching',ring:'Expanding board',revised:'Marking updated',
      covered:'Board covered',unknown:'Attempt limit reached',exhausted:'Search exhausted'})[data.status];
    if(['covered','unknown','exhausted'].includes(data.status)) {
      halt();
      if(data.status==='covered') {
        const results=history.get(key(config))??{};
        results[config.learning?'learn':'base']=data.backtracks;history.set(key(config),results);
        if(results.base!==undefined && results.learn!==undefined)
          $('comparison').textContent='Same board and seed · Base GCTS '+results.base.toLocaleString()+' backtracks · Learning '+results.learn.toLocaleString()+' backtracks.';
      }
    }
  };
  w.postMessage(config);
}
for(const r of document.querySelectorAll('input[name=mode]')) r.onchange=reset;
for(const id of ['first','radius']) $(id).onchange=reset;
$('seed').oninput=reset;
$('showMarks').onchange=render;
$('run').onclick=start;
$('stop').onclick=()=>{halt();$('status').textContent='Stopped';};
library();start();
