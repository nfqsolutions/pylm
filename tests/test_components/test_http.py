from pylm.components.core import zmq_context
from pylm.components.services import HttpService
from pylm.components.connections import HttpConnection
from pylm.components.messages_pb2 import BrokerMessage
from threading import Thread
import zmq
import logging


def fake_router():
    socket = zmq_context.socket(zmq.REQ)
    socket.bind('inproc://broker')

    message = BrokerMessage()
    message.payload = b'test message'
    message.key = 'x'
    socket.send(message.SerializeToString())
    socket.recv()


def fake_terminator():
    socket = zmq_context.socket(zmq.REP)
    socket.bind('inproc://terminator')
    message = BrokerMessage()
    message.ParseFromString(socket.recv())

    print("Got the message at the terminator: ")
    print(message)
    socket.send(b'0')


def isolated_connection():
    connection = HttpConnection(
        'connector',
        'http://localhost:8888',
        broker_address="inproc://broker",
        logger=logging,
        messages=1
    )
    print("Satarting connection")
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
    service.start()


def test_manual_http():
    """
    This test
    router -> connector -> service -> terminator

    :return:
    """
    threads = [
        Thread(target=fake_router),
        Thread(target=fake_terminator),
        Thread(target=isolated_connection),
        Thread(target=isolated_service)
    ]

    print("starting threads")
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    test_manual_http()
