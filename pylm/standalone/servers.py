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
from pylm.parts.utils import PushHandler, Pinger, PerformanceCounter, CacheService
from pylm.parts.servers import BaseMaster, ServerTemplate
from pylm.parts.messages_pb2 import PalmMessage, BrokerMessage
from pylm.persistence.kv import DictDB
from google.protobuf.message import DecodeError
from threading import Thread
from uuid import uuid4
import traceback
import logging
import zmq
import sys


# Standalone servers use some of the infrastructure of PALM, but they
# are not run-time configurable. You have to wire the connections yourself,
# but on the other hand, hou have a logger and the performance counter, and
# a convenient endpoint for these services.

class Server(object):
    """
    Standalone and minimal server that replies single requests.

    :param str name: Name of the server
    :param str rep_address: ZeroMQ address this server binds to.
    :param str log_address: Address of the central logging system. Leave to None to let the server manage the logs itself
    :param str perf_address: Address of the performance counter registry. Leave to None if you don't need performance counters.
    :param str ping_address: Address of the central server registry. Leave to None if you don't want to track the health of the server.
    :param log_level: Minimum output log level.
    :param int messages: Total number of messages that the server processes. Useful for debugging.
    """
    def __init__(self, name, rep_address, log_address=None, perf_address=None,
                 ping_address=None, log_level=logging.INFO,
                 messages=sys.maxsize):
        self.name = name
        self.cache = {}  # The simplest possible cache
        self.rep_address = rep_address

        # Configure the log handler
        if log_address:
            handler = PushHandler(log_address)
            self.logger = logging.getLogger(name)
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)

        else:
            self.logger = logging.getLogger(name=name)
            self.logger.setLevel(log_level)
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)

        if perf_address:
            # Configure the performance counter
            self.perfcounter = PerformanceCounter(listen_address=perf_address)

        if ping_address:
            # Configure the pinger.
            self.pinger = Pinger(listen_address=ping_address, every=30.0)

        # Configure the rep connection that binds and blocks.
        self.rep = zmq_context.socket(zmq.REP)

        # This is the function storage
        self.user_functions = {}

        self.messages = messages

        if ping_address:
            # This is the pinger thread that keeps the pinger alive.
            pinger_thread = Thread(target=self.pinger.start)
            pinger_thread.daemon = True
            pinger_thread.start()

    def set(self, data, key=None):
        if not key:
            key = str(uuid4())

        self.cache[key] = data
        return key.encode('utf-8')

    def delete(self, key):
        del self.cache[key.decode('utf-8')]
        return key

    def get(self, key):
        return self.cache[key.decode('utf-8')]

    def start(self):
        self.rep.bind(self.rep_address)

        for i in range(self.messages):
            message_data = self.rep.recv()
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
                            # This is a little exception for the cache to accept
                            # a value
                            if message.HasField('cache'):
                                result = user_function(message.payload,
                                                       message.cache)
                            else:
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
            self.rep.send(message.SerializeToString())


class Master(ServerTemplate, BaseMaster):
    """
    Standalone master server, intended to send workload to workers.
    WARNING. This implementation is not using the resilience service.

    :param name: Name of the server
    :param pull_address: Valid address for the pull service
    :param pub_address: Valid address for the pub service
    :param worker_pull_address: Valid address for the pull-from-workers service
    :param worker_push_address: Valid address for the push-to-workers service
    :param db_address: Valid address to bind the Cache service
    :param log_address: Address of the centralized logging service
    :param perf_address: Address of the centralized performance counter service
    :param ping_address: Address of the centralized health service
    :param cache: Key-value embeddable database. Pick from one of the supported ones
    :param palm: If messages are of the PALM kind
    :param debug_level: Logging level
    """
    def __init__(self, name: str, pull_address: str, pub_address: str,
                 worker_pull_address: str, worker_push_address: str, db_address: str,
                 log_address: str = None, perf_address: str = None,
                 ping_address: str = None, cache: object = DictDB(),
                 debug_level: int = logging.INFO):
        """
        """
        super(Master, self).__init__(ping_address, log_address, perf_address,
                                     logging_level=debug_level)
        self.name = name
        self.palm = True
        self.cache = cache
        self.cache.set('name', self.name.encode('utf-8'))
        self.cache.set('pull_address', pull_address.encode('utf-8'))
        self.cache.set('pub_address', pub_address.encode('utf-8'))
        self.cache.set('worker_pull_address', worker_pull_address.encode('utf-8'))
        self.cache.set('worker_push_address', worker_push_address.encode('utf-8'))

        self.register_inbound(PullService, 'Pull', pull_address,
                              route='WorkerPush', log='to_broker')
        self.register_inbound(WorkerPullService, 'WorkerPull', worker_pull_address,
                              route='Pub', log='from_broker')
        self.register_outbound(WorkerPushService, 'WorkerPush', worker_push_address,
                               log='to_broker')
        self.register_outbound(PubService, 'Pub', pub_address,
                               log='to_sink')
        self.register_bypass(CacheService, 'Cache', db_address)

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
    :param log_address: Address for the log service. If left blank, it logs to screen
    :param perf_address: Address for the performance counting service. If left blank, it logs to screen.
    :param ping_address: Address for the health monitoring service.
    :param log_level: Log level for this server.
    :param messages: Number of messages befor it is shut down.
    """
    def __init__(self, name, db_address, push_address=None, pull_address=None,
                 log_address=None, perf_address=None, ping_address=None,
                 log_level=logging.INFO, messages=sys.maxsize):
        self.name = name
        self.uuid = str(uuid4())

        # Configure the log handler
        if log_address:
            handler = PushHandler(log_address)
            self.logger = logging.getLogger(name)
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)

        else:
            self.logger = logging.getLogger(name=name)
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)

        # Configure the performance counter
        if perf_address:
            self.perfcounter = PerformanceCounter(listen_address=perf_address)

        # Configure the connections.
        self.push_address = push_address
        self.pull_address = pull_address

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

        # Configure the pinger.
        if ping_address:
            self.pinger = Pinger(listen_address=ping_address, every=30.0)

            # This is the pinger thread that keeps the pinger alive.
            pinger_thread = Thread(target=self.pinger.start)
            pinger_thread.daemon = True
            pinger_thread.start()

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
