/* Inspect an audited pilot. This reader does not rerun search or learn values. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const equal = (a,b) => JSON.stringify(a) === JSON.stringify(b);
  const need = (condition,message) => { if (!condition) throw Error(message); };
  const key = p => p.join(',');
  const element = (tag,content,className) => {
    const node = document.createElement(tag); if(content!==undefined)node.textContent=content;
    if(className)node.className=className; return node;
  };
  const atom = value => String(value).replace(/[\\{}_%#$&^~]/g,ch=>`\\${ch}`);
  function term(t) { return t[0]==='var' ? atom(t[1]) : `\\operatorname{${atom(t[1])}}${t[2].length?'('+t[2].map(term).join(',')+')':''}`; }
  function formula(f) {
    if(f[0]==='pred')return `\\operatorname{${atom(f[1])}}${f[2].length?'('+f[2].map(term).join(',')+')':''}`;
    if(f[0]==='eq')return `${term(f[1])}=${term(f[2])}`;
    if(f[0]==='all')return `\\forall ${atom(f[1])}\\,(${formula(f[2])})`;
    if(f[0]==='bot')return '\\bot';
    if(f[0]==='not')return `\\neg(${formula(f[1])})`;
    const op={imp:'\\Rightarrow',and:'\\land',or:'\\lor'}[f[0]];
    need(op,'supported formula');return `(${formula(f[1])}${op}${formula(f[2])})`;
  }
  function formulaWords(f) {
    if(f[0]==='pred')return f[1];
    if(f[0]==='imp')return `${formulaWords(f[1])} implies ${formulaWords(f[2])}`;
    if(f[0]==='all')return `for every ${f[1]}, ${formulaWords(f[2])}`;
    if(f[0]==='eq')return 'reflexive equality';
    return f[0];
  }
  const math = (latex,className) => element('div',`\\(${latex}\\)`,className);
  let typesetting=Promise.resolve();
  function typeset() {
    typesetting=typesetting.then(async()=>{
      if(window.MathJax?.startup?.promise){await MathJax.startup.promise;await MathJax.typesetPromise();}
    });return typesetting;
  }
  function validate(c) {
    const counts={}; c.probes.forEach(p=>{counts[p.label]=(counts[p.label]||0)+1;
      need(p.status===({positive:'finite_marked_proof_region',negative:'exhausted_finite_marked_region',unknown:'unknown_search_budget'})[p.label],'teacher outcome');
    });need(Object.keys(counts).every(k=>counts[k]===c.certificate.counts[k]),'teacher counts');
    need(c.failures.length===(counts.negative||0),'all negative values, no unknown constraint');
    for(const f of c.failures){
      const p=c.probes.find(p=>p.id===f.probe);need(p?.label==='negative'&&p.slot===f.slot&&equal(p.formula,f.formula),'failure provenance');
      need(equal(f.point,[4*f.slot+3,100000+c.basis.findIndex(b=>equal(b,f.formula))]),'exact failure coordinate');
      need(f.exterior_value===0&&f.tile_value===1,'unequal assigned values');
      need(equal(f.support.map(c=>c.key),f.affected_keys),'all affected identities');
      const bytes=[...new TextEncoder().encode(JSON.stringify(f.formula)),256];
      for(const r of f.representatives){
        need(f.support.some(c=>equal(c.key,r.key)&&c.kind===r.kind),'representative identity');
        const m=new Map(r.marks.map(([p,v])=>[key(p),v]));
        need(m.get(key(f.point))===1,'extra tile value');
        bytes.forEach((v,k)=>need(m.get(key([4*f.slot,100+k]))===v,'every source word byte and terminator'));
        need(r.occupancy.length===1&&r.occupancy[0][1]===12,'original occupancy');
      }
    }
    const marks=new Map(); const totals=new Map();
    const assign=(p,v)=>{let k=key(p);need(!marks.has(k)||marks.get(k)===v,'complete selected marking agreement');marks.set(k,v);};
    c.failures.forEach(f=>assign(f.point,0));
    [...new TextEncoder().encode(JSON.stringify(c.spec.target)),256].forEach((v,k)=>assign([4*(c.spec.length-1),100+k],v));
    for(const p of c.selected){p.occupancy.forEach(([q,v])=>totals.set(key(q),(totals.get(key(q))||0)+v));p.marks.forEach(([q,v])=>assign(q,v));}
    need(totals.size===c.spec.length*(2+c.arity)&&[...totals.values()].every(v=>v===12),'whole selected exact target');
    c.proof.forEach((command,j)=>{
      const bare={...command};delete bare.inputs;
      const cs=c.selected.filter(p=>p.slot===j&&p.key[1]<2);
      need(cs.length===2&&cs.every(p=>equal(p.command,bare)),'displayed command/guard proof binding');
      if(command.rule==='block'){
        const inputs=c.selected.filter(p=>p.slot===j&&p.kind==='lemma_input').sort((a,b)=>a.input-b.input);
        need(equal(inputs.map(p=>p.source),command.inputs)&&inputs.every(p=>p.source<j),'strict earlier lemma inputs');
      }
    });
    need(c.native.some(q=>q.id===c.proof_query&&q.result.status==='accepted'),'actual fresh native root check');
  }
  const labels={ 'two-premise':'Propositional implication', 'pa-universal-equality':'Universal equality', 'renamed-five':'Five-link implication chain' };
  let data, current;
  function svg(tag,attrs,text) {
    const n=document.createElementNS('http://www.w3.org/2000/svg',tag);
    Object.entries(attrs||{}).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;return n;
  }
  function draw(c,p,f) {
    const root=$('marking-view');root.replaceChildren();
    const title=svg('text',{x:25,y:28,fill:'#28463a','font-size':20},f?'Actual alternative candidates and their added failure point':'No extra marking is assigned for this prefix');root.append(title);
    const sourceY=95, sourceX=80;
    root.append(svg('text',{x:25,y:sourceY-28,'font-size':18},`Formula port on line ${p.slot+1}`));
    const bytes=[...new TextEncoder().encode(JSON.stringify(p.formula)),256];
    bytes.forEach((v,i)=>root.append(svg('rect',{x:sourceX+i*11,y:sourceY-8,width:8,height:16,fill:'#80569e'})));
    root.append(svg('text',{x:25,y:sourceY+36,'font-size':17,fill:'#596b61'},`All ${bytes.length} assigned word values, including the terminator`));
    if(!f){
      root.append(svg('rect',{x:45,y:200,width:720,height:160,fill:p.label==='positive'?'#e0eddc':'#f2e8ca',rx:5}));
      root.append(svg('text',{x:70,y:254,'font-size':17},p.label==='positive'?'A complete original prefix was found.':'The original teacher reached its budget.'));
      root.append(svg('text',{x:70,y:287,'font-size':14},'Neither outcome authorizes an exclusion point.'));return;
    }
    const portX=700,portY=365;
    f.representatives.forEach((r,i)=>{
      const x=85+i*220,y=240;const color=r.kind==='lemma_input'?'#377fa0':r.kind==='guard'?'#b98528':'#80569e';
      root.append(svg('rect',{x,y,width:62,height:62,fill:'#eef0e4',stroke:color,'stroke-width':4}));
      root.append(svg('text',{x:x+31,y:y+36,'text-anchor':'middle','font-size':15},r.kind==='command'?'C':r.kind==='guard'?'G':'Input'));
      root.append(svg('text',{x:x-15,y:y+90,'font-size':18},`${r.kind.replace('_',' ')} · line ${r.slot+1}`));
      root.append(svg('path',{d:`M${x+31},${y} Q${x+31},155 ${sourceX+bytes.length*5.5},${sourceY}`,fill:'none',stroke:color,'stroke-width':2}));
      root.append(svg('path',{d:`M${x+62},${y+40} Q${x+115},${portY} ${portX},${portY}`,fill:'none',stroke:'#b34851','stroke-width':2}));
    });
    root.append(svg('circle',{cx:portX,cy:portY,r:12,fill:'#b34851'}));
    root.append(svg('text',{x:25,y:portY+67,'font-size':18},'Tile assigns one; fixed boundary assigns zero.'));
    root.append(svg('text',{x:25,y:portY+96,'font-size':17,fill:'#9b414b'},'The ordinary marking comparison rejects the candidate.'));
  }
  function showProbe() {
    const p=current.probes.find(p=>String(p.id)===$('probe-control').value);
    const f=current.failures.find(f=>f.probe===p.id);
    $('failure-summary').replaceChildren(math(`F_{${p.slot+1}}=${formula(p.formula)}`,'statement'),
      element('p',`Test: a prefix of ${p.slot+1} logical lines ending with this formula.`));
    const status=$('label-status');status.className=`notice ${p.label}`;
    status.replaceChildren(element('strong',p.label==='negative'?'Certified exclusion':p.label==='positive'?'Witnessed positive':'Unresolved — no exclusion'),
      element('p',`${p.metrics.nodes||0} visited nodes; ${p.metrics.attempts||0} attempted placements.`));
    if(f)status.append(element('p',`${f.support.length} decorated candidates share this failure point: `+
      Object.entries(f.by_kind).map(([k,v])=>`${v} ${k.replace('_',' ')}`).join(', ')+'.'));
    draw(current,p,f);$('exact-data').textContent=JSON.stringify({probe:p,failure:f||null},null,2);typeset();
  }
  function reason(c,row) {
    if(row.rule==='axiom')return `Use the given hypothesis named ${row.name}.`;
    if(row.rule==='mp')return `Line ${row.antecedent+1} supplies the antecedent. Apply the implication on line ${row.implication+1}.`;
    if(row.rule==='generalize')return `Universally quantify ${row.variable} in line ${row.source+1}. The native checker verifies the scope condition.`;
    if(row.rule==='refl')return 'Use reflexivity of equality.';
    if(row.rule==='tautology')return 'Use a native-admitted propositional tautology.';
    if(row.rule==='block'){
      const d=c.inventory.definitions.find(d=>d.name===row.name);
      if(!row.inputs.length)return `Apply the checked closed lemma at level ${d?.level||1}. It has no local hypotheses.`;
      return `Apply the checked lemma interface at level ${d?.level||1} to earlier lines ${row.inputs.map(i=>i+1).join(', ')}. Each ordered premise is matched exactly.`;
    }return row.rule;
  }
  function showCase() {
    current=data.cases.find(c=>c.id===$('case-control').value);
    $('probe-control').replaceChildren(...current.probes.map(p=>{
      const o=element('option',`Line ${p.slot+1} · ${p.label} · ${formulaWords(p.formula)}`);o.value=p.id;return o;
    }));
    const preferred=current.failures.filter(f=>f.by_kind.lemma_input).sort((a,b)=>b.slot-a.slot)[0]||current.failures[0];
    if(preferred)$('probe-control').value=preferred.probe;showProbe();
    $('proof-context').replaceChildren(element('span','From the declared hypotheses, the search establishes '),math(formula(current.spec.target)),element('span',` Fresh native query ${current.proof_query} accepted.`));
    $('proof-lines').replaceChildren(...current.proof.map((row,i)=>{
      const n=element('div',undefined,'proof-line'),body=element('div');
      n.append(element('span',`Line ${i+1}`,'line-number'));body.append(math(formula(row.formula),'formula'),element('p',reason(current,row),'small'));
      if(row.rule==='block'){
        const d=current.inventory.definitions.find(d=>d.name===row.name),detail=element('details');
        detail.append(element('summary','Read the checked lemma interface'),math(d.definition.premises.map(formula).join('\\quad ')+`\\;\\vdash\\;${formula(d.definition.conclusion)}`));body.append(detail);
      }n.append(body);return n;
    }));
    $('all-results').textContent=JSON.stringify({case:current.id,census:current.census,observations:current.observations,native:current.native},null,2);typeset();
  }
  async function main() {
    const response=await fetch('certified-prefix-reader-001.json?v=20261011-cp1');need(response.ok,'reader data load');data=await response.json();
    need(data.audit.status==='passed'&&data.audit.native_queries===7,'completed audit');data.cases.forEach(validate);
    $('case-control').replaceChildren(...data.cases.map(c=>{const o=element('option',labels[c.id]);o.value=c.id;return o;}));
    $('case-control').value='renamed-five';$('case-control').addEventListener('change',showCase);$('probe-control').addEventListener('change',showProbe);
    data.cases.forEach(c=>{
      for(const mode of ['base','fixed','learned']){
        const row=element('tr');row.append(element('td',labels[c.id]),element('td',mode));
        for(const variant of ['original','output-only','all-writers']){
          const r=c.observations.find(o=>o.mode===mode&&(variant==='original'?!o.marked:o.marked&&o.variant===variant));
          const cell=element('td',`\\(${r.metrics.attempts||0}\\)${r.status==='unknown_search_budget'?' · unknown':''}`,'num');row.append(cell);
        }$('results-body').append(row);
      }
    });
    const long=data.cases.find(c=>c.id==='renamed-five'),a=data.audit;
    $('diagnosis').append(element('strong','Diagnosis from the complete point domains'),
      element('p',`${long.census.initial_before} initially legal incidences become ${long.census.initial_after}. Both constructions make ${long.census.forced_before} initial forced placements in the same sequence. The first branch and its candidates agree. ${long.census.changed_roots_after_forcing.length} remaining root domains differ.`));
    const costs=element('table');data.cases.forEach(c=>{const r=element('tr');r.append(element('td',labels[c.id]),element('td',`${c.probes.length} prefixes`),element('td',`${c.learning_seconds.toFixed(3)} seconds`));costs.append(r);});$('learning-costs').append(costs);
    $('audit-summary').textContent=`Independent replay covers ${a.teacher_nodes.toLocaleString()} teacher nodes, ${a.point_nodes.toLocaleString()} paired search nodes, ${a.events.toLocaleString()} policy decisions, ${a.hints.toLocaleString()} hints and all ${a.native_queries} fresh native computations. The tiny complete census preserves all ${a.finite_equivalence.original_regions} valid regions.`;
    const links=element('p');data.artifacts.forEach((r,i)=>{if(i)links.append(document.createTextNode(' · '));const link=element('a',r.name);link.href=r.name;links.append(link);});$('artifact-links').append(links);
    $('reader-status').textContent='Loaded: all three declarations, negative/unknown provenance, representative exact marking words, and whole selected proof targets checked in the reader. Native acceptance is independently replayed evidence, not a browser execution.';
    showCase();await typeset();
  }
  main().catch(error=>{$('reader-status').textContent=`Evidence reader failed: ${error.message}`;console.error(error);});
})();
