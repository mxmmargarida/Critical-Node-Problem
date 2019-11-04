# Critical-Node-Problem
Multilevel Approaches for the Critical Node Problem

Code for the paper 

*A. Baggio, M. Carvalho, A. Lodi, A. Tramontani, "Multilevel Approaches for the Critical Node Problem", 2018.*
http://cerc-datascience.polymtl.ca/wp-content/uploads/2017/11/Technical-Report_DS4DM-2017-012.pdf

The code was developed in python 2.7. 

## Instances

In the folder Instances/, it can be found the instances used in the paper as well as extra information on the instances' solution.

Generate_Instances.py enables the generation of new instances (running this script may overwrite files in Instances/).

## Algorithms

DAD.py corresponds to the approach MCN of the paper and makes use of AD.py and D.py.

DAD_Fischetti.py implements both MCN$^{MIX++}$ and HIB (there is a parameter to select one of these approaches) and makes use of AD_Fischetti.py and D.py.

To run AD_Fischetti.py, it is necessary to install the following bilevel solver:
https://msinnl.github.io/pages/bilevel.html

All the python scripts depend on having an instalation of CPLEX.

