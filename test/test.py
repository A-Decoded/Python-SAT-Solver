from pathlib import Path
import pytest

from controller import run_dpll, run_cdcl

TEST_DIR = Path(__file__).resolve().parent
SAT_DIR = TEST_DIR/"small-sat"
UNSAT_DIR = TEST_DIR/"small-unsat"

test_cases = []
test_cases.extend([(f, True) for f in SAT_DIR.glob("*.cnf")])
test_cases.extend([(f, False) for f in UNSAT_DIR.glob("*.cnf")])

@pytest.mark.parametrize("file_path, expected_output", test_cases)
def test_dpll(file_path, expected_output):
    assert run_dpll(str(file_path)) == expected_output

@pytest.mark.parametrize("file_path, expected_output", test_cases)
def test_cdcl(file_path, expected_output):
    assert run_cdcl(str(file_path)) == expected_output
