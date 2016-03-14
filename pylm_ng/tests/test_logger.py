# Test of the logger as a bypass connection.
from pylm_ng.components.core import Broker
from pylm_ng.components.utils import PylmLogFormatter, LogHandler
from pylm_ng.components.services import RepService
from pylm_ng.tests.endpoints import PullEndPoint, ReqConnection
from pylm_ng.tests.test_components import logger
from threading import Thread
import logging
from pylm_ng.components.core import zmq_context
import zmq


def test_logger():
    # Maybe improve this sequence to get a logger.
    pull_endpoint = PullEndPoint(logger=logger)

    pylm_logger = logging.getLogger(__name__)
    log_handler = logging.StreamHandler(LogHandler('logger',
                                                   pull_endpoint.bind_address)
                                        )
    log_handler.setFormatter(PylmLogFormatter)
    pylm_logger.addHandler(log_handler)
    pylm_logger.setLevel(logging.DEBUG)

    broker = Broker(logger=pylm_logger, messages=10)
    request_reply = RepService('test',
                               'inproc://repservice',
                               broker_address=broker.inbound_address,
                               logger=logger,
                               messages=10)

    req_connection = ReqConnection(listen_to=request_reply.listen_address,
                                   logger=logger)

    broker.register_inbound('test', log='Service responds!')

    t1 = Thread(target=pull_endpoint.start)
    t1.start()

    t2 = Thread(target=broker.start)
    t2.start()

    t3 = Thread(target=request_reply.start)
    t3.start()

    t4 = Thread(target=req_connection.start)
    t4.start()

    pusher = zmq_context.socket(zmq.PUSH)
    pusher.connect(pull_endpoint.bind_address)
    pusher.send(b'dfdfdfdfdfd')
    pusher.send(b'dfdfdfdfdfd')
    pusher.send(b'dfdfdfdfdfd')

    for t in [t1, t2, t3, t4]:
        t.join()

    req_connection.socket.close()
    broker.inbound.close()
    broker.outbound.close()

if __name__ == '__main__':
    test_logger()
