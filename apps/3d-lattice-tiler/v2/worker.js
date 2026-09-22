import {runExperiment} from './experiment.js?v=2.3.1';
self.onmessage=async({data})=>{for await(const e of runExperiment(data))self.postMessage(e);};
