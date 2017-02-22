from pylm.clients import Client

client = Client('server', 'tcp://127.0.0.1:5555',
                sub_address='tcp://127.0.0.1:5558')

if __name__ == '__main__':
    result = client.eval(['server.foo', 'hub.foo'], b'a message')
    print('Client got: ', result)
