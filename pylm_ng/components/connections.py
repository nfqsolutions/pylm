import zmq
import sys
from pylm_ng.components.core import ComponentInbound, ComponentOutbound, \
    ComponentBypassInbound, ComponentBypassOutbound


class RepConnection(ComponentInbound):
    """
    ReqRep is a component that connects a REQ socket to the broker, and a REP
    socket to an external service.
    """
    def __init__(self, name, listen_to, broker_address="inproc://broker",
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_to: ZMQ socket address to listen to
        :param broker_address: ZMQ socket address for the broker
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        super(RepConnection, self).__init__(
            name,
            listen_to,
            zmq.REP,
            reply=True,
            broker_address=broker_address,
            logger=logger,
            messages=messages
        )


class PullConnection(ComponentInbound):
    """
    ReqRep is a component that connects a REQ socket to the broker, and a PULL
    socket to an external service.
    """
    def __init__(self, name, listen_to, broker_address="inproc://broker",
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_to: ZMQ socket address to listen to
        :param broker_address: ZMQ socket address for the broker
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        super(PullConnection, self).__init__(
            name,
            listen_to,
            zmq.PULL,
            reply=False,
            broker_address=broker_address,
            logger=logger,
            messages=messages
        )


class PushConnection(ComponentOutbound):
    """
    ReqPush is a component that connects a REQ socket to the broker, and a PUSH
    socket to an external service.
    """
    def __init__(self, name, listen_to, broker_address="inproc://broker",
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_to: ZMQ socket address to listen to
        :param broker_address: ZMQ socket address for the broker
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        super(PushConnection, self).__init__(
            name,
            listen_to,
            zmq.PUSH,
            reply=False,
            broker_address=broker_address,
            logger=logger,
            messages=messages
        )


class PushBypassConnection(ComponentBypassOutbound):
    """
    Generic connection that sends a message to a sub service. Good for logs.
    """
    def __init__(self, name, listen_to, logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param listen_to: ZMQ socket address to listen to.
        :param logger: Logger instance
        :return:
        """
        super(PushBypassConnection, self).__init__(name, listen_to, zmq.PUSH,
                                                  reply=False, bind=False,
                                                  logger=logger, messages=messages)


class PullBypassConnection(ComponentBypassInbound):
    """
    Generic connection that opens a Sub socket and bypasses the broker.
    """
    def __init__(self, name, listen_to, logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param listen_to: ZMQ socket address to listen to
        :param logger: Logger instance
        :param messages:
        :return:
        """
        super(PullBypassConnection, self).__init__(name, listen_to, zmq.PULL,
                                                  reply=False, bind=False,
                                                  logger=logger, messages=messages)
