from __future__ import division
from pylm.components.connections import PushBypassConnection
from pylm.components.services import RepBypassService, RepService
from pylm.components.core import zmq_context
from pylm.components.messages_pb2 import PalmMessage, BrokerMessage
from logging import Handler, Formatter, NOTSET
from uuid import uuid4
from threading import Thread, Lock
from copy import copy
import zmq
import sys
import time


class PushHandler(Handler):
    def __init__(self, listen_address):
        """
        :param listen_address: Address for the handler to be connected to
        :return:
        """
        self.connection = PushBypassConnection('PushLogger', listen_address=listen_address)
        super(PushHandler, self).__init__(level=NOTSET)
        self.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        self.connection.send(self.format(record).encode('utf-8'))


class LogCollector(object):
    """
    Endpoint for log collection
    """
    def __init__(self, bind_address='inproc://LogCollector'):
        self.socket = zmq_context.socket(zmq.PULL)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.nlog = 0

    def start(self, messages=sys.maxsize):
        """
        Starts the log collector
        :param messages: Number of messages allowed. Used for debugging.
        :return:
        """
        for i in range(messages):
            self.emit(self.socket.recv())

    def emit(self, log_item):
        """
        Emits the message. At this point it is a stupid print
        :param log_item:
        :return:
        """
        self.nlog += 1
        print('LOG ENTRY #{:<8}:'.format(self.nlog), log_item.decode('utf-8'))


class PerformanceCounter(PushBypassConnection):
    """
    Class to record and to send performance counters to an external service.
    """
    def __init__(self, listen_address):
        super(PerformanceCounter, self).__init__('perfcounter', listen_address)
        if sys.version_info[0] < 3:
            if sys.platform == 'win32':
                self.timer = time.clock
            else:
                self.timer = time.time
        else:
            self.timer = time.perf_counter

        self.zero = self.timer()
        self.tick_db = {}

    def get_loop(self, label):
        if label not in self.tick_db:
            self.tick_db[label] = 1
        else:
            self.tick_db[label] += 1

        return self.tick_db[label]

    def tick(self, label):
        loop = self.get_loop(label)
        message = '{}: #{}: {}'.format(
            label, loop, self.timer()-self.zero
        ).encode('utf-8')
        self.send(message)


class PerformanceCollector(object):
    """
    Endpoint for log collection
    """
    def __init__(self, bind_address='inproc://PerformenceCollector'):
        self.socket = zmq_context.socket(zmq.PULL)
        self.socket.bind(bind_address)
        self.bind_address = bind_address
        self.nlog = 0

    def start(self, messages=sys.maxsize):
        """
        Starts the performance counter collector
        :param messages: Number of messages allowed. Used for debugging.
        :return:
        """
        for i in range(messages):
            self.emit(self.socket.recv())

    def emit(self, perfcounter):
        """
        Emits the performance counter. At this point it is a stupid print
        :param log_item:
        :return:
        """
        self.nlog += 1
        print('TICK #{:<8}:'.format(self.nlog), perfcounter.decode('utf-8'))


class Pinger(PushBypassConnection):
    """
    Pinger that is used for centralized heartbeat service. It has to be
    launched in a thread
    """
    def __init__(self, listen_address, every=1, pings=sys.maxsize):
        """
        :param listen_address: Address of the heartbeat collector
        :param every: Ping every n seconds
        :return:
        """
        super(Pinger, self).__init__('pinger', listen_address=listen_address)
        self.pings = pings
        self.every = every

    def start(self):
        for i in range(self.pings):
            time.sleep(self.every)
            self.send(b'ping')


class CacheService(RepBypassService):
    def recv(self):
        message_data = self.listen_to.recv()
        message = PalmMessage()
        message.ParseFromString(message_data)
        instruction = message.function.split('.')[1]

        if instruction == 'set':
            if message.HasField('cache'):
                key = message.cache
            else:
                key = str(uuid4())

            self.logger.debug('Cache Service: Set key {}'.format(key))
            value = message.payload
            self.cache.set(key, value)
            return_value = key.encode('utf-8')

        elif instruction == 'get':
            key = message.payload.decode('utf-8')
            self.logger.debug('Cache Service: Get key {}'.format(key))
            value = self.cache.get(key)
            return_value = value

        elif instruction == 'delete':
            key = message.payload.decode('utf-8')
            self.logger.debug('Cache Service: Delete key {}'.format(key))
            self.cache.delete(key)
            return_value = key.encode('utf-8')

        else:
            self.logger.error(
                'Cache {}:Key not found in the database'.format(self.name)
            )
            return_value = None

        self.listen_to.send(return_value)


