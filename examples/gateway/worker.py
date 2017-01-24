import sys

from pylm.servers import Worker


class MyWorker(Worker):
    def foo(self, message):
        return self.name.encode('utf-8') + b' processed ' + message

server = MyWorker(sys.argv[1],
                  push_address='tcp://127.0.0.1:5558',
                  pull_address='tcp://127.0.0.1:5557',
                  db_address='tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
