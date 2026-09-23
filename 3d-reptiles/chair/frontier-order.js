export function selectFrontier(points) {
  const dead=points.find(p=>p.candidates.size===0);
  const forced=points.find(p=>p.candidates.size===1);
  const earliest=[...points].sort((a,b)=>a.generation-b.generation||a.candidates.size-b.candidates.size||a.id.localeCompare(b.id))[0];
  return {dead,forced,selected:dead??forced??earliest};
}
