import copy

from Reader import prettyPrint
from Types import DPLLTable, DPLLClause


def DPLL(clausetable: DPLLTable, variables: int, starting: int) -> bool:
    """
    The core of the DPLL algorithm.
    """
    clausetable = _processVariable(clausetable, starting, abs(starting)/starting)
    clausetable = _handleUnitClausesRecursive(clausetable)
    clausetable = _handlePureLiterals(clausetable, variables)

    if evaluator(clausetable) is not None:
        return evaluator(clausetable)

    else:
        nextvalue = _getNextSizeValue(clausetable)
        # nextvalue = _getNextValue(starting, clausetable)
        return DPLL(copy.deepcopy(clausetable), variables, nextvalue) or DPLL(copy.deepcopy(clausetable), variables, -nextvalue)


def evaluator(clausetable: DPLLTable) -> bool|None:
    """
    Returns True if SAT, False if UNSAT, None if incomplete.
    """
    if (not clausetable):
        return True
    for clause in clausetable:
        if len(clause) == 0:
            return False
    return None


def DPLLpreProcessor(original_clausetable: DPLLTable, variables: int) -> bool|DPLLTable:
    """
    Recursively preprocesses the table. Handles pure literals, unit and tautological clauses.
    """
    # print("Preprocessing...")

    clausetable = []
    for clause in original_clausetable:
        normalized = sorted(list(set(clause)))
        if normalized not in clausetable:                                       # Remove any duplicate clauses
            clausetable.append(normalized)

    comparing_table = copy.deepcopy(clausetable)                                # Make a referential copy

    comparing_table = _handleTautologies(comparing_table)
    comparing_table = _handleUnitClausesRecursive(comparing_table)
    comparing_table = _handlePureLiterals(comparing_table, variables)
    comparing_table = _selfSubsumingResolutionRecursive(comparing_table)
    comparing_table = _handleBlockedClauses(comparing_table)

    if evaluator(comparing_table) is not None:
        return evaluator(comparing_table)

    if (comparing_table != clausetable):                                        # If the referential copy differs from what we have
        return DPLLpreProcessor(comparing_table, variables)

    # print("Finished preprocessing")
    return comparing_table


def _processVariable(clausetable: DPLLTable, variable: int, polarity: int) -> DPLLTable:
    """
    Non-recursively handles a single variable with linear propagation.
    """
    clausecopy = copy.deepcopy(clausetable)
    for clause in clausetable:                                                  # We're doing a side-by-side evaluation against clausetable so there may be discrepancies
        for literal in clause:
            if abs(literal) == abs(variable):
                if polarity*abs(variable) == literal:                           # If this variable evaluates to true
                    # print("Removing", clause)
                    clausecopy.remove(clause)                                   # Remove the clause              
                else:                                                           # If it evaluates to false
                    if clause in clausecopy:
                        clausecopy[clausecopy.index(clause)].remove(literal)    # Just remove the variable

    # prettyPrint(clausecopy)
    return clausecopy


def _handleBlockedClauses(clausetable: DPLLTable) -> DPLLTable:
    """
    Scans for clauses where a member literal has its opposite polarity present somewhere else in the table.
    And checks if all of those clauses can resolve to a tautology with the original clause.
    If they can, it is a blocked clause, and is removed, so recursively handled.
    """
    clausecopy = copy.deepcopy(clausetable)
    for clause in clausetable:
        if _isBlockedClause(clausetable, clause):
            if clause in clausecopy:
                clausecopy.remove(clause)
    if (clausecopy != clausetable):
        return _handleBlockedClauses(clausecopy)
    else:
        return clausetable

def _isBlockedClause(clausetable: DPLLTable, clause: DPLLClause) -> bool:
    for variable in clause:                                                     # There exists a variable in the clause
        otherClauseFound = False
        blockedDefault = True
        for other_clause in clausetable:                                        # For all other clauses
            if clause is other_clause:
                continue
            elif -variable in other_clause:                                     # Which have the opposite polarity of that variable in them
                otherClauseFound = True
                resolution = _makeResolution(clause, other_clause, variable)    # Such that their resolution
                if not _isTautology(resolution):                                # Is a tautology
                    blockedDefault = False
                    break
        if blockedDefault and otherClauseFound:
            # print("Found blocked clause", clause, "by variable", variable)
            return True
    return False


def _handleUnitClausesRecursive(clausetable: DPLLTable) -> DPLLTable:
    """
    Wrapper to handle the unit clause function recursively.
    """
    clausecopy = copy.deepcopy(clausetable)
    clausetable = _handleUnitClauses(clausetable)
    if (clausecopy != clausetable):
        return _handleUnitClausesRecursive(clausetable)
    return clausetable

