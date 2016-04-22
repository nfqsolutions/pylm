# Test for the prototype of the client for the parallel client.

from threading import Thread
from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage
from uuid import uuid4
import zmq
import sys


def worker(listen_pull, listen_push, messages):
    pull = zmq_context.socket(zmq.PULL)
    pull.bind(listen_pull)
    push = zmq_context.socket(zmq.PUSH)
    push.bind(listen_push)

    print('****', 'Worker waiting...')
    for i in range(messages):
        message_data = pull.recv()
        print('********', 'Worker1 got message.', i)
        push.send(message_data)


class ParallelClient(object):
    def __init__(self, push_address, pull_address, server_name):
        self.server_name = server_name
        self.push_address = push_address
        self.pull_address = pull_address
        self.function = ''
        self.job_generator = None
        self.messages = 0
        self.uuid = str(uuid4())

    def _push_job(self):
        for m in self.job_generator:
            message = PalmMessage()
            message.pipeline = str(uuid4())
            message.client = self.uuid
            message.stage = 0
            message.function = self.function
            message.payload = m

            self.push.send(message.SerializeToString())

    def _launch_job_from_generator(self, generator, messages=sys.maxsize):
        self.job_generator = generator
        self.messages = messages
        job_thread = Thread(target=self._push_job)
        job_thread.start()

        for i in range(self.messages):
