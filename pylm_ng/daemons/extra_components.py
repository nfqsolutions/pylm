import requests
from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage


class EtcdPoller(object):
    """
    Component that polls an etcd http connection and sends the result
    to the broker
    """
    def __init__(self, name, url, broker_address='inproc://broker',
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param url: Url to poll to
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
        self.url = url

    def start(self):
        self.logger.info('Launch Compoment {}'.format(self.name))
        for i in range(self.messages):
            response = requests.get(self.url)
            print(response)
            message = PalmMessage()
            message.function('etcd_update')
            message.pipeline = ''
            message.stage = 0
            message.client = 'EtcdPoller'
            message.payload = response
            # Build the PALM message that tells what to do with the data
            self.broker.send(message.SerializeToString())
            # Just unblock
            self.broker.recv()

r