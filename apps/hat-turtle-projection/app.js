import {HALFROOT3, latticeToCartesian, relativeTile, reflectedFrameStats, steadyFrame, IDENTITY_FRAME, projectVertex} from './projection.js?v=4';
import {FAMILY_STOPS, familyAngle, certifiedMarks, coefficients, projectPerspective, latticeBasis, namedAlignment} from './perspectives.js?v=4';
import {matrixPerspective, projectMatrix} from './matrix-perspectives.js?v=4';
import {createParameterMap} from './parameter-map.js?v=4';
import {ORIGIN_TILE, originFromMarks, originPlaneFrame, planeManhattanDistance, distanceColor} from './vertex-distance.js?v=8';
import {whiteMarkAlignment, rotateFrame} from './white-mark-alignment.js?v=6';
const $ = id => document.getElementById(id);
const canvas = $('scene'), ctx = canvas.getContext('2d', {alpha:false});
const TAU = 2*Math.PI;
const colors={H1:'#355e69',H:'#a7c5c1',T:'#ecd8ae',P:'#c4d3b7',F:'#e3b99d'};
const state={morph:1/3,phase:Math.acos(1/3),explore:false,phi:0,exact:{xn:3,yn:0,q:1},matrix:null,playing:!matchMedia('(prefers-reduced-motion: reduce)').matches,lifted:false,zoom:16,panX:0,panY:0,speed:1,selected:0,highlight:true,steady:true,single:false,framing:'marks'};
let data, marks, markModels, modelMean=[0,0,0,0], model, screenX, screenY, screenZ, centers, fitScale=1, width=1, height=1, dpr=1, lastTime=0, lastDraw=0, visible=[];
let drag=null, dirty=true, frameStats, tileCoordinates, tileModel, tileSides, tileRadius=3, selectedAnchor=null, whiteAlignment={re:1,im:0}, coordinateOrigin, shiftedVertices, vertexDistances, vertexColors, distanceMaximum=0;
const viewer=document.querySelector('.viewer');
const theta = () => familyAngle(state.morph);
function currentFrame(c,s){if(state.explore)return IDENTITY_FRAME;if(state.framing==='marks')return rotateFrame(originPlaneFrame(c,s,modelMean),whiteAlignment);return state.framing==='steady'&&frameStats?steadyFrame(frameStats,c,s):IDENTITY_FRAME;}
function weights(){return coefficients(state.morph,state.explore?state.phi:0,state.exact);}
function projected(point,w=weights(),f=activeFrame){if(state.matrix){const p=projectMatrix(point,state.matrix);return [p[0],p[1],0];}return projectPerspective(...point,w,f);}
function project4(u,v,s,t,c,si,lift){return projected([u,v,s,t],activeWeights,activeFrame);}
let activeFrame=IDENTITY_FRAME,activeWeights=weights();
const parameterMap=createParameterMap($('parameter-map'),setPerspective);

function setMorph(value,exact=null){state.morph=Math.max(0,Math.min(1,value));state.exact=exact;state.phase=Math.acos(1-2*state.morph);dirty=true;updateLabels();}
function setPlaying(value){state.playing=value;$('play-icon').textContent=value?'Ⅱ':'▶';$('play-text').textContent=value?'Pause':'Play';$('play').setAttribute('aria-label',value?'Pause animation':'Play animation');updateLabels();dirty=true;}
function setMode(value){
 state.explore=value;state.lifted=false;
 if(!value){state.phi=0;state.matrix=null;state.exact=null;for(const name of ['hat','turtle'])if(Math.abs(state.morph-FAMILY_STOPS[name])<1e-10)state.exact=namedAlignment(name).exact;}
 $('plane').setAttribute('aria-pressed',!value);$('lift').setAttribute('aria-pressed',value);
 $('perspective-controls').hidden=!value;$('framing').disabled=value;
 $('view-note').textContent=value?'Other projections can overlap or change tile shapes.':'Same tiles. Same neighbors.';
 updateMatrixControls();updateLabels();if(data){prepareSingleTile();resize();}dirty=true;
}
function shapeName(){if(state.matrix)return 'Four-parameter view';if(state.explore&&Math.abs(state.phi)>1e-10)return 'Other perspective';
 for(const [name,m] of Object.entries(FAMILY_STOPS))if(Math.abs(state.morph-m)<.004)return {chevron:'Chevron',hat:'Hat',equal:'Equal edges',turtle:'Turtle',comet:'Comet'}[name];return 'Tile family';}
