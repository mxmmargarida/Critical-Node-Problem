from tools import graph
from tools import tree
import random
import itertools

import os
import os.path

PATH = "Instances/"

def test_tree(number, N, Omega, Phi, Lambda):
    name = "%s-%d_%d-%d-%d_%0*d"%("tree", N, Omega, Phi, Lambda, 3, number)
    if os.path.isfile("tables/"+name.rsplit('_',1)[0]+"/"+name):
        V = range(1, N + 1)
        with open("tables/"+name.rsplit('_',1)[0]+"/"+name) as searchfile:
            for line in searchfile:
                if "A =" in line:
                    A = eval(line[4:])
    else:
        V, A = tree(N)
    test(V, A, Omega, Phi, Lambda, name)
    return

def test_rndgraph(number, N, density, Omega, Phi, Lambda):
    density = int(density)
    if (density < 0) or (density > 100):
        print "density not valid!"
        raise Exception
    name = "%s%0*d-%d_%d-%d-%d_%0*d"%("rndgraph", 2, density, N, Omega, Phi, Lambda, 3, number)
    if os.path.isfile("tables/"+name.rsplit('_',1)[0]+"/"+name):
        V = range(1, N + 1)
        with open("tables/"+name.rsplit('_',1)[0]+"/"+name) as searchfile:
            for line in searchfile:
                if "A =" in line:
                    A = eval(line[4:])
    else:
        V, A, = graph(N, int(float(density)/100 * N*(N-1)/2))
    test(V, A, Omega, Phi, Lambda, name)
    return

def test(V, A, Omega, Phi, Lambda, name):
    folder =  PATH + name.rsplit('_', 1)[0] + "/"
    os.system("mkdir -p " + folder)
    if not os.path.isfile("tables/"+name.rsplit('_',1)[0]+"/"+name):
        f_instance = open("tables/"+name.rsplit('_',1)[0]+"/"+name, 'w')
        f_instance.write("V = " + str(V) + "\n")
        f_instance.write("A = " + str(A) + "\n")
        f_instance.close()
    return



if __name__ == "__main__":

    NUM=20
    mode = "runExp"         # "wrStat" or "runExp"
    graphtype = "rndgraph"  # in ("tree", "rndgraph")
    N = 40
    budgSet = [[1,1,1],[3,1,3],[2,2,2],[3,3,1],[1,3,3],[3,3,3]]
    module = "from Generate_Instances import *"

    for budgets in budgSet:
        for density in range(6,16):
            Omega = budgets[0]
            Phi = budgets[1]
            Lambda = budgets[2]
            if mode in ["runExp"]:
                for cnt in range(1, NUM + 1):
                    if graphtype == "tree":
                        test = "test_tree(%d, %d, %d, %d, %d)"%(cnt, N, Omega, Phi, Lambda)
                    elif graphtype == "rndgraph":
                        test = "test_rndgraph(%d, %d, %d, %d, %d, %d)"%(cnt, N, density, Omega, Phi, Lambda)
                    else:
                        raise Exception
                    runTest = "python -c '%s; %s'"%(module, test)
                    # following command runs only in unix; it restricts the server to one threat and time limit of 2 hours
                    runSub = " OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 timeout 2h %s"%(runTest)
                    os.system(runSub)
                    print 'Finnished to run '+graphtype+" cnt=%d, N=%d, Omega=%d, Phi=%d, Lambda=%d"%(cnt, N, Omega, Phi, Lambda)

    import smtplib
    from email.mime.text import MIMEText
    msg = MIMEText("Your computation is finished")
    msg['Subject'] = 'Results are out for type='+graphtype+" V="+str(N)+" budget = "+str(budgets)
    me = 'server@super.chair.ca' # fixed email
    msg['From'] = me
    msg['To'] = "someone@domain.xyz" # replace by your email
    s = smtplib.SMTP('localhost')
    s.sendmail(me, ["someone@domain.xyz"], msg.as_string())
    s.quit()
