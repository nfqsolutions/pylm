from pylm.clients import Client
from itertools import repeat
from argparse import ArgumentParser


def parse_arguments():
    parser = ArgumentParser()
    parser.add_argument('--server', type=str,
                        help="Name of the component you want to connect to",
                        required=True)
    parser.add_argument('--function', type=str,
                        help="Name of the function you want to call",
                        required=True)
    parser.add_argument('--db', type=str,
                        help="tcp address of the cache service of the master "
                             "component",
                        default='tcp://127.0.0.1:5559')
    return parser.parse_args()


def main():
    args = parse_arguments()
    client = Client(args.server, args.db)

    for response in client.job('.'.join([args.server, args.function]),
                               repeat(b' a message', 10),
                               messages=10):
        print(response)


if __name__ == '__main__':
    main()