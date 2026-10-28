import { CrystalScene } from './scene.js';
const $ = s => document.querySelector(s);
const generate = $('#generate'), download = $('#download'), status = $('#status');
let exportJSON = null, exportRadius = 1, selected = null, scene = null, mode = 'crystal';
const texScalar = ([a,b,d]) => {
  let n = a === '0' ? '' : a;
  if(b !== '0') n += `${b.startsWith('-') || !n ? '' : '+'}${b === '1' ? '' : b === '-1' ? '-' : b}\\tau`;
  n ||= '0'; return d === '1' ? n : `\\frac{${n}}{${d}}`;
};
const typeset = e => window.MathJax?.typesetPromise?.([e]);
function showExact(vertices) {
  const sample = $('#sample'); window.MathJax?.typesetClear?.([sample]);
  sample.textContent = `\\[\\begin{aligned}${vertices.map((p,i) => `v_{${i}}&=\\left(${p.map(texScalar).join(',\\;')}\\right)`).join('\\\\')}\\end{aligned}\\]`;
  $('#sample-details').hidden = false; typeset(sample);
}
try {
  scene = new CrystalScene($('#scene'), tile => {
    selected = tile; $('#inspector').hidden = !tile;
    if(!tile) return;
    $('#tile-kind').textContent = `${tile.kind === 'prolate' ? 'Prolate' : 'Oblate'} rhombohedron`;
    const target = $('#tile-data'); window.MathJax?.typesetClear?.([target]);
    target.textContent = `Axes \\((${tile.axes.join(',')})\\) · exact volume \\(${texScalar(tile.volume)}\\).`; typeset(target);
  });
  $('#spin').checked = scene.controls.autoRotate;
} catch(error) {
  $('#loading p').textContent = '3D graphics are unavailable in this browser. Exact JSON export is still available.';
  status.textContent = error.message;
}
const worker = new Worker(new URL('./worker.js',import.meta.url),{type:'module'});
generate.onclick = () => {
  exportJSON = null; generate.disabled = true; download.disabled = true;
  $('#loading').hidden = false; $('#loading p').textContent = 'Constructing the exact patch';
  $('#summary').replaceChildren(); $('#sample-details').hidden = true;
  status.textContent = 'Constructing and projecting exact algebraic geometry…';
  exportRadius = Number($('#radius').value); worker.postMessage({radius:exportRadius});
};
worker.onmessage = ({data}) => {
  generate.disabled = false;
  if(!data.ok) { status.textContent = data.error; $('#loading p').textContent = data.error; return; }
  exportJSON = data.json; download.disabled = false;
  status.textContent = 'Exact patch ready. Display controls leave the exported geometry unchanged.';
  for(const [label,value] of [['Tiles',data.count],['Prolate',data.counts.prolate],['Oblate',data.counts.oblate],['Global grid regularity',data.regular?'Certified':'Inconclusive']]) {
    const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent=label; dd.textContent=String(value); $('#summary').append(dt,dd);
  }
  $('#prolate-count').textContent = data.counts.prolate.toLocaleString(); $('#oblate-count').textContent = data.counts.oblate.toLocaleString();
  $('#regularity').textContent = data.regular ? 'Exact geometry · regular grid certified' : 'Exact geometry · regularity inconclusive';
  showExact(data.sample.vertices);
  if(scene) { scene.setModel(data.display); $('#loading').hidden=true; }
  updateHeading();
};
worker.onerror = () => { generate.disabled=false; status.textContent='The construction worker could not load. Reload to retry.'; $('#loading p').textContent=status.textContent; };
const descriptions = {
  crystal:['Golden rhombohedra','The central connected patch from six grid directions. Click either color to inspect a tile, or reveal the interior to see how the pieces fit.','The two shapes meet face to face. Their golden rhombi reveal the structure of the assembly.','A finite icosahedral patch'],
  exploded:['Space between the pieces','Pull the assembly apart along the line from its center to each tile. Every piece retains its original shape and orientation.','Separation is a display transform. Set it to zero to return every tile to its exact placement.','Exploded assembly'],
  tiles:['Two shapes. One edge length.','Compare the elongated prolate tile with the flattened oblate tile. Both have six golden-rhombus faces and exactly the same edge length.','Both tiles are shown at the same scale. The prolate tile has the golden ratio times the volume of the oblate tile.','The golden rhombohedra'],
  window:['The hidden selection rule','In the complementary internal space, accepted vertices lie inside this rhombic triacontahedron. Gold points come from the current patch.','Thirty golden faces bound the acceptance window. Its exact supporting planes decide which integer lifts become vertices.','Internal space · acceptance window']
};
function updateHeading() {
  const [heading,description,caption,title]=descriptions[mode]; $('#view-heading').textContent=heading; $('#view-description').textContent=description; $('#caption').textContent=caption; $('#scene-title').textContent=title;
  $('.caption-index').textContent=`0${Object.keys(descriptions).indexOf(mode)+1} / 04`;
  const applicable=mode==='crystal'||mode==='exploded'; $('#separation').disabled=!applicable; $('#cutaway').disabled=!applicable;
  $('#show-prolate').disabled=mode==='window'; $('#show-oblate').disabled=mode==='window';
}
for(const button of document.querySelectorAll('[data-mode]')) button.onclick=()=>{
  mode=button.dataset.mode; document.querySelectorAll('[data-mode]').forEach(b=>{b.classList.toggle('active',b===button);b.setAttribute('aria-pressed',String(b===button));});
  $('#separation').value=mode==='exploded'?'35':'0'; $('#separation-value').textContent=`${$('#separation').value}%`; $('#cutaway').value='0'; $('#cutaway-value').textContent='0%';
  if(scene){scene.options.separation=Number($('#separation').value);scene.options.cutaway=0;scene.setMode(mode);} updateHeading();
};
let pending=false;
function updateDisplay(){
  $('#separation-value').textContent=`${$('#separation').value}%`; $('#cutaway-value').textContent=`${$('#cutaway').value}%`;
  if(pending)return;pending=true;requestAnimationFrame(()=>{pending=false;scene?.setOptions({separation:Number($('#separation').value),cutaway:Number($('#cutaway').value),prolate:$('#show-prolate').checked,oblate:$('#show-oblate').checked,edges:$('#edges').checked,fragments:$('#fragments').checked});});
}
for(const id of ['separation','cutaway','show-prolate','show-oblate','edges','fragments']) $(`#${id}`).addEventListener('input',updateDisplay);
$('#spin').onchange=()=>{if(scene)scene.controls.autoRotate=$('#spin').checked;};
for(const b of document.querySelectorAll('[data-camera]')) b.onclick=()=>{
  document.querySelectorAll('[data-camera]').forEach(x=>x.classList.toggle('active',x===b));if(scene){scene.controls.autoRotate=false;scene.fit(b.dataset.camera);$('#spin').checked=false;}
};
for(const b of document.querySelectorAll('[data-material]')) b.onclick=()=>{
  document.querySelectorAll('[data-material]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});scene?.setOptions({glass:b.dataset.material==='glass'});
};
$('#reset-view').onclick=()=>scene?.fit(); $('#snapshot').onclick=()=>scene?.saveImage(); $('#close-inspector').onclick=()=>scene?.select(null);
$('.math-link').onclick=()=>{ $('#mathematics').open=true; };
$('#inspect-exact').onclick=()=>{if(!selected)return;showExact(selected.exact);$('#mathematics').open=true;$('#sample-details').open=true;$('#sample-details').scrollIntoView({behavior:'smooth',block:'center'});};
$('#sample-details').ontoggle=e=>{if(e.target.open)typeset($('#sample'));};
download.onclick=()=>{if(!exportJSON)return;const url=URL.createObjectURL(new Blob([exportJSON],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`icosahedral-exact-radius-${exportRadius}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
generate.click();
