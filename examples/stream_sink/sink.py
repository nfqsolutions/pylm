from pylm.servers import Sink
import logging


class MySink(Sink):
    def foo(self, message):
        self.logger.warning('Got a message')
        return b'and gathered ' + message


if __name__ == '__main__':
    server = MySink('my_sink',
                    db_address='tcp://127.0.0.1:5580',
                    sub_addresses=['tcp://127.0.0.1:5561', 'tcp://127.0.0.1:5571'],
                    pub_address='tcp://127.0.0.1:5581',
                    previous=['my_pipeline', 'my_pipeline'],
                    to_client=True,
                    log_level=logging.DEBUG
    )
    server.start()
    
