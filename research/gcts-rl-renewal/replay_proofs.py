"""Replay exported JSON proofs against a separately declared trusted theory.

The proof cannot nominate new axioms. This codec only restores immutable AST
and tape-symbol tuples lost during JSON serialization; logic validity is still
decided by Kernel and Wang computation validity by the operational checker.
"""
import argparse,copy,json,time
from pathlib import Path
import logic,wang

AST_FIELDS={"formula","universal","template","term","left","right","consequent"}

def immutable(value):
    if isinstance(value,list): return tuple(immutable(x) for x in value)
    if isinstance(value,(str,int)) and not isinstance(value,bool): return value
    raise ValueError("invalid AST/tape data")

def decode_proof(lines):
    out=[]
    for line in lines:
        item=dict(line)
        for name,value in list(item.items()):
            if name in AST_FIELDS or (name=="antecedent" and item["rule"]=="distribute"):
                item[name]=immutable(value)
        out.append(item)
    return out

def arithmetic_kernel():
    # Trust this external theory declaration, never axiom lines from the proof.
    x,y=logic.V("x"),logic.V("y"); z=logic.F("zero")
    return logic.Kernel({"zero":0,"succ":1,"add":2},{},
        {"add_zero":logic.All("x",logic.Eq(logic.F("add",x,z),x)),
         "add_successor":logic.All("x",logic.All("y",logic.Eq(logic.F("add",x,logic.F("succ",y)),logic.F("succ",logic.F("add",x,y)))))} )

def check_logic(data,kernel=None):
    try:
        kernel=kernel or arithmetic_kernel()
        return kernel.check(decode_proof(data["proof"]),immutable(data["target"]))
    except (ValueError,TypeError,KeyError,IndexError,RecursionError): return False

def check_wang(data):
    try:
        c=wang.addition_machine(); pattern=wang.addition_pattern(1,1,2)
        initial=immutable(data["initial"]); rows=immutable(data["rows"])
        if len(initial)!=len(pattern) or len(rows)!=data["height"]+1: return False
        if not all(len(row)==len(initial) for row in rows): return False
        if not all(s in allowed for s,allowed in zip(initial,pattern)): return False
        placements=[(x,y,{k:immutable(v) for k,v in tile.items()}) for x,y,tile in data["placements"]]
        return wang.certificate_check(c,initial,rows,placements)
    except (ValueError,TypeError,KeyError,IndexError,RecursionError): return False

def audit(data):
    start=time.monotonic(); a=data["logic"]; b=data["wang_certificate_search"]
    assert check_logic(a) and check_wang(b)
    changed=copy.deepcopy(a); changed["target"]=changed["proof"][0]["formula"]
    assert not check_logic(changed)
    forged={"proof":[{"rule":"axiom","name":"unregistered_axiom","formula":a["target"]}],"target":a["target"]}
    assert not check_logic(forged)
    changed_tape=copy.deepcopy(b); changed_tape["initial"][6]="B"
    assert not check_wang(changed_tape)
    return {"logic_json_replayed":True,"wang_json_replayed":True,"trusted_theory_external_to_proof":True,
            "modified_target_rejected":True,"forged_axiom_rejected":True,"modified_tape_rejected":True,
            "seconds":time.monotonic()-start,"scope":"serialized existing finite certificates; no proof-kernel-to-TM compiler"}

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("path",nargs="?",type=Path,
        default=Path(__file__).resolve().parents[2]/"docs/research/gcts-rl-renewal/iteration-002.json")
    args=parser.parse_args(); print(json.dumps(audit(json.loads(args.path.read_text())),indent=2))
