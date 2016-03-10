import zmq
import time
from concurrent.futures import ThreadPoolExecutor

zmq_context = zmq.Context.instance()


class Master(object):
    def __init__(self, bind_address="inproc://master"):
        self.socket = zmq_context.socket(zmq.PUSH)
        self.socket.bind(bind_address)
        self.bind_address = bind_address

    def start(self):
        for i in range(10):
            self.socket.send(('{}'.format(i)).encode('utf-8'))


class Collector(object):
    def __init__(self, bind_address="inproc://collector"):
        self.socket = zmq_context.socket(zmq.PULL)
        self.socket.bind(bind_address)
        self.bind_address = bind_address

    def start(self):
        for i in range(10):
            print(self.socket.recv())
        
            
class Worker(object):
    def __init__(self, master_address, collector_address):
        self.socket_pull = zmq_context.socket(zmq.PULL)
        self.socket_push = zmq_context.socket(zmq.PUSH)
        self.socket_pull.connect(master_address)
        self.socket_push.connect(collector_address)
        
    def start(self):
        for i in range(10):
            m = self.socket_pull.recv()
            print('Worker got a message')
            self.socket_push.send(m)
            time.sleep(1)

if __name__ == '__main__':
    master = Master()
    collector = Collector()
    worker = Worker(master.bind_address, collector.bind_address)
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(master.start)
        executor.submit(collector.start)
        executor.submit(worker.start)
