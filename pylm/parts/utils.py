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

