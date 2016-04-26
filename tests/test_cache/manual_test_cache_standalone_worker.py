from pylm_ng.standalone import ParallelClient, Master, Worker, EndPoint
from threading import Thread


class NewWorker(Worker):
    def test_cache(self, message):
        self.perfcounter.tick('Pre-get {}'.format(self.name))
        value = self.get(message.decode('utf-8'))
        self.perfcounter.tick('Post-get {}'.format(self.name))
        return value


def test_cache_worker():
    this_log_address = "inproc://log10"
    this_perf_address = "inproc://perf10"
    this_ping_address = "inproc://ping10"
    this_rep_address = "inproc://rep10"

    # In this test, these address are connected, but no server is
    # actually listening
    this_push_address = "inproc://push10"
    this_pull_address = "inproc://pull10"
    this_worker_push_address = "inproc://worker_push10"
    this_worker_pull_address = "inproc://worker_pull10"

    endpoint = EndPoint("EndPoint",
                        this_log_address,
                        this_perf_address,
                        this_ping_address)

    master = Master('master', this_pull_address, this_push_address,
                    this_worker_pull_address, this_worker_push_address,
                    this_rep_address,
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

    threads = [
        Thread(target=endpoint._start_debug),
        Thread(target=master.start),
        Thread(target=worker1.start),
        Thread(target=worker2.start)
    ]

    for t in threads:
        t.start()

    client = ParallelClient(this_push_address, this_pull_address,
                            this_rep_address, "Server")

    key = client.set(b'something')

    new_key = client.set(b'otherthing', 'otherkey')
    assert new_key == 'otherkey'

    data = client.get(key)
    assert data == b'something'

    data = client.get(new_key)
    assert data == b'otherthing'

    key_list = [key.encode('utf-8'), new_key.encode('utf-8')]
    value_list = [b'something', b'otherthing']
    for k, m in zip(value_list, client.job('test_cache', key_list, 2)):
        print('Assertion:', k, m)
        assert k == m

    for t in threads:
        t.join(1)


if __name__ == '__main__':
    test_cache_worker()
