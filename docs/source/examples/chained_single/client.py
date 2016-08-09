from pylm.chained import LoopClient


client = LoopClient('tcp://127.0.0.1:5555',
                    'tcp://127.0.0.1:5561',
                    'tcp://127.0.0.1:5556',
                    'step1')

if __name__ == '__main__':
    result = client.job('foo', b'a message')
    print('Client got: ', result)
