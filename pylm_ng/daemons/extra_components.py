from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage
from pylm_ng.persistence.etcd import Client
import zmq
import sys
import json


class EtcdPoller(object):
    """
    Component that polls an etcd http connection and sends the result
    to the broker
    """
    def __init__(self, name, key, function='update',
                 broker_address='inproc://broker',
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param key: Key of the dict to poll to
        :param broker_address: ZMQ address of the broker
        :param logger: Logger instance
        :param messages: Maximum number of messages. Intended for debugging.
        :return:
        """
        self.name = name.encode('utf-8')
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.logger = logger
        self.messages = messages
        self.key = key
        self.function = function
        self.etcd = Client()
        self.wait_index = 0

    def start(self):
        self.logger.info('Launch Compoment {}'.format(self.name))
        for i in range(self.messages):
            self.logger.debug('Waiting for etcd')
            if self.wait_index > 0:
                response = self.etcd.wait(self.key, wait_index=self.wait_index)
            else:
                response = self.etcd.wait(self.key)

            self.wait_index = response['node']['modifiedIndex']+1
            self.logger.debug('New wait index: {}'.format(self.wait_index))
            message = PalmMessage()
            message.function = self.function
            message.pipeline = ''
            message.stage = 0
            message.client = 'EtcdPoller'
            message.payload = json.dumps(response).encode('utf-8')
            # Build the PALM message that tells what to do with the data
            self.broker.send(message.SerializeToString())
            # Just unblock
            self.logger.debug('blocked waiting broker')
            self.broker.recv()
            self.logger.debug('Got response from broker')

