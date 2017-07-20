The Sink server
===============

We have seen how to fan-out the stream of messages with :ref:`pipeline`. The
next step is to learn how to fan-in a series of streams and join the output. This
can be done via the :class:`pylm.servers.Sink` server.

A Sink server can subscribe to one or many components of type
:class:`pylm.servers.Server` or :class:`pylm.servers.Pipeline`, and fetch all the
message every previous step releases. The configuration is similar to a Pipeline
component, only the ``sub_addresses`` and the ``previous`` parameters require
further comment. Since the component must connect to multiple components upstream,
these parameters are of type :py:class:`list`, ``sub_addresses`` are the list
of addresses the component has to connect to, and ``previous`` are the topics for
subscription. The values of these two parameters are zipped, so the order of the
elements matter.

You can see a complete example of the use of a :class:`pylm.servers.Sink` in
:ref:`pipeline-sink`.
