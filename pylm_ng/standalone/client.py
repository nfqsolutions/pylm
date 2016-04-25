from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage
from threading import Thread
from uuid import uuid4
import zmq
import sys


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
        :return: UUID of the key
        """
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
        message.payload = key
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload

    def call(self, function, data):
        """
        RPC function with data
        :param function: Function name as string, already defined in the server
        :param data: Binary message to be sent as argument
        :return: Result
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, function])
        message.payload = data
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload


class ParallelClient(object):
    def __init__(self, push_address, pull_address, db_address, server_name):
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
        message.payload = key
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload
