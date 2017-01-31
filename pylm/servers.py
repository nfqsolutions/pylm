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
from pylm.parts.services import WorkerPullService, WorkerPushService
from pylm.parts.services import PullService, PubService
from pylm.parts.utils import CacheService
from pylm.parts.servers import BaseMaster, ServerTemplate
from pylm.parts.messages_pb2 import PalmMessage, BrokerMessage
from pylm.persistence.kv import DictDB
from google.protobuf.message import DecodeError
from uuid import uuid4
import concurrent.futures
import traceback
import logging
import zmq
import sys


class Server(object):
    """
    Standalone and minimal server that replies single requests.

    :param str name: Name of the server
    :param str db_address: ZeroMQ address of the cache service.
    :param str pull_address: Address of the pull socket
    :param str pub_address: Address of the pub socket
    :param pipelined: True if the server is chained to another server.
    :param log_level: Minimum output log level.
    :param int messages: Total number of messages that the server processes.
     Useful for debugging.
    """
    def __init__(self, name, db_address,
                 pull_address, pub_address, pipelined=False,
                 log_level=logging.INFO, messages=sys.maxsize):
        self.name = name
        self.cache = DictDB()
        self.db_address = db_address
        self.pull_address = pull_address
        self.pub_address = pub_address
        self.pipelined = pipelined

        self.cache.set('name', name.encode('utf-8'))
        self.cache.set('pull_address', pull_address.encode('utf-8'))
        self.cache.set('pub_address', pub_address.encode('utf-8'))

        self.logger = logging.getLogger(name=name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(log_level)

        self.messages = messages

    def _execution_handler(self):
        pull_socket = zmq_context.socket(zmq.PULL)
        pull_socket.bind(self.pull_address)

        pub_socket = zmq_context.socket(zmq.PUB)
        pub_socket.bind(self.pub_address)

        for i in range(self.messages):
            self.logger.debug('Server waiting for messages')
            message_data = pull_socket.recv()
            self.logger.debug('Got message {}'.format(i + 1))
            result = b'0'
            message = PalmMessage()
            try:
                message.ParseFromString(message_data)
                [server, function] = message.function.split('.')

                if not self.name == server:
                    self.logger.error('You called the wrong server')
                else:
                    try:
                        user_function = getattr(self, function)
                        self.logger.debug('Looking for {}'.format(function))
                        try:
                            result = user_function(message.payload)
                        except:
                            self.logger.error('User function gave an error')
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
                            for l in lines:
                                self.logger.exception(l)

                    except KeyError:
                        self.logger.error(
                            'Function {} was not found'.format(function)
                        )
            except DecodeError:
                self.logger.error('Message could not be decoded')

            message.payload = result

            if self.pipelined:
                topic = None
            else:
                topic = message.client

            pub_socket.send_multipart(
                [topic.encode('utf-8'), message.SerializeToString()]
            )

    def start(self, cache_messages=sys.maxsize):
        """
        Start the server

        :param cache_messages: Number of messages the cache service handles before it
          shuts down. Useful for debugging
        :return:
        """
        threads = []

        cache = CacheService('cache', self.db_address, logger=self.logger,
                             cache=self.cache, messages=cache_messages)

        threads.append(cache.start)
        threads.append(self._execution_handler)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(threads)) as executor:
            results = [executor.submit(thread) for thread in threads]
            for future in concurrent.futures.as_completed(results):
                try:
                    future.result()
                except Exception as exc:
                    self.logger.error('This is critical, one of the components of the server died')
                    lines = traceback.format_exception(*sys.exc_info())
                    for line in lines:
                        self.logger.error(line.strip('\n'))

        return self.name.encode('utf-8')


class Master(ServerTemplate, BaseMaster):
    """
    Standalone master server, intended to send workload to workers.

    :param name: Name of the server
    :param pull_address: Valid address for the pull service
    :param pub_address: Valid address for the pub service
    :param worker_pull_address: Valid address for the pull-from-workers service
    :param worker_push_address: Valid address for the push-to-workers service
    :param db_address: Valid address to bind the Cache service
    :param cache: Key-value embeddable database. Pick from one of the supported ones
    :param log_level: Logging level
    """
    def __init__(self, name: str, pull_address: str, pub_address: str,
                 worker_pull_address: str, worker_push_address: str, db_address: str,
                 cache: object = DictDB(), log_level: int = logging.INFO):
        """
        """
        super(Master, self).__init__(logging_level=log_level)
        self.name = name
        self.palm = True
        self.cache = cache
        self.cache.set('name', self.name.encode('utf-8'))
        self.cache.set('pull_address', pull_address.encode('utf-8'))
        self.cache.set('pub_address', pub_address.encode('utf-8'))
        self.cache.set('worker_pull_address', worker_pull_address.encode('utf-8'))
        self.cache.set('worker_push_address', worker_push_address.encode('utf-8'))

        self.register_inbound(PullService, 'Pull', pull_address, route='WorkerPush')
        self.register_inbound(WorkerPullService, 'WorkerPull', worker_pull_address, route='Pub')
        self.register_outbound(WorkerPushService, 'WorkerPush', worker_push_address)
        self.register_outbound(PubService, 'Pub', pub_address, log='to_sink')
        self.register_bypass(CacheService, 'Cache', db_address)
        self.preset_cache(name=name,
                          db_address=db_address,
                          pull_address=pull_address,
                          pub_address=pub_address,
                          worker_pull_address=worker_pull_address,
                          worker_push_address=worker_push_address)

        # Monkey patches the scatter and gather functions to the
        # scatter function of Push and Pull parts respectively.
        self.inbound_components['Pull'].scatter = self.scatter
        self.outbound_components['Pub'].scatter = self.gather


class Worker(object):
    """
    Standalone worker for the standalone master.

    :param name: Name assigned to this worker server
    :param db_address: Address of the db service of the master
    :param push_address: Address the workers push to. If left blank, fetches it from the master
    :param pull_address: Address the workers pull from. If left blank, fetches it from the master
    :param log_level: Log level for this server.
    :param messages: Number of messages before it is shut down.
    """
    def __init__(self, name='', db_address='', push_address=None, pull_address=None,
                 log_level=logging.INFO, messages=sys.maxsize):

        self.uuid = str(uuid4())

        # Give a random name if not given
        if not name:
            self.name = self.uuid
        else:
            self.name = name

        # Configure the log handler
        self.logger = logging.getLogger(name=name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(log_level)

        # Configure the connections.
        self.push_address = push_address
        self.pull_address = pull_address

        if not db_address:
            raise ValueError('db_address argument is mandatory')

        self.db_address = db_address
        self.db = zmq_context.socket(zmq.REQ)
        self.db.connect(db_address)

        self._get_config_from_master()

        self.pull = zmq_context.socket(zmq.PULL)
        self.pull.connect(self.push_address)

        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(self.pull_address)

        self.messages = messages
        self.message = BrokerMessage()

    def _get_config_from_master(self):
        if not self.push_address:
            self.push_address = self.get('worker_push_address').decode('utf-8')
            self.logger.info('Got worker push address: {}'.format(self.push_address))

        if not self.pull_address:
            self.pull_address = self.get('worker_pull_address').decode('utf-8')
            self.logger.info('Got worker pull address: {}'.format(self.pull_address))

        return {'push_address': self.push_address,
                'pull_address': self.pull_address}

    def start(self):
        for i in range(self.messages):
            message_data = self.pull.recv()
            self.logger.debug('{} Got a message'.format(self.name))
            result = b'0'
            try:
                self.message.ParseFromString(message_data)
                instruction = self.message.instruction
                try:
                    user_function = getattr(self, instruction)
                    self.logger.debug('Looking for {}'.format(instruction))
                    try:
                        result = user_function(self.message.payload)
                        self.logger.debug('{} Ok'.format(instruction))
                    except:
                        self.logger.error(
                            '{} User function {} gave an error'.format(self.name,
                                                                       instruction)
                        )
                        lines = traceback.format_exception(*sys.exc_info())
                        self.logger.exception(lines[0])
                        
                except AttributeError:
                    self.logger.error('Function {} was not found'.format(instruction))
            except DecodeError:
                self.logger.error('Message could not be decoded')

            self.message.payload = result
            self.push.send(self.message.SerializeToString())

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
        message.function = '.'.join(['_', 'set'])
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
        message.function = '.'.join(['_', 'get'])
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
        message.function = '.'.join(['_', 'delete'])
        message.payload = key.encode('utf-8')
        self.db.send(message.SerializeToString())
        return self.db.recv().decode('utf-8')
