import {runExperiment} from './experiment.js?v=20260923-nonacube';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
