from pylm.components.core import ComponentInbound, ComponentOutbound, Router
from pylm.components.core import zmq_context
from pylm.persistence.kv import DictDB
from pylm.components.messages_pb2 import BrokerMessage, PalmMessage
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from uuid import uuid4
import threading
import logging
import zmq
import sys


class HttpGatewayRouter(ComponentInbound):
    """
    Router part of the Http gateway

    :param broker_address: Broker address
    :param cache: K-v database for the cache
    :param palm: If messages are palm messages
    :param logger: Logger class
    :param messages: Number of messages until it is shut down
    """
    def __init__(self, broker_address="inproc://broker", cache=DictDB(), palm=False, logger=None, messages=sys.maxsize):
        super(HttpGatewayRouter, self).__init__(
            'gateway_router',
            'inproc://gateway_router',
            zmq.ROUTER,
            reply=False,
            broker_address=broker_address,
            bind=True,
            palm=palm,
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
        if self.palm:
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
        else:
            broker_message_key = str(uuid4())
            payload = message_data
            instruction = ''
            pipeline = ''

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

        for i in range(self.messages):
            self.logger.debug('Component {} blocked waiting messages'.format(self.name))
            response = self.listen_to.recv_multipart()

            if len(response) == 3:
                [target, empty, message_data] = response
                print('target: ', target, 'message: ', message_data)
                self.logger.debug('{} Got inbound message'.format(self.name))
                
                # There is no possibility to scatter messages here.
                scattered = self._translate_to_broker(message_data)
                print('Set key', 'target'+scattered.key)
                self.cache.set('target'+scattered.key, target) 
                self.broker.send(scattered.SerializeToString())
                self.logger.debug('Component {} blocked waiting for broker'.format(self.name))
                self.broker.recv()
                
            elif len(response) == 4 and response[0] == b'dealer':
                print('Unblocking client')
                self.listen_to.send_multipart(response[1:])

    
class HttpGatewayDealer(ComponentOutbound):
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
                 palm=False,
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

        if self.palm:
            message_data = self.cache.get(broker_message.key)
            # Clean up the cache. It is an outbound message and no one will
            # ever need the full message again.
            self.logger.debug('DELETE: {}'.format(broker_message.key))
            self.cache.delete(broker_message.key)
            palm_message = PalmMessage()
            palm_message.ParseFromString(message_data)
            palm_message.payload = broker_message.payload
            message_data = palm_message.SerializeToString()
        else:
            message_data = broker_message.payload

        print('Get key:', 'target'+broker_message.key)
        target = self.cache.get('target'+broker_message.key)
        
        self.cache.delete('target'+broker_message.key)
            
        return target, message_data
        
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
    def do_GET(self):
        socket = zmq_context.socket(zmq.REQ)
        socket.connect('inproc://gateway_router')
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'start...')

        if self.path == '/':
            socket.send(str(threading.currentThread().getName()).encode('utf-8'))
            message = socket.recv()
        else:
            message = b''
            
        self.wfile.write(message)
        self.wfile.write(b'\n')

        socket.close()
        return

    
class HttpGateway(object):
    def __init__(self, hostname='', port=8888, broker_address="inproc://broker", cache=DictDB(), palm=False, logger=None):
        self.router = HttpGatewayRouter(broker_address, cache, palm, logger)
        self.dealer = HttpGatewayDealer(broker_address, cache, palm, logger)
        self.server = MyServer((hostname, port), MyHandler)
        
    def start(self):
        router_thread = threading.Thread(target=self.router.start)
        dealer_thread = threading.Thread(target=self.dealer.start)

        router_thread.start()
        dealer_thread.start()
        self.server.serve_forever()

    def debug(self):
        router_thread = threading.Thread(target=self.router.start)
        dealer_thread = threading.Thread(target=self.dealer.start)

        router_thread.start()
        dealer_thread.start()
        self.server.serve_forever()

        
def test_http_gateway_router():
    """
    This tests only the router part of the HTTP gateway component
    """
    # A simple REP socket to act as a router. Just rebounds the message
    def dummy_response():
        dummy_router = zmq_context.socket(zmq.REP)
        dummy_router.bind('inproc://broker')
        msg = dummy_router.recv()
        broker_message = BrokerMessage()
        broker_message.ParseFromString(msg)
        print('At the router:\n', broker_message)
        dummy_router.send(msg)

    def dummy_initiator():
        dummy_client = zmq_context.socket(zmq.REQ)
        dummy_client.connect('inproc://gateway_router')
        dummy_client.send(b'This is a message')
        #print(dummy_client.recv())

    response_thread = threading.Thread(target=dummy_response)
    response_thread.start()

    starter_thread = threading.Thread(target=dummy_initiator)
    starter_thread.start()

    gateway = HttpGatewayRouter(logger=logging, messages=1)
    gateway.start()

    
def test_complete_gateway():
    """
    Test function for the complete gateway with a dummy router.
    """
    cache = DictDB()
    
    def dummy_response():
        dummy_router = zmq_context.socket(zmq.ROUTER)
        dummy_router.bind('inproc://broker')
        [target, empty, message] = dummy_router.recv_multipart()
        dummy_router.send_multipart([target, empty, b'0'])
        
        broker_message = BrokerMessage()
        broker_message.ParseFromString(message)
        print('at the router: \n', broker_message)
        
        dummy_router.send_multipart([b'gateway_dealer', empty, message])
        [target, message] = dummy_router.recv_multipart()

    def dummy_initiator():
        dummy_client = zmq_context.socket(zmq.REQ)
        dummy_client.connect('inproc://gateway_router')
        dummy_client.send(b'This is a message')
        print('Final message at the initiator ->', dummy_client.recv())

    response_thread = threading.Thread(target=dummy_response)
    response_thread.start()

    starter_thread = threading.Thread(target=dummy_initiator)
    starter_thread.start()

    dealer_component = HttpGatewayDealer(cache=cache, logger=logging, messages=1)
    dealer_thread = threading.Thread(target=dealer_component.start)
    dealer_thread.start()

    gateway = HttpGatewayRouter(cache=cache, logger=logging, messages=2)
    gateway.start()


def test_gateway():
    def dummy_response():
        dummy_router = zmq_context.socket(zmq.ROUTER)
        dummy_router.bind('inproc://broker')

        while True:
            [target, empty, message] = dummy_router.recv_multipart()
            dummy_router.send_multipart([target, empty, b'0'])
        
            broker_message = BrokerMessage()
            broker_message.ParseFromString(message)
            print('at the router: \n', broker_message)
        
            dummy_router.send_multipart([b'gateway_dealer', empty, message])
            [target, message] = dummy_router.recv_multipart()

    response_thread = threading.Thread(target=dummy_response)
    response_thread.start()

    gateway = HttpGateway(logger=logging)
    gateway.start()
    
    
if __name__ == "__main__":
    #test_http_gateway_router()
    #test_complete_gateway()
    test_gateway()
