from pylm.parts.servers import ServerTemplate
from pylm.parts.services import WorkerPullService, WorkerPushService, \
    CacheService
from pylm.parts.gateways import GatewayDealer, GatewayRouter, HttpGateway

server = ServerTemplate()

worker_pull_address = 'tcp://127.0.0.1:5557'
worker_push_address = 'tcp://127.0.0.1:5558'
db_address = 'tcp://127.0.0.1:5559'

server.register_inbound(GatewayRouter,
                        'gateway_router',
                        'inproc://gateway_router',
                        route='WorkerPush')
server.register_outbound(GatewayDealer,
                         'gateway_dealer',
                         listen_address='inproc://gateway_router')
server.register_bypass(HttpGateway,
                       name='HttpGateway',
                       listen_address='inproc://gateway_router',
                       hostname='localhost',
                       port=8888)
server.register_inbound(WorkerPullService, 'WorkerPull', worker_pull_address,
                        route='gateway_dealer')
server.register_outbound(WorkerPushService, 'WorkerPush', worker_push_address)
server.register_bypass(CacheService, 'Cache', db_address)

server.preset_cache(name='server',
                    db_address=db_address,
                    worker_pull_address=worker_pull_address,
                    worker_push_address=worker_push_address)

if __name__ == '__main__':
    server.start()
