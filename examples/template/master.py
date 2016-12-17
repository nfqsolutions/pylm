from pylm.persistence.kv import DictDB
from pylm.parts.servers import ServerTemplate
from pylm.parts.services import PullService, PubService, WorkerPullService, WorkerPushService
from pylm.parts.utils import CacheService

server = ServerTemplate()

db_address = 'tcp://127.0.0.1:5559'
pull_address = 'tcp://127.0.0.1:5555'
pub_address = 'tcp://127.0.0.1:5556'
worker_pull_address = 'tcp://127.0.0.1:5557'
worker_push_address = 'tcp://127.0.0.1:5558'

cache = DictDB()

# Set the name of the server and configuration parameters manually.
cache.set('name', b'server')
cache.set('pull_address', 'tcp://127.0.0.1:5555'.encode('utf-8'))
cache.set('pub_address', 'tcp://127.0.0.1:5556'.encode('utf-8'))
cache.set('worker_pull_address', 'tcp://127.0.0.1:5557'.encode('utf-8'))
cache.set('worker_push_address', 'tcp://127.0.0.1:5558'.encode('utf-8'))

server.register_inbound(PullService, 'Pull', pull_address, route='WorkerPush', cache=cache)
server.register_inbound(WorkerPullService, 'WorkerPull', worker_pull_address, route='Pub', cache=cache)
server.register_outbound(WorkerPushService, 'WorkerPush', worker_push_address, cache=cache)
server.register_outbound(PubService, 'Pub', pub_address, cache=cache)
server.register_bypass(CacheService, 'Cache', db_address, cache=cache)

if __name__ == '__main__':
    server.start()
