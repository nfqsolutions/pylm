# Test of the logger as a bypass connection.
from pylm_ng.components.core import Broker
from pylm_ng.components.utils import PylmLogFormatter, LogHandler
from pylm_ng.components.services import RepService
from pylm_ng.tests.endpoints import PullEndPoint, ReqConnection
from pylm_ng.tests.test_components import logger
from threading import Thread
import logging


def test_logger():
    # Maybe improve this sequence to get a logger.
    pull_endpoint = PullEndPoint(logger=logger)
    pylm_logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler(LogHandler('logge',
                                                   pull_endpoint.bind_address)
                                        )
    log_handler.setFormatter(PylmLogFormatter)
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

    t1 = Thread(target=pull_endpoint.start)
    t1.start()

    t2 = Thread(target=broker.start)
    t2.start()

    t3 = Thread(target=request_reply.start)
    t3.start()

    t4 = Thread(target=req_connection.start)
    t4.start()

    for t in [t1, t2, t3, t4]:
        t.join()

    pull_endpoint.socket.close()
    req_connection.socket.close()
    broker.inbound.close()
    broker.outbound.close()

if __name__ == '__main__':
    test_logger()
