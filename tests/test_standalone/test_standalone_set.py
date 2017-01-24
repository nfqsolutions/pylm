import logging
from threading import Thread

from pylm.clients import Client
from pylm.servers import Server

this_log_address = "inproc://log4"
this_perf_address = "inproc://perf4"
this_ping_address = "inproc://ping4"
this_rep_address = "inproc://rep4"


class RemoteServer(Server):
    def __init__(self, name, rep_address, log_level=logging.DEBUG):
        super(RemoteServer, self).__init__(name,
                                           rep_address,
                                           log_level=log_level)

    def echo_data(self, data):
        """
        Simple function to test the standalone server.
        :param data:
        :return:
        """
        self.logger.info(data)
        return b'something'


def test_standalone():
    server = RemoteServer('Echo_server',
                          this_rep_address)

    client = Client(this_rep_address, 'Echo_server')

    print('Starting')

    t2 = Thread(target=server.start)
    t2.daemon = True
    t2.start()

    keys = []

    for i in range(1, 10):
        retval = client.set(str(i).encode('utf-8'))
        keys.append(retval)

    for k in keys:
        retval = client.delete(k)
        assert retval == k

if __name__ == '__main__':
    test_standalone()
