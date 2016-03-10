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
        # Socket that will listen to all the components
        self.events = zmq_context.socket(zmq.ROUTER)
        self.events.bind(bind_address)
        self.bind_address=bind_address
        self.logger = logger
        self.internal_routing = {}
        self.user_functions = {}
        self.messages = messages

    def register_component(self, name, route=None, log=''):
        """
        The broker connects to components. Each component has to
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
            self.logger.info(self.internal_routing[component]['log'])

            # Finally routes the message
            message_data = message.SerializeToString()
            self.events.send_multipart([route_to, empty, message_data])


class ReqRepComponent(object):
    """
    ReqRep is a component that connects a REQ socket to the broker, and a REP
    socket to an external service.
    """
    def __init__(self, name, listen_to, broker_address="inproc://broker",
                 logger=None, messages=sys.maxsize):
        self.name = name
        self.listen_to = zmq_context.socket(zmq.REP)
        self.listen_to.connect(listen_to)
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = name.encode('utf-8')
        self.broker.connect(broker_address)
        self.logger = logger
        self.messages = messages

    def start(self):
        self.logger.info('Launch component'.format(self.name))
        for i in range(self.messages):
            message_data = self.listen_to.recv()
            self.broker.send(message_data)
            message_data = self.broker.recv()
            self.listen_to.send(message_data)
