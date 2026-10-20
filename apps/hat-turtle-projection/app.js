const $ = id => document.getElementById(id);
const canvas = $('scene'), ctx = canvas.getContext('2d', {alpha:false});
const TAU = 2*Math.PI, SQRT3 = Math.sqrt(3), HALFROOT3 = SQRT3/2;
const colors={H1:'#355e69',H:'#a7c5c1',T:'#ecd8ae',P:'#c4d3b7',F:'#e3b99d'};
const state={morph:0,phase:0,playing:!matchMedia('(prefers-reduced-motion: reduce)').matches,lifted:false,zoom:16,panX:0,panY:0,speed:1,selected:0,highlight:true};
let data, model, screenX, screenY, screenZ, centers, fitScale=1, width=1, height=1, dpr=1, lastTime=0, lastDraw=0, visible=[];
let drag=null, dirty=true;
const theta = () => Math.PI/3-state.morph*Math.PI/6;
function project4(u,v,s,t,c,si,lift){
 const x=c*u+si*s, y=c*v+si*t;
 if(!lift)return [x,y,0];
 const z=(-si*(u+v)+c*(s+t))/Math.SQRT2;
 const angle=.54;
 return [x,Math.cos(angle)*y-Math.sin(angle)*z,Math.sin(angle)*y+Math.cos(angle)*z];
}
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
 resize();$('loading').hidden=true;
}
function resize(){const r=canvas.getBoundingClientRect();width=r.width;height=r.height;dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
 if(model){let maxX=0,maxY=0;for(const angle of [Math.PI/6,Math.PI/4,Math.PI/3])for(let i=0;i<model.length;i+=4){const p=project4(...model.subarray(i,i+4),Math.cos(angle),Math.sin(angle),false);maxX=Math.max(maxX,Math.abs(p[0]));maxY=Math.max(maxY,Math.abs(p[1]));}fitScale=Math.min((width-40)/(2*maxX),(height-40)/(2*maxY));}dirty=true;}
function polygonPath(ids){ctx.beginPath();ctx.moveTo(screenX[ids[0]],screenY[ids[0]]);for(let i=1;i<14;i++)ctx.lineTo(screenX[ids[i]],screenY[ids[i]]);ctx.closePath();}
function draw(){if(!model)return;const angle=theta(),c=Math.cos(angle),s=Math.sin(angle),scale=fitScale*state.zoom,ox=width/2+state.panX,oy=height/2+state.panY;
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
$('play').onclick=()=>setPlaying(!state.playing);
$('morph').addEventListener('input',e=>{const value=Number(e.target.value)/1000;setPlaying(false);setMorph(value);});
$('hat').onclick=()=>{setPlaying(false);setMorph(0);};$('turtle').onclick=()=>{setPlaying(false);setMorph(1);};$('midpoint').onclick=()=>{setPlaying(false);setMorph(.5);};
$('plane').onclick=()=>setMode(false);$('lift').onclick=()=>setMode(true);
$('speed').onchange=e=>{state.speed=Number(e.target.value);};$('highlight').onchange=e=>{state.highlight=e.target.checked;dirty=true;};
$('zoom-in').onclick=()=>zoomBy(1.35);$('zoom-out').onclick=()=>zoomBy(1/1.35);
$('fit').onclick=()=>{state.zoom=1;state.panX=0;state.panY=0;dirty=true;};$('reset').onclick=()=>{state.zoom=16;state.panX=0;state.panY=0;dirty=true;};
$('about-toggle').onclick=()=>{const show=$('about').hidden;$('about').hidden=!show;$('about-toggle').setAttribute('aria-expanded',show);};
canvas.addEventListener('wheel',e=>{e.preventDefault();const r=canvas.getBoundingClientRect();zoomBy(Math.exp(-e.deltaY*.001),e.clientX-r.left,e.clientY-r.top);},{passive:false});
canvas.addEventListener('pointerdown',e=>{if(drag)return;canvas.setPointerCapture(e.pointerId);drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY};});
canvas.addEventListener('pointermove',e=>{if(!drag||e.pointerId!==drag.id)return;state.panX+=e.clientX-drag.x;state.panY+=e.clientY-drag.y;drag.x=e.clientX;drag.y=e.clientY;dirty=true;});
canvas.addEventListener('pointerup',e=>{if(!drag||e.pointerId!==drag.id)return;const click=Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)<6;drag=null;if(click&&data){const r=canvas.getBoundingClientRect();for(let i=visible.length-1;i>=0;i--){const id=visible[i].id;if(contains(data.tiles[id],e.clientX-r.left,e.clientY-r.top)){state.selected=id;state.highlight=true;$('highlight').checked=true;dirty=true;break;}}}});
canvas.addEventListener('pointercancel',()=>{drag=null;});
window.addEventListener('keydown',e=>{if(['INPUT','SELECT','BUTTON','A'].includes(document.activeElement.tagName))return;if(e.code==='Space'){e.preventDefault();setPlaying(!state.playing);}if(e.key==='ArrowLeft'){setPlaying(false);setMorph(state.morph-.025);}if(e.key==='ArrowRight'){setPlaying(false);setMorph(state.morph+.025);}});
new ResizeObserver(resize).observe(canvas);
// Expose only the visualization state for reproducible inspection.
window.projectionDemo={state,setMorph,setMode,setPlaying,get metadata(){return data?.metadata;},get visibleCount(){return visible.length;}};
setPlaying(state.playing);requestAnimationFrame(frame);
try{const response=await fetch('patch.json');if(!response.ok)throw Error(`Patch download failed (${response.status})`);data=await response.json();prepare();}catch(error){$('loading').textContent='The tiling could not load. Please reload the page.';console.error(error);}
