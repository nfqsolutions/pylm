from threading import Thread
from pylm_ng.components.core import zmq_context, Broker
from pylm_ng.components.endpoints import logger
import zmq


def inbound1(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'inbound1'
    broker.connect(listen_addr)

    for i in range(0, 10, 2):
        broker.send(str(i).encode('utf-8'))
        returned = broker.recv()
        print('Inbound1', i, returned)
        #assert int(returned) == i


def inbound2(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'inbound2'
    broker.connect(listen_addr)

    for i in range(1, 10, 2):
        broker.send(str(i).encode('utf-8'))
        returned = broker.recv()
        print('Inbound2', i, returned)
        #assert int(returned) == i


def outbound(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'outbound'
    broker.connect(listen_addr)

    broker.send(b'READY')

    for i in range(10):
        message_data = broker.recv()
        print('outbound:', message_data)
        broker.send(message_data)


def test_feedback():
    broker = Broker(logger=logger, messages=20)
    broker.register_inbound('inbound1', route='outbound', log='inbound1')
    broker.register_inbound('inbound2', route='outbound', log='inboubd2')
    broker.register_inbound('outbound', log='outbound')

    threads = [
        Thread(target=broker.start),
        Thread(target=inbound1, args=(broker.inbound_address,)),
        Thread(target=inbound2, args=(broker.inbound_address,)),
        Thread(target=outbound, args=(broker.outbound_address,))
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

if __name__ == '__main__':
    test_feedback()