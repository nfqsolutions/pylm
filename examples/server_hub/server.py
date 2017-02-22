from pylm.servers import Server
import logging


class MyServer(Server):
    def foo(self, message):
        self.logger.warning('Got a message')
        return b'you sent me ' + message


if __name__ == '__main__':
    server = MyServer('server',
                      db_address='tcp://127.0.0.1:5555',
                      pull_address='tcp://127.0.0.1:5556',
                      pub_address='tcp://127.0.0.1:5557',
                      pipelined=True,
                      log_level=logging.DEBUG
                      )
    server.start()