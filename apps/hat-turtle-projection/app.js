import {HALFROOT3, latticeToCartesian, relativeTile, reflectedFrameStats, steadyFrame, IDENTITY_FRAME, projectVertex} from './projection.js?v=2';
const $ = id => document.getElementById(id);
const canvas = $('scene'), ctx = canvas.getContext('2d', {alpha:false});
const TAU = 2*Math.PI;
const colors={H1:'#355e69',H:'#a7c5c1',T:'#ecd8ae',P:'#c4d3b7',F:'#e3b99d'};
const state={morph:0,phase:0,playing:!matchMedia('(prefers-reduced-motion: reduce)').matches,lifted:false,zoom:16,panX:0,panY:0,speed:1,selected:0,highlight:true,steady:true,single:false};
let data, model, screenX, screenY, screenZ, centers, fitScale=1, width=1, height=1, dpr=1, lastTime=0, lastDraw=0, visible=[];
let drag=null, dirty=true, frameStats, tileCoordinates, tileModel, tileSides, tileRadius=3;
const viewer=document.querySelector('.viewer');
const theta = () => Math.PI/3-state.morph*Math.PI/6;
function currentFrame(c,s){return state.steady&&frameStats?steadyFrame(frameStats,c,s):IDENTITY_FRAME;}
function project4(u,v,s,t,c,si,lift){return projectVertex(u,v,s,t,c,si,lift,activeFrame);}
let activeFrame=IDENTITY_FRAME;

function setMorph(value){state.morph=Math.max(0,Math.min(1,value));state.phase=Math.acos(1-2*state.morph);dirty=true;updateLabels();}
function setPlaying(value){state.playing=value;$('play-icon').textContent=value?'Ⅱ':'▶';$('play-text').textContent=value?'Pause':'Play';$('play').setAttribute('aria-label',value?'Pause animation':'Play animation');updateLabels();dirty=true;}
function setMode(value){state.lifted=value;$('plane').setAttribute('aria-pressed',!value);$('lift').setAttribute('aria-pressed',value);$('view-note').textContent=value?'A tilted view of the fixed lifted patch.':'Same tiles. Same neighbors.';dirty=true;}
function updateLabels(){const m=state.morph,shape=m<.015?'Hat':m>.985?'Turtle':Math.abs(m-.5)<.015?'Equal edges':'Hat → Turtle';$('shape-label').textContent=shape;$('morph').value=Math.round(m*1000);$('morph').style.setProperty('--progress',`${100*m}%`);$('morph').setAttribute('aria-valuetext',`${Math.round(m*100)} percent from Hat to Turtle`);$('position-label').textContent=state.playing?(Math.sin(state.phase)>=0?'Moving toward Turtle':'Moving toward Hat'):(shape==='Hat → Turtle'?'Paused between Hat and Turtle':shape);}
function prepare(){
 const n=data.vertices.length;model=new Float64Array(n*4);screenX=new Float64Array(n);screenY=new Float64Array(n);screenZ=new Float64Array(n);
 const mean=[0,0,0,0];
 for(let i=0;i<n;i++){const [p,q,r,s]=data.vertices[i],v=[p+q/2,HALFROOT3*q,HALFROOT3*r,r/2+s];for(let k=0;k<4;k++){model[4*i+k]=v[k];mean[k]+=v[k]/n;}}
 for(let i=0;i<n;i++)for(let k=0;k<4;k++)model[4*i+k]-=mean[k];
 centers=new Float64Array(data.tiles.length*4);let best=Infinity;
 for(let j=0;j<data.tiles.length;j++){for(const id of data.tiles[j])for(let k=0;k<4;k++)centers[4*j+k]+=model[4*id+k]/14;
 const v=project4(...centers.subarray(4*j,4*j+4),.5,HALFROOT3,false),dist=v[0]*v[0]+v[1]*v[1];if(dist<best){best=dist;state.selected=j;}}
 $('patch-info').textContent=`${data.tiles.length.toLocaleString()} tiles · drag to pan · scroll to zoom`;
 frameStats=reflectedFrameStats(centers,data.labels); prepareSingleTile(); resize(); $('loading').hidden=true; if(new URLSearchParams(location.search).get('view')==='tile')setDisplay(true);
}
function resize(){const r=canvas.getBoundingClientRect();width=r.width;height=r.height;dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
 if(model){let maxX=0,maxY=0;for(const angle of [Math.PI/6,Math.PI/4,Math.PI/3])for(let i=0;i<model.length;i+=4){const p=project4(...model.subarray(i,i+4),Math.cos(angle),Math.sin(angle),false);maxX=Math.max(maxX,Math.abs(p[0]));maxY=Math.max(maxY,Math.abs(p[1]));}fitScale=Math.min((width-40)/(2*maxX),(height-40)/(2*maxY));}dirty=true;}
