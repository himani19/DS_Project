from mpi4py import MPI
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

class Node:
	def __init__(self, id):
		self.id = id
		self.free = False
		self.notified = False
		self.requests = 0
		self.Out = []
		self.In = []
		self.initiator = False

	def addOut(self,u):
		self.Out.append(u)
		self.requests+=1

	def addIn(self,u):
		self.In.append(u)

	def initiate(self):
		self.initiator = True
		self.notify(self.id)

	def allDone(self):
		for i in self.Out:
			if i!="DONE":
				return False
		return True
	def listen(self):
		msg = comm.recv(source=MPI.ANY_SOURCE)
		self.handleMsg(msg)

	def handleMsg(self,msg):
		sender = msg[0]
		receiver = self.id

		if msg[1]=="NOTIFY":
			if self.notified==True:
				comm.send([self.id, "DONE"], dest = sender-1)
				return
			if self.notified==False:
				self.notify(self.id)
			while self.allDone()==False:
				msg = comm.recv()
				self.handleMsg(msg)
			comm.send([receiver, "DONE"], dest = sender-1)
		
		if msg[1]=="GRANT":
			if self.requests>0:
				self.requests-=1
				if self.requests==0:
					self.grant()
				comm.send([receiver, "ACK"], dest = sender-1)		
			
		if msg[1]=="DONE":
			for i in range(len(self.Out)):
				if self.Out[i]==msg[0]:
					self.Out[i]="DONE"
					break
		
		if msg[1]=="ACK":
			for i in range(len(self.In)):
				if msg[0]==self.In[i]:
					self.In[i]="ACK"
					break
		
		if msg[1]=="TERMINATE":
			sys.exit(0)


	def notify(self,sender):
		if self.notified==False:
			self.notified = True
			Out = self.Out
			for i in range(len(Out)):
				if Out[i]!="DONE":
					comm.send([self.id,"NOTIFY"], dest = Out[i]-1)

			if self.requests==0 :
				self.grant()

	def grant(self):
		self.free = True
		In = self.In
		for i in range(len(In)):
			if In[i]!="ACK":
				comm.send([self.id,"GRANT"], dest = In[i]-1)

nodes={}
file = open("input.txt","r")
lines = file.readlines()
numberOfNodes = int(lines[0])
initiator = int(lines[1])
lines = lines[2:]
nodes[rank+1] = Node(rank+1)
for i in lines:
	[u,v] = i.split(" ")
	u = int(u)
	v = int(v)
	if u == rank+1:
		nodes[u].addOut(v)
	elif v == rank+1:
		nodes[v].addIn(u)
file.close()

if rank+1==initiator:
	nodes[rank+1].initiate()


while True:
	nodes[rank+1].listen()
	if rank+1 == initiator and nodes[rank+1].allDone():
		if nodes[initiator].free==True:
			print(str(initiator)+" is deadlock free!")
		elif nodes[initiator].requests>0:
			print(str(initiator)+" is deadlocked!")
		for i in range(comm.Get_size()):
			if i!=rank:
				comm.send([initiator,"TERMINATE"],dest=i)
		break

file.close()
sys.exit(0)
