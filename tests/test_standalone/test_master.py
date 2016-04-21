from threading import Thread
from pylm_ng.components.core import zmq_context, Broker
from pylm_ng.components.messages_pb2 import BrokerMessage
from pylm_ng.components.endpoints import logger
from pylm_ng.components.services import PushPullService
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


def worker(listen_push, listen_pull):
    pull = zmq_context.socket(zmq.PULL)
    pull.connect(listen_push)
    push = zmq_context.socket(zmq.PUSH)
    push.connect(listen_pull)

    for i in range(10):
        message = pull.recv()
        push.send(message)


def test_feedback():
    broker = Broker(logger=logger, messages=20)
    broker.register_inbound('inbound1', route='outbound', block=True, log='inbound1')
    broker.register_inbound('inbound2', route='outbound', log='inbound2')
    broker.register_outbound('outbound', log='outbound')

    pushpull = PushPullService('PushPull', 'inproc://push', 'inproc://pull',
                               broker.outbound_address, logger=logger,
                               messages=20)

    threads = [
        Thread(target=broker.start),
        Thread(target=inbound1, args=(broker.inbound_address,)),
        Thread(target=inbound2, args=(broker.inbound_address,)),
        Thread(target=pushpull, args=(broker.outbound_address,))
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    broker.cleanup()


if __name__ == '__main__':
    test_feedback()
