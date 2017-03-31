from pylm.servers import MuxWorker
import sys


class MyWorker(Worker):
    def foo(self, message):
        yield self.name.encode('utf-8') + b' processed ' + message + ' 1'
        yield self.name.encode('utf-8') + b' processed ' + message + ' 1'

server = MyWorker(sys.argv[1], 'tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
