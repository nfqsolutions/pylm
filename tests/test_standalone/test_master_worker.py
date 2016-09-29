from threading import Thread
from pylm.parts.core import zmq_context, Router
from pylm.parts.endpoints import logger
from pylm.parts.services import WorkerPullService, WorkerPushService
from pylm.parts.services import PullService, PushService
import zmq


def inbound(listen_addr):
    socket = zmq_context.socket(zmq.PUSH)
    socket.connect(listen_addr)

    for i in range(10):
        socket.send(str(i).encode('utf-8'))


def outbound(listen_addr):
    socket = zmq_context.socket(zmq.PULL)
    socket.connect(listen_addr)

    for i in range(10):
        socket.recv()
        print('**********', 'Outbound got response', i)


def worker1(listen_push, listen_pull):
    pull = zmq_context.socket(zmq.PULL)
    pull.connect(listen_push)
    push = zmq_context.socket(zmq.PUSH)
    push.connect(listen_pull)

    print('****', 'Worker waiting...')
    for i in range(5):
        message_data = pull.recv()
        print('********', 'Worker1 got message.', i)
        push.send(message_data)


def worker2(listen_push, listen_pull):
    pull = zmq_context.socket(zmq.PULL)
    pull.connect(listen_push)
    push = zmq_context.socket(zmq.PUSH)
    push.connect(listen_pull)

    print('****', 'Worker waiting...')
    for i in range(5):
        message_data = pull.recv()
        print('********', 'Worker2 got message.', i)
        push.send(message_data)


def test_feedback():
    broker = Router(logger=logger, messages=42)
    pull_service = PullService('Pull', 'inproc://pull',
                               broker_address=broker.inbound_address,
                               logger=logger, messages=10)
    push_service = PushService('Push', 'inproc://push',
                               broker_address=broker.outbound_address,
                               logger=logger, messages=10)
    worker_pull_service = WorkerPullService('WorkerPull', 'inproc://worker_pull',
                                            broker_address=broker.inbound_address,
                                            logger=logger, messages=10)
    worker_push_service = WorkerPushService('WorkerPush', 'inproc://worker_push',
                                            broker_address=broker.outbound_address,
                                            logger=logger, messages=10)

    broker.register_inbound('Pull', route='WorkerPush', log='to_broker')
    broker.register_inbound('WorkerPull', route='Push', log='from_broker')
    broker.register_outbound('WorkerPush', log='to_broker')
    broker.register_outbound('Push', log='to_sink')

    threads = [
        Thread(target=broker.start),
        Thread(target=push_service.start),
        Thread(target=pull_service.start),
        Thread(target=worker_push_service.start),
        Thread(target=worker_pull_service.start),
        Thread(target=inbound, args=(pull_service.listen_address,)),
        Thread(target=outbound, args=(push_service.listen_address,)),
        Thread(target=worker1,
               args=(worker_push_service.listen_address, worker_pull_service.listen_address)),
        Thread(target=worker2,
               args=(worker_push_service.listen_address, worker_pull_service.listen_address))
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)

    broker.cleanup()


if __name__ == '__main__':
    test_feedback()
