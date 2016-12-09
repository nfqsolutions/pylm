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

from pylm.parts.core import ComponentInbound, ComponentOutbound
from pylm.parts.core import zmq_context
from pylm.persistence.kv import DictDB
from pylm.parts.messages_pb2 import BrokerMessage, PalmMessage
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from uuid import uuid4
import traceback
import threading
import zmq
import sys


class GatewayRouter(ComponentInbound):
    """
    Router part of the Http gateway

    :param broker_address: Broker address
    :param cache: K-v database for the cache
    :param palm: If messages are palm messages
    :param logger: Logger class
    :param messages: Number of messages until it is shut down
    """
    def __init__(self, broker_address="inproc://broker", cache=DictDB(), palm=False, logger=None, messages=sys.maxsize):
        super(GatewayRouter, self).__init__(
            'gateway_router',
            'inproc://gateway_router',
            zmq.ROUTER,
            reply=False,
            broker_address=broker_address,
            bind=True,
            palm=True,
            cache=cache,
            logger=logger,
            messages=messages,
            )

    def _translate_to_broker(self, message_data):
        """
        Translate the message that the component has got to be digestible by the router.
        To be refactored. This method is overriden because it returns the message
        instead of returning the serialized message.

        :param message_data: Message data from the component to the router
        """
        palm_message = PalmMessage()
        palm_message.ParseFromString(message_data)
        payload = palm_message.payload
        instruction = palm_message.function.split('.')[1]
        pipeline = palm_message.pipeline

        if palm_message.HasField('cache'):
            broker_message_key = ''.join(['_', palm_message.pipeline, palm_message.cache])
        else:
            broker_message_key = str(uuid4())

        # I store the message to get it later when the message is outbound. See that
        # if I am just sending binary messages, I do not need to assign any envelope.

        # The same message cannot be used, because it confuses the router.
        if broker_message_key in self.cache:
            new_key = ''.join([broker_message_key, str(uuid4())[:8]])
            self.logger.error(
                'Message key {} found, changed to {}'.format(broker_message_key,
                                                             new_key)
            )
            broker_message_key = new_key

        self.logger.debug('Set message key {}'.format(broker_message_key))
        self.cache.set(broker_message_key, message_data)

        broker_message = BrokerMessage()
        broker_message.key = broker_message_key
        broker_message.instruction = instruction
        broker_message.payload = payload
        broker_message.pipeline = pipeline

        return broker_message
        
    def start(self):
        """
        Call this function to start the component
        """
        self.listen_to.bind(self.listen_address)
        self.logger.info('Launch component {}'.format(self.name))

        # The socket this part is listening to is blocked waiting for a
        # relevant response, not a dummy response that only unblocks.
        # Therefore, this part sends the message to the router and
        # handles the input from the dealer, that it is later redirected
        # to the inbound socket.
        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting messages'.format(self.name))
            response = self.listen_to.recv_multipart()

            if len(response) == 3:
                [target, empty, message_data] = response
                self.logger.debug('{} Got inbound message'.format(self.name))
                
                try:
                    for scattered in self.scatter(message_data):
                        scattered = self._translate_to_broker(scattered)
                        self.broker.send(scattered.SerializeToString())
                        self.logger.debug('Component {} blocked waiting for broker'.format(
                            self.name))
                        self.broker.recv()

                except:
                    self.logger.error('Error in scatter function')
                    lines = traceback.format_exception(*sys.exc_info())
                    self.logger.exception(lines[0])

            elif len(response) == 4 and response[0] == b'dealer':
                self.listen_to.send_multipart(response[1:])

    
