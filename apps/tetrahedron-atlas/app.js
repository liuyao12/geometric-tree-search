const $ = id => document.getElementById(id);
const info = {
 quasi: {kind:'TWELVEFOLD ORDER',name:'Dodecagonal quasicrystal',description:'A simulated packing with a nonrepeating square–triangle organization in its layers. Corrugated layers stack periodically; twelve-member tetrahedron rings form columns called “logs”.',density:'83.24%',periodicity:'Aperiodic in the layer plane',provenance:'Original research figures',caveat:'The sample is finite and simulated with periodic boundaries. Its twelvefold diffraction and nonrepeating layer organization identify quasicrystalline order. This is not a new simulation.',source:'https://arxiv.org/abs/1012.5138'},
 approx: {kind:'THE PERIODIC RELATIVE',name:'Square–triangle approximant',description:'Inspect the published unit cell, separate its tetrahedra, then assemble translated copies into a small periodic block.',density:'84.7866% in this model',periodicity:'Periodic in all three directions',provenance:'Published 82-particle coordinates',caveat:'The available endpoint is the 82-particle cell at 84.7866%. The exploded view is illustrative; the original ideal starting cell and compression trajectory are unavailable. The 85.03% result uses separate supercell data.',source:'https://arxiv.org/abs/1012.5138'},
 dimer: {kind:'THE DENSITY BENCHMARK',name:'Double-dimer crystal',description:'Two face-sharing pairs form a repeating cell of four tetrahedra. Opposite dimers are related by inversion. Explore the record construction as a contrast to the large, complex approximant.',density:'85.6348%',periodicity:'Periodic · triclinic cell',provenance:'Theorem 1 lattice and offset vectors',caveat:'Inspect the record unit cell and its translated copies. Separating the solids is an exploded view, not a physical compression trajectory.',source:'https://arxiv.org/abs/1001.0586'}
};
let mode='quasi',figure='packing',engine,creation,comparing=false;
function setComparison(value){comparing=value;$('compare-source').hidden=!value;$('comparison-guide').hidden=!value;document.querySelector('.comparison-view').classList.toggle('comparing',value);$('compare-toggle').setAttribute('aria-pressed',String(value));$('compare-toggle').textContent=value?'Close comparison':'Compare quasicrystal & approximant';}
$('compare-toggle').onclick=()=>{setComparison(!comparing);if(comparing)select('approx');};
function enlarge(src){$('large-figure').src=src;$('figure-dialog').showModal();}
$('figure-open').onclick=()=>enlarge($('main-figure').src);
$('close-dialog').onclick=()=>$('figure-dialog').close();
document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>enlarge(b.dataset.image));
$('figure-switch').onclick=()=>{figure=figure==='packing'?'structure':'packing';$('main-figure').src=`figures/${figure}.jpg`;$('main-figure').alt=figure==='packing'?'Published Figure 1: local motifs, perspective quasicrystal, side view and twelvefold-axis view.':'Published Figure 3: quasicrystal square–triangle network, tetrahedron logs, periodic approximant, underlying tiling and tetrahelices.';$('figure-switch').textContent=figure==='packing'?'Show tiling & logs':'Show packing views';};
async function select(next){if(next!=='approx')setComparison(false);mode=next;history.replaceState(null,'',`#${mode}`);document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));const item=info[mode];for(const key of ['kind','name','description','density','periodicity','provenance','caveat'])$(key).textContent=item[key];$('density-title').textContent=mode==='quasi'?'Published packing fraction':'Published packed fraction';$('source-link').href=item.source;$('paper-view').hidden=mode!=='quasi';$('viewer').hidden=mode==='quasi';$('controls').hidden=mode==='quasi';$('data-link').hidden=mode!=='approx';$('visual-label').textContent=mode==='quasi'?'PUBLISHED QUASICRYSTAL':mode==='approx'?'PUBLISHED APPROXIMANT':'RECORD DIMER CONSTRUCTION';$('visual-tag').textContent=mode==='quasi'?'Source figure':'Interactive 3D';
 if(mode==='quasi'){if(engine)engine.pause();return;}
 try{if(!creation)creation=createViewer();engine=await creation;engine.activate();if(comparing)engine.alongStack();$('load-error').hidden=true;}catch(error){$('load-error').hidden=false;$('load-error').textContent='The 3D viewer could not load. The published figures and source links remain available. '+error.message;}
}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>select(b.dataset.mode));
async function createViewer(){
 const [{createPackingViewer},data]=await Promise.all([import('./viewer.js?v=5'),fetch('./data/approximant.json').then(r=>{if(!r.ok)throw Error('Coordinate file unavailable');return r.json();})]);
 return createPackingViewer(data,()=>mode);
}

if(['approx','dimer'].includes(location.hash.slice(1)))select(location.hash.slice(1));

if(new URLSearchParams(location.search).get('compare')==='1'){setComparison(true);select('approx');}
