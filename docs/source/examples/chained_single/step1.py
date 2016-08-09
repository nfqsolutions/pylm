from pylm.chained import Server


class Step1(Server):
    def foo(self, message):
        self.logger.warning('Got a message')
        return b'you sent me ' + message


if __name__ == '__main__':
    server = Step1('step1',
                   'tcp://127.0.0.1:5555',
                   'tcp://120.0.0.1:5557',
                   'step2.bar'
                   'tcp://127.0.0.1:5556')
    server.start()
