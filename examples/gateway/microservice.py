from pylm.parts.servers import ServerTemplate
from pylm.parts.services import WorkerPullService, WorkerPushService
from pylm.parts.gateways import GatewayDealer, GatewayRouter, HttpGateway
from pylm.parts.utils import CacheService
from pylm.persistence.kv import DictDB

server = ServerTemplate()

worker_pull_address = 'tcp://127.0.0.1:5557'
worker_push_address = 'tcp://127.0.0.1:5558'
db_address = 'tcp://127.0.0.1:5559'

cache = DictDB()
cache.set('name', b'server')
cache.set('worker_pull_address', 'tcp://127.0.0.1:5557'.encode('utf-8'))
cache.set('worker_push_address', 'tcp://127.0.0.1:5558'.encode('utf-8'))

server.register_inbound(GatewayRouter,
                        'gateway_router',
                        'inproc://gateway_router',
                        route='WorkerPush',
                        cache=cache)
server.register_outbound(GatewayDealer,
                         'gateway_dealer',
                         listen_address='inproc://gateway_router',
                         cache=cache)
server.register_bypass(HttpGateway,
                       name='HttpGateway',
                       listen_address='inproc://gateway_router',
                       hostname='localhost',
                       port=8888,
                       cache=cache)
server.register_inbound(WorkerPullService,
                        'WorkerPull',
                        worker_pull_address,
                        route='gateway_dealer',
                        cache=cache)
server.register_outbound(WorkerPushService,
                         'WorkerPush',
                         worker_push_address,
                         cache=cache)
server.register_bypass(CacheService,
                       'Cache',
                       db_address,
                       cache=cache)

if __name__ == '__main__':
    server.start()
