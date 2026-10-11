"""One-child full-lifetime gate for the fresh independent static audit only."""
import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for data in iter(lambda: handle.read(1048576), b""):
            result.update(data)
    return result.hexdigest()


def check_pins(plan):
    for pin in plan["sources"] + plan["inputs"]:
        path = ROOT / pin["path"]
        if sha(path) != pin["sha256"] or path.stat().st_size != pin["bytes"]:
            raise ValueError("changed frozen source/input: " + pin["path"])


def peak(kind):
    value = resource.getrusage(kind).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def main():
    began = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    plan_path = Path(args.plan)
    plan = json.loads(plan_path.read_bytes())
    if plan["scope"] != "independent_full171_static_audit_no_activation":
        raise ValueError("unsupported gate scope")
    wall = plan["limits"]["full_lifetime_seconds"]
    memory = plan["limits"]["conservative_peak_rss_bytes"]
    if wall != 180 or memory != 536870912:
        raise ValueError("declared static limits changed")
    for path in plan["outputs"].values():
        if (ROOT / path).exists():
            raise ValueError("immutable prospective output exists: " + path)
    check_pins(plan)
    command = [sys.executable, "-B", str(ROOT / plan["worker_source"]), "--plan", str(plan_path.resolve())]
    child = None
    status = "unknown_not_started"
    stdout = stderr = b""
    exit_code = None
    failure = None
    try:
        child = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=True)
        remaining = max(0.001, wall - (time.perf_counter() - began))
        stdout, stderr = child.communicate(timeout=remaining)
        exit_code = child.returncode
        status = "terminal_child_observed"
    except Exception as error:
        failure = type(error).__name__ + ": " + str(error)
        status = "unknown_worker_or_lifetime"
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if child is not None:
            stdout, stderr = child.communicate()
            exit_code = child.returncode
    finally:
        if child is not None and child.poll() is None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait()
    stdout_path = ROOT / plan["outputs"]["stdout"]
    stderr_path = ROOT / plan["outputs"]["stderr"]
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    check_pins(plan)
    audit_path = ROOT / plan["outputs"]["audit"]
    audit_status = None
    audit_counts = None
    if audit_path.exists():
        report = json.loads(audit_path.read_bytes())
        audit_status, audit_counts = report.get("status"), report.get("counts")
        del report
    child_peak = peak(resource.RUSAGE_CHILDREN)
    observer_peak = peak(resource.RUSAGE_SELF)
    conservative = child_peak + observer_peak
    elapsed = time.perf_counter() - began
    if (exit_code == 0 and audit_status == "passed_independent_finite_static_symbolic_and_aggregate_audit"
            and elapsed <= wall and conservative <= memory):
        status = "passed_full_lifetime_static_audit_gate"
    elif elapsed > wall or conservative > memory:
        status = "unknown_resource_gate"
    else:
        status = "unknown_or_failed_static_audit_gate"
    receipt = {"status": status, "plan_sha256": sha(plan_path), "worker_command": command,
               "worker_pid": child.pid if child else None, "child_exit_code": exit_code,
               "child_terminal_reaped": child is not None and child.returncode is not None,
               "failure": failure, "audit_status": audit_status, "audit_counts": audit_counts,
               "full_lifetime_seconds_before_final_receipt_write": elapsed,
               "child_kernel_peak_rss_bytes": child_peak, "observer_kernel_peak_rss_bytes": observer_peak,
               "conservative_sum_peak_rss_bytes": conservative,
               "limits": plan["limits"],
               "enforcement": {"time": "worker SIGALRM plus whole observer communicate deadline/kill/wait",
                               "memory": "final conservative sum of isolated child/observer kernel peaks",
                               "hard_OS_memory_limit": "not asserted", "ps_sampling": "not used"},
               "output_bindings": [{"path": path, "sha256": sha(ROOT / path),
                                    "bytes": (ROOT / path).stat().st_size}
                                   for role, path in plan["outputs"].items()
                                   if role != "lifetime" and (ROOT / path).exists()],
               "startup_and_report_serialization_charged": True,
               "final_lifetime_receipt_write": "excluded and unmeasured, not zero",
               "native_queries": 0, "search_runs": 0, "solver_runs": 0}
    receipt_path = ROOT / plan["outputs"]["lifetime"]
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({key: receipt[key] for key in ("status", "full_lifetime_seconds_before_final_receipt_write",
                                                   "conservative_sum_peak_rss_bytes", "child_terminal_reaped")}), flush=True)
    return 0 if status == "passed_full_lifetime_static_audit_gate" else 1


if __name__ == "__main__":
    raise SystemExit(main())
