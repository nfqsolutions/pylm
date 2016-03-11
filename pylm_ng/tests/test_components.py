from pylm_ng.components.core import Broker, RepComponent, PushComponent
from pylm_ng.components.endpoints import logger, ReqEndPoint, PullEndPoint
from concurrent.futures import ThreadPoolExecutor
from threading import Thread


def test_tests():
    print("test")


def test_request_reply():
    """
    Tests the following sequence

    REQ Endpoint -> Rep component -> broker
                 <-               <-
    :return:
    """
    broker = Broker(logger=logger, messages=10)
    endpoint = ReqEndPoint(logger=logger)
    request_reply = RepComponent('test',
                                 listen_to=endpoint.bind_address,
                                 broker_address=broker.inbound_address,
                                 logger=logger,
                                 messages=10)
    broker.register_inbound('test',
                            reply=request_reply.reply,
                            log='Send to test component')

    t1 = Thread(target=broker.start)
    t1.start()

    t2 = Thread(target=endpoint.start, kwargs={'function': 'this.function'})
    t2.start()

    t3 = Thread(target=request_reply.start)
    t3.start()

    for t in [t1, t2, t3]:
        t.join()


def test_request_push():
    """
    Tests the following sequence

    PUSH Endpoint -> Pull component -> Broker -> Push component -> PULL endpoint.
    :return:
    """
    broker = Broker(logger=logger, messages=20)
    endpoint_req = ReqEndPoint(logger=logger)
    endpoint_pull = PullEndPoint(logger=logger)
    print(endpoint_req.bind_address)
    rep_component = RepComponent('test_req',
                                 listen_to=endpoint_req.bind_address,
                                 broker_address=broker.inbound_address,
                                 logger=logger,
                                 messages=10)
    print(endpoint_pull.bind_address)
    push_component = PushComponent('test_push',
                                   listen_to=endpoint_pull.bind_address,
                                   broker_address=broker.outbound_address,
                                   logger=logger,
                                   messages=10)

    broker.register_inbound('test_req',
                            route='test_push',
                            reply=rep_component.reply,
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


if __name__ == '__main__':
    test_tests()
    test_request_reply()
    test_request_push()
