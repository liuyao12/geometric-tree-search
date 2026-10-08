(() => {
  'use strict';
  const dataElement = document.getElementById('mode-data');
  if (!dataElement) return;
  const data = JSON.parse(dataElement.textContent);
  const root = document.getElementById('spectrum-viewer');
  const get = id => document.getElementById(id);
  const math = value => '\\(' + value + '\\)';
  const number = value => Math.abs(value) < 1e-11 ? '0' : Number(value.toPrecision(8)).toString();
  const scientific = value => value === 0 ? '0' : value.toExponential(2).replace(/e([+-]?\d+)/, '\\times10^{$1}');
  const images = new Map();
  let domain = data.domains[0], selectedBC = 'D', selectedIndex = 0;
  let view = [0, 1], renderToken = 0, mathQueue = Promise.resolve();
  function typeset(elements) {
    if (window.MathJax?.typesetPromise) {
      mathQueue = mathQueue.catch(() => {}).then(() => window.MathJax.startup?.promise).then(() => window.MathJax.typesetPromise(elements));
    }
  }
  window.addEventListener('load', () => typeset([root]), {once:true});
  function replace(el, html) {
    window.MathJax?.typesetClear?.([el]);
    el.innerHTML = html;
  }
  const factor = () => get('spectrum-scale').value === 'pi' ? 1/(Math.PI**2) : get('spectrum-scale').value === 'area' ? domain.area : 1;
  const scaleLabel = () => ({pi:'\\lambda/\\pi^2', area:'A\\lambda', raw:'\\lambda'})[get('spectrum-scale').value];
  const spectrum = () => domain.spectra.find(s => s.bc === selectedBC);
  const visible = () => domain.spectra.filter(s => get('show-'+s.bc).checked);
  function fullRange() {
    const maximum = Math.max(...visible().flatMap(s => s.modes.map(m => m.value*factor())));
    return [0, maximum*1.03 || 1];
  }
  function lowRange() {
    const maximum = Math.max(...visible().map(s => s.modes[Math.min(11,s.modes.length-1)].value*factor()));
    return [0,maximum*1.07 || 1];
  }
  function fillModes() {
    const picker = get('spectrum-mode');
    picker.replaceChildren();
    for (const s of visible()) for (const m of s.modes) {
      const option = new Option(`${s.label} mode ${m.mode} · ${number(m.value*factor())}`, `${s.bc}:${m.index}`);
      picker.add(option);
    }
    picker.value = `${selectedBC}:${selectedIndex}`;
  }
  function drawChart() {
    const chart = get('spectrum-chart');
    window.MathJax?.typesetClear?.([chart]);
    chart.replaceChildren();
    chart.dataset.minimum = view[0]; chart.dataset.maximum = view[1]; chart.dataset.factor = factor();
    const style = getComputedStyle(chart);
    const width = Math.max(chart.clientWidth-parseFloat(style.paddingLeft)-parseFloat(style.paddingRight), 160);
    for (const s of visible()) {
      const band = document.createElement('div');
      band.className = 'spectrum-band bc-'+s.bc;
      band.dataset.bc = s.bc;
      const label = document.createElement('span');
      label.className = 'spectrum-band-label'; label.textContent = s.label;
      band.append(label);
      const lanes = [];
      for (const m of s.modes) {
        const value = m.value*factor();
        if (value < view[0] || value > view[1]) continue;
        const fraction = (value-view[0])/(view[1]-view[0]);
        let lane = lanes.findIndex(last => fraction*width-last >= 19);
        if (lane < 0) lane = lanes.length;
        lanes[lane] = fraction*width;
        const node = document.createElement('button');
        node.className = 'spectrum-node'+(m.exact_family ? ' family' : '')+(selectedBC === s.bc && selectedIndex === m.index ? ' selected' : '');
        node.type = 'button'; node.style.left = `${fraction*100}%`; node.style.top = `${37+lane*20}px`;
        node.dataset.value = m.value; node.dataset.index = m.index; node.dataset.bc = s.bc;
        node.setAttribute('aria-label', `${s.label} mode ${m.mode}`);
        node.setAttribute('aria-pressed', String(selectedBC === s.bc && selectedIndex === m.index));
        node.title = `${s.label} mode ${m.mode}: ${number(value)}${m.exact_family ? ' · constructed family' : ''}`;
        node.addEventListener('click', () => select(s.bc, m.index));
        const stem = document.createElement('span');
        stem.className = 'spectrum-stem'; stem.style.left = `${fraction*100}%`; stem.style.top = node.style.top;
        band.append(stem, node);
      }
      band.style.height = `${Math.max(70, 47+lanes.length*20)}px`;
      chart.append(band);
    }
    const axis = document.createElement('div'); axis.className = 'spectrum-axis';
    const rawStep = (view[1]-view[0])/5;
    const power = 10**Math.floor(Math.log10(rawStep));
    const step = [1,2,5,10].find(x => x*power >= rawStep)*power;
    for (let x = Math.ceil(view[0]/step)*step; x <= view[1]+step*1e-8; x += step) {
      const tick = document.createElement('span'); tick.className = 'spectrum-tick';
      tick.style.left = `${(x-view[0])/(view[1]-view[0])*100}%`; tick.innerHTML = math(number(x)); axis.append(tick);
    }
    chart.append(axis);
    const title = document.createElement('div'); title.className = 'spectrum-axis-title'; title.innerHTML = math(scaleLabel()); chart.append(title);
    replace(get('spectrum-range'), math(`${number(view[0])}\\le ${scaleLabel()}\\le ${number(view[1])}`));
    typeset([chart, get('spectrum-range')]);
  }
  function loadImage(atlas) {
    if (!images.has(atlas.file)) images.set(atlas.file, new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img); img.onerror = () => reject(new Error('Numerical field image could not be loaded.'));
      img.src = '../../research/spectral-tiling/'+atlas.file;
    }));
    return images.get(atlas.file);
  }
  async function drawField(s, m, token) {
    const canvas = get('spectrum-field'), ctx = canvas.getContext('2d');
    ctx.clearRect(0,0,canvas.width,canvas.height);
    get('spectrum-field-status').textContent = 'Loading numerical eigenfunction…';
    try {
      const img = await loadImage(s.atlas);
      if (token !== renderToken) return;
      const {cell_size:cell, columns:cols, bbox} = s.atlas;
      ctx.drawImage(img, (m.index%cols)*cell, Math.floor(m.index/cols)*cell, cell, cell, 0,0,canvas.width,canvas.height);
      const xy = p => [(p[0]-bbox[0])/(bbox[2]-bbox[0])*(canvas.width-1), (bbox[3]-p[1])/(bbox[3]-bbox[1])*(canvas.height-1)];
      domain.polygon.forEach((p, i) => {
        const a = xy(p), b = xy(domain.polygon[(i+1)%domain.polygon.length]);
        ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b); ctx.lineWidth = 3;
        ctx.strokeStyle = s.boundary_edges[i] === 'D' ? '#147b7b' : '#e09731';
        ctx.setLineDash(s.boundary_edges[i] === 'D' ? [] : [8,5]); ctx.stroke();
      });
      ctx.setLineDash([]);
      canvas.dataset.field = `${domain.id}:${s.bc}:${m.index}`;
      canvas.setAttribute('aria-label', `Numerical eigenfunction on ${domain.label}, ${s.label} mode ${m.mode}`);
      get('spectrum-field-status').textContent = 'Computed FEM eigenfunction; boundary types drawn on the outline.';
    } catch (error) {
      if (token !== renderToken) return;
      get('spectrum-field-status').textContent = error.message;
      get('spectrum-field-status').classList.add('spectrum-error');
    }
  }
  function drawDetail() {
    const s = spectrum(), m = s.modes[selectedIndex];
    const token = ++renderToken;
    const exact = m.exact_family;
    const symbol = s.bc === 'N' ? '\\mu' : s.bc === 'mixed' ? '\\nu' : '\\lambda';
    let html = `<h4>${domain.label} · ${s.label} · ${math(`${symbol}_{${m.mode}}`)}</h4><dl class="spectrum-metrics">`;
    for (const [label, value] of [
      ['Eigenvalue estimate', math(`${symbol}_{${m.mode}}\\approx ${number(m.value)}`)],
      ['Divided by squared pi', math(`${symbol}_{${m.mode}}/\\pi^2\\approx ${number(m.value/Math.PI**2)}`)],
      ['Area normalized', math(`A${symbol}_{${m.mode}}\\approx ${number(domain.area*m.value)}`)],
      ['Last refinement movement', math(scientific(m.last_change))],
      ['Mesh nodes / triangles', math(`${s.checks.nodes}\\;/\\;${s.checks.triangles}`)],
      ['Relative matrix residual', m.mode === 0 && s.bc === 'N' ? 'Constant mode checked separately' : math(scientific(m.relative_residual))]
    ]) html += `<div><dt>${label}</dt><dd>${value}</dd></div>`;
    html += '</dl>';
    if (exact) html += `<div class="spectrum-family"><p><strong>Known constructed family.</strong> Exact level ${math(`${exact.q}\\pi^2`)}; at least ${math(exact.constructed_multiplicity)} independent constructed mode${exact.constructed_multiplicity === 1 ? '' : 's'}. Numerical subspace projection ${math(number(exact.projection))}.</p></div>`;
    else html += '<p>No match to a constructed family is recorded for this mode. Its normalized algebraicity is unknown.</p>';
    html += `<p>${s.bc === 'mixed' ? 'Vertical edges: Dirichlet. Horizontal edges: Neumann. The constructed sine–cosine subset has coherent gluing on the translation tiling; this claim does not cover every mixed mode.' : s.bc === 'D' ? 'Dirichlet on the entire boundary: zero trace.' : 'Neumann on the entire boundary: zero normal derivative in the weak formulation. The zero mode is constant.'}</p>`;
    replace(get('spectrum-mode-detail'), html);
    get('spectrum-mode').value = `${s.bc}:${m.index}`;
    get('spectrum-previous').disabled = selectedIndex === 0;
    get('spectrum-next').disabled = selectedIndex === s.modes.length-1;
    get('spectrum-field-status').classList.remove('spectrum-error');
    typeset([get('spectrum-mode-detail')]);
    drawField(s,m,token);
  }
  function select(bc, index) {
    selectedBC = bc; selectedIndex = index;
    const x = spectrum().modes[index].value*factor();
    if (x < view[0] || x > view[1]) {
      const span = view[1]-view[0]; view = [Math.max(0,x-span/2), Math.max(0,x-span/2)+span];
    }
    drawChart(); drawDetail();
  }
  function resetDomain() {
    domain = data.domains.find(d => d.id === get('spectrum-domain').value);
    for (const bc of ['D','N','mixed']) {
      const input = get('show-'+bc); input.disabled = !domain.spectra.some(s => s.bc === bc);
      input.checked = !input.disabled; input.parentElement.hidden = input.disabled;
    }
    selectedBC = 'D'; selectedIndex = 0; view = lowRange(); fillModes(); drawChart(); drawDetail();
  }
  for (const d of data.domains) get('spectrum-domain').add(new Option(d.label,d.id));
  get('spectrum-domain').addEventListener('change', resetDomain);
  get('spectrum-scale').addEventListener('change', event => {
    const previousFactor = Number(get('spectrum-chart').dataset.factor);
    view = view.map(x => x*factor()/previousFactor); fillModes(); drawChart();
  });
  for (const bc of ['D','N','mixed']) get('show-'+bc).addEventListener('change', () => {
    if (!visible().length) get('show-'+bc).checked = true;
    if (!visible().some(s => s.bc === selectedBC)) { selectedBC = visible()[0].bc; selectedIndex = 0; }
    fillModes(); drawChart(); drawDetail();
  });
  get('spectrum-mode').addEventListener('change', event => { const [bc,index] = event.target.value.split(':'); select(bc,Number(index)); });
  get('spectrum-previous').addEventListener('click', () => select(selectedBC,selectedIndex-1));
  get('spectrum-next').addEventListener('click', () => select(selectedBC,selectedIndex+1));
  function zoom(ratio) {
    const x = spectrum().modes[selectedIndex].value*factor();
    const span = (view[1]-view[0])*ratio;
    view = [Math.max(0,x-span/2), Math.max(0,x-span/2)+span]; drawChart();
  }
  get('spectrum-zoom-in').addEventListener('click', () => zoom(.5));
  get('spectrum-zoom-out').addEventListener('click', () => zoom(2));
  get('spectrum-full').addEventListener('click', () => {view = fullRange(); drawChart();});
  get('spectrum-low').addEventListener('click', () => {
    view = lowRange();
    if (spectrum().modes[selectedIndex].value*factor() > view[1]) selectedIndex = 0;
    drawChart(); drawDetail();
  });
  let lastWidth = 0;
  new ResizeObserver(entries => {
    const width = entries[0].contentRect.width;
    if (Math.abs(width-lastWidth) > .5) { lastWidth = width; drawChart(); }
  }).observe(get('spectrum-chart'));
  resetDomain();
})();
