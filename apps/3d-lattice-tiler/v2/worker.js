import {runExperiment} from './experiment.js?v=20260923-chair-export';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
