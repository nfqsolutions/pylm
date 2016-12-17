from pylm.standalone import Client
from itertools import repeat

client = Client('server', 'tcp://127.0.0.1:5559',
                push_address='tcp://127.0.0.1:5555',
                sub_address='tcp://127.0.0.1:5556')

if __name__ == '__main__':
    for response in client.job('server.foo', repeat(b'a message', 10), messages=10):
        print(response)
