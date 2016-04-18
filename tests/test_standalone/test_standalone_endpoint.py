from threading import Thread

import zmq

from pylm_ng.components.core import zmq_context
from pylm_ng.standalone import EndPoint


def send_ten(socket):
    for i in range(10):
        socket.send(str(i).encode('utf-8'))


def test_endpoint():
    log_address = "inproc://log2"
    perf_address = "inproc://perf2"
    ping_address = "inproc://ping2"
    endpoint = EndPoint('EndPoint', log_address, perf_address,
                        ping_address)

    log_generator = zmq_context.socket(zmq.PUSH)
    log_generator.connect(log_address)

    perf_generator = zmq_context.socket(zmq.PUSH)
    perf_generator.connect(perf_address)

    ping_generator = zmq_context.socket(zmq.PUSH)
    ping_generator.connect(ping_address)

    threads = [
        Thread(target=endpoint._start_debug, args=(30,)),
        Thread(target=send_ten, args=(log_generator,)),
        Thread(target=send_ten, args=(perf_generator,)),
        Thread(target=send_ten, args=(ping_generator,))
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    test_endpoint()