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

import logging
import sys
import zmq
from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage

# A logger
logger = logging.getLogger('test-pylm')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class ReqEndPoint(object):
    """
    Request endpoint to test Rep to broker parts
    """
    def __init__(self, bind_address='inproc://ReqEndPoint', logger=None):
        self.socket = zmq_context.socket(zmq.REQ)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.logger = logger

    def start(self, function='none', payload=b'0', nmessages=10):
        """
        Start the endpoint, sending several test messages
        :param function: User defined function to job
        :param payload: Payload to send within the message
        :param nmessages: Number of test messages to send.
        :return: No return value
        """
        if self.logger:
            self.logger.info('Launch endpoint Req Endpoint')

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


class ReqConnection(object):
    """
    Request endpoint to test Rep to broker parts
    """
    def __init__(self, listen_to, logger=None):
        self.socket = zmq_context.socket(zmq.REQ)
        self.socket.connect(listen_to)
        self.listen_to = listen_to
        self.logger = logger

    def start(self, function='none', payload=b'0', nmessages=10):
        """
        Start the endpoint, sending several test messages
        :param function: User defined function to job
        :param payload: Payload to send within the message
        :param nmessages: Number of test messages to send.
        :return: No return value
        """
        if self.logger:
            self.logger.info('Launch endpoint Req Endpoint')

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
    Push endpoint to test pull to broker parts
    """
    def __init__(self, bind_address='inproc://PushEndPoint', logger=None):
        self.socket = zmq_context.socket(zmq.PUSH)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.logger = logger

    def start(self, function='none', payload=b'0', nmessages=10):
        """
        Start the endpoint, sending several test messages
        :param function: User defined function to job
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
    Pull endpoint to test broker to push parts
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
            m = self.socket.recv()
            self.logger.info('Got #{} message back in pull endpoint'.format(i+1))
            self.logger.info('pull: {}'.format(m))

        self.logger.info("Everything went fine")
        self.logger.info("********************")
