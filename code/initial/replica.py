from process import Process
from message import ProposeMessage,DecisionMessage,RequestMessage,NewBatchMessage,ResponseMessage,KillMessage
from utils import *
import time

class Replica(Process):
  def __init__(self, env, id, config):
    Process.__init__(self, env, id)
    self.slot_in = self.slot_out = 1
    self.proposals = {}
    self.decisions = {}
    self.requests = []
    self.config = self.env.conf

    # Values needed to calculate TPS
    self.start_time = None
    self.to_perform = None
    self.performed = 0

    self.env.addProc(self)


  def propose(self):
    while len(self.requests) != 0 and self.slot_in < self.slot_out+WINDOW:
      if self.slot_in > WINDOW and self.slot_in-WINDOW in self.decisions:
        if isinstance(self.decisions[self.slot_in-WINDOW],ReconfigCommand):
          r,a,l = self.decisions[self.slot_in-WINDOW].config.split(';')
          self.config = Config(r.split(','),a.split(','),l.split(','))
          print self.id, ": new config:", self.config
      if self.slot_in not in self.decisions:
        cmd = self.requests.pop(0)
        self.proposals[self.slot_in] = cmd
        for ldr in self.config.leaders:
          self.sendMessage(ldr, ProposeMessage(self.id,self.slot_in,cmd))
      self.slot_in +=1


  def perform(self, cmd):
    for s in range(1, self.slot_out):
      if self.decisions[s] == cmd:
        self.slot_out += 1
        return
    if isinstance(cmd, ReconfigCommand):
      self.slot_out += 1
      return
    # print self.id, ": perform",self.slot_out, ":", cmd
    self.slot_out += 1

    self.performed += 1
    # Tell client the decision on its request
    self.sendMessage(cmd.client, ResponseMessage(self.id, cmd.op))


  def body(self):
    # print "Here I am: ", self.id
    while True:
      msg = self.getNextMessage()

      if isinstance(msg, NewBatchMessage):
        self.to_perform = msg.num_requests
        self.start_time = time.time()

      elif isinstance(msg, RequestMessage):
        self.requests.append(msg.command)
      elif isinstance(msg, DecisionMessage):
        self.decisions[msg.slot_number] = msg.command
        while self.slot_out in self.decisions:
          if self.slot_out in self.proposals:
            if self.proposals[self.slot_out]!=self.decisions[self.slot_out]:
              self.requests.append(self.proposals[self.slot_out])
            del self.proposals[self.slot_out]
          self.perform(self.decisions[self.slot_out])
      elif isinstance(msg, KillMessage):
        break
      else:
        break
      self.propose()

      # Check if batch is done
      if(self.performed == self.to_perform):
        self.performed = 0

        # print self.id, "done in: ", time.time() - self.start_time
        self.env.setDone(True)
        break
