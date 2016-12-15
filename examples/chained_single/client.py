from pylm.chained import LoopClient


client = LoopClient(push_address='tcp://127.0.0.1:5561',
                    pull_address='tcp://127.0.0.1:5555',
                    db_address='tcp://127.0.0.1:5556',
                    server_name='step1')

if __name__ == '__main__':
    for result in client.job('foo', [b'a message'], messages=1):
        print('Client got: ', result)
