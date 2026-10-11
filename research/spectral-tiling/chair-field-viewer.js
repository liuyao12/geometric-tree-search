import * as THREE from '../../3d-reptiles/vendor/three.module.min.js';

const $=id=>document.getElementById(id);
const construction=JSON.parse($('chair-field-data').textContent);
const panels=construction.panels;
const DEFAULT_THETA=Math.PI/5,DEFAULT_PHI=Math.PI/3;
let data,selected=1,theta=DEFAULT_THETA,phi=DEFAULT_PHI;
const displays=[];
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
function trace(y,p){const r=dot(y,y);return r<1/16?Math.exp(1-1/(1-16*r))*(dot(p.arrow,y)+16*r*dot(p.cubic,y)):0;}
function formulaSurface(){
  const points=[],values=[],triangles=[],n=32;
  for(const p of panels){
    const tangent=[0,1,2].filter(i=>p.normal[i]===0),start=points.length;
    for(let i=0;i<=n;i++)for(let j=0;j<=n;j++){
      const y=[0,0,0];y[tangent[0]]=i/n-.5;y[tangent[1]]=j/n-.5;
      points.push(y.map((v,k)=>v+p.center[k]));values.push(trace(y,p));
    }
    for(let i=0;i<n;i++)for(let j=0;j<n;j++){
      const a=start+i*(n+1)+j,b=a+n+1,c=b+1,d=a+1;triangles.push([a,b,c],[a,c,d]);
    }
  }
  return {points,values,triangles};
}
function color(v){
  v=Math.max(-1,Math.min(1,v));const white=[.96,.95,.90],end=v<0?[.12,.32,.52]:[.62,.13,.20],t=Math.abs(v);
  return white.map((c,i)=>c+(end[i]-c)*t);
}
function createDisplay(id,points,triangles,values,peak){
  const host=$(id),renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setClearColor(0xf8f8f2);
  host.append(renderer.domElement);renderer.domElement.setAttribute('aria-label',id==='chair-exact-view'?'Exact formula field on the chair surface':'Selected numerical Neumann eigenfunction on the chair surface');
  const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(36,1,.1,100);camera.up.set(0,0,1);
  const position=new Float32Array(triangles.length*9),colors=new Float32Array(position.length),indices=triangles.flat();
  indices.forEach((index,j)=>position.set(points[index],3*j));
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(position,3));geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));
  geometry.computeVertexNormals();
  const mesh=new THREE.Mesh(geometry,new THREE.MeshLambertMaterial({vertexColors:true,side:THREE.DoubleSide}));scene.add(mesh);
  scene.add(new THREE.AmbientLight(0xffffff,.85));
  const light=new THREE.DirectionalLight(0xffffff,.65);light.position.set(3,-2,6);scene.add(light);
  scene.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry,20),new THREE.LineBasicMaterial({color:0x263a32})));
  const lines=[];
  for(const p of panels){
    const axes=[0,1,2].filter(i=>p.normal[i]===0),corners=[[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]].map(pair=>p.center.map((v,k)=>v+(k===axes[0]?pair[0]:k===axes[1]?pair[1]:0)));
    for(let j=0;j<4;j++)lines.push(...corners[j],...corners[(j+1)%4]);
  }
  const edges=new THREE.BufferGeometry();edges.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));scene.add(new THREE.LineSegments(edges,new THREE.LineBasicMaterial({color:0x93a69b})));
  const display={renderer,scene,camera,geometry,host,indices,colors};displays.push(display);
  display.update=(v,max)=>{indices.forEach((index,j)=>colors.set(color(v[index]/Math.max(max,1e-16)),3*j));geometry.attributes.color.needsUpdate=true;render();};
  display.update(values,peak);
  let drag;
  renderer.domElement.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];renderer.domElement.setPointerCapture(e.pointerId);});
  renderer.domElement.addEventListener('pointermove',e=>{if(!drag)return;theta-=(e.clientX-drag[0])*.008;phi=Math.max(.12,Math.min(Math.PI-.12,phi+(e.clientY-drag[1])*.008));drag=[e.clientX,e.clientY];render();});
  for(const event of ['pointerup','pointercancel'])renderer.domElement.addEventListener(event,()=>{drag=null;});
  new ResizeObserver(()=>{const width=host.clientWidth,height=320;renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();render();}).observe(host);
  return display;
}
function render(){for(const d of displays){d.camera.position.set(1+6*Math.sin(phi)*Math.cos(theta),1+6*Math.sin(phi)*Math.sin(theta),1+6*Math.cos(phi));d.camera.lookAt(1,1,1);d.renderer.render(d.scene,d.camera);}}
function typeset(element){if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([element]).catch(()=>{});}
const svgNS='http://www.w3.org/2000/svg';
function svgElement(tag,attributes,text){const element=document.createElementNS(svgNS,tag);for(const [key,value] of Object.entries(attributes))element.setAttribute(key,value);if(text!==undefined)element.textContent=text;return element;}
function drawChart(){
  if(!data)return;const values=data.mesh_runs.at(-1).eigenvalues;
  const maximum=$('chair-range').value==='full'?values.at(-1)*1.03:values[15]*1.04;
  const divisor=$('chair-scale').value==='pi2'?Math.PI**2:1;
  const svg=$('chair-spectrum');svg.replaceChildren();svg.append(svgElement('line',{x1:48,y1:116,x2:884,y2:116,stroke:'#63877b'}));
  for(let i=0;i<=5;i++){
    const x=48+i*836/5;svg.append(svgElement('line',{x1:x,y1:116,x2:x,y2:122,stroke:'#63877b'}));
    svg.append(svgElement('text',{x,y:143,'text-anchor':'middle',fill:'#40564e','font-size':13},(maximum*i/5/divisor).toPrecision(3)));
  }
  const previous=[];
  values.forEach((value,index)=>{
    if(value>maximum)return;const x=48+836*value/maximum;
    let lane=0;while(previous.some(p=>p.lane===lane&&Math.abs(p.x-x)<15))lane++;previous.push({x,lane});
    const y=83-15*lane;svg.append(svgElement('line',{x1:x,y1:y,x2:x,y2:116,stroke:'#d6e0d8'}));
    const node=svgElement('circle',{cx:x,cy:y,r:index===selected?6:4.8,fill:index===selected?'#bf6544':'#426d63',role:'button',tabindex:0,'aria-label':'Neumann mode '+index,'aria-pressed':String(index===selected)});
    node.append(svgElement('title',{},'Neumann mode '+index+': '+value.toPrecision(8)));node.addEventListener('click',()=>select(index));node.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();select(index);}});svg.append(node);
  });
  $('chair-axis-label').textContent=$('chair-scale').value==='pi2'?'\\(\\lambda/\\pi^2\\)':'\\(\\lambda\\)';typeset($('chair-axis-label'));
}
function select(index){
  selected=index;$('chair-mode').value=String(index);const fine=data.mesh_runs.at(-1),coarse=data.mesh_runs[0],coefficient=fine.coefficients[index];
  displays[1].update(data.viewer.surface_values[index],data.viewer.full_nodal_peaks[index]);
  $('chair-mode-detail').innerHTML=`<p><strong>Numerical mode \\(\\phi_{${index}}\\)</strong></p><p>\\(\\mu_{${index}}\\approx ${fine.eigenvalues[index].toPrecision(8)}\\), \\(\\mu_{${index}}/\\pi^2\\approx ${(fine.eigenvalues[index]/Math.PI**2).toPrecision(8)}\\).</p><p>Coefficient in the prescribed field: \\(c_{${index}}\\approx ${coefficient.toPrecision(7)}\\). Contribution to its sampled squared mass norm: \\(${(100*coefficient**2/fine.sampled_target_squared_mass_norm).toPrecision(4)}\\%\\).</p><p class="small">Last mesh movement: \\(${Math.abs(fine.eigenvalues[index]-coarse.eigenvalues[index]).toPrecision(3)}\\). The numerical surface trace is normalized by the largest absolute nodal value over the full chair.</p>`;
  $('chair-numerical-caption').textContent=`Numerical Neumann mode ${index}. Surface trace; drag either view to rotate both.`;
  drawChart();typeset($('chair-mode-detail'));
}
async function start(){
  try{
    const response=await fetch('../../research/spectral-tiling/chair-modal-projection.json?v=chair1');if(!response.ok)throw new Error('Mode data could not be loaded.');data=await response.json();
    const exact=formulaSurface();createDisplay('chair-exact-view',exact.points,exact.triangles,exact.values,Math.max(...exact.values.map(Math.abs)));
    createDisplay('chair-numerical-view',data.viewer.points,data.viewer.triangles,data.viewer.surface_values[1],data.viewer.full_nodal_peaks[1]);
    data.mesh_runs.at(-1).eigenvalues.forEach((value,index)=>$('chair-mode').add(new Option(`Neumann mode ${index} · ${value.toPrecision(7)}`,index)));
    $('chair-mode').addEventListener('change',()=>select(Number($('chair-mode').value)));
    for(const id of ['chair-range','chair-scale'])$(id).addEventListener('change',drawChart);
    $('chair-reset-camera').addEventListener('click',()=>{theta=DEFAULT_THETA;phi=DEFAULT_PHI;render();});
    select(1);$('chair-viewer-status').textContent='Loaded 60 numerical modes. The exact formula samples and numerical eigenfunction use separate peak color scales.';
  }catch(error){$('chair-viewer-status').textContent='Viewer unavailable: '+error.message;}
}
start();
