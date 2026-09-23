import { growOne } from './chair-gcts.js?v=20260923-centered-union';
// UI history stays on the main thread. Only the solver snapshot and branch
// stack cross this boundary; terminating this worker cancels pending work.
self.onmessage = ({data:{state}}) => {
  try {
    const next = growOne({...state,history:[]});
    self.postMessage({state:{...next,history:[]}});
  } catch(error) {
    self.postMessage({error:error.message});
  }
};
