from pylm_ng.components.core import Broker
from pylm_ng.components.utils import PushHandler, Pinger, PerformanceCounter
from pylm_ng.components.services import RepService
from pylm_ng.components.messages_pb2 import PalmMessage
import logging

# Standalone servers use some of the infrastructure of PALM, but they
# are not run-time configurable. You have to wire the connections yourself,
# but on the other hand, hou have a broker you can use for whatever you
# want, the logger and the performance counter, and a convenient endpoint
# for these services.


class StandaloneServer(object):
    """
    Standalone and minimal server that does not interact with the registry.
    It only offers a REP socket for anyone to connect. It still has a broker.
    Mostly for testing purposes and to implement dumb workers.
    """
    def __init__(self, name, rep_address, log_address, perf_address,
                 ping_address, debug_level=logging.DEBUG):
        self.name = name
        self.cache = {}  # The simplest possible cache

        # Configure the log handler
        handler = PushHandler(log_address)
        self.logger = logging.getLogger(name)
        self.logger.addHandler(handler)
        self.logger.setLevel(debug_level)

        # Configure the performance counter
        self.perfcounter = PerformanceCounter(listen_address=perf_address)

        # Configure the pinger.
        self.pinger = Pinger(listen_address=ping_address,
                             every=1.0)

        # Configure the broker, although probably it is never used.
        self.broker = Broker(logger=self.logger,
                             cache=self.cache)

        # Configure the rep connection that binds and blocks.
        self.rep = RepService('name', rep_address)

        # This is the function storage
        self.user_functions = {}

    def register_function(self, function):
        self.user_functions[function.__name__] = function

    def start(self):
        message_data = self.rep.recv()
        self.logger.info('Got a message')

        message = PalmMessage


class StandaloneCluster(object):
    pass


class StandaloneWorker(object):
    pass