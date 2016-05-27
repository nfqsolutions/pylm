from threading import Thread
from pylm.components.core import zmq_context, Router
from pylm.components.messages_pb2 import BrokerMessage
from pylm.components.endpoints import logger
from pylm.components.services import PushPullService
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
        print('Inbound1 sent', i)
        returned = broker.recv()
        print('Inbound1 recv', i)
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
        print('Inbound2 sent', i)
        returned = broker.recv()
        print('Inbound2 recv', i)
        assert int(returned) == 1


def worker(listen_push, listen_pull):
    pull = zmq_context.socket(zmq.PULL)
    pull.connect(listen_push)
    push = zmq_context.socket(zmq.PUSH)
    push.connect(listen_pull)

    print('****', 'Worker waiting...')
    for i in range(10):
        message_data = pull.recv()
        print('********', 'Worker got message.', i)
        push.send(message_data)


def test_feedback():
    broker = Router(logger=logger, messages=20)
    broker.register_inbound('inbound1', route='PushPull', block=True, log='inbound1')
    broker.register_inbound('inbound2', route='PushPull', log='inbound2')
    broker.register_outbound('PushPull', log='outbound')

    push_pull = PushPullService('PushPull', 'inproc://push', 'inproc://pull',
                                broker.outbound_address, logger=logger,
                                messages=10)
    threads = [
        Thread(target=broker.start),
        Thread(target=inbound1, args=(broker.inbound_address,)),
        Thread(target=inbound2, args=(broker.inbound_address,)),
        Thread(target=push_pull.start),
        Thread(target=worker, args=(push_pull.push_address, push_pull.pull_address))
        ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    broker.cleanup()


if __name__ == '__main__':
    test_feedback()
