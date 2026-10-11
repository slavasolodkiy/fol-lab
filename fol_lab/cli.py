import argparse, json
from pathlib import Path
from .model import reference_decision, to_smt2, validate_case
from .solvers import run_solver


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", type=Path)
    parser.add_argument("--solver", choices=["reference", "z3", "cvc5", "all"], default="all")
    parser.add_argument("--print-smt2", action="store_true")
    args = parser.parse_args()
    case = json.loads(args.case.read_text(encoding="utf-8"))
    errors = validate_case(case)
    if errors:
        raise SystemExit("; ".join(errors))
    if args.print_smt2:
        print(to_smt2(case))
    output = {"case": case["id"], "reference": reference_decision(case)}
    if args.solver in {"z3", "all"}:
        output["z3"] = run_solver(case, "z3")
    if args.solver in {"cvc5", "all"}:
        output["cvc5"] = run_solver(case, "cvc5")
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
