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
from pylm.parts.core import ComponentInbound, ComponentOutbound,\
    zmq_context, ComponentBypassInbound
from pylm.parts.messages_pb2 import BrokerMessage, PalmMessage
from http.server import HTTPServer, BaseHTTPRequestHandler
import zmq
import sys


class RepService(ComponentInbound):
    """
    RepService binds to a given socket and returns something.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param palm: True if the service gets PALM messages. False if they are binary
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
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )


class PullService(ComponentInbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param palm: True if service gets PALM messages. False if they are binary
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
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )
        self.resilience_socket = None

    def connect_resilience(self, resilience_address):
        """
        Creates and connects a socket to the resilience server
        :param resilience_address:
        :return:
        """
        self.logger.info('{} connected to the resilience service'.format(self.name))
        self.resilience_socket = zmq_context.socket(zmq.REQ)
        self.resilience_socket.connect(resilience_address)


class PushService(ComponentOutbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        """
        :param name: Name of the service
        :param listen_address: ZMQ socket address to bind to
        :param broker_address: ZMQ socket address of the broker
        :param logger: Logger instance
        :param palm: True if service gets PALM messages. False if they are binary
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
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )
        self.resilience_socket = None

    def connect_resilience(self, resilience_address):
        """
        Connect a socket to the resilience service
        :param resilience_address:
        :return:
        """
        self.logger.info('{} connected to the resilience service'.format(self.name))
        self.resilience_socket = zmq_context.socket(zmq.REQ)
        self.resilience_socket.connect(resilience_address)


class PubService(ComponentOutbound):
    """
    PullService binds to a socket waits for messages from a push-pull queue.

    :param name: Name of the service
    :param listen_address: ZMQ socket address to bind to
    :param broker_address: ZMQ socket address of the broker
    :param logger: Logger instance
    :param palm: True if service gets PALM messages. False if they are binary
    :param messages: Maximum number of messages. Defaults to infinity.
    :param pipelined: Defaults to False. Pipelined if publishes to a
        server, False if publishes to a client.
    """
    def __init__(self,
                 name,
                 listen_address,
                 broker_address="inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None,
                 messages=sys.maxsize,
                 pipelined=False):
        super(PubService, self).__init__(
            name,
            listen_address=listen_address,
            socket_type=zmq.PUB,
            reply=False,
            broker_address=broker_address,
            bind=True,
            palm=palm,
            logger=logger,
            cache=cache,
            messages=messages
        )
        self.pipelined = pipelined
        if self.pipelined:
            raise NotImplementedError('pipelined=True not supported yet')

        if not self.palm:
            raise ValueError('This part only works with PALM Components')
                    
        self.resilience_socket = None

    def connect_resilience(self, resilience_address):
        """
        Connect a socket to the resilience service
        :param resilience_address:
        :return:
        """
        self.logger.info('{} connected to the resilience service'.format(self.name))
        self.resilience_socket = zmq_context.socket(zmq.REQ)
        self.resilience_socket.connect(resilience_address)

    def start(self):
        """
        Call this function to start the component
        """
        self.listen_to.bind(self.listen_address)            

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
            message_data = self.broker.recv()
            self.logger.debug('Component {} Got message from broker'.format(self.name))
            message_data = self._translate_from_broker(message_data)

            if self.pipelined:
                topic = None
            else:
                message = PalmMessage()
                message.ParseFromString(message_data)
                topic = message.client

            for scattered in self.scatter(message_data):
                self.listen_to.send_multipart([topic.encode('utf-8'), scattered])
                self.logger.debug('Component {} Sent message'.format(self.name))

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
        if self.resilience_socket:
            self.logger.debug('{} sending to resilience service'.format(self.name))
            self.resilience_socket.send_multipart([b'to', message_data])
            self.resilience_socket.recv()
            self.logger.debug('----> Message registered in resilience service')

        else:
            self.logger.debug('----> No resilience service available')

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
        if self.resilience_socket:
            self.resilience_socket.send_multipart([b'from', message_data])
            action = self.resilience_socket.recv()
            if action == b'1':
                self.logger.debug('----> Resilience says go for it.')
                return message_data
            else:
                self.logger.debug('----> Resilience says discard the message')
                return ''
        else:
            self.logger.debug('----> No resilience service running')
            return message_data

    def _translate_from_broker(self, message_data):
        """
        See help of parent
        :param message_data:
        :return:
        """
        print('hi---------------')
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
                 palm=False,
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
        :param palm: True if the message is waiting is a PALM message. False if it is
          just a binary string
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

        self.palm = palm
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
        self.logger.info('Launch component {}'.format(self.name))
        initial_broker_message = BrokerMessage()
        initial_broker_message.key = '0'
        initial_broker_message.payload = b'0'
        self.broker.send(initial_broker_message.SerializeToString())

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
            # Workers use BrokerMessages, because they want to know the message ID.
            message_data = self.broker.recv()
            self.logger.debug('Got message {} from broker'.format(i))
            for scattered in self.scatter(message_data):
                self.push.send(scattered)
                self.handle_feedback(self.pull.recv())

            self.broker.send(self.reply_feedback())

    def cleanup(self):
        self.push.close()
        self.pull.close()
        self.broker.close()


class RepBypassService(ComponentBypassInbound):
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


class HttpService(ComponentInbound):
    """
    Similar to PullService, but the connection offered is an HTTP server
    that deals with inbound messages.

    ACHTUNG: this thing is deliberately single threaded
    """
    def __init__(self,
                 name,
                 hostname,
                 port,
                 broker_address = "inproc://broker",
                 palm=False,
                 logger=None,
                 cache=None):
        self.name = name.encode('utf-8')
        self.hostname = hostname
        self.port = port
        self.palm = palm
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
                self.send_response(200)
                self.end_headers()
                message_data = self.rfile.read(
                    int(
                        self.headers.get('Content-Length')
                    )
                )
                scattered_messages = scatter(message_data)

                if not scattered_messages:
                    self.wfile.write(b'0')

                else:
                    for scattered in scattered_messages:
                        scattered = _translate_to_broker(scattered)

                        if scattered:
                            broker.send(scattered)
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
