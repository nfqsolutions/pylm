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
worker_pull_address = 'inproc://worker_pull'
worker_push_address = 'inproc://worker_push'
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

    def bootclient():
        client = SubscribedClient('master',
                                  db_address,
                                  pipeline=None)
        return client.push_address, client.sub_address

    def broker():
        socket = zmq_context.socket(zmq.ROUTER)
        socket.bind(broker_address)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = [
            executor.submit(cache.start),
            executor.submit(bootclient),
            executor.submit(broker)
        ]

        # This works because servers do not return values.
        for future in concurrent.futures.as_completed(results):
            try:
                result = future.result(timeout=1.0)
                if result:
                    assert result == ('inproc://pull', 'inproc://pub')

            except Exception as exc:
                print(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(lines)


def test_client_job():
    pass

if __name__ == '__main__':
    test_get_config()