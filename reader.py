import copy

from type_defs import CDCLTable, DPLLTable, DPLLClause, CDCLClause


def extract_numbers(filepath: str) -> tuple[int, int, DPLLTable]:
    """
    Way to extract the required values and the clause text from the cnf file.
    Returns (variables, clauses, clause-table) for DPLL.
    """
    clause_table = []
    variables = 0
    clauses = 0

    with open(filepath) as f:
        for line in f:
            line_variables = line.split()
            if line.startswith("c") or line.startswith("%") or line.startswith("0") or line.startswith("\n"):
                continue
            # Is this the p cnf line?
            if line.startswith("p"):
                # Get the number of variables
                variables = int(line_variables[2])
                # Get the number of clauses
                clauses = int(line_variables[3])
            else:
                # Clauses end with 0s, remove them
                clause_table.append(list(map(int, line_variables[:-1])))

    return (variables, clauses, clause_table)


def convert_to_dpll(clause_table: CDCLTable | CDCLClause) -> DPLLTable | DPLLClause:
    """
    Converts a CDCL-style clause table to a simplified DPLL.
    This will result in a loss of data. Don't use it unnecessarily.
    Can also convert singular clauses to DPLL style, but True evaluations will return an empty list.

    [[(3, None), (2, False), (1, None)]]
    becomes
    [[3, 1]]

    [(1, False), (2, None), (3, None)]
    becomes
    [2, 3]
    """

    clause_copy = copy.deepcopy(clause_table)
    clauses_to_remove = []

    # Is this a CDCL Table?
    if isinstance(clause_table[0], list):
        # Just grab the first part with the variables.
        clause_table = clause_table.clauses
        clause_copy = copy.deepcopy(clause_table)

        for i, clause in enumerate(clause_table):
            variable_sets_to_remove = []
            variable_names_to_add = []
            found_true = False
            for variable_set in clause:
                variable_name, variable_value = variable_set
                if variable_value is True:                          # Does this clause evaluate to True?
                    clauses_to_remove.append(clause)
                    # Safety flag to avoid manipulating clauses which turn out to be True
                    found_true = True
                    break
                if variable_value is False:
                    variable_sets_to_remove.append(variable_set)
                else:
                    variable_sets_to_remove.append(variable_set)
                    variable_names_to_add.append(variable_name)
            if not found_true:
                for sets in variable_sets_to_remove:
                    clause_copy[i].remove(sets)
                clause_copy[i] += variable_names_to_add

    # Is this a CDCL Clause?
    elif isinstance(clause_table[0], tuple):
        for variable_set in clause_table:
            variable_name, variable_value = variable_set
            if variable_value is True:
                return []
            if variable_value is False:
                clauses_to_remove.append(variable_set)
            else:
                clauses_to_remove.append(variable_set)
                clause_copy.append(variable_name)

    for elements in clauses_to_remove:
        clause_copy.remove(elements)

    return clause_copy


def convert_to_cdcl(clause_table: DPLLTable | DPLLClause) -> CDCLTable | CDCLClause:
    """
    Converts a simplified DPLL list back to a CDCL form.
    Also makes the default list of clause values.
    Also converts singular DPLL clauses to CDCL ones.

    [[3, 2, 1]]
    becomes
    [(3, None), (2, None), (1, None)], [None]

    [1, 2, 3]
    becomes
    [(1, None), (2, None), (3, None)]
    """
    if isinstance(clause_table[0], list):                            # Is this a DPLL Table?
        clause_copy = []
        clauses = 0
        for clause in clause_table:
            new_clause = list(map(lambda x: (x, None), clause))
            clause_copy.append(new_clause)
            clauses += 1
        clause_values = [None] * clauses
        return CDCLTable(clause_copy, clause_values)

    # Is this a DPLL Clause?
    if isinstance(clause_table[0], int):
        new_clause = list(map(lambda x: (x, None), clause_table))
        return new_clause


def pretty_print(clause_table: DPLLTable | CDCLTable | bool) -> None:
    """
    Convenience function to pretty-list an array of clauses.
    """
    if isinstance(clause_table[0][0], list):                         # Is this a CDCL Table?
        clause_table = clause_table.clauses

    # Is this a table?
    if isinstance(clause_table[0], list):
        for clause in clause_table:
            print(clause)
    else:                                                           # Is this a boolean?
        print(clause_table)
