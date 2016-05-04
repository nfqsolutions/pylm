from pylm.components.core import zmq_context
from pylm.components.utils import ResilienceService
from pylm.components.messages_pb2 import BrokerMessage
from threading import Thread
from uuid import uuid4
import logging
import zmq
import time


def resilience_routine():
    resilience_service = ResilienceService('Resilience',
                                           'inproc://resilience',
                                           'inproc://false_broker',
                                           logger=logging)

    resilience_service.start()


def false_broker_routine():
    """Broker + worker only for resilience testing"""
    false_broker = zmq_context.socket(zmq.ROUTER)
    false_broker.bind('inproc://false_broker')

    before_worker = zmq_context.socket(zmq.REQ)
    before_worker.connect('inproc://resilience')

    after_worker = zmq_context.socket(zmq.REQ)
    after_worker.connect('inproc://resilience')

    message_stream = zmq_context.socket(zmq.REQ)
    message_stream.identity = b'message_stream'
    message_stream.connect('inproc://false_broker')

    def generate_messages():
        for i in range(100):
            message_stream.send(str(i).encode('utf-8'))
            message_stream.recv()

    message_stream_thread = Thread(target=generate_messages)
    message_stream_thread.start()

    for j in range(100):
        [client, empty, message_data] = false_broker.recv_multipart()
        print(client, message_data)
        false_broker.send_multipart([client, empty, b'0'])

        message = BrokerMessage()
        message.key = str(uuid4())
        message.payload = message_data

        before_worker.send_multipart([b'to', message.SerializeToString()])
        print(before_worker.recv())

        # Here's where the worker does his stuff.
        time.sleep('0.2')

        after_worker.send_multipart([b'from', message.SerializeToString()])
        print(after_worker.recv())

    false_broker.close()
    before_worker.close()
    after_worker.close()
    message_stream.close()


def test_resilience():
    threads = [
        Thread(target=false_broker_routine),
        Thread(target=resilience_routine)
    ]

    for t in threads:
        t.start()


if __name__ == "__main__":
    test_resilience()
