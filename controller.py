"""
Format is: python controller.py <cnf_file> <DPLL|CDCL>
"""

import os
import sys
import time

from src.reader import extract_numbers, convert_to_cdcl
from src.dpll_processor import dpll, dpll_preprocessor
from src.cdcl_processor import cdcl


def run_dpll(cnf_path: str) -> None:
    extracted_numbers = extract_numbers(cnf_path)
    variables = extracted_numbers[0]
    clause_table = extracted_numbers[2]
    clause_table = dpll_preprocessor(clause_table, variables)
    if not isinstance(clause_table, bool):
        return True if dpll(clause_table, variables, 0) else False
    else:
        return True if clause_table else False


def run_cdcl(cnf_path: str) -> None:
    extracted_numbers = extract_numbers(cnf_path)
    variables = extracted_numbers[0]
    clause_table = extracted_numbers[2]
    clause_table = dpll_preprocessor(clause_table, variables)
    if not isinstance(clause_table, bool):
        clause_table = convert_to_cdcl(clause_table)
        return True if cdcl(clause_table, []) else False
    else:
        return True if clause_table else False


def main():
    if len(sys.argv) < 3:
        print("Usage: python controller.py <cnf_file> {DPLL|CDCL} [--timer]")
        sys.exit(1)

    cnf_path = sys.argv[1]
    algorithm = sys.argv[2].upper()
    timer_flag = "--timer" in sys.argv

    if not os.path.isfile(cnf_path):
        print(f"File not found: {cnf_path}.")
        sys.exit(1)

    if algorithm not in ("DPLL", "CDCL"):
        print("Choose DPLL or CDCL")
        sys.exit(1)

    if algorithm == "DPLL":
        start_time = time.perf_counter()
        print("SAT") if run_dpll(cnf_path) else print("UNSAT")
    else:
        start_time = time.perf_counter()
        print("SAT") if run_cdcl(cnf_path) else print("UNSAT")
    end_time = time.perf_counter()

    if timer_flag:
        print(f"{algorithm} Time: {end_time - start_time}")


if __name__ == "__main__":
    main()
