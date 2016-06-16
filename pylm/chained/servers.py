from pylm.persistence.kv import DictDB
from pylm.standalone import Worker
from pylm.standalone import Master as StandaloneMaster
from pylm.components.connections import PushConnection
import logging


# TODO: Implement a connected Server to be put in a push-pull queue.

class Master(StandaloneMaster):
    def __init__(self, name, pull_address, next_address,
                 worker_pull_address, worker_push_address, db_address,
                 log_address, perf_address, ping_address, cache=DictDB(),
                 palm=False, debug_level=logging.DEBUG):
        """
        Connected PALM master server. It gets a message from the pull socket, that
        is bind, and sends the result from the push socket connected to the next_address
        :param name: Name of the server
        :param pull_address: Pull address to be bind
        :param next_address: Push address to be connected to a Pull socket of the next server
        :param worker_pull_address: Pull address for the worker connection
        :param worker_push_address: Push address for the worker connection
        :param db_address: Persistency address to be bind
        :param log_address: Address of the log service to be connected to
        :param perf_address: Address of the performance counter collector
        :param ping_address: Address of the ping collector
        :param cache: Key-value database to be used internally
        :param palm: True if the message that is sent through the server is a PALM message
        :param debug_level: Debug level for logging
        """

        super(Master, self).__init__(name,
                                     pull_address,
                                     next_address,
                                     worker_pull_address,
                                     worker_push_address,
                                     db_address=db_address,
                                     log_address=log_address,
                                     perf_address=perf_address,
                                     ping_address=ping_address,
                                     cache=cache,
                                     palm=palm,
                                     debug_level=debug_level)

        # self.push_service = PushConnection(
        #     'Push',
        #     self.push_address,
        #     broker_address=self.broker.outbound_address,
        #     logger=self.logger,
        #     palm=self.palm,
        #     cache=self.cache
        # )
