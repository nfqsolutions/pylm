from pylm.standalone import Master
from pylm.parts.messages_pb2 import PalmMessage
import logging


class MyMaster(Master):
    def __init__(self, *args, **kwargs):
        self.counter = 0
        super(MyMaster, self).__init__(*args, **kwargs)
    
    def scatter(self, message):
        for i in range(3):
            yield message

    def gather(self, message):
        self.counter += 1

        if self.counter == 30:
            self.logger.critical('Changing the payload of the message')
            yield self.change_payload(message, b'final message')
        else:
            yield message

server = MyMaster(name='server',
                  pull_address='tcp://127.0.0.1:5555',
                  push_address='tcp://127.0.0.1:5556',
                  worker_pull_address='tcp://127.0.0.1:5557',
                  worker_push_address='tcp://127.0.0.1:5558',
                  db_address='tcp://127.0.0.1:5559',
                  palm=True,
                  debug_level=logging.WARNING)

if __name__ == '__main__':
    server.start()
