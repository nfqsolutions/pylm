# Test for the prototype of the client for the parallel client.

from threading import Thread
from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage
from pylm_ng.standalone import Master, EndPoint, Worker
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
        self.push.connect(pull_address)

        self.pull_address = pull_address
        self.pull = zmq_context.socket(zmq.PULL)
        self.pull.connect(push_address)

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
            message.function = '.'.join([self.server_name, self.function])
            message.payload = m

            print('Client:: send message')
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
            #yield message_data

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


def test_standalone_parallel_client():
    this_log_address = "inproc://log6"
    this_perf_address = "inproc://perf6"
    this_ping_address = "inproc://ping6"
    endpoint = EndPoint('EndPoint',
                        this_log_address,
                        this_perf_address,
                        this_ping_address)
    master = Master('master', 'inproc://pull6', 'inproc://push6',
                    'inproc://worker_pull6', 'inproc://worker_push6',
                    endpoint.log_address, endpoint.perf_address,
                    endpoint.ping_address, palm=True)

    worker1 = Worker('worker1',
                     master.worker_push_address,
                     master.worker_pull_address,
                     this_log_address,
                     this_perf_address,
                     this_ping_address)
    worker2 = Worker('worker2',
                     master.worker_push_address,
                     master.worker_pull_address,
                     this_log_address,
                     this_perf_address,
                     this_ping_address)

    client = ParallelClient(master.push_address,
                            master.pull_address,
                            'master')

    threads = [
        Thread(target=endpoint._start_debug),
        Thread(target=master.start),
        Thread(target=worker1.start),
        Thread(target=worker2.start)
    ]

    for t in threads:
        t.start()

    def message_generator():
        for i in range(10):
            yield str(i).encode('utf-8')

    print('******* Launch client')
    for i, m in enumerate(client.job('somefunction', message_generator(), 10)):
        print('************ Got something back', m, i)

    for t in threads:
        t.join(1)


if __name__ == '__main__':
    test_standalone_parallel_client()
