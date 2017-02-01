from pylm.servers import Worker
from argparse import ArgumentParser
from uuid import uuid4


class MyWorker(Worker):
    def foo(self, message):
        return self.name.encode('utf-8') + b' processed' + message


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('--name', type=str, help='Name of this worker server',
                        default=str(uuid4()))
    parser.add_argument('--db', type=str,
                        help='Address for the db socket of the master server',
                        default='tcp://127.0.0.1:5559')

    return parser.parse_args()


def main():
    args = parse_arguments()
    server = MyWorker(args.name, args.db)
    server.start()


if __name__ == '__main__':
    main()