import copy

from Types import DPLLTable, DPLLClause


def DPLL(clause_table: DPLLTable, variables: int, starting: int) -> bool:
    """
    The core of the DPLL algorithm.
    """
    clause_table = _process_variable(
        clause_table, starting, abs(starting) / starting)
    clause_table = _handle_unit_clauses_recursive(clause_table)
    clause_table = _handle_pure_literals(clause_table, variables)

    if evaluator(clause_table) is not None:
        return evaluator(clause_table)

    else:
        nextvalue = _get_next_size_value(clause_table)
        # nextvalue = _getNextValue(starting, clausetable)
        return DPLL(copy.deepcopy(clause_table), variables, nextvalue) or DPLL(copy.deepcopy(clause_table), variables, -nextvalue)


def evaluator(clausetable: DPLLTable) -> bool | None:
    """
    Returns True if SAT, False if UNSAT, None if incomplete.
    """
    if not clausetable:
        return True
    for clause in clausetable:
        if len(clause) == 0:
            return False
    return None


def dpll_pre_processor(original_clause_table: DPLLTable, variables: int) -> bool | DPLLTable:
    """
    Recursively preprocesses the table. Handles pure literals, unit and tautological clauses.
    """
    # print("Preprocessing...")

    clausetable = []
    for clause in original_clause_table:
        normalized = sorted(list(set(clause)))
        if normalized not in clausetable:                                       # Remove any duplicate clauses
            clausetable.append(normalized)

    # Make a referential copy
    comparing_table = copy.deepcopy(clausetable)

    comparing_table = _handle_tautologies(comparing_table)
    comparing_table = _handle_unit_clauses_recursive(comparing_table)
    comparing_table = _handle_pure_literals(comparing_table, variables)
    comparing_table = _self_subsuming_resolution_recursive(comparing_table)
    comparing_table = _handle_blocked_clauses(comparing_table)

    if evaluator(comparing_table) is not None:
        return evaluator(comparing_table)

    # If the referential copy differs from what we have
    if comparing_table != clausetable:
        return dpll_pre_processor(comparing_table, variables)

    # print("Finished preprocessing")
    return comparing_table


def _process_variable(clause_table: DPLLTable, variable: int, polarity: int) -> DPLLTable:
    """
    Non-recursively handles a single variable with linear propagation.
    """
    clause_copy = copy.deepcopy(clause_table)
    # We're doing a side-by-side evaluation against clausetable so there may be discrepancies
    for clause in clause_table:
        for literal in clause:
            if abs(literal) == abs(variable):
                # If this variable evaluates to true
                if polarity * abs(variable) == literal:
                    # print("Removing", clause)
                    # Remove the clause
                    clause_copy.remove(clause)
                else:                                                           # If it evaluates to false
                    if clause in clause_copy:
                        clause_copy[clause_copy.index(clause)].remove(
                            literal)    # Just remove the variable

    # prettyPrint(clausecopy)
    return clause_copy


def _handle_blocked_clauses(clausetable: DPLLTable) -> DPLLTable:
    """
    Scans for clauses where a member literal has its opposite polarity present somewhere else in the table.
    And checks if all of those clauses can resolve to a tautology with the original clause.
    If they can, it is a blocked clause, and is removed, so recursively handled.
    """
    clausecopy = copy.deepcopy(clausetable)
    for clause in clausetable:
        if _is_blocked_clause(clausetable, clause):
            if clause in clausecopy:
                clausecopy.remove(clause)
    if clausecopy != clausetable:
        return _handle_blocked_clauses(clausecopy)
    else:
        return clausetable


def _is_blocked_clause(clausetable: DPLLTable, clause: DPLLClause) -> bool:
    # There exists a variable in the clause
    for variable in clause:
        otherClauseFound = False
        blockedDefault = True
        for other_clause in clausetable:                                        # For all other clauses
            if clause is other_clause:
                continue
            # Which have the opposite polarity of that variable in them
            elif -variable in other_clause:
                otherClauseFound = True
                # Such that their resolution
                resolution = _make_resolution(clause, other_clause, variable)
                # Is a tautology
                if not _is_tautology(resolution):
                    blockedDefault = False
                    break
        if blockedDefault and otherClauseFound:
            # print("Found blocked clause", clause, "by variable", variable)
            return True
    return False


def _handle_unit_clauses_recursive(clausetable: DPLLTable) -> DPLLTable:
    """
    Wrapper to handle the unit clause function recursively.
    """
    clausecopy = copy.deepcopy(clausetable)
    clausetable = _handle_unit_clauses(clausetable)
    if clausecopy != clausetable:
        return _handle_unit_clauses_recursive(clausetable)
    return clausetable