function updateLabels(){const m=state.morph,shape=shapeName();$('shape-label').textContent=shape;$('morph').value=Math.round(m*3000);$('morph').style.setProperty('--progress',`${100*m}%`);$('morph').setAttribute('aria-valuetext',`${shape}; ${Math.round(100*m)} percent from Chevron to Comet`);
 $('position-label').textContent=state.playing?(Math.sin(state.phase)>=0?'Toward Comet':'Toward Chevron'):shape;
 $('rotation-value').textContent=`${Math.round(state.phi*180/Math.PI)} degrees`;$('relative-angle').value=state.phi*180/Math.PI;
 for(const name of ['hat','turtle','chevron','comet'])$(name).setAttribute('aria-pressed',!state.matrix&&Math.abs(state.phi)<1e-10&&Math.abs(m-FAMILY_STOPS[name])<1e-10);
 let example='';if(!state.matrix&&state.exact)for(const name of ['hat','turtle','aligned-c','aligned-a','aligned-b']){const p=namedAlignment(name);if(Math.abs(p.m-m)<1e-12&&Math.abs(p.phi-state.phi)<1e-12)example=name;}$('aligned-example').value=example;
 updateFrameNote();if(state.explore){parameterMap.draw({m,phi:state.phi});updateLatticeStatus();}
}
function prepare(){
 coordinateOrigin=originFromMarks(marks);
 shiftedVertices=data.vertices.map(p=>p.map((v,k)=>v-coordinateOrigin[k]));
 vertexDistances=shiftedVertices.map(planeManhattanDistance);distanceMaximum=Math.max(...vertexDistances);vertexColors=vertexDistances.map(distanceColor);
 $('distance-summary').textContent=`${data.vertices.length.toLocaleString()} shared vertices · maximum distance ${distanceMaximum.toFixed(3)} · colors stay with vertices`;
 const n=data.vertices.length;model=new Float64Array(n*4);screenX=new Float64Array(n);screenY=new Float64Array(n);screenZ=new Float64Array(n);
 const mean=[0,0,0,0];
 for(let i=0;i<n;i++){const [p,q,r,s]=shiftedVertices[i],v=[p+q/2,HALFROOT3*q,HALFROOT3*r,r/2+s];for(let k=0;k<4;k++){model[4*i+k]=v[k];mean[k]+=v[k]/n;}}
 modelMean=mean;for(let i=0;i<n;i++)for(let k=0;k<4;k++)model[4*i+k]-=mean[k];
 markModels=new Map(marks.anchors.map(a=>[a.tile,latticeToCartesian(a.coordinates.map((v,k)=>v-coordinateOrigin[k])).map((x,k)=>x-mean[k])]));
 centers=new Float64Array(data.tiles.length*4);let best=Infinity;
 for(let j=0;j<data.tiles.length;j++){for(const id of data.tiles[j])for(let k=0;k<4;k++)centers[4*j+k]+=model[4*id+k]/14;
 const v=project4(...centers.subarray(4*j,4*j+4),.5,HALFROOT3,false),dist=v[0]*v[0]+v[1]*v[1];if(data.labels[j]==='H1'&&dist<best){best=dist;state.selected=j;}}
 state.selected=ORIGIN_TILE;
 $('patch-info').textContent=`${data.tiles.length.toLocaleString()} tiles · drag to pan · scroll to zoom`;
 whiteAlignment=whiteMarkAlignment([...markModels.values()].map(p=>[.5*p[0]+HALFROOT3*p[2],.5*p[1]+HALFROOT3*p[3]]));
 frameStats=reflectedFrameStats(centers,data.labels); updateFrameNote();prepareSingleTile(); resize(); $('loading').hidden=true; if(new URLSearchParams(location.search).get('view')==='tile')setDisplay(true);
}
function resize(){const r=canvas.getBoundingClientRect();if(r.width>0&&r.height>0){width=r.width;height=r.height;}dpr=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
 if(model){let maxX=0,maxY=0;
 if(state.explore){let radius=0;for(let i=0;i<model.length;i+=4)radius=Math.max(radius,Math.hypot(...model.subarray(i,i+4)));maxX=maxY=radius;}
 else for(let j=0;j<=12;j++){const m=j/12,w=coefficients(m),f=currentFrame(w.u,w.vr);for(let i=0;i<model.length;i+=4){const q=projectPerspective(...model.subarray(i,i+4),w,f);maxX=Math.max(maxX,Math.abs(q[0]));maxY=Math.max(maxY,Math.abs(q[1]));}}
 fitScale=Math.min((width-40)/(2*maxX),(height-40)/(2*maxY));}dirty=true;}
