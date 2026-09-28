import * as THREE from 'three';
import {OrbitControls} from '../../apps/3d-lattice-tiler/vendor/OrbitControls.js';
const $=id=>document.getElementById(id);
window.addEventListener('error',e=>{$('error').textContent=e.message;});
window.addEventListener('unhandledrejection',e=>{$('error').textContent=e.reason?.message??String(e.reason);});
const [catalog,summary]=await Promise.all(['catalog.json','summary.json'].map(async f=>{const r=await fetch('../../data/bent-six-arm/variants/'+f);if(!r.ok)throw Error(`${f}: ${r.status}`);return r.json();}));
const named=new Map(summary.rows.map(r=>[r.id,r]));
let mathQueue=Promise.resolve();
function math(els){mathQueue=mathQueue.then(async()=>{if(window.MathJax?.startup?.promise)await window.MathJax.startup.promise;await window.MathJax?.typesetPromise?.(els);});}
function link(path,label){const a=document.createElement('a');a.href='../../'+path;a.textContent=label;return a;}
const resultText=r=>r?.exact===0?'\\(H=0\\)':r?.lower?'\\(H\\geq'+r.lower+'\\); exact value unresolved':r?'Unresolved':'Not searched';
$('search-summary').textContent=`${summary.verifiedFirstCoronas} verified examples of \\(H\\geq1\\); ${summary.certifiedH0} certified cases of \\(H=0\\); ${summary.unresolvedClasses} unresolved; ${summary.notSearchedClasses} unsearched. A timeout is not a negative result.`;math([$('search-summary')]);
for(const r of summary.rows.filter(r=>r.exact!==null||r.lower||r.antipodal)){const tr=document.createElement('tr');for(const value of [r.name,resultText(r),r.note]){const td=document.createElement('td');td.textContent=value;tr.append(td);}tr.lastChild.append(' ',link(r.evidence[0],'Evidence'));$('results').append(tr);}math([$('results')]);
const host=$('scene'),scene=new THREE.Scene();scene.background=new THREE.Color('#101821');const camera=new THREE.PerspectiveCamera(40,1,.1,100),renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));host.append(renderer.domElement);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;scene.add(new THREE.HemisphereLight(0xf0f8ff,0x465568,2.6));const light=new THREE.DirectionalLight(0xffffff,3);light.position.set(5,9,7);scene.add(light);
const group=new THREE.Group();scene.add(group);const cube=new THREE.BoxGeometry(.98,.98,.98),edge=new THREE.EdgesGeometry(cube),line=new THREE.LineBasicMaterial({color:0x182739}),blue=new THREE.MeshStandardMaterial({color:0x669fe5,roughness:.65}),gold=new THREE.MeshStandardMaterial({color:0xf1c264,roughness:.65});
function reset(){camera.position.set(8,6,10);controls.target.set(0,0,0);controls.update();}$('reset').onclick=reset;reset();
const dir=['e_x','e_y','e_z','-e_x','-e_y','-e_z'];
function draw(){const r=catalog.rows.find(r=>r.id===$('variant').value),n=named.get(r.id);group.clear();for(const v of r.voxels){const mesh=new THREE.Mesh(cube,v.every(x=>x===0)?gold:blue);mesh.position.set(...v);mesh.add(new THREE.LineSegments(edge,line));group.add(mesh);}
 $('variant-name').textContent=n?.name??r.id;$('variant-result').textContent=resultText(n);$('variant-result').append(document.createElement('br'),n?.note??'');$('variant-facts').textContent=`25 cubes · ${r.orientations} proper orientations · ${r.antipodal?'centrally symmetric':'not centrally symmetric'}`;
 $('evidence').replaceChildren();for(const [i,p] of (n?.evidence??[]).entries()){if(i)$('evidence').append(' · ');$('evidence').append(link(p,p.endsWith('-verification.json')||p.endsWith('/verification.json')?'Verification':p.endsWith('.cnf.gz')?'CNF':p.endsWith('.drup.gz')?'Proof':p.endsWith('-screen.json')?p.split('/').slice(-2).join('/'):'Run record'));}
 $('directions').replaceChildren();for(let i=0;i<6;i++){const tr=document.createElement('tr');for(const d of [i,r.bends[i]]){const td=document.createElement('td');td.textContent=`\\(${dir[d]}\\)`;tr.append(td);}$('directions').append(tr);}math([$('variant-result'),$('directions')]);window.bendVariantView={id:r.id,voxelCount:r.voxels.length,exact:n?.exact??null,searched:!!n};}
function fill(){const prev=$('variant').value;$('variant').replaceChildren();for(const r of catalog.rows.filter(r=>$('family').value==='all'||r.antipodal)){const o=document.createElement('option');o.value=r.id;o.textContent=named.get(r.id)?.name??r.id;$('variant').append(o);}if([...$('variant').options].some(o=>o.value===prev))$('variant').value=prev;draw();}
$('family').onchange=fill;$('variant').onchange=draw;fill();
new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}).observe(host);renderer.setAnimationLoop(()=>{controls.update();renderer.render(scene,camera);});
