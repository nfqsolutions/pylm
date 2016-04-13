from pylm_ng.components.core import Broker
from pylm_ng.components.utils import PushHandler, Pinger, PerformanceCounter
from pylm_ng.components.services import RepService
import logging


class StandaloneServer(object):
    """
    Standalone and minimal server that does not interact with the registry.
    Mostly for testing purposes and to implement dumb workers.
    """
    def __init__(self, name, rep_address, log_address, perf_address,
                 ping_address, debug_level=logging.DEBUG):
        self.name = name

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
        self.broker = Broker(logger=self.logger)

        # Configure the rep connection that binds and blocks.
        self.rep = RepService('name', rep_address)
