import zmq
import sys
import concurrent.futures
from pylm.components.core import ComponentInbound, ComponentOutbound, \
    ComponentBypassInbound, ComponentBypassOutbound, zmq_context
from urllib.request import Request, urlopen


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


class HttpConnection(ComponentOutbound):
    """
    Similar to PushConnection. An HTTP client deals with outbound messages.
    """
    def __init__(self,
                 name,
                 listen_address,
                 reply=True,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 max_workers=4,
                 messages=sys.maxsize):
        self.name = name.encode('utf-8')
        self.broker = zmq_context.socket(zmq.REP)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.logger = logger
        self.palm = palm
        self.cache = cache
        self.messages = messages
        self.reply = reply
        self.last_message = b''
        self.url = listen_address
        self.max_workers = max_workers

    def start(self):
        """
        Call this function to start the component
        """
        def load_url(url, data):
            request = Request(url, data=data)
            response = urlopen(request)
            return response.read()

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
            message_data = self.broker.recv()
            self.logger.debug('Component {} Got message from broker'.format(self.name))
            message_data = self._translate_from_broker(message_data)

            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to = [executor.submit(load_url,
                                             self.url,
                                             scattered
                                             ) for scattered in self.scatter(message_data)]
                for future in concurrent.futures.as_completed(future_to):
                    try:
                        feedback = future.result()
                    except Exception as exc:
                        self.logger.error('HttpConnection generated an error')
                        feedback = b'0'

                    if self.reply:
                        feedback = self._translate_to_broker(feedback)
                        self.handle_feedback(feedback)

            self.broker.send(self.reply_feedback())
