"""Fresh-output reproduction under the exact measured checker/binary pins."""
import argparse,sys
from pathlib import Path
import external_commutativity_inputs as inputs
import external_commutativity_control as control
import external_commutativity_audit as audit
import external_commutativity_mutations as mutations
from external_prover_inputs import sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--e',required=True);a=p.parse_args();out=Path(a.output).resolve();binary=Path(a.e).resolve()
    if out.exists():raise ValueError('output directory must be fresh')
    if sha(binary.read_bytes())!='a2fc18a82ed1dbdcdd37eefeb5c71ccad1e8fc48662466f61372fc0be5947f21':raise ValueError('different E binary requires a different experiment')
    inputs.OUT=control.OUT=audit.OUT=mutations.OUT=out;control.E=binary
    control.prepare();audit.dump(out/'input-audit.json',audit.binding());control.run();audit.after();mutations.run()
    print('FRESH EXTERNAL COMMUTATIVITY REPRODUCTION COMPLETE',out,flush=True)
if __name__=='__main__':main()
