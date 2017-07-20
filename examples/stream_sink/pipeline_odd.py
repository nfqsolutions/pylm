from pylm.servers import Pipeline


class MyPipeline(Pipeline):
    def foo(self, message):
        self.logger.info('Got a message')
        return b'and I pipelined ' + message


if __name__ == '__main__':
    server = MyPipeline('my_pipeline',
                        db_address='tcp://127.0.0.1:5570',
                        sub_address='tcp://127.0.0.1:5557',
                        pub_address='tcp://127.0.0.1:5571',
                        previous='odd',
                        to_client=False)
    server.start()
