from reader import convert_to_cdcl
from type_defs import (
    CDCLTable,
    CDCLClause,
    CDCLVariable,
    DPLLClause,
    DecisionTrail,
    Decision,
)


def cdcl(clause_table: CDCLTable, decision_trail: DecisionTrail) -> bool:
    # Make a dictionary from the table
    variable_to_clauses: dict[int, list[int]] = {}
    for i, clause in enumerate(clause_table.clauses):
        for variable_set in clause:
            key = abs(variable_set[0])
            variable_to_clauses.setdefault(key, []).append(i)

    while True:  # Start solving
        if not decision_trail:  # If we've just started solving
            current_level = 0
        else:
            current_level = decision_trail[-1].level

        found_unit_variable = _find_unit_variable(
            clause_table)  # Look for unit variables
        if found_unit_variable is not None:
            unit_var, unit_clause = found_unit_variable
            normalized_cause = [v[0] for v in unit_clause]
            decision = Decision(unit_var, normalized_cause, current_level)
        else:  # Or just make a decision
            decision = Decision(_get_next_size_value(
                clause_table), None, current_level + 1)
            # print(_get_next_size_value(clause_table))
        decision_trail.append(decision)

        current_level = decision.level
        _evaluate_variable(
            clause_table, decision_trail, variable_to_clauses
        )  # And start solving

        # Now see what the table has in it
        table_value = _evaluate_table(clause_table)
        if table_value is True:  # If it's full of True, we're done
            return True
        if table_value is False:
            if current_level == 0:  # If it's False but we can't backtrack,
                return False  # We're UNSAT
            false_index = next(
                (i for i, x in enumerate(clause_table.values) if x is False), None
            )
            false_clause = list(
                set(x[0] for x in clause_table.clauses[false_index])
            )  # But if we can, look for the False clause
            learned_clause = convert_to_cdcl(
                _learn_clause(false_clause, decision_trail)
            )  # Derive a learned clause
            wipe_level = _second_highest_decision_level(
                learned_clause, decision_trail
            )  # Backtrack to the second highest decision level
            _wipe_trail_and_table_after(
                wipe_level, decision_trail, clause_table
            )  # Reset the table from there onwards
            _update_learned_clause(
                learned_clause, decision_trail, clause_table, variable_to_clauses
            )


def _learn_clause(starter_clause: DPLLClause, decision_trail: DecisionTrail) -> DPLLClause:
    current_level = decision_trail[-1].level
    working_clause = starter_clause

    while True:
        variable_decisions = [
            _get_variable_decision_level(x, decision_trail) for x in working_clause
        ]
        if (
            variable_decisions.count(current_level) == 1
        ):  # We need only one variable of the current level to be in the learned clause
            return working_clause

        simplified_trail = [abs(decision.variable)
                            for decision in decision_trail]
        latest_cause = None
        for i, latest_decision in enumerate(simplified_trail[::-1]):
            if latest_decision in [abs(x) for x in working_clause]:
                decision = decision_trail[-(i + 1)]
                if decision.level == current_level and decision.cause_clause is not None:
                    latest_cause = decision.cause_clause
                    break

        working_clause = _resolve_clauses(latest_cause, working_clause)


def _update_learned_clause(
    learned_clause: CDCLClause,
    decision_trail: DecisionTrail,
    clause_table: CDCLTable,
    variable_to_clauses: dict,
) -> None:
    """
    Brings the learned clause up to speed with everything assigned so far.
    Also adds it to the table.
    """
    for j, variable_set in enumerate(learned_clause):
        variable_name = variable_set[0]
        for i, decision in enumerate(decision_trail):
            if abs(decision.variable) == abs(variable_name):
                value_to_set = True if decision.variable / variable_name > 0 else False
                learned_clause[j] = _set_value(variable_set, value_to_set)

    clause_table.clauses.append(learned_clause)
    clause_table.values.append(_evaluate_clause(learned_clause))

    new_index = len(clause_table.clauses) - 1
    for variable_set in learned_clause:
        variable_to_clauses.setdefault(
            abs(variable_set[0]), []).append(new_index)


def _second_highest_decision_level(
    learned_clause: CDCLClause, decision_trail: DecisionTrail
) -> int:
    """
    Arranges all the levels in the decision trail and gets the second highest.
    And if there's just one, then levels-1
    """
    learned_clause = [x[0] for x in learned_clause]
    levels = sorted(
        [_get_variable_decision_level(v, decision_trail)
         for v in learned_clause],
        reverse=True,
    )
    if len(levels) < 2:
        return decision_trail[-1].level - 1
    return levels[1]


