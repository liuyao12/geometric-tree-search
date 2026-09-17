// Visualize published receipts, not new measurements or a simulated search.
const slot=document.querySelector('#rv-scene-slot'),scene=document.querySelector('#ice-inspection');
if(slot&&scene){
  slot.append(scene);
  const archive=document.createElement('details'),title=document.createElement('summary');
  title.textContent='Historical six-case coverage comparison';archive.append(title);
  for(const selector of ['.ice-legend','.ice-caption','[data-ice-chart]']){const node=scene.querySelector(selector);if(node)archive.append(node);}
  scene.insertBefore(archive,scene.querySelector('figcaption'));
}
const host=document.querySelector('[data-rv-chart]');
if(host){
 try{
  const response=await fetch(new URL('ice-frozen-frame-transfer/summary.json',import.meta.url));if(!response.ok)throw Error('Result receipt unavailable');
  const data=await response.json(),runs=[{channels:0,complete:20,baseCoversRetained:20,totals:data.baseTotals},...data.runs];
  if(runs.length!==5||data.runs.some(r=>r.rows.length!==20))throw Error('Unexpected result dimensions');
  function draw(mode){
   host.replaceChildren();const matrix=document.createElement('div');matrix.className='rv-matrix';
   for(const title of ['Channels','Ih','II','VI','VIII']){const e=document.createElement('span');e.className='rv-col';e.textContent=title;matrix.append(e);}
   for(const run of runs){
    const label=document.createElement('span');label.className='rv-label';label.textContent=run.channels===0?'None':String(run.channels);matrix.append(label);
    for(let phase=0;phase<4;phase++){
     const group=document.createElement('div');group.className='rv-phase';
     for(let i=0;i<5;i++){
      const row=run.rows?.[phase*5+i],pass=run.channels===0?true:mode==='complete'?row.complete:row.baseCoverRetained;
      const dot=document.createElement('span');dot.className='rv-dot';dot.dataset.pass=String(pass);dot.title=`${['Ih','II','VI','VIII'][phase]}, frame ${50+i}: ${pass?'yes':'no'}`;group.append(dot);
     }matrix.append(group);
    }
   }
   host.append(matrix);host.setAttribute('aria-label',runs.map(r=>`${r.channels} channels: ${mode==='complete'?r.complete:r.baseCoversRetained} of 20 ${mode==='complete'?'reconstructed':'original covers retained'}`).join('; '));
   document.querySelector('[data-rv-explanation]').textContent=mode==='complete'?'Filled teal squares: a verified reconstruction was found. All 20 targets complete at every tested channel count.':'Filled teal: the saved unmarked cover remains valid. Outlined amber: that cover is rejected, but a different verified filling is found. Retained: 20, 5, 0, 0, 0 of 20.';
   for(const b of document.querySelectorAll('[data-rv-mode]'))b.setAttribute('aria-pressed',String(b.dataset.rvMode===mode));
  }
  const work=document.querySelector('[data-rv-work]'),max=Math.max(...runs.map(r=>r.totals.backtracks));
  for(const r of runs){const row=document.createElement('div');row.className='rv-work-row';const label=document.createElement('span');label.textContent=`${r.channels} ch.`;const track=document.createElement('div');track.className='rv-work-track';const bar=document.createElement('span');bar.style.width=`${r.totals.backtracks/max*100}%`;track.append(bar);const value=document.createElement('span');value.textContent=r.totals.backtracks;row.append(label,track,value);work.append(row);}
  const caption=document.createElement('p');caption.textContent='Backtracks · common zero baseline';work.prepend(caption);
  for(const button of document.querySelectorAll('[data-rv-mode]'))button.onclick=()=>draw(button.dataset.rvMode);draw('complete');
 }catch(error){host.textContent=`Chart unavailable: ${error.message}. The protocol and downloadable receipts remain available.`;}
}
