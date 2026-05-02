import os
import sys
import time

from Reader import extractNumbers, convertToCDCL
from DPLLProcessor import DPLL, DPLLpreProcessor
from CDCLProcessor import CDCL


def run_dpll(cnf_path: str) -> None:
    variables, clauses, clausetable = extractNumbers(cnf_path)
    clausetable = DPLLpreProcessor(clausetable, variables)
    if not isinstance(clausetable, bool):
        print("SAT") if DPLL(clausetable, variables, 1) else print("UNSAT")
    else:
        print("SAT") if clausetable else print("UNSAT")


def run_cdcl(cnf_path: str) -> None:
    variables, clauses, clausetable = extractNumbers(cnf_path)
    clausetable = DPLLpreProcessor(clausetable, variables)
    if not isinstance(clausetable, bool):
        clausetable = convertToCDCL(clausetable)
        print("SAT") if CDCL(clausetable, []) else print("UNSAT")
    else:
        print("SAT") if clausetable else print("UNSAT")


def main():
    if len(sys.argv) < 3:
        print("Usage: python Controller.py <cnf_file> <DPLL|CDCL>")
        sys.exit(1)

    cnf_path = sys.argv[1]
    algorithm = sys.argv[2].upper()

    if not os.path.isfile(cnf_path):
        print(f"File not found: {cnf_path}.")
        sys.exit(1)

    if algorithm not in ("DPLL", "CDCL"):
        print(f"Choose DPLL or CDCL.")
        sys.exit(1)

    start_time = time.perf_counter()
    if algorithm == "DPLL":
        run_dpll(cnf_path)
    else:
        run_cdcl(cnf_path)
    end_time = time.perf_counter()

    print(f"{algorithm} Time: {end_time - start_time}")


if __name__ == "__main__":
    main()