def _handleUnitClauses(clausetable: DPLLTable) -> DPLLTable:
    """
    Look for singular clauses and handle them.
    """
    for clause in clausetable:
        if len(clause) == 1:
            # print("Handling unit clause", clause)
            value = clause[0]
            polarity = value/abs(value)
            clausetable = _processVariable(clausetable, value, polarity)

    return clausetable


def _handlePureLiterals(clausetable: DPLLTable, variables: int) -> DPLLTable:
    for variable in range(1, variables+1):
        isPure, polarity = _isPureLiteral(clausetable, variable)
        if (isPure):
            # print("Handling pure literal", variable)
            clausetable = _processVariable(clausetable, variable, polarity)

    return clausetable

def _isPureLiteral(clausetable: DPLLTable, variable: int) -> tuple[bool, int]:
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
                elif (literal != variable*positive_flag_set):       # If this isn't the first encounter and there's opposite polarities
                    return (False, 0)

    if positive_flag_set != 0:                                      # If there were no encounters
        return (True, positive_flag_set)
    else:
        return (False, 0)


def _handleTautologies(clausetable: DPLLTable) -> DPLLTable:
    comparing_table = copy.deepcopy(clausetable)
    for clause in clausetable:
        if _isTautology(clause):
            if clause in comparing_table:
                # print("Removing tautological clause", clause)
                comparing_table.remove(clause)

    return comparing_table

def _isTautology(clause: DPLLClause) -> bool:
    """
    Checks if a clause has the same variables which are opposite to each other in polarity.
    """
    for i in range(len(clause)):
        for j in range(i+1, len(clause)):
            if clause[i] == -clause[j]:
                return True
    return False


def _selfSubsumingResolutionRecursive(clausetable: DPLLTable) -> DPLLTable:
    """
    Finds clauses which have only one common variable of opposite polarity, and resolves them.
    Whichever clause is a superset of the resolution gets reduced to the resolution itself.
    """
    clausecopy = copy.deepcopy(clausetable)
    for i in range(len(clausetable)):
        for j in range(i, len(clausetable)):
            resolvable, value = _canBeResolved(clausetable[i], clausetable[j])
            if resolvable:
                resolvedClause = _resolveClauseSubsets(clausetable[i], clausetable[j], value)
                if resolvedClause is not None:
                    if (resolvedClause[0] in clausecopy):
                        clausecopy.remove(resolvedClause[0])
                        clausecopy.append(resolvedClause[1])

    if (clausecopy != clausetable):
        return _selfSubsumingResolutionRecursive(clausecopy)
    else:
        return clausetable

def _canBeResolved(clause1: DPLLClause, clause2: DPLLClause) -> tuple[bool, int]:
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

def _resolveClauseSubsets(clause1: DPLLClause, clause2: DPLLClause, value: int) -> tuple[DPLLClause, DPLLClause]:
    """
    Resolves 2 clauses and checks if the resolution is a subset of the opening clauses.
    If it is, it returns [clause-to-replace], [resolution]
    """
    resolvedClause = _makeResolution(clause1, clause2, value)

    if set(resolvedClause) <= set(clause1):
        # print("Resolved", clause1, "from", clause1, ",", clause2, "to", resolvedClause)
        return clause1, resolvedClause
    elif set(resolvedClause) <= set(clause2):
        # print("Resolved", clause2, "from", clause1, ",", clause2, "to", resolvedClause)
        return clause2, resolvedClause
    return None

def _makeResolution(clause1: DPLLClause, clause2: DPLLClause, valueToRemove: int) -> DPLLClause:
    """
    Makes a resolution from 2 clauses and removes the passed value.
    """
    resolvedClause = sorted(set(clause1 + clause2))
    resolvedClause.remove(valueToRemove)
    resolvedClause.remove(-valueToRemove)

    return resolvedClause


def _getNextSizeValue(clausetable: DPLLTable) -> int:
    """
    Heuristic to get the next value present in the CNF in the smallest clause.
    """
    clausesorted = sorted(clausetable, key=len)
    return clausesorted[0][0]

def _getNextValue(currentValue: int, clausetable: DPLLTable) -> int:
    """
    Heuristic to get the next available value present in the CNF.
    """
    check_value = abs(currentValue) + 1
    for clause in clausetable:
        for variable in clause:
            if check_value == abs(variable):
                return check_value

    return _getNextValue(check_value, clausetable)
