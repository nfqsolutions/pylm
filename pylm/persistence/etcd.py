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

from pylm.parts.core import zmq_context
from pylm.parts.messages_pb2 import PalmMessage
import requests
import time
import sys
import logging
import zmq
import json


MAX_RETRIES = 5


# Etcd client driver. In this version, the only requirement is the requests
# Python module. You can use an available client if you want, but the recommendation
# is to keep the same API.


class EtcdError(Exception):
    """Dummy error for dealing with etcd exceptions. It does nothing."""
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(EtcdError, self).__init__(message)


class Client(object):
    '''
    Very thin client for etcd. It supports only the required operations for our
    backends.
    '''
    def __init__(self, host='127.0.0.1', port=4001, version_prefix='/v2'):
        self.request_prefix = ''.join(['http://',
                                       host,
                                       ':',
                                       str(port),
                                       version_prefix,
                                       '/keys'])
        self.logger = logging.getLogger('etcd')

    def get(self, key, retries=MAX_RETRIES, params={}):
        """
        Gets a key from the key full path. Returns a dict
        """
        request_string = ''.join([self.request_prefix,key])
        try:
            req = requests.get(request_string,params=params)
        except requests.exceptions.ConnectionError:
            self.logger.error("Could not access etcd database")
            sys.exit(-1)
            
        self.logger.debug('Get key {}'.format(request_string))
        times = 1
        
        while req.status_code == 404: 
            req = requests.get(request_string)

            if req.status_code == 200:
                return req.json()

            if times == retries:
                raise EtcdError('Key {} not found'.format(key))

            times += 1
            time.sleep(0.25)

        return req.json()
        
    def list(self, key):
        """
        gets recursively from a node. Returns a dict
        """
        params = {'recursive':'true'}
        return self.get(key, params=params)

    def wait(self, key, wait_index = False):
        """
        Gets a key from the key full path. Returns a dict
        """
        if wait_index:
            params = {'recursive': 'true',
                      'wait': 'true',
                      'waitIndex': wait_index}
        else:
            params = {'recursive': 'true', 'wait': 'true'}
            
        return self.get(key, params=params)

    def put(self, key, value='', directory=False):
        """
        Puts a key with the key full path. Returns a dict.

        Set directory=True if the node is a directory. In this case, the value
        will be ignored
        """
        request_string = ''.join([self.request_prefix,key])

        if directory:
            request_params = {'dir': 'true'}
        else:
            request_params = {'value': value}

        try:
            r = requests.put(request_string,params=request_params)
        except requests.exceptions.ConnectionError:
            self.logger.error("Could not access etcd database")
            sys.exit(-1)

        self.logger.debug('Put key {} with value {}'.format(request_string,value))
        if r.status_code == 404:
            raise EtcdError("I don't know if it fits here.")

    def delete(self,key,directory=False):
        """
        Deletes a key or a node given the full path.
        """
        request_string = ''.join([self.request_prefix,key])
        self.logger.debug('Delete key {}'.format(request_string))
        if directory:
            r = requests.delete(request_string,params={'dir': 'true'})
        else:
            r = requests.delete(request_string)

        if r.status_code == 200:
            self.logger.debug('Successfully deleted key'.format(request_string))


class EtcdPoller(object):
    """
    Component that polls an etcd http connection and sends the result
    to the broker
    """
    def __init__(self, name, key, function='update',
                 broker_address='inproc://broker',
                 logger=None, messages=sys.maxsize):
        """
        :param name: Name of the connection
        :param key: Key of the dict to poll to
        :param broker_address: ZMQ address of the broker
        :param logger: Logger instance
        :param messages: Maximum number of messages. Intended for debugging.
        :return:
        """
        self.name = name.encode('utf-8')
        self.broker = zmq_context.socket(zmq.REQ)
        self.broker.identity = self.name
        self.broker.connect(broker_address)
        self.logger = logger
        self.messages = messages
        self.key = key
        self.function = function
        self.etcd = Client()
        self.wait_index = 0

    def start(self):
        self.logger.info('Launch Component {}'.format(self.name))
        for i in range(self.messages):
            self.logger.debug('Waiting for etcd')
            if self.wait_index > 0:
                response = self.etcd.wait(self.key, wait_index=self.wait_index)
            else:
                response = self.etcd.wait(self.key)

            self.wait_index = response['node']['modifiedIndex']+1
            self.logger.debug('New wait index: {}'.format(self.wait_index))
            message = PalmMessage()
            message.function = self.function
            message.pipeline = ''
            message.stage = 0
            message.client = 'EtcdPoller'
            message.payload = json.dumps(response).encode('utf-8')
            # Build the PALM message that tells what to do with the data
            self.broker.send(message.SerializeToString())
            # Just unblock
            self.logger.debug('blocked waiting broker')
            self.broker.recv()
            self.logger.debug('Got response from broker')

