from pylm.components.servers import ServerTemplate
from pylm.components.services import PullService, PushService
from pylm.components.connections import HttpConnection
from pylm.components.utils import CacheService

server = ServerTemplate()


server.palm = True
server.register_inbound(PullService, 'Pull', 'tcp://127.0.0.1:5555', route='HttpConnection')
server.register_outbound(HttpConnection, 'HttpConnection', 'http://localhost:8888', route='Push')
server.register_outbound(PushService, 'Push', 'tcp://127.0.0.1:5556')
server.register_bypass(CacheService, 'Cache', 'tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
