from pylm.parts.servers import ServerTemplate
from pylm.parts.services import PullService, PubService, WorkerPullService, WorkerPushService, \
    CacheService

server = ServerTemplate()

db_address = 'tcp://127.0.0.1:5559'
pull_address = 'tcp://127.0.0.1:5555'
pub_address = 'tcp://127.0.0.1:5556'
worker_pull_address = 'tcp://127.0.0.1:5557'
worker_push_address = 'tcp://127.0.0.1:5558'

server.register_inbound(PullService, 'Pull', pull_address, route='WorkerPush')
server.register_inbound(WorkerPullService, 'WorkerPull', worker_pull_address, route='Pub')
server.register_outbound(WorkerPushService, 'WorkerPush', worker_push_address)
server.register_outbound(PubService, 'Pub', pub_address)
server.register_bypass(CacheService, 'Cache', db_address)
server.preset_cache(name='server',
                    db_address=db_address,
                    pull_address=pull_address,
                    pub_address=pub_address,
                    worker_pull_address=worker_pull_address,
                    worker_push_address=worker_push_address)

if __name__ == '__main__':
    server.start()
