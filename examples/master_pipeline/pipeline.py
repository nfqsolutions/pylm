from pylm.servers import Pipeline
import logging


class MyPipeline(Pipeline):
    def foo(self, message):
        self.logger.info('Got a message')
        return b'and I pipelined ' + message


if __name__ == '__main__':
    server = MyPipeline('my_pipeline',
                        db_address='tcp://127.0.0.1:5560',
                        sub_address='tcp://127.0.0.1:5556',
                        pub_address='tcp://127.0.0.1:5561',
                        previous='server',
                        to_client=True)
    server.start()