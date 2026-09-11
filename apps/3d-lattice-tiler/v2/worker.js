import {runExperiment} from './experiment.js';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
