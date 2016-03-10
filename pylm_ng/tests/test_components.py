from pylm_ng.components.core import Broker, RepComponent, PushComponent, PullComponent
from pylm_ng.components.endpoints import logger, ReqEndPoint, PushEndPoint, PullEndPoint
from concurrent.futures import ThreadPoolExecutor


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
                                 broker_address=broker.bind_address,
                                 logger=logger,
                                 messages=10)
    broker.register_inbound('test',
                            log='Send to test component')

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(broker.start)
        executor.submit(endpoint.start)
        executor.submit(request_reply.start)


def test_request_push():
    """
    Tests the following sequence

    PUSH Endpoint -> Pull component -> Broker -> Push component -> PULL endpoint.
    :return:
    """
    broker = Broker(logger=logger, messages=10)
    endpoint_req = ReqEndPoint(logger=logger)
    endpoint_pull = PullEndPoint(logger=logger)
    print(endpoint_req.bind_address)
    rep_component = RepComponent('test_req',
                                 listen_to=endpoint_req.bind_address,
                                 broker_address=broker.bind_address,
                                 logger=logger,
                                 messages=10)
    print(endpoint_pull.bind_address)
    push_component = PushComponent('test_push',
                                   listen_to=endpoint_pull.bind_address,
                                   broker_address=broker.bind_address,
                                   logger=logger,
                                   messages=10)

    broker.register_inbound('test_req',
                            route='test_push',
                            log='Routing to test_push')

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(broker.start)
        executor.submit(push_component.start)
        executor.submit(rep_component.start)
        executor.submit(endpoint_pull.start)
        executor.submit(endpoint_req.start, function='test_request_pull')


if __name__ == '__main__':
    test_tests()
    test_request_reply()
    test_request_push()
