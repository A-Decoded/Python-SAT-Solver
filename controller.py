import os
import sys
import time

from reader import extract_numbers, convert_to_cdcl
from dpll_processor import dpll, dpll_preprocessor
from cdcl_processor import cdcl


def run_dpll(cnf_path: str) -> None:
    variables, clauses, clause_table = extract_numbers(cnf_path)
    clause_table = dpll_preprocessor(clause_table, variables)
    if not isinstance(clause_table, bool):
        print("SAT") if dpll(clause_table, variables, 1) else print("UNSAT")
    else:
        print("SAT") if clause_table else print("UNSAT")


def run_cdcl(cnf_path: str) -> None:
    variables, clauses, clause_table = extract_numbers(cnf_path)
    clause_table = dpll_preprocessor(clause_table, variables)
    if not isinstance(clause_table, bool):
        clause_table = convert_to_cdcl(clause_table)
        print("SAT") if cdcl(clause_table, []) else print("UNSAT")
    else:
        print("SAT") if clause_table else print("UNSAT")


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
