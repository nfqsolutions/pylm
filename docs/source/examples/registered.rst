A simple sequential pipeline
============================

This is a small example of the simplest server, that uses RegisteredServer as
a template. Its functionality is simple. It receives a random string, that
will make sense in other examples, and uses several important features of the
the server.

The code inherits ``RegisteredServer``, that has to be extended, the
helper function ``run_server``, and the constant ``SUCCESS``.  Extending a
server is about overriding existing functions, and implementing new ones. In
this case, this server called ``printf`` overrides the function ``reply``,
and implements the new function ``printf``.

The server
----------

.. literalinclude::  ../../../examples/example_registered/printf.py
    :language: python
    :linenos:


The behavior of the function ``reply`` is precisely to reply the client.

.. note::

    PALM offers some *enabling features*. It makes some things possible that
    are not strictly part of the concept of pipeline, like replying to the
    client. Some features are not intended for doing a precise task, but to
    make things possible. You do not have to reply to the client, but if some
    day you need to do it, PALM allows you to.  You may think that this is
    feature creep, but this is not. This means that the development team has
    found a case that justified adding that feature. You may run into the
    same case or not.

The function ``printf`` does some more things than the former. It assumes
that the message is serialized using json and encoded with UTF-8. It then
logs the deserialized message to the standard logger, with a logging level
of *critical*. The method ``self.log`` is the available logger, and it
centralizes all the messages in the registry.

.. important::

    All user-implemented functions must return a value. Sometimes it is a
    message for the next server down the pipeline, sometimes it is needed to
    synchronize

The client
----------

.. literalinclude::  ../../../examples/example_registered/client.py
    :language: python
    :linenos:


Running the example
-------------------

.. code-block:: bash

    $> python client.py
    100 b'Something in reply'

.. code-block:: none

    $> journalctl -n -u registry
    -- Logs begin at Fri 2015-11-06 12:01:43 CET, end at Tue 2016-02-16 17:38:33  CET. --
    Feb 16 17:38:33 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining
    Feb 16 17:38:33 nfqbabe registry.py[4559]: INFO:registry:9bd0999a-f222-47c9-8fa3-d10c49091631/printf/registered : b'I,2016-02-16T16:38:30.670213:9bd
    Feb 16 17:38:33 nfqbabe registry.py[4559]: : 87e14951eb50a0d9d7728deaa63d2a, 2016-02-16T16:38:30.688256:9bd0999a-f222-47c9-8fa3-d10c49091631:CRITICAL
    Feb 16 17:38:33 nfqbabe registry.py[4559]: :30 .692830:9bd0999a-f222-47c9-8fa3-d10c49091631:CRITICAL:printf.py/11:OUTPUT: bed7a17cd4cebfc9153e2755fa8
    Feb 16 17:38:33 nfqbabe registry.py[4559]: CRITICAL:printf.py/11:OUTPUT: 2c8c05319db913368734d94971687d,2016-02-16T16:38:30.696155:9bd0999a-f222-47c
    Feb 16 17:38:33 nfqbabe registry.py[4559]: fa987b04e1b,2016-02-16T16:38:30.698818:9bd0999a-f222-47c9-8fa3-d10c49091631:CRITICAL:printf.py/11:OUTPUT:
    Feb 16 17:38:33 nfqbabe registry.py[4559]:  222-47c9-8fa3-d10c49091631:CRITICAL:printf.py/11:OUTPUT: b97f701de842e5e7ae0f9572db6e2d,2016-02-16T16:38:
    Feb 16 17:38:33 nfqbabe registry.py[4559]: OUTPUT: efc33c5ef0b041e201960295fd8226,2016-02-16T16:38:30.704326:9bd0999a-f222-47c9-8fa3-d10c49091631:CR
    Feb 16 17:38:33 nfqbabe registry.py[4559]: INFO:registry:0 dead servers
    Feb 16 17:38:33 nfqbabe registry.py[4559]: INFO:registry:1 servers remaining



