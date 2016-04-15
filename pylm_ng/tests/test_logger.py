# Test of the logger as a bypass connection.
from pylm_ng.components.core import Broker
from pylm_ng.components.utils import PushHandler, LogCollector
from pylm_ng.components.services import RepService
from pylm_ng.tests.endpoints import ReqConnection
from threading import Thread
import logging


def test_logger():
    # Maybe improve this sequence to get a logger.

    collector = LogCollector()
    handler = PushHandler(collector.bind_address)
    pylm_logger = logging.getLogger('test_logger')
    pylm_logger.addHandler(handler)
    pylm_logger.setLevel(logging.DEBUG)

    broker = Broker(logger=pylm_logger, messages=10)
    request_reply = RepService('test',
                               'inproc://repservice',
                               broker_address=broker.inbound_address,
                               logger=pylm_logger,
                               messages=10)

    req_connection = ReqConnection(listen_to=request_reply.listen_address,
                                   logger=pylm_logger)

    broker.register_inbound('test', log='Service responds!')

    t1 = Thread(target=collector.start, args=(97,))  # 97 is the expected number of log messages
    t1.start()

    t2 = Thread(target=broker.start)
    t2.start()

    t3 = Thread(target=request_reply.start)
    t3.start()

    t4 = Thread(target=req_connection.start)
    t4.start()

    for t in [t1, t2, t3, t4]:
        t.join()

    req_connection.socket.close()
    broker.inbound.close()
    broker.outbound.close()

if __name__ == '__main__':
    test_logger()
