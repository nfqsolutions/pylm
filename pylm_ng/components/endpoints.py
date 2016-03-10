# Collection of test endpoints for components.
import logging
import sys
import zmq
from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage

# A logger
logger = logging.getLogger('test-pylm_ng')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class ReqEndpoint(object):
    """
    Request endpoint to test Rep to broker components
    """
    def __init__(self, bind_address='inproc://ReqEndPoint', logger=None):
        self.socket = zmq_context.socket(zmq.REQ)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.logger = logger

    def start(self, function='none', payload=b'0', nmessages=10):
        """
        Start the endpoint, sending several test messages
        :param function: User defined function to call
        :param payload: Payload to send within the message
        :param nmessages: Number of test messages to send.
        :return: No return value
        """
        if self.logger:
            self.logger.info('Launch endpoint')

        for i in range(nmessages):
            message = PalmMessage()
            message.function = function
            message.pipeline = 'none'
            message.stage = 0
            message.client = 'none'
            message.payload = payload
            self.socket.send(message.SerializeToString())
            self.socket.recv()

            self.logger.info('Got #{} message back'.format(i+1))

        self.logger.info("Everything went fine")
        self.logger.info("********************")


class PushEndPoint(object):
    """
    Push endpoint to test pull to broker components
    """
    def __init__(self, bind_address='inproc://PushEndPoint', logger=None):
        self.socket = zmq_context.socket(zmq.PUSH)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.logger = logger

    def start(self, function='none', payload=b'0', nmessages=10):
        """
        Start the endpoint, sending several test messages
        :param function: User defined function to call
        :param payload: Payload to send within the message
        :param nmessages: Number of test messages to send.
        :return: No return value
        """
        if self.logger:
            self.logger.info('Launch endpoint PushEndpoint')

        for i in range(nmessages):
            self.logger.debug('Message #{} sent'.format(i))
            message = PalmMessage()
            message.function = function
            message.pipeline = 'none'
            message.stage = 0
            message.client = 'none'
            message.payload = payload
            self.socket.send(message.SerializeToString())

        self.logger.info("All messages sent")


class PullEndPoint(object):
    """
    Pull endpoint to test broker to push components
    """
    def __init__(self, bind_address='inproc://PullEndPoint', logger=None):
        self.socket = zmq_context.socket(zmq.PULL)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.logger = logger

    def start(self, nmessages=10):
        """
        Start the endpoint, receiving some messages
        :param nmessages: Number of test messages to send.
        :return: No return value
        """
        if self.logger:
            self.logger.info('Launch endpoint Pull Endpoint')

        for i in range(nmessages):
            self.logger.info('Pull endpoint waiting for messages')
            self.socket.recv()
            self.logger.info('Got #{} message back in pull endpoint'.format(i+1))

        self.logger.info("Everything went fine")
