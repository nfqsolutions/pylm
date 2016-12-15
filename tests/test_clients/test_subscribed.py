from pylm.parts.core import zmq_context
from pylm.standalone.clients import SubscribedClient
from pylm.parts.utils import CacheService
from pylm.parts.services import PullService, PubService
from pylm.persistence.kv import DictDB
import concurrent.futures
import traceback
import logging
import sys
import zmq

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
        client = SubscribedClient('master',
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
        client = SubscribedClient('master',
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

if __name__ == '__main__':
    test_get_config()
    test_send_job()