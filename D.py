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



if __name__ == "__main__":

    # Test 1
    N = 10
    V = range(1, N+1)
    A = []
    for v in range(1, N):
        A.append((v, v+1))
        A.append((v+1, v))
    I = [1,N]
    Lambda = 2
    print "Test 1"
    X_opt, a_opt, opt = Defend(V, A, I, Lambda)
    print "X = " + str(X_opt)
    print "a = " + str({v: int(a_opt[v]) for v in V})
    print "value = " + str(opt)

    # Test 2
    V = range(1,11)
    A = [(1,2),(2,1),(2,3),(3,2),(3,4),(4,3),(3,5),(5,3),
        (2,6),(6,2),(6,7),(7,6),(7,8),(8,7),(6,9),(9,6),(7,10),(10,7)]
    I = [7,2]
    Lambda = 2
    print "Test 2"
    X_opt, a_opt, opt = Defend(V, A, I, Lambda)
    print "X = " + str(X_opt)
    print "a = " + str({v: int(a_opt[v]) for v in V})
    print "value = " + str(opt)

    # Test 3
    V = [7, 1, 9, 4, 2, 8]
    A = [(1,2),(2,1),(4,1),(1,4),(1,7),
        (7,1),(7,8),(8,7),(8,9),(9,8)]
    I = [7]
    Lambda = 1
    print "Test 3"
    X_opt, a_opt, opt = Defend(V, A, I, Lambda)
    print "X = " + str(X_opt)
    print "a = " + str({v: int(a_opt[v]) for v in V})
    print "value = " + str(opt)
