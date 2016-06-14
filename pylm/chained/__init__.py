"""
Series of servers and clients that can be chanied manually.
"""
from pylm.chained.client import Client, ParallelClient
from pylm.chained.servers import Master, Worker
from pylm.chained.endpoints import EndPoint