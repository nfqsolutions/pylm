from pylm_ng.components.core import zmq_context, Broker
from pylm_ng.components.services import WorkerPullService, WorkerPushService
from pylm_ng.components.services import PullService, PushService
from pylm_ng.components.utils import PushHandler, Pinger, PerformanceCounter, CacheService
from pylm_ng.components.messages_pb2 import PalmMessage, BrokerMessage
from pylm_ng.persistence.kv import DictDB
from google.protobuf.message import DecodeError
from threading import Thread
from uuid import uuid4
import logging
import zmq
import sys

# Standalone servers use some of the infrastructure of PALM, but they
# are not run-time configurable. You have to wire the connections yourself,
# but on the other hand, hou have a logger and the performance counter, and
# a convenient endpoint for these services.


class Server(object):
    """
    Standalone and minimal server that does not interact with the registry.
    It only offers a REP socket for anyone to connect. It still has a broker.
    Mostly for testing purposes and to implement dumb workers.
    """
    def __init__(self, name, rep_address, log_address, perf_address,
                 ping_address, debug_level=logging.DEBUG,
                 messages=sys.maxsize):
        self.name = name
        self.cache = {}  # The simplest possible cache

        # Configure the log handler
        handler = PushHandler(log_address)
        self.logger = logging.getLogger(name)
        self.logger.addHandler(handler)
        self.logger.setLevel(debug_level)

        # Configure the performance counter
        self.perfcounter = PerformanceCounter(listen_address=perf_address)

        # Configure the pinger.
        self.pinger = Pinger(listen_address=ping_address,
                             every=10.0)

        # Configure the rep connection that binds and blocks.
        self.rep = zmq_context.socket(zmq.REP)
        self.rep.bind(rep_address)

        # This is the function storage
        self.user_functions = {}

        self.messages = messages

        # This is the pinger thread that keeps the pinger alive.
        pinger_thread = Thread(target=self.pinger.start)
        pinger_thread.daemon = True
        pinger_thread.start()

    def set(self, data, key=None):
        if not key:
            key = str(uuid4()).encode('utf-8')

        self.cache[key] = data
        return key

    def delete(self, key):
        del self.cache[key]
        return key

    def get(self, key):
        return self.cache[key]

    def start(self):
        for i in range(self.messages):
            message_data = self.rep.recv()
            self.logger.info('Got a message')
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
                        self.logger.info('Looking for {}'.format(function))
                        try:
                            # This is a little exception for the cache to accept
                            # a value
                            if message.hasField('cache'):
                                result = user_function(message.payload, message.cache)
                            else:
                                result = user_function(message.payload)
                        except:
                            self.logger.error('User function gave an error')
                    except KeyError:
                        self.logger.error(
                            'Function {} was not found'.format(function)
                        )
            except DecodeError:
                self.logger.error('Message could not be decoded')

            message.payload = result
            self.rep.send(message.SerializeToString())


class Master(object):
    """
    Standalone master server, intended to send workload to workers
    """
    def __init__(self, name, pull_address, push_address,
                 worker_pull_address, worker_push_address,
                 log_address, perf_address, ping_address,
                 palm=False, cache=DictDB(), debug_level=logging.DEBUG):
        self.name = name

        # Addresses:
        self.pull_address = pull_address
        self.push_address = push_address
        self.worker_pull_address = worker_pull_address
        self.worker_push_address = worker_push_address

        # Configure the log handler
        handler = PushHandler(log_address)
        self.logger = logging.getLogger(name)
        self.logger.addHandler(handler)
        self.logger.setLevel(debug_level)

        # Handle that controls if the messages have to be processed
        self.palm = palm

        # Configure the performance counter
        self.perfcounter = PerformanceCounter(listen_address=perf_address)

        # Configure the pinger.
        self.pinger = Pinger(listen_address=ping_address, every=10.0)

        # Configure the broker and the connectors
        self.broker = Broker(logger=self.logger)
        self.pull_service = PullService(
            'Pull',
            pull_address,
            broker_address=self.broker.inbound_address,
            logger=self.logger,
            palm=palm,
            cache=cache)
        self.push_service = PushService(
            'Push',
            push_address,
            broker_address=self.broker.outbound_address,
            logger=self.logger,
            palm=palm,
            cache=cache)
        self.worker_pull_service = WorkerPullService(
            'WorkerPull',
            worker_pull_address,
            broker_address=self.broker.inbound_address,
            logger=self.logger,
            palm=palm,
            cache=cache)
        self.worker_push_service = WorkerPushService(
            'WorkerPush',
            worker_push_address,
            broker_address=self.broker.outbound_address,
            logger=self.logger,
            palm=palm,
            cache=cache)

        self.broker.register_inbound('Pull', route='WorkerPush', log='to_broker')
        self.broker.register_inbound('WorkerPull', route='Push', log='from_broker')
        self.broker.register_outbound('WorkerPush', log='to_broker')
        self.broker.register_outbound('Push', log='to_sink')

        # This is the pinger thread that keeps the pinger alive.
        pinger_thread = Thread(target=self.pinger.start)
        pinger_thread.daemon = True
        pinger_thread.start()

    def start(self):
        threads = [
            Thread(target=self.broker.start),
            Thread(target=self.push_service.start),
            Thread(target=self.pull_service.start),
            Thread(target=self.worker_push_service.start),
            Thread(target=self.worker_pull_service.start)
        ]
        for t in threads:
            t.daemon = True
            t.start()


class Worker(object):
    """
    Standalone worker for the standalone master.
    """
    def __init__(self, name, push_address, pull_address, db_address,
                 log_address, perf_address, ping_address,
                 debug_level=logging.DEBUG, messages=sys.maxsize):
        self.name = name
        self.cache = DictDB()

        # Configure the log handler
        handler = PushHandler(log_address)
        self.logger = logging.getLogger(name)
        self.logger.addHandler(handler)
        self.logger.setLevel(debug_level)

        # Configure the performance counter
        self.perfcounter = PerformanceCounter(listen_address=perf_address)

        # Configure the pinger.
        self.pinger = Pinger(listen_address=ping_address, every=10.0)

        # Configure the push and pull connections.
        self.push_address = push_address
        self.pull = zmq_context.socket(zmq.PULL)
        self.pull.connect(push_address)

        self.pull_address = pull_address
        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(pull_address)

        self.db_address = db_address
        self.cache_service = CacheService(self.name,
                                          db_address,
                                          self.logger,
                                          cache=self.cache)

        self.messages = messages

        # This is the pinger thread that keeps the pinger alive.
        pinger_thread = Thread(target=self.pinger.start)
        pinger_thread.daemon = True
        pinger_thread.start()

    def start(self):
        for i in range(self.messages):
            message_data = self.pull.recv()
            self.logger.info('{} Got a message'.format(self.name))
            result = b'0'
            message = BrokerMessage()
            try:
                message.ParseFromString(message_data)
                instruction = message.instruction
                try:
                    user_function = getattr(self, instruction)
                    self.logger.info('Looking for {}'.format(instruction))
                    try:
                        result = user_function(message.payload)
                    except:
                        self.logger.error('{} User function gave an error'.format(self.name))
                except AttributeError:
                    self.logger.error('Function {} was not found'.format(instruction))
            except DecodeError:
                self.logger.error('Message could not be decoded')

            message.payload = result
            self.push.send(message.SerializeToString())
