from pylm.standalone import Master
import logging

server = Master(name='server',
                pull_address='tcp://127.0.0.1:5555',
                push_address='tcp://127.0.0.1:5556',
                worker_pull_address='tcp://127.0.0.1:5557',
                worker_push_address='tcp://127.0.0.1:5558',
                db_address='tcp://127.0.0.1:5559',
                palm=True,
                debug_level=logging.DEBUG)

if __name__ == '__main__':
    server.start()
