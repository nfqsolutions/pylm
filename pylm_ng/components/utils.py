from pylm_ng.components.connections import PushBypassConnection
from pylm_ng.components.core import zmq_context
from logging import Handler, Formatter, NOTSET
import zmq
import sys
import time


class PushHandler(Handler):
    def __init__(self, listen_address):
        """
        :param name:
        :param address:
        :param level:
        :return:
        """
        self.connection = PushBypassConnection('PushLogger', listen_address=listen_address)
        super(PushHandler, self).__init__(level=NOTSET)
        self.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        self.connection.send(self.format(record).encode('utf-8'))


class LogCollector(object):
    """
    Endpoint for log collection
    """
    def __init__(self, bind_address='inproc://LogCollector'):
        self.socket = zmq_context.socket(zmq.PULL)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.nlog = 0

    def start(self, messages=sys.maxsize):
        """
        Starts the log collector
        :param messages: Number of messages allowed. Used for debugging.
        :return:
        """
        for i in range(messages):
            self.emit(self.socket.recv())

    def emit(self, log_item):
        """
        Emits the message. At this point it is a stupid print
        :param log_item:
        :return:
        """
        self.nlog += 1
        print('LOG ENTRY #{:<8}:'.format(self.nlog), log_item.decode('utf-8'))


class PerformanceCounter(PushBypassConnection):
    """
    Class to record and to send performance counters to an external service.
    """
    def __init__(self, listen_address):
        super(PerformanceCounter, self).__init__('perfcounter', listen_address)
        if sys.version_info[0] < 3:
            if sys.platform == 'win32':
                self.timer = time.clock
            else:
                self.timer = time.time
        else:
            self.timer = time.perf_counter

        self.zero = self.timer()

    def tick(self, label):
        self.send('{}: {}'.format(label, self.timer()-self.zero).encode('utf-8'))


class PerformanceCollector(object):
    """
    Endpoint for log collection
    """
    def __init__(self, bind_address='inproc://PerformenceCollector'):
        self.socket = zmq_context.socket(zmq.PULL)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.nlog = 0

    def start(self, messages=sys.maxsize):
        """
        Starts the performance counter collector
        :param messages: Number of messages allowed. Used for debugging.
        :return:
        """
        for i in range(messages):
            self.emit(self.socket.recv())

    def emit(self, perfcounter):
        """
        Emits the performance counter. At this point it is a stupid print
        :param log_item:
        :return:
        """
        self.nlog += 1
        print('TICK #{:<8}:'.format(self.nlog), perfcounter.decode('utf-8'))


class Pinger(PushBypassConnection):
    """
    Pinger that is used for centralized heartbeat service. It has to be
    launched in a thread
    """
    def __init__(self, listen_address, every=1, pings=sys.maxsize):
        """
        :param listen_address: Address of the heartbeat collector
        :param every: Ping every n seconds
        :return:
        """
        super(Pinger, self).__init__('pinger', listen_address=listen_address)
        self.pings = pings
        self.every = every

    def start(self):
        for i in range(self.pings):
            time.sleep(self.every)
            self.send(b'ping')
