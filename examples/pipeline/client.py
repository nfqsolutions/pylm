from pylm.clients import Client

client = Client('my_server', 'tcp://127.0.0.1:5555',
                sub_address='tcp://127.0.0.1:5561')

if __name__ == '__main__':
    result = client.eval(['my_server.foo', 'my_pipeline.foo'], b'a message')
    print('Client got: ', result)
