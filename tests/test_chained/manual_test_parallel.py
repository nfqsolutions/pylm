# Test for the prototype of the client for the parallel client.

from threading import Thread
from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage
from pylm.chained import Master, EndPoint, Worker, Client
import zmq


class NewWorker(Worker):
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
    this_log_address = "inproc://log6"
    this_perf_address = "inproc://perf6"
    this_ping_address = "inproc://ping6"
    this_db_address = "inproc://db6"

    endpoint = EndPoint('EndPoint',
                        this_log_address,
                        this_perf_address,
                        this_ping_address)

    master = Master('master',
                    'inproc://pull6',
                    'inproc://push6',
                    'inproc://worker_pull6',
                    'inproc://worker_push6',
                    this_db_address,
                    endpoint.log_address, endpoint.perf_address,
                    endpoint.ping_address, palm=True)

    worker1 = NewWorker('worker1',
                        master.worker_push_address,
                        master.worker_pull_address,
                        master.db_address,
                        this_log_address,
                        this_perf_address,
                        this_ping_address)
    worker2 = NewWorker('worker2',
                        master.worker_push_address,
                        master.worker_pull_address,
                        master.db_address,
                        this_log_address,
                        this_perf_address,
                        this_ping_address)

    client = Client(master.pull_address,
                    master.db_address,
                    'master')

    threads = [
        Thread(target=endpoint.start_debug),
        Thread(target=master.start),
        Thread(target=worker1.start),
        Thread(target=worker2.start),
        Thread(target=listener, args=(master.push_address,))
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
