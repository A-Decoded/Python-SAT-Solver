import copy

from Reader import convert_to_cdcl
from Types import CDCLTable, CDCLClause, CDCLVariable, DPLLClause, DecisionTrail, Decision


def CDCL(clause_table: CDCLTable, decision_trail: DecisionTrail) -> bool:
    variable_to_clauses: dict[int, list[int]] = {}
    for i, clause in enumerate(clause_table.clauses):
        for variable_set in clause:
            key = abs(variable_set[0])
            variable_to_clauses.setdefault(key, []).append(i)

    while True:
        if not decision_trail:
            current_level = 0
        else:
            current_level = decision_trail[-1].level

        found_unit_variable = _findUnitVariable(clause_table)
        if found_unit_variable is not None:
            unit_var, unit_clause = found_unit_variable
            normalized_cause = [v[0] for v in unit_clause]
            decision = Decision(unit_var, normalized_cause, current_level)
        else:
            decision = Decision(_getNextSizeValue(
                clause_table), None, current_level + 1)
            # print(_getNextSizeValue(clausetable))
        decision_trail.append(decision)

        current_level = decision.level
        _evaluateVariable(clause_table, decision_trail, variable_to_clauses)

        table_value = _evaluateTable(clause_table)
        if table_value is True:
            return True
        if table_value is False:
            if current_level == 0:
                return False
            false_index = next((i for i, x in enumerate(
                clause_table.values) if x is False), None)
            false_clause = list(set(x[0]
                                for x in clause_table.clauses[false_index]))
            learned_clause = convert_to_cdcl(
                _learnClause(false_clause, decision_trail))
            wipe_level = _secondHighestDecisionLevel(
                learned_clause, decision_trail)
            _wipeTrailandTableAfter(wipe_level, decision_trail, clause_table)
            _updateLearnedClause(learned_clause, decision_trail,
                                 clause_table, variable_to_clauses)


def _learnClause(starterclause: DPLLClause, decisiontrail: DecisionTrail) -> DPLLClause:
    current_level = decisiontrail[-1].level
    working_clause = starterclause

    while True:
        variable_decisions = [_getVariableDecisionLevel(
            x, decisiontrail) for x in working_clause]
        if variable_decisions.count(current_level) == 1:
            return working_clause

        simplified_trail = [abs(decision.variable)
                            for decision in decisiontrail]
        latest_cause = None
        for i, latest_decision in enumerate(simplified_trail[::-1]):
            if latest_decision in [abs(x) for x in working_clause]:
                decision = decisiontrail[-(i + 1)]
                if decision.level == current_level and decision.causeClause is not None:
                    latest_cause = decision.causeClause
                    break

        working_clause = _resolveClauses(latest_cause, working_clause)


def _updateLearnedClause(learned_clause: CDCLClause, decision_trail: DecisionTrail, clause_table: CDCLTable, variable_to_clauses: dict) -> None:
    """
    Brings the learned clause up to speed with everything assigned so far.
    Also adds it to the table.
    """
    for j, variable_set in enumerate(learned_clause):
        variable_name = variable_set[0]
        for i, decision in enumerate(decision_trail):
            if abs(decision.variable) == abs(variable_name):
                value_to_set = True if decision.variable / variable_name > 0 else False
                learned_clause[j] = _setValue(variable_set, value_to_set)

    clause_table.clauses.append(learned_clause)
    clause_table.values.append(_evaluateClause(learned_clause))

    new_index = len(clause_table.clauses) - 1
    for variable_set in learned_clause:
        variable_to_clauses.setdefault(
            abs(variable_set[0]), []).append(new_index)


def _secondHighestDecisionLevel(learnedclause: CDCLClause, decisiontrail: DecisionTrail) -> int:
    """
    Arranges all the levels in the decision trail and gets the second highest.
    And if there's just one, then levels-1
    """
    learnedclause = [x[0] for x in learnedclause]
    levels = sorted(
        [_getVariableDecisionLevel(v, decisiontrail) for v in learnedclause],
        reverse=True
    )
    if len(levels) < 2:
        return decisiontrail[-1].level - 1
    return levels[1]


def _getVariableDecisionLevel(variable: int, decisiontrail: DecisionTrail) -> int:
    """
    Given a variable, get its decision level from the trail.
    Can handle both polarities.
    """
    for decision in decisiontrail:
        if abs(decision.variable) == abs(variable):
            return decision.level
    return -1


