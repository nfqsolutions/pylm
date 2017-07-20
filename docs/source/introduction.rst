.. _introduction:

Introduction
============

This is a short introduction of some of the key aspects of pylm, a framework to implement high performance
micro-services from reusable components.

But let's begin with something basic, a server and a client able to call one of the server's methods. Much in the
fashion of a RPC server.

.. only:: html

    .. figure:: _images/single.png
        :align: center

.. only:: latex

    .. figure:: _images/single.pdf
        :align: center
        :scale: 60

With pylm, the first step is to create the server by subclassing one of the available templates in the high-level API:

.. literalinclude:: ../../examples/single/server.py
    :language: python
    :linenos:

Secondly, we create the client that connects to the server and calls the ``foo`` function from the server.

.. literalinclude:: ../../examples/single/client.py
    :language: python
    :linenos:

It does not care in which order you start the client and the server, pylm
uses ZeroMQ sockets for all the connections, that deal with all the details.
Pylm uses ZeroMQ extensively, and somehow, it also follows its philosophy.

This is what we get when we start the server::

    $> python server.py
    2016-08-09 07:34:53,205 - my_server - WARNING - Got a message

And the client::

    $> python client.py
    Client got: b'you sent me a message'

Which is what we expected. The function ``foo`` only picks what is sent from the client,
and adds it to ``you sent me``. As simple as it seems. However, this basic example
allows us to discover some important aspects of pylm.

* All messages are binary, represented as a sequence of bytes. This means that
  you decide how to serialize and deserialize the data you send to the server.
  If I decided to send a number instead of a sequence of bytes
  (replacing line 6 for ``result = client.job('foo', 1)``), the client would
  crash with a *TypeError*.

* The server inherits from :py:class:`pylm.servers.Server`. This parent
  class includes some interesting capabilities so you don't have to deal with
  health monitoring, logging, performance analysis and so on. Maybe you don't need
  all these things with a single server, but they become really handy when you
  have to monitor hundreds of microservers.

* The philisopy of pylm has two main principles:

  #. Simple things must be simple. If you don't need something, you just ignore it
     and the whole system will react accordingly.

  #. Pylm is a framework, and does not come with any imposition that is not strictly
     necessary. Use the deployment system of your choice, the infrastructure you
     want... Pylm gives you the pieces to create the cluster, and you are in charge
     of the rest.

.. important::      

    At this point you are maybe wondering where to start, and you are afraid that you
    may have to read tons of documentation to start using pylm. Well, despite we'd love if
    you carefully read the documentation, it is probable that you find a template that works
    for you in the :ref:`examples` section. This way you can start from code that it
    already works.
     
The example presented in this section does not honor of the capabilities of pylm. Particularly the
patterns that support parallel execution of jobs. To learn what are the capabilities
of the different servers that are already implemented in pylm, visit the section about
the :ref:`high-level-api`.

If you want to understand the underlying principles and algorithms of the small components
that are used to implement a palm micro-service, visit the section about the :ref:`low-level-api`.

