################################################################################
#######################   Defend-Attack-Defend Solver    #######################
################################################################################

import timeit
import os
import cplex

from AD_MIX import Attack_Defend as Attack_Defend_MIX
from AD import Attack_Defend

DAD_STATS_IND = ("fail", "totTm", "lastADTm", "itDAD", "avItADGoal", "itADOpt")

# INPUT
# V - set of nodes (list of integers)
# A - set of arcs  (list of tuples: [...,(i,j),(j,i),...], i,j in V)
# Omega - budget for vaccination (integer)
# Phi - budget for attack (integer)
# Lambda - budget for defence (integer)
# if mix = False then use MCN_MIX++
# if mix = True then use HIB
#Aif mix = True, AD_it_limit controls the number of iterations before using MIX++

# OUTPUT
# - vaccination (subset of V)
# - attack (subset of V)
# - defense (subset of V)
# - indicator vector for survived nodes (dictionary over V)
# - number of survived nodes (integer)
# - status of solution (integer)
#      1 -> optimal
#      2 -> no guarantee for attacker's optimality
#      3 -> iteration limit reached
# - statistics for the computation (dictionary)
#      fail :
#      totTm :
#      lastADTm :
#      itDAD :
#      avItADGoal :
#      itADOpt :

def Defend_Attack_Defend(V, A, Omega, Phi, Lambda, fileWr = None, mix = False, AD_it_limit = 10):

    def vprint(arg):
        if fileWr is not None:
            fileWr.write(arg +"\n")
            fileWr.flush()
            os.fsync(fileWr.fileno())
        return

    vprint("V = " + str(V))
    vprint("A = " + str(A))

    stats = {ind : "X" for ind in DAD_STATS_IND}

    totItADGoal = 0
    startTotTm = timeit.default_timer()

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

    # global variables
    Delta_name = "Delta"
    z_names = {v: "z_%d"%v for v in V}
    model.variables.add(obj = [1],
                        types = [model.variables.type.continuous],
                        names = [Delta_name])
    for v in V:
        model.variables.add(obj = [0],
                            types = [model.variables.type.binary],
                            names = [z_names[v]])

    # budget constraints
    model.linear_constraints.add(
        lin_expr = [cplex.SparsePair(ind = z_names.values(),
                                     val = [1]*len(V))],
        senses = ["L"],
        rhs = [Omega])

    # add new scenarios in U and update the model with
    #  correpsonding variables and constraints
    value_best = len(V)
    Z = []
    a_names = [] # list of dictionaries over V
    x_names = [] #
    U = []
    status = 0
    cnt = 0
    while True:
        vprint("\nIteration -> " + str(cnt) + ":")
        # solve optimal Attack-Defend on V\Z
        V_red = [v for v in V if v not in Z]
        A_red = [arc for arc in A if (arc[0] not in Z) and (arc[1] not in Z)]
        try:
            vprint("Solving Attack-Defend for Z = " + str(Z))
            if mix:
                vprint("Attack-Defend by Baggio et al")
                Y_opt, X_opt, a_opt, opt, AD_status, AD_stats = Attack_Defend(V_red, A_red, Phi, Lambda, fileWr, value_best-len(Z)-1, AD_it_limit)
                if AD_status == 3: # iteration limit for AD reached
                    vprint("Iteration limit reached -> use Fischetti et al")
                    Y_opt, X_opt, a_opt, opt, AD_status, AD_stats = Attack_Defend_MIX(V_red, A_red, Phi, Lambda, fileWr, value_best-len(Z)-1,'HPR-'+str(len(V))+str(mix))
            else:
                Y_opt, X_opt, a_opt, opt, AD_status, AD_stats = Attack_Defend_MIX(V_red, A_red, Phi, Lambda, fileWr, value_best-len(Z)-1, 'HPR-'+str(len(V))+str(mix))
        except:
            raise Exception
        opt = opt + len(Z)
	if (AD_status == 2): #### goal was reached
            totItADGoal = totItADGoal + int(AD_stats["totIt"])
            vprint("CLB-> %d   vs   UB -> %d" %(opt, value_best))
        else:
            a_opt = {v : a_opt[v] if v in V_red else 1.0 for v in V}
            if AD_status == 1:
                vprint("\n\nOptimal solution has value %d:"%value_best)
                status = 1
                stats["fail"] = "no"
            elif AD_status == 3:
            # if AD_status == 3 no further improvements for DAD are possible
                vprint("\n\nSolution cannot be guaranteed to be optimal " +
                      "for the attacker")
                vprint("Solution has value %d:"%value_best)
                status = 2
                stats["fail"] = "itADLmt"
            stats["totTm"] = "%.3f"%(timeit.default_timer() - startTotTm)
            stats["lastADTm"] = AD_stats["totTm"]
            stats["itDAD"] = str(cnt+1)
            stats["avItADGoal"] = "%.3f"%(float(totItADGoal)/cnt)
            stats["itADOpt"] = AD_stats["totIt"]
            vprint("Z = "+str(Z) + ", Y = "+str(Y_opt) + ", X = "+str(X_opt))
            vprint("Saved nodes = " + str([v for v in V if a_opt[v] > 0.9]))
            vprint("Dead nodes = "+str([v for v in V if a_opt[v] < 0.1])+"\n")
            return Z, Y_opt, X_opt, a_opt, opt, status, stats

	# create scenario for Y_opt
        U.append(Y_opt) # at the moment useless
        # variables corresponding to Y_opt
        a_names.append({v: "a(%d)_%d"%(cnt,v) for v in V})
        x_names.append({v: "x(%d)_%d"%(cnt,v) for v in V})
        for v in V:
            model.variables.add(obj = [0],
				types = [model.variables.type.binary],
                                names = [a_names[cnt][v]])
            model.variables.add(obj = [0],
                                types = [model.variables.type.binary],
                                names = [x_names[cnt][v]])
        # constraints corresponding to Y_opt
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(ind = x_names[cnt].values(),
                                         val = [1]*len(V))],
            senses = ["L"],
            rhs = [Lambda])
        for v in V:
            model.linear_constraints.add(
                lin_expr = [cplex.SparsePair(
                    ind = [a_names[cnt][v], z_names[v]],
                    val = [1.0, -1.0])],
                senses = ["L"],
                rhs = [0.0 if v in Y_opt else 1.0])
        for arc in A:
            model.linear_constraints.add(
                lin_expr = [cplex.SparsePair(
                    ind = [a_names[cnt][arc[1]], x_names[cnt][arc[1]],
                           a_names[cnt][arc[0]], z_names[arc[1]]],
                    val = [1.0, -1.0, -1.0, -1.0])],
                senses = ["L"],
                rhs = [0.0])
        model.linear_constraints.add(
            lin_expr = [cplex.SparsePair(
                ind = [Delta_name] + a_names[cnt].values(),
                val = [1.0] + [-1.0]*len(V))],
            senses = ["L"],
            rhs = [0.0])

	#Solve the model
        vprint("Solving up to date DAD model")
        model.solve()
        sol = model.solution
        if sol.get_status() in [101, 102]:
            value_best = int(round(sol.get_objective_value()))
            Z = [v for v in V if sol.get_values(z_names[v]) > 0.9]
        else:
            vprint("Problem has occurred in Defend-Attack-Defend!")
            vprint("Solution has status code: " + str(sol.get_status()))
            raise Exception
        cnt = cnt + 1
    # END while

