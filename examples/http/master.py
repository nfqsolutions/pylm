from pylm.persistence.kv import DictDB
from pylm.parts.servers import ServerTemplate
from pylm.parts.services import PullService, PubService
from pylm.parts.connections import HttpConnection
from pylm.parts.utils import CacheService

server = ServerTemplate()

db_address = 'tcp://127.0.0.1:5559'
pull_address = 'tcp://127.0.0.1:5555'
push_address = 'tcp://127.0.0.1:5556'

cache = DictDB()
cache.set('name', b'server')
cache.set('db_address', b'tcp://127.0.0.1:5559')
cache.set('pull_address', b'tcp://127.0.0.1:5555')
cache.set('pub_address', b'tcp://127.0.0.1:5556')


server.register_inbound(PullService, 'Pull', pull_address, route='HttpConnection', cache=cache)
server.register_outbound(HttpConnection, 'HttpConnection', 'http://localhost:8888', route='Pub', cache=cache)
server.register_outbound(PubService, 'Pub', push_address, cache=cache)
server.register_bypass(CacheService, 'Cache', db_address, cache=cache)

if __name__ == '__main__':
    server.start()
