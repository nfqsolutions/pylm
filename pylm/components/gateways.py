from pylm.components.core import zmq_context
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import threading
import sys
import zmq


class HttpServer(object):
    """
    HttpServer that turns a PALM server into a web server.
    """
    def __init__(self,
                 broker_address="inproc://broker",
                 logger=None,
                 cache=None,
                 messages=sys.maxsize):
        # All the sockets and configuration
        self.inbound_name = 'http_server_inbound'
        self.outbound_name = 'http_server_outbound'
        self.router_address = 'inprox://http_server_router'

        self.inbound_socket = zmq_context.socket(zmq.PULL)
        self.outbound_socket = zmq_context.socket(zmq.PUSH)
        self.router = zmq_context.socket(zmq.ROUTER)

    def _router_thread(self):
        self.router.bind(self.router_address)

    def _server_thread(self):
        pass

    def _translate_to_broker(self):
        pass

    def _translate_from_broker(self):
        pass


class Offloader(object):
    """
    Offloader to an external elastic service for workers
    """
    def __init__(self):
        pass


#### From the tests

def router():
    push = context.socket(zmq.PUSH)
    pull = context.socket(zmq.PULL)
    router = context.socket(zmq.ROUTER)
    push.bind('tcp://127.0.0.1:5555')
    pull.bind('tcp://127.0.0.1:5556')
    router.bind('inproc://router')
    
    while True:
        [dest, empty, message] = router.recv_multipart()
        print('Sending to an external process')
        push.send_multipart([dest, message])
        [dest, message] = pull.recv_multipart()
        print('Got something from an external process')
        router.send_multipart([dest, b'', message])


class MyServer(ThreadingMixIn, HTTPServer):
    """Server that handles multiple requests"""

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        socket = context.socket(zmq.REQ)
        socket.connect('inproc://router')

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

def run():
    server_address = ('localhost', 8888)
    httpd = MyServer(server_address, MyHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    threads = [
        threading.Thread(target=run),
        threading.Thread(target=router)
    ]

    for t in threads:
        t.start()
        
    print('Starting http server in a separate thread')
 
