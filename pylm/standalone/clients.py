# Pylm, a framework to build components for high performance distributed
# applications. Copyright (C) 2016 NFQ Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage
from threading import Thread
from uuid import uuid4
from itertools import repeat
import concurrent.futures
import time
import zmq
import sys


class Client(object):
    """Serial client"""
    def __init__(self, connection, server_name, pipeline=None):
        self.req = zmq_context.socket(zmq.REQ)
        self.req.connect(connection)
        self.server_name = server_name
        self.uuid = str(uuid4())
        if pipeline:
            self.pipeline = pipeline
        else:
            self.pipeline = str(uuid4())

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
        message.pipeline = self.pipeline
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

        :param key: Key for the data to get
        :return:
        """
        message = PalmMessage()
        message.pipeline = self.pipeline
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
        message.pipeline = self.pipeline
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
        :param pipeline: Name of the pipeline if an existing one has to be used
        :param cache: Value of the cache for manually overriding that internal variable
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


class SubscribedClient(object):
    """
    Client to connect to parallel servers

    :param sub_address: Address of the pub service of the server to subscribe to
    :param pull_address: Address of the push service of the server to pull from
    :param db_address: Address for the cache service
    :param server_name: Name of the server to be connected to
    :param pipeline: Name of the pipeline if the session has to be reused
    """
    def __init__(self, sub_address: str, pull_address: str,
                 db_address: str, server_name: str,
                 pipeline: str = None):
        self.sub_address = sub_address
        self.pull_address = pull_address
        self.db_address = db_address
        self.server_name = server_name
        if pipeline:
            self.pipeline = pipeline
        else:
            self.pipeline = str(uuid4())
        self.uuid = str(uuid4())

        # PUB-SUB takes a while
        time.sleep(0.5)

    def clean(self):
        self.push.close()
        self.sub.close()
        self.db.close()

    def _sender(self, socket, function, generator):
        for payload in generator:
            message = PalmMessage()
            message.function = function
            message.stage = 1
            message.pipeline = self.pipeline
            message.client = self.uuid
            message.payload = payload

            socket.send(message.SerializeToString())
        
    def job(self, function, generator, cache=None, messages=sys.maxsize):
        push_socket = zmq_context.socket(zmq.PUSH)
        push_socket.connect(self.pull_address)
        sender_thread = Thread(target=self._sender,
                               args=(push_socket, function, generator))

        # Sender runs in background.
        sender_thread.start()
        
        sub_socket = zmq_context.socket(zmq.SUB)
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.uuid)
        sub_socket.connect(self.sub_address)

        for i in range(messages):
            [client, message] = sub_socket.recv_multipart()
            if not client.decode('utf-8') == self.uuid:
                raise ValueError('The client got a message that does not belong')

            yield message 


    def set(self, value: bytes, key=None):
        """
        Sets a key value pare in the remote database. If the key is not set,
        the function returns a new key. Note that the order of the arguments
        is reversed from the usual

        :param value: Value to be stored
        :param key: Key for the k-v storage
        :return: New key or the same key
        """
        if not type(value) == bytes:
            raise TypeError('First argument {} must be of type <bytes>'.format(value))

        message = PalmMessage()
        message.pipeline = str(uuid4())  # For a set job, the pipeline is not important
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'set'])
        message.payload = value
        if key and self.session_set:
            message.cache = ''.join([self.pipeline, key])
        elif key:
            message.cache = key

        self.db.send(message.SerializeToString())
        return self.db.recv().decode('utf-8')

    def get(self, key):
        """
        Gets a value from server's internal cache

        :param key: Key for the data to be selected.
        :return: Value
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


class ParallelClient(object):
    """
    Client to connect to parallel servers

    :param push_address: Address of the pull service of the server to push to
    :param pull_address: Address of the push service of the server to pull from
    :param db_address: Address for the cache service
    :param server_name: Name of the server to be connected to
    :param pipeline: Name of the pipeline if the session has to be reused
    """
    def __init__(self, push_address: str, pull_address: str,
                 db_address: str, server_name: str,
                 pipeline: str = None):
        # TODO: Change the order of push and pull addresses. This is confusing now.
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
        if pipeline:
            self.pipeline = pipeline
            self.session_set = True
        else:
            self.pipeline = str(uuid4())
            self.session_set = False

        # Cache to tag messages
        self.cache = None

    def _push_job(self):
        for m, c in zip(self.job_generator, repeat(self.cache)):
            message = PalmMessage()
            message.pipeline = self.pipeline
            message.client = self.uuid
            message.stage = 0
            message.function = '.'.join([self.server_name, self.function])
            message.payload = m
            if c:
                message.cache = c

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
            if type(cache) == bytes or type(cache) == str:
                self.cache = cache
            else:
                raise TypeError('Cache must be <bytes> or <str>')

        self.function = function
        yield from self._launch_job_from_generator(generator, messages)

    def set(self, value: bytes, key=None):
        """
        Sets a key value pare in the remote database. If the key is not set,
        the function returns a new key. Note that the order of the arguments
        is reversed from the usual

        :param value: Value to be stored
        :param key: Key for the k-v storage
        :return: New key or the same key
        """
        if not type(value) == bytes:
            raise TypeError('First argument {} must be of type <bytes>'.format(value))

        message = PalmMessage()
        message.pipeline = str(uuid4())  # For a set job, the pipeline is not important
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'set'])
        message.payload = value
        if key and self.session_set:
            message.cache = ''.join([self.pipeline, key])
        elif key:
            message.cache = key

        self.db.send(message.SerializeToString())
        return self.db.recv().decode('utf-8')

    def get(self, key):
        """
        Gets a value from server's internal cache

        :param key: Key for the data to be selected.
        :return: Value
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
