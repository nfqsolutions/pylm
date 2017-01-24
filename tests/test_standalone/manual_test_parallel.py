# Test for the prototype of the client for the parallel client.

from threading import Thread
from pylm.servers import Master, Worker
from pylm.clients import Client


class NewWorker(Worker):
    @staticmethod
    def echo(message):
        print('Echoing message---')
        return message


def test_standalone_parallel_client():
    this_db_address = "inproc://db6"

    master = Master('master',
                    'inproc://pull6',
                    'inproc://push6',
                    'inproc://worker_pull6',
                    'inproc://worker_push6',
                    this_db_address)

    worker1 = NewWorker('worker1',
                        master.worker_push_address,
                        master.worker_pull_address,
                        master.db_address)
    worker2 = NewWorker('worker2',
                        master.worker_push_address,
                        master.worker_pull_address,
                        master.db_address)

    client = Client(master.push_address,
                    master.pull_address,
                    master.db_address,
                    'master')

    threads = [
        Thread(target=master.start),
        Thread(target=worker1.start),
        Thread(target=worker2.start)
    ]

    for t in threads:
        t.start()

    def message_generator():
        for j in range(10):
            yield str(j).encode('utf-8')

    print('******* Launch client')
    for i, m in enumerate(client.job('echo', message_generator())):
        print('************ Got something back', m, i)

    for t in threads:
        t.join(1)


if __name__ == '__main__':
    test_standalone_parallel_client()
