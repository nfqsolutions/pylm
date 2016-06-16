import zmq
import sys
from pylm.components.core import ComponentInbound, ComponentOutbound, \
    ComponentBypassInbound, ComponentBypassOutbound


class RepConnection(ComponentInbound):
    """
    RepConnection is a component that connects a REQ socket to the broker, and a REP
    socket to an external service.
    """
    def __init__(self, name, listen_address, broker_address="inproc://broker", palm=False,
                 logger=None, cache=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param broker_address: ZMQ socket address for the broker
        :param palm: True if the connection will get PALM messages. False if they are binary
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        super(RepConnection, self).__init__(
            name,
            listen_address,
            zmq.REP,
            reply=True,
            broker_address=broker_address,
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PullConnection(ComponentInbound):
    """
    PullConnection is a component that connects a REQ socket to the broker, and a PULL
    socket to an external service.
    """
    def __init__(self, name, listen_address, broker_address="inproc://broker", palm=False,
                 logger=None, cache=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param broker_address: ZMQ socket address for the broker
        :param palm: True if the connection will get PALM messages. False if they are binary.
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        super(PullConnection, self).__init__(
            name,
            listen_address,
            zmq.PULL,
            reply=False,
            broker_address=broker_address,
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PushConnection(ComponentOutbound):
    """
    PushConnection is a component that connects a REQ socket to the broker, and a PUSH
    socket to an external service.
    """
    def __init__(self, name, listen_address, broker_address="inproc://broker", palm=False,
                 logger=None, cache=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param broker_address: ZMQ socket address for the broker
        :param palm: True if the component gets a PALM message. False if it is binary
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        super(PushConnection, self).__init__(
            name,
            listen_address,
            zmq.PUSH,
            reply=False,
            broker_address=broker_address,
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PushBypassConnection(ComponentBypassOutbound):
    """
    Generic connection that sends a message to a sub service. Good for logs or metrics.
    """
    def __init__(self, name, listen_address, logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param listen_address: ZMQ socket address to listen to.
        :param logger: Logger instance
        :return:
        """
        super(PushBypassConnection, self).__init__(name, listen_address, zmq.PUSH,
                                                   reply=False, bind=False,
                                                   logger=logger)


class PullBypassConnection(ComponentBypassInbound):
    """
    Generic connection that opens a Sub socket and bypasses the broker.
    """
    def __init__(self, name, listen_address, logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param listen_address: ZMQ socket address to listen to
        :param logger: Logger instance
        :param messages:
        :return:
        """
        super(PullBypassConnection, self).__init__(name, listen_address, zmq.PULL,
                                                   reply=False, bind=False,
                                                   logger=logger)


