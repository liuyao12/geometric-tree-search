"""Fresh-directory reproduction under the exact binary and adapter pins."""
import argparse
from pathlib import Path
import external_hilbert_transfer_inputs as inputs
import external_hilbert_transfer_control as control
import external_hilbert_transfer_audit as audit
import external_hilbert_transfer_mutations as mutations
from external_prover_inputs import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--e',required=True);a=p.parse_args();out=Path(a.output).resolve();e=Path(a.e).resolve()
    if out.exists():raise ValueError('fresh output directory required')
    if sha(e.read_bytes())!='a2fc18a82ed1dbdcdd37eefeb5c71ccad1e8fc48662466f61372fc0be5947f21':raise ValueError('a different binary requires another experiment')
    inputs.OUT=control.OUT=audit.OUT=mutations.OUT=out;control.E=e
    control.prepare();audit.dump(out/'input-audit.json',audit.binding());control.run();audit.after();mutations.run()
    print('FRESH HILBERT TRANSFER REPRODUCTION COMPLETE',out,flush=True)
if __name__=='__main__':main()
