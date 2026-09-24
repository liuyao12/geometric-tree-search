import {runExperiment} from './experiment.js?v=20260924-certified';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
