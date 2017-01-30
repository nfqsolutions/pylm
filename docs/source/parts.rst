Building components from separate parts
=======================================

The router
----------

At the very core of most Pylm servers, there is a router, and its architecture is the only profound idea
in the whole pylm architecture. The goal is to manage the communication between the servers in a way as much
similar to an actual network architecture as possible.


.. only:: html

    .. figure:: _images/core.png
        :align: center

.. only:: latex

    .. figure:: _images/core.pdf
        :align: center
        :scale: 60

The two tall blocks at each side of a routing table are two ZeroMQ ROUTER sockets. The one in the left deals with
the messages arriving to the router (inbound), while the one in the right sends the messages away from the router
(outbound). At each side there are a series of parts that are connected to the exterior and the router. If
you know how an actual router works, a part would be a NIC, while the two ROUTER sockets and the routing table
would be the switch. The router is documented in :py:class:`pylm.parts.core.Router`.

The parts are also related to the router by the fact that they are all threads that run
within the same processor. In consequence, a pylm micro-service could be described as a router and a series of
parts that run in the same process.


The parts
---------

The parts can be inbound or outbound, and blocking or non-blocking.

:`Inbound part`: The part waits for a message coming from the exterior. This kind of parts
    are documented in :py:class:`pylm.parts.core.ComponentInbound`. This includes parts that connect to the
    exterior via SUB or PULL sockets.

:`Outbound part`: The part waits for a message coming from the router.  This kind of parts
    are documented in :py:class:`pylm.parts.core.ComponentOutbound`. This includes parts that connect to the
    exterior via PUB or PUSH sockets.

:`Non-blocking part`: The part never blocks after getting the message, regardless if the message comes
    from the router or the exterior.

:`Blocking part`: The part blocks after getting the message to give a response, even if the message is sent
    to the router. **You must know what you are doing if you use this kind of parts**, because they tend to block the
    ROUTER socket completely. This is the reason why in the previous sketch about the router and the parts, there
    are arrows that point in both directions, meaning that messages may block the rest of the router to go back and
    forth.

While Inbound and Outbound parts are different classes, the blocking or non-blocking type is set with a parameter
when the part is instantiated.

The two part classes (:py:class:`pylm.parts.core.ComponentInbound` and
:py:class:`pylm.parts.core.ComponentOutbound`) are not designed to be used but to be subclassed. The children
of the parts are called services and connections.

Services and connections
------------------------

The family of parts grows with their children: the services and the connections. We have classified the
parts as a function of where the message comes from and their behavior. One can further classify the parts
whether they bind the socket or they connect to a socket.

:Service: A part that binds a socket that faces the exterior.

:Connection: A part that connects to an exterior socket.

With this piece of classification, the whole family picture is (almost) over. There is a small library of services
available in :py:mod:`pylm.parts.services`, and a similar library of parts in
:py:mod:`pylm.parts.connections`.

.. note::

   All parts, and the router, have a ``start`` method. Since they are all designed to run on a thread, the
   threading library must call only that method to get the part running.


It's time to build a small micro-service from a router and some services and parts that are already available.
This way you will have a rough idea of how the high level API of pylm is built. Some of the details of the
implementation are not described yet, but this example is a nice prologue about the things you need to know
to master the low level API.

In this section, we have seen that the router is a crucial part of any server in pylm. The helper class
:py:class:`pylm.parts.servers.ServerTemplate` is designed to easily attach the parts to a router. The internal
design of a master server can be seen in the following sketch.


.. only:: html

    .. figure:: _images/master_internals.png
        :align: center

.. only:: latex

    .. figure:: _images/master_internals.pdf
        :align: center
        :scale: 60


A master server like the one used in the examples needs the router and four service parts.

* A *Pull* part that receives the messages from the client

* A *Push* part that sends the messages to the workers

* A *Pull* part that gets the result from the workers

* A *Push* part that sends the results down the message pipeline or back to the client.

All parts are non-blocking, and the message stream is never interrupted.  All the parts are *services*,
meaning that the workers and the client connect to the respective sockets, since *service parts* bind to its
respective outwards-facing socket.

The part library has a part for each one of the needs depicted above. There is a
:py:class:`pylm.parts.services.PullService` that binds a ZeroMQ Pull socket to the exterior, and sends the
messages to the router. There is a :py:class:`pylm.parts.services.PubService` that works exactly the other
way around. It listens to the router, and forwards the messages to a ZeroMQ Push socket. There are also
specific services to connect to worker servers, :py:class:`pylm.parts.services.WorkerPullService` and
:py:class:`pylm.parts.services.WorkerPushService`, that are very similar to the two previously described
services. With those pieces, we are ready to build a master server as follows

.. literalinclude:: ../../examples/template/master.py
    :language: python
    :linenos:

.. note::

   There is an additional type of service called *bypass* in this implementation, that will be described at the end
   of this section.

This server is functionally identical to the master server used in the first example of the section describing
:ref:`standalone`. You can test it using the same client and workers.

Bypass parts
------------

