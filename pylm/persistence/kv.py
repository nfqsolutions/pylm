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

from threading import Lock


# Class that implements a simple in-memory key value data store for the servers
# and the services. This is a required service, but it does not have to be
# implemented exactly like the Python version.

class DictDB(object):
    """
    DictDB is just a dictionary with a lock that keeps threads from colliding.
    """
    lock = Lock()

    def __init__(self):
        self.store = {}

    def __contains__(self, item):
        if item in self.store:
            return True
        else:
            return False

    def get(self, key):
        try:
            return self.store[key]
        except KeyError:
            return None

    def set(self, key, value):
        with self.lock:
            self.store[key] = value

    def delete(self, key):
        with self.lock:
            del self.store[key]

    def clean(self, prefix):
        deleted = list()
        with self.lock:
            for key in self.store:
                if key.startswith(prefix):
                    deleted.append(key)

            for key in deleted:
                del self.store[key]

