from http.server import HTTPServer, BaseHTTPRequestHandler
from pylm.components.messages_pb2 import BrokerMessage


class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        data = self.rfile.read(int(self.headers.get('Content-Length')))
        message = BrokerMessage()
        message.ParseFromString(data)
        message.payload = message.payload + b' processed online'
        print(message)

        self.wfile.write(message.SerializeToString())

        return


if __name__ == '__main__':
    server = HTTPServer(('', 8888), MyHandler)
    server.serve_forever()
