from threading import Thread

from pylm.components.core import Broker
from pylm.components.endpoints import ReqConnection, logger
from pylm.components.services import RepService
from pylm.components.utils import PerformanceCounter, PerformanceCollector


def test_perfcounter():
    collector = PerformanceCollector()
    perfcounter = PerformanceCounter(listen_address=collector.bind_address)

    perfcounter.tick('Instantiate Broker')
    broker = Broker(logger=logger, messages=10)

    perfcounter.tick('Instantiate Reply Service')
    request_reply = RepService('test',
                               'inproc://repservice',
                               broker_address=broker.inbound_address,
                               logger=logger,
                               messages=10)

    perfcounter.tick('Instantiate Req connection')
    req_connection = ReqConnection(listen_to=request_reply.listen_address,
                                   logger=logger)

    broker.register_inbound('test', log='Service responds!')

    perfcounter.tick('Launched all threads')
    t1 = Thread(target=collector.start, args=(7,))
    t1.start()

    t2 = Thread(target=broker.start)
    t2.start()

    t3 = Thread(target=request_reply.start)
    t3.start()

    t4 = Thread(target=req_connection.start)
    t4.start()
    perfcounter.tick('Finished launching threads')

    for t in [t2, t3, t4]:
        t.join()

    perfcounter.tick('Joining threads')

    req_connection.socket.close()
    broker.inbound.close()
    broker.outbound.close()
    perfcounter.tick('Cleaning up')

    t1.join()

if __name__ == '__main__':
    test_perfcounter()
