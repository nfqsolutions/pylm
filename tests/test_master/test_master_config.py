from pylm.standalone.clients import SubscribedClient
from pylm.parts.utils import CacheService
from pylm.persistence.kv import DictDB
import concurrent.futures
import traceback
import logging
import sys


pull_address = 'inproc://pull'
pub_address = 'inproc://pub'
worker_pull_address = 'inproc://worker_pull'
worker_push_address = 'inproc://worker_push'
db_address = 'inproc://db'

cache = DictDB()
cache.set('pub_address', pub_address.encode('utf-8'))

master = CacheService('db', db_address,
                      cache=cache,
                      logger=logging,
                      messages=1)

client = SubscribedClient(
    sub_address=pub_address,
    pull_address=pull_address,
    db_address=db_address,
    server_name='master',
    pipeline=None
)


def test_get_config():
    got = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = [
            executor.submit(master.start),
            executor.submit(client.get, 'pub_address')
        ]

        # This works because servers do not return values.
        for future in concurrent.futures.as_completed(results):
            try:
                result = future.result(timeout=1.0)
                if result:
                    assert result == b'inproc://pub'

            except Exception as exc:
                print(exc)
                lines = traceback.format_exception(*sys.exc_info())
                print(*lines)

if __name__ == '__main__':
    test_get_config()