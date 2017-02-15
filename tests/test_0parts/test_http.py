from pylm.parts.core import zmq_context
from pylm.parts.services import HttpService
from pylm.parts.connections import HttpConnection
from pylm.parts.messages_pb2 import PalmMessage
import concurrent.futures
import zmq
import logging
import time


def fake_router():
    socket = zmq_context.socket(zmq.REQ)
    socket.bind('inproc://broker')

    # Give some time for everything to start
    time.sleep(1.0)
    message = PalmMessage()
    message.payload = b'test message'
    socket.send(message.SerializeToString())
    socket.recv()


def fake_terminator():
    socket = zmq_context.socket(zmq.REP)
    socket.bind('inproc://terminator')
    message = PalmMessage()
    message.ParseFromString(socket.recv())

    print("Got the message at the terminator: ")
    socket.send(b'0')
    return message


def isolated_connection():
    connection = HttpConnection(
        'connector',
        'http://localhost:8888',
        broker_address="inproc://broker",
        logger=logging,
        messages=1
    )
    print("Starting connection")
    connection.start()


def isolated_service():
    service = HttpService(
        'service',
        'localhost',
        8888,
        logger=logging,
        broker_address="inproc://terminator"
    )
    print("Starting server")
    service.debug()


def test_http():
    """
    This test
    router -> connector -> service -> terminator

    :return:
    """
    got = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = [
            executor.submit(fake_router),
            executor.submit(fake_terminator),
            executor.submit(isolated_connection),
            executor.submit(isolated_service)
        ]

        for future in concurrent.futures.as_completed(results):
            try:
                result = future.result()
                if result:
                    got.append(result)
            except Exception as exc:
                print(exc)

    assert got[0].payload == b"test message"

if __name__ == '__main__':
    test_http()
