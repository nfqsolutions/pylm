from pylm.chained import Server


class Step1(Server):
    def foo(self, message):
        self.logger.warning('Got a message')
        return b'you sent me ' + message


server = Step1(name='step1',
               pull_address='tcp://127.0.0.1:5555',
               next_address='tcp://127.0.0.1:5557',
               next_call='step2.bar',
               db_address='tcp://127.0.0.1:5556')

if __name__ == '__main__':
    server.start()
