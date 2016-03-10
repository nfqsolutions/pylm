import zmq
import sys
from pylm_ng.components.messages_pb2 import PalmMessage


zmq_context = zmq.Context.instance()


class Broker(object):
    """
    Broker for the internal event-loop. It is a ROUTER socket that blocks
    waiting for the components to send something.
    """
    def __init__(self, bind_address="inproc://broker", logger=None,
                 messages=sys.maxsize):
        """
        Initiate a broker instance
        :param bind_address: Valid ZMQ bind address
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        # Socket that will listen to all the components
        self.events = zmq_context.socket(zmq.ROUTER)
        self.events.bind(bind_address)
        self.bind_address = bind_address
        self.logger = logger
        self.internal_routing = {}
        self.user_functions = {}
        self.messages = messages

    def register_inbound(self, name, route=None, log=''):
        """
        Register component by name. Only inbound components have to be registered.
        :param name: Name of the component. Each component has a name, that
          uniquely identifies it to the broker
        :param route: Each message that the broker gets from the component
          may be routed to another component. This argument gives the name
          of the target component for the message.
        :param log: Log message for each inbound connection.
        :return:
        """
        # If route is not specified, the component wants a message back.
        if not route:
            route = name

        self.internal_routing[name.encode('utf-8')] = {
            'route': route.encode('utf-8'),
            'log': log
        }

    def register_function(self, function):
        """
        Register a user-defined function to the broker.
        :param function:
        :return:
        """
        self.user_functions[function.__name__] == function

    def start(self):
        self.logger.info('Launch broker')
        for i in range(self.messages):
            # Listens to the socket for messages
            self.logger.debug('Broker blocked waiting for events')
            component, empty, message_data = self.events.recv_multipart()

            # Deserialize the message
            message = PalmMessage()
            message.ParseFromString(message_data)

            # Tries to execute the user defined function
            if message.function in self.user_functions:
                result = self.user_functions[message.function](message.payload)
            else:
                self.logger.warning('User defined function {} not available'.format(message.function))
                result = b''

            message.payload = result

            # Reads the internal router and emits the log message
            route_to = self.internal_routing[component]['route']

            # Finally routes the message
            if route_to:
                self.logger.debug(self.internal_routing[component]['log'])
                message_data = message.SerializeToString()
                self.logger.debug('Sending message to {}'.format(route_to))
                self.events.send_multipart([route_to, empty, message_data])


class ComponentInbound(object):
    """
    Generic component that connects a REQ socket to the broker, and a
    socket to an inbound external service.
    """
    def __init__(self, name, listen_to, socket_type, reply=True,
                 broker_address="inproc://broker",
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_to: ZMQ socket address to listen to
        :param socket_type: ZMQ inbound socket type
        :param reply: True if the listening socket blocks waiting a reply
        :param broker_address: ZMQ socket address for the broker
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        self.name = name
        self.listen_to = zmq_context.socket(socket_type)
        self.listen_to.connect(listen_to)
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = name.encode('utf-8')
        self.broker.connect(broker_address)
        self.logger = logger
        self.messages = messages
        self.reply = reply

    def start(self):
        self.logger.info('Launch component {}'.format(self.name))
        for i in range(self.messages):
            self.logger.debug('Component {} blocked'.format(self.name))
            message_data = self.listen_to.recv()
            self.logger.debug('Got inbound message')
            self.broker.send(message_data)

            if self.reply:
                self.logger.debug('Component {} blocked'.format(self.name))
                message_data = self.broker.recv()
                self.listen_to.send(message_data)

            else:
                self.logger.debug('Component {} blocked'.format(self.name))
                self.broker.recv()


class ComponentOutbound(object):
    """
    Generic component that connects a REQ socket to the broker, and a
    socket to an inbound external service.
    """
    def __init__(self, name, listen_to, socket_type, reply=True,
                 broker_address="inproc://broker",
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_to: ZMQ socket address to listen to
        :param socket_type: ZMQ inbound socket type
        :param reply: True if the listening socket blocks waiting a reply
        :param broker_address: ZMQ socket address for the broker
        :param logger: Logger instance
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        self.name = name
        self.listen_to = zmq_context.socket(socket_type)
        self.listen_to.connect(listen_to)
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = name.encode('utf-8')
        self.broker.connect(broker_address)
        self.logger = logger
        self.messages = messages
        self.reply = reply

    def start(self):
        self.logger.info('Launch component {}'.format(self.name))

        for i in range(self.messages):
            self.logger.debug('Component {} blocked'.format(self.name))
            message_data = self.broker.recv()
            self.logger.debug('Got message from broker')
            self.listen_to.send(message_data)

            if self.reply:
                message_data = self.listen_to.recv()
                self.broker.send(message_data)

            else:
                self.broker.send()


class RepComponent(ComponentInbound):
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
        super(RepComponent, self).__init__(
            name,
            listen_to,
            zmq.REP,
            reply=True,
            broker_address=broker_address,
            logger=logger,
            messages=messages
        )


class PullComponent(ComponentInbound):
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
        super(PullComponent, self).__init__(
            name,
            listen_to,
            zmq.PULL,
            reply=False,
            broker_address=broker_address,
            logger=logger,
            messages=messages
        )


class PushComponent(ComponentOutbound):
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
        super(PushComponent, self).__init__(
            name,
            listen_to,
            zmq.PUSH,
            reply=False,
            broker_address=broker_address,
            logger=logger,
            messages=messages
        )
