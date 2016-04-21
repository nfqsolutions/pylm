from pylm_ng.components.messages_pb2 import PalmMessage, BrokerMessage
from uuid import uuid4
import zmq
import sys


zmq_context = zmq.Context.instance()


class Broker(object):
    """
    Broker for the internal event-loop. It is a ROUTER socket that blocks
    waiting for the components to send something. This is more a bus than
    a broker.
    """
    def __init__(self,
                 inbound_address="inproc://inbound",
                 outbound_address="inproc://outbound",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        Initiate a broker instance
        :param inbound_address: Valid ZMQ bind address for inbound components
        :param outbound_address: Valid ZMQ bind address for outbound components
        :param logger: Logger instance
        :param cache: Global cache of the server
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :param messages: Number of messages allowed before the router starts buffering.
        :return:
        """
        # Socket that will listen to the inbound components
        self.inbound = zmq_context.socket(zmq.ROUTER)
        self.inbound.bind(inbound_address)
        self.inbound_address = inbound_address
        self.inbound_components = {}

        # Socket that listens to the outbound components
        self.outbound = zmq_context.socket(zmq.ROUTER)
        self.outbound.bind(outbound_address)
        self.outbound_address = outbound_address
        self.outbound_components = {}

        # Other utilities
        self.logger = logger
        self.messages = messages

        # Ledger for inbound components that are waiting for a message
        self.ledger = {}

        # Despite this is a dictionary, only one message can be buffered
        self.buffer = {}

        # Poller for the event loop
        self.poller = zmq.Poller()
        # Register only inbound to avoid having to buffer stuff
        self.poller.register(self.outbound, zmq.POLLIN)

        # Cache for the server
        self.cache = cache

    def register_inbound(self, name, route='', block=False, log=''):
        """
        Register component by name.
        :param name: Name of the component. Each component has a name, that
          uniquely identifies it to the broker
        :param route: Each message that the broker gets from the component
          may be routed to another component. This argument gives the name
          of the target component for the message.
        :param block: Register if the component is waiting for a reply.
        :param log: Log message for each inbound connection.
        :return:
        """
        self.inbound_components[name.encode('utf-8')] = {
            'route': route.encode('utf-8'),
            'block': block,
            'log': log
        }

    def register_outbound(self, name, log=''):
        self.outbound_components[name.encode('utf-8')] = {
            'log': log
        }

    def start(self):
        # List of available outbound components
        available_outbound = []

        # If no outbound components are expected, just register inbound
        # to allow inbound connections
        if not self.outbound_components:
            self.poller.register(self.inbound, zmq.POLLIN)

        self.logger.info('Launch broker')
        self.logger.info('Inbound socket: {}'.format(self.inbound))
        self.logger.info('Outbound socket: {}'.format(self.outbound))

        for i in range(self.messages):
            # Polls the outbound socket for inbound and outbound connections
            event = dict(self.poller.poll())
            self.logger.debug('Event {}'.format(event))

            if self.outbound in event:
                component, empty, feedback = self.outbound.recv_multipart()
                broker_message = BrokerMessage()
                broker_message.ParseFromString(feedback)
                self.logger.debug('Handling outbound event: {}'.format(broker_message.key))

                # If any message has been buffered,
                if component in self.buffer:
                    self.logger.debug('The message was buffered')
                    message_data = self.buffer.pop(component)
                    self.outbound.send_multipart([component, empty, message_data])

                    # Check if some socket is waiting for the response.
                    if broker_message.key in self.ledger:
                        self.logger.debug('Message ID found in ledger')
                        component = self.ledger.pop(broker_message.key)
                        self.logger.debug('Unblocking pending inbound: {}'.format(component))
                        self.inbound.send_multipart([component, empty, broker_message.payload])

                else:
                    self.logger.debug('Component added as available')
                    available_outbound.append(component)

                    # Check if some socket is waiting for the response.
                    if broker_message.key in self.ledger:
                        self.logger.debug('Message ID found in ledger')
                        component = self.ledger.pop(broker_message.key)
                        self.logger.debug('Unblocking pending inbound: {}'.format(component))
                        self.inbound.send_multipart([component, empty, broker_message.payload])

                if available_outbound and not self.buffer and not self.ledger:
                    self.poller.register(self.inbound, zmq.POLLIN)

            elif self.inbound in event:
                broker_message = BrokerMessage()
                component, empty, message_data = self.inbound.recv_multipart()
                self.logger.debug('Handling inbound event from {}'.format(component))
                broker_message.ParseFromString(message_data)

                # Start internal routing
                route_to = self.inbound_components[component]['route']
                block = self.inbound_components[component]['block']

                # If no routing needed
                if not route_to:
                    self.logger.debug('Message back to {}'.format(route_to))
                    self.inbound.send_multipart([component, empty, b'1'])

                # If an outbound is listening
                elif route_to in available_outbound:
                    self.logger.debug('Broker routing to {}'.format(route_to))
                    available_outbound.remove(route_to)
                    self.outbound.send_multipart([route_to, empty, broker_message.SerializeToString()])

                    # Unblock the component
                    if not block:
                        self.logger.debug('Unblocking inbound')
                        self.inbound.send_multipart([component, empty, b'1'])
                    else:
                        self.ledger[broker_message.key] = component
                        self.logger.debug('Inbound waiting for feedback: {}'.format(self.ledger))
                        # TODO: Check if ledger condition is necessary
                        self.poller.unregister(self.inbound)

                # If the corresponding outbound not is listening, buffer the message
                else:
                    self.buffer[route_to] = broker_message.SerializeToString()
                    self.logger.info('Sent to buffer.')
                    self.poller.unregister(self.inbound)

                    if block:
                        self.ledger[broker_message.key] = component
                        self.logger.debug('Inbound waiting for feedback: {}'.format(self.ledger))

            else:
                self.logger.critical('Socket not known.')

            self.logger.debug('Finished event cycle.')

    def cleanup(self):
        self.inbound.close()
        self.outbound.close()


class ComponentInbound(object):
    """
    Generic component that connects a REQ socket to the broker, and a
    socket to an inbound external service.
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
        self.listen_to = zmq_context.socket(socket_type)
        if bind:
            self.listen_to.bind(listen_address)
        else:
            self.listen_to.connect(listen_address)
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
        Translate the message that the component has got to be digestible by the broker
        :param message_data:
        :return:
        """
        broker_message_key = str(uuid4())
        if self.palm:
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            payload = palm_message.payload

            # I store the message to get it later when the message is outbound. See that
            # if I am just sending binary messages, I do not need to assign any envelope.
            self.cache.set(broker_message_key, message_data)
        else:
            payload = message_data

        broker_message = BrokerMessage()
        broker_message.key = broker_message_key
        broker_message.payload = payload

        return broker_message.SerializeToString()

    def _translate_from_broker(self, message_data):
        """
        Translate the message that the component gets from the broker to the output format
        :param message_data:
        :return:
        """
        broker_message = BrokerMessage()
        broker_message.ParseFromString(message_data)
        message_data = self.cache.get(broker_message.key)
        palm_message = PalmMessage()
        palm_message.ParseFromString(message_data)
        palm_message.payload = broker_message.payload
        message_data = palm_message.SerializeToString()
        return message_data

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
        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting messages'.format(self.name))
            message_data = self.listen_to.recv()
            self.logger.debug('Got inbound message')

            for scattered in self.scatter(message_data):
                scattered = self._translate_to_broker(scattered)
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
        """
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
        :return:
        """
        self.name = name.encode('utf-8')
        self.listen_to = zmq_context.socket(socket_type)
        if bind:
            self.listen_to.bind(listen_address)
        else:
            self.listen_to.connect(listen_address)
        self.listen_address = listen_address
        self.broker = zmq_context.socket(zmq.REQ)
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

            # I store the message to get it later when the message is outbound. See that
            # if I am just sending binary messages, I do not need to assign any envelope.
            self.cache.set(broker_message_key, message_data)
        else:
            payload = message_data

        broker_message = BrokerMessage()
        broker_message.key = broker_message_key
        broker_message.payload = payload

        return broker_message.SerializeToString()

    def _translate_from_broker(self, message_data):
        """
        Translate the message that the component gets from the broker to the output format
        :param message_data:
        :return:
        """
        broker_message = BrokerMessage()
        broker_message.ParseFromString(message_data)

        if self.palm:
            message_data = self.cache.get(broker_message.key)
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            palm_message.payload = broker_message.payload
            message_data = palm_message.SerializeToString()
        else:
            message_data = broker_message.payload

        return message_data

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
            message_data = self.broker.recv()
            message_data = self._translate_from_broker(message_data)

            self.logger.debug('Got message from broker')
            for scattered in self.scatter(message_data):
                self.listen_to.send(scattered)

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
    """
    def __init__(self,
                 name,
                 listen_address,
                 socket_type,
                 reply=True,
                 bind=False,
                 logger=None,
                 cache=None):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param socket_type: ZMQ inbound socket type
        :param reply: True if the listening socket blocks waiting a reply
        :param bind: True if the component has to bind instead of connect.
        :param logger: Logger instance
        :param cache: Access to the server cache
        :return:
        """
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

    def recv(self, reply_data=None):
        """
        Receives, yields and returns answer_data if needed
        :param reply_data: Message to send if connection needs an answer.
        :return:
        """
        message_data = self.listen_to.recv()

        if self.reply:
            self.listen_to.send(reply_data)

        return message_data


class ComponentBypassOutbound(object):
    """
    Generic inbound component that does not connect to the broker.
    """
    def __init__(self,
                 name,
                 listen_address,
                 socket_type,
                 reply=True,
                 bind=False,
                 logger=None,
                 cache=None):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param socket_type: ZMQ inbound socket type
        :param reply: True if the listening socket blocks waiting a reply
        :param bind: True if the socket has to bind instead of connect
        :param logger: Logger instance
        :param cache: Access to the cache of the server
        :return:
        """
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

    def send(self, message_data):
        self.listen_to.send(message_data)

        if self.reply:
            message_data = self.listen_to.recv()
            return message_data

