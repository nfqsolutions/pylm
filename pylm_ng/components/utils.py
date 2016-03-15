from pylm_ng.components.connections import PushBypassConnection
from pylm_ng.components.core import zmq_context
from logging import Handler, Formatter, NOTSET
import zmq
import sys


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
