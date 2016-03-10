from pylm_ng.components.core import Broker, ReqRepComponent
from pylm_ng.components.endpoints import logger, ReqEndpoint
from concurrent.futures import ThreadPoolExecutor


def test_tests():
    print("test")


def test_request_reply():
    broker = Broker(logger=logger, messages=10)
    endpoint = ReqEndpoint(logger=logger)
    request_reply = ReqRepComponent('test',
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


if __name__ == '__main__':
    test_tests()
    test_request_reply()
