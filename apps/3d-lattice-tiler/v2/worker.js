import {runExperiment} from './experiment.js?v=2.2.1';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
