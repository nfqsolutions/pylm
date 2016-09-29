from pylm.remote.server import RequestHandler, DebugServer, WSGIApplication


class MyHandler(RequestHandler):
    def foo(self, payload):
        return payload + b' processed online'
    
app = WSGIApplication(MyHandler)

if __name__ == '__main__':
    server = DebugServer('localhost', 8888, MyHandler)
    server.serve_forever()
