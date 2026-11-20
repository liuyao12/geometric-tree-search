import {runExperiment} from './companion-run.js';
self.onmessage=({data})=>{
  try {runExperiment(data,frame=>self.postMessage(frame));}
  catch(error) {self.postMessage({status:'error',message:error.message});}
};
