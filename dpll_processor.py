import copy

from type_defs import DPLLTable, DPLLClause


def dpll(clause_table: DPLLTable, variables: int, starting: int) -> bool:
    """
    The core of the DPLL algorithm.
    """
    clause_table = _process_variable(
        clause_table, starting, abs(starting) / starting
    )
    clause_table = _handle_unit_clauses_recursive(clause_table)
    clause_table = _handle_pure_literals(clause_table, variables)

    if evaluator(clause_table) is not None:
        return evaluator(clause_table)

    next_value = _get_next_size_value(clause_table)
    # nextvalue = _get_next_value(starting, clause_table)
    return dpll(copy.deepcopy(clause_table), variables, next_value) or dpll(
        copy.deepcopy(clause_table), variables, -next_value
    )


def evaluator(clause_table: DPLLTable) -> bool | None:
    """
    Returns True if SAT, False if UNSAT, None if incomplete.
    """
    if not clause_table:
        return True
    for clause in clause_table:
        if len(clause) == 0:
            return False
    return None


def dpll_preprocessor(
    original_clause_table: DPLLTable, variables: int
) -> bool | DPLLTable:
    """
    Recursively preprocesses the table. Handles pure literals, unit and tautological clauses.
    """
    # print("Preprocessing...")

    clause_table = []
    for clause in original_clause_table:
        normalized = sorted(list(set(clause)))
        if normalized not in clause_table:                                  # Remove any duplicate clauses
            clause_table.append(normalized)

    # Make a referential copy
    comparing_table = copy.deepcopy(clause_table)
    # Process everything (super expensive)
    comparing_table = _handle_tautologies(comparing_table)
    comparing_table = _handle_unit_clauses_recursive(comparing_table)
    comparing_table = _handle_pure_literals(comparing_table, variables)
    comparing_table = _self_subsuming_resolution_recursive(comparing_table)
    comparing_table = _handle_blocked_clauses(comparing_table)

    # If there's SAT or UNSAT, we're done
    if evaluator(comparing_table) is not None:
        return evaluator(comparing_table)

    if (
        comparing_table != clause_table
    ):                                                                      # Should we process this again?
        return dpll_preprocessor(comparing_table, variables)

    # print("Finished preprocessing")
    # If not, return the processed table
    return comparing_table


def _process_variable(clause_table: DPLLTable, variable: int, polarity: int) -> DPLLTable:
    """
    Non-recursively handles a single variable with linear propagation.
    """
    clause_copy = copy.deepcopy(clause_table)
    for clause in clause_table:
        # We're doing a side-by-side evaluation against clause_table so there may be discrepancies
        for literal in clause:
            if abs(literal) == abs(variable):
                if (
                    polarity * abs(variable) == literal
                ):                                                      # If this variable evaluates to true
                    # print("Removing", clause)                         # Remove the clause
                    clause_copy.remove(clause)
                else:                                                   # But if it evaluates to false
                    if clause in clause_copy:
                        clause_copy[clause_copy.index(clause)].remove(
                            literal
                        )                                               # Then just remove the variable

    # pretty_print(clause_copy)
    return clause_copy


def _handle_blocked_clauses(clause_table: DPLLTable) -> DPLLTable:
    """
    Scans for clauses where a member literal has its opposite polarity present somewhere else in the table.
    And checks if all of those clauses can resolve to a tautology with the original clause.
    If they can, it is a blocked clause, and is removed, so recursively handled.
    """
    clause_copy = copy.deepcopy(clause_table)
    for clause in clause_table:
        if _is_blocked_clause(clause_table, clause):
            if clause in clause_copy:
                clause_copy.remove(clause)
    if clause_copy != clause_table:
        return _handle_blocked_clauses(clause_copy)

    return clause_table


def _is_blocked_clause(clause_table: DPLLTable, clause: DPLLClause) -> bool:
    # A clause is said to be blocked if
    for variable in clause:                         # There exists a certain variable in the clause
        other_clause_found = False
        blocked_default = True
        for other_clause in clause_table:           # And if for all other clauses
            if clause is other_clause:
                continue
            if (
                -variable in other_clause
            ):                                      # Which have the opposite polarity of that variable in them
                other_clause_found = True
                resolution = _make_resolution(
                    clause, other_clause, variable
                )                                   # Their resolution
                if not _is_tautology(resolution):   # Is a tautology
                    blocked_default = False
                    break
        if blocked_default and other_clause_found:
            # print("Found blocked clause", clause, "by variable", variable)
            return True
    return False


def _handle_unit_clauses_recursive(clause_table: DPLLTable) -> DPLLTable:
    """
    Wrapper to handle the unit clause function recursively.
    """
    clause_copy = copy.deepcopy(clause_table)
    clause_table = _handle_unit_clauses(clause_table)
    if clause_copy != clause_table:
        return _handle_unit_clauses_recursive(clause_table)
    return clause_table


def _handle_unit_clauses(clause_table: DPLLTable) -> DPLLTable:
    """
    Look for singular clauses and handle them.
    """
    for clause in clause_table:
        if len(clause) == 1:
            # print("Handling unit clause", clause)
            value = clause[0]
            polarity = value / abs(value)
            clause_table = _process_variable(clause_table, value, polarity)

    return clause_table


