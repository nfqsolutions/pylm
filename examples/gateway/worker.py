import sys

from pylm.servers import Worker


class MyWorker(Worker):
    def function(self, message):
        return b'acknowledged'

server = MyWorker(sys.argv[1], db_address='tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