def _get_variable_decision_level(variable: int, decision_trail: DecisionTrail) -> int:
    """
    Given a variable, get its decision level from the trail.
    Can handle both polarities.
    """
    for decision in decision_trail:
        if abs(decision.variable) == abs(variable):
            return decision.level
    return -1


def _wipe_trail_and_table_after(
    level: int, decision_trail: DecisionTrail, clause_table: CDCLTable
) -> None:
    """
    Takes a level and wipes it out from the table, along with anything after it.
    """
    wiped = []
    for i, decision in enumerate(decision_trail):
        if decision.level > level:
            wiped = [d.variable for d in decision_trail[i:]]
            del decision_trail[i:]
            break
    _undo_evaluations(clause_table, wiped)


def _undo_evaluations(clause_table: CDCLTable, variables: list) -> None:
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
                clause[j] = _set_value(variable_set, None)
        if reevaluate_clause:
            clause_values[i] = _evaluate_clause(clause)
            # print("Unevaluated clause to", clause_values[i])


def _evaluate_table(clause_table: CDCLTable, lazy: bool = True) -> bool | None:
    """
    Evaluates the entire clause table.
    Has a lazy flag (automatically enabled).
    Disable lazy flag if you want to evaluate every clause (computationally expensive.)
    """
    clause_values = clause_table.values
    if not lazy:
        clause_variables = clause_table.clauses
        for i, clause in enumerate(clause_variables):
            clause_values[i] = _evaluate_clause(clause)

    if False in clause_values:
        return False
    if None in clause_values:
        return None
    return True


def _evaluate_clause(clause: CDCLClause) -> bool | None:
    """
    Looks at the values of the variables in a clause and decides its current value.
    """
    false_flag = True

    for variable_set in clause:
        variable_value = variable_set[1]
        if (
            variable_value is True
        ):  # If we find a singular True, it's a True evaluation.
            return True
        elif variable_value is None:  # If we find a singular None, it cannot be False.
            false_flag = False

    return (
        False if false_flag else None
        # If we haven't found any Nones or Trues, it must be False, otherwise None.
    )


def _evaluate_variable(
    clause_table: CDCLTable, decision_trail: DecisionTrail, variable_to_clauses: dict
) -> None:
    decision = decision_trail[-1]
    variable = decision.variable
    decision_polarity = variable > 0

    clause_variables = clause_table.clauses
    clause_values = clause_table.values

    for i in variable_to_clauses.get(abs(variable), []):
        if clause_values[i] is True:
            continue
        clause = clause_variables[i]
        for j, variable_set in enumerate(clause):
            if abs(variable_set[0]) == abs(variable):
                polarity = variable_set[0] > 0
                clause[j] = _set_value(
                    variable_set, polarity == decision_polarity)
        clause_values[i] = _evaluate_clause(clause)


def _set_value(variable: CDCLVariable, value: bool | None) -> CDCLVariable:
    """
    Pure helper function to set a value for a variable tuple in a clause.
    """
    return (variable[0], value)


def _resolve_clauses(clause1: DPLLClause, clause2: DPLLClause) -> DPLLClause:
    """
    Makes the resolution of two clauses.

    (-3, 4, 5) and (3, -4, 6) resolve to (5, 6)
    """
    variables_to_resolve = []
    full_variables = set(clause1 + clause2)

    for variable in full_variables:
        if ((variable in clause1) and (-variable in clause2)) or (
            (-variable in clause1) and (variable in clause2)
        ):
            variables_to_resolve.append(variable)

    for variable in variables_to_resolve:
        full_variables.discard(variable)
        full_variables.discard(-variable)

    # print("Resolved", clause1, "and", clause2, "to", full_variables)

    return list(full_variables)


def _find_unit_variable(clause_table: CDCLTable) -> tuple[int, CDCLClause] | None:
    """
    Finds unit variables in the table, along with their clause.
    """
    for clause in clause_table.clauses:
        if any(v[1] is True for v in clause):
            continue
        unassigned = [v for v in clause if v[1] is None]
        if len(unassigned) == 1:
            return unassigned[0][0], clause
    return None


def _get_next_size_value(clause_table: CDCLTable) -> int:
    """
    Heuristic to get the next value present in the CNF in the smallest clause.
    """
    unresolved = [c for c in clause_table.clauses if not any(
        v[1] is True for v in c)]
    clause_sorted = sorted(unresolved, key=lambda c: sum(
        1 for v in c if v[1] is None))
    for clause in clause_sorted:
        for variable_set in clause:
            if variable_set[1] is None:
                return variable_set[0]
