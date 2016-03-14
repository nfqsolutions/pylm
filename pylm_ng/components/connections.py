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


class PubConnection(ComponentBypassOutbound):
    """
    Generic connection that sends a message to a sub service. Good for logs.
    """
    def __init__(self, name, listen_to, socket_type, logger=None):
        """
        :param name: Name of the connection
        :param listen_to: ZMQ socket address to listen to.
        :param socket_type:  ZMQ Outbound socket type
        :param logger: Logger instance
        :return:
        """