function polygonPath(ids){ctx.beginPath();ctx.moveTo(screenX[ids[0]],screenY[ids[0]]);for(let i=1;i<14;i++)ctx.lineTo(screenX[ids[i]],screenY[ids[i]]);ctx.closePath();}
function draw(){if(!model)return; if(state.single){drawSingleTile();dirty=false;lastDraw=performance.now();return;}const angle=theta(),c=Math.cos(angle),s=Math.sin(angle),scale=fitScale*state.zoom,ox=width/2+state.panX,oy=height/2+state.panY;
 activeWeights=weights();activeFrame=currentFrame(c,s);
 ctx.setTransform(dpr,0,0,dpr,0,0);ctx.fillStyle='#e9ede3';ctx.fillRect(0,0,width,height);
 // One projection per shared vertex keeps adjoining boundaries identical.
 for(let i=0,j=0;i<model.length;i+=4,j++){const p=project4(model[i],model[i+1],model[i+2],model[i+3],c,s,state.lifted);screenX[j]=ox+p[0]*scale;screenY[j]=oy-p[1]*scale;screenZ[j]=p[2];}
 visible=[];
 const margin=5*scale;
 for(let j=0;j<data.tiles.length;j++){const p=project4(centers[j*4],centers[j*4+1],centers[j*4+2],centers[j*4+3],c,s,state.lifted);const x=ox+p[0]*scale,y=oy-p[1]*scale;if(x+margin>=0&&x-margin<=width&&y+margin>=0&&y-margin<=height)visible.push({id:j,z:p[2]});}
 if(state.lifted)visible.sort((a,b)=>a.z-b.z);
 ctx.lineJoin='round';ctx.lineWidth=Math.max(.4,Math.min(.85,scale*.055));ctx.strokeStyle='#365650a0';
 for(const tile of visible){polygonPath(data.tiles[tile.id]);ctx.fillStyle=colors[data.labels[tile.id]];ctx.globalAlpha=$('show-vertices').checked ? .22 : 1;ctx.fill();ctx.globalAlpha=1;ctx.stroke();}
 if(!state.explore&&certifiedMarks(state.morph)&&state.framing==='marks'){for(const item of visible){const anchor=markModels.get(item.id);if(!anchor)continue;const p=project4(...anchor,c,s,state.lifted);ctx.beginPath();ctx.arc(ox+p[0]*scale,oy-p[1]*scale,2.6,0,TAU);ctx.fillStyle='#fffaf0';ctx.fill();ctx.lineWidth=.8;ctx.strokeStyle='#294c48';ctx.stroke();}}
 if(state.explore&&$('show-lattice').checked)drawLattice(scale,ox,oy);
 drawVertexPoints();
 if(state.highlight){polygonPath(data.tiles[state.selected]);ctx.lineWidth=3;ctx.strokeStyle='#c45430';ctx.stroke();ctx.lineWidth=1;ctx.strokeStyle='#fff8e6';ctx.stroke();}
 dirty=false;lastDraw=performance.now();
}
function frame(time){const dt=lastTime?Math.min(time-lastTime,100):0;lastTime=time;
 if(state.playing&&model){state.phase=(state.phase+dt/36000*TAU*state.speed)%TAU;state.morph=(1-Math.cos(state.phase))/2;state.exact=null;dirty=true;}
 if(dirty&&time-lastDraw>=30){if(state.playing)updateLabels();draw();}requestAnimationFrame(frame);
}
function zoomBy(factor,x=width/2,y=height/2){const old=state.zoom;state.zoom=Math.max(.25,Math.min(80,old*factor));factor=state.zoom/old;state.panX=x-width/2-(x-width/2-state.panX)*factor;state.panY=y-height/2-(y-height/2-state.panY)*factor;dirty=true;}
function contains(ids,x,y){let inside=false;for(let i=0,j=13;i<14;j=i++){const ax=screenX[ids[i]],ay=screenY[ids[i]],bx=screenX[ids[j]],by=screenY[ids[j]];if((ay>y)!==(by>y)&&x<(bx-ax)*(y-ay)/(by-ay)+ax)inside=!inside;}return inside;}
function updateFrameNote(){
 $('frame-note').textContent=state.explore?'Every view is a two-dimensional projection. General perspectives may overlap or change reflected tile shapes.':state.framing==='marks'?(certifiedMarks(state.morph)?'White marks stay fixed; their average triangular direction is horizontal. The spacing is not an exact lattice.':'Horizontal white-mark layout; interior marks are shown between Hat and Turtle.'):state.framing==='steady'?'Overall rotation and spacing stabilized; small local shifts remain.':'Fixed edge directions across the entire tile family.';
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
 selectedAnchor=markModels.get(state.selected)||null;tileCoordinates=data.tiles[state.selected].map(id=>shiftedVertices[id]);
 tileModel=relativeTile(shiftedVertices,data.tiles[state.selected]).map(latticeToCartesian);
 const average=[0,0,0,0];tileModel.forEach(p=>p.forEach((x,k)=>average[k]+=x/14));
 tileModel=tileModel.map(p=>p.map((x,k)=>x-average[k]));
 const mid=tileModel.map(p=>projectVertex(...p,Math.SQRT1_2,Math.SQRT1_2,false));
 const sorted=mid.map((p,i)=>({i,x:p[0],y:p[1]})).sort((a,b)=>a.x-b.x);
 tileSides=[sorted.slice(0,7),sorted.slice(7)].map(side=>side.sort((a,b)=>b.y-a.y).map(p=>p.i));
 const NS='http://www.w3.org/2000/svg';$('single-leaders').replaceChildren();$('single-points').replaceChildren();
 for(let i=0;i<14;i++){
  const label=document.createElement('div');label.className='vertex-label';label.dataset.vertex=i;
  const prefix=document.createElement('span');prefix.className='coordinate-prefix';prefix.textContent=String.raw`\(\mathrm{v}_{${i}}=\)`;
  const tuple=document.createElement('span');tuple.textContent=String.raw`\(\approx(${tileCoordinates[i].map(x=>Math.abs(x)<.0005?'0':x.toFixed(3)).join(',')})\)`;label.append(prefix,tuple);label.title=`Vertex ${i}; distance ${vertexDistances[data.tiles[state.selected][i]].toFixed(6)}`;
  host.append(label);
  const line=document.createElementNS(NS,'line');line.id=`leader-${i}`;$('single-leaders').append(line);
  const point=document.createElementNS(NS,'circle');point.id=`vertex-${i}`;point.setAttribute('r',i===0?'4.5':'3.2');$('single-points').append(point);
 }
 tileRadius=0;
 if(state.explore){for(const p of tileModel)tileRadius=Math.max(tileRadius,Math.hypot(...p));}
 else for(let j=0;j<=60;j++){const m=j/60,w=coefficients(m),f=currentFrame(w.u,w.vr);for(const p of tileModel){const local=state.framing==='marks'&&selectedAnchor?p.map((x,k)=>x-(selectedAnchor[k]-centers[state.selected*4+k])):p;const q=projectPerspective(...local,w,{...f,tx:0,ty:0});tileRadius=Math.max(tileRadius,Math.hypot(q[0],q[1]));}}
 typesetCoordinates();dirty=true;
}
function drawSingleTile(){
 const rect=viewer.getBoundingClientRect(),w=rect.width,h=rect.height;
 const labelWidth=w<500?120:w<850?190:260,gutter=labelWidth+(w<500?18:30);
 const sc=Math.min(Math.max(60,w-2*gutter)/(2*tileRadius),(h-150)/(2*tileRadius))*.91;
 const c=Math.cos(theta()),s=Math.sin(theta()),f={...currentFrame(c,s),tx:0,ty:0};
 const anchorOffset=selectedAnchor?selectedAnchor.map((v,k)=>v-centers[state.selected*4+k]):[0,0,0,0];
 const lock=!state.explore&&state.framing==='marks'&&selectedAnchor;
 const points=tileModel.map(p=>{const local=lock?p.map((x,k)=>x-anchorOffset[k]):p;const q=projected(local,weights(),f);return [w/2+q[0]*sc,h/2+25-q[1]*sc];});
 $('single-svg').setAttribute('viewBox',`0 0 ${w} ${h}`);
 $('single-path').setAttribute('d',points.map((p,i)=>`${i?'L':'M'}${p[0]},${p[1]}`).join(' ')+' Z');
 $('single-path').style.fill=colors[data.labels[state.selected]];$('single-path').style.fillOpacity=$('show-vertices').checked?'.22':'1';
 $('single-anchor').style.display=lock&&certifiedMarks(state.morph)?'':'none';$('single-anchor').setAttribute('cx',w/2);$('single-anchor').setAttribute('cy',h/2+25);
 tileSides.forEach((side,k)=>side.forEach((i,row)=>{
  const y=88+row*(h-128)/6,inside=k===0?gutter-13:w-gutter+13;
  const label=$('coordinate-labels').children[i];label.style.top=`${y}px`;label.style.width=`${labelWidth}px`;label.style.left=k===0?'12px':'auto';label.style.right=k===1?'12px':'auto';label.style.textAlign=k===0?'right':'left';
  const line=$(`leader-${i}`);line.setAttribute('x1',points[i][0]);line.setAttribute('y1',points[i][1]);line.setAttribute('x2',inside);line.setAttribute('y2',y);
  const circle=$(`vertex-${i}`);circle.setAttribute('cx',points[i][0]);circle.setAttribute('cy',points[i][1]);circle.style.fill=$('show-vertices').checked?vertexColors[data.tiles[state.selected][i]]:'';
 }));
 $('distance-visible').textContent='Fourteen vertices of the selected tile';
}
let lastLatticeTex='';
function chosenLattice(){return state.matrix?state.matrix.basis:latticeBasis(state.morph,state.explore?state.phi:0,state.exact);}
function updateLatticeStatus(){
 const exact=state.exact,pole=state.morph<1e-12||state.morph>1-1e-12;
 $('lattice-status').textContent=state.matrix?(state.matrix.rankTwo?'Exact rank-two lattice in this matrix chart.':'This irrational matrix chart does not project to a discrete rank-two lattice.'):pole?'Exact triangular lattice · limiting perspective.':exact?'Exact triangular lattice · rational alignment selected.':'Free perspective · generic projected lattices are dense.';
 const f=(n,d)=>d===1?`${n}`:String.raw`\frac{${n}}{${d}}`;
 const tex=state.matrix?'':pole?'':exact?String.raw`\(x=\sqrt3\operatorname{Re}z=${f(exact.xn,exact.q)},\quad y=\operatorname{Im}z=${f(exact.yn,exact.q)}\)`:'Select a teal dot or a named example for an exact alignment.';
 if(tex!==lastLatticeTex){lastLatticeTex=tex;window.MathJax?.typesetClear?.([$('exact-readout')]);$('exact-readout').textContent=tex;window.MathJax?.typesetPromise?.([$('exact-readout')]).catch(console.error);}
 if(!chosenLattice())$('lattice-grid-note').textContent='';
}
function drawLattice(scale,ox,oy){
 const basis=chosenLattice();if(!basis)return;
 const f=activeFrame,bs=basis.map(([x,y])=>[scale*(f.re*x-f.im*y),-scale*(f.im*x+f.re*y)]),o=projected(latticeToCartesian(shiftedVertices[0]).map((x,k)=>x-modelMean[k]),activeWeights,activeFrame),origin=[ox+scale*o[0],oy-scale*o[1]];
 const det=bs[0][0]*bs[1][1]-bs[1][0]*bs[0][1];if(Math.abs(det)<1e-14){$('lattice-grid-note').textContent='The aligned lattice is too fine to resolve at this zoom.';return;}
 const corners=[[0,0],[width,0],[0,height],[width,height]].map(([x,y])=>{x-=origin[0];y-=origin[1];return [(x*bs[1][1]-bs[1][0]*y)/det,(bs[0][0]*y-x*bs[0][1])/det];});
 const lo=[0,1].map(k=>Math.floor(Math.min(...corners.map(p=>p[k])))-1),hi=[0,1].map(k=>Math.ceil(Math.max(...corners.map(p=>p[k])))+1),count=(hi[0]-lo[0]+1)*(hi[1]-lo[1]+1);
 if(count>12000){$('lattice-grid-note').textContent='Exact alignment; zoom in to resolve its fine lattice.';return;}
 $('lattice-grid-note').textContent='Dots show the underlying projected lattice, not translation symmetries of the tiling.';
 ctx.fillStyle='#264c4870';ctx.beginPath();for(let i=lo[0];i<=hi[0];i++)for(let j=lo[1];j<=hi[1];j++){const x=origin[0]+i*bs[0][0]+j*bs[1][0],y=origin[1]+i*bs[0][1]+j*bs[1][1];if(x>=0&&x<=width&&y>=0&&y<=height){ctx.moveTo(x+.85,y);ctx.arc(x,y,.85,0,TAU);}}ctx.fill();
}
function drawVertexPoints(){
 let inView=0;
 if($('show-vertices').checked){
  // Every shared vertex participates; viewport clipping is the only exclusion.
  for(let i=0;i<screenX.length;i++){
   const x=screenX[i],y=screenY[i];if(x<0||x>width||y<0||y>height)continue;inView++;
   ctx.beginPath();ctx.arc(x,y,2.35,0,TAU);ctx.fillStyle=vertexColors[i];ctx.fill();ctx.lineWidth=.65;ctx.strokeStyle='#fffaf0';ctx.stroke();
  }
 }
 $('distance-visible').textContent=$('show-vertices').checked?`${inView.toLocaleString()} vertices in view · Whole patch shows the complete patch`:'Vertex colors hidden';
}
function setPerspective(p){setPlaying(false);if(!state.explore)setMode(true);state.matrix=null;state.phi=p.phi;updateMatrixControls();setMorph(p.m,p.exact);dirty=true;}
function goStop(name){setPlaying(false);setMode(false);const p=namedAlignment(name);setMorph(FAMILY_STOPS[name],p?.exact||null);}
function updateMatrixControls(){const on=!!state.matrix;$('morph').disabled=on;$('relative-angle').disabled=on;$('play').disabled=on;$('perspective-controls').classList.toggle('matrix-mode',on);if(!on)$('matrix-status').textContent='Four-parameter view inactive. Apply the displayed inputs to select a general screen plane.';}
function applyMatrix(){try{
 const values=['a','b','c','d'].map(k=>$(`matrix-${k}`).value),pivots=$('matrix-chart').value.split(',').map(Number),projection=matrixPerspective(values,pivots);
 setPlaying(false);if(!state.explore)setMode(true);state.matrix=projection;updateMatrixControls();updateLabels();prepareSingleTile();dirty=true;
 $('matrix-status').textContent=projection.rankTwo?'Four-parameter view active. All four chart entries are rational, so the image is a discrete two-dimensional lattice.':'Four-parameter view active. An irrational chart entry prevents a discrete rank-two lattice.';
 }catch(error){$('matrix-status').textContent=error.message;}}
