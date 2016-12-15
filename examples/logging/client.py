from pylm.standalone import ParallelClient
from itertools import repeat

client = ParallelClient(push_address='tcp://127.0.0.1:5556',
                        pull_address='tcp://127.0.0.1:5555',
                        db_address='tcp://127.0.0.1:5559',
                        server_name='server')

if __name__ == '__main__':
    client.set(b' cached data ', 'cached')
    print(client.get('cached'))
    
    for response in client.job('foo', repeat(b'a message', 10), messages=30):
       print(response)
