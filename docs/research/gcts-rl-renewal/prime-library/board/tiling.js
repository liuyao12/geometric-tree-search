(() => {
  const grid=document.getElementById('tile-grid');
  const north=document.getElementById('tile-north');
  const south=document.getElementById('tile-south');
  const heading=document.getElementById('tile-selection');
  const rows=[...grid.querySelectorAll('.tile-row')].map(row=>[...row.querySelectorAll('button')]);
  const roles={write:'Write',read:'Read',carry:'Carry',vacant:'Vacant',wall:'Side wall'};
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
    const {row,col,role}=tile.dataset;
    heading.textContent='Row '+(+row+1)+' · column '+(+col+1)+' · '+roles[role];
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