function polygonPath(ids){ctx.beginPath();ctx.moveTo(screenX[ids[0]],screenY[ids[0]]);for(let i=1;i<14;i++)ctx.lineTo(screenX[ids[i]],screenY[ids[i]]);ctx.closePath();}
function draw(){if(!model)return; if(state.single){drawSingleTile();dirty=false;lastDraw=performance.now();return;}const angle=theta(),c=Math.cos(angle),s=Math.sin(angle),scale=fitScale*state.zoom,ox=width/2+state.panX,oy=height/2+state.panY;
 activeFrame=currentFrame(c,s);
 ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#e9ede3';ctx.fillRect(0,0,width,height);
 // One projection per shared vertex keeps adjoining boundaries identical.
 for(let i=0,j=0;i<model.length;i+=4,j++){const p=project4(model[i],model[i+1],model[i+2],model[i+3],c,s,state.lifted);screenX[j]=ox+p[0]*scale;screenY[j]=oy-p[1]*scale;screenZ[j]=p[2];}
 visible=[];
 const margin=5*scale;
 for(let j=0;j<data.tiles.length;j++){const p=project4(centers[j*4],centers[j*4+1],centers[j*4+2],centers[j*4+3],c,s,state.lifted);const x=ox+p[0]*scale,y=oy-p[1]*scale;if(x+margin>=0&&x-margin<=width&&y+margin>=0&&y-margin<=height)visible.push({id:j,z:p[2]});}
 if(state.lifted)visible.sort((a,b)=>a.z-b.z);
 ctx.lineJoin='round';ctx.lineWidth=Math.max(.4,Math.min(.85,scale*.055));ctx.strokeStyle='#365650a0';
 for(const tile of visible){polygonPath(data.tiles[tile.id]);ctx.fillStyle=colors[data.labels[tile.id]];ctx.fill();ctx.stroke();}
 if(state.highlight){polygonPath(data.tiles[state.selected]);ctx.lineWidth=3;ctx.strokeStyle='#c45430';ctx.stroke();ctx.lineWidth=1;ctx.strokeStyle='#fff8e6';ctx.stroke();}
 // Orientation guide in lifted view, kept separate from the tiling geometry.
 if(state.lifted){ctx.font='10px ui-sans-serif, system-ui';ctx.fillStyle='#49665d';ctx.textAlign='left';ctx.fillText('Lifted view · projected tiles can overlap',18,89);}
 dirty=false;lastDraw=performance.now();
}
function frame(time){const dt=lastTime?Math.min(time-lastTime,100):0;lastTime=time;
 if(state.playing&&model){state.phase=(state.phase+dt/22000*TAU*state.speed)%TAU;state.morph=(1-Math.cos(state.phase))/2;dirty=true;}
 if(dirty&&time-lastDraw>=30){if(state.playing)updateLabels();draw();}requestAnimationFrame(frame);
}
function zoomBy(factor,x=width/2,y=height/2){const old=state.zoom;state.zoom=Math.max(.25,Math.min(80,old*factor));factor=state.zoom/old;state.panX=x-width/2-(x-width/2-state.panX)*factor;state.panY=y-height/2-(y-height/2-state.panY)*factor;dirty=true;}
function contains(ids,x,y){let inside=false;for(let i=0,j=13;i<14;j=i++){const ax=screenX[ids[i]],ay=screenY[ids[i]],bx=screenX[ids[j]],by=screenY[ids[j]];if((ay>y)!==(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)inside=!inside;}return inside;}
function updateFrameNote(){
 $('frame-note').textContent=state.steady?'Overall rotation and spacing stabilized; small local shifts remain.':'Fixed edge directions; the patch is free to turn and change spacing.';
}
function setDisplay(single){
 state.single=single;
 $('patch-view').setAttribute('aria-pressed',!single);$('tile-view').setAttribute('aria-pressed',single);
 $('scene').hidden=single;$('single-tile').hidden=!single;$('coordinate-note').hidden=!single;
 $('patch-note').hidden=single;$('camera-tools').hidden=single;
 viewer.classList.toggle('single-display',single);
 $('patch-info').textContent=single?'Fourteen vertices · labels stay fixed during the animation':`${data?.tiles.length.toLocaleString()} tiles · drag to pan · scroll to zoom`;
 dirty=true;
}
function typesetCoordinates(){
 if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([$('coordinate-labels'),$('coordinate-note')]).then(()=>{dirty=true;}).catch(console.error);
 else $('MathJax-script').addEventListener('load',()=>window.MathJax.startup.promise.then(typesetCoordinates),{once:true});
}
function prepareSingleTile(){
 if(!data)return;
 const host=$('coordinate-labels');
 window.MathJax?.typesetClear?.([host]);host.replaceChildren();
 tileCoordinates=relativeTile(data.vertices,data.tiles[state.selected]);
 tileModel=tileCoordinates.map(latticeToCartesian);
 const average=[0,0,0,0];tileModel.forEach(p=>p.forEach((x,k)=>average[k]+=x/14));
 tileModel=tileModel.map(p=>p.map((x,k)=>x-average[k]));
 const mid=tileModel.map(p=>projectVertex(...p,Math.SQRT1_2,Math.SQRT1_2,false));
 const sorted=mid.map((p,i)=>({i,x:p[0],y:p[1]})).sort((a,b)=>a.x-b.x);
 tileSides=[sorted.slice(0,7),sorted.slice(7)].map(side=>side.sort((a,b)=>b.y-a.y).map(p=>p.i));
 const NS='http://www.w3.org/2000/svg';$('single-leaders').replaceChildren();$('single-points').replaceChildren();
 for(let i=0;i<14;i++){
  const label=document.createElement('div');label.className='vertex-label';label.dataset.vertex=i;
  const prefix=document.createElement('span');prefix.className='coordinate-prefix';prefix.textContent=String.raw`\(\mathrm{v}_{${i}}=\)`;
  const tuple=document.createElement('span');tuple.textContent=String.raw`\((${tileCoordinates[i].join(',')})\)`;label.append(prefix,tuple);label.title=`Vertex ${i}`;
  host.append(label);
  const line=document.createElementNS(NS,'line');line.id=`leader-${i}`;$('single-leaders').append(line);
  const point=document.createElementNS(NS,'circle');point.id=`vertex-${i}`;point.setAttribute('r',i===0?'4.5':'3.2');$('single-points').append(point);
 }
 tileRadius=0;
 for(let j=0;j<=20;j++){const a=Math.PI/6+j/20*Math.PI/6,c=Math.cos(a),s=Math.sin(a),f=currentFrame(c,s);for(const p of tileModel){const q=projectVertex(...p,c,s,false,{...f,tx:0,ty:0});tileRadius=Math.max(tileRadius,Math.hypot(q[0],q[1]));}}
 typesetCoordinates();dirty=true;
}
function drawSingleTile(){
 const rect=viewer.getBoundingClientRect(),w=rect.width,h=rect.height;
 const labelWidth=w<500?76:150,gutter=labelWidth+(w<500?23:30);
 const sc=Math.min(Math.max(60,w-2*gutter)/(2*tileRadius),(h-150)/(2*tileRadius))*.91;
 const c=Math.cos(theta()),s=Math.sin(theta()),f={...currentFrame(c,s),tx:0,ty:0};
 const points=tileModel.map(p=>{const q=projectVertex(...p,c,s,state.lifted,f);return [w/2+q[0]*sc,h/2+25-q[1]*sc];});
 $('single-svg').setAttribute('viewBox',`0 0 ${w} ${h}`);
 $('single-path').setAttribute('d',points.map((p,i)=>`${i?'L':'M'}${p[0]},${p[1]}`).join(' ')+' Z');
 $('single-path').style.fill=colors[data.labels[state.selected]];
 tileSides.forEach((side,k)=>side.forEach((i,row)=>{
  const y=88+row*(h-128)/6,inside=k===0?gutter-13:w-gutter+13;
  const label=$('coordinate-labels').children[i];label.style.top=`${y}px`;label.style.width=`${labelWidth}px`;label.style.left=k===0?'12px':'auto';label.style.right=k===1?'12px':'auto';label.style.textAlign=k===0?'right':'left';
  const line=$(`leader-${i}`);line.setAttribute('x1',points[i][0]);line.setAttribute('y1',points[i][1]);line.setAttribute('x2',inside);line.setAttribute('y2',y);
  const circle=$(`vertex-${i}`);circle.setAttribute('cx',points[i][0]);circle.setAttribute('cy',points[i][1]);
 }));
}
$('play').onclick=()=>setPlaying(!state.playing);
$('morph').addEventListener('input',e=>{const value=Number(e.target.value)/1000;setPlaying(false);setMorph(value);});
$('hat').onclick=()=>{setPlaying(false);setMorph(0);};$('turtle').onclick=()=>{setPlaying(false);setMorph(1);};$('midpoint').onclick=()=>{setPlaying(false);setMorph(.5);};
$('plane').onclick=()=>setMode(false);$('lift').onclick=()=>setMode(true);
$('patch-view').onclick=()=>setDisplay(false);$('tile-view').onclick=()=>setDisplay(true);
$('steady').onchange=e=>{state.steady=e.target.checked;updateFrameNote();dirty=true;};
$('speed').onchange=e=>{state.speed=Number(e.target.value);};$('highlight').onchange=e=>{state.highlight=e.target.checked;dirty=true;};
$('zoom-in').onclick=()=>zoomBy(1.35);$('zoom-out').onclick=()=>zoomBy(1/1.35);
$('fit').onclick=()=>{state.zoom=1;state.panX=0;state.panY=0;dirty=true;};$('reset').onclick=()=>{state.zoom=16;state.panX=0;state.panY=0;dirty=true;};
$('about-toggle').onclick=()=>{const show=$('about').hidden;$('about').hidden=!show;$('about-toggle').setAttribute('aria-expanded',show);};
canvas.addEventListener('wheel',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();zoomBy(Math.exp(-e.deltaY*.001),e.clientX-r.left,e.clientY-r.top);},{passive:false});
canvas.addEventListener('pointerdown',e=>{if(drag)return;canvas.setPointerCapture(e.pointerId);drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};});
canvas.addEventListener('pointermove',e=>{if(!drag||e.pointerId!==drag.id)return;state.panX+=e.clientX-drag.x;state.panY+=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;dirty=true;});
canvas.addEventListener('pointerup',e=>{if(!drag||e.pointerId!==drag.id)return;const click=Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)<6;drag=null;if(click&&data){const r=canvas.getBoundingClientRect();for(let i=visible.length-1;i>=0;i--){const id=visible[i].id;if(contains(data.tiles[id],e.clientX-r.left,e.clientY-r.top)){state.selected=id;prepareSingleTile();state.highlight=true;$('highlight').checked=true;dirty=true;break;}}}});
canvas.addEventListener('pointercancel',()=>{drag=null;});
window.addEventListener('keydown',e=>{if(['INPUT','SELECT','BUTTON','A'].includes(document.activeElement.tagName))return;if(e.code==='Space'){e.preventDefault();setPlaying(!state.playing);}if(e.key==='ArrowLeft'){setPlaying(false);setMorph(state.morph-.025);}if(e.key==='ArrowRight'){setPlaying(false);setMorph(state.morph+.025);}});
new ResizeObserver(resize).observe(canvas);
// Expose only the visualization state for reproducible inspection.
window.projectionDemo={state,setMorph,setMode,setPlaying,get metadata(){return data?.metadata;},get visibleCount(){return visible.length;},get tileCoordinates(){return tileCoordinates;},get frame(){return currentFrame(Math.cos(theta()),Math.sin(theta()));},setDisplay};
setPlaying(state.playing);requestAnimationFrame(frame);
try{const response=await fetch('patch.json');if(!response.ok)throw Error(`Patch download failed (${response.status})`);data=await response.json();prepare();}catch(error){$('loading').textContent='The tiling could not load. Please reload the page.';console.error(error);}
