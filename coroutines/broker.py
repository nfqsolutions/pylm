# Testing a coroutine-based broker.

import asyncio
import sys


class Broker(object):
    event_loop = asyncio.get_event_loop()
    outbound = {}
    connections = {}
    futures = []
    counter = 0

    def __init__(self, messages=sys.maxsize):
        self.messages = messages

    def looping(self):
        while self.counter < self.messages:
            recv = (yield)
            print(recv, self.counter)
            self.counter += 1

        print('Closing event loop')
        yield from asyncio.wait(self.futures)
        self.event_loop.stop()
        self.event_loop.close()

    @property
    def gen(self):
        generator = self.looping()
        generator.send(None)
        return generator

    def register_inbound(self, connector, name, outbound=None, messages=sys.maxsize):
        connector_instance = connector(name, self.gen)
        self.futures.append(asyncio.ensure_future(connector_instance.start(messages)))

    def register_outbound(self, connector, name, messages=sys.maxsize):
        connector_instance = connector(name, self.gen)
        self.futures.append(asyncio.ensure_future(connector_instance.start(messages)))

    def start(self):
        print("Starting event loop.")
        for f in self.futures:
            self.event_loop.run_until_complete(f)

    def stop(self):
        self.event_loop.stop()

    def close(self):
        self.event_loop.close()


class ConnectorInbound(object):
    def __init__(self, name, events):
        self.name = name
        self.events = events

    async def start(self, messages=sys.maxsize):
        for i in range(messages):
            await asyncio.sleep(1)
            self.events.send(self.name)

        print('done {}'.format(self.name))
        return b'0'


class ConnectorOutbound(object):
    def __init__(self, name, events):
        self.name = name
        self.events = events

    async def start(self, messages=sys.maxsize):
        for i in range(20):
            pass


broker = Broker(messages=20)
broker.register_inbound(ConnectorInbound, 'connector1', messages=10)
broker.register_inbound(ConnectorInbound, 'connector2', messages=10)
broker.start()