class ResilienceService(RepService):
    """
    Keeps track of the messages that have not been processed by the
    workers, and sends them again if some conditions are met. It
    communicates with the worker push and worker pull components.
    """
    def __init__(self, name, listen_address, broker_address,
                 logger=None, cache=None, messages=sys.maxsize):
        super(ResilienceService, self).__init__(name,
                                                listen_address,
                                                broker_address,
                                                palm=False,
                                                logger=logger,
                                                cache=cache,
                                                messages=messages)

        self.flush_time = 1  # seconds. Parameter to be trained.
        self.redundancy = 0.01  # Training target. Ratio of messages that are repeated.
        self.waiting = {}
        self.resent = {}
        self.omit = {}
        self.messages_sent = 1
        self.resent_lock = Lock()

        # Started the thread that flushes periodically.
        flush_thread = Thread(target=self.flush_routine)
        flush_thread.daemon = True
        flush_thread.start()

    def flush_routine(self):
        """
        Little scheduler that flushes the waiting messages periodically. Some
        messages may be mistakenly considered to be failed, but a failed message
        will never be mistaken as good.
        :return:
        """
        new_time = self.flush_time
        while True:
            time.sleep(max([self.flush_time, new_time]))
            self.logger.info('{}: Flushing messages'.format(self.name))

            # Copy the dictionary to prevent collisions:
            waiting_dict = copy(self.waiting)

            for k, v in waiting_dict.items():
                with self.resent_lock:
                    # Resent tracks how much time the message has been resent.
                    if k not in self.resent:
                        self.resent[k] = 1
                    else:
                        self.resent[k] += 1

                self.broker.send(v)
                self.broker.recv()

            # Algorithm that trains the flush time according to the redundancy
            # parameter, which is the target.
            actual_redundancy = len(waiting_dict) / self.messages_sent

            # Recalibrate flush time to be according to the redundancy rate.
            new_time = max([self.flush_time, new_time]) *\
                actual_redundancy / self.redundancy
            self.logger.info(
                'Redundancy ratio: {}, New time: {}'.format(
                    actual_redundancy, max([self.flush_time, new_time])
                )
            )
            self.messages_sent = 1

    def start(self):
        # Dicts to temporarily store messages, and statistics. These
        # are dictionaries, hence there is particular care to prevent collisions.

        for i in range(self.messages):
            message_data = self.listen_to.recv_multipart()
            message = BrokerMessage()

            # Registers any message as pending in a local dict
            if message_data[0] == b'to':
                message.ParseFromString(message_data[1])

                self.waiting[message.key] = message_data[1]

                self.messages_sent += 1
                # Send a dummy message, since no action is required
                self.listen_to.send(b'0')

            # This is more complex. These are the messages that come from
            # the workers. This section manages the local message cache,
            # and updates the statistics accordingly
            elif message_data[0] == b'from':
                message.ParseFromString(message_data[1])

                # First thing is to remove the message from the waiting list
                self.waiting.pop(message.key)

                if message.key in self.resent:
                    # Put in omit list to avoid getting the message twice
                    with self.resent_lock:
                        self.resent[message.key] -= 1
                        if self.resent[message.key] == 0:
                            self.resent.pop(message.key)

                    self.omit[message.key] = 1

                    # This one means that the message should be processed
                    self.listen_to.send(b'1')

                # The omit set are the messages that were mistakenly set
                # as failed, and they should not be processed
                elif message.key in self.omit:
                    # If the message was resent only once, purge from omit list.
                    if message.key not in self.resent:
                        self.omit.pop(message.key)

                    # This zero means that the message should not be processed
                    self.listen_to.send(b'0')

                # If the message is not registered in any way, process it.
                else:
                    self.listen_to.send(b'1')

            else:
                # Just unblock
                self.logger.error('{} Got an invalid message'.format(self.name))
                self.listen_to.send(b'1')
