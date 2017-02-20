# Pylm, a framework to build components for high performance distributed
# applications. Copyright (C) 2016 NFQ Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pylm.parts.core import Router
from pylm.persistence.kv import DictDB
from pylm.parts.messages_pb2 import PalmMessage
import concurrent.futures
import traceback
import logging
import sys


class ServerTemplate(object):
    """
    Low-level tool to build a server from parts.

    :param logging_level: A correct logging level from the logging module.
    Defaults to INFO.

    It has important attributes that you may want to override, like

    :cache: The key-value database that the server should use
    :logging_level: Controls the log output of the server.
    :router: Here's the router, you may want to change its attributes too.
    """
    def __init__(self,
                 logging_level=logging.INFO,
                 router_messages=sys.maxsize):
        # Name of the server
        self.name = ''

        # Logging level for the server
        self.logging_level = logging_level

        # Basic Key-value database for storage
        self.cache = DictDB()

        self.inbound_components = {}
        self.outbound_components = {}
        self.bypass_components = {}

        # Basic console logging
        self.logger = logging.getLogger(name=self.name)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(self.logging_level)

        # Finally, the router
        self.router = Router(logger=self.logger,
                             cache=self.cache,
                             messages=router_messages)

    def register_inbound(self, part, name='', listen_address='', route='',
                         block=False, log='', **kwargs):
        """
        Register inbound part to this server.

        :param part: part class
        :param name: Name of the part
        :param listen_address: Valid ZeroMQ address listening to the exterior
        :param route: Outbound part it routes to
        :param block: True if the part blocks waiting for a response
        :param log: Log message in DEBUG level for each message processed.
        :param kwargs: Additional keyword arguments to pass to the part
        """
        # Inject the server cache in case it is not configured for the component
        if 'cache' not in kwargs:
            kwargs['cache'] = self.cache

        instance = part(name,
                        listen_address,
                        broker_address=self.router.inbound_address,
                        logger=self.logger,
                        **kwargs)

        self.router.register_inbound(name,
                                     route=route,
                                     block=block,
                                     log=log)

        self.inbound_components[name] = instance

    def register_outbound(self, part, name='', listen_address='', route='',
                          log='', **kwargs):
        """
        Register outbound part to this server

        :param part: part class
        :param name: Name of the part
        :param listen_address: Valid ZeroMQ address listening to the exterior
        :param route: Outbound part it routes the response (if there is) to
        :param log: Log message in DEBUG level for each message processed
        :param kwargs: Additional keyword arguments to pass to the part
        """
        # Inject the server cache in case it is not configured for the component
        if 'cache' not in kwargs:
            kwargs['cache'] = self.cache

        instance = part(name,
                        listen_address,
                        broker_address=self.router.outbound_address,
                        logger=self.logger,
                        **kwargs)

        self.router.register_outbound(name,
                                      route=route,
                                      log=log)

        self.outbound_components[name] = instance

    def register_bypass(self, part, name='', listen_address='', **kwargs):
        """
        Register a bypass part to this server

        :param part: part class
        :param name: part name
        :param listen_address: Valid ZeroMQ address listening to the exterior
        :param kwargs: Additional keyword arguments to pass to the part
        """
        # Inject the server cache in case it is not configured for the component
        if 'cache' not in kwargs:
            kwargs['cache'] = self.cache

        instance = part(name,
                        listen_address,
                        logger=self.logger,
                        **kwargs)

        self.bypass_components[name] = instance

    def preset_cache(self, **kwargs):
        """
        Send the following keyword arguments as cache variables. Useful
        for configuration variables that the workers or the clients
        fetch straight from the cache.

        :param kwargs:
        """
        for arg, val in kwargs.items():
            if type(val) == str:
                self.cache.set(arg, val.encode('utf-8'))
            else:
                self.cache.set(arg, val)

    def start(self):
        """
        Start the server with all its parts.
        """
        threads = []

        self.logger.info("Starting the router")
        threads.append(self.router.start)
        
        for name, part in self.inbound_components.items():
            self.logger.info("Starting inbound part {}".format(name))
            threads.append(part.start)

        for name, part in self.outbound_components.items():
            self.logger.info("Starting outbound part {}".format(name))
            threads.append(part.start)

        for name, part in self.bypass_components.items():
            self.logger.info("Starting bypass part {}".format(name))
            threads.append(part.start)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(threads)) as executor:
            results = [executor.submit(thread) for thread in threads]
            for future in concurrent.futures.as_completed(results):
                try:
                    future.result()
                except Exception as exc:
                    self.logger.error('This is critical, one of the parts died')
                    lines = traceback.format_exception(*sys.exc_info())
                    for line in lines:
                        self.logger.error(line.strip('\n'))


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
