from pylm.servers import Hub
import logging


server = Hub(name='hub',
             sub_address='tcp://127.0.0.1:5557',
             pub_address='tcp://127.0.0.1:5558',
             worker_pull_address='tcp://127.0.0.1:5559',
             worker_push_address='tcp://127.0.0.1:5560',
             db_address='tcp://127.0.0.1:5561',
             previous='server',
             pipelined=False)

if __name__ == '__main__':
    server.start()
