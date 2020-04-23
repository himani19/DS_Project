# DS_Project
Distributed Project on Global State Deadlock Detection
# Dependencies
python3
Mpi4py

# To run code 
1.Kshemkalyani-singhal<br>
mpiexec -n (number of processes) python3 kshem-singhal.py (name of input file)<br>
2.Bracha-Toueg<br>
mpiexec -n (number of processes) python bracha-toueg-mpi.py (name of input file)<br>


# Assumptions
Each node is considered as process<br>
Input file format:<br>
Number of nodes<br>
Initiator Id<br>
u v where (u,v) are vertices of edges in graph and edge is directed from u to v.<br>

# Input File
1.Kshemkalyani-singhal<br>
test.txt and test2.txt are two input files given indexing of nodes starting from 0.<br>
2.Bracha-Toueg<br>
input.txt is the input file given indexing of nodes starting from 1.

