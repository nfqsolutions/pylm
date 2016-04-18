from threading import Thread
from pylm_ng.components.core import zmq_context
from pylm_ng.components.endpoints import logger
import zmq

# To be deleted
import sys


# Temporally copied here
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
                 messages=sys.maxsize,
                 max_buffer_size=sys.maxsize):
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
        self.buffer = {}
        if max_buffer_size < 100:  # Enforce a limit in buffer size.
            max_buffer_size = 100
        self.max_buffer_size = max_buffer_size

        # Poller for the event loop
        self.poller = zmq.Poller()
        self.poller.register(self.outbound, zmq.POLLIN)
        self.poller.register(self.inbound, zmq.POLLIN)

        # Cache for the server
        self.cache = cache

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

        self.inbound_components[name.encode('utf-8')] = {
            'route': route.encode('utf-8'),
            'log': log
        }

    def register_outbound(self, name, log=''):
        self.outbound_components[name.encode('utf-8')] = {
            'log': log
        }

    def start(self):
        # Buffer to store the message when the outbound component is not available
        # for routing. Maybe replace by a heap queue.
        buffering = False

        # List of available outbound components
        available_outbound = []

        self.logger.info('Launch broker')
        self.logger.info('Inbound socket: {}'.format(self.inbound))
        self.logger.info('Outbound socket: {}'.format(self.outbound))

        for i in range(self.messages):
            # Polls the outbound socket for inbound and outbound connections
            event = dict(self.poller.poll())
            self.logger.debug('Event {}'.format(event))

            if self.outbound in event:
                self.logger.debug('Handling outbound event')
                component, empty, message_data = self.outbound.recv_multipart()

                # If messages for the outbound are buffered.
                if component in self.buffer:
                    # Look in the buffer
                    message_data = self.buffer[component].pop()
                    if len(self.buffer[component]) == 0:
                        del self.buffer[component]

                    # If the buffer is empty enough and the broker was buffering
                    if sum([len(v) for v in self.buffer.values()])*10 < self.max_buffer_size \
                            and buffering:
                        # Listen to inbound connections again.
                        self.logger.info('Broker accepting messages again.')
                        self.poller.register(self.inbound, zmq.POLLIN)
                        buffering = False

                    self.outbound.send_multipart([component, empty, message_data])

                # If they are no buffered messages, set outbound as available.
                else:
                    available_outbound.append(component)

            elif self.inbound in event:
                self.logger.debug('Handling inbound event')
                component, empty, message_data = self.inbound.recv_multipart()

                # Start internal routing
                route_to = self.inbound_components[component]['route']

                # If no routing needed
                if route_to == component:
                    self.logger.debug('Message back to {}'.format(route_to))
                    self.inbound.send_multipart([component, empty, message_data])

                # If an outbound is listening
                elif route_to in available_outbound:
                    self.logger.debug('Broker routing to {}'.format(route_to))
                    available_outbound.remove(route_to)
                    self.outbound.send_multipart([route_to, empty, message_data])

                    # Unblock the component
                    self.logger.debug('Unblocking inbound')
                    self.inbound.send_multipart([component, empty, b'1'])

                # If the corresponding outbound not is listening, buffer the message
                else:
                    self.logger.info('Sent to buffer.')
                    if route_to in self.buffer:
                        self.buffer[route_to].append(message_data)
                    else:
                        self.buffer[route_to] = [message_data]

                    if sum([len(v) for v in self.buffer.values()]) >= self.max_buffer_size:
                        self.logger.info('Broker buffering messages')
                        self.poller.unregister(self.inbound)
                        buffering = True

                    self.logger.debug('Unblocking inbound')
                    self.inbound.send_multipart([component, empty, b'1'])

            else:
                self.logger.critical('Socket not known.')

            self.logger.debug('Finished event cycle.')


def inbound1(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'inbound1'
    broker.connect(listen_addr)

    for i in range(0, 10, 2):
        broker.send(str(i).encode('utf-8'))
        returned = broker.recv()
        print('Inbound1', i, returned)
        #assert int(returned) == i


def inbound2(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'inbound2'
    broker.connect(listen_addr)

    for i in range(1, 10, 2):
        broker.send(str(i).encode('utf-8'))
        returned = broker.recv()
        print('Inbound2', i, returned)
        #assert int(returned) == i


def outbound(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'outbound'
    broker.connect(listen_addr)

    broker.send(b'READY')

    for i in range(10):
        message_data = broker.recv()
        print('outbound:', message_data)
        broker.send(message_data)


def test_feedback():
    broker = Broker(logger=logger, messages=20)
    broker.register_inbound('inbound1', route='outbound', log='inbound1')
    broker.register_inbound('inbound2', route='outbound', log='inboubd2')
    broker.register_inbound('outbound', log='outbound')

    threads = [
        Thread(target=broker.start),
        Thread(target=inbound1, args=(broker.inbound_address,)),
        Thread(target=inbound2, args=(broker.inbound_address,)),
        Thread(target=outbound, args=(broker.outbound_address,))
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

if __name__ == '__main__':
    test_feedback()
