import {runExperiment} from './experiment.js?v=2.2.9';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
