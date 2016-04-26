from pylm_ng.standalone import ParallelClient, Master, Worker, EndPoint
from threading import Thread


def test_cache_worker():
    this_log_address = "inproc://log9"
    this_perf_address = "inproc://perf9"
    this_ping_address = "inproc://ping9"
    this_rep_address = "inproc://rep9"

    # In this test, these address are connected, but no server is
    # actually listening
    this_push_address = "inproc://push9"
    this_pull_address = "inproc://pull9"
    this_worker_push_address = "inproc://worker_push9"
    this_worker_pull_address = "inproc://worker_pull9"

    endpoint = EndPoint("EndPoint",
                        this_log_address,
                        this_perf_address,
                        this_ping_address,
                        messages=26)

    master = Master('master', this_pull_address, this_push_address,
                    this_worker_pull_address, this_worker_push_address,
                    this_rep_address,
                    endpoint.log_address, endpoint.perf_address,
                    endpoint.ping_address, palm=True)

    threads = [
        Thread(target=endpoint._start_debug),
        Thread(target=master.start)
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

    assert key == client.delete(key)
    assert new_key == client.delete(new_key)

    for t in threads:
        t.join()


if __name__ == '__main__':
    test_cache_worker()
