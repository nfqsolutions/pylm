from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import BrokerMessage, PalmMessage
from pylm.parts.gateways import GatewayRouter, GatewayDealer
from pylm.persistence.kv import DictDB
import concurrent.futures
import logging
import zmq


def test_gateway_router():
    """
    This tests only the router part of the HTTP gateway component
    """

    # A simple REP socket to act as a router. Just rebounds the message
    def dummy_response():
        dummy_router = zmq_context.socket(zmq.REP)
        dummy_router.bind('inproc://broker')
        msg = dummy_router.recv()
        broker_message = BrokerMessage()
        broker_message.ParseFromString(msg)
        dummy_router.send(msg)
        return broker_message.payload

    def dummy_initiator():
        dummy_client = zmq_context.socket(zmq.REQ)
        dummy_client.identity = b'0'
        dummy_client.connect('inproc://gateway_router')
        message = PalmMessage()
        message.client = dummy_client.identity
        message.pipeline = '0'
        message.function = 'f.servername'
        message.stage = 1
        message.payload = b'This is a message'
        dummy_client.send(message.SerializeToString())

    gateway = GatewayRouter(logger=logging, messages=1)
    got = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = [
            executor.submit(dummy_initiator),
            executor.submit(dummy_response),
            executor.submit(gateway.start)
        ]
        for future in concurrent.futures.as_completed(results):
            try:
                result = future.result()
                if result:
                    got.append(result)

            except Exception as exc:
                print(exc)

    assert got[0] == b'This is a message'


def test_gateway_dealer():
    """
    Test function for the complete gateway with a dummy router.
    """
    cache = DictDB()

    def dummy_response():
        dummy_router = zmq_context.socket(zmq.ROUTER)
        dummy_router.bind('inproc://broker')
        [target, empty, message] = dummy_router.recv_multipart()
        dummy_router.send_multipart([target, empty, b'0'])

        broker_message = BrokerMessage()
        broker_message.ParseFromString(message)

        dummy_router.send_multipart([b'gateway_dealer', empty, message])
        [target, message] = dummy_router.recv_multipart()

    def dummy_initiator():
        dummy_client = zmq_context.socket(zmq.REQ)
        dummy_client.identity = b'0'
        dummy_client.connect('inproc://gateway_router')
        message = PalmMessage()
        message.client = dummy_client.identity
        message.pipeline = '0'
        message.function = 'f.servername'
        message.stage = 1
        message.payload = b'This is a message'
        dummy_client.send(message.SerializeToString())
        return dummy_client.recv()

    got = []

    dealer = GatewayDealer(cache=cache, logger=logging, messages=1)
    router = GatewayRouter(cache=cache, logger=logging, messages=2)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = [
            executor.submit(dummy_response),
            executor.submit(dummy_initiator),
            executor.submit(dealer.start),
            executor.submit(router.start)
        ]

        for future in concurrent.futures.as_completed(results):
            try:
                result = future.result()
                if result:
                    got.append(result)

            except Exception as exc:
                print(exc)

    message = PalmMessage()
    message.ParseFromString(got[0])
    assert message.payload == b'This is a message'


if __name__ == "__main__":
    test_gateway_router()
    test_gateway_dealer()
