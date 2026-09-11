import {runExperiment} from './experiment.js?v=2.1.0';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
