from process import Process
from message import RequestMessage, NewBatchMessage, ResponseMessage, KillMessage
from utils import Command
import random
import time

class Client(Process):
    def __init__(self, env, id):
        Process.__init__(self, env, id)
        self.env.addProc(self)


    def body(self):
        # print "Here I am: ", self.id

        while True:
            try:
                msg = self.getNextMessage()
                if isinstance(msg, NewBatchMessage):
                    self.sendRequests(msg.num_requests)
                    break
            except:
                pass
            
            time.sleep(0.02)

    def sendRequests(self, num_requests):
        for i in range(num_requests):
            # define the request
            operation = "operation %s.%d" % (self.id[-1], i)
            cmd = Command(self.id, "%s.%d" % (self.id[-1], i), operation)

            # send out request to all replicas (implementation asks for it, but it works sending to only one also)
            for r in self.env.conf.replicas:
                self.sendMessage(r, RequestMessage(self.id, cmd))

            # wait for response(s)
            count = 0
            while True:
                msg = self.getNextMessage()
                if isinstance(msg, ResponseMessage):
                    if msg.decision == operation:
                        # count += 1
                        break  # one confirmation is enough

                # Received confirmation from all replicas (should be enough with one though..)
                # if count == self.env.NREPLICAS:
                #     break
