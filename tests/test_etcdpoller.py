from threading import Thread

import requests

from pylm_ng.components.connections import PushConnection
from pylm_ng.components.core import Broker
from pylm_ng.components.endpoints import PullEndPoint, logger
from pylm_ng.persistence.etcd import EtcdPoller


def test_etcd_poller():
    """
    Tests the following sequence

    HTTP reply -> broker -> Push Connection -> Pull endpoint.
    :return:
    """

    broker = Broker(logger=logger, messages=20)
    endpoint_pull = PullEndPoint(logger=logger)
    poller = EtcdPoller('etcdpoller',
                        '/servers',
                        broker_address=broker.inbound_address,
                        logger=logger,
                        messages=10)
    push_component = PushConnection('test_push',
                                    listen_address=endpoint_pull.bind_address,
                                    broker_address=broker.outbound_address,
                                    logger=logger, messages=10)

    broker.register_inbound('etcdpoller',
                            route='test_push',
                            log='Redirecting etcd data')

    threads = [
        Thread(target=broker.start),
        Thread(target=endpoint_pull.start),
        Thread(target=poller.start),
        Thread(target=push_component.start)
        ]

    for t in threads:
        t.start()

    # This part here needs etcd running
    for i in range(10):
        requests.put('http://127.0.0.1:4001/v2/keys/servers/key', data='x')

    for t in threads:
        t.join()


if __name__ == '__main__':
    test_etcd_poller()
