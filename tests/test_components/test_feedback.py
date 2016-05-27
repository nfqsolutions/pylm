from threading import Thread
from pylm.components.core import zmq_context, Router
from pylm.components.messages_pb2 import BrokerMessage
from pylm.components.endpoints import logger
from uuid import uuid4
import zmq


def inbound1(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'inbound1'
    broker.connect(listen_addr)

    for i in range(0, 10, 2):
        broker_message = BrokerMessage()
        broker_message.key = str(uuid4())
        broker_message.payload = str(i).encode('utf-8')
        broker.send(broker_message.SerializeToString())
        returned = broker.recv()
        assert int(returned) == i

        
def inbound2(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'inbound2'
    broker.connect(listen_addr)

    for i in range(1, 10, 2):
        broker_message = BrokerMessage()
        broker_message.key = str(uuid4())
        broker_message.payload = str(i).encode('utf-8')
        broker.send(broker_message.SerializeToString())
        returned = broker.recv()
        assert int(returned) == 1


def outbound(listen_addr):
    broker = zmq_context.socket(zmq.REQ)
    broker.identity = b'outbound'
    broker.connect(listen_addr)
    broker_message = BrokerMessage()
    broker_message.key = '0'
    broker_message.payload = b'READY'
    broker.send(broker_message.SerializeToString())

    for i in range(10):
        broker_message.ParseFromString(broker.recv())
        broker.send(broker_message.SerializeToString())


def test_feedback():
    broker = Router(logger=logger, messages=20)
    broker.register_inbound('inbound1', route='outbound', block=True, log='inbound1')
    broker.register_inbound('inbound2', route='outbound', log='inbound2')
    broker.register_outbound('outbound', log='outbound')

    threads = [
        Thread(target=broker.start),
        Thread(target=inbound1, args=(broker.inbound_address,)),
        Thread(target=inbound2, args=(broker.inbound_address,)),
        Thread(target=outbound, args=(broker.outbound_address,))
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    broker.cleanup()


if __name__ == '__main__':
    test_feedback()
