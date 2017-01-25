from pylm.servers import Server


class MyServer(Server):
    def foo(self, message):
        self.logger.warning('Got a message')
        return b'you sent me ' + message


if __name__ == '__main__':
    server = MyServer('my_server', 'tcp://127.0.0.1:5555',
                      'tcp://127.0.0.1:5556', 'tcp://127.0.0.1:5557')
    server.start()
