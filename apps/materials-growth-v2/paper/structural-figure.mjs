const $=id=>document.getElementById(id);
const node=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
const pct=x=>x===null?'Not defined':`${(100*x).toFixed(1)}%`;
try{
  const response=await fetch('structural-results.json');if(!response.ok)throw Error('Data unavailable');
  const report=await response.json();
  function render(){
    const id=$('structure-material').value,epsilon=id==='copper'?.03:Number($('structure-epsilon').value),step=Number($('structure-step').value),factor=Number($('structure-window').value);
    $('structure-epsilon').disabled=id==='copper';
    const target=$('structure-comparison');target.replaceChildren();
    for(const strict of [false,true]){
      const row=report.results.find(r=>r.id===id&&r.epsilon===epsilon&&r.observedOnly===strict);
      const point=row.checkpoints.find(c=>c.step===step),m=point?.metrics;
      const card=node('div');card.className='quality-card';card.append(node('h3',strict?'Observed-overlap restricted':'Occupancy-only'));
      if(!m){card.append(node('p',`No checkpoint: ${row.status}`));target.append(card);continue;}
      const w=m.windows.find(w=>w.factor===factor);
      card.append(node('p',`${m.atoms} atoms · ${point.stats.backtracks} backtracks · ${point.types} support types`));
      for(const [label,value] of [['Correct-site precision',m.sitePrecision],['Window site coverage',w.siteRecall],['Reference-neighbor recovery',w.neighborRecall]]){
        const line=node('div');line.className='bar-row';line.append(node('div',`${label}: ${pct(value)}`));
        const track=node('div');track.className='track';track.setAttribute('aria-hidden','true');const bar=node('div');bar.className=`bar ${strict?'':'global'}`;bar.style.width=`${100*(value??0)}%`;track.append(bar);line.append(track);card.append(line);
      }
      card.append(node('p',`${w.coveredSites}/${w.referenceSites} reference sites covered within radius ${w.radius.toFixed(3)}. Atom-count ceiling: ${pct(Math.min(m.atoms,w.referenceSites)/w.referenceSites)}.`));
      card.append(node('p',`${w.recoveredEdges}/${w.expectedEdges} reference neighbor incidences recovered around ${w.centers} matched inner-window centres.`));
      card.append(node('p',`Composition TV: ${m.compositionTV.toFixed(3)} · angle-histogram TV: ${w.angleTV===null?'not defined':w.angleTV.toFixed(3)} (0 = equal distributions).`));
      card.append(node('p',Object.entries(m.counts).map(([s,n])=>`${s}: ${n}`).join(' · ')));
      target.append(card);
    }
  }
  for(const id of ['structure-material','structure-epsilon','structure-step','structure-window'])$(id).addEventListener('change',render);
  render();
}catch(error){$('structure-comparison').textContent='Interactive data unavailable. See Table 2 and the downloadable raw records.';console.error(error);}
