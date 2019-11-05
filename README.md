# Critical-Node-Problem
Multilevel Approaches for the Critical Node Problem

Code for the paper 

*A. Baggio, M. Carvalho, A. Lodi, A. Tramontani, "Multilevel Approaches for the Critical Node Problem", 2018.*
http://cerc-datascience.polymtl.ca/wp-content/uploads/2017/11/Technical-Report_DS4DM-2017-012.pdf

The code was developed in python 2.7. 

## Instances

In the folder Instances/, it can be found the instances used in the paper as well as extra information on the instances' solution.

There are three folders for the randomly generated instances. In all these folders the instances under the same name are equal, but the computational information might vary as they were solved with different methods (see paper). In tables_MNC.rar all instances can be found, while in the other folders some instances might not exist because the associated approach did not solved them within the imposed time limit.

Generate_Instances.py enables the generation of new instances (running this script may overwrite files in Instances/).

## Algorithms

DAD.py corresponds to the approach MCN of the paper and makes use of AD.py and D.py.

DAD_MIXi.py implements both MCN$^{MIX++}$ and HIB (there is a parameter to select one of these approaches) and makes use of AD_MIX.py and D.py.

To run AD_Fischetti.py, it is necessary to install the following bilevel solver:
https://msinnl.github.io/pages/bilevel.html

All the python scripts depend on having an instalation of CPLEX.