def _wipeTrailandTableAfter(level: int, decisiontrail: DecisionTrail, clausetable: CDCLTable) -> None:
    """
    Takes a level and wipes it out from the table, along with anything after it.
    """
    wiped = []
    for i, decision in enumerate(decisiontrail):
        if decision.level > level:
            wiped = [d.variable for d in decisiontrail[i:]]
            del decisiontrail[i:]
            break
    _undoEvaluations(clausetable, wiped)


def _undoEvaluations(clause_table: CDCLTable, variables: list) -> None:
    """
    Takes a list of variables, and removes their evaluation from the clause table.
    """
    clause_variables = clause_table.clauses
    clause_values = clause_table.values
    variables = [abs(variable) for variable in variables]
    for i, clause in enumerate(clause_variables):
        reevaluate_clause = False
        for j, variable_set in enumerate(clause):
            variable_name = variable_set[0]
            if abs(variable_name) in variables:
                # print("Modifying", clause)
                reevaluate_clause = True
                clause[j] = _setValue(variable_set, None)
        if reevaluate_clause:
            clause_values[i] = _evaluateClause(clause)
            # print("Unevaluated clause to", clausevalues[i])


def _evaluateTable(clausetable: CDCLTable, lazy: bool = True) -> bool | None:
    """
    Evaluates the entire clause table.
    Has a lazy flag (automatically enabled).
    Disable lazy flag if you want to evaluate every clause (computationally expensive.)
    """
    clausevalues = clausetable.values
    if not lazy:
        clausevariables = clausetable.clauses
        for i, clause in enumerate(clausevariables):
            clausevalues[i] = _evaluateClause(clause)

    if False in clausevalues:
        return False
    if None in clausevalues:
        return None
    return True


def _evaluateClause(clause: CDCLClause) -> bool | None:
    """
    Looks at the values of the variables in a clause and decides its current value.
    """
    false_flag = True

    for variable_set in clause:
        variable_value = variable_set[1]
        # If we find a singular True, it's a True evaluation.
        if variable_value is True:
            return True
        # If we find a singular None, it cannot be False.
        elif variable_value is None:
            false_flag = False

    # If we haven't found any Nones or Trues, it must be False, otherwise None.
    return False if false_flag else None


def _evaluateVariable(clausetable: CDCLTable, decisiontrail: DecisionTrail, variable_to_clauses: dict) -> None:
    decision = decisiontrail[-1]
    variable = decision.variable
    decision_polarity = variable > 0

    clausevariables = clausetable.clauses
    clausevalues = clausetable.values

    for i in variable_to_clauses.get(abs(variable), []):
        if clausevalues[i] is True:
            continue
        clause = clausevariables[i]
        for j, variable_set in enumerate(clause):
            if abs(variable_set[0]) == abs(variable):
                polarity = variable_set[0] > 0
                clause[j] = _setValue(
                    variable_set, polarity == decision_polarity)
        clausevalues[i] = _evaluateClause(clause)


def _setValue(variable: CDCLVariable, value: bool | None) -> CDCLVariable:
    """
    Pure helper function to set a value for a variable tuple in a clause.
    """
    return (variable[0], value)


def _resolveClauses(clause1: DPLLClause, clause2: DPLLClause) -> DPLLClause:
    """
    Makes the resolution of two clauses.

    (-3, 4, 5) and (3, -4, 6) resolve to (5, 6)
    """
    variables_to_resolve = []
    full_variables = set(clause1 + clause2)

    for variable in full_variables:
        if (variable in clause1 and -variable in clause2) or (-variable in clause1 and variable in clause2):
            variables_to_resolve.append(variable)

    for variable in variables_to_resolve:
        full_variables.discard(variable)
        full_variables.discard(-variable)

    # print("Resolved", clause1, "and", clause2, "to", full_variables)

    return list(full_variables)


def _findUnitVariable(clausetable: CDCLTable) -> tuple[int, CDCLClause] | None:
    """
    Finds unit variables in the table, along with their clause.
    """
    for clause in clausetable.clauses:
        if any(v[1] is True for v in clause):
            continue
        unassigned = [v for v in clause if v[1] is None]
        if len(unassigned) == 1:
            return unassigned[0][0], clause
    return None


def _getNextSizeValue(clausetable: CDCLTable) -> int:
    """
    Heuristic to get the next value present in the CNF in the smallest clause.
    """
    unresolved = [c for c in clausetable.clauses if not any(
        v[1] is True for v in c)]
    clause_sorted = sorted(unresolved, key=lambda c: sum(
        1 for v in c if v[1] is None))
    for clause in clause_sorted:
        for variable_set in clause:
            if variable_set[1] is None:
                return variable_set[0]
