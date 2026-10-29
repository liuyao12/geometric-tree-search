import {SYSTEMS,loadSpecimens} from './polyhedral-catalog.js?v=live-search-workspace-v2';
import {TileViewer} from './tile-viewer.js?v=live-search-workspace-v2';
const $=s=>document.querySelector(s),typeset=e=>window.MathJax?.typesetPromise?.([e]);
const scalar=([a,b,d])=>{let n=a==='0'?'':a;if(b!=='0')n+=`${b.startsWith('-')||!n?'':'+'}${b==='1'?'':b==='-1'?'-':b}\\tau`;n||='0';return d==='1'?n:`\\frac{${n}}{${d}}`;};
const texPoint=p=>`\\left(${p.map(scalar).join(',\\;')}\\right)`;
const escape=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
export function setupCatalog({onSystem=()=>{}}={}){
 const select=$('#system-select'),shelf=$('#tile-shelf'),meta=$('#catalog-meta');let system=SYSTEMS[0],tiles=[],cards=[],selected=null,epoch=0,shown=0;
 for(const s of SYSTEMS){const o=document.createElement('option');o.value=s.id;o.textContent=`${s.name} · ${s.id==='ammann'?'live search':s.count+' · prototypes'}`;select.append(o);}
 function inspect(t,face=null){
  const panel=$('#catalog-inspector');window.MathJax?.typesetClear?.([panel]);panel.replaceChildren();const title=document.createElement('h3');title.textContent=`${t.name}${t.mirrored?' · mirrored':''}${face===null?'':` · face ${face+1}`}`;panel.append(title);
  const info=document.createElement('p');info.textContent=t.displayOnly?'Author’s rounded print mesh · display only':`${t.exact.length.toLocaleString()} exact vertices · ${t.faces.length.toLocaleString()} boundary facets`;panel.append(info);
  const ids=face===null?Array.from({length:Math.min(12,t.exact?.length||0)},(_,i)=>i):t.faces[face];
  if(t.exact){const maths=document.createElement('div');maths.className='specimen-coordinates';maths.textContent=`\\[\\begin{aligned}${ids.map(i=>`v_{${i}}&=${texPoint(t.exact[i])}`).join('\\\\')}\\end{aligned}\\]`;panel.append(maths);if(face===null&&t.exact.length>12){const note=document.createElement('p');note.textContent='First 12 vertices shown. Click a face for its vertices, or download the complete exact data.';panel.append(note);}}
  if(face!==null&&t.faceSymbols){const v=document.createElement('p');v.textContent=`Face symbol: ${JSON.stringify(t.faceSymbols[face])}. Face order and symbolic values are in the download.`;panel.append(v);}
  if(t.pointMarkings?.length){const d=document.createElement('details'),s=document.createElement('summary'),p=document.createElement('pre');s.textContent='Point marking assignments';p.textContent=JSON.stringify(face===null?t.pointMarkings:t.pointMarkings.filter((_,i)=>i===face),null,2);d.append(s,p);panel.append(d);}
  typeset(panel);
 }
 function show(t,face=null){selected=t;$('#catalog-download').disabled=false;inspect(t,face);for(const card of cards)card.element.classList.toggle('selected',card.id===t.id);}
 async function choose(id){
  const token=++epoch;system=SYSTEMS.find(s=>s.id===id)||SYSTEMS[0];select.value=system.id;$('#catalog-state').textContent='Loading source-backed specimens…';shelf.replaceChildren();cards.forEach(c=>c.viewer.dispose());cards=[];tiles=[];shown=0;selected=null;$('#catalog-download').disabled=true;
  meta.innerHTML=`<div><p class="eyebrow">${escape(system.category)} · ${escape(system.year)}</p><h2>${escape(system.name)}</h2><p>${escape(system.summary)}</p></div><dl><dt>Coordinates</dt><dd>\\(${system.field}\\)</dd><dt>Inventory</dt><dd>${escape(system.count)}</dd><dt>Rule status</dt><dd>${escape(system.status)}</dd></dl><div><h3>Matching rule</h3><p>${escape(system.rules)}</p><p>${system.action}</p></div><div><h3>Available here</h3><p>${escape(system.implementation)}</p><p class="catalog-sources">${system.sources.map(([label,url])=>`<a href="${escape(url)}" target="_blank" rel="noreferrer">${escape(label)} ↗</a>`).join('')}</p></div>`;typeset(meta);
  onSystem(system);
  try{const loaded=await loadSpecimens(system.id);if(token!==epoch)return;tiles=loaded;addCards();$('#catalog-state').textContent=tiles.length?`${tiles.length} ${tiles.length===1?'specimen':'specimens'} · drag to rotate · click to inspect`:'Source entry · no verified specimen mesh';if(tiles.length)show(tiles[0]);else $('#catalog-inspector').replaceChildren();}
  catch(e){$('#catalog-state').textContent=e.message;}
 }
 function addCards(){for(const t of tiles.slice(shown,shown+6)){
   const card=document.createElement('article');card.className='tile-card';const title=document.createElement('h3');title.textContent=t.name;const canvas=document.createElement('canvas');canvas.setAttribute('aria-label',`Rotate ${t.name} independently`);canvas.title='Drag to rotate · click a face to inspect';canvas.tabIndex=0;card.append(title,canvas);shelf.append(card);
   const chooseTile=face=>{show(t,face);$('#prototype-inspection').open=true;$('#prototype-inspection').scrollIntoView({behavior:'smooth',block:'start'});};
   const viewer=new TileViewer(canvas,{onFace:(_,face)=>chooseTile(face),color:t.id.includes('oblate')?'#70b9b2':'#ddb475'});viewer.setModel(t);
   canvas.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();chooseTile(null);}});
   const note=document.createElement('small');note.textContent=t.displayOnly?'Display mesh':t.note||t.id==='X1'?'Carrier · marking identity retained':system.id==='wang'?'View rotates; placements do not':'Exact coordinates';if(t.note)note.textContent=t.note;card.append(note);cards.push({id:t.id,element:card,viewer});
  }shown=Math.min(tiles.length,shown+6);$('#catalog-more').hidden=shown>=tiles.length;$('#catalog-more').textContent=`Show next ${Math.min(6,tiles.length-shown)} of ${tiles.length} tiles`;
 }
 select.onchange=()=>choose(select.value);$('#catalog-more').onclick=addCards;
 $('#catalog-download').onclick=()=>{if(!selected)return;const blob=new Blob([JSON.stringify({format:'gcts-polyhedral-specimen-v1',system,displayOnly:!!selected.displayOnly,scalar:selected.exact?'(a+b*tau)/d; tau^2=tau+1':null,specimen:{...selected,vertices:undefined,displayVertices:selected.vertices}},null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`${system.id}-${selected.id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
 $('#catalog-index').innerHTML=SYSTEMS.map(s=>`<tr><td><button data-system="${s.id}">${escape(s.name)}</button></td><td>${escape(s.count)}</td><td>\\(${s.field}\\)</td><td>${escape(s.status)}</td></tr>`).join('');for(const b of document.querySelectorAll('[data-system]'))b.onclick=()=>{choose(b.dataset.system);document.querySelector('.system-toolbar').scrollIntoView({behavior:'smooth',block:'start'});};typeset($('#catalog-index'));
 choose('ammann');
 return {get system(){return system;},get selected(){return selected;}};
}
