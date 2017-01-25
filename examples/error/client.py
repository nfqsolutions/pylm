from pylm.clients import Client

client = Client('my_server', 'tcp://127.0.0.1:5555')

if __name__ == '__main__':
    result = client.eval('my_server.foo', b'a message', messages=1)
    print('Client got: ', result)
