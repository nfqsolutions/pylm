from pylm.standalone import Worker
import sys


class MyWorker(Worker):
    def __init__(self, *args, **kwargs):
        self.ncalls = 0
        super(MyWorker, self).__init__(*args, **kwargs)
    
    def foo(self, message):
        self.ncalls += 1
        data = self.get('cached')

        if self.ncalls%10 == 0:
            self.logger.info('Processed {} messages'.format(self.ncalls))
            
        return self.name.encode('utf-8') + data + message

server = MyWorker(sys.argv[1],
                  db_address='tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
