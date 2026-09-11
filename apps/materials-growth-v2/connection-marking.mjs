import {connectionScore} from './connection-descriptor.mjs';
import {compileConflictMarkings} from './conflict-marking.mjs';

// Explicit bridge from a frozen, approximate connection hypothesis to exact
// point-value agreement in a FINITE placement library. The caller supplies each
// pair's already-posed joint support. This is not a motif-local spatial field,
// a continuous-domain certificate, or a sound rule for the unmarked problem.
export function compileConnectionHypothesis(candidates, comparisons, library, threshold, options={}) {
  if(!Number.isFinite(threshold)||threshold<0)throw Error('Finite nonnegative threshold required');
  const scores=comparisons.map(({pair,sites})=>{
    const score=connectionScore(library,sites);
    return {pair:[...pair],score:Number.isFinite(score)?score:null,
      status:!Number.isFinite(score)?'abstain':score>threshold?'restricted':'admitted'};
  });
  const compiled=compileConflictMarkings(candidates,scores.filter(s=>s.status==='restricted').map(s=>s.pair),options);
  return {...compiled,scores,semantics:'Learned, problem-restricting finite hypothesis. Unknown label strata abstain. Rule/library changes require recompilation and search replay.'};
}
