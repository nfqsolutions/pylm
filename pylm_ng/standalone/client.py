from pylm_ng.components.core import zmq_context
from pylm_ng.components.messages_pb2 import PalmMessage
import zmq
from uuid import uuid4


class Client(object):
    def __init__(self, connection, server_name):
        self.req = zmq_context.socket(zmq.REQ)
        self.req.connect(connection)
        self.server_name = server_name
        self.uuid = str(uuid4())

    def set(self, data):
        """
        Sets some data in the server's internal cache.
        :param data: Data to be cached.
        :return: UUID of the key
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, 'set'])
        message.payload = data
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload

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
        message.function = '.'.join([self.server_name, 'delete'])
        message.payload = key
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload

    def call(self, function, data):
        """
        RPC function with data
        :param function: Function name as string, already defined in the server
        :param data: Binary message to be sent as argument
        :return: Result
        """
        message = PalmMessage()
        message.pipeline = str(uuid4())
        message.client = self.uuid
        message.stage = 0
        message.function = '.'.join([self.server_name, function])
        message.payload = data
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        return message.payload
