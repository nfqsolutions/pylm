from pylm_ng.components.core import Broker
from pylm_ng.daemons.extra_components import EtcdPoller
from pylm_ng.components.connections import PushConnection
from pylm_ng.tests.endpoints import PullEndPoint, logger
from threading import Thread


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

    for t in threads:
        t.join()


if __name__ == '__main__':
    test_etcd_poller()
