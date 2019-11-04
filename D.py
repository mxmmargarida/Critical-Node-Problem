################################################################################
#############################     Defend Solver    #############################
################################################################################

import cplex

# INPUT
# V - set of nodes (list of integers)
# A - set of arcs  (list of tuples: [...,(i,j),(j,i),...], i,j in V)
# I - attacked nodes (subset of V)
# Lambda - budget for defense (integer)

# OUTPUT
# - optimal defense (subset of V)
# - indicator vector for survived nodes (dictionary over V)
# - number of survived nodes (integer)

def Defend(V,A,I,Lambda):

    # initiate the model
    model = cplex.Cplex()
    # output stream setup
    model.set_log_stream(None)
    model.set_error_stream(None)
    model.set_warning_stream(None)
    model.set_results_stream(None)
    model.parameters.threads.set(1)
    # set objective direction
    model.objective.set_sense(model.objective.sense.maximize)

    # variables
    a_names = {v: "a_%d"%v for v in V}
    x_names = {v: "x_%d"%v for v in V}
    for v in V:
        model.variables.add(obj = [1],
                            types = [model.variables.type.continuous],
                            names = [a_names[v]])
    for v in V:
        model.variables.add(obj = [0],
                            types = [model.variables.type.binary],
                            names = [x_names[v]])

    # constraints
    model.linear_constraints.add(
        lin_expr = [cplex.SparsePair(ind = x_names.values(),
                                     val = [1]*len(V))],
        senses = ["L"],
        rhs = [Lambda])
    for v in V:
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(ind = [a_names[v]],
                                         val = [1.0])],
            senses = ["L"],
            rhs = [0.0 if v in I else 1.0])
    for arc in A:
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [a_names[arc[1]], x_names[arc[1]], a_names[arc[0]]],
                val = [1.0, -1.0, -1.0])],
            senses = ["L"],
            rhs = [0.0])

    # solve the model and return an optimal solution
    model.solve()
    sol = model.solution
    if sol.get_status() in [101, 102]:
        #if sol.get_status() != 101:
        #    print "Solution in Defend has status code: "+str(sol.get_status())
        X_opt = [v for v in V if sol.get_values(x_names[v]) > 0.9]
        a_opt = {v: round(sol.get_values(a_names[v])) for v in V}
        #TODO: handle tolerance (102 status) and check the solution
        return X_opt, a_opt, int(round(sol.get_objective_value()))
    else:
        print "Problem has occurred in Defend!"
        print "Solution has status code: " + str(sol.get_status())
	raise Exception



