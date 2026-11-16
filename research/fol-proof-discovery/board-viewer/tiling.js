(() => {
  const grid=document.getElementById('tile-grid');
  const north=document.getElementById('tile-north');
  const south=document.getElementById('tile-south');
  const heading=document.getElementById('tile-selection');
  const explanation=document.getElementById('tile-step');
  const steps=JSON.parse(document.getElementById('proof-steps').textContent);
  const rows=[...grid.querySelectorAll('.tile-row')].map(row=>[...row.querySelectorAll('button')]);
  const roles={write:'new clause',read:'premise',carry:'carried clause',vacant:'vacant slot',wall:'side wall'};
  const clauseName=id=>'C'+(Number(id)+1);
  let selected, revision=0;

  function showClause(container,id,role) {
    container.replaceChildren();
    if (id==='') {
      container.textContent=role==='wall' ? 'Wall edge' : 'Vacant register';
      return;
    }
    container.append(document.getElementById('clause-'+id).content.cloneNode(true));
  }

  function choose(tile,focus=false) {
    if (selected) {
      selected.setAttribute('aria-pressed','false');
      selected.tabIndex=-1;
    }
    selected=tile;
    selected.setAttribute('aria-pressed','true');
    selected.tabIndex=0;
    if (focus) selected.focus();
    const {row,role}=tile.dataset;
    const step=steps[Number(row)];
    heading.textContent='Step '+(+row+1)+' · '+(tile.dataset.south==='' ? '' : clauseName(tile.dataset.south)+' · ')+roles[role];
    explanation.textContent='This row reads '+[...new Set(step.parents)].map(clauseName).join(' and ')+
      ' and writes '+clauseName(step.written)+'.';
    const bottom=Number(tile.dataset.south);
    if (role==='write' && document.getElementById('clause-'+bottom).content.querySelector('.symbol-empty')) {
      explanation.textContent+=' This is the empty clause, which closes the proof.';
    }
    grid.querySelectorAll('.premise').forEach(node=>node.classList.remove('premise'));
    rows[row].filter(node=>node.dataset.role==='read').forEach(node=>node.classList.add('premise'));
    const math=window.MathJax;
    const ticket=++revision;
    if (math?.typesetClear) math.typesetClear([north,south]);
    showClause(north,tile.dataset.north,role);
    showClause(south,tile.dataset.south,role);
    math?.startup?.promise.then(()=>{
      if (ticket===revision) return math.typesetPromise([north,south]);
    });
  }

  grid.addEventListener('click',event=>{
    const tile=event.target.closest('.tile');
    if (tile) choose(tile);
  });
  grid.addEventListener('keydown',event=>{
    if (!selected) return;
    let row=+selected.dataset.row,col=+selected.dataset.col;
    if (event.key==='ArrowLeft') col--;
    else if (event.key==='ArrowRight') col++;
    else if (event.key==='ArrowUp') row--;
    else if (event.key==='ArrowDown') row++;
    else return;
    event.preventDefault();
    const next=rows[row]?.[col];
    if (next) choose(next,true);
  });
  choose(grid.querySelector('.tile-write'));
})();
