from pylm.clients import Client
from itertools import repeat

client = Client('my_server', 'tcp://127.0.0.1:5555',
                sub_address='tcp://127.0.0.1:5561')

if __name__ == '__main__':
    for response in client.job(['my_server.foo', 'my_pipeline.foo'],
                               repeat(b'a message', 10),
                               messages=5):
        print('Client got: ', response)
