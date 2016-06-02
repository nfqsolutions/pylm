from pylm.components.core import zmq_context
from pylm.components.messages_pb2 import PalmMessage
from threading import Thread
from uuid import uuid4
from itertools import repeat
import zmq
import sys
import time


class Client(object):
    def __init__(self, connection, server_name):
        self.req = zmq_context.socket(zmq.REQ)
        self.req.connect(connection)
        self.server_name = server_name
        self.uuid = str(uuid4())

    def set(self, data, key=None):
        """
        Sets some data in the server's internal cache.
        :param data: Data to be cached.
        :param key: Sets a key. Otherwise it returns an automatically generated key
        :return: UUID of the key
        """
        if not type(data) == bytes:
            raise TypeError('First argument *data* must be of type <bytes>')

        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'set'])
        message.payload = data
        if key:
            message.cache = key
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload.decode('utf-8')

    def get(self, key):
        """
        Gets data from the server's internal cache.
        :param data:
        :param key:
        :return:
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'get'])
        message.payload = key.encode('utf-8')
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload

    def delete(self, key):
        """
        Deletes data in the server's internal cache.
        :param key: Key of the data to be deleted
        :return:
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'delete'])
        message.payload = key.encode('utf-8')
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload.decode('utf-8')

    def job(self, function, data, pipeline=None, cache=None):
        """
        RPC function with data
        :param function: Function name as string, already defined in the server
        :param data: Binary message to be sent as argument
        :return: Result
        """
        message = PalmMessage()
        if pipeline:
            message.pipeline = pipeline
        else:
            message.pipeline = str(uuid4())

        if cache:
            message.cache = cache

        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, function])
        message.payload = data
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload


class ParallelClient(object):
    def __init__(self, push_address, pull_address, db_address, server_name, pipeline=None):
        self.server_name = server_name
        self.push_address = push_address
        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(pull_address)

        self.pull_address = pull_address
        self.pull = zmq_context.socket(zmq.PULL)
        self.pull.connect(push_address)

        self.db_address = db_address
        self.db = zmq_context.socket(zmq.REQ)
        self.db.connect(db_address)

        self.function = ''
        self.job_generator = None
        self.messages = 0
        self.uuid = str(uuid4())
        # Pipeline, also session.
        self.pipeline = pipeline
        # Cache to tag messages
        self.cache = None

    def _push_job(self):
        if self.pipeline:
            pipeline_id = self.pipeline
        else:
            pipeline_id = str(uuid4())

        for m, c in zip(self.job_generator, repeat(self.cache)):
            message = PalmMessage()
            message.pipeline = pipeline_id
            message.client = self.uuid
            message.stage = 0
            message.function = '.'.join([self.server_name, self.function])
            message.payload = m
            if c:
                message.cache = c

            self.push.send(message.SerializeToString())
            time.sleep(0.001)  # Flushing the socket the wrong way.

        print('**************** killing job')
        time.sleep(10)

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
        self.db.close()

    def job(self, function, generator, cache=None, messages=sys.maxsize):
        """
        Submit a job for the cluster given a function to be executed, and a generator
        that provides the payloads for each message
        :param function: String. Function to be executed
        :param generator: Generator of messages.
        :param messages: Number of expected messages before shutting down the client.
        :return:
        """
        if cache:
            self.cache = cache

        self.function = function
        yield from self._launch_job_from_generator(generator, messages)

    def set(self, value, key=None):
        """
        Sets a key value pare in the remote database.
        :param key:
        :param value:
        :return:
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'set'])
        message.payload = value
        if key:
            message.cache = key

        self.db.send(message.SerializeToString())
        return self.db.recv().decode('utf-8')

    def get(self, key):
        """
        Gets a value from server's internal cache
        :param key: Key for the data to be selected.
        :return:
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'get'])
        message.payload = key.encode('utf-8')
        self.db.send(message.SerializeToString())
        return self.db.recv()

    def delete(self, key):
        """
        Deletes data in the server's internal cache.
        :param key: Key of the data to be deleted
        :return:
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'delete'])
        message.payload = key.encode('utf-8')
        self.db.send(message.SerializeToString())
        return self.db.recv().decode('utf-8')
