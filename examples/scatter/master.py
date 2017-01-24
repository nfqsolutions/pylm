from pylm.servers import Master


class MyMaster(Master):
    def scatter(self, message):
        for i in range(3):
            yield message

server = MyMaster(name='server',
                  pull_address='tcp://127.0.0.1:5555',
                  pub_address='tcp://127.0.0.1:5556',
                  worker_pull_address='tcp://127.0.0.1:5557',
                  worker_push_address='tcp://127.0.0.1:5558',
                  db_address='tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
