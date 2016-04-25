# The difference between connections and services is that connections
# connect, while services bind.
from pylm_ng.components.core import ComponentInbound, ComponentOutbound, zmq_context
from pylm_ng.components.messages_pb2 import BrokerMessage
import zmq
import sys


class RepService(ComponentInbound):
    """
    RepService binds to a given socket and returns something.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
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
            cache=cache,
            messages=messages
        )


class PullService(ComponentInbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
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
            cache=cache,
            messages=messages
        )


class PushService(ComponentOutbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param palm: True if service gets PALM messages. False if they are binary
        :param messages: Maximum number of messages. Defaults to infinity.
        :return:
        """
        super(PushService, self).__init__(
            name,
            listen_address=listen_address,
            socket_type=zmq.PUSH,
            reply=False,
            broker_address=broker_address,
            bind=True,
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )


class WorkerPushService(PushService):
    """
    This is a particular push service that does not modify the messages that
    the broker sends.
    """
    def _translate_from_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data

    def _translate_to_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data


class WorkerPullService(PullService):
    """
    This is a particular pull service that does not modify the messages that
    the broker sends.
    """
    def _translate_to_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data

    def _translate_from_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data


class PushPullService(object):
    """
    Push-Pull Service to connect to workers
    """
    def __init__(self,
                 name,
                 push_address,
                 pull_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param socket_type: ZMQ inbound socket type
        :param reply: True if the listening socket blocks waiting a reply
        :param broker_address: ZMQ socket address for the broker
        :param bind: True if socket has to bind, instead of connect.
        :param palm: True if the message is waiting is a PALM message. False if it is
          just a binary string
        :param logger: Logger instance
        :param cache: Cache for shared data in the server
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        self.name = name.encode('utf-8')

        self.push = zmq_context.socket(zmq.PUSH)
        self.pull = zmq_context.socket(zmq.PULL)
        self.push_address = push_address
        self.pull_address = pull_address
        self.push.bind(push_address)
        self.pull.bind(pull_address)

        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = self.name
        self.broker.connect(broker_address)

        self.palm = palm
        self.logger = logger
        self.cache = cache
        self.messages = messages

        self.last_message = b''

    def scatter(self, message_data):
        """
        To be overriden. Picks a message and returns a generator that multiplies the messages
        to the broker.
        :param message_data:
        :return:
        """
        yield message_data

    def handle_feedback(self, message_data):
        """
        To be overriden. Handles the feedback from the broker
        :param message_data:
        :return:
        """
        self.last_message = message_data

    def reply_feedback(self):
        """
        To be overriden. Returns the feedback if the component has to reply.
        :return:
        """
        return self.last_message

    def start(self):
        self.logger.info('Launch component {}'.format(self.name))
        initial_broker_message = BrokerMessage()
        initial_broker_message.key = '0'
        initial_broker_message.payload = b'0'
        self.broker.send(initial_broker_message.SerializeToString())

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
            # Workers use BrokerMessages, because they want to know the message ID.
            message_data = self.broker.recv()
            self.logger.debug('Got message {} from broker'.format(i))
            for scattered in self.scatter(message_data):
                self.push.send(scattered)
                self.handle_feedback(self.pull.recv())

            self.broker.send(self.reply_feedback())

    def cleanup(self):
        self.push.close()
        self.pull.close()
        self.broker.close()
