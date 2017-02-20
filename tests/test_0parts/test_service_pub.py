from pylm.persistence.kv import DictDB
from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage
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

listen_address = 'inproc://pub1'
broker_address = 'inproc://broker1'

pub_service = PubService(
    'pull_service',
    listen_address=listen_address,
    broker_address=broker_address,
    logger=logger,
    cache=cache,
    messages=1)


def fake_router():
    original_message = PalmMessage()
    original_message.pipeline = 'pipeline'
    original_message.client = 'client'
    original_message.stage = 1
    original_message.cache = '0'
    original_message.function = 'function'
    original_message.payload = b'0'

    socket = zmq_context.socket(zmq.REQ)
    socket.bind(broker_address)
    serialized = original_message.SerializeToString()
    socket.send(serialized)
    socket.recv()


def fake_client():
    socket = zmq_context.socket(zmq.SUB)
    socket.setsockopt_string(zmq.SUBSCRIBE, 'client')
    socket.connect(listen_address)

    # Pub sockets take some time.
    time.sleep(1.0)
    return socket.recv_multipart()


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
                if type(result) == list:
                    assert result[0] == b'client'

            except Exception as exc:
                logger.error('Thread {} generated an exception'.format(future))
                logger.error(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(*lines)


if __name__ == '__main__':
    test_pub_client()
