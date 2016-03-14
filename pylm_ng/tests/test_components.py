from threading import Thread

from pylm_ng.components.connections import RepConnection, PushConnection, PullConnection
from pylm_ng.components.core import Broker
from pylm_ng.tests.endpoints import logger, ReqEndPoint, PullEndPoint, PushEndPoint


def test_tests():
    print("test")


def test_request_reply():
    """
    Tests the following sequence

    REQ Endpoint -> Rep connection -> broker
                 <-                <-
    :return:
    """
    broker = Broker(logger=logger, messages=10)
    endpoint = ReqEndPoint(logger=logger)
    request_reply = RepConnection('test',
                                  listen_address=endpoint.bind_address,
                                  broker_address=broker.inbound_address,
                                  logger=logger,
                                  messages=10)
    broker.register_inbound('test',
                            log='Send to test component')

    t1 = Thread(target=broker.start)
    t1.start()

    t2 = Thread(target=endpoint.start, kwargs={'function': 'this.function'})
    t2.start()

    t3 = Thread(target=request_reply.start)
    t3.start()

    for t in [t1, t2, t3]:
        t.join()

    endpoint.socket.close()
    broker.inbound.close()
    broker.outbound.close()


def test_request_push():
    """
    Tests the following sequence

    Req Endpoint -> Rep component -> Broker -> Push component -> PULL endpoint.
                 <-               <-
    :return:
    """
    broker = Broker(logger=logger, messages=20)
    endpoint_req = ReqEndPoint(logger=logger)
    endpoint_pull = PullEndPoint(logger=logger)

    rep_component = RepConnection('test_req',
                                  listen_address=endpoint_req.bind_address,
                                  broker_address=broker.inbound_address,
                                  logger=logger,
                                  messages=10)

    push_component = PushConnection('test_push',
                                    listen_address=endpoint_pull.bind_address,
                                    broker_address=broker.outbound_address,
                                    logger=logger,
                                    messages=10)

    broker.register_inbound('test_req',
                            route='test_push',
                            log='Routing to test_push')

    t1 = Thread(target=broker.start)
    t1.start()

    t2 = Thread(target=endpoint_req.start, kwargs={'function': 'this.function'})
    t2.start()

    t3 = Thread(target=endpoint_pull.start)
    t3.start()

    t4 = Thread(target=rep_component.start)
    t4.start()

    t5 = Thread(target=push_component.start)
    t5.start()

    for t in [t1, t2, t3, t4, t5]:
        t.join()

    endpoint_pull.socket.close()
    endpoint_req.socket.close()
    broker.inbound.close()
    broker.outbound.close()


def test_pull_push():
    """
    Tests the following sequence

    Push Endpoint -> pull component -> Broker -> Push component -> PULL endpoint.
    :return:
    """
    broker = Broker(logger=logger, messages=20)
    endpoint_push = PushEndPoint(logger=logger)
    endpoint_pull = PullEndPoint(logger=logger)

    pull_component = PullConnection('test_pull',
                                    listen_address=endpoint_push.bind_address,
                                    broker_address=broker.inbound_address,
                                    logger=logger,
                                    messages=10)

    push_component = PushConnection('test_push',
                                    listen_address=endpoint_pull.bind_address,
                                    broker_address=broker.outbound_address,
                                    logger=logger,
                                    messages=10)

    broker.register_inbound('test_pull',
                            route='test_push',
                            log='Routing to test_push')

    t1 = Thread(target=broker.start)
    t1.start()

    t2 = Thread(target=endpoint_push.start, kwargs={'function': 'this.function'})
    t2.start()

    t3 = Thread(target=endpoint_pull.start)
    t3.start()

    t4 = Thread(target=pull_component.start)
    t4.start()

    t5 = Thread(target=push_component.start)
    t5.start()

    for t in [t1, t2, t3, t4, t5]:
        t.join()

    endpoint_pull.socket.close()
    endpoint_push.socket.close()
    broker.inbound.close()
    broker.outbound.close()


if __name__ == '__main__':
    test_tests()
    test_request_reply()
    test_request_push()
    test_pull_push()
