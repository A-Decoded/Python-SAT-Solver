import copy

from Types import CDCLTable, DPLLTable, DPLLClause, CDCLClause


def extractNumbers(filepath: str) -> tuple[int, int, DPLLTable]:
    """
    Way to extract the required values and the clause text from the cnf file.
    Returns (variables, clauses, clause-table) for DPLL.
    """
    clausetable = []
    variables = 0
    clauses = 0

    with open(filepath) as f:
        for line in f:
            line_variables = line.split()
            if line.startswith("c") or line.startswith("%") or line.startswith("0") or line.startswith("\n"):
                continue
            elif line.startswith("p"):                                  # Is this the p cnf line?
                variables = int(line_variables[2])                      # Get the number of variables
                clauses = int(line_variables[3])                        # Get the number of clauses
            else:
                # Clauses end with 0s, remove them
                clausetable.append(list(map(int, line_variables[:-1]))) 

    return (variables, clauses, clausetable)


def convertToDPLL(clausetable: CDCLTable | CDCLClause) -> DPLLTable | DPLLClause:
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
    clausesToRemove = []

    if isinstance(clausetable[0], list):                                 # Is this a CDCL Table?
        clausetable = clausetable.clauses                                # Just grab the first part with the variables.
        clausecopy = copy.deepcopy(clausetable)

        for i, clause in enumerate(clausetable):
            variableSetsToRemove = []
            variableNamesToAdd = []
            foundTrue = False
            for variable_set in clause:
                variable_name, variable_value = variable_set
                if variable_value is True:                          # Does this clause evaluate to True? 
                    clausesToRemove.append(clause)
                    foundTrue = True                                # Safety flag to avoid manipulating clauses which turn out to be True
                    break
                elif variable_value is False:                     
                    variableSetsToRemove.append(variable_set)
                else:
                    variableSetsToRemove.append(variable_set)
                    variableNamesToAdd.append(variable_name)
            if not foundTrue:                               
                for sets in variableSetsToRemove:
                    clausecopy[i].remove(sets)
                clausecopy[i] += variableNamesToAdd
        
    elif isinstance(clausetable[0], tuple):                         # Is this a CDCL Clause?
        for variable_set in clausetable:
            variable_name, variable_value = variable_set
            if variable_value is True:
                return []
            elif variable_value is False:
                clausesToRemove.append(variable_set)
            else:
                clausesToRemove.append(variable_set)
                clausecopy.append(variable_name)
    
    for elements in clausesToRemove:
        clausecopy.remove(elements)

    return clausecopy

def convertToCDCL(clausetable: DPLLTable | DPLLClause) -> CDCLTable | CDCLClause:
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
            newclause = list(map(lambda x: (x, None), clause))
            clausecopy.append(newclause)
            clauses += 1
        clausevalues = [None] * clauses
        return CDCLTable(clausecopy, clausevalues)

    elif isinstance(clausetable[0], int):                           # Is this a DPLL Clause?
        newclause = list(map(lambda x: (x, None), clausetable))
        return newclause


def prettyPrint(clausetable: DPLLTable | CDCLTable | bool) -> None:
    """
    Convenience function to pretty-list an array of clauses.
    """
    if isinstance(clausetable[0][0], list):                         # Is this a CDCL Table?
        clausetable = clausetable.clauses

    if isinstance(clausetable[0], list):                            # Is this a table?
        for clause in clausetable:
            print(clause)
    else:                                                           # Is this a boolean?
        print(clausetable)
