from threading import Thread

from pylm.parts.connections import PushConnection
from pylm.parts.core import Router
from pylm.parts.endpoints import PullEndPoint, logger
from pylm.parts.services import PullService
from pylm.parts.utils import Pinger


def test_pinger():
    """
    Tests the following sequence

    Pinger -> Pull End Point.

    :return:
    """
    endpoint_pull = PullEndPoint(logger=logger)
    pinger = Pinger(listen_address=endpoint_pull.bind_address,
                    every=0.01,
                    pings=10)

    threads = [
        Thread(target=endpoint_pull.start),
        Thread(target=pinger.start)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


def test_pinger_with_broker():
    """
    Tests the following sequence

    Pinger -> Pull service -> Router -> Push connection -> Pull endpoint.
    :return:
    """
    broker = Router(logger=logger, messages=20)
    pull_service = PullService('test',
                               'inproc://pullservice',
                               broker_address=broker.inbound_address,
                               logger=logger,
                               messages=10
                               )
    push_connection = PushConnection('test_push',
                                     listen_address='inproc://pushconnection',
                                     broker_address=broker.outbound_address,
                                     logger=logger,
                                     messages=10)
    endpoint_pull = PullEndPoint(bind_address=push_connection.listen_address,
                                 logger=logger)
    broker.register_inbound('test',
                            route='test_push',
                            log='Redirecting from pull to push')

    pinger = Pinger(listen_address=pull_service.listen_address,
                    every=0.01,
                    pings=10)

    threads = [
        Thread(target=broker.start),
        Thread(target=pull_service.start),
        Thread(target=push_connection.start),
        Thread(target=endpoint_pull.start),
        Thread(target=pinger.start)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

if __name__ == '__main__':
    test_pinger()
    test_pinger_with_broker()
