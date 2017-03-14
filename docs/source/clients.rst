Clients
=======

A client has the mission of being the source, and maybe the sink, of the
message pipeline. The capabilities of the clients are
related on how the stream of messages is handled, so this section is a short
review of all of them. You can find the clients in :py:mod:`pylm.clients`, like
:py:class:`pylm.clients.Client`, and they all work in a
very similar way.

The simplest configuration is to connect the client to the
``db_address`` of a :py:class:`pylm.servers.Server` or a
:py:class:`pylm.servers.Master`, with its corresponding ``server_name``. If no
other arguments are specified, the client will assume that you want to
send all the messages to this server, and also to receive all its output back.
There are several examples on how these sockets are managed manually to control
the flow of data around the cluster, particularly when there are
:py:class:`pylm.servers.Pipeline` and :py:class:`pylm.servers.Hub`. You can see
some of the cases in the :ref:`examples` section, in which the ``sub_address``
argument is set as the address of the last server in the pipeline.

Another relevant argument is the ``session``, a tag that is added to all the
messages in case you need to label them somehow. It is relevant when using
the cache of the servers, and it may be useful in some applications.

Clients connect to the key-value store of the server they send the message
stream. This feature can be used to implement all sorts of algorithms, and it
comes handy when one has to communicate the client with the workers with
more information that the one that is sent through the messages. A client
has therefore the usual functions for the management of key-value stores:
:py:meth:`pylm.clients.Client.get`, :py:meth:`pylm.clients.Client.set` and
:py:meth:`pylm.clients.Client.delete`.

.. note::

    The set function reverses the argument order from the usual. The first
    argument is the value and the second is the key. The reason for that is
    that you can set a value without the key, and the client generates a
    random key for you.

The two methods that are used to start the execution of a pipeline are
:py:meth:`pylm.clients.Client.eval` and :py:meth:`pylm.clients.Client.job`.
The former sends only one message, while the latter loops over a generator
that produces the message stream. In any case, the message is of the type
:py:class:`bytes`.

The first argument of these two methods is the function to be called in the
server or the succession of servers forming a pipeline. The argument can be
therefore a string or a list of string, always formatted as two words: the name
of the server and the function, separated by a dot. For instance, if we
have a server called *first* connected to a pipeline called *second*, and we
want to call the *firstfunction* of the former, and the *secondfunction* of
the latter, the first argument will be the following list::

    ['first.firstfunction', 'second.secondfunction']

The second argument is the palyoad described previously, while the third
argument ``messages`` refers to the number of messages the client has to
receive before it exits. If this value is not set, it just stays alive
forever waiting for a practically inifinite number of messages.

The last argument ``cache`` sets the *cache* field of the message, and it is
intended for advanced uses.