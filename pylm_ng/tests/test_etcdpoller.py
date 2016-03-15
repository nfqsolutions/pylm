from pylm_ng.components.core import Broker
from pylm_ng.daemons.extra_components import EtcdPoller
from pylm_ng.compoments.connections import PushConnection
from pylm_ng.tests.endpoints import PullEndPoint, logger
from threading import Thread


def test_etcd_poller():
    """
    Tests the following sequence

    HTTP reply -> broker -> Push Connection -> Pull endpoint.
    :return:
    """

    broker = Broker(logger=logger, messages=10)
    endpoint_pull = PullEndPoint(logger=logger)
    poller = EtcdPoller('etcdpoller', )

