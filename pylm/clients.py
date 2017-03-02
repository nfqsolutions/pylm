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
import logging
import time
import zmq
import sys


class Client(object):
    """
    Client to connect to parallel servers

    :param server_name: Server you are connecting to
    :param db_address: Address for the cache service, for first connection or configuration.
    :param push_address: Address of the push service of the server to pull from
    :param sub_address: Address of the pub service of the server to subscribe to
    :param session: Name of the pipeline if the session has to be reused
    :param logging_level: Specify the logging level.
    :param this_config: Do not fetch configuration from the server
    """
    def __init__(self, server_name: str,
                 db_address: str,
                 push_address: str=None,
                 sub_address: str=None,
                 session: str=None,
                 logging_level: int=logging.INFO,
                 this_config=False):
        self.server_name = server_name
        self.db_address = db_address

        if session:
            self.pipeline = session
            self.session_set = True
        else:
            self.pipeline = str(uuid4())
            self.session_set = False
            
        self.uuid = str(uuid4())

        self.db = zmq_context.socket(zmq.REQ)
        self.db.identity = self.uuid.encode('utf-8')
        self.db.connect(db_address)

        self.sub_address = sub_address
        self.push_address = push_address

        # Basic console logging
        self.logger = logging.getLogger(name=self.uuid)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging_level)

        if this_config:
            self.logger.warning('Not fetching config from the server')
        else:
            self.logger.info('Fetching configuration from the server')
            self._get_config_from_master()

        # PUB-SUB takes a while
        time.sleep(0.5)

    def _get_config_from_master(self):
        name = self.get('name').decode('utf-8')
        if not name == self.server_name:
            raise ValueError('You are connecting to the wrong server')

        if not self.sub_address:
            self.sub_address = self.get('pub_address').decode('utf-8')
            self.logger.info(
                'CLIENT {}: Got subscription address: {}'.format(
                    self.uuid,
                    self.sub_address)
                )

        if not self.push_address:
            self.push_address = self.get('pull_address').decode('utf-8')
            self.logger.info(
                'CLIENT {}: Got push address: {}'.format(
                    self.uuid,
                    self.push_address)
                )

        return {'sub_address': self.sub_address,
                'push_address': self.push_address}

    def clean(self):
        self.db.close()

    def _sender(self, socket, function, generator, cache):
        for payload in generator:
            message = PalmMessage()
            message.function = function
            message.stage = 0
            message.pipeline = self.pipeline
            message.client = self.uuid
            message.payload = payload
            if cache:
                message.cache = cache

            socket.send(message.SerializeToString())
        
    def job(self, function, generator, messages: int=sys.maxsize, cache: str=''):
        """
        Submit a job with multiple messages to a server.

        :param function: Sting or list of strings following the format
            ``server.function``.
        :param payload: A generator that yields a series of binary messages.
        :param messages: Number of messages expected to be sent back to the
            client. Defaults to infinity (sys.maxsize)
        :param cache: Cache data included in the message
        :return: an iterator with the messages that are sent back to the client.
        """
        push_socket = zmq_context.socket(zmq.PUSH)
        push_socket.connect(self.push_address)

        sub_socket = zmq_context.socket(zmq.SUB)
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.uuid)
        sub_socket.connect(self.sub_address)

        if type(function) == str:
            # Single-stage job
            pass
        elif type(function) == list:
            # Pipelined job.
            function = ' '.join(function)

        # Remember that sockets are not thread safe
        sender_thread = Thread(target=self._sender,
                               args=(push_socket, function, generator, cache))

        # Sender runs in background.
        sender_thread.start()

        for i in range(messages):
            [client, message_data] = sub_socket.recv_multipart()
            if not client.decode('utf-8') == self.uuid:
                raise ValueError('The client got a message that does not belong')

            message = PalmMessage()
            message.ParseFromString(message_data)
            yield message.payload

    def eval(self, function, payload: bytes, messages: int=1, cache: str=''):
        """
        Execute single job.

        :param function: Sting or list of strings following the format
            ``server.function``.
        :param payload: Binary message to be sent
        :param messages: Number of messages expected to be sent back to the
            client
        :param cache: Cache data included in the message
        :return: If messages=1, the result data. If messages > 1, a list with the results
        """
        push_socket = zmq_context.socket(zmq.PUSH)
        push_socket.connect(self.push_address)

        sub_socket = zmq_context.socket(zmq.SUB)
        sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.uuid)
        sub_socket.connect(self.sub_address)

        if type(function) == str:
            # Single-stage job
            pass
        elif type(function) == list:
            # Pipelined job.
            function = ' '.join(function)

        message = PalmMessage()
        message.function = function
        message.stage = 0
        message.pipeline = self.pipeline
        message.client = self.uuid
        message.payload = payload
        if cache:
            message.cache = cache

        push_socket.send(message.SerializeToString())

        result = []

        for i in range(messages):
            [client, message_data] = sub_socket.recv_multipart()
            message.ParseFromString(message_data)
            result.append(message.payload)

        if messages == 1:
            return result[0]

        else:
            return result

    def set(self, value: bytes, key=None):
        """
        Sets a key value pare in the remote database. If the key is not set,
        the function returns a new key. Note that the order of the arguments
        is reversed from the usual.

        .. warning::

            If the session attribute is specified, all the keys will be
            prepended with the session id.

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

