#!/usr/bin/env python3
"""Reproduce the ordinary Glucose baseline with the same ten-second polling."""
import argparse,importlib.util,json,time
from pathlib import Path
from threading import Timer
from pysat.solvers import Glucose3
p=argparse.ArgumentParser();p.add_argument('--proof',required=True);a=p.parse_args()
spec=importlib.util.spec_from_file_location('builder',Path(__file__).with_name('build.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
data=b.build();clauses=data['clauses'];print(json.dumps(data['stats']),flush=True)
with Glucose3(bootstrap_with=clauses,with_proof=True) as g:
 start=time.time();answer=None
 for _ in range(60):
  timer=Timer(10,g.interrupt);timer.start()
  try:answer=g.solve_limited(expect_interrupt=True)
  finally:timer.cancel();timer.join();g.clear_interrupt()
  print(json.dumps({'answer':answer,'seconds':time.time()-start,**g.accum_stats()}),flush=True)
  if answer is not None:break
 if answer is False:Path(a.proof).write_text('\n'.join(g.get_proof())+'\n')
