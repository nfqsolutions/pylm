from pylm.chained import Server


class Step2(Server):
    def bar(self, message):
        self.logger.warning('Got a message')
        return b'got it too, after ' + message


if __name__ == '__main__':
    server = Step2('step2',
                   'tcp://127.0.0.1:5557',
                   'tcp://127.0.0.1:5559',
                   'last.baz',
                   'tcp://127.0.0.1:5558')
    server.start()
