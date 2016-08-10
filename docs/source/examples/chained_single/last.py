from pylm.chained import LastServer


class Last(LastServer):
    def baz(self, message):
        self.logger.warning('Got a message')
        return b'ACK: ' + message


server = Last(name='last',
              pull_address='tcp://127.0.0.1:5559',
              push_address='tcp://127.0.0.1:5561',
              db_address='tcp://127.0.0.1:5560')

if __name__ == '__main__':
    server.start()
