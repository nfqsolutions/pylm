from pylm.persistence.kv import DictDB
from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage, BrokerMessage
from pylm.parts.services import PubService
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import time
import zmq
import logging
import sys
import traceback

logger = logging.getLogger('test_service_pub')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

cache = DictDB()

original_message = PalmMessage()
original_message.pipeline = 'pipeline'
original_message.client = 'client'
original_message.stage = 1
original_message.function = 'function'
original_message.payload = b'0'

broker_message_key = 'some key'
broker_message = BrokerMessage()
broker_message.key = broker_message_key
broker_message.instruction = 'function'
broker_message.payload = b'0'
broker_message.pipeline = 'pipeline'

cache.set(broker_message_key, original_message.SerializeToString())

listen_address = 'inproc://pub4623'
broker_address = 'inproc://broker2346'

pub_service = PubService(
    'pull_service',
    listen_address=listen_address,
    broker_address=broker_address,
    palm=True,
    logger=logger,
    cache=cache,
    messages=1)


def fake_router():
    socket = zmq_context.socket(zmq.REQ)
    socket.bind(broker_address)

    socket.send(broker_message.SerializeToString())
    socket.recv()


def fake_client():
    socket = zmq_context.socket(zmq.SUB)
    socket.setsockopt_string(zmq.SUBSCRIBE, 'client')
    socket.connect(listen_address)

    # Pub sockets take some time.
    time.sleep(1.0)
    result = socket.recv_multipart()
    return result[1]


def test_pub_client():
    parts = [
        pub_service.start,
        fake_router,
        fake_client
    ]
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = [executor.submit(thread) for thread in parts]
        for future in concurrent.futures.as_completed(results):
            try:
                result = future.result()
                if result:
                    message = PalmMessage()
                    message.ParseFromString(result)
                    assert message.payload == b'0'

            except Exception as exc:
                logger.error('Thread {} generated an exception'.format(future))
                logger.error(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(*lines)


if __name__ == '__main__':
    test_pub_client()
