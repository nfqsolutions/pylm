from pylm.parts.servers import ServerTemplate
from pylm.parts.services import WorkerPullService, WorkerPushService
from pylm.parts.gateways import HttpGateway
from pylm.parts.utils import CacheService

server = ServerTemplate()

server.palm = True
server.register_gateway(HttpGateway,
                        'Gateway',
                        'localhost',
                        8888,
                        route='WorkerPush')
server.register_inbound(WorkerPullService,
                        'WorkerPull',
                        'tcp://127.0.0.1:5557',
                        route='gateway_dealer')
server.register_outbound(WorkerPushService,
                         'WorkerPush',
                         'tcp://127.0.0.1:5558')
server.register_bypass(CacheService,
                       'Cache',
                       'tcp://127.0.0.1:5559')

if __name__ == '__main__':
    server.start()
