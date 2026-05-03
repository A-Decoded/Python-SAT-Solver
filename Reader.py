import copy

from Types import CDCLTable, DPLLTable, DPLLClause, CDCLClause


def extract_numbers(file_path: str) -> tuple[int, int, DPLLTable]:
    """
    Way to extract the required values and the clause text from the cnf file.
    Returns (variables, clauses, clause-table) for DPLL.
    """
    clause_table = []
    variables = 0
    clauses = 0

    with open(file_path) as f:
        for line in f:
            line_variables = line.split()
            if line.startswith("c") or line.startswith("%") or line.startswith("0") or line.startswith("\n"):
                continue
            # Is this the p cnf line?
            elif line.startswith("p"):
                # Get the number of variables
                variables = int(line_variables[2])
                # Get the number of clauses
                clauses = int(line_variables[3])
            else:
                # Clauses end with 0s, remove them
                clause_table.append(list(map(int, line_variables[:-1])))

    return (variables, clauses, clause_table)


def convert_to_dpll(clausetable: CDCLTable | CDCLClause) -> DPLLTable | DPLLClause:
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

    clausecopy = copy.deepcopy(clausetable)
    clauses_to_remove = []

    # Is this a CDCL Table?
    if isinstance(clausetable[0], list):
        # Just grab the first part with the variables.
        clausetable = clausetable.clauses
        clausecopy = copy.deepcopy(clausetable)

        for i, clause in enumerate(clausetable):
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
                elif variable_value is False:
                    variable_sets_to_remove.append(variable_set)
                else:
                    variable_sets_to_remove.append(variable_set)
                    variable_names_to_add.append(variable_name)
            if not found_true:
                for sets in variable_sets_to_remove:
                    clausecopy[i].remove(sets)
                clausecopy[i] += variable_names_to_add

    # Is this a CDCL Clause?
    elif isinstance(clausetable[0], tuple):
        for variable_set in clausetable:
            variable_name, variable_value = variable_set
            if variable_value is True:
                return []
            elif variable_value is False:
                clauses_to_remove.append(variable_set)
            else:
                clauses_to_remove.append(variable_set)
                clausecopy.append(variable_name)

    for elements in clauses_to_remove:
        clausecopy.remove(elements)

    return clausecopy


def convert_to_cdcl(clausetable: DPLLTable | DPLLClause) -> CDCLTable | CDCLClause:
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
    if isinstance(clausetable[0], list):                            # Is this a DPLL Table?
        clausecopy = []
        clauses = 0
        for clause in clausetable:
            new_clause = list(map(lambda x: (x, None), clause))
            clausecopy.append(new_clause)
            clauses += 1
        clause_values = [None] * clauses
        return CDCLTable(clausecopy, clause_values)

    # Is this a DPLL Clause?
    elif isinstance(clausetable[0], int):
        new_clause = list(map(lambda x: (x, None), clausetable))
        return new_clause


def pretty_print(clausetable: DPLLTable | CDCLTable | bool) -> None:
    """
    Convenience function to pretty-list an array of clauses.
    """
    if isinstance(clausetable[0][0], list):                         # Is this a CDCL Table?
        clausetable = clausetable.clauses

    # Is this a table?
    if isinstance(clausetable[0], list):
        for clause in clausetable:
            print(clause)
    else:                                                           # Is this a boolean?
        print(clausetable)
