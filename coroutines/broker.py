# Testing a coroutine-based broker.

import asyncio
import sys
import zmq
from source import Source


zmq_context = zmq.Context.instance()


class Broker(object):
    """
    Pylm broker that does not use the ZeroMQ polling mechanism, but
    generators and coroutines to wire the connectors.
    """
    # Asyncio event loop.
    event_loop = asyncio.get_event_loop()
    # Mapping of outbound connections as generators
    outbound = {}
    # Mapping of components (component, outbound)
    components = {}
    # List of futures for the connections
    tasks = []
    # Message counter. It has to be a class attribute.
    counter = 0

    def __init__(self, messages=sys.maxsize):
        self.messages = messages

    def loop(self):
        while self.counter < self.messages:
            recv = (yield)
            print(recv, self.counter)
            self.counter += 1

        print('Closing event loop')
        yield from asyncio.wait(self.tasks)
        self.event_loop.stop()
        self.event_loop.close()

    @property
    def handler(self):
        generator = self.loop()
        generator.send(None)
        return generator

    def register_inbound(self, component, outbound=None, messages=sys.maxsize):
        self.components[component.name] = (component, outbound)
        self.tasks.append(asyncio.ensure_future(component.start(messages)))

    def register_outbound(self, component, messages=sys.maxsize):
        self.outbound[component.name] = component
        self.components[component.name] = (component, None)
        self.tasks.append(asyncio.ensure_future(component.start(messages)))

    def start(self):
        print("Starting event loop.")
        for f in self.tasks:
            self.event_loop.run_until_complete(f)

    def stop(self):
        self.event_loop.stop()

    def close(self):
        self.event_loop.close()


class ConnectorInbound(object):
    def __init__(self, name, events, address='inproc://inbound'):
        self.name = name
        self.events = events
        self.socket = zmq_context.socket(zmq.REP)
        self.address = address

    async def recv(self):
        value = self.socket.recv()
        self.socket.send(b'0')
        return value

    async def start(self, messages=sys.maxsize):
        print(self.address)
        self.socket.bind(self.address)
        
        for i in range(messages):
            message = await self.recv()
            self.events.send(message)

        print('done {}'.format(self.name))


class ConnectorOutbound(object):
    def __init__(self, name, events):
        self.name = name
        self.events = events

    async def start(self, messages=sys.maxsize):
        for i in range(messages):
            print(self.name)


broker = Broker(messages=5)
broker.register_inbound(ConnectorInbound('connector1',
                                         broker.handler,
                                         'tcp://127.0.0.1:5555'),
                        messages=5)
broker.start()
