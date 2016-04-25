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
        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(push_address)

        self.pull_address = pull_address
        self.pull = zmq_context.socket(zmq.PULL)
        self.pull.connect(pull_address)

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
            message_data = self.pull.recv()
            message = PalmMessage()
            message.ParseFromString(message_data)
            yield message.payload

    def clean(self):
        self.push.close()
        self.pull.close()

    def job(self, function, generator, messages=sys.maxsize):
        """
        Submit a job for the cluster given a function to be executed, and a generator
        that provides the payloads for each message
        :param function: String. Function to be executed
        :param generator: Generator of messages.
        :param messages: Number of expected messages before shutting down the client.
        :return:
        """
        self.function = function
        yield from self._launch_job_from_generator(generator, messages)
        self.clean()