$('return-family').onclick=()=>setMode(false);
$('relative-angle').oninput=e=>setPerspective({m:state.morph,phi:Number(e.target.value)*Math.PI/180,exact:null});
$('aligned-example').onchange=e=>{const p=namedAlignment(e.target.value);if(p)setPerspective(p);};
$('show-lattice').onchange=()=>{dirty=true;};$('apply-matrix').onclick=applyMatrix;
$('irrational-matrix').onclick=()=>{$('matrix-chart').value='0,1';for(const [k,v] of Object.entries({a:'sqrt(2)',b:'0',c:'0',d:'1'}))$(`matrix-${k}`).value=v;applyMatrix();};

$('show-vertices').onchange=()=>{dirty=true;};
$('play').onclick=()=>setPlaying(!state.playing);
$('morph').addEventListener('input',e=>{const value=Number(e.target.value)/3000;state.matrix=null;setPlaying(false);setMorph(value);});
for(const name of ['hat','turtle','chevron','comet'])$(name).onclick=()=>goStop(name);$('midpoint').onclick=()=>goStop('equal');
$('plane').onclick=()=>setMode(false);$('lift').onclick=()=>setMode(true);
$('patch-view').onclick=()=>setDisplay(false);$('tile-view').onclick=()=>setDisplay(true);
$('framing').onchange=e=>{state.framing=e.target.value;state.steady=state.framing!=='edges';updateFrameNote();prepareSingleTile();resize();dirty=true;};
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
window.projectionDemo={state,setMorph,setMode,setPlaying,get metadata(){return data?.metadata;},get visibleCount(){return visible.length;},get tileCoordinates(){return tileCoordinates;},get fixedMarkCount(){return marks?.anchors.length;},get frame(){return currentFrame(Math.cos(theta()),Math.sin(theta()));},setDisplay};
setPlaying(state.playing);requestAnimationFrame(frame);
try{const responses=await Promise.all([fetch('patch.json'),fetch('fixed-marks.json')]);if(responses.some(r=>!r.ok))throw Error('Tiling data download failed');[data,marks]=await Promise.all(responses.map(r=>r.json()));prepare();}catch(error){$('loading').textContent='The tiling could not load. Please reload the page.';console.error(error);}