def _handle_unit_clauses(clausetable: DPLLTable) -> DPLLTable:
    """
    Look for singular clauses and handle them.
    """
    for clause in clausetable:
        if len(clause) == 1:
            # print("Handling unit clause", clause)
            value = clause[0]
            polarity = value / abs(value)
            clausetable = _process_variable(clausetable, value, polarity)

    return clausetable


def _handle_pure_literals(clausetable: DPLLTable, variables: int) -> DPLLTable:
    for variable in range(1, variables+1):
        isPure, polarity = _is_pure_literal(clausetable, variable)
        if isPure:
            # print("Handling pure literal", variable)
            clausetable = _process_variable(clausetable, variable, polarity)

    return clausetable


def _is_pure_literal(clausetable: DPLLTable, variable: int) -> tuple[bool, int]:
    """
    Checks if a variable in the clause table is pure.
    Returns 2 values, first is a boolean, second is +1 or -1 for the polarity of the variable, otherwise 0.
    """
    positive_flag_set = 0                                           # A flag for checking if we encountered this
    for clause in clausetable:
        for literal in clause:
            if abs(literal) == abs(variable):
                if positive_flag_set == 0:                          # If this is the first encounter
                    if literal == variable:
                        positive_flag_set = 1                       # This is only a positive
                    else:
                        positive_flag_set = -1                      # This is only a negative
                # If this isn't the first encounter and there's opposite polarities
                elif literal != variable * positive_flag_set:
                    return (False, 0)

    if positive_flag_set != 0:                                      # If there were no encounters
        return (True, positive_flag_set)
    else:
        return (False, 0)


def _handle_tautologies(clausetable: DPLLTable) -> DPLLTable:
    comparing_table = copy.deepcopy(clausetable)
    for clause in clausetable:
        if _is_tautology(clause):
            if clause in comparing_table:
                # print("Removing tautological clause", clause)
                comparing_table.remove(clause)

    return comparing_table


def _is_tautology(clause: DPLLClause) -> bool:
    """
    Checks if a clause has the same variables which are opposite to each other in polarity.
    """
    for i in range(len(clause)):
        for j in range(i+1, len(clause)):
            if clause[i] == -clause[j]:
                return True
    return False


def _self_subsuming_resolution_recursive(clausetable: DPLLTable) -> DPLLTable:
    """
    Finds clauses which have only one common variable of opposite polarity, and resolves them.
    Whichever clause is a superset of the resolution gets reduced to the resolution itself.
    """
    clausecopy = copy.deepcopy(clausetable)
    for i in range(len(clausetable)):
        for j in range(i, len(clausetable)):
            resolvable, value = _can_be_resolved(
                clausetable[i], clausetable[j])
            if resolvable:
                resolvedClause = _resolve_clause_subsets(
                    clausetable[i], clausetable[j], value)
                if resolvedClause is not None:
                    if resolvedClause[0] in clausecopy:
                        clausecopy.remove(resolvedClause[0])
                        clausecopy.append(resolvedClause[1])

    if clausecopy != clausetable:
        return _self_subsuming_resolution_recursive(clausecopy)
    else:
        return clausetable


def _can_be_resolved(clause1: DPLLClause, clause2: DPLLClause) -> tuple[bool, int]:
    """
    Checks if 2 clauses are resolvable, and returns the common value if they are.
    """
    commonValueFound = False
    commonValue = 0
    for variable in clause1:
        if -variable in clause2:                    # If we find a common value of opposite polarity in the clauses
            if commonValueFound is False:           # And it's unique
                commonValueFound = True
                commonValue = variable
            else:
                return False, 0
    return commonValueFound, commonValue


def _resolve_clause_subsets(clause1: DPLLClause, clause2: DPLLClause, value: int) -> tuple[DPLLClause, DPLLClause]:
    """
    Resolves 2 clauses and checks if the resolution is a subset of the opening clauses.
    If it is, it returns [clause-to-replace], [resolution]
    """
    resolved_clause = _make_resolution(clause1, clause2, value)

    if set(resolved_clause) <= set(clause1):
        # print("Resolved", clause1, "from", clause1, ",", clause2, "to", resolvedClause)
        return clause1, resolved_clause
    elif set(resolved_clause) <= set(clause2):
        # print("Resolved", clause2, "from", clause1, ",", clause2, "to", resolvedClause)
        return clause2, resolved_clause
    return None


def _make_resolution(clause1: DPLLClause, clause2: DPLLClause, value_to_remove: int) -> DPLLClause:
    """
    Makes a resolution from 2 clauses and removes the passed value.
    """
    resolvedClause = sorted(set(clause1 + clause2))
    resolvedClause.remove(value_to_remove)
    resolvedClause.remove(-value_to_remove)

    return resolvedClause


def _get_next_size_value(clausetable: DPLLTable) -> int:
    """
    Heuristic to get the next value present in the CNF in the smallest clause.
    """
    clausesorted = sorted(clausetable, key=len)
    return clausesorted[0][0]


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
