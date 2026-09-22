import {POLYCUBE_GCTS_CANDIDATES} from '../../assets/polycube-census-candidates.js';

// Catalogue metadata and geometry only. No labels or learned assignments enter
// the live learner; evidence links describe separately recorded experiments.
const updates={
 'p10-346304':{priority:0,note:'Threefold-symmetric ten-cube candidate. Recorded pair-corona work resolves 54 positive and 24 negative pairs; 1,846 remain unresolved. A viable-frontier finite patch is known. Infinite tiling remains unresolved.',evidence:'docs/projects/3d-viable-frontier-search.md'},
 'p9-42947':{priority:1,note:'Nine-cube candidate with a completed 1,408-pair research catalogue (1,405 positive, 3 negative) and verified viable-frontier patches. Infinite tiling remains unresolved; fitting every local pair did not resolve larger growth.',evidence:'docs/projects/3d-point-corona-sat.md#p9-42947-complete-classification-and-limits-of-the-pair-marking'},
 'p10-054782':{priority:2},'p10-055695':{priority:3},'p10-290795':{priority:4},
 'p9-48258':{note:'Nine-cube cross with an independently checked integer-grid non-tiling proof. Useful as a delayed-obstruction control, not an unresolved aperiodic candidate. The proof does not cover unrestricted Euclidean placements.',evidence:'docs/projects/p9-48258-grid-obstruction.md'},
 'p10-052588':{note:'Ten-cube delayed-obstruction control. Recorded complete radius-three-to-four exhaustion excludes extension in the original voxel-corona model.',evidence:'data/polycube-p10-052588-complete-radius3-exhaustion-2026-08-23.json'},
 'p10-052670':{note:'Ten-cube obstruction control with a verified first corona and a recorded exhausted radius-two check.'},
 'p9-43172':{note:'Nine-cube periodic control with a verified eight-copy quotient construction. Eight is the size of a found motif, not a claimed minimum period.'}
};
export const RESEARCH_TILES=POLYCUBE_GCTS_CANDIDATES.map((candidate,index)=>{
 const s=candidate.screening,u=updates[candidate.id]??{};
 const periodic=['translational','isohedral_periodic_quotient'].includes(s.certificate),unresolved=s.status==='inconclusive';
 const group=unresolved?'Unresolved polycube research':periodic?'Periodic polycube controls':'Grid non-tiling controls';
 const category=unresolved?'Unresolved Polycube Candidates':periodic?'GCTS Periodic Controls':'GCTS Non-Tiler Controls';
 const through=s.periodic_exact_through??s.periodic_hnf_max_motif_tiles;
 const note=u.note??`${candidate.voxels.length}-cube candidate. Recorded periodic screening found no motif through ${through} copies; a radius-${s.corona_completed_radius} corona was verified. Larger extension remains unresolved.`;
 const evidence=u.evidence??s.corona_complete_exhaustion_report??s.corona_report??s.periodic_hnf_report??s.fresh_rerun_report??'docs/projects/3d-learned-catalog-audit.md';
 const status=unresolved?'Unresolved':periodic?'Periodic control':'Grid obstruction';
 const review={note,evidence,status,priority:u.priority??10+index};
 return {id:candidate.registry_id,sourceId:candidate.id,name:`${candidate.id} · ${candidate.volume} cubes`,group,category,note,evidence,priority:review.priority,voxels:candidate.voxels,candidate:{...candidate,catalogueReview:review}};
}).sort((a,b)=>a.priority-b.priority);
export const RESEARCH_BY_ID=new Map(RESEARCH_TILES.map(c=>[c.id,c]));
export const RESEARCH_SUITE_IDS=['polycube_p10_346304','polycube_p9_42947','polycube_p10_054782','polycube_p9_48258','polycube_p9_43172'];
export const HISTORICAL_CASE_IDS=['a2_hat_prism','a2_turtle_prism','buckled_ring','twisted_h','tuning_fork'];
