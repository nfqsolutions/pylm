from pylm.components.core import Router
from pylm.persistence.kv import DictDB
from pylm.components.messages_pb2 import PalmMessage
from pylm.components.utils import Pinger, PushHandler, PerformanceCounter
from threading import Thread
import logging
import sys


class ServerTemplate(object):
    """
    Low-level tool to build a server from components.

    :param ping_address: Address for the external health monitoring service
    :param log_address: Address for the external logging service
    :param perf_address: Address for the external performance analysis service

    It has important attributes that you may want to override, like

    :palm: Whether your messages are serialized using PALM messages or not
    :cache: The key-value database that the server should use
    :logging_level: Controls the log output of the server.
    :router: Here's the router, you may want to change its attributes too.
    """
    def __init__(self,
                 ping_address: str = '',
                 log_address: str = '',
                 perf_address: str = ''):
        # Name of the server
        self.name = ''

        # Messages use the PALM specification
        self.palm = False

        # Logging level for the server
        self.logging_level = logging.INFO

        # Basic Key-value database for storage
        self.cache = DictDB()

        self.inbound_components = {}
        self.outbound_components = {}
        self.bypass_components = {}

        # Services that may be configured or not

        # Configure the pinger.
        if ping_address:
            self.pinger = Pinger(listen_address=ping_address, every=30.0)

            # This is the pinger thread that keeps the pinger alive.
            pinger_thread = Thread(target=self.pinger.start)
            pinger_thread.daemon = True
            pinger_thread.start()

        if log_address:
            handler = PushHandler(log_address)
            self.logger = logging.getLogger(self.name)
            self.logger.addHandler(handler)
            self.logger.setLevel(self.logging_level)

        else:
            # Basic console logging
            self.logger = logging.getLogger(name=self.name)
            self.logger.setLevel(self.logging_level)
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(self.logging_level)

        if perf_address:
            # Configure the performance counter
            self.perfcounter = PerformanceCounter(listen_address=perf_address)

        # Finally, the router
        self.router = Router(logger=self.logger,
                             cache=self.cache)

    def register_inbound(self, component, name, listen_address, route='', block=False, log='', **kwargs):
        """
        Register inbound component to this server.

        :param component: Component class
        :param name: Name of the component
        :param listen_address: Valid ZeroMQ address listening to the exterior
        :param route: Outbound component it routes to
        :param block: True if the component blocks waiting for a response
        :param log: Log message in DEBUG level for each message processed.
        :param kwargs: Additional keyword arguments to pass to the component
        """
        instance = component(name,
                             listen_address,
                             broker_address=self.router.inbound_address,
                             logger=self.logger,
                             palm=self.palm,
                             cache=self.cache,
                             **kwargs)

        self.router.register_inbound(name,
                                     route=route,
                                     block=block,
                                     log=log)

        self.inbound_components[name] = instance

    def register_outbound(self, component, name, listen_address, log='', **kwargs):
        """
        Register outbound component to this server

        :param component: Component class
        :param name: Name of the component
        :param listen_address: Valid ZeroMQ address listening to the exterior
        :param log: Log message in DEBUG level for each message processed
        :param kwargs: Additional keyword arguments to pass to the component
        """
        instance = component(name,
                             listen_address,
                             broker_address=self.router.outbound_address,
                             logger=self.logger,
                             palm=self.palm,
                             cache=self.cache,
                             **kwargs)

        self.router.register_outbound(name,
                                      log=log)

        self.outbound_components[name] = instance

    def register_bypass(self, component, name, listen_address, **kwargs):
        """
        Register a bypass component to this server

        :param component: Component class
        :param name: Component name
        :param listen_address: Valid ZeroMQ address listening to the exterior
        :param kwargs: Additional keyword arguments to pass to the component
        """
        instance = component(name,
                             listen_address,
                             logger=self.logger,
                             cache=self.cache,
                             **kwargs)

        self.bypass_components[name] = instance

    def register_gateway(self):
        pass

    def start(self):
        """
        Start the server with all its components.
        """
        threads = []

        self.logger.info("Starting the router")
        threads.append(Thread(target=self.router.start))

        for name, component in self.inbound_components.items():
            self.logger.info("Starting inbound component {}".format(name))
            threads.append(Thread(target=component.start))

        for name, component in self.outbound_components.items():
            self.logger.info("Starting outbound component {}".format(name))
            threads.append(Thread(target=component.start))

        for name, component in self.bypass_components.items():
            self.logger.info("Starting bypass component {}".format(name))
            threads.append(Thread(target=component.start))

        for thread in threads:
            thread.start()

        self.logger.info("All components started successfully")


class BaseMaster(object):
    @staticmethod
    def change_payload(message: bytes, new_payload: bytes) -> bytes:
        """
        Change the payload of the message

        :param message: The binary message to be processed
        :param new_payload: The new binary payload
        :return: Serialized message with the new payload
        """
        palm_message = PalmMessage()
        palm_message.ParseFromString(message)
        palm_message.payload = new_payload
        return palm_message.SerializeToString()

    @staticmethod
    def change_call(message: bytes, next_server: str, next_call: str) -> bytes:
        """
        Assign a call for the next server

        :param message: The binary message to be processed
        :param next_server: The name of the next server
        :param next_call: The name of the function to be called
        :return: Serialized message with the new call
        """
        call = '.'.join([next_server, next_call])
        palm_message = PalmMessage()
        palm_message.ParseFromString(message)
        palm_message.function = call
        return palm_message.SerializeToString()

    def scatter(self, message: bytes):
        """
        Scatter function for inbound messages

        :param message: Binary message
        :return: Yield none, one or multiple binary messages
        """
        yield message

    def gather(self, message: bytes):
        """
        Gather function for outbound messages

        :param message: Binary message
        :return: Yield none, one or multiple binary messages
        """
        yield message
