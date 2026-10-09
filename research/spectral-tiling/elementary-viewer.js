(() => {
  'use strict';
  const payload = document.getElementById('elementary-data');
  if (!payload) return;
  const data = JSON.parse(payload.textContent);
  const numerical = JSON.parse(document.getElementById('mode-data').textContent);
  const additional = document.getElementById('additional-elementary-data');
  if (additional) data.domains.push(...JSON.parse(additional.textContent).domains);
  const additionalNumeric = document.getElementById('additional-mode-data');
  if (additionalNumeric) numerical.domains.push(...JSON.parse(additionalNumeric.textContent).domains);
  const get = id => document.getElementById(id);
  const math = value => '\\(' + value + '\\)';
  const number = value => Number(value.toPrecision(8)).toString();
  const labels = {D:'All Dirichlet',N:'All Neumann',mixed:'Vertical Dirichlet / horizontal Neumann',shortD:'Short Dirichlet / long Neumann',longD:'Short Neumann / long Dirichlet'};
  let domain, family, selected = 0, view = [0,1], mathQueue = Promise.resolve();
  function typeset(elements) {
    if (window.MathJax?.typesetPromise) mathQueue = mathQueue.catch(() => {}).then(() => window.MathJax.startup?.promise).then(() => window.MathJax.typesetPromise(elements));
  }
  window.addEventListener('load',() => typeset([get('elementary-viewer')]),{once:true});
  function replace(el,html) {
    window.MathJax?.typesetClear?.([el]); el.innerHTML = html;
  }
  function exactLevel(m) {
    if (family.source_kind === 'square') return m.q === 0 ? '0' : `${m.q}\\pi^2`;
    return m.q === 0 ? '0' : m.q%3 === 0 ? `${16*m.q/3}\\pi^2` : `\\frac{${16*m.q}}{3}\\pi^2`;
  }
  function physicalFrequencies(m) {
    const [[a,b],[c,d]] = domain.lattice_basis, determinant = a*d-b*c;
    return m.frequencies_axial?.map(([p,q],i) => [(d*p-c*q)/determinant,(-b*p+a*q)/determinant,m.coefficients[i]]);
  }
  function evaluator(m) {
    if (family.source_kind === 'square') return (x,y) => Math[m.x_kind](Math.PI*m.m*x)*Math[m.y_kind](Math.PI*m.n*y);
    const frequencies = physicalFrequencies(m), trig = Math[m.trig];
    return (x,y) => frequencies.reduce((u,[kx,ky,c]) => u+c*trig(2*Math.PI*(kx*x+ky*y)),0);
  }
  function chart() {
    const el = get('elementary-chart'); window.MathJax?.typesetClear?.([el]); el.replaceChildren();
    el.dataset.minimum = view[0]; el.dataset.maximum = view[1];
    const band = document.createElement('div'); band.className = 'spectrum-band bc-'+family.bc;
    const label = document.createElement('span'); label.className = 'spectrum-band-label'; label.textContent = labels[family.bc]; band.append(label);
    const width = Math.max(el.clientWidth-48,160), lanes = [];
    family.modes.forEach((m,i) => {
      if (m.normalized_value < view[0] || m.normalized_value > view[1]) return;
      const fraction = (m.normalized_value-view[0])/(view[1]-view[0]);
      let lane = lanes.findIndex(last => fraction*width-last >= 19);
      if (lane < 0) lane = lanes.length; lanes[lane] = fraction*width;
      const node = document.createElement('button'); node.type = 'button';
      node.className = 'spectrum-node family'+(i === selected ? ' selected' : '');
      node.style.left = `${fraction*100}%`; node.style.top = `${37+lane*20}px`;
      node.dataset.normalizedValue = m.normalized_value; node.dataset.index = i;
      node.setAttribute('aria-label',`Exact ${domain.label} ${labels[family.bc]} level ${number(m.normalized_value)}, function ${i+1}`);
      node.setAttribute('aria-pressed',String(i === selected));
      node.title = `Exact normalized level ${number(m.normalized_value)} · elementary function ${i+1}`;
      node.addEventListener('click',() => select(i));
      const stem = document.createElement('span'); stem.className = 'spectrum-stem'; stem.style.left = node.style.left; stem.style.top = node.style.top;
      band.append(stem,node);
    });
    band.style.height = `${Math.max(70,47+lanes.length*20)}px`; el.append(band);
    const axis = document.createElement('div'); axis.className = 'spectrum-axis';
    const rawStep = (view[1]-view[0])/5, power = 10**Math.floor(Math.log10(rawStep));
    const step = [1,2,5,10].find(x => x*power >= rawStep)*power;
    for (let x = Math.ceil(view[0]/step)*step; x <= view[1]+step*1e-8; x += step) {
      const tick = document.createElement('span'); tick.className = 'spectrum-tick'; tick.style.left = `${100*(x-view[0])/(view[1]-view[0])}%`; tick.innerHTML = math(number(x)); axis.append(tick);
    }
    el.append(axis); const title = document.createElement('div'); title.className = 'spectrum-axis-title'; title.innerHTML = math('\\lambda/\\pi^2'); el.append(title); typeset([el]);
  }
  function inside(x,y,polygon) {
    let result = false;
    for (let i=0,j=polygon.length-1;i<polygon.length;j=i++) {
      const a = polygon[i], b = polygon[j];
      if ((a[1]>y) !== (b[1]>y) && x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]) result = !result;
    }
    return result;
  }
  function sample(canvas,polygon,fn) {
    const x = polygon.map(p=>p[0]), y = polygon.map(p=>p[1]);
    const cx = (Math.min(...x)+Math.max(...x))/2, cy = (Math.min(...y)+Math.max(...y))/2;
    const span = Math.max(Math.max(...x)-Math.min(...x),Math.max(...y)-Math.min(...y))*1.12;
    const size = canvas.width, values = new Float64Array(size*size); values.fill(NaN); let peak = 0;
    for (let j=0;j<size;j++) for (let i=0;i<size;i++) {
      const px = cx-span/2+span*i/(size-1), py = cy+span/2-span*j/(size-1);
      if (!inside(px,py,polygon)) continue;
      const value = fn(px,py); values[j*size+i] = value; peak = Math.max(peak,Math.abs(value));
    }
    return {canvas,polygon,cx,cy,span,values,peak};
  }
  const palette = [[5,48,97],[33,102,172],[146,197,222],[247,247,247],[244,165,130],[178,24,43],[103,0,31]];
  function paint(plot,conditions,peak,medians) {
    const {canvas,polygon,cx,cy,span,values} = plot, ctx = canvas.getContext('2d'), size = canvas.width;
    const pixels = ctx.createImageData(size,size);
    values.forEach((v,i) => {
      if (!Number.isFinite(v)) return;
      const p = Math.max(0,Math.min(6,3*(v/peak+1))), k = Math.min(5,Math.floor(p)), f = p-k;
      for (let c=0;c<3;c++) pixels.data[4*i+c] = Math.round(palette[k][c]*(1-f)+palette[k+1][c]*f);
      pixels.data[4*i+3] = 255;
    });
    ctx.putImageData(pixels,0,0);
    const xy = p => [(p[0]-cx+span/2)/span*(size-1),(cy+span/2-p[1])/span*(size-1)];
    function edge(a,b,condition,width) {
      ctx.beginPath(); ctx.moveTo(...xy(a)); ctx.lineTo(...xy(b)); ctx.lineWidth = width;
      ctx.strokeStyle = condition === 'D' ? '#147b7b' : '#e09731'; ctx.setLineDash(condition === 'D' ? [] : [6,4]); ctx.stroke();
    }
    polygon.forEach((p,i) => edge(p,polygon[(i+1)%polygon.length],conditions[i],2.2));
    if (medians) polygon.forEach((p,i) => edge(p,[(polygon[(i+1)%3][0]+polygon[(i+2)%3][0])/2,(polygon[(i+1)%3][1]+polygon[(i+2)%3][1])/2],medians,1));
    ctx.setLineDash([]);
  }
  function formula(m) {
    if (family.source_kind === 'square') return `u(x,y)=\\${m.x_kind}(${m.m}\\pi x)\\,\\${m.y_kind}(${m.n}\\pi y)`;
    const [[a,b],[c,d]] = domain.lattice_basis;
    const rotated = Math.abs(c) > 1e-10;
    const argument = rotated ? '\\frac{2p-q}{\\sqrt3}x+qy' : 'px+\\frac{2q-p}{\\sqrt3}y';
    return `u(x,y)=\\sum_{(p,q)\\in\\mathcal O}c_{p,q}\\${m.trig}\\!\\left(2\\pi\\left(${argument}\\right)\\right)`;
  }
  function detail() {
    const m = family.modes[selected], sourceName = family.source_kind === 'square' ? 'Unit square' : 'Unit equilateral triangle';
    const fn = evaluator(m), source = sample(get('elementary-source'),domain.source_polygon,fn), tile = sample(get('elementary-tile'),domain.polygon,fn);
    const peak = Math.max(source.peak,tile.peak) || 1;
    paint(source,family.source_boundary,peak,family.median_boundary); paint(tile,family.boundary_edges,peak);
    for (const [canvas,label] of [[source.canvas,sourceName],[tile.canvas,domain.label]]) {
      canvas.dataset.function = `${domain.id}:${family.bc}:${m.id}`;
      canvas.setAttribute('aria-label',`Explicit elementary function on ${label}, exact normalized level ${number(m.normalized_value)}`);
    }
    get('elementary-source-caption').textContent = sourceName+(family.median_boundary ? `; ${family.median_boundary === 'D' ? 'odd' : 'even'} median symmetry` : '');
    get('elementary-tile-caption').textContent = `${domain.label}; ${labels[family.bc]}`;
    let html = `<h4>Exact level ${math('\\lambda='+exactLevel(m))}</h4><p>${math(formula(m))}</p>`;
    html += family.source_kind === 'square' ? `<p>Indices ${math(`(m,n)=(${m.m},${m.n})`)}. The sine factor forces zero trace on that edge family; the cosine factor forces zero normal derivative.</p>` :
      `<p>Frequency orbit generated by ${math(`(m,n)=(${m.representative.join(',')})`)}; ${math(`Q=${m.q}`)}. Triangle sides are ${family.source_boundary[0] === 'D' ? 'Dirichlet' : 'Neumann'}; its medians are ${family.median_boundary === 'D' ? 'odd' : 'even'} reflection lines.</p><details><summary>Explicit frequency coefficients</summary><p>${math('\\mathcal O;\\ c_{p,q}:\\quad '+m.frequencies_axial.map((k,i)=>`(${k.join(',')}):${m.coefficients[i]}`).join(',\\;'))}</p></details>`;
    html += `<p>Induced tile problem: <strong>${labels[family.bc]}</strong>. This level has at least ${math(m.constructed_multiplicity)} independent functions in this constructed family. Extra tile multiplicity is unknown.</p>`;
    if (family.constant_only) html += '<p>Only the universal Neumann constant has been added to this exact catalogue for this shape. Its gradient is zero on every edge, regardless of direction. No nonconstant compatible elementary family is asserted here.</p>';
    if (!family.constant_only) html += '<p class="spectrum-note">Exact boundary certificate: odd affine reflection gives zero trace; even affine reflection gives zero normal derivative on each open edge. The receipts verify the mirror and translation phase for every edge. Corners use the weak boundary formulation.</p>';
    if (domain.tiling_status) html += `<p>${domain.tiling_status} <a href="${domain.source_url}" target="_blank" rel="noopener">Primary source</a>.</p>`;
    const problem = numerical.domains.find(d=>d.id === domain.id).spectra.find(s=>s.bc === family.bc);
    const matches = problem.modes.filter(mode=>(m.q === 0 && family.bc === 'N' && mode.mode === 0) || (mode.exact_family && mode.exact_family.q === m.q && (family.source_kind === 'square' || ['mixed_reflection','triangle_reflection'].includes(mode.exact_family.family))));
    const candidates = problem.modes.filter(mode=>mode.candidate_families?.some(c=>c.q === m.q));
    const target = m.normalized_value*Math.PI**2;
    let index;
    if (matches.length) {
      index = matches[0].index;
      html += `<p>Recorded numerical family match: mode${matches.length === 1 ? '' : 's'} ${math(matches.map(mode=>mode.mode).join(',\\;'))}. A numerical basis need not equal the displayed elementary basis function.</p>`;
      get('elementary-numerical').textContent = 'Inspect numerical family match';
    } else if (candidates.length) {
      index = candidates[0].index;
      html += `<p>Numerical identification remains unresolved; candidate modes ${math(candidates.map(mode=>mode.mode).join(',\\;'))} are retained.</p>`;
      get('elementary-numerical').textContent = 'Inspect unresolved numerical candidates';
    } else {
      index = problem.modes.reduce((best,mode)=>Math.abs(mode.value-target)<Math.abs(problem.modes[best].value-target) ? mode.index : best,0);
      html += `<p>${target > problem.modes.at(-1).value ? 'This exact level is above the current numerical list’s cutoff.' : 'No numerical subspace match is recorded at this exact level.'} The exact construction does not depend on numerical identification.</p>`;
      get('elementary-numerical').textContent = target > problem.modes.at(-1).value ? 'Open computed spectrum' : 'Inspect nearby numerical modes';
    }
    get('elementary-numerical').onclick = () => {
      document.dispatchEvent(new CustomEvent('inspect-spectrum',{detail:{domain:domain.id,bc:family.bc,index}}));
      get('spectrum-viewer').scrollIntoView({behavior:'smooth',block:'start'});
    };
    replace(get('elementary-detail'),html); get('elementary-level').value = String(selected);
    get('elementary-previous').disabled = selected === 0; get('elementary-next').disabled = selected === family.modes.length-1;
    get('elementary-status').textContent = 'Same explicit function on the source cell and tile; formula evaluated on a plotting grid.';
    typeset([get('elementary-detail')]);
  }
  function select(index) {
    selected = index; const value = family.modes[index].normalized_value;
    if (value < view[0] || value > view[1]) { const span = view[1]-view[0]; view = [Math.max(0,value-span/2),Math.max(0,value-span/2)+span]; }
    chart(); detail();
  }
  function resetFamily() {
    family = domain.families.find(f=>f.bc === get('elementary-family').value); selected = 0;
    const levels = get('elementary-level'); levels.replaceChildren();
    family.modes.forEach((m,i)=>levels.add(new Option(`Exact level ${number(m.normalized_value)} · function ${i+1}`,String(i))));
    view = [0,(family.modes[Math.min(11,family.modes.length-1)].normalized_value || 1)*1.08]; chart(); detail();
  }
  function resetDomain() {
    domain = data.domains.find(d=>d.id === get('elementary-domain').value);
    get('elementary-family').replaceChildren(); domain.families.forEach(f=>get('elementary-family').add(new Option(f.label,f.bc))); resetFamily();
  }
  data.domains.forEach(d=>get('elementary-domain').add(new Option(d.label,d.id)));
  get('elementary-domain').value = 'sphinx';
  get('elementary-domain').addEventListener('change',resetDomain);
  get('elementary-family').addEventListener('change',resetFamily);
  get('elementary-level').addEventListener('change',()=>select(Number(get('elementary-level').value)));
  get('elementary-previous').addEventListener('click',()=>select(selected-1));
  get('elementary-next').addEventListener('click',()=>select(selected+1));
  get('elementary-full').addEventListener('click',()=>{view=[0,(family.modes.at(-1).normalized_value || 1)*1.05];chart();});
  get('elementary-low').addEventListener('click',resetFamily);
  let lastWidth = 0;
  new ResizeObserver(entries=>{const width=entries[0].contentRect.width;if(Math.abs(width-lastWidth)>.5){lastWidth=width;chart();}}).observe(get('elementary-chart'));
  resetDomain();
})();
