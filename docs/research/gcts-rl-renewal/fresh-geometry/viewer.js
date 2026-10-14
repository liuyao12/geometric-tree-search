(() => {
  'use strict';
  const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
  const math=s=>'\\('+s+'\\)';
  const num=n=>{if(!Number.isSafeInteger(n)||n<0)throw Error('Invalid saved count');return String(n).replace(/\B(?=(\d{3})+(?!\d))/g,'\\,');};
  function formula(a){
    if(!Array.isArray(a))throw Error('Missing formula AST');
    if(a[0]==='fun'&&a.length===3&&Array.isArray(a[2])&&a[2].length===0&&/^[A-Za-z]+$/.test(a[1]))return a[1];
    if(a[0]==='eq'&&a.length===3)return formula(a[1])+'='+formula(a[2]);
    if(a[0]==='pred'&&a[1]==='Incident'&&Array.isArray(a[2])&&a[2].length===2)return '\\operatorname{Incident}('+a[2].map(formula).join(',')+')';
    throw Error('Unexpected saved calibration AST');
  }
  const typeset=n=>window.MathJax&&MathJax.typesetPromise?MathJax.typesetPromise([n]):Promise.resolve();
  function seedDrawing(code){
    const ns='http://www.w3.org/2000/svg',s=document.createElementNS(ns,'svg');s.setAttribute('viewBox','0 0 150 90');s.setAttribute('role','img');s.setAttribute('aria-label','One actual occupancy point and its formula-code marking');
    for(const [tag,attrs] of [['rect',{x:15,y:20,width:44,height:44,fill:'#edf5fb',stroke:'#1b6ea8'}],['line',{x1:37,y1:42,x2:115,y2:42,stroke:'#a9b6c1','stroke-dasharray':'3 3'}],['circle',{cx:37,cy:42,r:5,fill:'#263341'}],['circle',{cx:115,cy:42,r:9,fill:'hsl('+code%360+' 55% 45%)',stroke:'#263341'}]]){const p=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))p.setAttribute(k,String(v));s.append(p);}return s;
  }
  function renderCase(c,index){
    if(c.proof_search_status!=='UNSEARCHED'||c.discovered_proofs!==0||!c.static_qualification_accepted||c.initial_row_receipts.length!==24)throw Error('Wrong static-only scope');
    const card=el('article',undefined,'case');card.id=c.id;card.append(el('h2',index===0?'Equality in the first argument':'Equality in the second argument'),el('p',c.statement_latex),el('p','UNSEARCHED · complete static qualification accepted','muted'));
    const table=el('table'),tbody=el('tbody');for(const [label,value] of [['Formulas',c.dimensions.formula_count],['Primitive licences',c.dimensions.primitive_license_count],['Logical row obligations',c.dimensions.logical_rows],['Complete initial candidates',c.complete_initial_candidate_count],['Inventory bodies',c.dimensions.source_body_count]]){const r=el('tr');r.append(el('th',label),el('td',math(num(value))));tbody.append(r);}table.append(tbody);card.append(table);
    const seeds=el('div',undefined,'seeds');c.initial_seed_placements.forEach((p,i)=>{if(JSON.stringify(p.command.formula)!==JSON.stringify(c.hypothesis_asts[i])||p.t.length!==1||p.m.length!==1)throw Error('Saved seed binding differs');const f=el('figure',undefined,'seed');f.append(seedDrawing(p.m[0][2]),el('figcaption',math('\\Gamma_{'+i+'}: '+formula(p.command.formula))),el('p',math('t(0,'+i+')=1,\\quad m(1,'+i+')='+p.m[0][2])),el('p','Fixed hypothesis · translation only','muted'));seeds.append(f);});card.append(el('h3','Actual starting hypotheses'),seeds);
    const legend=el('div',undefined,'legend');legend.append(el('span','Fixed hypothesis','fixed'),el('span','Unfilled row','open'),el('span','Conclusion boundary','target'));card.append(el('h3','All row domains remain available'),legend);
    const grid=el('div',undefined,'grid'),detail=el('div',undefined,'detail');detail.setAttribute('role','region');detail.setAttribute('aria-label','Selected row evidence');const buttons=[];
    const choose=r=>{buttons.forEach((b,j)=>b.setAttribute('aria-pressed',String(j===r.row)));detail.replaceChildren(el('strong','Saved row evidence'),el('p',math('t(0,'+r.row+')='+c.initial_state.totals[r.row]+',\\quad |D_{'+r.row+'}|='+num(r.count))),el('p',math('\\text{Factors}='+num(r.factor_count)+',\\quad\\text{encoded bytes}='+num(r.bytes))));const mark=c.initial_state.marks.find(a=>a[0]===1&&a[1]===r.row);detail.append(el('p',mark?math('m(1,'+r.row+')='+mark[2]):'Formula marking is absent at this row; absence is unconstrained.'));if(r.row<3)detail.append(el('p',math(formula(c.hypothesis_asts[r.row]))));if(r.row===23)detail.append(el('p','Required conclusion: '+math(formula(c.target_ast))));const d=el('details');d.append(el('summary','Exact complete row receipt'),el('pre',JSON.stringify(r,null,2)));detail.append(d);typeset(detail);};
    c.initial_row_receipts.forEach(r=>{const b=el('button',math('\\rho_{'+r.row+'}'),'row'+(r.row<3?' fixed':r.row===23?' target':''));b.type='button';b.setAttribute('aria-label','Row '+r.row+(r.row<3?' fixed hypothesis':r.row===23?' conclusion boundary':' unfilled'));b.setAttribute('aria-pressed','false');b.append(el('small',r.row<3?'Fixed':r.row===23?'Target':'Open'));b.addEventListener('click',()=>choose(r));buttons.push(b);grid.append(b);});card.append(grid,detail);choose(c.initial_row_receipts[3]);
    const rules=el('details'),rt=el('table');rules.append(el('summary','Every primitive rule family was retained'));for(const [rule,count] of Object.entries(c.rule_counts)){const tr=el('tr'),td=el('td');td.append(el('code',rule));tr.append(td,el('td',math(num(count))));rt.append(tr);}rules.append(rt);card.append(rules);return card;
  }
  async function main(){
    const response=await fetch('summary.json');if(!response.ok)throw Error('Summary could not be loaded');const d=await response.json();if(d.schema!=='ROOT-accepted-fresh-geometry-complete-static-contexts-v1'||d.proof_searches!==0||d.cases.length!==2||!d.all_four_complete_static_stages_accepted)throw Error('Unexpected qualification scope');
    document.querySelector('#status').textContent='Both complete static contexts accepted. Four actual phases; no proof searches or discovered proofs at this cutoff.';
    const cases=document.querySelector('#cases');d.cases.forEach((c,i)=>cases.append(renderCase(c,i)));
    const table=el('table'),head=el('tr');['Context / actual phase','Caller time','Owned post-write time','Conservative peak'].forEach(t=>head.append(el('th',t)));table.append(head);d.cases.forEach((c,i)=>c.resources.forEach(r=>{const tr=el('tr');tr.append(el('td',(i===0?'First argument context':'Second argument context')+' / '+r.stage),el('td',math(r.caller_elapsed_seconds.toFixed(3)+'\\,\\mathrm{s}')),el('td',math(r.owned_post_write_seconds.toFixed(6)+'\\,\\mathrm{s}')),el('td',math((r.conservative_peak_bytes/1048576).toFixed(2)+'\\,\\mathrm{MiB}')));table.append(tr);}));document.querySelector('#resources').append(table,el('p','All fourteen resource predicates passed in each phase. These are construction and static-audit costs; they are not proof-search timings.','muted'));
    const artifacts=document.querySelector('#artifacts'),list=el('ul');d.public_artifacts.forEach(a=>{const li=el('li'),link=el('a',a.label);link.href=a.url;li.append(link);list.append(li);});artifacts.append(el('details'));const details=artifacts.firstChild;details.append(el('summary','Download complete raw evidence'),list);
    await typeset(document.querySelector('main'));
  }
  main().catch(e=>{document.querySelector('#status').textContent='Saved records could not be displayed: '+e.message;console.error(e);});
})();
