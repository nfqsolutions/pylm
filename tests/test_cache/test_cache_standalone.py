from pylm_ng.standalone import Client, ParallelClient, Server, Master, EndPoint
from threading import Thread


def test_standalone_server():
    this_log_address = "inproc://log7"
    this_perf_address = "inproc://perf7"
    this_ping_address = "inproc://ping7"
    this_rep_address = "inproc://rep7"

    endpoint = EndPoint("EndPoint",
                        this_log_address,
                        this_perf_address,
                        this_ping_address,
                        messages=11)

    server = Server("cache_test", this_rep_address,
                    this_log_address, this_perf_address,
                    this_ping_address, messages=6)

    threads = [
        Thread(target=endpoint._start_debug),
        Thread(target=server.start)
    ]

    for t in threads:
        t.start()

    client = Client(this_rep_address, "cache_test")
    key = client.set(b'something')
    print('***** Got key', key)

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
    test_standalone_server()
