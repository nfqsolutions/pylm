from threading import Lock
import plyvel
import pickle
import tempfile
import shutil


# Class that implements a simple on-disk key value data store for the servers
# and the services. This is a required service, but it does not have to be
# implemented exactly like the Python version

class DictDB(dict):
    """
    DictDB is just a dictionary with a lock that keeps threads from colliding.
    """
    lock = Lock()

    def get(self, key):
        try:
            return self.__getitem__(key)
        except KeyError:
            return None

    def set(self, key, value):
        with self.lock:
            self.__setitem__(key, value)

    def delete(self, key):
        with self.lock:
            self.__delitem__(key)


class IndexedLevelDB(object):
    """
    Make `Leveldb` behave a little like pickledb, with support for lists.
    """

    def __init__(self, path, create_if_missing=True):
        """
        Database initialisation
        :param path: Database path folder.
        :param create_if_missing: Create the file if it is not already present
        :return: No return value.

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> shutil.rmtree(tempdir)
        """
        self.db = plyvel.DB(path, create_if_missing=create_if_missing)
        self.index = {}

    def __contains__(self, item):
        if item in self.index:
            return True
        else:
            return False

    def set(self, key, value, serialize=False):
        """
        Sets a value in the database
        :param key:
        :param value:
        :param serialize: If True, data is serialized using a native format
        :return: No return value

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.set('key1','A value', serialize=True)
        >>> db.set('key2', 0.01, serialize=True)
        >>> shutil.rmtree(tempdir)
        """
        # TODO: CHANGE THE SET TO CONFORM THE NEW V, K CONVENTION.
        self.index[key] = 0
        if serialize:
            self.db.put(key.encode("UTF-8"), pickle.dumps(value))
        else:
            self.db.put(key.encode("UTF-8"), value)

    def get(self, key, serialize=False):
        """
        Get the value of a key
        :param key:
        :param serialize: If True, data is deserialized
        :return: the value

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.set('key1','A value', serialize=True)
        >>> db.set('key2', 1234, serialize=True)
        >>> assert db.get('key1', serialize=True) == 'A value'
        >>> assert db.get('key2', serialize=True) == 1234
        >>> shutil.rmtree(tempdir)
        """
        if serialize:
            return pickle.loads(self.db.get(key.encode("UTF-8")))
        else:
            return self.db.get(key.encode("UTF-8"))

    def delete(self, key):
        """
        Delete a key or a list
        :param key:
        :return: No return value
        """
        if self.index[key] > 0:
            self.list_delete(key)
        else:
            self.db.delete(key.encode("UTF-8"))
            del self.index[key]

    def list_create(self, key):
        """
        Group a series of key-value pairs using key as a
        prefix, and an integer as a sub-index.
        :param key:
        :return: No return value
        """
        self.index[key] = 0

    def list_append(self, key, value, serialize=False, create=False):
        """
        Appends the value to the list identified by key
        :param key: Key for the list
        :param value: Value to be appended
        :param serialize: If True, data is serialized using a native format
        :param create: If True, the list will be created and value will
          be appended as first element
        :return: No return value

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.list_append('key1', 0.01, serialize=True, create=True)
        >>> db.list_append('key1', 0.02, serialize=True)
        >>> shutil.rmtree(tempdir)
        """
        if key in self.index:
            self.index[key] += 1
            new_key = '_'.join((key, str(self.index[key]).zfill(16)))
            self.set(new_key, value, serialize)

        else:
            if create and key not in self:
                self.list_create(key)
                self.index[key] += 1
                new_key = '_'.join((key, str(self.index[key]).zfill(16)))
                self.set(new_key, value, serialize)
            else:
                raise KeyError('Key not found. Maybe you should create the list first')

    def list_get_all(self, key, serialize=False):
        """
        Returns all the values under prefix in order
        :param key:
        :param serialize: If True, data will be deserialized
        :return: iterator with all the values under key

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.list_append('key1', 1234, serialize=True, create=True)
        >>> db.list_append('key1', 5678, serialize=True)
        >>> output = [it for it in db.list_get_all('key1', serialize=True)]
        >>> assert output == [1234,5678]
        >>> shutil.rmtree(tempdir)
        """
        if key in self.index:
            for _, value in self.db.iterator(prefix=key.encode("UTF-8")):
                if serialize:
                    yield pickle.loads(value)
                else:
                    yield value
        else:
            raise KeyError('List not found')

    def prefix_get_all(self, key, serialize=False):
        """
        Returns all the values under prefix in order
        :param key:
        :param serialize: If True, data will be deserialized
        :return: iterator with all the values under key

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.set('key1', 1234, serialize=True)
        >>> db.set('key2', 5678, serialize=True)
        >>> output = [it for it in db.prefix_get_all('key', serialize=True)]
        >>> assert output == [1234,5678]
        >>> shutil.rmtree(tempdir)
        """
        for _, value in self.db.iterator(prefix=key.encode("UTF-8")):
            if serialize:
                yield pickle.loads(value)
            else:
                yield value

    def list_get_range(self, key, start=0, stop=-1, serialize=False, reverse=False):
        """
        Returns all the values under prefix in order
        :param key:
        :param start:
        :param stop:
        :param serialize: If True, data will be deserialized
        :param reverse:
        :return: iterator with all the values under key

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.list_create('key1')
        >>> for i in range(100): db.list_append('key1', i, serialize=True)
        >>> output = [it for it in db.list_get_range('key1', 3, 6, serialize=True)]
        >>> assert output == [3,4,5]
        >>> output = [it for it in db.list_get_range('key1', start=3, stop=9, serialize=True)]
        >>> assert output == [3,4,5,6,7,8]
        >>> output = [it for it in db.list_get_range('key1', start=95, stop=101, serialize=True)]
        >>> assert output == [95,96,97,98,99]
        >>> output = [it for it in db.list_get_range('key1', start=95, serialize=True, reverse=True)]
        >>> assert output == [99,98,97,96,95]
        >>> shutil.rmtree(tempdir)
        """
        if key in self.index:
            if stop < 0 or (stop + 1) > self.list_get_size(key):
                stop = self.list_get_size(key)

            # The keys have to be filled with 0 to be comparable
            for _, value in self.db.iterator(
                    start=('_'.join([key, str(start+1).zfill(16)])).encode("UTF-8"),
                    stop=('_'.join([key, str(stop+1).zfill(16)])).encode("UTF-8"),
                    reverse=reverse):
                if serialize:
                    yield pickle.loads(value)
                else:
                    yield value
        else:
            raise KeyError('List not found')

    def list_get_last(self, key, serialize=False):
        """
        Returns the last value under prefix.
        :param key:
        :param serialize: If True, data will be deserialized
        :return: Last element set under key

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.list_append('key1', 1234, serialize=True, create=True)
        >>> db.list_append('key1', 5678, serialize=True)
        >>> output = db.list_get_last('key1', serialize=True)
        >>> assert output == 5678
        >>> shutil.rmtree(tempdir)
        """
        if key in self.index:
            new_key = '_'.join((key, str(self.index[key]).zfill(16)))
            return self.get(new_key, serialize)
        else:
            raise KeyError('List not found')

    def list_get_size(self, key):
        """
        Get last key in list
        :param key: Get size of the list
        :return: Integer. Size of the list

        >>> tempdir = tempfile.mkdtemp()
        >>> db = IndexedLevelDB(tempdir, create_if_missing=True)
        >>> db.list_append('key1', 1234, serialize=True, create=True)
        >>> db.list_append('key1', 5678, serialize=True)
        >>> assert db.list_get_size('key1') == 2
        >>> shutil.rmtree(tempdir)
        """
        return self.index[key]

    def list_delete(self, key):
        """
        Deletes the list identified with key
        :param key: Key for the prefix of the list to be deleted
        :return: No return value
        """
        if key in self.index:
            for idx in range(1, self.index[key]+1):
                new_key = '_'.join((key, str(idx).zfill(16)))
                self.delete(new_key)

            del self.index[key]
        else:
            raise KeyError('List not found')


def test_all():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    test_all()
