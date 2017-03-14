.. _workers:

Workers
=======

Workers are the simplest, but not least important, piece of the parallel
servers in pylm. They are in charge of doing the actual work, since the
master server deals with worker management, storing data, and other smaller
details.

A worker subclasses :py:class:`pylm.servers.Worker`, and defines a set of
additional methods that are exposed to the cluster. To configure the worker,
only the ``db_address`` parameter is needed, since the other sockets that
connect to the master are usually configured automatically. However, those
arguments are present in case you really need to set them manually.

Another feature of the workers is that they are connected to the key-value
store of the Master or the Hub, along with the client. This means that the
key-value store can be used to communicate each worker with the client and with
the other workers too. The methods to interact with the key-value store are
the same as the client's.