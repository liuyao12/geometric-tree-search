"""One sole-owned independent actual-model audit, never proof search."""
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def pin(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return dict(sha256=h.hexdigest(), bytes=Path(path).stat().st_size)


def main():
    began = time.perf_counter()
    planpath = HERE / "geometry-full-independent-plan-v1.json"
    plan = json.loads(planpath.read_bytes())
    destination = ROOT / plan["lifetime_path"]
    if destination.exists():
        raise ValueError("immutable independent whole lifetime exists")
    child = terminal = usage = None
    failure = None
    try:
        for entry in plan["sources"] + plan["inputs"] + plan["preserved_files"]:
            if pin(ROOT / entry["path"]) != {k: entry[k] for k in ("sha256", "bytes")}:
                raise ValueError("frozen independent pin " + entry["path"])
        with (ROOT / plan["stdout_path"]).open("xb") as stdout, (ROOT / plan["stderr_path"]).open("xb") as stderr:
            child = subprocess.Popen([sys.executable, str(ROOT / plan["worker_path"])], cwd=ROOT, stdout=stdout, stderr=stderr)
            while terminal is None:
                waited, status, got = os.wait4(child.pid, os.WNOHANG)
                if waited:
                    terminal, usage = os.waitstatus_to_exitcode(status), got
                    child.returncode = terminal
                    break
                if time.perf_counter() - began >= plan["whole_seconds"]:
                    failure = "owned independent full lifetime wall gate"
                    os.kill(child.pid, signal.SIGKILL)
                    _, status, usage = os.wait4(child.pid, 0)
                    terminal = os.waitstatus_to_exitcode(status)
                    child.returncode = terminal
                    break
                time.sleep(.02)
    except BaseException as exc:
        failure = type(exc).__name__ + ": " + str(exc)
    finally:
        if child is not None and terminal is None:
            try:
                os.kill(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _, status, usage = os.wait4(child.pid, 0)
            terminal = os.waitstatus_to_exitcode(status)
            child.returncode = terminal
    resultpath = ROOT / plan["result_path"]
    result = None
    if resultpath.exists():
        try:
            result = json.loads(resultpath.read_bytes())
        except Exception as exc:
            failure = failure or "invalid independent result " + str(exc)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    childpeak = usage.ru_maxrss if usage else 0
    if sys.platform != "darwin":
        peak *= 1024; childpeak *= 1024
    elapsed = time.perf_counter() - began
    success = terminal == 0 and failure is None and result is not None \
        and result["status"] == "passed_independent_full_primitive_graph_state_identity_and_authored_logical_word_audit" \
        and result["plan_sha256"] == pin(planpath)["sha256"] \
        and elapsed <= plan["whole_seconds"] and peak + childpeak <= plan["peak_bytes"]
    receipt = dict(status="passed_owned_independent_full_model_audit_lifetime" if success else "unknown_or_failed_owned_independent_full_model_audit",
        plan_sha256=pin(planpath)["sha256"], result_pin=pin(resultpath) if resultpath.exists() else None,
        child_pid=child.pid if child else None, child_exit_code=terminal,
        owned_child_terminal_and_reaped=child is not None and terminal is not None,
        failure=failure, full_worker_and_owner_seconds_before_receipt_write=elapsed,
        fresh_child_kernel_peak_bytes=childpeak, owner_kernel_peak_bytes=peak,
        conservative_combined_peak_bytes=peak + childpeak, whole_ceiling_seconds=plan["whole_seconds"], peak_ceiling_bytes=plan["peak_bytes"],
        wall_overshoot_seconds=max(0, elapsed - plan["whole_seconds"]), memory_overshoot_bytes=max(0, peak + childpeak - plan["peak_bytes"]),
        enforcement="Sole direct-child wait4 owner, internal alarm and owned external wall kill/reap; conservative final fresh child plus owner kernel peaks. No hard OS memory limit or live RSS sampler claim.",
        clock_scope="From owner entry through exact pin hashing, worker complete receipt serialization/exit, own terminal reconciliation. Own final lifetime receipt write excluded; source authoring unmeasured.",
        producer_phase_separately_charged=True, prior_unknowns_preserved=True,
        target_searches=0, native_queries=0, training_episodes=0, compiler_activations=0,
        cluster_lifecycle="open; fixed preference-set gap remains")
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2); stream.write("\n")
    print(json.dumps(receipt), flush=True)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
