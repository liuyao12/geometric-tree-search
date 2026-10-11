"""Task-owned prospective full-language conformance process; root review before execution."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SECONDS, BYTES = 175, 512 * 1024 * 1024


def peak(kind):
    return resource.getrusage(kind).ru_maxrss * (1 if sys.platform == "darwin" else 1024)


def save(name, data):
    path = HERE / name
    if path.exists():
        raise ValueError("immutable full-model evidence already exists: " + name)
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    started = time.perf_counter()
    planpath = HERE / "full-model-plan-v1.json"
    plan = json.loads(planpath.read_text())
    for p in plan["sources"] + plan["inputs"] + plan["preserved_files"]:
        path = ROOT / p["path"]
        data = path.read_bytes()
        if len(data) != p["bytes"] or hashlib.sha256(data).hexdigest() != p["sha256"]:
            raise ValueError("frozen input/source changed: " + p["path"])
    for name in ("full-model-outcome-v1.json", "full-model-launch-v1.json", "full-model-supervision-v1.json"):
        if (HERE / name).exists():
            raise ValueError("prior immutable full-model run exists")
    child, terminal, reason, error = None, None, None, None
    samples = []
    try:
        with (HERE / "full-model-stdout-v1.txt").open("wb") as out, (HERE / "full-model-stderr-v1.txt").open("wb") as err:
            child = subprocess.Popen([sys.executable, str(HERE / "hilbert_primitive_graph_full_v1.py")],
                                     cwd=HERE, stdout=out, stderr=err)
            save("full-model-launch-v1.json", {"pid": child.pid, "scope": "owned complete primitive point-domain conformance only",
                 "wall_ceiling_seconds": SECONDS, "host_ceiling_bytes": BYTES,
                 "actual_geometry_models": 1, "native_queries": 0})
            try:
                while child.poll() is None:
                    elapsed = time.perf_counter() - started
                    if elapsed > SECONDS:
                        reason = "wall_ceiling"; break
                    ps = subprocess.run(["ps", "-o", "rss=", "-p", str(child.pid)], capture_output=True,
                                        timeout=min(2, max(.01, SECONDS - elapsed)), check=False)
                    raw = ps.stdout.strip()
                    if ps.returncode == 0 and raw:
                        rss = int(raw) * 1024
                        if rss < 0:
                            raise ValueError("negative child RSS")
                        own = peak(resource.RUSAGE_SELF)
                        samples.append({"seconds": elapsed, "child_rss_bytes": rss, "supervisor_peak_bytes": own})
                        if rss + own > BYTES:
                            reason = "sampled_combined_host_ceiling"; break
                    elif child.poll() is None:
                        raise RuntimeError("owned process metadata unavailable: " + ps.stderr.decode(errors="replace"))
                    time.sleep(.02)
            except BaseException as exc:
                reason, error = "watchdog_failure", type(exc).__name__ + ": " + str(exc)
            finally:
                if reason is not None and child.poll() is None:
                    child.kill()
                terminal = child.wait()
    except BaseException as exc:
        reason = reason or "supervision_failure"
        error = error or type(exc).__name__ + ": " + str(exc)
        if child is not None:
            if child.poll() is None:
                child.kill()
            terminal = child.wait()
    receipt = None
    try:
        receipt = json.loads((HERE / "full-model-outcome-v1.json").read_text())
    except BaseException as exc:
        reason, error = reason or "missing_or_invalid_child_receipt", error or str(exc)
    childpeak, ownpeak = peak(resource.RUSAGE_CHILDREN), peak(resource.RUSAGE_SELF)
    elapsed = time.perf_counter() - started
    if childpeak + ownpeak > BYTES:
        reason = reason or "final_conservative_kernel_host_peak_ceiling"
    if elapsed > SECONDS:
        reason = reason or "final_wall_ceiling"
    if not samples:
        reason = reason or "no_external_owned_RSS_sample"
    if receipt is not None and receipt["status"] != "passed_authored_full_primitive_point_graph_controls_pending_independent_audit":
        reason = reason or "fixture_receipt_status"
    passed = terminal == 0 and reason is None and receipt is not None
    data = {"status": "passed_bounded_authored_full_primitive_point_graph_controls" if passed else "unknown_or_failed",
            "pid": child.pid if child else None, "exit_code": terminal,
            "owned_child_terminal_wait_reaped": child is not None and terminal is not None,
            "supervisor_seconds_before_receipt_write": elapsed, "wall_ceiling_seconds": SECONDS,
            "host_ceiling_bytes": BYTES, "kernel_child_peak_bytes": childpeak,
            "supervisor_peak_bytes": ownpeak, "conservative_host_peak_bytes": childpeak + ownpeak,
            "rss_samples": samples, "resource_reason": reason, "watchdog_error": error,
            "enforcement": "task-owned external sampled RSS/time watchdog; child SIGALRM; final kernel peak rejection",
            "OS_soft_limit_claim": "none", "plan_sha256": hashlib.sha256(planpath.read_bytes()).hexdigest(),
            "actual_geometry_model_execution": True, "geometry_target_searches": 0, "native_queries": 0,
            "native_authority_activated": False, "independent_kernel_audit": "separate_pending_gate"}
    save("full-model-supervision-v1.json", data)
    print(json.dumps({k: v for k, v in data.items() if k != "rss_samples"}), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
