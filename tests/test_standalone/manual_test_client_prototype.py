# Test for the prototype of the client for the parallel client.

from threading import Thread
from pylm_ng.standalone import Master, EndPoint, Worker, ParallelClient


def test_standalone_parallel_client():
    this_log_address = "inproc://log6"
    this_perf_address = "inproc://perf6"
    this_ping_address = "inproc://ping6"
    endpoint = EndPoint('EndPoint',
                        this_log_address,
                        this_perf_address,
                        this_ping_address)
    master = Master('master', 'inproc://pull6', 'inproc://push6',
                    'inproc://worker_pull6', 'inproc://worker_push6',
                    endpoint.log_address, endpoint.perf_address,
                    endpoint.ping_address, palm=True)

    worker1 = Worker('worker1',
                     master.worker_push_address,
                     master.worker_pull_address,
                     this_log_address,
                     this_perf_address,
                     this_ping_address)
    worker2 = Worker('worker2',
                     master.worker_push_address,
                     master.worker_pull_address,
                     this_log_address,
                     this_perf_address,
                     this_ping_address)

    client = ParallelClient(master.push_address,
                            master.pull_address,
                            'master')

    threads = [
        Thread(target=endpoint._start_debug),
        Thread(target=master.start),
        Thread(target=worker1.start),
        Thread(target=worker2.start)
    ]

    for t in threads:
        t.start()

    def message_generator():
        for i in range(10):
            yield str(i).encode('utf-8')

    print('******* Launch client')
    for i, m in enumerate(client.job('somefunction', message_generator(), 10)):
        print('************ Got something back', m, i)

    for t in threads:
        t.join(1)


if __name__ == '__main__':
    test_standalone_parallel_client()