class GatewayDealer(ComponentOutbound):
    """
    Generic component that connects a REQ socket to the broker, and a
    socket to an inbound external service.

    :param broker_address: ZMQ socket address for the broker,
    :param palm: The component is sending back a Palm message
    :param logger: Logger instance
    :param cache: Access to the cache of the server
    :param messages: Maximum number of inbound messages. Defaults to infinity.
    """
    def __init__(self,
                 broker_address="inproc://broker",
                 cache=None,
                 palm=True,
                 logger=None,
                 messages=sys.maxsize):
        self.name = 'gateway_dealer'.encode('utf-8')
        self.listen_to = zmq_context.socket(zmq.DEALER)
        self.listen_to.identity = b'dealer'
        self.bind = False
        self.listen_address = 'inproc://gateway_router'
        self.broker = zmq_context.socket(zmq.DEALER)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.logger = logger
        self.palm = palm
        self.cache = cache
        self.messages = messages
        self.reply = False
        self.last_message = b''

    def _translate_from_broker(self, message_data):
        """
        Translate the message that the component gets from the broker to the output format

        :param message_data:
        """
        broker_message = BrokerMessage()
        broker_message.ParseFromString(message_data)

        message_data = self.cache.get(broker_message.key)
        # Clean up the cache. It is an outbound message and no one will
        # ever need the full message again.
        self.logger.debug('DELETE: {}'.format(broker_message.key))
        self.cache.delete(broker_message.key)
        palm_message = PalmMessage()
        palm_message.ParseFromString(message_data)
        palm_message.payload = broker_message.payload
        message_data = palm_message.SerializeToString()
            
        return palm_message.client.encode('utf-8'), message_data
        
    def start(self):
        """
        Call this function to start the component
        """
        self.listen_to.connect(self.listen_address)

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
            [me, message_data] = self.broker.recv_multipart()
            
            self.logger.debug('Component {} Got message from broker'.format(self.name))
            target, message_data = self._translate_from_broker(message_data)

            self.listen_to.send_multipart([target, b'', message_data])
            self.broker.send(b'')

            
class MyServer(ThreadingMixIn, HTTPServer):
    """Server that handles multiple requests"""

    
class MyHandler(BaseHTTPRequestHandler):
    @staticmethod
    def path_parser(path):
        """
        Function that parses the path to get the function
        """
        function = path.split('/')[1]
        
        if function and '.' not in function:
            function = '.'.join(['_', function])

        return function
        
    def do_GET(self):
        socket = zmq_context.socket(zmq.REQ)
        socket.connect('inproc://gateway_router')
        
        function = self.path_parser(self.path)
        
        if function:
            message = PalmMessage()
            message.pipeline = str(uuid4())

            message.function = self.path_parser(self.path)
            
            content_length = self.headers.get('content-length')
            if content_length:
                message.payload = self.rfile.read(int(content_length))
            else:
                message.payload = b''
                
            message.stage = 0
            message.client = 'HttpGateway'
            
            socket.send(message.SerializeToString())
            message = socket.recv()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            message = b'Not found'
            
        self.wfile.write(message)

        socket.close()
        return

    def do_POST(self):
        """
        The two methods work the exact same way
        """
        self.do_GET()
        
    
class HttpGateway(object):
    def __init__(self, hostname='', port=8888,
                 broker_inbound_address="inproc://broker",
                 broker_outbound_address="inproc://broker",
                 cache=DictDB(), palm=False, logger=None):
        self.router = GatewayRouter(broker_inbound_address, cache, palm, logger=logger)
        self.dealer = GatewayDealer(broker_outbound_address, cache, palm, logger=logger)
        self.handler = MyHandler
        self.server = MyServer((hostname, port), self.handler)
        self.logger = logger
        self.port = port
        
    def start(self):
        router_thread = threading.Thread(target=self.router.start)
        dealer_thread = threading.Thread(target=self.dealer.start)

        self.logger.info("Starting HttpGateway router component (inbound)")
        router_thread.start()
        self.logger.info("Starting HttpGateway dealer component (outbound)")
        dealer_thread.start()
        self.logger.info("Serving HttpGateway on port {}".format(self.port))
        self.server.serve_forever()

    def debug(self):
        router_thread = threading.Thread(target=self.router.start)
        dealer_thread = threading.Thread(target=self.dealer.start)

        router_thread.start()
        dealer_thread.start()
        self.server.serve_forever()


# def test_gateway():
#     def dummy_response():
#         dummy_router = zmq_context.socket(zmq.ROUTER)
#         dummy_router.bind('inproc://broker')
#
#         while True:
#             [target, empty, message] = dummy_router.recv_multipart()
#             dummy_router.send_multipart([target, empty, b'0'])
#
#             broker_message = BrokerMessage()
#             broker_message.ParseFromString(message)
#             print('at the router: \n', broker_message)
#
#             dummy_router.send_multipart([b'gateway_dealer', empty, message])
#             [target, message] = dummy_router.recv_multipart()
#
#     response_thread = threading.Thread(target=dummy_response)
#     response_thread.start()
#
#     gateway = HttpGateway(logger=logging)
#     gateway.start()
