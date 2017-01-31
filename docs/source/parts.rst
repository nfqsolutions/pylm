Building components from separate parts
=======================================

The router
----------

At the very core of most Pylm servers, there is a router, and its
architecture is the only profound idea in the whole pylm
architecture. The goal is to manage the communication between the
servers in a way as much similar to an actual network architecture as
possible.


.. only:: html

    .. figure:: _images/core.png
        :align: center

.. only:: latex

    .. figure:: _images/core.pdf
        :align: center
        :scale: 60

The mission of this router sockets is to connect the parts that
receive inbound messages with the parts that deal with outbound
messages. The two tall blocks at each side of the table is a
representation with such connection. If you know how an actual router
works, a part would be a NIC, while the ROUTER socket and the routing
table would be the switch. The router is documented in
:py:class:`pylm.parts.core.Router`.

The parts are also related to the router by the fact that they are all
threads that run within the same process. In consequence, a pylm
server could be described as a router and a series of parts that run
in the same process.


The parts
---------

There is a decent number of parts, each one covering some functionality
within the PALM ecosystem. What follows is a classification of the several
parts that are already available according to their characteristics.

First of all, parts can be services or connections. A service is a
part that *binds* to a socket, which is an important detail when you
design a cluster. A bind socket blocks waiting for a connection from a
different thread or process. Therefore, a service is used to define
the communication endpoint. All the available services are present in
the module :py:mod:`pylm.parts.services`.

Connections are the complementary of servers, they are used in the
*client* side of the communication, and are present in the module
:py:mod:`pylm.parts.connections`.

On the second hand, parts can be standard or *bypass*. The former
connects to the router, while the latter ignores the router
completely. Bypass components inherit from
:py:class:`pylm.parts.core.BypassInbound` or from
:py:class:`pylm.parts.core.BypassOutbound` and also use the word
*bypass* in its name, while standard components that connect to the
router inherit from :py:class:`pylm.parts.core.Inbound` and
:py:class:`pylm.parts.core.Outbound`. As an example, the part
:py:class:`pylm.parts.services.CacheService`, regardless of not being
named as a bypass name, it exposes the internal cache of a server to
workers and clients and does no communicate to the router in any case.
    
On the third hand, and related to the previous classification, parts
can be inbound or outbound according to the direction of the *first*
message respect to the router. Inbound services and components inherit
from :py:class:`pylm.parts.core.Inbound` and
:py:class:`pylm.parts.core.BypassInbound`, while outbound inherit from
:py:class:`pylm.parts.core.Outbound` and
:py:class:`pylm.parts.core.BypassOutbound`.

On the fourth hand, components may block or not depending on whether
they expect the pair to send some message back. This behavior depends
on the kind of ZeroMQ socket in use.

.. warning::

   There is such a thing as a blocking outbound service. This means
   that the whole server is expecting some pair of an outbound service
   to send a message back. As you can imagine, these kind of parts
   must be handled with extreme care.

This classification may seem a little confusing, so we will offer
plenty of examples covering most of the services and connections
avialiable at the present version.
   
Services and connections
------------------------

It's time to build a small micro-service from a router and some
services and parts that are already available.  This way you will have
a rough idea of how the high level API of pylm is built. Some of the
details of the implementation are not described yet, but this example
is a nice prologue about the things you need to know to master the low
level API.

In this section, we have seen that the router is a crucial part of any
server in pylm. The helper class
:py:class:`pylm.parts.servers.ServerTemplate` is designed to easily
attach the parts to a router. The internal design of a master server
can be seen in the following sketch.


.. only:: html

    .. figure:: _images/master_internals.png
        :align: center

.. only:: latex

    .. figure:: _images/master_internals.pdf
        :align: center
        :scale: 60


A master server like the one used in the examples needs the router and
four service parts.

* A *Pull* part that receives the messages from the client

* A *Push* part that sends the messages to the workers

* A *Pull* part that gets the result from the workers

* A *Push* part that sends the results down the message pipeline or back to the client.

All parts are non-blocking, and the message stream is never
interrupted.  All the parts are *services*, meaning that the workers
and the client connect to the respective sockets, since *service
parts* bind to its respective outwards-facing socket.

The part library has a part for each one of the needs depicted
above. There is a :py:class:`pylm.parts.services.PullService` that
binds a ZeroMQ Pull socket to the exterior, and sends the messages to
the router. There is a :py:class:`pylm.parts.services.PubService` that
works exactly the other way around. It listens to the router, and
forwards the messages to a ZeroMQ Push socket. There are also specific
services to connect to worker servers,
:py:class:`pylm.parts.services.WorkerPullService` and
:py:class:`pylm.parts.services.WorkerPushService`, that are very
similar to the two previously described services. With those pieces,
we are ready to build a master server as follows

.. literalinclude:: ../../examples/template/master.py
    :language: python
    :linenos:

.. note::

   There is an additional type of service called *bypass* in this
   implementation, that will be described at the end of this section.

This server is functionally identical to the master server used in the
first example of the section describing :ref:`standalone`. You can
test it using the same client and workers.

Bypass parts
------------

