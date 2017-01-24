# ACHTUNG! You have to run this test manually,
# because it cannot die.

from threading import Thread
from pylm.parts.core import zmq_context
from pylm.servers import Master
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
    this_db_address = "inproc://db"

    master = Master('master', 'inproc://pull5', 'inproc://push5',
                    'inproc://worker_pull5', 'inproc://worker_push5',
                    this_db_address)

    threads = [
        Thread(target=master.start),
        Thread(target=inbound, args=(master.pull_address,)),
        Thread(target=outbound, args=(master.push_address,)),
        Thread(target=worker1,
               args=(master.worker_push_address, master.worker_pull_address)),
        Thread(target=worker2,
               args=(master.worker_push_address, master.worker_pull_address))
    ]

    # for t in threads[:2]:
    #     t.daemon = True

    for t in threads:
        t.start()

    for t in threads:
        t.join(1)


if __name__ == '__main__':
    test_feedback()
