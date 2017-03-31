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

# The difference between connections and services is that connections
# connect, while services bind.
from uuid import uuid4

from pylm.parts.core import Inbound, Outbound,\
    zmq_context, BypassInbound
from pylm.parts.messages_pb2 import PalmMessage
from http.server import HTTPServer, BaseHTTPRequestHandler
import zmq
import sys


class RepService(Inbound):
    """
    RepService binds to a given socket and returns something.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param messages: Maximum number of messages. Defaults to infinity
        :return:
        """
        super(RepService, self).__init__(
            name,
            listen_address,
            zmq.REP,
            reply=True,
            broker_address=broker_address,
            bind=True,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PullService(Inbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param messages: Maximum number of messages. Defaults to infinity.
        :return:
        """
        super(PullService, self).__init__(
            name,
            listen_address=listen_address,
            socket_type=zmq.PULL,
            reply=False,
            broker_address=broker_address,
            bind=True,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PushService(Outbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param messages: Maximum number of messages. Defaults to infinity.
        :return:
        """
        super(PushService, self).__init__(
            name,
            listen_address=listen_address,
            socket_type=zmq.PUSH,
            reply=False,
            broker_address=broker_address,
            bind=True,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PubService(Outbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.

    :param name: Name of the service
    :param listen_address: ZMQ socket address to bind to
    :param broker_address: ZMQ socket address of the broker
    :param logger: Logger instance
    :param messages: Maximum number of messages. Defaults to infinity.
    :param pipelined: Defaults to False. Pipelined if publishes to a
        server, False if publishes to a client.
    :param server: Name of the server, necessary to pipeline messages.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize,
                 pipelined=False,
                 server=None):
        super(PubService, self).__init__(
            name,
            listen_address=listen_address,
            socket_type=zmq.PUB,
            reply=False,
            broker_address=broker_address,
            bind=True,
            logger=logger,
            cache=cache,
            messages=messages
        )
        self.name = server
        self.pipelined = pipelined

    def handle_stream(self, message):
        """
        Handle the stream of messages.

        :param message: The message about to be sent to the next step in the
            cluster
        :return: topic (str) and message (PalmMessage)

        The default behaviour is the following. If you leave this function
        unchanged and pipeline is set to False, the topic is the ID of the
        client, which makes the message return to the client. If the pipeline
        parameter is set to True, the topic is set as the name of the server and
        the step of the message is incremented by one.

        You can alter this default behaviour by overriding this function.
        Take into account that the message is also available in this function,
        and you can change other parameters like the stage or the function.
        """
        if self.pipelined:
            # If the master is pipelined,
            topic = self.name
            message.stage += 1
        else:
            topic = message.client

        return topic, message

    def start(self):
        """
        Call this function to start the component
        """
        message = PalmMessage()

        self.listen_to.bind(self.listen_address)
        self.logger.info('{} successfully started'.format(self.name))

        for i in range(self.messages):
            self.logger.debug('{} blocked waiting for broker'.format(self.name))
            message_data = self.broker.recv()
            self.logger.debug('{} Got message from broker'.format(self.name))
            message_data = self._translate_from_broker(message_data)
            message.ParseFromString(message_data)

            for scattered in self.scatter(message):
                topic, scattered = self.handle_stream(scattered)
                self.listen_to.send_multipart([topic.encode('utf-8'),
                                               message.SerializeToString()])
                self.logger.debug('Component {} Sent message. Topic {}'.format(
                    self.name, topic))

                if self.reply:
                    feedback = self.listen_to.recv()
                    feedback = self._translate_to_broker(feedback)
                    self.handle_feedback(feedback)

            self.broker.send(self.reply_feedback())

        return self.name

        
class WorkerPushService(PushService):
    """
    This is a particular push service that does not modify the messages that
    the broker sends.
    """
    def _translate_from_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        self.logger.debug('{} translating from broker'.format(self.name))
        return message_data

    def _translate_to_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data


class WorkerPullService(PullService):
    """
    This is a particular pull service that does not modify the messages that
    the broker sends.
    """
    def _translate_to_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data

    def _translate_from_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        return message_data


class PushPullService(object):
    """
    Push-Pull Service to connect to workers
    """
    def __init__(self,
                 name,
                 push_address,
                 pull_address,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the component
        :param listen_address: ZMQ socket address to listen to
        :param socket_type: ZMQ inbound socket type
        :param reply: True if the listening socket blocks waiting a reply
        :param broker_address: ZMQ socket address for the broker
        :param bind: True if socket has to bind, instead of connect.
        :param logger: Logger instance
        :param cache: Cache for shared data in the server
        :param messages: Maximum number of inbound messages. Defaults to infinity.
        :return:
        """
        self.name = name.encode('utf-8')

        self.push = zmq_context.socket(zmq.PUSH)
        self.pull = zmq_context.socket(zmq.PULL)
        self.push_address = push_address
        self.pull_address = pull_address
        self.push.bind(push_address)
        self.pull.bind(pull_address)

        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = self.name
        self.broker.connect(broker_address)

        self.logger = logger
        self.cache = cache
        self.messages = messages

        self.last_message = b''

    def scatter(self, message_data):
        """
        To be overriden. Picks a message and returns a generator that multiplies the messages
        to the broker.
        :param message_data:
        :return:
        """
        yield message_data

    def handle_feedback(self, message_data):
        """
        To be overriden. Handles the feedback from the broker
        :param message_data:
        :return:
        """
        self.last_message = message_data

    def reply_feedback(self):
        """
        To be overriden. Returns the feedback if the component has to reply.
        :return:
        """
        return self.last_message

    def start(self):
        message = PalmMessage
        self.logger.info('{} Successfully started'.format(self.name))
        initial_message = PalmMessage()
        initial_message.pipeline = '0'
        initial_message.client = '0'
        initial_message.stage = 0
        initial_message.function = ''
        initial_message.payload = b'0'
        self.broker.send(initial_message.SerializeToString())

        for i in range(self.messages):
            self.logger.debug('{} blocked waiting for broker'.format(self.name))
            message_data = self.broker.recv()
            self.logger.debug('Got message {} from broker'.format(i))
            message.ParseFromString(message_data)

            for scattered in self.scatter(message):
                self.push.send(scattered)
                self.handle_feedback(self.pull.recv())

            self.broker.send(self.reply_feedback())

        return self.name

    def cleanup(self):
        self.push.close()
        self.pull.close()
        self.broker.close()


class RepBypassService(BypassInbound):
    """
    Generic connection that opens a Rep socket and bypasses the broker.
    """
    def __init__(self, name, listen_address, logger=None,
                 cache=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param listen_address: ZMQ socket address to listen to
        :param logger: Logger instance
        :param messages:
        :return:
        """
        super(RepBypassService, self).__init__(name, listen_address, zmq.REP,
                                               reply=True, bind=True,
                                               logger=logger, cache=cache,
                                               messages=messages)


class HttpService(Inbound):
    """
    Similar to PullService, but the connection offered is an HTTP server
    that deals with inbound messages.

    ACHTUNG: this thing is deliberately single threaded
    """
    def __init__(self,
                 name,
                 hostname,
                 port,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None):
        self.name = name.encode('utf-8')
        self.hostname = hostname
        self.port = port
        self.logger = logger
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.cache = cache

    def _make_handler(self):
        """
        This is serious meta programming. Note that the handler reuses
        the socket that connects to the router. This is intentional and
        makes the handler strictly single threaded.

        :return: Returns a PalmHandler class, that is a subclass of
          BaseHttpRequestHandler
        """
        # Clarify the scope since self is masked by the returned class
        scatter = self.scatter
        _translate_to_broker = self._translate_to_broker
        broker = self.broker
        handle_feedback = self.handle_feedback
        reply_feedback = self.reply_feedback

        class PalmHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                """
                Note that this http server always replies
                """
                message = PalmMessage()
                self.send_response(200)
                self.end_headers()
                message_data = self.rfile.read(
                    int(
                        self.headers.get('Content-Length')
                    )
                )

                message.ParseFromString(message_data)
                scattered_messages = scatter(message)

                if not scattered_messages:
                    self.wfile.write(b'0')

                else:
                    for scattered in scattered_messages:
                        scattered = _translate_to_broker(scattered)

                        if scattered:
                            broker.send(scattered.SerializeToString())
                            handle_feedback(broker.recv())

                    self.wfile.write(reply_feedback())

        return PalmHandler

    def debug(self):
        """
        Starts the component and serves the http server forever.
        """
        server = HTTPServer((self.hostname, self.port), self._make_handler())
        server.handle_request()

    def start(self):
        """
        Starts the component and serves the http server forever.
        """
        server = HTTPServer((self.hostname, self.port), self._make_handler())
        server.serve_forever()


class CacheService(RepBypassService):
    """
    Cache service for clients and workers
    """
    def recv(self):
        message_data = self.listen_to.recv()
        message = PalmMessage()
        message.ParseFromString(message_data)
        instruction = message.function.split('.')[1]

        if instruction == 'set':
            if message.cache:
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

        if isinstance(return_value, str):
            self.listen_to.send_string(return_value)
        else:
            self.listen_to.send(return_value)
