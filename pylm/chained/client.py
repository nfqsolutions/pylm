from pylm.standalone import ParallelClient as LoopClient
from pylm.components.core import zmq_context
from uuid import uuid4
import zmq
import sys


class Client(LoopClient):
    def __init__(self, pull_address, db_address, server_name, pipeline=None):
        self.server_name = server_name
        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(pull_address)
        self.pull_address = pull_address

        self.db_address = db_address
        self.db = zmq_context.socket(zmq.REQ)
        self.db.connect(db_address)

        self.function = ''
        self.job_generator = None
        self.messages = 0
        self.uuid = str(uuid4())
        # Pipeline, also session.
        if pipeline:
            self.pipeline = pipeline
        else:
            self.pipeline = str(uuid4())

        # Cache to tag messages
        self.cache = None

    def job(self, function, generator, cache=None, messages=sys.maxsize):
        """
        Submit a job for the cluster given a function to be executed, and a generator
        that provides the payloads for each message
        :param function: String. Function to be executed
        :param generator: Generator of messages.
        :param cache: Use a cache constant for the message
        :param messages: Number of expected messages before shutting down the client.
        :return:
        """
        if cache:
            if type(cache) == bytes or type(cache) == str:
                self.cache = cache
            else:
                raise TypeError('Cache must be <bytes> or <str>')

        self.function = function
        self.job_generator = generator
        self._push_job()

    def clean(self):
        self.push.close()
        self.db.close()
