from threading import Thread

from pylm_ng.components.core import Broker
from pylm_ng.components.endpoints import ReqConnection, logger
from pylm_ng.components.services import RepService


def test_request_reply():
    """
    Tests the followign sequence

    REQ connection -> Rep service -> broker
                   <-             <-
    :return:
    """
    broker = Broker(logger=logger, messages=10)

    request_reply = RepService('test',
                               "inproc://repservice",
                               broker_address=broker.inbound_address,
                               logger=logger,
                               messages=10)

    connection = ReqConnection(listen_to=request_reply.listen_address,
                               logger=logger)

    broker.register_inbound('test', log='Service responds!')

    t1 = Thread(target=broker.start)
    t1.start()

    t2 = Thread(target=request_reply.start)
    t2.start()

    t3 = Thread(target=connection.start)
    t3.start()

    for t in [t1, t2, t3]:
        t.join()

    connection.socket.close()
    request_reply.listen_to.close()
    broker.inbound.close()
    broker.outbound.close()


if __name__ == '__main__':
    test_request_reply()
