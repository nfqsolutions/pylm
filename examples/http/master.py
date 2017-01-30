from pylm.parts.servers import ServerTemplate
from pylm.parts.services import PullService, PubService
from pylm.parts.connections import HttpConnection
from pylm.parts.utils import CacheService

server = ServerTemplate()

db_address = 'tcp://127.0.0.1:5559'
pull_address = 'tcp://127.0.0.1:5555'
pub_address = 'tcp://127.0.0.1:5556'

server.register_inbound(PullService, 'Pull', pull_address, route='HttpConnection')
server.register_outbound(HttpConnection, 'HttpConnection', 'http://localhost:8888', route='Pub')
server.register_outbound(PubService, 'Pub', pub_address)
server.register_bypass(CacheService, 'Cache', db_address)
server.preset_cache(name='server',
                    db_address=db_address,
                    pull_address=pull_address,
                    pub_address=pub_address)

if __name__ == '__main__':
    server.start()
