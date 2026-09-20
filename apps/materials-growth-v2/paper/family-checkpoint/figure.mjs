const figure=document.querySelector('#family-checkpoint');
if(figure){
  try{
    const response=await fetch(new URL('./results.json',import.meta.url));
    if(!response.ok)throw Error(`Evidence request: ${response.status}`);
    const data=await response.json();
    const tabs=figure.querySelector('[data-fc-tabs]');
    const chart=figure.querySelector('[data-fc-chart]');
    function render(experiment){
      figure.querySelector('[data-fc-title]').textContent=experiment.title;
      figure.querySelector('[data-fc-description]').textContent=experiment.description;
      figure.querySelector('[data-fc-hash]').textContent=experiment.hash;
      for(const button of tabs.children)button.setAttribute('aria-pressed',String(button.dataset.id===experiment.id));
      chart.replaceChildren();
      data.phases.forEach((phase,index)=>{
        const box=document.createElement('div');box.className='fc-phase';
        const heading=document.createElement('h4');heading.textContent=`Ice ${phase}`;
        const dots=document.createElement('div');dots.className='fc-dots';dots.setAttribute('aria-hidden','true');
        for(let i=0;i<experiment.perPhase;i++){const dot=document.createElement('span');dot.className=`fc-dot${i<experiment.passed[index]?' pass':''}`;dots.append(dot);}
        const count=document.createElement('p');count.className='fc-count';count.textContent=`${experiment.passed[index]} / ${experiment.perPhase} meet this criterion`;
        box.append(heading,dots,count);chart.append(box);
      });
    }
    for(const experiment of data.experiments){const button=document.createElement('button');button.type='button';button.dataset.id=experiment.id;button.textContent=experiment.label;button.addEventListener('click',()=>render(experiment));tabs.append(button);}
    render(data.experiments[0]);
  }catch(error){figure.querySelector('[data-fc-description]').textContent='The interactive evidence could not load. The verified summary and downloadable JSON remain available below.';console.error(error);}
}
