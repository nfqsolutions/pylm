from pylm.standalone import Client

client = Client('tcp://127.0.0.1:5555', 'my_server')

if __name__ == '__main__':
    result = client.job('foo', b'a message')
    print('Client got: ', result)
