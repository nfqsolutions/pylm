from pylm.standalone import Master


server = Master(name='server',
                pull_address='tcp://127.0.0.1:5555',
                push_address='tcp://127.0.0.1:5556',
                worker_pull_address='tcp://127.0.0.1:5557',
                worker_push_address='tcp://127.0.0.1:5558',
                db_address='tcp://127.0.0.1:5559',
                palm=True)

def scatter(message):
    for i in range(3):
        yield message

# Monkey patching the component's method
server.pull_service.scatter = scatter

if __name__ == '__main__':
    server.start()
