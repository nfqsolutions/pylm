from pylm.servers import Master
from argparse import ArgumentParser


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('--name', type=str,
                        help="Name of the component", required=True)
    parser.add_argument('--pull', type=str,
                        help="Tcp address of the pull service",
                        default='tcp://127.0.0.1:5555')
    parser.add_argument('--pub', type=str,
                        help="Tcp address of the pub service",
                        default='tcp://127.0.0.1:5556')
    parser.add_argument('--wpush', type=str,
                        help="Tcp address of the push-to-workers service",
                        default='tcp://127.0.0.1:5557')
    parser.add_argument('--wpull', type=str,
                        help="Tcp address of the pull-from-workers service",
                        default='tcp://127.0.0.1:5558')
    parser.add_argument('--db', type=str,
                        help="Tcp address of the cache service",
                        default='tcp://127.0.0.1:5559')

    return parser.parse_args()


def main():
    args = parse_arguments()
    server = Master(name=args.name,
                    pull_address=args.pull,
                    pub_address=args.pub,
                    worker_pull_address=args.wpull,
                    worker_push_address=args.wpush,
                    db_address=args.db)
    server.start()


if __name__ == '__main__':
    main()
