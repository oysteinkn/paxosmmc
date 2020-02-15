import sys, os, signal, sys, time, math, argparse
from acceptor import Acceptor
from leader import Leader
from message import RequestMessage, NewBatchMessage, KillMessage
from process import Process
from replica import Replica
from client import Client
from utils import *

NLEADERS = 1

class Env:
  def __init__(self, size=2, num_clients=1, num_requests=200):
    self.NACCEPTORS = 2 * (size - 1) + 1  # how many acceptor for same fault-tolerance as 'size' replicas (2f+1)
    self.NREPLICAS = size
    self.num_requests = num_requests
    self.num_clients = num_clients
    self.conf = Config([], [], [], [])
    self.procs = {}
    self.done = False

    self.setup()


  def sendMessage(self, dst, msg):
    if dst in self.procs:
      self.procs[dst].deliver(msg)


  def addProc(self, proc):
    self.procs[proc.id] = proc
    proc.start()


  def removeProc(self, pid):
    del self.procs[pid]

  def setup(self):
    # Initiate system
    for i in range(self.NREPLICAS):
      pid = "replica %d" % i
      Replica(self, pid, self.conf)
      self.conf.replicas.append(pid)
    for i in range(self.NACCEPTORS):
      pid = "acceptor %d" % i
      Acceptor(self, pid)
      self.conf.acceptors.append(pid)
    for i in range(NLEADERS):
      pid = "leader %d" % i
      Leader(self, pid, self.conf)
      self.conf.leaders.append(pid)
    
    # Intiate clients
    for c in range(self.num_clients):
      pid = "client %d" % c
      Client(self, pid)
      self.conf.clients.append(pid)

  def bench(self):
    # Ensure same amount of requests per client
    requests_per_client = int(math.floor(self.num_requests / self.num_clients))
    self.num_requests = requests_per_client * self.num_clients

    # Tell replicas that a new batch of 'num_requests' is coming
    for r in self.conf.replicas:
      self.sendMessage(r, NewBatchMessage("env", self.num_requests))

    time.sleep(0.5)

    start_time = time.time()

    # Tell clients to send requests for current batch
    for c in self.conf.clients:
      self.sendMessage(c, NewBatchMessage("env", requests_per_client))

    while not self.done:
      time.sleep(0.1)
      continue
    
    t = time.time() - start_time
    tps = self.num_requests / t

    time.sleep(1)

    return tps

  def setDone(self, done):
    self.done = done

  def kill(self):
    for p in self.procs.keys():
      self.procs[p].deliver(KillMessage("env"))

    time.sleep(1.5)


if __name__=='__main__':

  parser = argparse.ArgumentParser()
  parser.add_argument("-s", "--size", help="size of cluster", action="store", type=int, default=2)
  parser.add_argument("-c", "--clients", help="number of concurrent clients (proposals)", action="store", type=int, default=10)
  args = parser.parse_args()

  e = Env(args.size, args.clients)
  tps = e.bench()
  e.kill()
  print tps
