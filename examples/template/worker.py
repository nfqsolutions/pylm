from pylm.standalone.servers import Worker
import sys


class MyWorker(Worker):
    def foo(self, message):
        return self.name.encode('utf-8') + b' processed ' + message

server = MyWorker(sys.argv[1], 'tcp://127.0.0.1:5559',
                  pull_address= 'tcp://127.0.0.1:5557',
                  push_address= 'tcp://127.0.0.1:5558')

if __name__ == '__main__':
    server.start()
