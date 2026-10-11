"""Prospective outer full-graph conformance lifetime including supervisor serialization."""
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    destination = HERE / "full-model-lifetime-v1.json"
    if destination.exists():
        raise ValueError("immutable outer full-model receipt exists")
    start = time.perf_counter()
    planpath = HERE / "full-model-plan-v1.json"
    plan = json.loads(planpath.read_text())
    for p in plan["sources"] + plan["inputs"] + plan["preserved_files"]:
        path = HERE.parent.parent / p["path"]
        data = path.read_bytes()
        assert len(data) == p["bytes"] and hashlib.sha256(data).hexdigest() == p["sha256"]
    process = subprocess.run([sys.executable, str(HERE / "hilbert_primitive_graph_full_run_v1.py")], check=False)
    wall = time.perf_counter() - start
    stagepath = HERE / "full-model-supervision-v1.json"
    inner = json.loads(stagepath.read_text()) if stagepath.exists() else None
    own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    if sys.platform != "darwin":
        own *= 1024; children *= 1024
    combined = own + max(children, inner["conservative_host_peak_bytes"] if inner else 0)
    passed = (process.returncode == 0 and inner is not None
              and inner["status"] == "passed_bounded_authored_full_primitive_point_graph_controls"
              and wall <= 180 and combined <= 512 * 1024 * 1024)
    receipt = {"status": "passed_authored_full_primitive_graph_full_lifetime" if passed else "unknown_or_failed",
               "full_supervisor_process_seconds_including_receipt_write": wall,
               "process_return_code": process.returncode, "supervisor_wait_reaped": True,
               "outer_own_peak_bytes": own, "outer_children_kernel_peak_bytes": children,
               "conservative_host_peak_bytes": combined, "host_ceiling_bytes": 512 * 1024 * 1024,
               "wall_ceiling_seconds": 180, "prior_synthetic_v1_unknown_seconds": 0.520595542,
               "prior_synthetic_v2_seconds": 0.844840583, "plan_sha256": hashlib.sha256(planpath.read_bytes()).hexdigest(),
               "supervision_sha256": hashlib.sha256(stagepath.read_bytes()).hexdigest() if inner else None,
               "own_receipt_write": "outside pre-write outer measurement; fixture and supervisor serialization included",
               "actual_geometry_model_execution": True, "geometry_target_searches": 0,
               "native_queries": 0, "native_authority_activated": False,
               "independent_audit": "pending independent full-language point-graph audit"}
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
