import logging
from threading import Thread

import zmq

from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage
from pylm.standalone import Server, EndPoint

this_log_address = "inproc://log1"
this_perf_address = "inproc://perf1"
this_ping_address = "inproc://ping1"
this_rep_address = "inproc://rep1"


class DummyClient(object):
    def __init__(self, connection, server_name):
        self.req = zmq_context.socket(zmq.REQ)
        self.req.connect(connection)
        self.server_name = server_name

    def job(self, function, data):
        message = PalmMessage()
        message.pipeline = 'test'
        message.client = 'test'
        message.stage = 0
        message.function = '.'.join([self.server_name, function])
        message.payload = data
        print('Sending Message')
        self.req.send(message.SerializeToString())
        message.ParseFromString(self.req.recv())
        print('Got response')
        return message.payload


class RemoteServer(Server):
    def __init__(self, name, rep_address, log_address, perf_address,
                 ping_address, log_level=logging.DEBUG):
        super(RemoteServer, self).__init__(name,
                                           rep_address,
                                           log_address,
                                           perf_address,
                                           ping_address,
                                           log_level=log_level)

    def echo_data(self, data):
        """
        Simple function to test the standalone server.
        :param data:
        :return:
        """
        self.logger.info(data)
        return b'something'


def test_standalone():
    endpoint = EndPoint('EndPoint',
                        this_log_address,
                        this_perf_address,
                        this_ping_address)
    server = RemoteServer('Echo_server',
                          this_rep_address,
                          endpoint.log_address,
                          endpoint.perf_address,
                          endpoint.ping_address)

    client = DummyClient(this_rep_address, 'Echo_server')

    print('Starting')
    t1 = Thread(target=endpoint.start_debug)
    t1.daemon = True
    t1.start()

    t2 = Thread(target=server.start)
    t2.daemon = True
    t2.start()

    for i in range(1, 10):
        retval = client.job('echo_data', str(i).encode('utf-8'))
        print(retval)

if __name__ == '__main__':
    test_standalone()
