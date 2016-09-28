from http.server import HTTPServer, BaseHTTPRequestHandler


class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.end_headers()

        data = self.rfile.read(int(self.headers.get('Content-Length')))
        print(data)

        self.wfile.write(data)

        return


if __name__ == '__main__':
    server = HTTPServer(('', 8888), MyHandler)
    server.serve_forever()
