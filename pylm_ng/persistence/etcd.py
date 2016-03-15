import requests
import time
import sys
import logging


MAX_RETRIES = 5


# Etcd client driver. In this version, the only requirement is the requests
# Python module. You can use an available client if you want, but the recommendation
# is to keep the same API.


class EtcdError(Exception):
    'Dummy error for dealing with etcd exceptions. It does nothing.'
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


