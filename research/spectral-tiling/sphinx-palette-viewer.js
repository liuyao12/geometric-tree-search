(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('palette-data').textContent);
  const get = id => document.getElementById(id);
  const picker = get('palette-state');
  const math = value => '\\(' + value + '\\)';
  let queue = Promise.resolve();
  const typeset = elements => {
    if (window.MathJax?.typesetPromise) queue = queue.catch(() => {}).then(() => window.MathJax.startup?.promise).then(() => window.MathJax.typesetPromise(elements));
  };
  const replace = (element, html) => {window.MathJax?.typesetClear?.([element]);element.innerHTML=html;};
  const physical = p => [p[0]+p[1]/2,p[1]*Math.sqrt(3)/2];
  const bump = z => Math.abs(z)<1 ? Math.exp(1-1/(1-z*z)) : 0;
  const stops = [[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
  function color(z) {
    const v = Math.min(1,Math.max(0,z/150))**.4*4;
    const index = Math.min(3,Math.floor(v)), alpha=v-index;
    return stops[index].map((c,i) => Math.round(c*(1-alpha)+stops[index+1][i]*alpha));
  }
  function selected() {return data.states.find(s => s.id === picker.value);}
  function updateCoefficient() {
    const index = Number(get('spectrum-mode').value.split(':')[1]);
    const state=selected(), projection=data.projections.find(s=>s.id===state.id);
    if (!Number.isInteger(index)) return;
    const coefficient=projection.coefficients_first_180[index];
    const fraction=coefficient*coefficient/projection.sampled_target_squared_mass_norm;
    const formatted=coefficient.toPrecision(7).replace(/e([+-]?\d+)/,'\\times10^{$1}');
    replace(get('palette-coefficient'),'<p><strong>Coefficient in '+math(state.role+'_{'+state.wang_id+'}')+'</strong></p><p>'+math('c_{'+index+'}\\approx '+formatted)+'</p><p>Contribution to the sampled squared mass norm: '+math((100*fraction).toFixed(3)+'\\%')+'.</p>');
    typeset([get('palette-coefficient')]);
  }
  function updateField() {
    const state=selected(), canvas=get('palette-field'), ctx=canvas.getContext('2d');
    const width=canvas.width,height=canvas.height;
    const xmin=-.15,xspan=3.3,ymin=-.15,yspan=Math.sqrt(3)+.3;
    const edges=data.edges.map(([p,q]) => {p=physical(p);q=physical(q);return {p,t:[q[0]-p[0],q[1]-p[1]]};});
    const image=ctx.createImageData(width,height);
    for (let y=0;y<height;y++) for(let x=0;x<width;x++) {
      const px=xmin+x*xspan/(width-1),py=ymin+(height-1-y)*yspan/(height-1);
      let value=0;
      for(let j=0;j<8;j++) {
        const {p,t}=edges[j],dx=px-p[0],dy=py-p[1],s=dx*t[0]+dy*t[1],r=-(dx*t[1]-dy*t[0]);
        value+=state.amplitudes[j]*bump(4*(s-.5))*Math.exp(2*state.profile_direction*(s-.5))*bump(8*r);
      }
      const c=color(value),offset=4*(y*width+x);
      image.data.set([...c,255],offset);
    }
    const xy=p=>[(p[0]-xmin)/xspan*(width-1),(height-1)-(p[1]-ymin)/yspan*(height-1)];
    const path=new Path2D();data.polygon.forEach((p,i)=>{const v=xy(p);i?path.lineTo(...v):path.moveTo(...v);});path.closePath();
    const scratch=document.createElement('canvas');scratch.width=width;scratch.height=height;scratch.getContext('2d').putImageData(image,0,0);
    ctx.clearRect(0,0,width,height);ctx.save();ctx.clip(path);ctx.drawImage(scratch,0,0);ctx.restore();
    ctx.strokeStyle='#25353a';ctx.lineWidth=2;ctx.stroke(path);
    canvas.dataset.state=state.id;canvas.setAttribute('aria-label','Exact total field '+state.id+' on the sphinx; homogeneous Neumann on all sides');
    replace(get('palette-amplitudes'),'Boundary amplitudes: '+math('a=('+state.amplitudes.join(',')+')')+'. Fixed color scale: '+math('0\\le u\\le150')+'.');
    const projection=data.projections.find(s=>s.id===state.id),last=projection.truncations.at(-1);
    replace(get('palette-truncation'),'The first '+math('180')+' FEM modes capture '+math((100*last.sampled_target_mass_fraction).toFixed(2)+'\\%')+' of this sampled squared mass norm. Maximum sampled boundary error / target peak: '+math((100*last.maximum_sampled_boundary_value_error_over_peak).toFixed(2)+'\\%')+'.');
    typeset([get('palette-amplitudes'),get('palette-truncation')]);updateCoefficient();
  }
  for(const state of data.states) picker.add(new Option(state.id+' · '+(state.role==='A'?'forward':'reversed')+' boundary profiles',state.id));
  picker.addEventListener('change',updateField);
  get('spectrum-mode').addEventListener('change',updateCoefficient);
  get('spectrum-viewer').addEventListener('click',()=>queueMicrotask(updateCoefficient));
  window.addEventListener('load',()=>typeset([get('palette-amplitudes'),get('palette-truncation'),get('palette-coefficient')]),{once:true});
  updateField();
})();
