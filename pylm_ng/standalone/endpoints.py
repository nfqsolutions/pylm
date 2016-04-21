from pylm_ng.components.core import zmq_context
import zmq
import sys


class EndPoint(object):
    def __init__(self, name, log_address, perf_address, ping_address,
                 messages=sys.maxsize):
        self.poller = zmq.Poller()
        self.name = name

        self.log_address = log_address
        self.logs = zmq_context.socket(zmq.PULL)
        self.logs.bind(log_address)

        self.perf_address = perf_address
        self.perf = zmq_context.socket(zmq.PULL)
        self.perf.bind(perf_address)

        self.ping_address = ping_address
        self.ping = zmq_context.socket(zmq.PULL)
        self.ping.bind(ping_address)

        self.poller.register(self.logs, zmq.POLLIN)
        self.poller.register(self.perf, zmq.POLLIN)
        self.poller.register(self.ping, zmq.POLLIN)

        self.messages = messages

    def _start_debug(self):
        for i in range(self.messages):
            event = dict(self.poller.poll())

            if self.logs in event:
                print('LOG:', self.logs.recv())

            elif self.perf in event:
                print('PRF:', self.perf.recv())

            elif self.ping in event:
                print('PNG:', self.ping.recv())
