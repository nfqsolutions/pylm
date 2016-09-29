from pylm.parts.connections import RepConnection, PushConnection, PullConnection
from pylm.parts.core import Router
from pylm.parts.endpoints import logger, ReqEndPoint, PullEndPoint, PushEndPoint
from threading import Thread
import atexit


def test_request_reply():
    """
    Tests the following sequence

    REQ Endpoint -> Rep connection -> broker
                 <-                <-
    :return:
    """
    broker = Router(logger=logger, messages=10)
    endpoint = ReqEndPoint(logger=logger)
    request_reply = RepConnection('test',
                                  listen_address=endpoint.bind_address,
                                  broker_address=broker.inbound_address,
                                  logger=logger,
                                  messages=10)
    broker.register_inbound('test',
                            log='Send to test component')

    threads = [
        Thread(target=broker.start),
        Thread(target=endpoint.start, kwargs={'function': 'this.function'}),
        Thread(target=request_reply.start)
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    endpoint.socket.close()
    broker.cleanup()


def test_request_push():
    """
    Tests the following sequence

    Req Endpoint -> Rep component -> Router -> Push component -> PULL endpoint.
                 <-               <-
    :return:
    """
    broker = Router(logger=logger, messages=20)
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

    threads = [
        Thread(target=broker.start),
        Thread(target=endpoint_req.start, kwargs={'function': 'this.function'}),
        Thread(target=endpoint_pull.start),
        Thread(target=rep_component.start),
        Thread(target=push_component.start)
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    endpoint_pull.socket.close()
    endpoint_req.socket.close()
    broker.cleanup()


def test_pull_push():
    """
    Tests the following sequence

    Push Endpoint -> pull component -> Router -> Push component -> PULL endpoint.
    :return:
    """
    broker = Router(logger=logger, messages=20)
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

    threads = [Thread(target=broker.start),
               Thread(target=endpoint_push.start, kwargs={'function': 'this.function'}),
               Thread(target=endpoint_pull.start),
               Thread(target=pull_component.start),
               Thread(target=push_component.start)]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    endpoint_pull.socket.close()
    endpoint_push.socket.close()
    broker.cleanup()

    
if __name__ == '__main__':
    test_request_reply()
    test_request_push()
    test_pull_push()
