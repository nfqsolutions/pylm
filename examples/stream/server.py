from pylm.servers import Server
import logging


class MyServer(Server):
    def __init__(self, *args, **kwargs):
        super(MyServer, self).__init__(*args, **kwargs)
        self.counter = 0

    def foo(self, message):
        self.logger.warning('Got a message')
        return b'you sent me ' + message

    def handle_stream(self, message):
        # if message is even
        if self.counter % 2 == 0:
            topic = 'even'

        else:
            topic = 'odd'

        # Remember to increment the stage
        message.stage += 1

        # Increment the message counter
        self.counter += 1
        return topic, message


if __name__ == '__main__':
    server = MyServer('my_server',
                      db_address='tcp://127.0.0.1:5555',
                      pull_address='tcp://127.0.0.1:5556',
                      pub_address='tcp://127.0.0.1:5557',
                      pipelined=True,
                      log_level=logging.DEBUG
                      )
    server.start()