def _handle_pure_literals(clause_table: DPLLTable, variables: int) -> DPLLTable:
    for variable in range(1, variables + 1):
        is_pure, polarity = _is_pure_literal(clause_table, variable)
        if is_pure:
            # print("Handling pure literal", variable)
            clause_table = _process_variable(clause_table, variable, polarity)

    return clause_table


def _is_pure_literal(clause_table: DPLLTable, variable: int) -> tuple[bool, int]:
    """
    Checks if a variable in the clause table is pure.
    Returns 2 values, first is a boolean, second is +1 or -1 for the polarity of the variable, otherwise 0.
    """
    # A flag for checking if we encountered this
    positive_flag_set = 0
    for clause in clause_table:
        for literal in clause:
            if abs(literal) == abs(variable):
                if positive_flag_set == 0:      # If this is the first encounter
                    if literal == variable:
                        positive_flag_set = 1   # This is only a positive literal
                    else:
                        positive_flag_set = -1  # This is only a negative literal
                elif (
                    literal != variable * positive_flag_set
                ):                              # If this isn't the first encounter and there's opposite polarities
                    return (False, 0)           # It's not pure

    if positive_flag_set != 0:                  # If there were no other encounters
        # It's pure, the flag denotes its polarity
        return (True, positive_flag_set)
    return (False, 0)


def _handle_tautologies(clause_table: DPLLTable) -> DPLLTable:
    comparing_table = copy.deepcopy(clause_table)
    for clause in clause_table:
        if _is_tautology(clause):
            if clause in comparing_table:
                # print("Removing tautological clause", clause)
                comparing_table.remove(clause)

    return comparing_table


def _is_tautology(clause: DPLLClause) -> bool:
    """
    Checks if a clause has the same variables which are opposite to each other in polarity.
    """
    for i, variable in enumerate(clause):
        for other_variable_enum in enumerate(clause[i + 1:], start=i + 1):
            other_variable = other_variable_enum[1]
            if variable == -other_variable:
                return True
    return False


def _self_subsuming_resolution_recursive(clause_table: DPLLTable) -> DPLLTable:
    """
    Finds clauses which have only one common variable of opposite polarity, and resolves them.
    Whichever clause is a superset of the resolution gets reduced to the resolution itself.
    """
    clause_copy = copy.deepcopy(clause_table)
    for i in range(len(clause_table)):
        for j in range(i, len(clause_table)):
            resolvable, value = _can_be_resolved(
                clause_table[i], clause_table[j])
            if resolvable:
                resolved_clause = _resolve_clause_subsets(
                    clause_table[i], clause_table[j], value
                )
                if resolved_clause is not None:
                    if resolved_clause[0] in clause_copy:
                        clause_copy.remove(resolved_clause[0])
                        clause_copy.append(resolved_clause[1])

    if clause_copy != clause_table:
        return _self_subsuming_resolution_recursive(clause_copy)
    return clause_table


def _can_be_resolved(clause1: DPLLClause, clause2: DPLLClause) -> tuple[bool, int]:
    """
    Checks if 2 clauses are resolvable, and returns the common value if they are.
    """
    common_value_found = False
    common_value = 0
    for variable in clause1:
        if (
            -variable in clause2
        ):                                   # If we find a common value of opposite polarity in the clauses
            if common_value_found is False:  # And it's unique
                common_value_found = True
                common_value = variable
            else:
                return False, 0
    return common_value_found, common_value


def _resolve_clause_subsets(
    clause1: DPLLClause, clause2: DPLLClause, value: int
) -> tuple[DPLLClause, DPLLClause]:
    """
    Resolves 2 clauses and checks if the resolution is a subset of the opening clauses.
    If it is, it returns [clause-to-replace], [resolution]
    """
    resolved_clause = _make_resolution(clause1, clause2, value)

    if set(resolved_clause) <= set(clause1):
        # print("Resolved", clause1, "from", clause1, ",", clause2, "to", resolved_clause)
        return clause1, resolved_clause
    if set(resolved_clause) <= set(clause2):
        # print("Resolved", clause2, "from", clause1, ",", clause2, "to", resolved_clause)
        return clause2, resolved_clause
    return None


def _make_resolution(
    clause1: DPLLClause, clause2: DPLLClause, value_to_remove: int
) -> DPLLClause:
    """
    Makes a resolution from 2 clauses and removes the passed value.
    """
    resolved_clause = sorted(set(clause1 + clause2))
    resolved_clause.remove(value_to_remove)
    resolved_clause.remove(-value_to_remove)

    return resolved_clause


def _get_next_size_value(clause_table: DPLLTable) -> int:
    """
    Heuristic to get the next value present in the CNF in the smallest clause.
    """
    clause_sorted = sorted(clause_table, key=len)
    return clause_sorted[0][0]


def _get_next_value(current_value: int, clause_table: DPLLTable) -> int:
    """
    Heuristic to get the next available value present in the CNF.
    """
    check_value = abs(current_value) + 1
    for clause in clause_table:
        for variable in clause:
            if check_value == abs(variable):
                return check_value

    return _get_next_value(check_value, clause_table)
