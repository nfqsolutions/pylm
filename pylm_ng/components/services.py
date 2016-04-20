# The difference between connections and services is that connections
# connect, while services bind.

import zmq
import sys
from pylm_ng.components.core import ComponentInbound


class RepService(ComponentInbound):
    """
    RepService binds to a given socket and returns something.
    """
    def __init__(self, name, listen_address, broker_address="inproc://broker", palm=False,
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param palm: True if the service gets PALM messages. False if they are binary
        :param messages: Maximum number of messages. Defaults to infinity
        :return:
        """
        super(RepService, self).__init__(
            name,
            listen_address,
            zmq.REP,
            reply=True,
            broker_address=broker_address,
            bind=True,
            palm=palm,
            logger=logger,
            messages=messages
        )


class PullService(ComponentInbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self, name, listen_address, broker_address="inproc_//broker", palm=False,
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param palm: True if service gets PALM messages. False if they are binary
        :param messages: Maximum number of messages. Defaults to infinity.
        :return:
        """
        super(PullService, self).__init__(
            name,
            listen_address=listen_address,
            socket_type=zmq.PULL,
            reply=False,
            broker_address=broker_address,
            bind=True,
            palm=palm,
            logger=logger,
            messages=messages
        )

