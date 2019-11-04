################################################################################
##########################    Attack-Defend Solver    ##########################
################################################################################

import timeit
import cplex
import os


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
#      1 -> optimal and cannot reach goal
#      2 -> satisfying goal
#      3 -> time limit reached
# - statistics (dictionary)
#      totTm :
#      totIt :

def Attack_Defend(V, A, Phi, Lambda, fileWR=None, goal = 0,name_hpr='HPR'):
    def vprint(arg):
        # if fileWr is not None:
        #     fileWr.write(arg +"\n")
        #     fileWr.flush()
        #     os.fsync(fileWr.fileno())
        return
    # create mps file: the high-point relaxation (HPR) of the problem
    model = cplex.Cplex()
    # output stream setup
    model.set_log_stream(None)
    model.set_error_stream(None)
    model.set_warning_stream(None)
    model.set_results_stream(None)
    # set objective direction
    model.objective.set_sense(model.objective.sense.minimize)

    # variables
    a_names = {v: "a_%d"%v for v in V}
    y_names = {v: "y_%d"%v for v in V}
    x_names = {v: "x_%d"%v for v in V}
    size_V = len(V)
    size_A = len(A)
    model.variables.add(obj = [1]*size_V,
                        types = [model.variables.type.binary]*size_V,
                        names = a_names.values())
    model.variables.add(obj = [0]*size_V,
                        types = [model.variables.type.binary]*size_V,
                        names = y_names.values())
    model.variables.add(obj = [0]*size_V,
                        types = [model.variables.type.binary]*size_V,
                        names = x_names.values())
    # Attacker budget constraint
    model.linear_constraints.add(
        lin_expr = [cplex.SparsePair(ind = y_names.values(),val = [1]*len(V))],
        senses = ["L"],rhs = [Phi],names = ["Phi"])
    # Follower constraints
    model.linear_constraints.add(
        lin_expr = [cplex.SparsePair(ind = x_names.values(),val = [1]*len(V))],
        senses = ["L"],rhs = [Lambda],names = ["Lambda"])
    # constraints for attacked nodes
    for v in V:
        model.linear_constraints.add(lin_expr =
        [cplex.SparsePair(ind = [a_names[v],y_names[v]],val=[1.0,1.0])],
        senses = ["L"], rhs = [1.0],names = ["V%d"%v])
    for arc in A:
        model.linear_constraints.add(lin_expr =
        [cplex.SparsePair(ind = [a_names[arc[1]],a_names[arc[0]],x_names[arc[1]]],val=[1.0,-1.0,-1.0])],
        senses = ["L"], rhs = [0.0],names = ["A%d-%d"%arc])
    model.write(name_hpr+'.mps','mps')

    # create follower auxfile
    f_auxfile = open(name_hpr+'.aux','w')
    # number of follower variables
    f_auxfile.write("N "+str(size_V*2)+"\n")
    # number of follower constraints
    f_auxfile.write("M "+str(1+size_V+size_A)+"\n")
    # index in the mpsfile of follower variables
    # a variables
    # x variables
    f_auxfile.write("\n".join(["LC %d"%i for i in range(size_V)]+["LC %d"%i for i in range(2*size_V,3*size_V)])+"\n")
    # index in the MPS file of follower constraint
    for i in range(1,size_V+size_A+1+1):
        f_auxfile.write("LR "+str(i)+"\n")
    # follower objective of follower variable (order as given by LC)
    f_auxfile.write("\n".join(["LO 1.000000" for _ in xrange(size_V)]+["LO 0.000000" for _ in xrange(size_V)])+"\n")
    # objective sense of the follower, 1: min, -1: max
    f_auxfile.write("OS -1")
    f_auxfile.close()

    # run Matteo Fischetti, Ivana Ljubic, Michele Monaci and Markus Sinnl's Algorithm
    os.system("./bilevel -mpsfile " + name_hpr+'.mps' +" -time_limit 7200 -num_threads 1 > "+ name_hpr+"_output.txt")
    stats = {ind : "0" for ind in AD_STATS_IND}
    a_best = {v:0 for v in V}
    Y_best = []
    X_best = []
    sol_search = False
    with open(name_hpr+'_output.txt') as searchfile:
        for line in searchfile:
            if "STAT;" in line:
                value_best,_,_,stats["totTm"],_,status = map(float,line.split(";")[2:8])
                stats["totTm"]="%.3f"%stats["totTm"]
            elif "LEADER COST" in line:
                sol_search = True
            elif sol_search:
                if "a_" in line:
                    aux = line.split()[0]
                    aux = aux.split("_")[1]
                    a_best[int(aux)] = 1.0
                elif "x_" in line:
                    aux = line.split()[0]
                    aux = aux.split("_")[1]
                    X_best.append(int(aux))
                elif "y_" in line:
                    aux = line.split()[0]
                    aux = aux.split("_")[1]
                    Y_best.append(int(aux))
    if value_best <= goal:
        vprint("Attack-Defend reached goal")
        status = 2
    else:
        if status == 0: # no optimality guarantee
            status = 3
            vprint("Attack-Defend reached time limit and goal was not achieved")
    return Y_best, X_best, a_best, value_best, int(status), stats





if __name__ == "__main__":

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
