from pylm.servers import Worker
import sys


class MyWorker(Worker):
    def foo(self, message):
        data = self.get('cached')
        return self.name.encode('utf-8') + data + message

server = MyWorker(sys.argv[1],
                  db_address='tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
