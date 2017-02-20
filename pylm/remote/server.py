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

from wsgiref.simple_server import make_server
from collections import namedtuple
from pylm.parts.messages_pb2 import PalmMessage

Request = namedtuple('Request', 'method data')


class RequestHandler(object):
    def __init__(self, environ):
        self.environ = environ
        length = int(environ.get('CONTENT_LENGTH'), 0)
        self.request = Request(method=environ.get('REQUEST_METHOD'),
                               data=environ.get('wsgi.input').read(length))
        self.message = None

    def handle(self):
        if self.request.method == 'POST':
            try:
                message = PalmMessage()
                message.ParseFromString(self.request.data)

                # This exports the message information
                self.message = message
                instruction = message.function.split('.')[1]
                result = getattr(self, instruction)(message.payload)
                message.payload = result
                response_body = message.SerializeToString()
                status = '200 OK'

            except Exception as exc:
                status = '500 Internal Server Error'
                response_body = b''
        else:
            status = '405 Method not allowed'
            response_body = b''

        return status, response_body


class WSGIApplication(object):
    def __init__(self, handler):
        self.handler = handler

    def __call__(self, environ, start_response):
        my_handler = self.handler(environ)
        status, response = my_handler.handle()
        response_headers = [
            ('Content-Type', 'application/octet-stream'),
            ('Content-Length', str(len(response)))
        ]

        start_response(status, response_headers)
        yield response


class DebugServer(object):
    def __init__(self, host, port, handler):
        my_application = WSGIApplication(handler)
        self.httpd = make_server(host, port, my_application)

    def serve_forever(self):
        self.httpd.serve_forever()

    def handle_request(self):
        self.httpd.handle_request()
