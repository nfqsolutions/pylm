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

from pylm.parts.core import zmq_context

import zmq
import sys


class EndPoint(object):
    def __init__(self, name, log_address, perf_address, ping_address,
                 messages=sys.maxsize):
        self.poller = zmq.Poller()
        self.name = name

        self.log_address = log_address
        self.logs = zmq_context.socket(zmq.PULL)
        self.logs.bind(log_address)

        self.perf_address = perf_address
        self.perf = zmq_context.socket(zmq.PULL)
        self.perf.bind(perf_address)

        self.ping_address = ping_address
        self.ping = zmq_context.socket(zmq.PULL)
        self.ping.bind(ping_address)

        self.poller.register(self.logs, zmq.POLLIN)
        self.poller.register(self.perf, zmq.POLLIN)
        self.poller.register(self.ping, zmq.POLLIN)

        self.messages = messages

    def start_debug(self):
        for i in range(self.messages):
            event = dict(self.poller.poll())

            if self.logs in event:
                try:
                    print('LOG:', self.logs.recv().decode('utf-8'))
                except UnicodeDecodeError:
                    print('LOG:', self.logs.recv())

            elif self.perf in event:
                print('PRF:', self.perf.recv().decode('utf-8'))

            elif self.ping in event:
                print('PNG:', self.ping.recv().decode('utf-8'))

    def cleanup(self):
        self.ping.close()
        self.perf.close()
        self.logs.close()

