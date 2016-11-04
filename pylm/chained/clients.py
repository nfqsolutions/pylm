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

from pylm.standalone import ParallelClient
from pylm.parts.core import zmq_context
from uuid import uuid4
import zmq
import sys


class LoopClient(ParallelClient):
    """
    Client for pipelines that end in a client.
    """


class Client(LoopClient):
    """
    Client when the pipeline does not end in a client
    """
    def __init__(self, pull_address, db_address, server_name, pipeline=None):
        self.server_name = server_name
        self.push = zmq_context.socket(zmq.PUSH)
        self.push.connect(pull_address)
        self.pull_address = pull_address

        self.db_address = db_address
        self.db = zmq_context.socket(zmq.REQ)
        self.db.connect(db_address)

        self.function = ''
        self.job_generator = None
        self.messages = 0
        self.uuid = str(uuid4())
        # Pipeline, also session.
        if pipeline:
            self.pipeline = pipeline
            self.session_set = True
        else:
            self.pipeline = str(uuid4())
            self.session_set = False

        # Cache to tag messages
        self.cache = None

    def job(self, function, generator, cache=None, messages=sys.maxsize):
        """
        Submit a job for the cluster given a function to be executed, and a generator
        that provides the payloads for each message

        :param function: String. Function to be executed
        :param generator: Generator of messages.
        :param cache: Use a cache constant for the message
        :param messages: Number of expected messages before shutting down the client.
        :return:
        """
        if cache:
            if type(cache) == bytes or type(cache) == str:
                self.cache = cache
            else:
                raise TypeError('Cache must be <bytes> or <str>')

        self.function = function
        self.job_generator = generator
        self._push_job()

    def clean(self):
        self.push.close()
        self.db.close()
