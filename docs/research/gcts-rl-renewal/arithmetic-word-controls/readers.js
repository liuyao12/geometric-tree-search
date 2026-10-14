/* Saved-presentation renderer only. No semantic/checker/fixture execution. */
(() => {
  'use strict';
  const SCHEMA = 'ROOT-unrelated-word-controls-display-packet-v1';
  const byId = id => document.getElementById(id);
  const colors = {assumption:'#8865a8',axiom:'#6c7782',instantiate:'#307dac',eq_subst:'#307dac',mp:'#c97c32',generalize:'#258572'};
  let packet = null, selected = null, visible = [], mathTail = Promise.resolve();
  const node = (tag, text, className) => {
    const value = document.createElement(tag);
    if (text !== undefined && text !== null) value.textContent = String(text);
    if (className) value.className = className;
    return value;
  };
  const clear = value => { value.replaceChildren(); return value; };
  const isObject = value => value && typeof value === 'object' && !Array.isArray(value);
  const literal = value => JSON.stringify(value);
  function texName(value) {
    if (typeof value !== 'string') return '\\text{invalid symbol literal}';
    return '\\mathrm{' + value.replace(/[\\{}_$%&#^~]/g, c => ({'\\':'\\backslash{}','{':'\\{','}':'\\}','_':'\\_','$':'\\$','%':'\\%','&':'\\&','#':'\\#','^':'\\textasciicircum{}','~':'\\textasciitilde{}'}[c])) + '}';
  }
  function term(value, depth = 0) {
    if (!Array.isArray(value) || depth > 96) return '\\text{invalid term AST}';
    if (value[0] === 'var' && value.length === 2) return texName(value[1]);
    if (value[0] === 'fun' && value.length === 3 && Array.isArray(value[2])) {
      return texName(value[1]) + (value[2].length ? '\\left(' + value[2].map(t => term(t, depth + 1)).join(',') + '\\right)' : '');
    }
    return '\\text{unsupported term AST}';
  }
  function formula(value, depth = 0) {
    if (!Array.isArray(value) || depth > 96) return '\\text{invalid formula AST}';
    if (value[0] === 'eq' && value.length === 3) return term(value[1], depth + 1) + '=' + term(value[2], depth + 1);
    if (value[0] === 'pred' && value.length === 3 && Array.isArray(value[2])) {
      return texName(value[1]) + (value[2].length ? '\\left(' + value[2].map(t => term(t, depth + 1)).join(',') + '\\right)' : '');
    }
    if (value[0] === 'imp' && value.length === 3) return '\\left(' + formula(value[1], depth + 1) + '\\longrightarrow ' + formula(value[2], depth + 1) + '\\right)';
    if (value[0] === 'all' && value.length === 3) return '\\forall ' + texName(value[1]) + '\\;\\left(' + formula(value[2], depth + 1) + '\\right)';
    return '\\text{unsupported formula AST}';
  }
  const math = tex => node('div', '\\[' + tex + '\\]', 'formula');
  function safeLink(parent, label, href) {
    if (typeof href !== 'string') { parent.append(node('span', label + ' (link not attached)')); return; }
    try {
      const url = new URL(href, window.location.href);
      if (!['http:','https:'].includes(url.protocol)) throw Error('unsupported link protocol');
      const a = node('a', label); a.href = url.href; parent.append(a);
    } catch (_) { parent.append(node('span', label + ' (invalid presentation link)')); }
  }
  const flag = value => value === true ? 'accepted in the attached ROOT scope' : value === false ? 'not accepted' : 'pending';
  function typeset(elements) {
    mathTail = mathTail.then(async () => {
      if (window.MathJax?.startup?.promise) await window.MathJax.startup.promise;
      if (window.MathJax?.typesetPromise) await window.MathJax.typesetPromise(elements);
    }).catch(error => { byId('load-status').textContent = 'Math rendering failed: ' + error.message + '. Raw ASTs remain in the literal packet.'; });
  }
  function validate(value) {
    if (!isObject(value) || value.schema !== SCHEMA || !['pending','complete','failed'].includes(value.status)) throw Error('unrecognized ROOT display packet');
    if (!Array.isArray(value.records) || !Array.isArray(value.costs) || !Array.isArray(value.evidence) || !Array.isArray(value.prior_failures)) throw Error('whole explicit presentation arrays required');
    if (value.call_metrics !== null && (!isObject(value.call_metrics) || !['cases_completed','API_started','API_returned','API_exceptions'].every(k => Number.isInteger(value.call_metrics[k]) && value.call_metrics[k] >= 0))) throw Error('explicit recorded call metrics or null required');
    const ids = new Set();
    for (const record of value.records) {
      const f = record?.fixture;
      if (!isObject(f) || typeof f.id !== 'string' || ids.has(f.id) || !['check_primitive_word','Boundary'].includes(f.api) || !isObject(f.wire) || !isObject(f.expected)) throw Error('complete unique literal fixture records required');
      if (!['accept','reject'].includes(f.expected.status)) throw Error('literal accept/reject expectation required');
      ids.add(f.id);
      if (record.actual !== null && (!isObject(record.actual) || record.actual.id !== f.id || record.actual.api !== f.api)) throw Error('actual result identity does not match its literal fixture');
    }
    if (value.records.length && value.records.length !== 68) throw Error('partial fixture arrays are not the declared whole suite');
    if (value.records.length === 68 && (value.records.filter(r => r.fixture.api === 'check_primitive_word').length !== 56 || value.records.filter(r => r.fixture.api === 'Boundary').length !== 12)) throw Error('whole56-word/12-boundary split required');
    if (value.status === 'complete' && (value.records.length !== 68 || value.records.some(r => r.actual === null))) throw Error('complete presentation needs every actual record; no accepted prefix');
    if (!isObject(value.authority) || !['resource_accepted','reconciled_controls_accepted'].every(k => [true,false,null].includes(value.authority[k]))) throw Error('separate ROOT scope flags required');
    for (const field of ['Q_target_proof_discovered','native_accepted','full24_accepted','full_trajectory_accepted','full_PA_accepted','induction_accepted','GCTS_RL_advantage_established']) if (value.authority[field] !== false) throw Error('stronger proof/performance claim outside this reader');
    return value;
  }
  function expectedText(f) {
    return f.expected.status === 'accept' ? 'return expected' : String(f.expected.exception) + ' expected';
  }
  function actualText(record) {
    const a = record.actual;
    if (a === null) return 'pending';
    return a.error_type ? String(a.error_type) + ': input rejected' : 'returned';
  }
  function outcomeBadge(record) {
    const a = record.actual;
    return node('span', a === null ? 'Actual outcome pending' : a.all_checks_passed === true ? 'Saved expectation match' : 'Saved expectation mismatch / incomplete', 'badge ' + (a === null ? '' : a.all_checks_passed === true ? 'good' : 'bad'));
  }
  function orderedPorts(command) {
    if (!isObject(command)) return [];
    if (command.rule === 'mp') return [{port:0,field:'antecedent',row:command.antecedent},{port:1,field:'implication',row:command.implication}];
    if (command.rule === 'generalize') return [{port:0,field:'source',row:command.source}];
    return [];
  }
  function english(command) {
    switch (command?.rule) {
      case 'axiom': return 'Requests the displayed named original axiom. The exact name is retained below.';
      case 'assumption': return 'Requests the indexed original hypothesis occurrence. Equal repeated hypotheses keep separate occurrence indexes.';
      case 'instantiate': return 'Requests a universal-instantiation implication with the displayed universal formula and replacement term. This licence consumes no prior row.';
      case 'eq_subst': return 'Requests the equality-substitution implication for the displayed atomic template, placeholder and ordered operands. This licence consumes no prior row.';
      case 'mp': return 'Requests modus ponens: the first ordered port is the antecedent and the second is the implication. Port order is not interchangeable.';
      case 'generalize': return 'Requests unary universal introduction from the displayed prior row. Freshness is checked against the entire original undischarged context, including unused and duplicate occurrences.';
      default: return 'The unrecognized rule is retained literally. This display supplies no inference licence.';
    }
  }
  function detailsValue(parent, title, value) {
    const d = node('details'); d.append(node('summary', title), node('pre', JSON.stringify(value, null, 2))); parent.append(d);
  }
  function renderCommands(parent, record) {
    const commands = record.fixture.wire.commands;
    if (!Array.isArray(commands)) { parent.append(node('p', 'The commands field is malformed or absent; see the full literal fixture.')); return; }
    const section = node('div', null, 'commands scroll'); const table = node('table');
    const head = node('tr'); ['Row / rule','Requested formula','Ordered prior ports','English / literal operands','Saved certificate row'].forEach(t => head.append(node('th',t)));
    table.append(head);
    const savedRows = record.actual?.complete_positive_record?.rows;
    commands.forEach((command, index) => {
      const tr = node('tr'); const rule = isObject(command) ? command.rule : null;
      const address = node('td'); address.append(node('code', 'row ' + index + ' / ' + String(rule ?? 'invalid'))); tr.append(address);
      const out = node('td'); out.append(math(formula(command?.formula))); tr.append(out);
      const ports = node('td'); const list = orderedPorts(command);
      ports.append(node('code', list.length ? list.map(p => 'port ' + p.port + ' ' + p.field + ': ' + literal(p.row)).join('\n') : 'no ordered prior port')); tr.append(ports);
      const explanation = node('td'); explanation.append(node('p',english(command)));
      if (rule === 'assumption') explanation.append(node('code','original occurrence index: '+literal(command.index)));
      if (rule === 'axiom') explanation.append(node('code','axiom name: '+literal(command.name)));
      if (rule === 'generalize') explanation.append(node('code','bound variable: '+literal(command.variable)));
      if (rule === 'instantiate') { explanation.append(node('div','Universal formula', 'literal-label'),math(formula(command.universal)),node('div','Replacement term','literal-label'),math(term(command.term))); }
      if (rule === 'eq_subst') { explanation.append(node('code','placeholder: '+literal(command.variable)),node('div','Atomic template','literal-label'),math(formula(command.template)),node('div','Left / right operands','literal-label'),math(term(command.left)+'\\ ;\\quad '+term(command.right))); }
      tr.append(explanation);
      const certificate = node('td'); const saved = Array.isArray(savedRows) ? savedRows.find(r => r.row === index) : null;
      if (saved) certificate.append(node('p','Metadata from the saved whole-word certificate'),node('code','ordered prior rows: '+literal(saved.ordered_prior_rows)),node('code','formula SHA256: '+String(saved.formula_sha256)));
      else certificate.append(node('p',record.actual === null ? 'Pending' : 'No accepted row certificate attached. Rejection grants no prefix.'));
      tr.append(certificate); table.append(tr);
    });
    section.append(table); parent.append(section);
  }
  function svgElement(name, attrs = {}, text) {
    const e = document.createElementNS('http://www.w3.org/2000/svg', name);
    for (const [key,value] of Object.entries(attrs)) e.setAttribute(key,String(value));
    if (text !== undefined) e.textContent=String(text);
    return e;
  }
  function renderDiagram(record) {
    const parent = clear(byId('word-diagram')); const commands = record.fixture.wire.commands;
    if (!Array.isArray(commands) || !commands.length) { parent.append(node('p','No commanded rows to draw.')); return; }
    const height=80+commands.length*94; const svg=svgElement('svg',{viewBox:'0 0 820 '+height,role:'img','aria-label':'Literal proof-word row addresses and ordered prior references; no compiled tile board'});
    const defs=svgElement('defs');
    for (const [id,color] of [['prior','#c97c32'],['invalid','#b53f45']]) { const marker=svgElement('marker',{id:'arrow-'+id,viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:6,markerHeight:6,orient:'auto-start-reverse'});marker.append(svgElement('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:color}));defs.append(marker); }
    svg.append(defs);
    commands.forEach((command,index) => {
      const y=40+index*94; const color=colors[command?.rule] || '#b53f45';
      svg.append(svgElement('rect',{x:205,y,width:545,height:60,rx:5,fill:'#fff',stroke:color,'stroke-width':2}),svgElement('rect',{x:205,y,width:10,height:60,fill:color}));
      svg.append(svgElement('text',{x:233,y:y+25,fill:'#20322d','font-size':17},'row '+index+'  ·  '+String(command?.rule ?? 'malformed command')));
      svg.append(svgElement('text',{x:233,y:y+46,fill:'#5c6c66','font-size':12},'Formula and literal operands in the table above'));
    });
    commands.forEach((command,index) => orderedPorts(command).forEach(p => {
      const toY=40+index*94+20+p.port*20; const valid=Number.isInteger(p.row) && p.row>=0 && p.row<index;
      const present=Number.isInteger(p.row) && p.row>=0 && p.row<commands.length;
      const fromY=present ? 40+p.row*94+30 : toY-30;
      const x=70+p.port*44; const color=valid ? '#c97c32' : '#b53f45';
      const d=present ? 'M 205 '+fromY+' H '+x+' V '+toY+' H 202' : 'M '+x+' '+(toY-25)+' V '+toY+' H 202';
      svg.append(svgElement('path',{d,fill:'none',stroke:color,'stroke-width':2,'stroke-dasharray':valid ? 'none' : '5 4','marker-end':'url(#arrow-'+(valid?'prior':'invalid')+')'}));
      svg.append(svgElement('text',{x:118,y:toY-6,fill:color,'font-size':10},'port '+p.port+': '+literal(p.row)));
      if (!valid) svg.append(svgElement('text',{x:20,y:toY+28,fill:color,'font-size':10},'non-prior / malformed address'));
    }));
    parent.append(svg);
  }
  function renderSelected() {
    const parent=byId('selected-control');
    if (window.MathJax?.typesetClear) window.MathJax.typesetClear([parent]); clear(parent);
    const record=packet.records.find(r=>r.fixture.id===selected);
    if (!record) {parent.append(node('p','No actual control selected.','pending'));byId('diagram-section').hidden=true;return;}
    const f=record.fixture; parent.append(node('h3',f.id),node('p',f.description),node('span',f.api==='Boundary'?'NONLOGICAL boundary mechanics':'Authored logical word','badge'),outcomeBadge(record));
    parent.append(node('p','Expected: '+expectedText(f)+'; actual: '+actualText(record)+'.'));
    if (record.actual?.message) parent.append(node('p','Saved rejection message: '+record.actual.message));
    if (f.api==='Boundary') {
      byId('diagram-section').hidden=true;
      parent.append(node('p','This case uses an invented callback and private Boundary instance. Temporary code/default/closure changes or deadline/visit-limit probes are mechanics controls. They are not logical rows, a mathematical conclusion, or mutations of the production worker guard.'));
      detailsValue(parent,'Literal toy operation / expected outcome', {wire:f.wire,expected:f.expected});
    } else {
      byId('diagram-section').hidden=false;
      const columns=node('div',null,'two-columns'); const gamma=node('article'); gamma.append(node('h3','Original indexed context'));
      if (Array.isArray(f.wire.original_Gamma) && !f.wire.original_Gamma.length) gamma.append(math('\\Gamma=\\varnothing'));
      else if (Array.isArray(f.wire.original_Gamma)) f.wire.original_Gamma.forEach((g,index)=>gamma.append(node('div','Original occurrence '+index,'literal-label'),math(formula(g))));
      else gamma.append(node('p','Malformed original-context field; preserved in raw fixture.'));
      const axioms=node('article');axioms.append(node('h3','Original named axioms'));
      const declaredAxioms=f.wire.theory?.axioms;
      if (isObject(declaredAxioms) && Object.keys(declaredAxioms).length) Object.entries(declaredAxioms).forEach(([name,value])=>axioms.append(node('code',name),math(formula(value))));
      else axioms.append(node('p','No named original axioms.'));
      parent.append(axioms);
      const target=node('article');target.append(node('h3','Exact requested final target'),math(formula(f.wire.target)),node('code','parameters: '+literal(f.wire.parameters)));
      columns.append(gamma,target);parent.append(columns);
      const accepted=record.actual?.complete_positive_record;
      if (accepted) parent.append(node('p','Saved consumed original occurrence indexes: '+literal(accepted.consumed_original_occurrence_indices)+'. The whole original context remains preserved; ancestry consumption and weakening are separate.'),node('code','saved essential rows: '+literal(accepted.essential_rows)));
      renderCommands(parent,record);renderDiagram(record);
    }
    detailsValue(parent,'Complete original fixture',f);detailsValue(parent,'Complete actual result (null means pending)',record.actual);
    typeset([parent]);
  }
  function renderIndex() {
    const q=byId('filter').value.trim().toLowerCase();
    visible=packet.records.filter(r=>(r.fixture.id+' '+r.fixture.category+' '+expectedText(r.fixture)+' '+actualText(r)).toLowerCase().includes(q));
    const select=clear(byId('case-select')); visible.forEach(r=>{const option=node('option',r.fixture.id+' · '+r.fixture.category);option.value=r.fixture.id;select.append(option);});
    select.disabled=!visible.length;
    if (!visible.some(r=>r.fixture.id===selected)) selected=visible[0]?.fixture.id ?? null;
    if (selected) select.value=selected;
    const parent=clear(byId('case-table'));const table=node('table');const header=node('tr');['Control / type','Expected','Actual','Recorded expectation match'].forEach(t=>header.append(node('th',t)));table.append(header);
    visible.forEach(r=>{const tr=node('tr',null,r.fixture.id===selected?'selected-row':'');const id=node('td');const button=node('button',r.fixture.id,'row-button');button.type='button';button.addEventListener('click',()=>{selected=r.fixture.id;renderIndex();renderSelected();});id.append(button,node('div',r.fixture.api==='Boundary'?'NONLOGICAL_BOUNDARY':r.fixture.category,'scope-line'));tr.append(id,node('td',expectedText(r.fixture)),node('td',actualText(r)));const matched=node('td');matched.append(outcomeBadge(r));tr.append(matched);table.append(tr);});
    parent.append(node('p',visible.length+' of '+packet.records.length+' literal control records shown.'),table);
    if (!visible.length) parent.append(node('p','No record matches this filter. No case is omitted from the attached packet.','pending'));
  }
  function renderScopes() {
    const parent=clear(byId('scope-flags'));
    for (const [title,k] of [['ROOT resource acceptance','resource_accepted'],['Reconciled control scope','reconciled_controls_accepted']]) parent.append(node('div',title+': '+flag(packet.authority[k]),'card'));
    const metrics=clear(byId('call-metrics'));
    if (packet.call_metrics === null) metrics.append(node('p','No actual API count is attached. Cases and API invocations are separate.','pending'));
    else { const m=packet.call_metrics;metrics.append(node('p','Attached records report '+m.cases_completed+' completed control cases and '+m.API_started+' started API invocations: '+m.API_returned+' returns and '+m.API_exceptions+' exceptions. API exceptions include expected rejections; these are not discovered proofs or a control-failure count.')); }
    const authors=clear(byId('authorship'));
    authors.append(node('p','The suite and cold worker were authored by /root/hilbert_advice_controls; the independent semantic auditor by /root/hilbert_ordering_diagnosis; distinct Source review by /root/arithmetic_induction. ROOT owns the recorded actual activation, resource decision and publication. Authored fixture words test mechanics and are not automatic theorem discovery.','scope-line'));
    if (Array.isArray(packet.authorship)) packet.authorship.forEach(row=>authors.append(node('p',row.label+': '+row.identity,'scope-line')));
  }
  function renderCosts() {
    const parent=clear(byId('cost-table')); if (!packet.costs.length) {parent.append(node('p','No actual whole cost is attached.','pending'));return;}
    const wrap=node('div',null,'scroll');const table=node('table');const header=node('tr');['Phase / scope','Actual elapsed','Actual peak','Finish reserve / custody'].forEach(t=>header.append(node('th',t)));table.append(header);
    packet.costs.forEach(c=>{const tr=node('tr');tr.append(node('td',c.label+' — '+c.clock_scope));const seconds=node('td');seconds.append(typeof c.seconds==='number'?math(String(c.seconds)+'\\,\\mathrm{s}'):node('span','not attached'));tr.append(seconds);const peak=node('td');peak.append(typeof c.peak_bytes==='number'?math(String(c.peak_bytes)+'\\,\\mathrm{B}'):node('span','not attached'));tr.append(peak);const scope=node('td');scope.append(node('p',c.includes));if(typeof c.finish_reserve_seconds==='number') scope.append(math(String(c.finish_reserve_seconds)+'\\,\\mathrm{s}'));if(c.href)safeLink(scope,'Exact evidence',c.href);tr.append(scope);table.append(tr);});wrap.append(table);parent.append(wrap);
  }
  function renderLinks() {
    const failures=clear(byId('failure-records'));if(!packet.prior_failures.length) failures.append(node('p','No preserved failure presentation is attached.','pending'));
    packet.prior_failures.forEach(f=>{const box=node('div',null,'card');box.append(node('h3',f.label),node('p',f.status+' — '+f.scope));safeLink(box,'Preserved raw failure',f.href);failures.append(box);});
    const links=clear(byId('evidence-links'));const list=node('ul',null,'links');packet.evidence.forEach(e=>{const li=node('li');safeLink(li,e.label,e.href);if(e.sha256)li.append(node('code',' SHA256 '+e.sha256));list.append(li);});links.append(list);
    if(!packet.evidence.length)links.append(node('p','No raw record links are attached.','pending'));
    byId('packet-json').textContent=JSON.stringify(packet,null,2);
  }
  async function init() {
    try {
      const response=await fetch('display-packet-v1.json',{cache:'no-store'});
      if (!response.ok) {byId('load-status').textContent='Pending: ROOT has not attached the reconciled presentation packet. This reader contains no actual outcomes.';return;}
      packet=validate(await response.json());
      byId('load-status').textContent=packet.status==='complete'?'Full saved control presentation attached. ROOT resource and reconciled-control scopes are stated separately below.':packet.status==='failed'?'Failed / incomplete attempt attached. No completed-control or proof prefix is accepted by this display.':'Pending presentation. Expected fixture mechanics may be inspected; no actual success is implied.';
      selected=packet.records.find(r=>r.fixture.id==='gen-genuine-unary')?.fixture.id ?? null;
      byId('filter').disabled=!packet.records.length;renderScopes();renderCosts();renderLinks();renderIndex();renderSelected();typeset([byId('costs')]);
      byId('case-select').addEventListener('change',()=>{selected=byId('case-select').value;renderIndex();renderSelected();});byId('filter').addEventListener('input',()=>{renderIndex();renderSelected();});
    } catch (error) {byId('load-status').textContent='Presentation remains unaccepted: '+error.message+'. No scientific or semantic checker was run.';}
  }
  init();
})();
