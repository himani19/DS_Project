# DS_Project
Distributed Project on Global State Deadlock Detection
# Dependencies
python3<br>
Mpi4py

# To run code
mpiexec -n (number of processes) python3 kshem-singhal.py (name of input file)

# Assumptions
Each node is considered as process<br>
Input file format:<br>
Number of nodes<br>
Initiator Id<br>
u v where (u,v) are vertices of edges in graph and edge is directed from u to v.

