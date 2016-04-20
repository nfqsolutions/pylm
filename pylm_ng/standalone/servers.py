from pylm_ng.components.core import zmq_context
from pylm_ng.components.utils import PushHandler, Pinger, PerformanceCounter
from pylm_ng.components.messages_pb2 import PalmMessage
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

    def set(self, data):
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
    pass


class Worker(object):
    """
    Standalone worker for the standalone master.
    """
    def __init__(self, name, pull_address, push_address,
                 log_address, perf_address,
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

        # Configure the push and pull connections.
        self.pull = zmq_context.socket(zmq.PULL)
        self.pull.connect(pull_address)
        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(push_address)

        self.messages = messages

        # This is the pinger thread that keeps the pinger alive.
        pinger_thread = Thread(target=self.pinger.start)
        pinger_thread.daemon = True
        pinger_thread.start()


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
                    self.logger.info('Loking for {}'.format(function))
                    try:
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
