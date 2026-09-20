const root=document.querySelector('#decoration-progress');
if(root)main().catch(()=>{root.querySelector('[data-dp-lanes]').textContent='Evidence could not load. Download the linked results below.';});
async function main(){
 const response=await fetch(new URL('./results.json',import.meta.url));if(!response.ok)throw Error('Evidence unavailable');
 const {lanes}=await response.json();let selected='oxalic-beta-0135';
 const controls=root.querySelector('[data-dp-lanes]');controls.replaceChildren();
 for(const lane of lanes){const button=document.createElement('button');button.type='button';button.className='dp-lane';button.dataset.lane=lane.id;
  const count=document.createElement('strong');count.textContent=`${lane.totals.verified}/88`;const title=document.createElement('span');title.textContent=lane.title;button.append(count,title);button.onclick=()=>render(lane);controls.append(button);}
 function render(lane){
  for(const button of controls.children)button.setAttribute('aria-pressed',String(button.dataset.lane===lane.id));
  root.querySelector('[data-dp-summary]').textContent=`${lane.totals.verified} verified · ${lane.totals.unknown} budget-unknown · ${lane.totals.exhausted} exhausted restricted pools`;
  const grid=root.querySelector('[data-dp-grid]');grid.replaceChildren();
  function inspect(row){selected=row.id;for(const b of grid.querySelectorAll('button'))b.setAttribute('aria-pressed',String(b.dataset.id===selected));
   const text=row.status==='verified'?`Verified: ${row.witness.requiredAtoms} atom sites + ${row.witness.activatedLatentPoints} activated latent sites; every active t-sum is 1. Maximum marking-ball error ${row.witness.maximumMarkBallError.toFixed(4)} Å (limit 0.15 Å). ${row.stats.backtracks} backtracks.`:row.status==='unknown'?'Unknown: alignment preparation exceeded its budget. This is not a failed tiling.':'No solution in this declared finite candidate pool. This does not prove geometric impossibility.';
   root.querySelector('[data-dp-detail]').textContent=`${row.id}: ${text}`;}
  for(const phase of ['alpha','beta']){const group=document.createElement('div');group.className='dp-phase';const label=document.createElement('strong');label.textContent=phase==='alpha'?'α':'β';const cells=document.createElement('div');cells.className='dp-cells';
   for(const row of lane.rows.filter(r=>r.phase===phase)){const button=document.createElement('button');button.type='button';button.className='dp-cell';button.dataset.id=row.id;button.dataset.status=row.status;button.textContent=row.status==='verified'?'●':row.status==='unknown'?'◇':'·';button.title=`${row.id}: ${row.status}`;button.setAttribute('aria-label',button.title);button.onclick=()=>inspect(row);cells.append(button);}group.append(label,cells);grid.append(group);}
  inspect(lane.rows.find(r=>r.id===selected)||lane.rows[0]);
 }
 render(lanes.at(-1));
}
