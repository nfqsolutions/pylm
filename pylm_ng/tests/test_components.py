from pylm_ng.components.core import Broker, RepComponent, PushComponent, PullComponent
from pylm_ng.components.endpoints import logger, ReqEndpoint, PushEndPoint, PullEndPoint
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
    endpoint = ReqEndpoint(logger=logger)
    request_reply = RepComponent('test',
                                 listen_to=endpoint.bind_address,
                                 broker_address=broker.bind_address,
                                 logger=logger,
                                 messages=10)
    broker.register_component('test',
                              log='Send to test component')

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(broker.start)
        executor.submit(endpoint.start)
        executor.submit(request_reply.start)


def test_push_pull():
    """
    Tests the following sequence

    PUSH Endpoint -> Pull component -> Broker -> Push component -> PULL endpoint.
    :return:
    """
    broker = Broker(logger=logger, messages=10)
    endpoint_push = PushEndPoint(logger=logger)
    endpoint_pull = PullEndPoint(logger=logger)
    push_component = PushComponent('test_push',
                                   listen_to=endpoint_pull.bind_address,
                                   broker_address=broker.bind_address,
                                   logger=logger,
                                   messages=10)
    pull_component = PullComponent('test_pull',
                                   listen_to=endpoint_push.bind_address,
                                   broker_address=broker.bind_address,
                                   logger=logger,
                                   messages=10)

    broker.register_component('test_pull',
                              route='test_push',
                              log='Routing...')

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(broker.start)
        executor.submit(endpoint_pull.start)
        executor.submit(endpoint_push.start)
        executor.submit(push_component.start)
        executor.submit(pull_component.start)


if __name__ == '__main__':
    test_tests()
    test_request_reply()
    test_push_pull()
