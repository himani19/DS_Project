import time
import sys
# !pip install mpi4py
from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

import datetime
from collections import defaultdict

def addEdge(graph,u,v): 
      graph[u].append(v)


""" 
This function is used read the input from txt file and 
store incoming and outgoing edges of a node in their local storage.
Each node knows only about it's own dependencies and who it is dependent on.
"""


def setGraph(processId):
  file = open(sys.argv[1],"r")
  lines = file.readlines()
  numberOfNodes = int(lines[0])
  initiator = int(lines[1])
  lines = lines[2:]

    
  # function for adding edge to graph 
  inEdges = defaultdict(list) 
  outEdges = defaultdict(list) 

  for i in lines:
    [u,v] = i.split(" ")
    u = int(u)
    v = int(v)
    addEdge(outEdges,u,v)
    addEdge(inEdges,v,u)

  myId=processId
  myIncomingEdges=[]
  myOutgoingEdges=[]
  if processId in inEdges:
    myIncomingEdges=inEdges[processId]
  if processId in outEdges:
    myOutgoingEdges=outEdges[processId]
  return numberOfNodes,initiator,myOutgoingEdges,myIncomingEdges

n,initiator,myOutgoingEdges,myIncomingEdges=setGraph(rank) #n corresponds to the number of nodes in the graph

class Node:
  def __init__(self, id):
    self.id = id
    self.outset = set()
    self.inset = set()
    date_time_str = '2001-01-01 00:00:00.243860'
    self.time = datetime.datetime.strptime(
            date_time_str, '%Y-%m-%d %H:%M:%S.%f')  #Sets some past time for each node
    self.p_requests=0
    # self.blocked=False
    self.initiator = False
    self.weight=0
    self.init_id=0


  # Initiates the snapshot
  def setInitiator(self):
    self.initiator=True
    self.time= datetime.datetime.now()
    self.p_requests=len(myOutgoingEdges)
    self.outset=myOutgoingEdges
    # self.blocked=True
    w=float(1/len(self.outset))
    data={'source':rank,'init':rank,'t_init':self.time,'weight':w,'type':'FLOOD'}
    for neigh in self.outset:
      comm.send(data,neigh)


  """
  Executed by process i(which is always init) on receiving a SHORT
  msg for which t_init= t_block. 
  SHORT for an outdated snapshot (t_init<t_block) is discarded.
  """
  def receiveShort(self,source,init,t_init,weight):
    if t_init<self.time:
      return
    if t_init== self.time:
      if self.p_requests==0:
        return
      elif self.p_requests>0:
        self.weight+=weight
        if init==rank:
          if self.weight==1: # declare deadlock and abort
            print('\033[1m'+'\033[91m'+"Deadlock detected"+'\033[0m')
            data={'source':rank,'init':init,'t_init':self.time,'weight':1,'type':'TERMINATE'}
            for node in range(n):
              comm.send(data,node)
            sys.exit('Terminated')
    

  """
  Executed by process i on receiving an ECHO msg from process
  source for a current snapshot for which LS[init].t of process i
  is equal t_init. 
  ECHO for an outdated snapshot(LS[int]>t_init) is discarded
  """
  def receiveEcho(self,source,init,t_init,weight):
    if(self.time>t_init):
      return
    elif self.time == t_init:
      if source in self.outset:
        self.outset.remove(source)
      if self.p_requests==0:        # For current snapshot, it is already reduced.Hence send SHORT msg to initiator
        data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'SHORT'}
        comm.send(data,init)
      elif self.p_requests>0:       #For current snapshot, process is blocked
        self.p_requests-=1
        if self.p_requests==0:      #Process is reduced 
          if init==rank:            #if process is inititor,that implies no deadlock.
            # print("No deadlock")
            data={'source':rank,'init':init,'t_init':self.time,'weight':1,'type':'TERMINATE'}
            for node in range(n):
              comm.send(data,node)
            print('\033[1m'+'\033[91m'+"No deadlock"+'\033[0m')
            sys.exit('')
          weight1=float(weight/len(self.inset))
          data={'source':rank,      #Non init process sends an ECHO to edges in inset indicating it is reduced.
                'init':init,
                't_init':t_init,
                'weight':weight1,
                'type':'ECHO'}
          for k in self.inset:
            # print("neigh:",k)
            comm.send(data,k)
        else:                       #Process remains blocked
          data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'SHORT'}
          comm.send(data,init)

    else:
      return


  """
  Executed by process i on receiving a FLOOD msg from source
  """  
  def receiveFlood(self,source,init,t_init,weight):
    if(self.time>t_init):     #Outdated flood msg. Discard the msg
      return
    

    elif self.time< t_init:   #Valid FLOOD for a new snapshot.
      if source in myIncomingEdges:
        self.outset=myOutgoingEdges
        self.inset={source}
        self.time=t_init
        self.p_requests=len(myOutgoingEdges)
        try:

          w=weight/len(myOutgoingEdges)
        except:
          pass
        if self.p_requests>0:     #Process is blocked.Forwards the FLOOD msg to processed in outset
          data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':w,
                'type':'FLOOD'}
          for neigh in myOutgoingEdges:
               # print("neigh:",neigh)
               comm.send(data,neigh)
        elif self.p_requests==0:   #Process is unblocked.Replies with an ECHO msg.
          data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'ECHO'}
          comm.send(data,source)
          # self.outset=[]
            # self.inset.remove(source)

      else:           #New snapshot but the FLOOD msg came across the edge which is not in process' inset
        data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'ECHO'}
        comm.send(data,source)

    elif self.time==t_init:     #Valid FLOOD for current snapshot
      if source not in myIncomingEdges: #The FLOOD msg came across the edge which is not in process' inset
        data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'ECHO'}
        comm.send(data,source)    
      else:
        self.inset.add(source)
        if self.p_requests==0:      #Process is reduced
           data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'ECHO'}
           comm.send(data,source)
        elif self.p_requests>0:     #Process is blocked
          data={'source':rank,
                'init':init,
                't_init':t_init,
                'weight':weight,
                'type':'SHORT'}
          comm.send(data,init)      
    

LS={}
for i in range(n):
  LS[i] = Node(i)

if rank==initiator:
	LS[initiator].setInitiator()
 
while(True):
  if rank==initiator:
    if LS[initiator].weight==1:
      data={'source':rank,'init':rank,'t_init':LS[init].time,'weight':1,'type':"TERMINATE"}
      for node in range(n):
        comm.send(data,node)
      sys.exit('Terminated')

 
  msg_recv=comm.recv(source=MPI.ANY_SOURCE)     #Process waits for msgs
  source=msg_recv['source']
  print("Node:",rank," recieved ",msg_recv['type'], " from:",source)
  init=msg_recv['init']
  t_init=msg_recv['t_init']
  weight=msg_recv['weight']
  if(msg_recv['type']=="FLOOD"):
    LS[init].receiveFlood(source,init,t_init,weight)

  if(msg_recv['type']=="ECHO"):
    LS[init].receiveEcho(source,init,t_init,weight)
  if(msg_recv['type']=="SHORT"):
    LS[init].receiveShort(source,init,t_init,weight)
  if(msg_recv['type']=="TERMINATE"):
    sys.exit("Terminated")
