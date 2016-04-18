from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage
import zmq


class Client(object):
    def __init__(self, connection, server_name):
        self.req = zmq_context.socket(zmq.REQ)
        self.req.connect(connection)
        self.server_name = server_name

    def job(self, function, data):
        message = PalmMessage()
        message.pipeline = 'standalone'
        message.client = 'standalone'
        message.stage = 0
        message.function = '.'.join([self.server_name, function])
        message.payload = data
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload
