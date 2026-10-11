from __future__ import annotations
import shutil
import subprocess
from .model import to_smt2


def run_solver(case, solver):
    binary = shutil.which(solver)
    if not binary:
        return {"solver": solver, "status": "NOT_INSTALLED", "result": None}
    args = [binary, "-in"] if solver == "z3" else [binary, "--lang", "smt2"]
    completed = subprocess.run(args, input=to_smt2(case), text=True, capture_output=True, timeout=15)
    token = completed.stdout.strip().splitlines()[0].upper() if completed.stdout.strip() else "ERROR"
    return {"solver": solver, "status": "RAN", "result": token, "stderr": completed.stderr.strip()}
