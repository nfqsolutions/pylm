from pylm.parts.messages_pb2 import PalmMessage, BrokerMessage
from uuid import uuid4
import zmq
import sys


zmq_context = zmq.Context.instance()


class Router(object):
    """
    Router for the internal event-loop. It is a ROUTER socket that blocks
    waiting for the parts to send something. This is more a bus than
    a broker.

    :param inbound_address: Valid ZMQ bind address for inbound parts
    :param outbound_address: Valid ZMQ bind address for outbound parts
    :param logger: Logger instance
    :param cache: Global cache of the server
    :param messages: Maximum number of inbound messages. Defaults to infinity.
    :param messages: Number of messages allowed before the router starts buffering.
    """
    def __init__(self,
                 inbound_address="inproc://inbound",
                 outbound_address="inproc://outbound",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        # Socket that will listen to the inbound parts
        self.inbound = zmq_context.socket(zmq.ROUTER)
        self.inbound.bind(inbound_address)
        self.inbound_address = inbound_address
        self.inbound_components = {}

        # Socket that listens to the outbound parts
        self.outbound = zmq_context.socket(zmq.ROUTER)
        self.outbound.bind(outbound_address)
        self.outbound_address = outbound_address
        self.outbound_components = {}

        # Other utilities
        self.logger = logger
        self.messages = messages

        # Cache for the server
        self.cache = cache

    def register_inbound(self, name, route='', block=False, log=''):
        """
        Register component by name.

        :param name: Name of the component. Each component has a name, that uniquely identifies it to the broker
        :param route: Each message that the broker gets from the component may be routed to another component. This argument gives the name of the target component for the message.
        :param block: Register if the component is waiting for a reply.
        :param log: Log message for each inbound connection.
        :return:
        """
        self.inbound_components[name.encode('utf-8')] = {
            'route': route.encode('utf-8'),
            'block': block,
            'log': log
        }

    def register_outbound(self, name, route='', log=''):
        """
        Register outbound component by name

        :param name: Name of the component
        :param route: Each message sent back to the component can be routed
        :param log: Logging for each message that comes from the router.
        :return:
        """
        self.outbound_components[name.encode('utf-8')] = {
            'route': route.encode('utf-8'),
            'log': log
        }

    def start(self):
        self.logger.info('Launch router')
        self.logger.info('Inbound socket: {}'.format(self.inbound))
        self.logger.info('Inbound parts: {}'.format(self.inbound_components))
        self.logger.info('Outbound socket: {}'.format(self.outbound))
        self.logger.info('Outbound parts: {}'.format(self.outbound_components))

        for i in range(self.messages):
            component, empty, message_data = self.inbound.recv_multipart()

            # Routing from inbound to outbound
            route_to = self.inbound_components[component]['route']
            block = self.inbound_components[component]['block']

            if route_to:
                self.logger.debug('Router: {} routing to {}'.format(component, route_to))
                self.outbound.send_multipart([route_to, empty, message_data])
                try:
                    route_to, empty, feedback = self.outbound.recv_multipart()
                except:
                    self.logger.error('Message badly formatted from {}'.format(route_to))
                    # And now drop the message
                    continue

                # Rerouting from outbound to a different outbound.
                # You can reroute only once, and if inbound blocks it gets
                # the message from the first outbound. This can be used to
                # implement weird routing schemes.
                reroute = self.outbound_components[route_to]['route']
                if reroute:
                    self.outbound.send_multipart([reroute, empty, feedback])
                    self.outbound.recv_multipart()

                # The inbound is blocked, but sometimes it can process the
                # feedback. You can use this to remove the block thing, because
                # now you can redirect from outbound to outbound.
                if block:
                    self.inbound.send_multipart([component, empty, feedback])
                else:
                    self.inbound.send_multipart([component, empty, b'1'])
            else:
                self.inbound.send_multipart([component, empty, b'1'])

    def cleanup(self):
        self.inbound.close()
        self.outbound.close()


class ComponentInbound(object):
    """
    Generic component that connects a REQ socket to the broker, and a
    socket to an inbound external service.

    :param name: Name of the component
    :param listen_address: ZMQ socket address to listen to
    :param socket_type: ZMQ inbound socket type
    :param reply: True if the listening socket blocks waiting a reply
    :param broker_address: ZMQ socket address for the broker
    :param bind: True if socket has to bind, instead of connect.
    :param palm: True if the message is waiting is a PALM message. False if it is just a binary string
    :param logger: Logger instance
    :param cache: Cache for shared data in the server
    :param messages: Maximum number of inbound messages. Defaults to infinity.
    """
    def __init__(self,
                 name,
                 listen_address,
                 socket_type,
                 reply=True,
                 broker_address="inproc://broker",
                 bind=False,
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        self.name = name.encode('utf-8')
        self.listen_to = zmq_context.socket(socket_type)
        self.bind = bind
        self.listen_address = listen_address
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.palm = palm
        self.logger = logger
        self.cache = cache
        self.messages = messages
        self.reply = reply
        self.last_message = b''

    def _translate_to_broker(self, message_data):
        """
        Translate the message that the component has got to be digestible by the router.
        To be refactored

        :param message_data: Message data from the component to the router
        """
        if self.palm:
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            payload = palm_message.payload
            instruction = palm_message.function.split('.')[1]
            pipeline = palm_message.pipeline

            if palm_message.HasField('cache'):
                broker_message_key = ''.join(['_', palm_message.pipeline, palm_message.cache])
            else:
                broker_message_key = str(uuid4())

            # I store the message to get it later when the message is outbound. See that
            # if I am just sending binary messages, I do not need to assign any envelope.

            # The same message cannot be used, because it confuses the router.
            if broker_message_key in self.cache:
                new_key = ''.join([broker_message_key, str(uuid4())[:8]])
                self.logger.error(
                    'Message key {} found, changed to {}'.format(broker_message_key,
                                                                 new_key)
                )
                broker_message_key = new_key

            self.logger.debug('Set message key {}'.format(broker_message_key))
            self.cache.set(broker_message_key, message_data)
        else:
            broker_message_key = str(uuid4())
            payload = message_data
            instruction = ''
            pipeline = ''

        broker_message = BrokerMessage()
        broker_message.key = broker_message_key
        broker_message.instruction = instruction
        broker_message.payload = payload
        broker_message.pipeline = pipeline

        return broker_message.SerializeToString()

    def _translate_from_broker(self, message_data):
        """
        Translate the message that the component gets from the router to the output format

        :param message_data: Data from the router
        """
        broker_message = BrokerMessage()
        broker_message.ParseFromString(message_data)

        if self.palm:
            message_data = self.cache.get(broker_message.key)
            # Clean up the cache. It is an outbound message and
            # the metadata is not necessary anymore. This may cause
            # double deletions, so be ready to manage the messages
            # yourself. Note this may cause memory leaks in the cache.
            self.logger.debug('DELETE: {}'.format(broker_message.key))
            self.cache.delete(broker_message.key)
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            palm_message.payload = broker_message.payload
            message_data = palm_message.SerializeToString()

        else:
            message_data = broker_message.payload

        return message_data

    def scatter(self, message_data):
        """
        Abstract method. Picks a message and returns a generator that multiplies the messages
        to the broker.

        :param message_data:
        """
        yield message_data

    def handle_feedback(self, message_data):
        """
        Abstract method. Handles the feedback from the broker

        :param message_data:
        """
        self.last_message = message_data

    def reply_feedback(self):
        """
        Abstract method. Returns the feedback if the component has to reply.
        """
        return self.last_message

    def start(self):
        """
        Call this function to start the component
        """
        if self.bind:
            self.listen_to.bind(self.listen_address)
        else:
            self.listen_to.connect(self.listen_address)

        self.logger.info('Launch component {}'.format(self.name))
        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting messages'.format(self.name))
            message_data = self.listen_to.recv()
            self.logger.debug('{} Got inbound message'.format(self.name))
            scattered_messages = self.scatter(message_data)

            if not scattered_messages:
                if self.reply:
                    self.listen_to.send(b'0')

                continue

            for scattered in scattered_messages:
                scattered = self._translate_to_broker(scattered)
                # The translation may delete the message. E.g. the WorkerPull case
                if scattered:
                    self.broker.send(scattered)
                    self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
                    self.handle_feedback(self.broker.recv())

            if self.reply:
                self.listen_to.send(self.reply_feedback())

    def cleanup(self):
        self.broker.close()
        self.listen_to.close()


class ComponentOutbound(object):
    """
    Generic component that connects a REQ socket to the broker, and a
    socket to an inbound external service.

    :param name: Name of the component
    :param listen_address: ZMQ socket address to listen to
    :param socket_type: ZMQ inbound socket type
    :param reply: True if the listening socket blocks waiting a reply
    :param broker_address: ZMQ socket address for the broker,
    :param bind: True if the socket has to bind instead of connect.
    :param palm: The component is sending back a Palm message
    :param logger: Logger instance
    :param cache: Access to the cache of the server
    :param messages: Maximum number of inbound messages. Defaults to infinity.
    """
    def __init__(self,
                 name,
                 listen_address,
                 socket_type,
                 reply=True,
                 broker_address="inproc://broker",
                 bind=False,
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        self.name = name.encode('utf-8')
        self.listen_to = zmq_context.socket(socket_type)
        self.bind = bind
        self.listen_address = listen_address
        self.broker = zmq_context.socket(zmq.REP)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.logger = logger
        self.palm = palm
        self.cache = cache
        self.messages = messages
        self.reply = reply
        self.last_message = b''

    def _translate_to_broker(self, message_data):
        """
        Translate the message that the component has got to be digestible by the broker
        :param message_data:
        :return:
        """
        broker_message_key = str(uuid4())
        if self.palm:
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            payload = palm_message.payload
            instruction = palm_message.function.split('.')[1]
            pipeline = palm_message.pipeline

            # I store the message to get it later when the message is outbound. See that
            # if I am just sending binary messages, I do not need to assign any envelope.
            self.cache.set(broker_message_key, message_data)
        else:
            payload = message_data
            instruction = ''
            pipeline = ''

        broker_message = BrokerMessage()
        broker_message.key = broker_message_key
        broker_message.instruction = instruction
        broker_message.payload = payload
        broker_message.pipeline = pipeline

        return broker_message.SerializeToString()

    def _translate_from_broker(self, message_data):
        """
        Translate the message that the component gets from the broker to the output format

        :param message_data:
        """
        broker_message = BrokerMessage()
        broker_message.ParseFromString(message_data)

        if self.palm:
            message_data = self.cache.get(broker_message.key)
            # Clean up the cache. It is an outbound message and no one will
            # ever need the full message again.
            self.logger.debug('DELETE: {}'.format(broker_message.key))
            self.cache.delete(broker_message.key)
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            palm_message.payload = broker_message.payload
            message_data = palm_message.SerializeToString()
        else:
            message_data = broker_message.payload

        return message_data

    def scatter(self, message_data):
        """
        Abstract method. Picks a message and returns a generator that multiplies the messages
        to the broker.

        :param message_data:
        """
        yield message_data

    def handle_feedback(self, message_data):
        """
        Abstract method. Handles the feedback from the broker

        :param message_data:
        """
        self.last_message = message_data

    def reply_feedback(self):
        """
        Abstract method. Returns the feedback if the component has to reply.
        """
        return self.last_message

    def start(self):
        """
        Call this function to start the component
        """
        if self.bind:
            self.listen_to.bind(self.listen_address)
        else:
            self.listen_to.connect(self.listen_address)

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
            message_data = self.broker.recv()
            self.logger.debug('Component {} Got message from broker'.format(self.name))
            message_data = self._translate_from_broker(message_data)

            for scattered in self.scatter(message_data):
                self.listen_to.send(scattered)
                self.logger.debug('Component {} Sent message'.format(self.name))

                if self.reply:
                    feedback = self.listen_to.recv()
                    feedback = self._translate_to_broker(feedback)
                    self.handle_feedback(feedback)

            self.broker.send(self.reply_feedback())

    def cleanup(self):
        self.listen_to.close()
        self.broker.close()


class ComponentBypassInbound(object):
    """
    Generic inbound component that does not connect to the broker.

    :param name: Name of the component
    :param listen_address: ZMQ socket address to listen to
    :param socket_type: ZMQ inbound socket type
    :param reply: True if the listening socket blocks waiting a reply
    :param bind: True if the component has to bind instead of connect.
    :param logger: Logger instance
    :param cache: Access to the server cache
    """
    def __init__(self,
                 name,
                 listen_address,
                 socket_type,
                 reply=True,
                 bind=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        self.name = name.encode('utf-8')
        self.listen_to = zmq_context.socket(socket_type)
        self.bind = bind
        self.listen_address = listen_address
        self.logger = logger
        self.reply = reply
        self.cache = cache
        self.messages = messages

    def recv(self, reply_data=None):
        """
        Receives, yields and returns reply_data if needed

        :param reply_data: Message to send if connection needs an answer.
        """
        message_data = self.listen_to.recv()

        if self.reply:
            self.listen_to.send(reply_data)

        return message_data

    def start(self):
        if self.bind:
            self.listen_to.bind(self.listen_address)
        else:
            self.listen_to.connect(self.listen_address)

        for i in range(self.messages):
            self.recv()

    def cleanup(self):
        self.listen_to.close()


class ComponentBypassOutbound(object):
    """
    Generic inbound component that does not connect to the broker.

    :param name: Name of the component
    :param listen_address: ZMQ socket address to listen to
    :param socket_type: ZMQ inbound socket type
    :param reply: True if the listening socket blocks waiting a reply
    :param bind: True if the socket has to bind instead of connect
    :param logger: Logger instance
    :param cache: Access to the cache of the server
    """
    def __init__(self,
                 name,
                 listen_address,
                 socket_type,
                 reply=True,
                 bind=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        self.name = name.encode('utf-8')
        self.listen_to = zmq_context.socket(socket_type)
        if bind:
            self.listen_to.bind(listen_address)
        else:
            self.listen_to.connect(listen_address)
        self.listen_address = listen_address
        self.logger = logger
        self.reply = reply
        self.cache = cache
        self.messages = messages

    def send(self, message_data):
        self.listen_to.send(message_data)

        if self.reply:
            message_data = self.listen_to.recv()
            return message_data
