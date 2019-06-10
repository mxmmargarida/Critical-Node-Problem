################################################################################
##########################    Attack-Defend Solver    ##########################
################################################################################

import timeit
import cplex


from D import Defend



AD_STATS_IND = ("totTm", "totIt")

# INPUT
# V - set of nodes (list of integers)
# A - set of arcs  (list of tuples: [...,(i,j),(j,i),...], i,j in V)
# Phi - budget for attack (integer)
# Lambda - budget for defense (integer)
# goal [default = 0] - objective value for early stopping condition (integer)

# OUTPUT
# - attack (subset of V)
# - defense (subset of V)
# - indicator vector for survived nodes (dictionary over V)
# - number of survived nodes (integer)
# - status of solution
#      1 -> optimal
#      2 -> satisfying goal
#      3 -> iteration limit reached
# - statistics (dictionary)
#      totTm :
#      totIt :


def Attack_Defend(V, A, Phi, Lambda, fileWR=None, goal = 0, it_limit = 5000):

    def vprint(arg):
#        if fileWR is not None:
#            fileWR.write(arg + "\n")
#            fileWR.flush()
#            os.fsync(fileWR.fileno())
        return

    stats = {ind : "X" for ind in AD_STATS_IND}
    startTotTm = timeit.default_timer()

    # noGood = []
    # defenses = []

    # initiate the model
    model = cplex.Cplex()
    # output stream setup
    model.set_log_stream(None)
    model.set_error_stream(None)
    model.set_warning_stream(None)
    model.set_results_stream(None)
    model.parameters.threads.set(1)
    # set objective direction
    model.objective.set_sense(model.objective.sense.minimize)

    # variables
    y_names = {v: "y_%d"%v for v in V}
    p_name = "p"
    h_names = {v: "h_%d"%v for v in V}
    q_names = {arc: "q_%d-%d"%(arc[0],arc[1]) for arc in A}
    u_names = {v: "u_%d"%v for v in V}

    model.variables.add(obj = [Lambda],
                        types = [model.variables.type.continuous],
                        names = [p_name])
    for v in V:
        model.variables.add(obj = [0],
                            types = [model.variables.type.binary],
                            names = [y_names[v]])
        model.variables.add(obj = [0],
                            types = [model.variables.type.continuous],
                            names = [h_names[v]])
        model.variables.add(obj = [1],
                            types = [model.variables.type.continuous],
                            names = [u_names[v]])
    for arc in A:
        model.variables.add(obj = [0],
                            types = [model.variables.type.continuous],
                            names = [q_names[arc]])

    # budget constraint
    model.linear_constraints.add(
        lin_expr = [cplex.SparsePair(ind = y_names.values(),
                                     val = [1]*len(V))],
        senses = ["L"],
        rhs = [Phi])

    # dual contraints
    for v in V:
        arcs_in = [q_names[arc] for arc in A if arc[1] == v]
        arcs_out = [q_names[arc] for arc in A if arc[0] == v]
        if v==36:
            print h_names[v]
            print arcs_in
            print arcs_out
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [h_names[v]] + arcs_in + arcs_out,
                val = [1.0] + [1.0]*len(arcs_in) + [-1.0]*len(arcs_out))],
            senses = ["E"],
            rhs = [1.0])
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [p_name] + arcs_in,
                val = [1.0] + [-1.0]*len(arcs_in))],
            senses = ["G"],
            rhs = [0.0])

    # McCormick constraints: u_v = h_v*(1-y_v)
    #  note: h_v <= |V| for all v
    for v in V:
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [u_names[v], y_names[v], h_names[v]],
                val = [1.0, len(V), -1.0])],
            senses = ["G"],
            rhs = [0.0])
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [u_names[v]],
                val = [1.0])],
            senses = ["G"],
            rhs = [0.0])

    # Nonnegativity constraints
    model.linear_constraints.add(
        lin_expr = [cplex.SparsePair(ind = [p_name], val = [1.0])],
        senses = ["G"],
        rhs = [0.0])
    for v in V:
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(ind = [h_names[v]], val = [1.0])],
            senses = ["G"],
            rhs = [0.0])
    for arc in A:
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(ind = [q_names[arc]], val = [1.0])],
            senses = ["G"],
            rhs = [0.0])

    # solve the model and add cuts until necessary
    Y_best = []
    X_best = []
    a_best = {}
    value_best = len(V)
    status = 0
    cnt = 1

    while True:
        vprint("Iteration -> " + str(cnt) + ": " + str(value_best))
        model.solve()
        sol = model.solution
        if sol.get_status() in [101, 102]: # optimal solution reached
            #if sol.get_status() != 101:
            #    print ("Solution in Attack-Defend has status code: " +
            #            str(sol.get_status()))
            I = [v for v in V if sol.get_values(y_names[v]) > 0.9]
            #TODO: handle tolerance (102 status) and check the solution
            try:
                X_opt, a_opt, value_opt = Defend(V, A, I, Lambda)
            except:
                raise Exception
            if value_opt < value_best:
                Y_best = I
                X_best = X_opt
                a_best = a_opt
                value_best = value_opt
            if value_opt <= goal:
               vprint("Attack-Defend reached goal in %d iterations"%(cnt))
               status = 2
               break
        elif sol.get_status() == 103: # infeasible model
            vprint("Attack-Defend reached optimality in %d iterations"%(cnt))
            status = 1
            break
        else:
            print "Problem has occurred in Attack-Defend!"
            print "Solution has status code: " + str(sol.get_status())
            raise Exception
        if cnt >= it_limit:
            vprint("Attack-Defend reached iteration limit %d"%it_limit)
            status = 3
            break
        # add defender's nogood constraint
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [y_names[v] for v in V],
                val = [a_opt[v] for v in V])],
            senses = ["G"],
            rhs = [1.0])
        cnt = cnt + 1
    # END while

    stats["totTm"] = "%.3f"%(timeit.default_timer() - startTotTm)
    stats["totIt"] = str(cnt)
    return Y_best, X_best, a_best, value_best, status, stats

#if __name__ == "__main__":

    # Test 1
    # N = 20
    # V = range(1, N+1)
    # A = []
    # for v in range(1, N):
    #     A.append((v, v+1))
    #     A.append((v+1, v))
    # Phi = 3
    # Lambda = 2
    # print "Test 1"
    # Y_opt, X_opt, a_opt, opt, status, stats = Attack_Defend(V, A, Phi, Lambda, None, 10)
    # print "Y = " + str(Y_opt)
    # print "X = " + str(X_opt)
    # print "a = " + str({v: int(a_opt[v]) for v in V})
    # print "value = " + str(opt)
    # print "status = " + str(status)
    # print "stats = " + str(stats)

    # Test 2
    # N = 20
    # V = range(1, N+1)
    # A = []
    # for v in range(1, N):
    #     A.append((v, v+1))
    #     A.append((v+1, v))
    # Z = [3, 15]
    # V_red = [v for v in V if v not in Z]
    # A_red = [arc for arc in A if (arc[0] not in Z) and (arc[1] not in Z)]
    # Phi = 3
    # Lambda = 2
    # print "Test 2"
    # Y_opt, X_opt, a_opt, opt, status, stats = Attack_Defend(V_red, A_red, Phi, Lambda, None, 0)
    # print "Y = " + str(Y_opt)
    # print "X = " + str(X_opt)
    # print "a = " + str({v: int(a_opt[v]) for v in V_red})
    # print "value = " + str(opt)
    # print "status = " + str(status)
    # print "stats = " + str(stats)
