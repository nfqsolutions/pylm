from pylm.components.core import zmq_context
from pylm.components.utils import ResilienceService
from pylm.components.messages_pb2 import BrokerMessage
from threading import Thread
from uuid import uuid4
import logging
import zmq
import time
import random
import collections


def resilience_routine():
    resilience_service = ResilienceService('Resilience',
                                           'inproc://resilience',
                                           'inproc://false_broker',
                                           logger=logging)
    print('Starting {}'.format(resilience_service.name))
    resilience_service.start()


def false_broker_routine():
    messages_created = []
    messages_received = []
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

    # Generate a bunch of messages and send all of them asynchronously.
    def generate_messages():
        for i in range(100):
            broker_message = BrokerMessage()
            broker_message.key = str(uuid4())
            broker_message.payload = str(i).encode('utf-8')
            messages_created.append(broker_message.key)
            message_stream.send(broker_message.SerializeToString())
            message_stream.recv()

    message_stream_thread = Thread(target=generate_messages)
    message_stream_thread.start()

    while True:
        [client, empty, message_data] = false_broker.recv_multipart()
        false_broker.send_multipart([client, empty, b'0'])

        message = BrokerMessage()
        message.ParseFromString(message_data)
        print(message)

        before_worker.send_multipart([b'to', message.SerializeToString()])
        before_worker.recv()
        # Here's where the worker does his stuff.
        time.sleep(0.1)

        if not random.randint(0, 5) == 1:
            after_worker.send_multipart([b'from', message.SerializeToString()])
            action = after_worker.recv()
        else:
            action = False
            print('Message failed: ', message.key)

        if action == b'1':
            print('Message processed: ', message.key, message.payload)
            messages_received.append(message.key)
        else:
            print('Message ignored:', message.key)

        print(len(messages_created),
              len(messages_received),
              [item for item, count in collections.Counter(messages_received).items() if count > 1])

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
