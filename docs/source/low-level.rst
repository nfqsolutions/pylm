.. _low-level-api:

Low level API
=============

If you are proficient in distributed computing, some of the key aspects of pylm may sound like
the actor model. We are aware of this similarity, but we would rather use the term micro-service,
because pylm does not expose a programming paradigm. It's just a framework with pieces to implement
distributed systems.

Some concepts in this section may be hard, particularly if you don't know how message queues work,
ZeroMQ in particular. Before reading this section, it may be a good idea to read the
`ZeroMQ Guide <http://zguide.zeromq.org/page:all>`_.

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
(outbound). At each side there are a series of components that are connected to the exterior and the router. If
you know how an actual router works, a component would be a NIC, while the two ROUTER sockets and the routing table
would be the switch. The router is documented in :py:class:`pylm.components.core.Router`.

The components are also related to the router by the fact that they are all threads that run
within the same processor. In consequence, a pylm micro-service could be described as a router and a series of
components that run in the same process.

The components
--------------

The components can be inbound or outbound, and blocking or non-blocking.

:`Inbound component`: The component waits for a message coming from the exterior. This kind of components
    are documented in :py:class:`pylm.components.core.ComponentInbound`. This includes components that connect to the
    exterior via SUB or PULL sockets.

:`Outbound component`: The component waits for a message coming from the router.  This kind of components
    are documented in :py:class:`pylm.components.core.ComponentOutbound`. This includes components that connect to the
    exterior via PUB or PUSH sockets.

:`Non-blocking component`: The component never blocks after getting the message, regardless if the message comes
    from the router or the exterior.

:`Blocking component`: The component blocks after getting the message to give a response, even if the message is sent
    to the router. **You must know what you are doing if you use this kind of components**, because they tend to block the
    ROUTER socket completely. This is the reason why in the previous sketch about the router and the components, there
    are arrows that point in both directions, meaning that messages may block the rest of the router to go back and
    forth.

While Inbound and Outbound components are different classes, the blocking or non-blocking type is set with a parameter
when the component is instantiated.

The two component classes (:py:class:`pylm.components.core.ComponentInbound` and
:py:class:`pylm.components.core.ComponentOutbound`) are not designed to be used but to be subclassed. The children
of the components are called services and connections.

Services and connections
------------------------

The family of components grows with their children: the services and the connections. We have classified the
components as a function of where the message comes from and their behavior. One can further classify the components
whether they bind the socket or they connect to a socket.

:Service: A component that binds a socket that faces the exterior.

:Connection: A component that connects to an exterior socket.

With this piece of classification, the whole family picture is (almost) over. There is a small library of services
available in :py:mod:`pylm.components.services`, and a similar library of components in
:py:mod:`pylm.components.connections`.

.. note::

   All components, and the router, have a ``start`` method. Since they are all designed to run on a thread, the
   threading library must call only that method to get the component running.

Example
.......

It's time to build a small micro-service from a router and some services and components that are already available.

Bypass components
-----------------
