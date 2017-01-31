import concurrent.futures
import logging
import sys
import traceback

import zmq

from pylm.clients import Client
from pylm.parts.core import zmq_context, Router
from pylm.parts.messages_pb2 import PalmMessage
from pylm.parts.services import PullService, PubService, CacheService
from pylm.persistence.kv import DictDB

pull_address = 'inproc://pull'
pub_address = 'inproc://pub'
db_address = 'inproc://db'
broker_address = 'inproc://broker'


def test_get_config():
    cache = DictDB()
    cache.set('name', b'master')
    cache.set('pub_address', pub_address.encode('utf-8'))
    cache.set('pull_address', pull_address.encode('utf-8'))

    cache = CacheService('db', db_address,
                         cache=cache,
                         logger=logging,
                         messages=3,
                         )

    def boot_client():
        client = Client('master',
                        db_address,
                        pipeline=None)
        return client.push_address, client.sub_address

    def broker():
        socket = zmq_context.socket(zmq.ROUTER)
        socket.bind(broker_address)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = [
            executor.submit(cache.start),
            executor.submit(boot_client),
            executor.submit(broker)
        ]

        # This works because servers do not return values.
        for i, future in enumerate(concurrent.futures.as_completed(results)):
            try:
                result = future.result()
                print(result)

            except Exception as exc:
                print(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(lines)

        assert i == 2


def test_send_job():
    cache = DictDB()
    cache.set('name', b'master')
    cache.set('pub_address', pub_address.encode('utf-8'))
    cache.set('pull_address', pull_address.encode('utf-8'))

    cache_service = CacheService('db', db_address,
                                 cache=cache,
                                 logger=logging,
                                 messages=3,
                                 )

    puller = PullService('puller',
                         pull_address,
                         palm=True,
                         logger=logging,
                         cache=cache,
                         messages=1)

    publisher = PubService('publisher',
                           pub_address,
                           logger=logging,
                           cache=cache,
                           palm=True,
                           messages=1)

    def client_job():
        client = Client('master',
                        db_address,
                        pipeline=None)
        return [r for r in client.job('master.something', [b'1'], messages=1)]

    def broker():
        socket = zmq_context.socket(zmq.ROUTER)
        socket.bind(broker_address)
        message = socket.recv_multipart()
        # Unblock. Here you see why the actual router is complicated.
        socket.send_multipart(message)
        socket.send_multipart([b'publisher', b'', message[2]])
        socket.close()

        return b'router'

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = [
            executor.submit(cache_service.start),
            executor.submit(puller.start),
            executor.submit(publisher.start),
            executor.submit(client_job),
            executor.submit(broker)
        ]

        # This works because servers do not return values.
        for i, future in enumerate(concurrent.futures.as_completed(results)):
            try:
                result = future.result()
                print(result)

            except Exception as exc:
                print(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(*lines)

        assert i == 4


def test_multiple_clients():
    cache = DictDB()
    cache.set('name', b'master')
    cache.set('pub_address', pub_address.encode('utf-8'))
    cache.set('pull_address', pull_address.encode('utf-8'))

    router = Router(logger=logging, cache=cache, messages=4)
    router.register_inbound('puller', route='publisher')
    router.register_outbound('publisher')

    cache_service = CacheService('db', db_address,
                                 cache=cache,
                                 logger=logging,
                                 messages=6,
                                 )

    puller = PullService('puller',
                         pull_address,
                         broker_address=router.inbound_address,
                         palm=True,
                         logger=logging,
                         cache=cache,
                         messages=4)

    publisher = PubService('publisher',
                           pub_address,
                           broker_address=router.outbound_address,
                           logger=logging,
                           cache=cache,
                           palm=True,
                           messages=4)

    def client1_job():
        client = Client('master',
                        db_address,
                        pipeline=None)
        return [r for r in client.job('master.something', [b'1', b'2'], messages=2)]

    def client2_job():
        client = Client('master',
                        db_address,
                        pipeline=None)
        return [r for r in client.job('master.something', [b'3', b'4'], messages=2)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        results = [
            executor.submit(cache_service.start),
            executor.submit(puller.start),
            executor.submit(publisher.start),
            executor.submit(router.start),
            executor.submit(client1_job),
            executor.submit(client2_job),
        ]

        # This works because servers do not return values.
        for i, future in enumerate(concurrent.futures.as_completed(results)):
            try:
                result = future.result()
                if type(result) == list:
                    got = []
                    for r in result:
                        message = PalmMessage()
                        message.ParseFromString(r)
                        got.append(message.payload)

                    assert got == [b'1', b'2'] or got == [b'3', b'4']

            except Exception as exc:
                print(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(*lines)

    assert i == 5


if __name__ == '__main__':
    test_get_config()
    test_send_job()
    test_multiple_clients()