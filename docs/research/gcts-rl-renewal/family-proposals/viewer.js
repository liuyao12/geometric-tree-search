/* Read-only display of saved preparation records; no proof/search execution. */
'use strict';
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const math=s=>el('span','\\('+s+'\\)','math');
const safe=s=>String(s).replace(/[^a-zA-Z0-9]/g,'');
function term(a){
  if(!Array.isArray(a))throw Error('Unsupported term record');
  if(a[0]==='var')return '\\mathit{'+safe(a[1])+'}';
  if(a[0]==='fun')return '\\operatorname{'+safe(a[1])+'}'+(a[2].length?'('+a[2].map(term).join(',')+')':'');
  throw Error('Unsupported term constructor');
}
function formula(a){
  if(a[0]==='pred')return '\\operatorname{'+safe(a[1])+'}('+a[2].map(term).join(',')+')';
  if(a[0]==='eq')return term(a[1])+'='+term(a[2]);
  if(a[0]==='not')return '\\neg('+formula(a[1])+')';
  if(['and','or','imp'].includes(a[0]))return '('+formula(a[1])+({and:'\\land',or:'\\lor',imp:'\\to'}[a[0]])+formula(a[2])+')';
  if(['all','exists'].includes(a[0]))return (a[0]==='all'?'\\forall':'\\exists')+'\\mathit{'+safe(a[1])+'}\\,('+formula(a[2])+')';
  throw Error('Unsupported formula constructor');
}
function words(row){
  if(row.rule==='assumption')return 'Use this original hypothesis.';
  if(row.rule==='axiom')return 'Introduce an axiom from the declared theory.';
  if(row.rule==='instantiate')return 'Introduce the universal-instantiation implication for the declared term; applying it requires modus ponens.';
  if(row.rule==='eq_subst')return 'Introduce this equality substitution instance.';
  if(row.rule==='mp')return 'Apply modus ponens to the two ordered source rows shown on the tile.';
  return 'Read the declared primitive command in the exact record below.';
}
let saved,rendering=false;
async function render(){
  if(rendering)return;rendering=true;
  const select=document.querySelector('#group');select.disabled=true;
  try{
    const g=saved.groups[Number(select.value)],box=document.querySelector('#group-view');
    if(window.MathJax?.typesetClear)MathJax.typesetClear([box]);box.replaceChildren();
    const intro=el('p');intro.append('This saved proposal contains ',math(String(g.raw.distinct_member_count)),' distinct primitive placements. The original hypotheses are displayed first for reading its external receptors. It has not been executed as a search hint or admitted as a proof.');box.append(intro);
    const hierarchy=el('div',undefined,'hierarchy');
    g.raw.components.forEach((c,i)=>{const card=el('div',undefined,'component-card');card.append(el('strong','Component '+String(i+1)),math('('+c.ordered_input_rows.join(',')+')\\longrightarrow '+c.conclusion_row),el('small',c.name));hierarchy.append(card);});box.append(hierarchy);
    for(const row of g.rows){
      const line=el('div',undefined,'tile-line'),square=el('div',undefined,'square');
      square.append(math('t(0,'+row.row+')=1'));
      const blue=el('div',undefined,'blue-layer');blue.append(math('m(1,'+row.row+')='+row.code));
      row.input_codes.forEach((code,i)=>blue.append(el('div'),math('m(1,'+row.refs[i]+')='+code)));square.append(blue);
      const purple=el('div',undefined,'purple-layer');
      row.refs.forEach((ref,port)=>{const p=el('div');p.append(math('m('+(2+port)+','+row.row+')='+(ref-row.row)));purple.append(p);});square.append(purple);
      const text=el('div',undefined,'row-text');text.append(math('\\text{Row }'+row.row+':\\quad '+formula(row.formula)),el('p',words(row)));
      text.append(el('p',row.original_hypothesis?'Original context hypothesis.':(row.components.length>1?'Shared by both components; counted once in occupancy.':'Member of component '+row.components.join(',')+'.'),'membership'));
      if(row.refs.length){const p=el('p');p.append('Ordered sources: ',math('('+row.refs.join(',')+')'));text.append(p);}
      const d=el('details'),s=el('summary','Exact primitive and membership record');d.append(s,el('pre',JSON.stringify(row,null,2)));text.append(d);line.append(square,text);box.append(line);
    }
    const raw=el('details');raw.append(el('summary','Exact saved group record'),el('pre',JSON.stringify(g.raw,null,2)));box.append(raw);
    layers();if(window.MathJax?.typesetPromise)await MathJax.typesetPromise([box]);
    box.dataset.renderedGroup=select.value;
  }catch(e){document.querySelector('#group-view').append(el('p','Reader error: '+e.message,'reader-error'));}
  finally{select.disabled=false;rendering=false;}
}
function layers(){
  document.querySelectorAll('.blue-layer').forEach(e=>e.hidden=!document.querySelector('#blue').checked);
  document.querySelectorAll('.purple-layer').forEach(e=>e.hidden=!document.querySelector('#purple').checked);
}
async function start(){
  const response=await fetch('visual-data.json');if(!response.ok)throw Error('Saved data unavailable');saved=await response.json();
  const select=document.querySelector('#group');
  saved.groups.forEach((g,i)=>{const o=el('option',g.label);o.value=String(i);select.append(o);});
  if(!saved.groups.length){document.querySelector('#group-view').append(el('p','No complete proposal pool is available to display.'));return;}
  select.addEventListener('change',render);document.querySelector('#blue').addEventListener('change',layers);document.querySelector('#purple').addEventListener('change',layers);await render();
}
start().catch(e=>document.querySelector('#group-view').append(el('p','Reader error: '+e.message,'reader-error')));
