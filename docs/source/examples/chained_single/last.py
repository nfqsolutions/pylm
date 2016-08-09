from pylm.chained import LastServer


class Last(LastServer):
    def baz(self, message):
        self.logger.warning('Got a message')
        return b'ACK: ' + message


if __name__ == '__main__':
    server = Last('step1',
                  'tcp://127.0.0.1:5559',
                  'tcp://120.0.0.1:5561',
                  'tcp://127.0.0.1:5560')
    server.start()
