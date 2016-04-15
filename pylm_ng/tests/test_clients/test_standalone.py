from pylm_ng.servers.standalone import StandaloneServer
from pylm_ng.daemons.standalone import StandaloneEndPoint
from pylm_ng.clients.standalone import StandaloneClient
from threading import Thread
import logging


this_log_address = "inproc://log3"
this_perf_address = "inproc://perf3"
this_ping_address = "inproc://ping3"
this_rep_address = "inproc://rep3"


class RemoteServer(StandaloneServer):
    def __init__(self, name, rep_address, log_address, perf_address,
                 ping_address, debug_level=logging.DEBUG):
        super(RemoteServer, self).__init__(name,
                                           rep_address,
                                           log_address,
                                           perf_address,
                                           ping_address,
                                           debug_level=debug_level)

    def echo_data(self, data):
        """
        Simple function to test the standalone server.
        :param data:
        :return:
        """
        self.logger.info(data)
        return b'something'


def test_standalone():
    endpoint = StandaloneEndPoint('EndPoint',
                                  this_log_address,
                                  this_perf_address,
                                  this_ping_address)
    server = RemoteServer('Echo_server',
                          this_rep_address,
                          endpoint.log_address,
                          endpoint.perf_address,
                          endpoint.ping_address)

    client = StandaloneClient(this_rep_address, 'Echo_server')

    print('Starting')
    t1 = Thread(target=endpoint._start_debug)
    t1.daemon = True
    t1.start()

    t2 = Thread(target=server.start)
    t2.daemon = True
    t2.start()

    for i in range(1, 10):
        retval = client.job('echo_data', str(i).encode('utf-8'))
        print(retval)

if __name__ == '__main__':
    test_standalone()
