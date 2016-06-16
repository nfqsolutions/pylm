# Test for the prototype of the client for the parallel client.

from threading import Thread
from pylm.components.core import zmq_context
from pylm.components.messages_pb2 import PalmMessage
from pylm.chained import Server, EndPoint, Client
import zmq


class NewMaster(Server):
    @staticmethod
    def echo(message):
        print('Echoing message---')
        return message


def listener(addr):
    pull = zmq_context.socket(zmq.PULL)
    pull.bind(addr)
    while True:
        message = PalmMessage()
        message.ParseFromString(pull.recv())
        print('LISTENER:', message)


def test_standalone_parallel_client():
    this_log_address = "inproc://log"
    this_perf_address = "inproc://perf"
    this_ping_address = "inproc://ping"
    this_db_address = "inproc://db"

    endpoint = EndPoint('EndPoint',
                        this_log_address,
                        this_perf_address,
                        this_ping_address)

    server = NewMaster('master',
                       'inproc://pull',
                       'inproc://next',
                       this_db_address,
                       endpoint.log_address,
                       endpoint.perf_address,
                       endpoint.ping_address,
                       palm=True)

    client = Client(server.pull_address,
                    server.db_address,
                    'master')

    threads = [
        Thread(target=endpoint.start_debug),
        Thread(target=server.start),
        Thread(target=listener, args=(server.next_address,))
    ]

    for t in threads:
        t.start()

    def message_generator():
        for j in range(10):
            yield str(j).encode('utf-8')

    print('******* Launch client')
    client.job('echo', message_generator())

    for t in threads:
        t.join(1)


if __name__ == '__main__':
    test_standalone_parallel_client()
