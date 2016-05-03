import logging
import sys
from threading import Thread
from pylm.standalone import Client, Server, EndPoint

this_log_address = "inproc://log3"
this_perf_address = "inproc://perf3"
this_ping_address = "inproc://ping3"
this_rep_address = "inproc://rep3"


class RemoteServer(Server):
    def __init__(self, name, rep_address, log_address, perf_address,
                 ping_address, debug_level=logging.DEBUG, messages=sys.maxsize):
        super(RemoteServer, self).__init__(name,
                                           rep_address,
                                           log_address,
                                           perf_address,
                                           ping_address,
                                           debug_level=debug_level,
                                           messages=messages)

    def echo_data(self, data):
        """
        Simple function to test the standalone server.
        :param data:
        :return:
        """
        self.logger.info(data)
        return b'something'


def test_standalone():
    endpoint = EndPoint('EndPoint',
                        this_log_address,
                        this_perf_address,
                        this_ping_address,
                        messages=27)
    server = RemoteServer('Echo_server',
                          this_rep_address,
                          endpoint.log_address,
                          endpoint.perf_address,
                          endpoint.ping_address,
                          messages=9)

    client = Client(this_rep_address, 'Echo_server')

    print('Starting')

    threads = [
        Thread(target=endpoint.start_debug),
        Thread(target=server.start),
    ]

    for t in threads:
        t.start()

    for i in range(1, 10):
        retval = client.job('echo_data', str(i).encode('utf-8'))
        print(retval)


if __name__ == '__main__':
    test_standalone()
