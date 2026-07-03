"""
Contains type definitions for the DPLL and CDCL functions.
"""

# This is apparently really important because runtime evaluation of complex types is bugged
from __future__ import annotations

from typing import NamedTuple


type DPLLClause = list[int]
"""
A DPLL Clause is a list of variables.
"""

type DPLLTable = list[DPLLClause]
"""
A DPLL Table is a list of clauses.
It is a 2D array.
"""


type CDCLVariable = tuple[int, bool | None]
"""
A CDCL Variable is a tuple of:
the name of the variable, with polarity,
its evaluated value (post-polarity).
"""

type CDCLClause = list[CDCLVariable]
"""
A CDCL Clause is a list of variable tuples.
"""


class CDCLTable(NamedTuple):
    """
    A CDCL Table is a tuple of:
    a "clauses" attribute at index 0 that is a list of CDCL clauses,
    a "values" attribute at index 1, where values[i] is the evaluated value of clauses[i].
    """
    clauses: list[CDCLClause]
    values: list[bool | None]


class Decision:
    """
    A member of a decision trail.
    It is of form: +/- (variable)^(clause)_(decision level)
    +/- is the True/False value of the variable, represented mathematically
    """

    def __init__(self, variable: int, cause_clause: DPLLClause | None = None, level: int = 0):
        self.variable = variable
        self.cause_clause = cause_clause
        self.level = level


type DecisionTrail = list[Decision]
"""
The x+1th decision in a trail was performed after the xth.
"""
