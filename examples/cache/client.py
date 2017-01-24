from pylm.clients import Client
from itertools import repeat

client = Client('server', 'tcp://127.0.0.1:5559')

if __name__ == '__main__':
    client.set(b' cached data ', 'cached')
    print(client.get('cached'))
    
    for response in client.job('server.foo', repeat(b'a message', 10), messages=10):
        print(response)
