from pylm.servers import Pipeline
import logging


class MyPipeline(Pipeline):
    def foo(self, message):
        self.logger.warning('Got a message')
        return b'and I pipelined ' + message


if __name__ == '__main__':
    server = MyPipeline('my_pipeline',
                        db_address='tcp://127.0.0.1:5560',
                        sub_address='tcp://127.0.0.1:5557',
                        pub_address='tcp://127.0.0.1:5561',
                        previous='my_server',
                        to_client=True,
                        log_level=logging.DEBUG
                        )
    server.start()