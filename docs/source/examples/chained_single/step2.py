from pylm.chained import Server


class Step2(Server):
    def bar(self, message):
        self.logger.warning('Got a message')
        return b'got it too, after ' + message


server = Step2(name='step2',
               pull_address='tcp://127.0.0.1:5557',
               next_address='tcp://127.0.0.1:5559',
               next_call='last.baz',
               db_address='tcp://127.0.0.1:5558')

if __name__ == '__main__':
    server.start()
