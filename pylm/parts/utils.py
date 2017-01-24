# Pylm, a framework to build components for high performance distributed
# applications. Copyright (C) 2016 NFQ Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division
from pylm.parts.connections import PushBypassConnection
from pylm.parts.services import RepBypassService, RepService
from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage, BrokerMessage
from logging import Handler, Formatter, NOTSET
from uuid import uuid4
from threading import Thread, Lock
import zmq
import sys
import time


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
            if not value:
                self.logger.error('key {} not present'.format(key))
                return_value = b''
            else:
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
            return_value = b''

        self.listen_to.send(return_value)


class ResilienceService(RepService):
    """
    Keeps track of the messages that have not been processed by the
    workers, and sends them again if some conditions are met. It
    communicates with the worker push and worker pull parts.
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
        self.max_flush_time = 10
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
            self.logger.warning('{}: Flushing messages'.format(self.name))

            # Copy the dictionary to prevent collisions:
            waiting_dict = {}

            with self.resent_lock:
                for k, v in self.waiting.items():
                    # Resent tracks how much time the message has been resent.
                    if k not in self.resent:
                        self.resent[k] = 1
                    else:
                        self.resent[k] += 1
                    waiting_dict[k] = v

            for k, v in waiting_dict.items():
                self.broker.send(v)
                self.broker.recv()

            # Algorithm that trains the flush time according to the redundancy
            # parameter, which is the target.
            actual_redundancy = len(waiting_dict) / self.messages_sent

            # Recalibrate flush time to be according to the redundancy rate.
            new_time = self.flush_time * actual_redundancy / self.redundancy
            new_time = min([new_time, self.max_flush_time])
            self.logger.warning(
                'Redundancy ratio: {}, New time: {}'.format(
                    actual_redundancy, max([self.flush_time, new_time])
                )
            )
            self.messages_sent = 1

    def start(self):
        # Dicts to temporarily store messages, and statistics. These
        # are dictionaries, hence there is particular care to prevent collisions.
        self.logger.info('Resilience service {} started'.format(self.name))

        for i in range(self.messages):
            message_data = self.listen_to.recv_multipart()
            self.logger.debug('Got message')
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
